This is an extension for Inkscape that lets you import a CSV file and have your file exported with one copy per row in the CSV.
Data is replaced from each column with variables you use in your Inkscape SVG file

The component is a reimplementation of the very old Inkscape generator plugin from  Aurélio A. Heckert, which can be found here: http://wiki.colivre.net/Aurium/InkscapeGenerator as well as the prior Python version found here: https://github.com/butesa/ink-generator-python 

This component does everything the others do with some enhancements for using dynamic layers if you wish

It is enhanced to also allow for a dynamic selection of which LAYERS to include for each record as well.

# Installation
The component was made for both Windows & Linux installations of Inkscape (it has been tested more on Linux so please report any Windows problems you may encounter)

### Requirements

- Python 2.7 or higher (shipped with windows Inkscape 0.92.1 or later)

#### Windows

Copy the **_component-generator.inx_** and **_component-generator.py_** files to either of the two locations

```
Installed Globally : C:\Program files\Inkscape\share\extensions
Installed For User : C:\Users\<Username>\Application Data\Roaming\inkscape\share\extension
```

The following features do not work on windows:

- Progress Bar during batch processing
- Output to JPG format

#### GNU / Linux

Copy the **_component-generator.inx_** and **_component-generator.py_** files to either of the two locations

```
Installed Globally : /usr/share/inkscape/extensions
Installed For User : /home/<Username>/.config/inkscape/extensions
```

# Usage

There is an example CSV file included in this repository that will be referenced here

Load your Inkscape file that you wish to batch process output per record for. You will add variables and layer prefixes to indicate what and how you want data replaced for each output file.
Adding variables you want replaced will be done with **%VAR_<key\>%** where key will be the column name or column number from your CSV record

You can find the extension under the main menu:

**Extensions -> Export -> Component Generator...**

A popup will appear with various tabs and options each tab is explained below

### Component Generator PopUp

##### Input Tab

1. REQUIRED: Decide if you will be using the first row in your CSV file as column labels (Choose **CSV Column Name**) or if you will simply reference the column numbers starting with 1 (Choose **CSV Column Position**)
2. REQUIRED: For the CSV File field, you must put in the full path to your CSV file on your computer
3. Optional: Extra text-based values can be added to the replacement options that will match your CSV fields. This will be explained below

##### Layers Tab

If you leave the layer filter column empty. The generator will use all layers as you have them toggled in your working copy (so it ignored prefixes).

1. Optional: If you will be using the dynamic layer selection options (explained below) you must add either the column name or column number (depending on which setting you choose on the Input Tab) that will contain the values for which layer prefixes to include
2. Optional: If using the layer filter above, Toggle on the HIDDEN prefixed layers and ALL layers with the indicated prefixes from that CSV row will be made visible for that record. This allows you to work with the layers prefixed and hidden and they will automatically be turned on at the time of batch processing (it would get pretty ugly if you needed to have all layers ON in your working copy). If this is left unchecked, then only the working layers that match the prefixes and are already visible in the master file will be included
3. Optional: If using the layer filter above and a row in your CSV does NOT specify which prefixed layers to include. This option will include ALL currently visible layers that do NOT have a prefix (or have the prefix [*] or [fixed]). See the Layer information below

##### Output Tab

1. REQUIRED: Export As... lets you choose the type of file that will be output for each record. (JPG is not available on Windows)
2. REQUIRED (for JPG or PNG Exports) : The DPI for output. Each record will output using the PAGE size at the set DPI
3. REQUIRED: Output File Pattern is the pattern that all files will be named with when batching them out
4. Optional: Preview Toggle (If checked, this will only run the first record in your CSV. Use it as a check before running 100 rows and waiting for generation only to find a critical error in your variables)

**IMPORTANT:** You must specify at least one variable in this pattern or all of your output records will overwrite the previous record and you will only get one file.

BAD Example:
```
/my/file/output/folder/image.png
``` 

