#!/usr/bin/env python3
import logging
import cadquery as cq
import sys

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

    htext =0.697
    dcut = 0.102

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

def generate_build_object(cube_number: int, cube_size: float, tube_size: float):
        logging.info(f"generate_build_object: cube_number: {cube_number}")

        # build plate size in pixels
        resolution = 0.017
        layer_height = 0.030
        base_layers = 6
        support_len = 5.0
        support_diameter = round_to_resolution(0.75, resolution)
        support_tip_diameter = round_to_resolution(0.3, resolution)

        support = generate_support(layer_height, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)
        cube = generate_cube(cube_number, cube_size, tube_size)
        cube = cube.translate((0, 0, support_len))
        build_object = cube.add(support)

        ## Additional variables for mulitple cubes
        #pixels_per_mm = 1 / 0.017
        #build_plate_width = 9024 / pixels_per_mm
        #build_plate_height = 5120 / pixels_per_mm
        #cube_size_half = cube_size / 2

        ## Postion so the cube is in the upper left corner of build plate
        #cube1 = generate_cube(cube_number, cube_size, tube_size)
        #cube1 = cube1.translate((cube_size_half, cube_size_half, 0))
        #cube1_support = generate_support(0.050, cube_size, base_layers, support_len, support_diameter, support_tip_diameter)

        ## Postion so the cube is in the lower left corner of build plate
        #cube2 = generate_cube(cube_number + 1, cube_size, tube_size)
        #cube2 = cube2.translate((cube_size_half, build_plate_height - cube_size_half, 0))

        ## Postion so the cube is in the upper right corner of build plate
        #cube3 = generate_cube(cube_number + 2, cube_size, tube_size)
        #cube3 = cube3.translate((build_plate_width - cube_size_half, cube_size_half, 0))

        ## Postion so the cube is in the lower right corner of build plate
        #cube4 = generate_cube(cube_number + 3, cube_size, tube_size)
        #cube4 = cube4.translate((build_plate_width - cube_size_half, build_plate_height - cube_size_half, 0))

        ## Create the build object by uniting the four cubes
        #build_object = cube1.add(cube2).add(cube3).add(cube4)

        return build_object

def doit(file_name: str, file_format: str, cube_number: int, cube_size: float, tube_size: float):
    """
    Generates a 3D model of cubes with text inscriptions and exports it to a file.
    Parameters:
        file_name (str): The name of the output file (without extension).
        file_format (str): The format to export the model ('stl' or 'step').
        cube_number (int): The cube number to engrave on the +Y face.
        cube_size (float): The size of the cube to engrave on the +X face.
        tube_size (float): The tube size to engrave on the -X face.
    Returns:
        CadQuery object representing the final model.
    """
    build_object = generate_build_object(cube_number, cube_size, tube_size)
    export_model(build_object, file_name, file_format)
    return build_object


if __name__ == "__main__":
    logging.info(f"__main__ logging.info: __name__: {__name__}")
    print(f"__main__ logging.info: __name__: {__name__}")

    if len(sys.argv) != 6:
        print("Usage: rerf-cubes <filename> <format> <cube_number> <cube_size> <tube_size>")
        print("Example: ./rerf-cube my_cube stl 1 2.397 0.595")
    else:
        file_name = sys.argv[1]
        file_format = sys.argv[2]
        cube_number = int(sys.argv[3])
        cube_size = float(sys.argv[4])
        tube_size = float(sys.argv[5])
        layer_height = 0.050
        support_len = 5.0
        base_layers = 5

        build_object = doit(file_name, file_format, cube_number, cube_size, tube_size)
elif __name__ == "__cq_main__":
    logging.info(f"__cq_main__ logging.info: __name__: {__name__}")

    #file_name = "boxes-at-corners"
    file_name = "supported_cube"
    file_format = "stl"
    cube_number = 1
    layer_height = 0.030
    base_layers = 5
    cube_size = 2.397
    tube_size = 0.595
    support_len = 5.0

    build_object = doit(file_name, file_format, cube_number, cube_size, tube_size)

    show_object(build_object, name=file_name)
else:
    logging.info(f"Unreconized __name__: {__name__}")
