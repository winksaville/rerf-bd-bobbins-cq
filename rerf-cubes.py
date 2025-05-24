#!/usr/bin/env python3

# Rerf generator for braille dot solenoids
# Note: rerf and R_E_R_F are short for "Resin Exposure Range Finder"

import argparse
import logging
import cadquery as cq
import sys

from context import Context
from cadquery.vis import show

VERSION = "1.0.0"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


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


def generate_shape(ctx: Context, row_col: int, cube_size: float, tube_length: float, tube_hole_diameter: float, tube_wall_thickness: float, rerf_number=None) ->   cq.Workplane:
    """
    Generates a shape with text inscriptions on specified faces.

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        row_col (int): The row column number to engrave on the <Y face.
        cube_size (float): The size of the cube to engrave on the >X face.
        tube_length (float): The length of the tube between the two cubes.
        tube_hole_diameter (float): The diameter of the hole in the tube and cube.
        tube_wall_thickness (float): The wall thickness of the tube.
        rerf_number (Optional): The rerf number to engrave on the >Y face, not printed if None

    Returns:
        CadQuery object representing the final shape.
    """

    # Create the upper cube centered with base on the XY plane
    upper_cube = cq.Workplane("XY").box(cube_size, cube_size, cube_size, centered=(True, True, False))

    # Move the upper cube to its final position relative to the base cube
    upper_cube_z = round_to_resolution(cube_size + tube_length, ctx.layer_height)
    upper_cube = upper_cube.translate((0, 0, upper_cube_z))
    #show(upper_cube, title=f"upper_cube: cube_size: {cube_size:5.3f} upper_cube_z: {upper_cube_z:5.3f}")

    # Prepare formatted text with three significant digits
    rerf_number_text = f"{rerf_number}"
    row_col_text = f"{row_col:02d}"
    cube_size_text = f"{cube_size:5.3f}"
    tube_hole_diameter_text = f"{tube_hole_diameter:5.3f}"

    htext = round_to_resolution(0.8, ctx.layer_height)
    distance = round_to_resolution(0.1, ctx.bed_resolution)

    def make_text(s, htext):
        def callback(wp):
            ## Protuding text
            #wp = wp.workplane(centerOption="CenterOfMass").text(
            #    s, htext, distance, cut=False, combine='a', font="RobotoMono Nerd Font")

            # Recessed text
            wp = wp.workplane(centerOption="CenterOfMass").text(
                s, htext, -distance, combine='cut', font="RobotoMono Nerd Font")
            return wp

        return callback

    # Add text into the respective faces
    upper_cube = upper_cube.faces(">X").invoke(make_text(cube_size_text, htext))
    upper_cube = upper_cube.faces("<X").invoke(make_text(tube_hole_diameter_text, htext))
    if rerf_number:
        upper_cube = upper_cube.faces(">Y").invoke(make_text(rerf_number_text, htext * 2.0))
    upper_cube = upper_cube.faces("<Y").invoke(make_text(row_col_text, htext * 2.0))
    #show(upper_cube, title=f"upper_cube: with_text cube_size: {cube_size:5.3f} upper_cube_z: {upper_cube_z:5.3f}")

    # Create the base cube centered at (0,0,0) with base on the XY plane
    base_cube = cq.Workplane("XY").box(cube_size, cube_size, cube_size, centered=(True, True, False))

    # Create the tube between the two cubes with half of the overlap in the base and upper cubes
    tube_full_length = round_to_resolution(tube_length + ctx.overlap, ctx.layer_height)
    tube_radius = round_to_resolution((tube_hole_diameter + (tube_wall_thickness * 2)) / 2, ctx.bed_resolution)

    # Base of tube is on the XY plane
    tube = cq.Workplane("XY").circle(tube_radius).extrude(tube_full_length)

    # Move the tube from the XY plane to the top of the base cube
    # but with half of the overlap into the base cube
    tube_z = round_to_resolution(cube_size - (ctx.overlap / 2), ctx.layer_height)
    tube = tube.translate((0, 0, tube_z))
    #show(tube, title=f"tube overlap: {ctx.overlap:5.3f}, tube_full_length: {tube_full_length:5.3f}, tube_radius: {tube_radius:5.3f}")

    # Union the upper cube and the tube and the base cube
    shape = base_cube.union(tube).union(upper_cube)
    #show(shape, title="shape")

    # Create a hole through the shape
    shape = shape.faces(">Z").workplane(centerOption="CenterOfMass").hole(tube_hole_diameter)
    #show(shape, title="shape with hole")

    # Shape on the XY plane with the bottom at z=0
    return shape