Causes each record to write over the previous one and you end up with one image.png file

GOOD Example:
```
/my/file/output/folder/image_%VAR_id%.png
```
In this example the "id" column from your CSV will be used to give a unique name to each output file (make sure whatever column(s) you use do not repeat in your CSV records)

If our CSV file had 3 rows in it, and  in the "id" column for each row it had 100, 200, and 300 (one on each row). We would end up with the following 3 files generated:
```
/my/file/output/folder/image_100.png
/my/file/output/folder/image_200.png
/my/file/output/folder/image_300.png
```
Each file would have the data replacements for its row in the CSV

IMPORTANT: Make sure the directory you are writing to has permission to allow new files to be created.
If you specify DIRECTORIES that do not exist, component-generator will attempt to create them on the fly for you

## Using Variables In Your Drawing

You can decide what content will be replaced with data from each row in your CSV by simply setting it to be a variable. There are two ways the variables can be referenced, depending on if you are going to use COLUMN NAMES or COLUMN POSITIONS when running the generator
- If using column names you simply set the text to **%VAR_<column_name\>%**

The column_name should match the value of the first row in your CSV. For example if we have a column called "name" in our CSV first row we would add the variable
**%VAR_name%** to our working text object and it will get replaced with the name column from each row

If we were using the column positions (lets same "name" was the 3rd column in our CSV and we had no first row of column names).
Then the variable to use would be **%VAR_3%**

**IMPORTANT:** It is usually better to use a named set of columns in the first row if you can. This insures that even if you change the order of your columns, the right data will still be used in your replacements. If you used the column position and then decided to add a new column in front of existing ones... well, that means all of the later columns variable replacements would need to be increased by 1 (and that can be a pain)

## Replacing COLORS and IMAGES
So adding text variables that can easily be viewed and seen on your drawing is easy enough... but what about those default colors or placeholder images you imported that you want to be swapped out from each row of your CSV...

Don't worry... Component Generator can handle that just fine ! You just have to add some extra text replacement values.

Remember the INPUT TAB (Step 3)... that's how we will replace colors and images with new data

In that text box you can add any number of text replacements you want swapped out with content from your CSV but you will have to be careful that you pick unique colors and placeholder image names to not cause any accidental replacements.

Here's an example of replacing a color and an image with data from a row
```
#000000=>color_column|myimage.png=>image_column
```
1. You can have any number of variable text replacements done. Just seperate them with a pipe |
2. Each replacement has the original value then an arrow (=>) then the name (or number depending on your setting) of the column you want that replaced with

In the example above this says.... Everywhere in my SVG that uses the color #000000 replace it with whatever I put in my CSV column named color_column (Be sure you put a hex color in each row or you never know what you'll get). So lets say we wanted this record to replace the black (#000000) value with a green one (#46a04b). In that row of the CSV we would simply put **#46a04b** as the value.

**WARNING:** If you haven't thought of it yet... that means ALL (I mean ALL) instances of the #000000 color will be replaced with the rows replacement value. It's very probable that you will unintentionally replace lots of things you didnt mean to and all your black will be green. When choosing a color for something you know will be getting replaced from a CSV record, pick a hex color that you KNOW won't exist elsewhere in your drawing. I like to use a hot pink like #ffc9f8 or whatever works for you. Think of it like a movie/photo green screen... what color will not naturally exist and therefore can easily have all of its usage replaced.

ALSO... if you plan to replace multiple colors with multiple columns from your CSV... you'll need to pick a different starting (placeholder) color for each. Because as it traverses the columns and replaces them, all of your original placeholder colors will be swapped to the new color. So use once placeholder color per column you plan to replace  

###### Image Replacements

In our example above you also saw the myimage.png=>image_column replacement. This is a bit trickier but still easily done with some planning and thought.

- When working in your drawing, you will want to import an image to use as the placeholder for the images you want swapped out.

