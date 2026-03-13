#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль интеграции ядра обработки с графическим интерфейсом
Обеспечивает связь между данными в таблицах и движком уравнивания
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

from geoadjust.core.network.models import NetworkPoint, Observation
from geoadjust.gui.models.points_model import PointsTableModel
from geoadjust.gui.models.observations_model import ObservationsTableModel

logger = logging.getLogger(__name__)


class ProcessingIntegration(QObject):
    """Интеграция ядра обработки с интерфейсом"""
    
    # Сигналы для обновления прогресса
    progress_updated = pyqtSignal(int, str)  # процент, сообщение
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(dict)  # результаты
    processing_error = pyqtSignal(str)  # сообщение об ошибке
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points_model: Optional[PointsTableModel] = None
        self.observations_model: Optional[ObservationsTableModel] = None
    
    def set_models(self, points_model: PointsTableModel, 
                   observations_model: ObservationsTableModel):
        """Установка моделей данных"""
        self.points_model = points_model
        self.observations_model = observations_model
    
    def prepare_data_for_adjustment(self) -> Tuple[Dict[str, NetworkPoint], List[Observation], List[str]]:
        """
        Подготовка данных из моделей для уравнивания
        
        Возвращает:
        - points_dict: словарь пунктов {point_id: NetworkPoint}
        - observations_list: список измерений
        - fixed_points: список идентификаторов исходных пунктов
        """
        if self.points_model is None or self.observations_model is None:
            raise ValueError("Модели данных не установлены")
        
        # Сбор пунктов
        points_dict = {}
        fixed_points = []
        
        for row in range(self.points_model.rowCount()):
            point = self.points_model.get_point(row)
            if point:
                points_dict[point.point_id] = point
                if point.coord_type == 'FIXED':
                    fixed_points.append(point.point_id)
        
        # Сбор измерений (только активных)
        observations_list = []
        for row in range(self.observations_model.rowCount()):
            obs = self.observations_model.get_observation(row)
            if obs and obs.is_active:
                observations_list.append(obs)
        
        logger.info(f"Подготовлено для уравнивания: "
                   f"{len(points_dict)} пунктов, "
                   f"{len(observations_list)} измерений, "
                   f"{len(fixed_points)} исходных пунктов")
        
        return points_dict, observations_list, fixed_points
    
    def run_adjustment(self) -> Dict[str, Any]:
        """
        Запуск уравнивания сети
        
        Возвращает:
        - Словарь с результатами уравнивания
        """
        try:
            self.processing_started.emit()
            self.progress_updated.emit(10, "Подготовка данных...")
            
            # Подготовка данных
            points_dict, observations_list, fixed_points = self.prepare_data_for_adjustment()
            
            self.progress_updated.emit(30, "Построение матрицы коэффициентов...")
            
            # Здесь будет вызов ядра уравнивания
            # Пока возвращаем заглушку для демонстрации
            result = self._run_dummy_adjustment(points_dict, observations_list, fixed_points)
            
            self.progress_updated.emit(90, "Обновление результатов...")
            
            # Обновление моделей с результатами
            self._update_models_with_results(result, points_dict, observations_list)
            
            self.progress_updated.emit(100, "Уравнивание завершено")
            self.processing_finished.emit(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при уравнивании: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.processing_error.emit(error_msg)
            raise
    
    def _run_dummy_adjustment(self, points_dict: Dict[str, NetworkPoint],
                               observations_list: List[Observation],
                               fixed_points: List[str]) -> Dict[str, Any]:
        """
        Заглушка для демонстрации работы уравнивания
        В реальной реализации здесь будет вызов AdjustmentEngine
        """
        num_unknowns = len([p for p in points_dict.values() if p.coord_type != 'FIXED']) * 2
        
        # Имитация поправок
        corrections = np.zeros(num_unknowns)
        for i in range(num_unknowns):
            corrections[i] = np.random.uniform(-0.01, 0.01)
        
        # Имитация поправок в измерениях
        residuals = np.zeros(len(observations_list))
        for i, obs in enumerate(observations_list):
            residuals[i] = np.random.uniform(-0.001, 0.001)
        
        return {
            'sigma0': 1.0 + np.random.uniform(-0.1, 0.1),
            'iterations': 1,
            'coordinate_corrections': corrections,
            'residuals': residuals,
            'convergence': True
        }
    
    def _update_models_with_results(self, result: Dict[str, Any],
                                    points_dict: Dict[str, NetworkPoint],
                                    observations_list: List[Observation]):
        """Обновление моделей данных с результатами уравнивания"""
        
        # Обновление координат и СКО пунктов
        if 'coordinate_corrections' in result:
            corrections = result['coordinate_corrections']
            unknown_idx = 0
            
            for row in range(self.points_model.rowCount()):
                point = self.points_model.get_point(row)
                if point and point.coord_type != 'FIXED':
                    # Обновление координат
                    if unknown_idx * 2 < len(corrections):
                        point.x += corrections[unknown_idx * 2]
                        point.y += corrections[unknown_idx * 2 + 1]
                        
                        # Обновление СКО (имитация)
                        point.sigma_x = np.abs(corrections[unknown_idx * 2]) * 0.001
                        point.sigma_y = np.abs(corrections[unknown_idx * 2 + 1]) * 0.001
                    
                    unknown_idx += 1
                    self.points_model.update_point(row, point)
        
        # Обновление поправок и СКО измерений
        if 'residuals' in result:
            residuals = result['residuals']
            
            for row in range(self.observations_model.rowCount()):
                obs = self.observations_model.get_observation(row)
                if obs and obs.is_active:
                    idx = observations_list.index(obs)
                    if idx < len(residuals):
                        obs.residual = residuals[idx]
                        
                        # Расчёт апостериорного СКО
                        if hasattr(obs, 'weight') and obs.weight > 0:
                            obs.sigma_aposteriori = result.get('sigma0', 1.0) / np.sqrt(obs.weight)
                        else:
                            obs.sigma_aposteriori = result.get('sigma0', 1.0)
                        
                        self.observations_model.update_observation(row, obs)