def support_pillar_base_cube(ctx: Context, support_len: float, support_diameter: float, support_tip_diameter: float):
    """
    Creates a support pillar with a base and a tip.

    Created with the help of ChatGPT:
        https://chatgpt.com/share/67f8446f-77b4-800c-ba3c-30de5b676896

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        support_len (float): The length of the support pillar.
        support_diameter (float): The diameter of the base of the support.
        support_tip_diameter (float): The diameter of the tip of the support.
    Returns:
        CadQuery object representing a support pillar.
        Located on the XY plane with the bottom at z=0.
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

def generate_square_support_base(ctx: Context, base_size: float, base_height: float) -> cq.Workplane:
    """
    Generates a square support base with tappered edges
    so it's easier to pry off the build plate.

    Created with the help of ChatGPT:
        https://chatgpt.com/share/67f84393-dd80-800c-8a29-d3d0e446f434)

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        base_size (float): The size of the base.
        base_layers (float): The number of layers for the base.

    Returns:
        CadQuery object representing the square base
        sitting on the xy plane with the bottom at z=0.
    """
    # Calculate the base height and the top is full sized
    top_size = base_size

    # The bottom is smaller than the top and will have a 45 degree slope
    # so it's easier to pry off the build plate
    bottom_size = top_size - (base_height * 2)

    # Create the base and top squares
    bottom = cq.Workplane("XY").rect(bottom_size, bottom_size).workplane(offset=base_height)
    top = bottom.rect(top_size, top_size).clean()

    # Create the solid by lofting between the bottom and top squares
    base = top.loft().clean()

    return base.clean()


def generate_base_cube_supports(
        ctx: Context,
        cube_size: float,
        support_len: float,
        support_base_diameter: float,
        support_tip_diameter: float):
    """
    Generates a support structure for the cube.

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        cube_size (float): The size of the cube, use to position supports beneath cube.
        support_len (float): The length of the support structure.
        support_base_diameter (float): The diameter of the base of the support.
        support_tip_diameter (float): The diameter of the tip of the support.

    Returns:
        CadQuery object representing the supports for the base cube.
        Located on the XY plane with the bottom at z=0.
    """

    # The support pillar is the length of the support includes the base_height
    # so we exclude it but we add the fudge so there is significant overlap between
    # the cube and the base.
    support_radius = support_base_diameter / 2
    support_loc_offset = (cube_size / 2) - support_radius

    support1 = support_pillar_base_cube(ctx, support_len, support_base_diameter, support_tip_diameter).clean()
    support1 = support1.translate((-support_loc_offset, -support_loc_offset, 0))
    support2 = support_pillar_base_cube(ctx, support_len, support_base_diameter, support_tip_diameter).clean()
    support2 = support2.translate((support_loc_offset, -support_loc_offset, 0))
    support3 = support_pillar_base_cube(ctx, support_len, support_base_diameter, support_tip_diameter).clean()
    support3 = support3.translate((0, support_loc_offset, 0))
    
    # Union the base and support
    supports = support1.add(support2).add(support3).clean()

    return supports

def generate_upper_cube_supports(ctx: Context, support_diameter: float, support_tip_diameter: float):
    """
    Creates a support pillar for upper cube with a base and a tip.

    Created with the help of ChatGPT:
        https://chatgpt.com/share/67f8446f-77b4-800c-ba3c-30de5b676896

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
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


def export_model(ctx: Context, model: cq.Workplane, file_name: str, file_format) -> None:
    """
    Exports the given CadQuery model to a file in the specified format.

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        model (cq.Workplane): The CadQuery model to export.
        file_name (str): The base name of the output file (without extension).
        file_format (str): The format to export the model ('stl' or 'step').

    Returns:
        None
    """

    if file_format.lower() == "stl":
        # TODO: Allow ascii=True/False to be passed as a parameter
        cq.Assembly(model).export(file_name + ".stl", exportType="STL", ascii=True)
    elif file_format.lower() == "step":
        cq.exporters.export(model, file_name + ".step")
    else:
        print("Unsupported format. Use 'stl' or 'step'.", file=sys.sdterr)

