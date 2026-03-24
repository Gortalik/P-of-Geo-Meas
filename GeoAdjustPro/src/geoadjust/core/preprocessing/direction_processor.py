"""
Модуль улучшенной обработки круговых приемов по методике DynAdjust
с адаптацией под СП 11-104-97 РФ

Вдохновлено реализацией DynAdjust с учётом российских нормативов
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NetworkClass(Enum):
    """Классы точности геодезических сетей по СП 11-104-97"""
    CLASS_1 = '1_class'      # 1 класс
    CLASS_2 = '2_class'      # 2 класс
    CLASS_3 = '3_class'      # 3 класс
    CLASS_4 = '4_class'      # 4 класс
    RANK_1 = '1st_rank'      # 1 разряд
    RANK_2 = '2nd_rank'      # 2 разряд


@dataclass
class DirectionObservation:
    """Направление из кругового приема"""
    target_point: str
    value: float  # значение направления в градусах
    sigma: Optional[float] = None  # СКО направления
    reception_number: Optional[int] = None
    datetime: Optional[Any] = None


class DirectionSetProcessor:
    """
    Обработка кругового приема направлений с контролем по классам точности
    Вдохновлено методикой DynAdjust с адаптацией под СП 11-104-97 РФ
    """
    
    # Допуски замыкания горизонта по классам (в секундах)
    CLOSURE_TOLERANCES = {
        NetworkClass.CLASS_1: 2.0,
        NetworkClass.CLASS_2: 3.0,
        NetworkClass.CLASS_3: 4.0,
        NetworkClass.CLASS_4: 5.0,
        NetworkClass.RANK_1: 8.0,
        NetworkClass.RANK_2: 12.0
    }
    
    # Допуски расхождения направлений между приемами (в секундах)
    BETWEEN_RECEIPTS_TOLERANCES = {
        NetworkClass.CLASS_1: 1.0,
        NetworkClass.CLASS_2: 2.0,
        NetworkClass.CLASS_3: 3.0,
        NetworkClass.CLASS_4: 4.0,
        NetworkClass.RANK_1: 6.0,
        NetworkClass.RANK_2: 10.0
    }
    
    # Допуски колебаний изображений сигналов (в секундах)
    OSCILLATION_TOLERANCES = {
        NetworkClass.CLASS_1: 0.5,
        NetworkClass.CLASS_2: 1.0,
        NetworkClass.CLASS_3: 1.5,
        NetworkClass.CLASS_4: 2.0,
        NetworkClass.RANK_1: 3.0,
        NetworkClass.RANK_2: 5.0
    }
    
    def __init__(self, class_name: str = '4_class'):
        """
        Инициализация процессора направлений
        
        Параметры:
        - class_name: класс точности сети ('1_class', '2_class', ..., '2nd_rank')
        """
        try:
            self.network_class = NetworkClass(class_name)
        except ValueError:
            logger.warning(f"Неизвестный класс точности '{class_name}', используется 4 класс")
            self.network_class = NetworkClass.CLASS_4
        
        self.closure_tolerance = self.CLOSURE_TOLERANCES[self.network_class]
        self.between_receipts_tolerance = self.BETWEEN_RECEIPTS_TOLERANCES[self.network_class]
        self.oscillation_tolerance = self.OSCILLATION_TOLERANCES[self.network_class]
    
    def process_direction_set(self, directions: List[DirectionObservation]) -> Dict[str, Any]:
        """
        Обработка кругового приема направлений с контролем замыкания горизонта
        
        Параметры:
        - directions: список направлений в приеме
        
        Возвращает:
        - Словарь с результатами обработки
        """
        if not directions:
            return {
                'status': 'error',
                'error_message': 'Список направлений пуст'
            }
        
        if len(directions) < 2:
            return {
                'status': 'error',
                'error_message': 'Недостаточно направлений для обработки (минимум 2)'
            }
        
        # Расчёт невязки замыкания горизонта
        closure_result = self._calculate_closure(directions)
        
        # Проверка допуска замыкания
        is_closure_compliant = closure_result['closure_seconds'] <= self.closure_tolerance
        
        # Усреднение направлений с весами
        weighted_result = self._average_directions(directions)
        
        # Оценка качества приема
        quality_score = self._evaluate_quality(closure_result, directions)
        
        return {
            'status': 'success',
            'mean_directions': weighted_result['directions'],
            'closure_seconds': closure_result['closure_seconds'],
            'tolerance_seconds': self.closure_tolerance,
            'is_closure_compliant': is_closure_compliant,
            'num_directions': len(directions),
            'class_name': self.network_class.value,
            'quality_score': quality_score,
            'first_direction': directions[0].value,
            'last_direction': directions[-1].value,
            'closure_in_degrees': closure_result['closure_degrees']
        }
    
    def _calculate_closure(self, directions: List[DirectionObservation]) -> Dict[str, float]:
        """
        Расчёт невязки замыкания горизонта
        
        Параметры:
        - directions: список направлений
        
        Возвращает:
        - closure_degrees: невязка в градусах
        - closure_seconds: невязка в секундах
        """
        first_direction = directions[0].value
        last_direction = directions[-1].value
        
        # Расчёт невязки
        closure = abs(last_direction - first_direction - 360.0)
        
        # Нормализация невязки в диапазон [0, 360)
        closure = closure % 360.0
        if closure > 180.0:
            closure = 360.0 - closure
        
        # Перевод в секунды
        closure_seconds = closure * 3600.0
        
        return {
            'closure_degrees': closure,
            'closure_seconds': closure_seconds
        }
    
    def _average_directions(self, directions: List[DirectionObservation]) -> Dict[str, Any]:
        """
        Усреднение направлений с весами
        
        Параметры:
        - directions: список направлений
        
        Возвращает:
        - directions: усреднённые направления
        - weights: использованные веса
        """
        averaged_directions = []
        
        # Группировка направлений по целевым точкам
        target_groups: Dict[str, List[DirectionObservation]] = {}
        for dir_obs in directions:
            target = dir_obs.target_point
            if target not in target_groups:
                target_groups[target] = []
            target_groups[target].append(dir_obs)
        
        # Усреднение по каждой целевой точке
        for target, dir_list in target_groups.items():
            if len(dir_list) == 1:
                # Одно направление - используем как есть
                mean_value = dir_list[0].value
                std_dev = 0.0
                num_observations = 1
            else:
                # Несколько направлений - усредняем с весами
                weighted_sum = 0.0
                weight_sum = 0.0
                
                for dir_obs in dir_list:
                    # Вес обратно пропорционален дисперсии
                    sigma = dir_obs.sigma if dir_obs.sigma is not None else 5.0
                    weight = 1.0 / (sigma ** 2)
                    weighted_sum += dir_obs.value * weight
                    weight_sum += weight
                
                if weight_sum > 0:
                    mean_value = weighted_sum / weight_sum
                    # Расчёт СКО среднего
                    residuals = [d.value - mean_value for d in dir_list]
                    variance = sum(r**2 for r in residuals) / (len(dir_list) - 1)
                    std_dev = np.sqrt(variance)
                else:
                    mean_value = sum(d.value for d in dir_list) / len(dir_list)
                    std_dev = 0.0
                
                num_observations = len(dir_list)
            
            averaged_directions.append({
                'target_point': target,
                'mean_value': mean_value,
                'std_dev': std_dev,
                'num_observations': num_observations
            })
        
        return {
            'directions': averaged_directions
        }
    
    def _evaluate_quality(self, closure_result: Dict[str, float], 
                         directions: List[DirectionObservation]) -> str:
        """
        Оценка качества кругового приема
        
        Параметры:
        - closure_result: результаты расчёта невязки
        - directions: список направлений
        
        Возвращает:
        - quality: оценка качества ('excellent', 'good', 'acceptable', 'poor')
        """
        closure_ratio = closure_result['closure_seconds'] / self.closure_tolerance
        
        if closure_ratio <= 0.5:
            return 'excellent'
        elif closure_ratio <= 0.75:
            return 'good'
        elif closure_ratio <= 1.0:
            return 'acceptable'
        else:
            return 'poor'
    
    def process_multiple_receptions(self, receptions: List[List[DirectionObservation]]) -> Dict[str, Any]:
        """
        Обработка нескольких круговых приемов на станции
        
        Параметры:
        - receptions: список приемов, каждый прием - список направлений
        
        Возвращает:
        - Словарь с результатами обработки всех приемов
        """
        if not receptions:
            return {
                'status': 'error',
                'error_message': 'Список приемов пуст'
            }
        
        results = []
        all_directions_by_target: Dict[str, List[float]] = {}
        
        for i, reception in enumerate(receptions):
            result = self.process_direction_set(reception)
            result['reception_number'] = i + 1
            results.append(result)
            
            # Сбор направлений для контроля сходимости между приемами
            if result['status'] == 'success':
                for dir_data in result['mean_directions']:
                    target = dir_data['target_point']
                    if target not in all_directions_by_target:
                        all_directions_by_target[target] = []
                    all_directions_by_target[target].append(dir_data['mean_value'])
        
        # Контроль сходимости между приемами
        between_receipts_check = self._check_between_receipts_consistency(
            all_directions_by_target
        )
        
        # Итоговая оценка
        all_compliant = all(
            r.get('is_closure_compliant', False) for r in results if r['status'] == 'success'
        )
        between_receipts_ok = between_receipts_check['is_consistent']
        
        overall_status = 'success' if (all_compliant and between_receipts_ok) else 'warning'
        
        return {
            'status': overall_status,
            'num_receptions': len(receptions),
            'reception_results': results,
            'between_receipts_check': between_receipts_check,
            'final_directions': self._combine_receptions(receptions),
            'all_compliant': all_compliant,
            'between_receipts_ok': between_receipts_ok
        }
    
    def _check_between_receipts_consistency(self, 
                                           directions_by_target: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Контроль сходимости направлений между приемами
        
        Параметры:
        - directions_by_target: направления по целевым точкам
        
        Возвращает:
        - Словарь с результатами контроля
        """
        inconsistencies = []
        
        for target, values in directions_by_target.items():
            if len(values) < 2:
                continue
            
            max_diff = max(values) - min(values)
            max_diff_seconds = max_diff * 3600.0
            
            if max_diff_seconds > self.between_receipts_tolerance:
                inconsistencies.append({
                    'target_point': target,
                    'max_diff_degrees': max_diff,
                    'max_diff_seconds': max_diff_seconds,
                    'tolerance_seconds': self.between_receipts_tolerance,
                    'is_violation': True
                })
        
        return {
            'is_consistent': len(inconsistencies) == 0,
            'num_inconsistencies': len(inconsistencies),
            'inconsistencies': inconsistencies
        }
    
    def _combine_receptions(self, receptions: List[List[DirectionObservation]]) -> List[Dict[str, Any]]:
        """
        Объединение результатов нескольких приемов
        
        Параметры:
        - receptions: список приемов
        
        Возвращает:
        - Список объединённых направлений
        """
        all_directions_by_target: Dict[str, List[Tuple[float, float]]] = {}
        
        for reception in receptions:
            for dir_obs in reception:
                target = dir_obs.target_point
                sigma = dir_obs.sigma if dir_obs.sigma is not None else 5.0
                if target not in all_directions_by_target:
                    all_directions_by_target[target] = []
                all_directions_by_target[target].append((dir_obs.value, sigma))
        
        combined = []
        for target, values in all_directions_by_target.items():
            if not values:
                continue
            
            # Взвешенное среднее
            weighted_sum = sum(v / (s**2) for v, s in values)
            weight_sum = sum(1.0 / (s**2) for _, s in values)
            
            if weight_sum > 0:
                mean_value = weighted_sum / weight_sum
                # СКО взвешенного среднего
                combined_sigma = np.sqrt(1.0 / weight_sum)
            else:
                mean_value = sum(v for v, _ in values) / len(values)
                combined_sigma = 0.0
            
            combined.append({
                'target_point': target,
                'mean_value': mean_value,
                'combined_sigma': combined_sigma,
                'num_observations': len(values)
            })
        
        return combined


def process_direction_set(directions: List[Dict], 
                         class_name: str = '4_class') -> Dict[str, Any]:
    """
    Удобная функция для обработки кругового приема
    
    Параметры:
    - directions: список направлений в формате Dict
    - class_name: класс точности сети
    
    Возвращает:
    - Словарь с результатами обработки
    """
    # Конвертация в объекты DirectionObservation
    dir_objects = [
        DirectionObservation(
            target_point=d.get('target_point', d.get('to_point', '')),
            value=d['value'],
            sigma=d.get('sigma', d.get('sigma_apriori', None)),
            reception_number=d.get('reception_number', None),
            datetime=d.get('datetime', None)
        )
        for d in directions
    ]
    
    processor = DirectionSetProcessor(class_name)
    return processor.process_direction_set(dir_objects)
