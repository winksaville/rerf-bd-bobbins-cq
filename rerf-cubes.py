#!/usr/bin/env python3
import argparse
import logging
import cadquery as cq
import sys

from context import Context

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# Resulution for of my printer
# TODO: Make a context class and add this to it
# and pass the context to the functions.
# TODO: Add x, y, z resolution to the context class

def round_to_resolution(value: float, resolution: float) -> float:
    """
    Rounds a value to the nearest multiple of the specified resolution.

    Parameters:
        value (float): The value to round.
        resolution (float): The resolution to round to.

    Returns:
        float: The rounded value.
    """
    return round(value / resolution) * resolution


def generate_cube(ctx: Context, cube_number: int, cube_size: float, tube_size: float):
    """
    Generates a 3D cube with text inscriptions on specified faces.

    Parameters:
        cube_number (int): The cube number to engrave on the +Y face.
        cube_size (float): The size of the cube to engrave on the +X face.
        tube_size (float): The tube size to engrave on the -X face.

    Returns:
        CadQuery object representing the final cube.
    """

    # Create the base cube centered at (0,0,0)
    cube = cq.Workplane("XY").box(cube_size, cube_size, cube_size)

    # Prepare formatted text with three significant digits
    cube_number_text = f"{cube_number}"
    cube_size_text = f"{cube_size:5.3f}"
    tube_size_text = f"{tube_size:5.3f}"

    htext = round_to_resolution(0.7, resolution)
    dcut = round_to_resolution(0.1, resolution)

    def make_text(s):
        def callback(wp):
            wp = wp.workplane(centerOption="CenterOfMass").text(
                s, htext, -dcut, font="RobotoMono Nerd Font"
            )
            return wp

        return callback

    # Chisel text into the respective faces
    cube = cube.faces(">X").invoke(make_text(cube_size_text))
    cube = cube.faces("<X").invoke(make_text(tube_size_text))
    cube = cube.faces(">Y").invoke(make_text(cube_number_text))

    # Create a hole for the tube on the top face
    cube = cube.faces(">Z").workplane(centerOption="CenterOfMass").hole(tube_size)

    # Shift the cube so its bottom face is on the XY plane at Z=0
    cube = cube.translate((0, 0, cube_size / 2))

    return cube

def support_pillar(ctx: Context, support_len: float, support_diameter: float, support_tip_diameter: float):
    """
    Creates a support pillar with a base and a tip.

    Created with the help of ChatGPT:
        https://chatgpt.com/share/67f8446f-77b4-800c-ba3c-30de5b676896

    Parameters:
        support_len (float): The length of the support pillar.
        support_diameter (float): The diameter of the base of the support.
        support_tip_diameter (float): The diameter of the tip of the support.
    Returns:
        CadQuery object representing the support pillar.
    """
    base_len = support_len / 2
    tip_len = support_len / 2

    # Base: create a cylinder for the base
    base = cq.Workplane("XY").circle(support_diameter / 2).extrude(base_len)

    # Cone: create using makeCone and move it into place
    tip = cq.Solid.makeCone(
        support_diameter / 2,
        support_tip_diameter / 2,
        tip_len,
    ).translate(cq.Vector(0, 0, base_len))

    return base.union(tip)

def gnerate_square_support_base(ctx: Context, base_size: float, base_layers: float, layer_height: float):
    """
    Generates a square support base with tappered edges
    so it's easier to pry off the build plate.

    Created with the help of ChatGPT:
        https://chatgpt.com/share/67f84393-dd80-800c-8a29-d3d0e446f434)

    Parameters:
        base_size (float): The size of the base.
        base_layers (float): The number of layers for the base.

    Returns:
        CadQuery object representing the square base.
    """
    # Calculate the base height and the top is full sized
    base_height = base_layers * layer_height
    top_size = base_size

    # The bottom is smaller than the top and will have a 45 degree slope
    # so it's easier to pry off the build plate
    bottom_size = top_size - ((base_layers * layer_height) * 2)

    # Create the base and top squares
    bottom = cq.Workplane("XY").rect(bottom_size, bottom_size).workplane(offset=base_height)
    top = bottom.rect(top_size, top_size).clean()

    # Create the solid by lofting between the bottom and top squares
    base = top.loft().clean()

    return base.clean()