def generate_shape_with_support(ctx: Context, row_count: int, col_count: int, rerf_number=None) -> cq.Workplane:
    """
    Generates one or more shapes with support as specified by row_count and col_count.

    Each shape is placed in a grid pattern within the specified context position box.
    The shapes are positioned so that they are centered within the context position box.
    The shapes are also supported by a support structure.
    The function returns the final 3D object.

    Parameters:
        ctx (Context): The context object containing overall parameters for the model.
        column_count (int): The number of columns to create.
        row_count (int): The number of rows to create.
        rerf_number (None): The rerf number to engrave on the >Y face, not printed if <= 0.
    Returns:
        cq.Workplane: The final 3D object representing the cubes and support structures.
    """
    support_len_base_cube = ctx.zlift_height
    support_diameter = round_to_resolution(0.75, ctx.bed_resolution)
    support_tip_diameter = round_to_resolution(0.3, ctx.bed_resolution)

    position_box_width = round_to_resolution(ctx.position_box_size[0], ctx.bed_resolution)
    position_box_height = round_to_resolution(ctx.position_box_size[1], ctx.bed_resolution)

    # Problem: cube_size_half may not be an integer multiple of the bed_resolution
    # unless the bed_resolution is a factor of the cube_size_half which can be accomplished
    # having the cube_size be an even number of bed_resolution in size
    cube_size_half = round_to_resolution(ctx.cube_size / 2, ctx.bed_resolution)
    print(f"position_box_width: {position_box_width:5.3f}, position_box_height: {position_box_height:5.3f}, cube_size_half: {cube_size_half:5.3f}")

    x_initial = cube_size_half
    y_initial = cube_size_half
    x_step = round_to_resolution((position_box_width - ctx.cube_size) / col_count, ctx.bed_resolution)
    y_step = round_to_resolution((position_box_height - ctx.cube_size) / row_count, ctx.bed_resolution)
    print(f"x_initial: {x_initial:5.3f}, y_initial: {y_initial:5.3f}, x_step: {x_step:5.3f}, y_step: {y_step:5.3f}")
    for col in range(col_count):
        x = round_to_resolution(x_initial + (x_step * col), ctx.bed_resolution)
        for row in range(row_count):
            y = round_to_resolution(y_initial + (y_step * row), ctx.bed_resolution)

            # Cube number is 2 digits first digit is the row second is the column
            row_col = (row * 10) + col
            print(f"rerf_number: {rerf_number} row_col: {row_col:02d} x: {x:5.3f}, y: {y:5.3f}")

            # Generate the shape
            shape = generate_shape(ctx, row_col, ctx.cube_size, ctx.tube_length, ctx.tube_hole_diameter, ctx.tube_wall_thickness, rerf_number)
            #show(shape, title="shape")

            # Generate base
            base_height = ctx.base_layers * ctx.layer_height
            base = generate_square_support_base(ctx, ctx.cube_size * 2, base_height)
            #show(base, title="base")

            # Create the base cube support structure
            base_cube_support_len = ctx.zlift_height - base_height + (ctx.overlap * 2)
            base_cube_supports = generate_base_cube_supports(ctx, ctx.cube_size, base_cube_support_len, support_diameter, support_tip_diameter)
            #show(base_cube_supports, title="base_cube_supports")

            # Create the upper cube support structure
            #zloc_bottom_upper_cube = round_to_resolution(base_height + support_len_base_cube + ctx.cube_size, ctx.layer_height)
            #print(f"zloc_bottom_upper_cube: {zloc_bottom_upper_cube:5.3f}")
            #upper_cube_supports = generate_upper_cube_supports(ctx, ctx.cube_size, zloc_bottom_upper_cube, support_diameter, support_tip_diameter)
            #shape = shape.add(upper_cube_supports)

            # Place the base cube support structure on the base
            base_cube_supports = base_cube_supports.translate((0, 0, base_height - ctx.overlap))

            # Place the shape on the support structure
            shape = shape.translate((0, 0, ctx.zlift_height))

            # Merge the shape, base_supports ,  cube and the support structure
            shape = base.add(base_cube_supports).add(shape)

            # Move the shape to the specified position on XY plane (i.e. z=0)
            shape = shape.translate((x, y, 0))

            if col == 0 and row == 0:
                build_object = shape
            else:
                build_object = build_object.add(shape)

    # Translate the build object to the specified position if not at (0,0)
    if ctx.position_box_location[0] > 0.0 and ctx.position_box_location[1] > 0.0:
        print(f"position_box_location_x: {ctx.position_box_location[0]:5.3f}, position_box_location_y: {ctx.position_box_location[1]:5.3f}")
        build_object = build_object.translate((ctx.position_box_location[0], ctx.position_box_location[1], 0))

    if ctx.file_name != "":
        # The user wants to output a file for this sets objects

        # Formate We are going to export the object shape a file
        size_in_mm = ctx.position_box_size[0], ctx.position_box_size[1]
        location_in_mm = [(ctx.position_box_location[0]), (ctx.position_box_location[1])]
        if ctx.rerf:
            if ctx.file_name.__contains__("_rerf_rc-") == False:
                # Update the file name for the rerf build only once
                ctx.file_name = f"{ctx.file_name}_rerf_rc-{ctx.row_count}_cc-{ctx.col_count}_lh-{ctx.layer_height:5.3f}"
        else:
            # If location is not (0,0) add it to the file name
            if (location_in_mm[0] > 0.0) or (location_in_mm[1] > 0.0):
                pos_in_mm_str = f"_pos-{location_in_mm[0]:5.3f}-{location_in_mm[1]:5.3f}"
            else:
                pos_in_mm_str = ""

            # Initialize the file name for the object
            ctx.file_name = f"{ctx.file_name}_cz-{ctx.cube_size:5.3f}_tl-{ctx.tube_length:5.3f}_thd-{ctx.tube_hole_diameter:5.3f}_twt-{ctx.tube_wall_thickness:5.3f}_rc-{ctx.row_count}_cc-{ctx.col_count}_lh-{ctx.layer_height:5.3f}_box-{size_in_mm[0]:5.3f}x{size_in_mm[1]:5.3f}{pos_in_mm_str}"

    return build_object