So for example you may import an image you called "**main-graphic-placeholder.png**" from a folder called "**images/main-graphics**". It is important that your placeholder AND all of your replacement images all reside in the same folder (it can be done with multiple folders but this is the easiest way to do it so thats all I will explain here)

**VERY IMPORTANT:** In order for image replacement to work you MUST import your images using "Link" and NOT the Embed option. If you already have the image imported and "embedded" you will need to make sure you import it as a link. Our replacement script is going to be swapping out the file names and if it's embedded... there will be nothing to swap

So now you have imported a placeholder image called "main-graphic-placeholder.png", got it all sized and positioned where you'll want it.

You will add to the text-based replacement values on the Input Tab:
```
main-graphic-placeholder.png=>image_column
```
 
Then in your CSV file, each row will need a new image file in the "image_column" (or column number if using number position). This new image would simply be named "image1.png" or whatever and would exist in the exact same folder your original placeholder image did.
The generator will simply swap out the "main-graphic-placeholder.png" text with the "image1.png" as the source of the link on that object and all will be done

IMPORTANT: Make sure the images used to replace other images are all the same dimensions. The original placeholders settings will all remain intact and if they are different sizes you may get stretching or skewing or blurriness or whatever. This feature works great for image swaps that are all the same original size

Make sure your placeholder image name is unique. If you used the SAME placeholder image in 5 different places... they will ALL swap out with the image value from the record (this can be great if that was your intent but a mess if you just named all your images placeholder.png or something and intended them to each be replaced by a different column)

One more example of replacing 3 different imported images with 3 different columns from the DB
```
placeholder1.png=>main_graphic|placeholderX.png=>top_icon|dummyicon.png=>lower_icon
```

## Dynamic Layer Displays
Sometimes each record in your CSV would want different layers to be visible for itself but not for the other records in the list. Component Generator is here to save the day. Now you don't have to toggle layers off and on and re-export multiple times if say ONLY "layer1" was needed for your first record but in record 2 you only wanted "layer2" and "layer3" to be included. But all of your records wanted to include a background layer.

Here's how its done.
1. First you have to give your layers a "prefix" in their layer name (thats what generator will look for)

Example:
```
[layer1] My Layer
[layer2] My Second Layer
[layer3] My Third Layer
[layer3] My OTHER Third Layer
My Fourth Layer
[*] Background Layer
```

If these were our layer names we can easily decide which ones to include for each record.

In your CSV you will need a column for the layers you want included (usually I use a column name called "layers"... makes sense right)

Then in EACH row that you want to control the layers visible... you will add which prefixes you want on for that record. So in my first row since I wanted only layer1 and the background to be included... my value in the CSV would look like this: **layer1**

Now in my second row I wanted both layer2 and 3... so the value would look like this: **layer2|layer3**

But wait... I wanted the background layer on all of them. We have you covered. Because you prefixed the background layer with the special "[*]" prefix... it will be included on every record automatically.

So now what about that "My Fourth Layer"... well since it has no prefix it will be left off. Had we wanted it to be on every record we could have simply prefixed it with a [*] as well.

```
Record 1 layers column value = layer1 {will include the following}
[layer1] My Layer
[*] Background Layer

Record 2 layers column value = layer2|layer3 {will include the following}
[layer2] My Second Layer
[layer3] My Third Layer
[layer3] My OTHER Third Layer
[*] Background Layer
```

You see how in the second record there were 2 different layers that used the prefix [layer3] and both are included. You do not have to name each layer individually. Think of the prefixes as a group label. You can name as many with the same prefix as you like.

Prefixes as completely custom, name them whatever you want. The only reserved names are "*, fixed, and export" (but anything else goes, I suggest not using spaces in the prefix but it should technically work, maybe?)

# Running the Generator

Once all your settings in the popup are corrent, your working file is filled with variables you want replaced, and you have a CSV file of different data outputs you want... Just press "APPLY" in the popup and away it goes... if you did everything right... you should have one file of the type you wanted in the location you specified !












