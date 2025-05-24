from dataclasses import dataclass

# This is passed as the context to many of the functions
# in the app and it contains the parameters that are
# used to generate the objects.

# TODO: Removed frozen=True as I'm currrently updating, revisit!
# TODO: Add x, y, z resolution to the context class and pass as a parameter
@dataclass(kw_only=True)
class Context:
    version: str
    file_name: str
    file_format: str

    rerf: bool
    # Resin Exposure Range Finder" if rerf True the app will generate
    # row_count * col_count objects in each of 8 grid areas
    # arranged in a 2 x 4 grid. Each grid area has a position_box_location
    # and position_box_size that defines the location and size of the
    # a each grid area.

    row_count: int
    # The number of rows of ojects to generate

    col_count: int
    # The number of columns of objects to generate

    position_box_location: tuple[float, float]
    # The X and Y location (position_box_location[0], position_box_location[1]),
    # of the box which contains the row_coutn * col_count number of objects

    position_box_size: tuple[float, float]
    # Width and Height (position_box_size[0], position_box_size[1]),
    # of a box that contains row_count * col_count number of obects.

    cube_size: float
    # The LxWxH of the top and bottom cube

    tube_length: float
    # The length of the tube connecting the two cubes

    tube_hole_diameter: float
    # Diameter of the hole in the tube and cube

    tube_wall_thickness: float
    # Thickness of the tube wall

    bed_resolution: float
    # The bed resolution, ATM the AnyCubic Mono 4 is the same in X and Y but
    # but this is not always the case and this should be a tuple of X and Y
    # resultions.

    bed_size: tuple[float, float]
    # The size of the bed in X and Y, this is a tuple of (X, Y)

    zlift_height: float
    # The number of millitiers that the bottom of object is above the bed

    layer_height: float
    # The layer height is the vertical resolution of the print

    base_layers: int
    # The number of layers in the base of the object

    overlap: float
    # The distance that one object is buried into the other object

    show: bool
    # True if the final result is to be shown using cq.show