default_layer_height = 0.050
default_bed_resolution = 0.017
default_bed_size = (9024 * default_bed_resolution, 5120 * default_bed_resolution)
default_cube_size = round_to_resolution(2.4, default_bed_resolution) # Make multiple of bed_resolution
default_tube_length= round_to_resolution(3 * 2.4, default_layer_height) # Make multiple of layer_height
default_tube_hole_diameter = round_to_resolution(0.714, default_bed_resolution) # Make multiple of bed_resolution
default_tube_wall_thickness = round_to_resolution(0.2, default_bed_resolution) # Make multiple of bed_resolution
default_overlap = round_to_resolution(default_layer_height * 2.0, default_layer_height) # Make multiple of layer_height
default_base_layers = 10 # Change to mm and then calculate the number of layers
default_zlift_height = 5
default_position_box_width = round_to_resolution(5000 * default_bed_resolution, default_bed_resolution)
default_position_box_height = round_to_resolution(2500 * default_bed_resolution, default_bed_resolution)
default_position_box_location_x = 0
default_position_box_location_y = 0
default_rerf = False
default_show = False

if __name__ == "__main__":
    logging.debug(f"__main__ logging.info: __name__: {__name__}")

    def row_col_checker(value: str) -> int:
        """
        Custom type checker for row and column counts.
        Ensures the value is an integer greater than or equal to 1.
        """
        try:
            ivalue = int(value)
            if ivalue < 1 or ivalue > 10:
                raise argparse.ArgumentTypeError(f"{ivalue} is not a valid row/column count (must be >= 1 <= 10)")
            return ivalue
        except ValueError:
            raise argparse.ArgumentTypeError(f"{ivalue} is not a valid row/column count (must be >= 1 <= 10")

    parser = argparse.ArgumentParser(
        description=f"rerf-cubes v{VERSION} Generate 3D cubes with text inscriptions.",
        epilog=f"Version: {VERSION}"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s v{VERSION}")
    parser.add_argument("filename", type=str, help="Name of the output file (without extension)")
    parser.add_argument("format", type=str, choices=["stl", "step"], help="Format to export the model ('stl' or 'step')")
    parser.add_argument("row_count", type=row_col_checker, help="Number of rows to create (>= 1)")
    parser.add_argument("col_count", type=row_col_checker, help="Number of columns to create (>= 1)")
    parser.add_argument("-cs", "--cube_size", type=float, default=default_cube_size, help=f"Cube size engraved on the +X face, defaults to {default_cube_size:5.3f}")
    parser.add_argument("-tl", "--tube_length", type=float, default=default_tube_length, help=f"Tube length defaults to {default_tube_length:5.3f}")
    parser.add_argument("-thd", "--tube_hole_diameter", type=float, default=default_tube_hole_diameter, help=f"Tube hole diameter engraved on the -X face, defaults to {default_tube_hole_diameter:5.3f}")
    parser.add_argument("-twt", "--tube_wall_thickness", type=float, default=default_tube_wall_thickness, help=f"Tube wall thickness, defaults to {default_tube_wall_thickness:5.3f}")
    parser.add_argument("-br", "--bed_resolution", type=float, default=default_bed_resolution, help=f"resolution of the printer bed, defaults to {default_bed_resolution}")
    parser.add_argument("-bs", "--bed_size", type=float, default=default_bed_size, help=f"size of the bed, defaults to ({default_bed_size[0]:5.3f}, {default_bed_size[1]:5.3f})")
    parser.add_argument("-lh", "--layer_height", type=float, default=default_layer_height, help=f"Layer height for this print, defaults to {default_layer_height:5.3f}")
    parser.add_argument("-bl", "--base_layers", type=int, default=default_base_layers, help=f"Number of layers for the base, defaults to {default_base_layers}")
    parser.add_argument("-zl", "--zlift_height", type=float, default=default_zlift_height, help="Height from bed to bottom of the solenoid base, defaults to {default_zlift_height}")
    parser.add_argument("-ol", "--overlap", type=float, default=default_overlap, help=f"Overlap between two objects, defaults to {default_overlap:5.3f}")
    parser.add_argument("-pbsp", "--position_box_size", type=float, nargs=2, default=[default_position_box_width, default_position_box_height], metavar=('width', 'height'), help=f"Size of box to disperse the solenoids into, defaults to ({default_position_box_width}, {default_position_box_height})")
    parser.add_argument("-pbl", "--position_box_location", type=float, nargs=2, default=[default_position_box_location_x, default_position_box_location_y], metavar=('x', 'y'), help=f"Location of position_box, defaults to ({default_position_box_location_x}, {default_position_box_location_y})")
    parser.add_argument("-re", "--rerf", type=bool, action=argparse.BooleanOptionalAction, default=default_rerf, help=f"If true generate 8 objects in R_E_R_F orientation, defaults to {default_rerf}")
    parser.add_argument("-s", "--show", type=bool, action=argparse.BooleanOptionalAction, default=default_show, help="Show the created object in the viewer")

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

    # Parse the command line arguments
    args = parser.parse_args()

    # Initialize the context with the parsed arguments
    ctx = Context(
        version=VERSION,
        file_name=args.filename,
        file_format=args.format,
        row_count=args.row_count,
        col_count=args.col_count,
        cube_size=args.cube_size,
        tube_length=args.tube_length,
        tube_hole_diameter=args.tube_hole_diameter,
        tube_wall_thickness=args.tube_wall_thickness,
        bed_resolution=args.bed_resolution,
        bed_size=args.bed_size,
        layer_height=args.layer_height,
        overlap=args.overlap,
        base_layers=args.base_layers,
        zlift_height=args.zlift_height,
        position_box_size=[args.position_box_size[0], args.position_box_size[1]],
        position_box_location=[args.position_box_location[0], args.position_box_location[1]],
        rerf=args.rerf,
        show=args.show,
    )
    logging.debug(f"ctx: {ctx}")

    if ctx.rerf:
        print("Generating 8 sets of R_E_R_F cubes with rerf_numbers 1 .. 8")

        # Generate ctx.row_count * ctx.col_count number of 3D objects in each position box
        # of in a R_E_R_F set. A R_E_R_F is a 2x4 grid. The idea is that each position box
        # has a different exposure time and the upper left corner has the shortest exposure
        # and the lower right corner has the longest exposure. The rerf_number for all the
        # objects in a particular R_E_R_F grid and will be 1 .. 8.

        # The sequential_to_printer_order is a two dimensional array of printers, the
        # first dimension is the printer idx and the second is the arrangement order.
        # Currently we only have one printer, the Anycubic Mono 4, which is a simple reversal
        any_cubic_mono_4 = 0
        current_printer = any_cubic_mono_4
        sequential_to_printer_order = [
            [8, 7, 6, 5, 4, 3, 2, 1] # Anycubic Mono 4 is a simple reversal
        ]

        # Were going to generate 2 rows with and 4 columns of
        # build_objects positioning them on the build plate
        rerf_number_rows = 2
        rerf_number_cols = 4

        # There will be rerf_number_rows * rerf_number_cols number of rerf objects
        # We'll calculate the length of x and y for each position box and use 90%:
        position_box_size_x = (ctx.bed_size[0] / rerf_number_cols) * 0.9
        position_box_size_y = (ctx.bed_size[1] / rerf_number_rows) * 0.9

        # Round the position box size to the nearest multiple of the bed resolution
        ctx.position_box_size[0] = round_to_resolution(position_box_size_x, ctx.bed_resolution)
        ctx.position_box_size[1] = round_to_resolution(position_box_size_y, ctx.bed_resolution)

        # Calculate the step size for the X and Y positions
        rerf_x_step = ctx.bed_size[0] / (rerf_number_cols)
        rerf_y_step = ctx.bed_size[1] / (rerf_number_rows)

        # Calculate the initial X position for the first column
        rerf_x_initial = ctx.bed_size[0] / (rerf_number_rows * 2)
        rerf_y_initial = ctx.bed_size[1] / (rerf_number_cols * 2)

        for rerf_number_col in range(rerf_number_cols):
            # Calculate initial Y position for this row
            x = round_to_resolution(rerf_x_initial + (rerf_number_col * rerf_x_step), ctx.bed_resolution)
            for rerf_number_row in range(rerf_number_rows):

                # Calcuate the position for this set of cubes
                y = round_to_resolution(rerf_y_initial + (rerf_number_row * rerf_y_step), ctx.bed_resolution)
                ctx.position_box_location[0] = x
                ctx.position_box_location[1] = y

                # Sequential order is print both rows in rerf_number_col and then advance to next column
                # Logical Layout of our sequential order
                #   0, 2, 4, 6
                #   1, 3, 5, 7
                # This maps to the order needed for the current
                sequential_order = (rerf_number_col * rerf_number_rows) + rerf_number_row
                rerf_number = sequential_to_printer_order[current_printer][sequential_order]
                print(f"sequential_order: {sequential_order} rerf_number: {rerf_number}")

                # Generate the cubes
                bo = generate_shape_with_support(ctx, ctx.row_count, ctx.col_count, rerf_number)

                # Group them into a single object
                if rerf_number_col == 0 and rerf_number_row == 0:
                    build_object = bo
                else:
                    build_object = build_object.add(bo)
    else:
        print("Generating one set of objects with no rerf_number")
        # Generate only one 3D object in each position box using the specified number of rows and columns
        # and export it to the specified file format
        build_object = generate_shape_with_support(ctx, ctx.row_count, ctx.col_count, rerf_number=None)

    # Export the file if a file name is provided
    if ctx.file_name != "":
        # Export the object to the specified file name and file format defined in ctx
        export_model(ctx, build_object, ctx.file_name, ctx.file_format)

    # Show the object in the viewer if the show flag is set
    if ctx.show:
        show(build_object)
elif __name__ == "__cq_main__":
    logging.debug(f"__cq_main__ logging.info: __name__: {__name__}")

    # Initialize the context with default values
    default_bed_resolution = 0.017
    ctx = Context(
        file_name="rerf-cubes",
        file_format="stl",
        row_count=3,
        col_count=3,
        cube_size=default_cube_size,
        tube_hole_diameter=default_tube_hole_diameter,
        bed_resolution=default_bed_resolution,
        bed_size=default_bed_size,
        layer_height=default_layer_height,
        overlap=default_overlap,
        base_layers=default_base_layers,
        position_box_size=[default_position_box_width, default_position_box_height],
        position_box_location=[default_position_box_location_x, default_position_box_location_y],
        rerf=default_rerf,
        show=default_show,
    )
    logging.debug(f"ctx: {ctx}")

    # Generate the 3D objects using the specified number of rows and columns
    # and use the cadquery show_object function to display it
    build_object = generate_shape_with_support(ctx, ctx.row_count, ctx.col_count)
    show_object(build_object, name=ctx.file_name)
else:
    logging.info(f"Unreconized __name__: {__name__}")
