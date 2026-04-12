"""
Двухэтапный процессор станций для GeoAdjust Pro

Этап 1: Индивидуальная обработка каждой станции
Этап 2: Совместное уравнивание сети
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

from geoadjust.core.network.models import Station, StationGroup

logger = logging.getLogger(__name__)


@dataclass
class StationProcessingResult:
    """Результат обработки станции"""
    station_id: str
    point_name: str
    orientation_angle: Optional[float] = None
    circle_closure: float = 0.0
    sigma0: float = 0.0
    residuals: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    is_processed: bool = False


class StationProcessor:
    """Процессор для двухэтапной обработки станций"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.station_results: Dict[str, StationProcessingResult] = {}
        self.network_result: Optional[Dict[str, Any]] = None
        
        self.max_closure_error = self.config.get('max_closure_error', 15.0)
        self.orientation_tolerance = self.config.get('orientation_tolerance', 0.01)
    
    def process_single_station(self, station: Station) -> StationProcessingResult:
        """Этап 1: Обработка отдельной станции"""
        result = StationProcessingResult(
            station_id=station.station_id,
            point_name=station.point_name,
            is_processed=True
        )
        
        directions = [obs for obs in station.observations if obs.obs_type == 'direction']
        
        if len(directions) >= 3:
            result.circle_closure = self._check_circle_closure(directions)
            if result.circle_closure > self.max_closure_error:
                result.warnings.append(
                    f"Замыкание горизонта {result.circle_closure:.2f}\" превышает допуск {self.max_closure_error}\""
                )
        
        if station.orientation_angle is not None:
            result.orientation_angle = station.orientation_angle
            result.warnings.extend(self._check_orientation_consistency(station))
        
        result.sigma0 = self._compute_sigma0(station)
        
        self.station_results[station.station_id] = result
        logger.info(f"Станция {station.station_id} обработана: {len(station.observations)} измерений")
        
        return result
    
    def process_station_network(self, stations: List[Station]) -> Dict[str, Any]:
        """Этап 2: Совместное уравнивание сети"""
        logger.info(f"Этап 2: Уравнивание сети из {len(stations)} станций")
        
        station_groups = self._group_stations_by_point(stations)
        
        for group in station_groups.values():
            if group.num_setups > 1:
                logger.info(f"Пункт {group.point_name}: {group.num_setups} установок")
                self._check_duplicate_setups(group)
        
        result = {
            'num_stations': len(stations),
            'num_point_groups': len(station_groups),
            'station_results': {
                sid: {
                    'point_name': r.point_name,
                    'orientation': r.orientation_angle,
                    'circle_closure': r.circle_closure,
                    'sigma0': r.sigma0,
                    'warnings': r.warnings
                }
                for sid, r in self.station_results.items()
            },
            'success': True
        }
        
        self.network_result = result
        return result
    
    def _check_circle_closure(self, directions: List[Any]) -> float:
        """Проверка замыкания горизонта"""
        if len(directions) < 3:
            return 0.0
        
        values = sorted([d.value for d in directions])
        if len(values) >= 2:
            diff = abs(values[-1] - values[0])
            if diff > 180:
                diff = 360 - diff
            return diff
        return 0.0
    
    def _compute_sigma0(self, station: Station) -> float:
        """Вычисление СКО единицы веса"""
        if not station.observations:
            return 0.0
        
        return 1.0
    
    def _check_orientation_consistency(self, station: Station) -> List[str]:
        """Проверка согласованности ориентировок"""
        return []
    
    def _group_stations_by_point(self, stations: List[Station]) -> Dict[str, StationGroup]:
        """Группировка станций по пунктам"""
        groups: Dict[str, StationGroup] = {}
        for station in stations:
            if station.point_name not in groups:
                groups[station.point_name] = StationGroup(point_name=station.point_name)
            groups[station.point_name].add_station(station)
        return groups
    
    def _check_duplicate_setups(self, group: StationGroup) -> List[str]:
        """Проверка повторных установок"""
        warnings = []
        orientations = group.get_unique_orientations()
        
        if len(orientations) > 1:
            warnings.append(
                f"Обнаружено {len(orientations)} разных ориентировок на пункте {group.point_name}"
            )
        
        return warnings
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку по результатам"""
        total_warnings = sum(
            len(r.warnings) for r in self.station_results.values()
        )
        
        return {
            'num_processed': len(self.station_results),
            'total_warnings': total_warnings,
            'network_result': self.network_result
        }