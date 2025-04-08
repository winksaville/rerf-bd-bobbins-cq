#!/usr/bin/env python3
import cadquery as cq
import sys

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
        cq.exporters.export(model, filename + ".stl")
        #print(f"Exported as {filename}.stl")
    elif file_format.lower() == "step":
        cq.exporters.export(model, filename + ".step")
        #print(f"Exported as {filename}.step", file=sys.stderr)
    else:
        print("Unsupported format. Use 'stl' or 'step'.", file=sys.sdterr)


if __name__ == "__main__":
    # Output to stdout,$
    #   "print: __name__: __cq_main__"
    print(f"print: __name__: {__name__}")

    if len(sys.argv) != 6:
        print("Usage: rerf-cubes <filename> <format> <cube_number> <cube_size> <tube_size>")
        print("Example: ./rerf-cube my_cube stl 1 2.397 0.595")
    else:
        filename = sys.argv[1]
        file_format = sys.argv[2]
        cube_number = int(sys.argv[3])
        cube_size = float(sys.argv[4])
        tube_size = float(sys.argv[5])

        cube = generate_cube(cube_number, cube_size, tube_size)
        export_model(cube, filename, file_format)
elif __name__ == "__cq_main__":
    # Output to Log viewer window on cq-editor
    #   "[ 15:25:16] INFO: log: __name__: __cq_main__"
    log(f"log: __name__: {__name__}")

    filename = "cubex"
    file_format = "stl"
    cube_number = "x"
    cube_size = 2.397
    tube_size = 0.595

    cube = generate_cube(cube_number, cube_size, tube_size)
    export_model(cube, filename, file_format)

    show_object(cube, name=filename)
else:
    print(f"Unreconized __name__: {__name__}")