def generate_support(
        ctx: Context,
        base_size: float,
        base_layers: float,
        support_len: float,
        support_base_diameter: float,
        support_tip_diameter: float):
    """
    Generates a support structure for the cube.

    Parameters:
        base_size (float): The size of the base.
        base_layers (float): The number of layers for the base.
        support_len (float): The length of the support structure.
        support_base_diameter (float): The diameter of the base of the support.
        support_tip_diameter (float): The diameter of the tip of the support.

    Returns:
        CadQuery object representing the final support structure.
    """

    # Create a cube for the base laying on the xy plane
    base_height = base_layers * ctx.layer_height
    base = gnerate_square_support_base(ctx, base_size, base_layers, ctx.layer_height)

    # Add lenth to the support to guarantee here is overlap with cube and base
    support_len_fudge = 4 * ctx.layer_height

    # 1/2 of the support_len_fudge is into base the other 1/2 is into the cube
    support_z = base_height - (support_len_fudge / 2)

    # The support pillar is the length of the support includes the base_height
    # so we exclude it but we add the fudge so there is significant overlap between
    # the cube and the base.
    support_pillar_len = (support_len - base_height) + support_len_fudge
    support_radius = support_base_diameter / 2
    support_loc_offset = (base_size / 2) - support_radius

    support1 = support_pillar(ctx, support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support1 = support1.translate((-support_loc_offset, -support_loc_offset, support_z))
    support2 = support_pillar(ctx, support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support2 = support2.translate((support_loc_offset, -support_loc_offset, support_z))
    support3 = support_pillar(ctx, support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support3 = support3.translate((0, support_loc_offset, support_z))
    
    # Union the base and support
    build_object = base.add(support1).add(support2).add(support3).clean()

    return build_object


def export_model(ctx: Context, model: cq.Workplane):
    """
    Exports the given CadQuery model to a file in the specified format.

    Parameters:
        ctx (Context): The context object containing parameters for the model.
        model (cq.Workplane): The CadQuery model to export.
        filename (str): The base name of the output file (without extension).

    Returns:
        None
    """

    if ctx.file_format.lower() == "stl":
        # TODO: Allow ascii=True/False to be passed as a parameter
        cq.Assembly(model).export(ctx.file_name + ".stl", exportType="STL", ascii=True)
    elif ctx.file_format.lower() == "step":
        cq.exporters.export(model, ctx.file_name + ".step")
    else:
        print("Unsupported format. Use 'stl' or 'step'.", file=sys.sdterr)

def generate_build_object(ctx: Context) -> cq.Workplane:
        support_len = ctx.support_len
        support_diameter = round_to_resolution(0.75, ctx.resolution)
        support_tip_diameter = round_to_resolution(0.3, ctx.resolution)

        pixels_per_mm = 1 / ctx.resolution

        if ctx.cube_count == 1:
            # Create a single cube with support
            support = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
            cube = generate_cube(ctx, 1, ctx.cube_size, ctx.tube_size)
            cube = cube.translate((0, 0, support_len))
            build_object = cube.add(support)

            # The size is the cube size since there is only one cube
            ctx.position_box_size_pixels = [ctx.cube_size * pixels_per_mm, ctx.cube_size * pixels_per_mm]
        elif ctx.cube_count == 4:
            # Create 4 cubes with support
            position_box_width = ctx.position_box_size_pixels[0] / pixels_per_mm
            position_box_height = ctx.position_box_size_pixels[1] / pixels_per_mm
            cube_size_half = ctx.cube_size / 2

            cube_number = 1

            # Postion so the cube is in the upper left corner of position_box
            support1 = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
            cube1 = generate_cube(ctx, cube_number, ctx.cube_size, ctx.tube_size)
            cube1 = cube1.translate((0, 0, support_len))
            cube1 = cube1.add(support1)
            cube1 = cube1.translate((cube_size_half, cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the lower left corner of position_box
            support2 = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
            cube2 = generate_cube(ctx, cube_number, ctx.cube_size, ctx.tube_size)
            cube2 = cube2.translate((0, 0, support_len))
            cube2 = cube2.add(support2)
            cube2 = cube2.translate((cube_size_half, position_box_height - cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the upper right corner of position_box
            support3 = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
            cube3 = generate_cube(ctx, cube_number, ctx.cube_size, ctx.tube_size)
            cube3 = cube3.translate((0, 0, support_len))
            cube3 = cube3.add(support3)
            cube3 = cube3.translate((position_box_width - cube_size_half, cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the lower right corner of position_box
            support4 = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
            cube4 = generate_cube(ctx, cube_number, ctx.cube_size, ctx.tube_size)
            cube4 = cube4.translate((0, 0, support_len))
            cube4 = cube4.add(support4)
            cube4 = cube4.translate((position_box_width - cube_size_half, position_box_height - cube_size_half, 0))
            cube_number += 1

            # Create the build object by uniting the four cubes
            build_object = cube1.add(cube2).add(cube3).add(cube4)

        elif ctx.cube_count == 9:
            print("Creating 9 cubes")
            position_box_width = ctx.position_box_size_pixels[0] / pixels_per_mm
            position_box_height = ctx.position_box_size_pixels[1] / pixels_per_mm
            cube_size_half = ctx.cube_size / 2
            print(f"position_box_width: {position_box_width}, position_box_height: {position_box_height}, cube_size_half: {cube_size_half}")

            y_initial = cube_size_half
            x_initial = cube_size_half
            y_step = (position_box_height - ctx.cube_size) / 3
            x_step = (position_box_width - ctx.cube_size) / 3
            print(f"y_initial: {y_initial}, x_initial: {x_initial}, y_step: {y_step}, x_step: {x_step}")
            for i in range(3):
                x = x_initial + (x_step * i)
                for j in range(3):
                    y = y_initial + (y_step * j)

                    cube_number = i * 3 + j + 1

                    print(f"cube_number: {cube_number}, x: {x}, y: {y}")
                    # Postion so the cube is in the upper left corner of position_box
                    support = generate_support(ctx, ctx.cube_size, ctx.base_layers, support_len, support_diameter, support_tip_diameter)
                    cube = generate_cube(ctx, cube_number, ctx.cube_size, ctx.tube_size)
                    cube = cube.translate((0, 0, support_len))
                    cube = cube.add(support)
                    cube = cube.translate((x, y, 0))

                    if i == 0 and j == 0:
                        build_object = cube
                    else:
                        build_object = build_object.add(cube)

        else:
            print("Unsupported cube count, expected 1 or 4.", file=sys.stderr)
            return None

        # Translate the build object to the specified position
        build_object = build_object.translate((ctx.position_box_location[0], ctx.position_box_location[1], 0))

        # Have the file name include the size and location of the position box
        size_in_mm = [(ctx.position_box_size_pixels[0]) / pixels_per_mm, (ctx.position_box_size_pixels[1] / pixels_per_mm)]
        location_in_mm = [(ctx.position_box_location[0]), (ctx.position_box_location[1])]
        ctx.file_name = f"{ctx.file_name}-{size_in_mm[0]:5.3f}x{size_in_mm[1]:5.3f}-{location_in_mm[0]:5.3f}-{location_in_mm[1]:5.3f}"

        return build_object

def doit(ctx: Context):
    """
    Generates a 3D model of cubes with text inscriptions and exports it to a file.

    Parameters:
        ctx (Context): The context object containing parameters for the model.
    Returns:
        CadQuery object representing the final model.
    """
    build_object = generate_build_object(ctx)
    export_model(ctx, build_object)
    return build_object


resolution = 0.017
default_cube_size = resolution * 141
default_tube_size = resolution * 37
default_layer_height = 0.050
default_resolution = resolution
default_support_len = 5.0
default_base_layers = 10 # Change to mm and then calculate the number of layers
default_position_box_width = round_to_resolution(5000, default_resolution)
default_position_box_height = round_to_resolution(2500, default_resolution)
default_position_box_location_x = 0
default_position_box_location_y = 0

if __name__ == "__main__":
    logging.debug(f"__main__ logging.info: __name__: {__name__}")

    parser = argparse.ArgumentParser(description="Generate 3D cubes with text inscriptions.")
    parser.add_argument("filename", type=str, help="Name of the output file (without extension)")
    parser.add_argument("format", type=str, choices=["stl", "step"], help="Format to export the model ('stl' or 'step')")
    parser.add_argument("cube_count", type=int, choices=[1, 4, 9], help="Number of cubes to create (1, 4 or 9)")
    parser.add_argument("-c", "--cube_size", type=float, default=default_cube_size, help=f"Cube size engraved on the +X face, defaults to {default_cube_size:5.3f}")
    parser.add_argument("-t", "--tube_size", type=float, default=default_tube_size, help=f"Tube size engraved on the -X face, defaults to {default_tube_size:5.3f}")
    parser.add_argument("-r", "--resolution", type=float, default=default_resolution, help=f"resolution of the printer, defaults to {default_resolution}")
    parser.add_argument("-l", "--layer_height", type=float, default=default_layer_height, help=f"Layer height of the printer, defaults to {default_layer_height:5.3f}")
    parser.add_argument("-s", "--support_len", type=float, default=default_support_len, help=f"Length of the support structure, defaults to {default_support_len:5.3f}")
    parser.add_argument("-bl", "--base_layers", type=int, default=default_base_layers, help=f"Number of layers for the base, defaults to {default_base_layers}")
    parser.add_argument("-pbsp", "--position_box_size_pixels", type=float, nargs=2, default=[default_position_box_width, default_position_box_height], metavar=('width', 'height'), help=f"Size of box to place the cubes, defaults to ({default_position_box_width}, {default_position_box_height})")
    parser.add_argument("-pbl", "--position_box_location", type=float, nargs=2, default=[default_position_box_location_x, default_position_box_location_y], metavar=('x', 'y'), help=f"Location of placement box, defaults to ({default_position_box_location_x}, {default_position_box_location_y})")

    # Print help if no arguments are provided
    #
    # What I really want is to print the help if not enough positional arguments
    # are passed but parser.parase_args() can't do that. The Bot suggested
    # subclassing ArgumentParser. If follow this link:
    #    https://chatgpt.com/share/67fc1e3c-647c-800c-a1be-00d68d516b10
    # and then search for "subclassing ArgumentParser" you see the suggestion.
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    ctx = Context(
        file_name=args.filename,
        file_format=args.format,
        cube_count=args.cube_count,
        cube_size=args.cube_size,
        tube_size=args.tube_size,
        resolution=args.resolution,
        layer_height=args.layer_height,
        support_len=args.support_len,
        base_layers=args.base_layers,
        position_box_size_pixels=[args.position_box_size_pixels[0], args.position_box_size_pixels[1]],
        position_box_location=[args.position_box_location[0], args.position_box_location[1]],
    )
    logging.debug(f"ctx: {ctx}")

    build_object = doit(ctx)
elif __name__ == "__cq_main__":
    logging.debug(f"__cq_main__ logging.info: __name__: {__name__}")

    resolution = 0.017

    ctx = Context(
        file_name="rerf-cubes",
        file_format="stl",
        cube_count=1,
        cube_size=default_cube_size,
        tube_size=default_tube_size,
        resolution=resolution,
        layer_height=default_layer_height,
        support_len=default_support_len,
        base_layers=default_base_layers,
        position_box_size_pixels=[default_position_box_width, default_position_box_height],
        position_box_location=[default_position_box_location_x, default_position_box_location_y],
    )
    logging.debug(f"ctx: {ctx}")

    build_object = doit(ctx)

    show_object(build_object, name=ctx.file_name)
else:
    logging.info(f"Unreconized __name__: {__name__}")
