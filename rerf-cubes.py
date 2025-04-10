#!/usr/bin/env python3
import logging
import cadquery as cq
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


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

    htext =0.7
    dcut = 0.1

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

def export_model(model, filename, file_format):
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
        cq.Assembly(model).export(filename + ".stl", exportType="STL", ascii=True)
        #print(f"Exported as {filename}.stl")
    elif file_format.lower() == "step":
        cq.exporters.export(model, filename + ".step")
        #print(f"Exported as {filename}.step", file=sys.stderr)
    else:
        print("Unsupported format. Use 'stl' or 'step'.", file=sys.sdterr)

def generate_build_object(cube_number: int, cube_size: float, tube_size: float):
        logging.info(f"generate_build_object: cube_number: {cube_number}")

        # build plate size in pixels
        pixels_per_mm = 1 / 0.017
        build_plate_width = 9024 / pixels_per_mm
        build_plate_height = 5120 / pixels_per_mm
        cube_size_half = cube_size / 2

        # Postion so the cube is in the upper left corner of build plate
        cube1 = generate_cube(cube_number, cube_size, tube_size)
        cube1 = cube1.translate((cube_size_half, cube_size_half, 0))

        # Postion so the cube is in the lower left corner of build plate
        cube2 = generate_cube(cube_number + 1, cube_size, tube_size)
        cube2 = cube2.translate((cube_size_half, build_plate_height - cube_size_half, 0))

        # Postion so the cube is in the upper right corner of build plate
        cube3 = generate_cube(cube_number + 2, cube_size, tube_size)
        cube3 = cube3.translate((build_plate_width - cube_size_half, cube_size_half, 0))

        # Postion so the cube is in the lower right corner of build plate
        cube4 = generate_cube(cube_number + 3, cube_size, tube_size)
        cube4 = cube4.translate((build_plate_width - cube_size_half, build_plate_height - cube_size_half, 0))

        # Create the build object by uniting the four cubes
        build_object = cube1.add(cube2).add(cube3).add(cube4)

        return build_object


if __name__ == "__main__":
    logging.info(f"__main__ logging.info: __name__: {__name__}")
    print(f"__main__ logging.info: __name__: {__name__}")

    if len(sys.argv) != 6:
        print("Usage: rerf-cubes <filename> <format> <cube_number> <cube_size> <tube_size>")
        print("Example: ./rerf-cube my_cube stl 1 2.397 0.595")
    else:
        filename = sys.argv[1]
        file_format = sys.argv[2]
        cube_number = int(sys.argv[3])
        cube_size = float(sys.argv[4])
        tube_size = float(sys.argv[5])

        build_object = generate_build_object(cube_number, cube_size, tube_size)

        export_model(build_object, filename, file_format)
elif __name__ == "__cq_main__":
    logging.info(f"__cq_main__ logging.info: __name__: {__name__}")

    filename = "boxes-at-corners"
    file_format = "stl"
    cube_number = 1
    cube_size = 2.397
    tube_size = 0.595

    build_object = generate_build_object(cube_number, cube_size, tube_size)

    export_model(build_object, filename, file_format)

    show_object(build_object, name=filename)
else:
    logging.info(f"Unreconized __name__: {__name__}")
