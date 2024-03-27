# svg2apng #

## Convert an animated SVG to an animated PNG ##

This code implements (a somewhat "janky") method for converting an animated `.svg` file into an animated `.png` file.
Of course, there are some restrictions:
the animation in the `.svg` must be accomplished via SVG SMIL tags (`<animate>`, `<animateTransform>`, etc.), not 
via the more common CSS tags.
This may require some editing on the caller's part.

### Usage ###

`python3 svg2apng.py [-help] [-width ww] [-height hh] [-duration dd] <folder>`

where:

  - `-dur` sets the duration (in msecs) of each frame of the animation (default = 333)
  - `-width` sets the width of the HTML `<canvas>` element used to draw the SVG image (default = 64)
  - `-height` sets the height of the `<canvas>` element (default = 64)
  - `-help` invokes a short command synopsis
  - `<folder>` is the working folder containing an SVG file to convert and where all output files are created

### Operation ###

It is intended that this app be called 3 times:

During the first call, if there is only one `.svg` file, a copy will be made by appending '2' to the filename.
Next, an `index.html` file is created from a template that simply displays both files.
This is intended to allow editing of the second file to, for example, replace CSS animations with SMIL tags or 
change the size of the image. *Note:* the `repeatCount` parameter for all animation tags must be set to a limited
amount of time - not `indefinite`.
Having the `index.html` file open in a browser eases the "edit, save, refresh" cycle.

Calling the app a second time will generate a `convert.html` file that embeds the second `.svg` file inside it using another template.
This HTML is designed to display the image and take snapshots while the animation runs.
The `-duration` parameter does double duty in that it also specifies how often these snapshots are taken.
The script in the HTML stops creating snapshots when the animations all stop -
hence the need for `repeatCount` parameters to be finite values.
After the "Frame #" outputs stop appearing in the browser window,
clicking on the button will solicit the user to download a `<folder>.json` file into the working folder.
This file contains base64-encoded strings for each snapshot created.

Finally, calling the app a third time will read the downloaded `.json` file and output
an animated `<folder>.png`.

This mechanism for determining which "step" of the program operation to perform is done by
checking for the existence of files generated during a previous run. I.e., if the `index.html`
file does not exist, run step 1. If the `convert.html` file does not exist, run step 2.
If the `<folder>.png` file does not exist, run step 3.

### Requirements ###

This app makes use of the following packages that need to be installed via `pip`:

  - Jinja2
  - PIL (Pillow)

### Credits ###

The Javascript code in the `convert.html` file came from an answer by `@chrwahl` to a
question on [stackoverflow](https://stackoverflow.com/questions/76276767/convert-animatetransform-svgs-transformation-into-animated-gif-image).
I have modified it to generate a single download-able `.json` file that can be processed by this app.
I have also changed the image background to be "transparent" instead of a solid color.
