#! /usr/bin/env python
# coding=utf-8

#   Component Generator - An Inkscape extension to generate tabletop game components from a CSV file
#   Copyright (C) 2019 Joel Colombo
#   Inspired by the Generator extension by Aurélio A. Heckert & Export Layers extension
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   Version 1.0

import sys
import inkex
import distutils
import os
import platform
import distutils.spawn
import csv
import ctypes
import subprocess
import tempfile
import shutil
import copy


def is_executable(filename):
    return distutils.spawn.find_executable(filename) is not None


if platform.system() != 'Windows' and is_executable('zenity'):
    class ProgressBar:
        def __init__(self, title, text):
            self.__title = title
            self.__text = text
            self.__active = False

        def __enter__(self):
            self.__devnull = open(os.devnull, 'w')
            self.__proc = subprocess.Popen(
                [
                    'zenity',
                    '--progress',
                    '--title={0}'.format(self.__title),
                    '--text={0}'.format(self.__text),
                    '--auto-close',
                    '--width=400'
                ], stdin=subprocess.PIPE, stdout=self.__devnull,
                stderr=self.__devnull)
            self.__active = True
            return self

        def __exit__(self, *args):
            if self.__active:
                self.__close()

        def set_percent(self, p):
            if self.is_active:
                self.__proc.stdin.write(str(p) + '\n')

        @property
        def is_active(self):
            if self.__active and self.__proc.poll() is not None:
                self.__close()
            return self.__active

        def __close(self):
            if not self.__proc.stdin.closed:
                self.__proc.stdin.close()
            if not self.__devnull.closed:
                self.__devnull.close()
            self.__active = False
