from dataclasses import dataclass, field
from typing import Literal, Optional, List, Union, Any
import numpy as np

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
    # Географические координаты для работы с геоидом
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@dataclass
class Observation:
    obs_id: str
    obs_type: Literal['direction', 'distance', 'height_diff', 'gnss_vector', 'azimuth', 'vertical_angle', 'zenith_angle']
    from_point: str
    to_point: str
    value: float
    instrument_name: str
    sigma_apriori: Optional[float]
    is_active: bool = True
    weight_multiplier: float = 1.0
    
    # Расширенные атрибуты для ГНСС векторов (поддержка полной ковариационной матрицы)
    delta_x: Optional[float] = None
    delta_y: Optional[float] = None
    delta_z: Optional[float] = None
    sigma_x: Optional[float] = None
    sigma_y: Optional[float] = None
    sigma_z: Optional[float] = None
    covariance_matrix: Optional[Union[List[List[float]], np.ndarray]] = None
    
    # Атрибуты для угловых измерений
    angle_unit: Literal['degrees', 'radians', 'gons'] = 'degrees'
    reception_number: Optional[int] = None
    datetime: Optional[Any] = None
    
    # Атрибуты для превышений
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    num_stands: Optional[int] = None
    
    # Атрибуты для линейных измерений
    temperature: Optional[float] = None
    pressure: Optional[float] = None