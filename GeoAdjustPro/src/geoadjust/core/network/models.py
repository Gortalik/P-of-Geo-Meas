from dataclasses import dataclass, field
from typing import Literal, Optional, List, Union, Any, Dict
from datetime import datetime
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
class InstrumentSetup:
    """
    Одна установка инструмента на пункте
    (может быть несколько на одном пункте с разной ориентировкой)
    """
    setup_id: str                    # Уникальный ID: "P1_SETUP_001"
    point_id: str                    # Имя пункта стояния: "P1"
    instrument_name: str             # Прибор: "Leica TS16"
    instrument_height: float         # Высота инструмента, м
    target_height: float             # Высота цели по умолчанию, м
    orientation_angle: Optional[float] = None  # Ориентировка лимба, градусы
    face_position: Literal['CL', 'CP', 'NONE'] = 'NONE'  # Круг лево/право
    timestamp: Optional[datetime] = None  # Время установки
    atmospheric_params: Dict = field(default_factory=dict)  # T, P, Humidity
    
    # Статус обработки
    is_processed: bool = False
    processing_warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.setup_id is None:
            self.setup_id = f"{self.point_id}_SETUP_{datetime.now().strftime('%H%M%S')}"



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
    
    # Атрибуты для поддержки станций - ОБНОВЛЕНО
    station_id: Optional[str] = None  # Устарело, использовать from_setup_id
    from_setup_id: Optional[str] = None  # Привязка к конкретной установке
    circle_position: Optional[Literal['KL', 'KP', 'CL', 'CP']] = None


@dataclass
class Station:
    """Класс станции для геодезических измерений"""
    station_id: str
    point_name: str
    instrument_height: float
    target_height: float = 0.0
    orientation_angle: Optional[float] = None
    timestamp: Optional[Any] = None
    observations: List[Observation] = field(default_factory=list)
    instrument_name: str = ""
    atmospheric_params: dict = field(default_factory=dict)
    is_processed: bool = False
    
    @property
    def num_directions(self) -> int:
        """Количество направлений на станции"""
        return len([obs for obs in self.observations if obs.obs_type == 'direction'])
    
    @property
    def num_distances(self) -> int:
        """Количество расстояний на станции"""
        return len([obs for obs in self.observations if obs.obs_type == 'distance'])
    
    def get_observation(self, to_point: str) -> Optional[Observation]:
        """Получить измерение на указанную цель"""
        for obs in self.observations:
            if obs.to_point == to_point:
                return obs
        return None
    
    def get_observations_by_type(self, obs_type: str) -> List[Observation]:
        """Получить все измерения указанного типа"""
        return [obs for obs in self.observations if obs.obs_type == obs_type]


@dataclass
class StationGroup:
    """Группа станций на одном пункте"""
    point_name: str
    stations: List[Station] = field(default_factory=list)
    
    def add_station(self, station: Station):
        """Добавить станцию в группу"""
        self.stations.append(station)
    
    def get_unique_orientations(self) -> List[float]:
        """Возвращает уникальные ориентировки лимба"""
        orientations = set()
        for station in self.stations:
            if station.orientation_angle is not None:
                orientations.add(station.orientation_angle)
        return sorted(list(orientations))
    
    def get_total_observations(self) -> int:
        """Общее количество измерений"""
        return sum(len(s.observations) for s in self.stations)
    
    @property
    def num_setups(self) -> int:
        """Количество установок на пункте"""
        return len(self.stations)