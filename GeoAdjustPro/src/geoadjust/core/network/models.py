from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class NetworkPoint:
    point_id: str
    coord_type: Literal['FIXED', 'APPROXIMATE', 'FREE']
    x: float
    y: float
    h: Optional[float]
    sigma_x_apriori: float = 0.0
    sigma_y_apriori: float = 0.0
    sigma_h_apriori: float = 0.0
    sigma_x: float = 0.0
    sigma_y: float = 0.0
    sigma_h: float = 0.0
    normative_class: Optional[str] = None

@dataclass
class Observation:
    obs_id: str
    obs_type: Literal['direction', 'distance', 'height_diff', 'gnss_vector']
    from_point: str
    to_point: str
    value: float
    instrument_name: str
    sigma_apriori: Optional[float]
    is_active: bool = True
    weight_multiplier: float = 1.0