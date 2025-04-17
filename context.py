from dataclasses import dataclass

# TODO: Removed frozen=True as I'm currrently updating, revisit!
# TODO: Add x, y, z resolution to the context class and pass as a parameter
@dataclass(kw_only=True)
class Context:
    file_name: str
    file_format: str
    row_count: int
    col_count: int
    cube_size: float
    tube_size: float
    resolution: float
    layer_height: float
    support_len: float
    base_layers: int
    position_box_size_pixels: list[float, float]
    position_box_location: list[float, float]