else:
    class ProgressBar:
        def __init__(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_percent(self, p):
            pass

        @property
        def is_active(self):
            return True


if platform.system() == 'Windows':
    def show_info(title, message):
        mb_iconinformation = 0x40
        ctypes.windll.user32.MessageBoxA(0, message, title, mb_iconinformation)

    def show_question(title, message):
        mb_iconquestion = 0x20
        mb_yesno = 0x4
        idyes = 6
        return ctypes.windll.user32.MessageBoxA(
            0, message, title, mb_iconquestion | mb_yesno) == idyes

    def show_error_and_exit(title, message):
        mb_iconerror = 0x10
        ctypes.windll.user32.MessageBoxA(0, message, title, mb_iconerror)
        sys.exit(1)

elif is_executable('zenity'):
    def show_info(title, message):
        zenity('info', title, message)

    def show_question(title, message):
        return zenity('question', title, message) == 0

    def show_error_and_exit(title, message):
        zenity('error', title, message)
        sys.exit(1)

    def zenity(mode, title, message):
        return call_no_output(
            [
                'zenity',
                '--{0}'.format(mode),
                '--title={0}'.format(title),
                '--text={0}'.format(message)
            ])
else:
    def show_info():
        pass

    def show_question():
        return None

    def show_error_and_exit(title, message):
        sys.stderr.write(title + '\n' + message + '\n')
        sys.exit(1)


def open_file_viewer(filename):
    if platform.system() == 'Windows':
        os.startfile(filename)
    elif is_executable('xdg-open'):
        call_no_output(['xdg-open', filename])
    else:
        show_error_and_exit(
            'No preview', 'Preview is not available because '
            '"xdg-open" is not installed.')


def call_no_output(args):
    with open(os.devnull, 'w') as devnull:
        return subprocess.call(args, stdout=devnull, stderr=devnull)


def call_or_die(args, error_title):
    try:
        subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        show_error_and_exit(error_title, error.output)


class ComponentGenerator(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        # self.OptionParser.add_option('-w', '--what', action='store', type='string', dest='what', default='World', help='What would you like to greet?')

        self.OptionParser.add_option("--tabset", dest="tabset")
        self.OptionParser.add_option("--vartype", action='store', type='string', dest="varType", default="column")
        self.OptionParser.add_option("--datafile", action='store', type='string', dest="dataFile", default="")
        self.OptionParser.add_option("--specialchars", action='store', type='inkbool', dest="specialChars", default=True)
        self.OptionParser.add_option("--extravars", action='store', type='string', dest="extraVars", default="")

        self.OptionParser.add_option("--layerCol", action='store', type='string', dest="layerCol", default="")
        self.OptionParser.add_option("--includeHidden", action='store', type='inkbool', dest="includeHidden", default=True)
        self.OptionParser.add_option("--includeEmptyLayers", action='store', type='inkbool', dest="includeEmptyLayers", default=False)

        self.OptionParser.add_option("--format", action='store', type='string', dest="format", default="PDF")
        self.OptionParser.add_option("--dpi", action='store', type='int', dest="dpi", default=90)
        self.OptionParser.add_option("--output", action='store', type='string', dest="output", default="")
        self.OptionParser.add_option("--preview", action='store', type='inkbool', dest="preview", default=False)

    def effect(self):
        # what = self.options.what
        # svg = self.document.getroot()
        # or alternatively
        # svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]

        tempdir = tempfile.mkdtemp()

        try:
            args = self.options
            tempdir = tempfile.mkdtemp()

            if not os.path.isfile(args.dataFile):
                show_error_and_exit(
                    'File not found', 'The CSV file "{0}" does not '
                                      'exist.'.format(args.dataFile))

            if (not os.path.splitext(args.output)[1][1:].upper() ==
                    args.format):
                if show_question(
                        'Output file extension',
                        'Your output pattern has a file extension '
                        'different from the export format.\n\nDo you want to '
                        'add the file extension?'):
                    args.output += '.' + \
                                              args.format.lower()

            outdir = os.path.dirname(args.output)
            if outdir != '' and not os.path.exists(outdir):
                os.makedirs(outdir)
            template = self.document
            opts = self.options
            with open(self.options.dataFile, 'rb') as csvfile:
                data = parse_csv(opts, csvfile)
                generate_output(opts, template, data, tempdir)

        finally:
            shutil.rmtree(tempdir)


def parse_csv(opts, csvfile):
    if opts.varType == 'column':
        csvdata = [[(str(x), y) for x, y in enumerate(row, start=1)] for row in csv.reader(csvfile)]
    else:
        csvdata = [row.items() for row in csv.DictReader(csvfile)]

    csvdata = prepare_data(csvdata, opts)
    if len(csvdata) < 1:
        show_error_and_exit(
            'Empty CSV file', 'There are no data sets in your CSV file.')

    return csvdata


def prepare_data(data_old, opts):
    data_new = []
    if len(opts.extraVars) == 0:
        extra_value_info = []
    else:
        extra_value_info = \
            [x.split('=>', 2) for x in opts.extraVars.split('|')]

    for row in data_old:
        row_new = []
        for key, value in row:
            if not value:
                value = ''
            debug(str(key)+' : '+str(value))
            if key == '':
                continue
            if opts.specialChars:
                value = value.replace('&', '&amp;')
                value = value.replace('<', '&lt;')
                value = value.replace('>', '&gt;')
                value = value.replace('"', '&quot;')
                value = value.replace("'", '&apos;')
            row_new.append(('%VAR_'+key+'%', value))
            for search_replace in extra_value_info:
                if len(search_replace) != 2:
                    show_error_and_exit(
                        'Extra vars error',
                        'There is something wrong with your extra vars '
                        'parameter')
                if search_replace[1] == key:
                    row_new.append((search_replace[0], value))
        data_new.append(row_new)

    return data_new


def generate_output(opts, template, data, tempdir):
    count = len(data)
    if opts.preview:
        for row in data:
            varlist = '\n'.join([key for key, value in row])
            show_info(
                'Generator Variables',
                'The replaceable text, based on your configuration and on '
                'the CSV are:\n{0}'.format(varlist))

            new_file = generate_item(template, opts, row, tempdir)
            open_file_viewer(new_file)
            break
    else:  # no preview
        with ProgressBar('Generator', 'Generating...') as progress:
            for num, row in enumerate(data, start=1):
                generate_item(template, opts, row, tempdir)
                if not progress.is_active:
                    break
                progress.set_percent(num * 100 / count)


def debug(line):
    txt_file = "/srv/python/inkscape/plugin-sandbox/output/debug.txt"
    with open(txt_file, 'a+') as f:
        f.write(line + "\n")
    f.close()


def generate_item(template, opts, replacements, tempdir):
    # Parse layer values from replacements opts.layerCol (also use opts.includeHidden when building temp SVG)
    if len(replacements) < 1:
        return
    force_all = False
    valid_layers = []
    lay_col = opts.layerCol.lower().strip()
    lay_col_found = len(lay_col) == 0
    if lay_col_found:
        force_all = True
    if not force_all:
        for key, value in replacements:
            if key.lower() == '%var_'+lay_col+'%':
                lay_col_found = True
                if value.strip() != '':
                    valid_layers = value.split('|')
                    for idx, lay in enumerate(valid_layers):
                        valid_layers[idx] = lay.strip()
    if not lay_col_found:
        show_error_and_exit(
            'Layer Column Error', 'A column "'+lay_col+'" was specified for layer data but was not found in the CSV')

    layers = get_layers(template)
    template_content = build_temp_svg_file(template, layers, valid_layers, opts, force_all)
    destfile = opts.output

    # show_error_and_exit('SVG FILE', template_content)

    # Replace ALL the text in the SVG string (template must be a string at this point I think)
    for search, replace in replacements:
        template_content = template_content.replace(search, replace)
        destfile = destfile.replace(search, replace)

    tmp_svg = os.path.join(tempdir, 'temp.svg')

    with open(tmp_svg, 'wb') as f:
        f.write(template_content)

    if opts.format == 'SVG':
        shutil.move(tmp_svg, destfile)
    elif opts.format == 'JPG':
        tmp_png = os.path.join(tempdir, 'temp.png')
        ink_render(tmp_svg, tmp_png, 'PNG', opts.dpi)
        png_to_jpg(tmp_png, destfile)
    else:
        ink_render(tmp_svg, destfile, opts.format, opts.dpi)

    return destfile


def build_temp_svg_file(template, layers, valid_layers, opts, force_all):

    include_hidden = opts.includeHidden
    include_all = opts.includeEmptyLayers and len(valid_layers) < 1

    show_layer_ids = []
    if not force_all:
        for (layer_id, layer_label, layer_type) in layers:
            if layer_type == 'fixed':
                show_layer_ids.append(layer_id)
            elif layer_type == 'export':
                for vlayer in valid_layers:
                    if layer_label.startswith("["+vlayer.lower().strip()+"] "):
                        show_layer_ids.append(layer_id)
            elif layer_type == 'all' and include_all:
                show_layer_ids.append(layer_id)

    with tempfile.NamedTemporaryFile() as fp_svg:
        dest_svg_path = fp_svg.name
        doc = copy.deepcopy(template)
        for layer in doc.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS):
            was_hidden = str(layer.get('style')).find('display:none') > -1
            layer.attrib['style'] = 'display:none'
            layer_id = layer.attrib["id"]
            if force_all and not was_hidden:
                layer.attrib['style'] = 'display:inline'
            elif layer_id in show_layer_ids and (not was_hidden or (was_hidden and include_hidden and not include_all)):
                layer.attrib['style'] = 'display:inline'
        doc.write(dest_svg_path)
        return fp_svg.read()


def get_layers(template):
    svg_layers = template.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
    layers = []

    for layer in svg_layers:
        label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
        if label_attrib_name not in layer.attrib:
            continue

        layer_id = layer.attrib["id"]
        layer_label = layer.attrib[label_attrib_name]

        if layer_label.lower().startswith("[fixed] "):
            layer_type = "fixed"
            layer_label = layer_label[8:]
        elif layer_label.lower().startswith("[*] "):
            layer_type = "fixed"
            layer_label = layer_label[4:]
        elif layer_label.lower().startswith("["):
            layer_label = layer_label.lower().strip()
            layer_type = "export"
        else:
            layer_label = layer_label.lower().strip()
            layer_type = "all"

        layers.append([layer_id, layer_label, layer_type])

    return layers


def ink_render(infile, outfile, fileformat, dpi):
    call_or_die(
        [
            'inkscape',
            '--without-gui',
            '--export-{0}={1}'.format(
                fileformat.lower(), outfile),
            '--export-dpi={0}'.format(dpi),
            infile
        ],
        'Inkscape Converting Error')


def png_to_jpg(pngfile, jpgfile):
    if platform.system() == 'Windows':
        show_error_and_exit(
            'JPG Export', 'JPG Export is not available on Windows.')
    elif is_executable('convert'):
        call_or_die(
            [
                'convert',
                'PNG:' + pngfile,
                'JPG:' + jpgfile
            ],
            'ImageMagick Converting Error')
    else:
        show_error_and_exit(
            'JPG export', 'JPG export is not available because ImageMagick is not installed.')


def _main():
    effect = ComponentGenerator()
    effect.affect()
    exit()


if __name__ == "__main__":
    _main()
