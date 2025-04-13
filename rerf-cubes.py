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
resolution = 0.017

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


def generate_cube(cube_number: int, cube_size: float, tube_size: float):
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

    # Shift the cube so its bottom face is on the build plate (Z = 0)
    cube = cube.translate((0, 0, cube_size / 2))

    return cube

def support_pillar(support_len: float, support_diameter: float, support_tip_diameter: float):
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

def gnerate_square_support_base(base_size: float, base_layers: float, layer_height: float):
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
        layer_height: float,
        base_size: float,
        base_layers: float,
        support_len: float,
        support_base_diameter: float,
        support_tip_diameter: float):
    """
    Generates a support structure for the cube.

    Parameters:
        layer_height (float): The height of each layer.
        base_size (float): The size of the base.
        base_layers (float): The number of layers for the base.
        support_len (float): The length of the support structure.
        support_base_diameter (float): The diameter of the base of the support.
        support_tip_diameter (float): The diameter of the tip of the support.

    Returns:
        CadQuery object representing the final support structure.
    """

    # Create a cube for the base laying on the xy plane (build plate)
    base_height = base_layers * layer_height
    base = gnerate_square_support_base(base_size, base_layers, layer_height)
    #base = cq.Workplane("XY").box(base_size, base_size, base_height, centered=(True, True, False))

    # Create three support pillars on top of the base
    support_pillar_len = support_len - base_height
    support_radius = support_base_diameter / 2
    support_loc_offset = (base_size / 2) - support_radius

    support1 = support_pillar( support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support1 = support1.translate((-support_loc_offset, -support_loc_offset, base_height))
    support2 = support_pillar( support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support2 = support2.translate((support_loc_offset, -support_loc_offset, base_height))
    support3 = support_pillar( support_pillar_len, support_base_diameter, support_tip_diameter).clean()
    support3 = support3.translate((0, support_loc_offset, base_height))
    
    # Union the base and support
    build_object = base.add(support1).add(support2).add(support3).clean()

    return build_object


def export_model(model: cq.Workplane, file_name: str, file_format: str):
    """
    Exports the given CadQuery model to a file in the specified format.

    Parameters:
        model (cq.Workplane): The CadQuery model to export.
        filename (str): The base name of the output file (without extension).
        file_format (str): The export format, either 'stl' or 'step'.

    Returns:
        None
    """
    if file_format.lower() == "stl":
        # TODO: Allow ascii=True/False to be passed as a parameter
        cq.Assembly(model).export(file_name + ".stl", exportType="STL", ascii=True)
        #print(f"Exported as {filename}.stl")
    elif file_format.lower() == "step":
        cq.exporters.export(model, file_name + ".step")
        #print(f"Exported as {filename}.step", file=sys.stderr)
    else:
        print("Unsupported format. Use 'stl' or 'step'.", file=sys.sdterr)

def generate_build_object(cube_count: int, cube_size: float, tube_size: float):
        # build plate size in pixels
        layer_height = 0.030
        base_layers = 6
        support_len = 5.0
        support_diameter = round_to_resolution(0.75, resolution)
        support_tip_diameter = round_to_resolution(0.3, resolution)

        if cube_count == 1:
            # Create a single cube with support
            support = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
            cube = generate_cube(1, cube_size, tube_size)
            cube = cube.translate((0, 0, support_len))
            build_object = cube.add(support)
        elif cube_count == 4:
            # Create 4 cubes with support
            pixels_per_mm = 1 / 0.017
            build_plate_width = 9024 / pixels_per_mm
            build_plate_height = 5120 / pixels_per_mm
            cube_size_half = cube_size / 2

            cube_number = 1

            # Postion so the cube is in the upper left corner of build plate
            support1 = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
            cube1 = generate_cube(cube_number, cube_size, tube_size)
            cube1 = cube1.translate((0, 0, support_len))
            cube1 = cube1.add(support1)
            cube1 = cube1.translate((cube_size_half, cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the lower left corner of build plate
            support2 = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
            cube2 = generate_cube(cube_number, cube_size, tube_size)
            cube2 = cube2.translate((0, 0, support_len))
            cube2 = cube2.add(support2)
            cube2 = cube2.translate((cube_size_half, build_plate_height - cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the upper right corner of build plate
            support3 = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
            cube3 = generate_cube(cube_number, cube_size, tube_size)
            cube3 = cube3.translate((0, 0, support_len))
            cube3 = cube3.add(support3)
            cube3 = cube3.translate((build_plate_width - cube_size_half, cube_size_half, 0))
            cube_number += 1

            # Postion so the cube is in the lower right corner of build plate
            support4 = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
            cube4 = generate_cube(cube_number, cube_size, tube_size)
            cube4 = cube4.translate((0, 0, support_len))
            cube4 = cube4.add(support4)
            cube4 = cube4.translate((build_plate_width - cube_size_half, build_plate_height - cube_size_half, 0))
            cube_number += 1

            # Create the build object by uniting the four cubes
            build_object = cube1.add(cube2).add(cube3).add(cube4)
        else:
            print("Unsupported cube count, expected 1 or 4.", file=sys.stderr)
            return None

        return build_object

def doit(file_name: str, file_format: str, cube_count: int, cube_size: float, tube_size: float):
    """
    Generates a 3D model of cubes with text inscriptions and exports it to a file.
    Parameters:
        file_name (str): The name of the output file (without extension).
        file_format (str): The format to export the model ('stl' or 'step').
        cube_count (int): The number of cubes to create, cube number is engraved on the +Y face.
        cube_size (float): The size of the cube to engrave on the +X face.
        tube_size (float): The tube size to engrave on the -X face.
    Returns:
        CadQuery object representing the final model.
    """
    build_object = generate_build_object(cube_count, cube_size, tube_size)
    export_model(build_object, file_name, file_format)
    return build_object


if __name__ == "__main__":
    logging.debug(f"__main__ logging.info: __name__: {__name__}")

    parser = argparse.ArgumentParser(description="Generate 3D cubes with text inscriptions.")
    parser.add_argument("filename", type=str, help="Name of the output file (without extension)")
    parser.add_argument("format", type=str, choices=["stl", "step"], help="Format to export the model ('stl' or 'step')")
    parser.add_argument("cube_count", type=int, choices=[1, 4], help="Number of cubes to create (1 or 4)")
    parser.add_argument("-c", "--cube_size", type=float, default=2.397, help="Size of the cube engraved on the +X face")
    parser.add_argument("-t", "--tube_size", type=float, default=0.595, help="Tube size and engraved on the -X face")
    parser.add_argument("-r", "--resolution", type=float, default=0.017, help="resolution of the printer")
    parser.add_argument("-l", "--layer_height", type=float, default=0.050, help="Layer height for the model")
    parser.add_argument("-s", "--support_len", type=float, default=5.0, help="Length of the support structure")
    parser.add_argument("-bl", "--base_layers", type=int, default=5, help="Number of base layers for the support structure")
    parser.add_argument("-pbs", "--position_box_size", type=float, nargs=2, default=[round_to_resolution(5000, resolution), round_to_resolution(2500, resolution)], metavar=('width', 'height'), help="Size of box to place the cubes")
    parser.add_argument("-pbl", "--position_box_location", type=float, nargs=2, default=[0, 0], metavar=('x', 'y'), help="Location of placement box")

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
        position_box_size=[args.position_box_size[0], args.position_box_size[1]],
        position_box_location=[args.position_box_size[0], args.position_box_size[1]],
    )
    logging.debug(f"ctx: {ctx}")

    build_object = doit(ctx.file_name, ctx.file_format, ctx.cube_count, ctx.cube_size, ctx.tube_size)
elif __name__ == "__cq_main__":
    logging.debug(f"__cq_main__ logging.info: __name__: {__name__}")

    ctx = Context(
        file_name="rerf-cubes",
        file_format="stl",
        cube_count=1,
        cube_size=2.397,
        tube_size=0.595,
        resolution=resolution,
        layer_height=0.050,
        support_len=5.0,
        base_layers=5,
        position_box_size=[round_to_resolution(5000, resolution), round_to_resolution(2500, resolution)],
        position_box_location=[0, 0],
    )
    logging.debug(f"ctx: {ctx}")

    build_object = doit(ctx.file_name, ctx.file_format, ctx.cube_count, ctx.cube_size, ctx.tube_size)

    show_object(build_object, name=ctx.file_name)
else:
    logging.info(f"Unreconized __name__: {__name__}")
