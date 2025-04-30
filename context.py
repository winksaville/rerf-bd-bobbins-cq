from dataclasses import dataclass

# TODO: Removed frozen=True as I'm currrently updating, revisit!
# TODO: Add x, y, z resolution to the context class and pass as a parameter
@dataclass(kw_only=True)
class Context:
    version: str
    file_name: str
    file_format: str
    row_count: int
    col_count: int
    cube_size: float
    tube_length: float # Length of the tube between the two cubes
    tube_hole_diameter: float # Diameter of the hole in the tube and cube
    tube_wall_thickness: float
    bed_resolution: float # TODO change to tuple[float, float] for x, y
    bed_size: tuple[float, float] # multiple of bed_resolution
    layer_height: float
    support_len: float
    base_layers: int
    position_box_size: tuple[float, float]
    position_box_location: tuple[float, float]
    rerf: bool
    show: bool
