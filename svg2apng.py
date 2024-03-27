"""
Create an animated .png from an animated .svg:

This assumes the directory specified on the command line contains at least .svg file.
During the first invocation, if only 1 .svg file exists it is copied with a '2' appended
to the filename before generating an index.html file with the two .svg's included.
This is done to permit checking while editing the seconds .svg to be the appropriate size
as well as to replace any CSS-based animations with SMIL-based ones. Don't forget to set
the "repeatCount" settings to something other than "indefinite".

The second invocation on the same directory will create a convert.html file with the
second .svg file embedded. When loaded into a browser, this file will take snapshots of
the animation and encode the images into a .json file and then ask the user to download
the result.

The third invocation will read the downloaded .json file and create an animated .png
with the folder name as the file name.

The files 's2a_index.j2' and 's2d_convert.j2' are templates into which .svg files are
either referenced or embedded. The bulk of the Javascript in 's2a_convert.j2' came from:
https://stackoverflow.com/questions/76276767/convert-animatetransform-svgs-transformation-into-animated-gif-image
"""
import sys
from pathlib import Path
import glob
import shutil
import json
import base64
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from PIL import Image


INDEX_FN = 'index.html'
CONVERT_FN = 'convert.html'
BASE64_PRE = 'data:image/png;base64,'
INDEX_TEMPLATE = 's2a_index.html.j2'
CONVERT_TEMPLATE = 's2a_convert.html.j2'


def need_index(folder: Path) -> bool:
    """ Do we need to create an index.html? """
    index_path = folder / INDEX_FN
    return not index_path.is_file()


def create_index(folder: Path):
    """ Create index.html with references to .svg so one can be edited """
    svg_file_names = sorted(glob.glob('*.svg', root_dir=folder))
    if not svg_file_names:
        raise FileNotFoundError(f'No .svg file in {folder}')
    if len(svg_file_names) > 2:
        raise RuntimeError(f'Too many .svg files in {folder}')

    # Make a copy of the svg for editing if necessary
    if len(svg_file_names) == 1:
        src_path = Path(folder, svg_file_names[0])
        dst_path = Path(folder, src_path.stem + '2.svg')
        print(f'Making a copy of {src_path.name} as {dst_path.name}')
        shutil.copy(src_path, dst_path)
        svg_file_names.append(dst_path.name)

    env = Environment(loader=FileSystemLoader('.'))
    html_str = env.get_template(INDEX_TEMPLATE).render(
        svg1=svg_file_names[0],
        svg2=svg_file_names[1]
    )
    index_path = folder / INDEX_FN
    with open(index_path, 'w') as outf:
        outf.write(html_str)

    print(f'Created {index_path} with {svg_file_names[0]} and {svg_file_names[1]}')


def need_convert(folder: Path) -> bool:
    """ Do we need to create a convert.html? """
    convert_path = folder / CONVERT_FN
    return not convert_path.is_file()


def create_convert(folder: Path, width: int, height: int, duration: int):
    """ Create convert.html with included .svg contents """
    svg_file_names = sorted(glob.glob('*.svg', root_dir=folder))
    if len(svg_file_names) != 2:
        raise RuntimeError(f'Expected exactly 2 .svg files in {folder}')

    svg_file = folder / svg_file_names[1]
    with open(svg_file, 'r') as src:
        while line := src.readline():
            if '<svg' in line:                  # start of <svg> tag?
                svg_src = line + src.read()     # grab this line plus the rest of the file
                break

    # fill in template parameters and output to .html file
    env = Environment(loader=FileSystemLoader('.'))
    html_str = env.get_template(CONVERT_TEMPLATE).render(
        svg_src=svg_src,
        canvas_width=width,
        canvas_height=height,
        duration_ms=duration,
        output_filename=folder.name + '.json'
    )
    convert_path = folder / CONVERT_FN
    with open(convert_path, 'w') as outf:
        outf.write(html_str)

    print(f'Created {convert_path} with {svg_file_names[1]}')


def need_ani_png(folder: Path) -> bool:
    """ Do we need to process a .json into an animated .png? """
    png_path = folder / (folder.name + '.png')
    if png_path.is_file():
        return False

    json_path = folder / (folder.name + '.json')
    if not json_path.is_file():
        raise FileNotFoundError(f'{json_path} not found')

    return True


def create_ani_png(folder: Path):
    """ Create an animated .png from the info in the generated .json file """
    json_path = folder / (folder.name + '.json')
    with open(json_path, 'r') as jpath:
        jobj = json.load(jpath)

    frames: list[Image] = []
    for pic64 in jobj['pics']:      # decode b64 strings as PNG images
        bio = BytesIO(base64.b64decode(pic64[len(BASE64_PRE):]))
        frames.append(Image.open(bio))

    png_path = folder / (folder.name + '.png')
    frames[0].save(png_path,
                   disposal=1,      # revert to bg before next frame
                   duration=jobj['duration'],
                   loop=0,          # infinite loop
                   append_images=frames[1:],
                   save_all=True,
                   optimze=False)
    print(f'{len(frames)} frames written to {png_path}')


def do_help():
    print("""
Usage is:
python3 svg2apng.py [-dur ddd] [-width www] [-height hhh] [-help] <directory>
""")
    sys.exit(1)


def main(args: list[str]):
    dir_path = None
    width = 64
    height = 64
    duration = 333

    while args:
        arg = args.pop(0)
        if '-help'.startswith(arg):
            do_help()
        elif arg == '-dur':
            duration = int(args.pop(0))
        elif arg == '-width':
            width = int(args.pop(0))
        elif arg == '-height':
            height = int(args.pop(0))
        elif dir_path is None:
            dir_path = Path(arg)
        else:
            print(f'Ignoring extraneous paramter: "{arg}"')

    if dir_path is None or not dir_path.is_dir():
        raise FileNotFoundError(f'Non-existent input directory: {dir_path}')

    if need_index(dir_path):
        create_index(dir_path)
    elif need_convert(dir_path):
        create_convert(dir_path, width, height, duration)
    elif need_ani_png(dir_path):
        create_ani_png(dir_path)
    else:
        print('Already done')


if __name__ == "__main__":
    argv = sys.argv[1:]  # copy inputs; skip script name
    if not argv:  # default for testing
        main(['testing'])
    else:
        try:
            main(argv)
        except Exception as ex:  # noqa
            print(ex, file=sys.stderr)
