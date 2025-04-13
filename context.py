from dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class Context:
    file_name: str
    file_format: str
    cube_count: int
    cube_size: float
    tube_size: float
    resolution: float
    layer_height: float
    support_len: float
    base_layers: int
    position_box_size: list[float, float]
    position_box_location: list[float, float]
