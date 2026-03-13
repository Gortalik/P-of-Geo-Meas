#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграция ядра обработки с графическим интерфейсом
Обеспечивает связь между GUI и модулями уравнивания
"""

import logging
from typing import Dict, Any, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

from geoadjust.core.network.models import NetworkPoint, Observation
from geoadjust.core.adjustment.engine import AdjustmentEngine
from geoadjust.core.adjustment.equations_builder import EquationsBuilder
from geoadjust.core.adjustment.weight_builder import WeightBuilder

logger = logging.getLogger(__name__)


class ProcessingIntegration(QObject):
    """Полная интеграция ядра обработки с графическим интерфейсом"""
    
    progress_updated = pyqtSignal(int, str)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(dict)
    processing_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points_model = None
        self.observations_model = None
        self.engine = AdjustmentEngine()
        self.builder = EquationsBuilder()
        self.weight_builder = WeightBuilder()
    
    def set_models(self, points_model, observations_model):
        """Установка моделей данных для интеграции
        
        Args:
            points_model: PointsTableModel - модель пунктов
            observations_model: ObservationsTableModel - модель измерений
        """
        self.points_model = points_model
        self.observations_model = observations_model
    
    def prepare_data_for_adjustment(self) -> tuple:
        """Подготовка данных для уравнивания из моделей
        
        Returns:
            tuple: (points_dict, observations_list, fixed_points)
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
        """Запуск уравнивания
        
        Returns:
            Dict[str, Any]: Результаты уравнивания
        """
        try:
            self.processing_started.emit()
            self.progress_updated.emit(10, "Подготовка данных...")
            
            # Подготовка данных
            points_dict, observations_list, fixed_points = self.prepare_data_for_adjustment()
            
            self.progress_updated.emit(30, "Построение матрицы коэффициентов...")
            
            # Построение матрицы коэффициентов
            A, L = self.builder.build_adjustment_matrix(
                observations_list,
                points_dict,
                fixed_points
            )
            
            self.progress_updated.emit(50, "Формирование весовой матрицы...")
            
            # Формирование весовой матрицы
            P = self.weight_builder.build_weight_matrix(
                observations_list,
                points_dict
            )
            
            self.progress_updated.emit(70, "Уравнивание сети...")
            
            # Уравнивание
            result = self.engine.adjust(A, L, P)
            
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
    
    def _update_models_with_results(self, result: Dict[str, Any],
                                    points_dict: Dict[str, NetworkPoint],
                                    observations_list: List[Observation]):
        """Обновление моделей данных с результатами уравнивания
        
        Args:
            result: Результаты уравнивания
            points_dict: Словарь пунктов
            observations_list: Список измерений
        """
        # Обновление координат и СКО пунктов
        if 'coordinate_corrections' in result:
            corrections = result['coordinate_corrections']
            
            for row in range(self.points_model.rowCount()):
                point = self.points_model.get_point(row)
                if point and point.coord_type != 'FIXED':
                    idx = list(points_dict.keys()).index(point.point_id)
                    if idx * 2 < len(corrections):
                        point.x += corrections[idx * 2]
                        point.y += corrections[idx * 2 + 1]
                    
                    if 'covariance_matrix' in result:
                        Qxx = result['covariance_matrix']
                        if idx * 2 < Qxx.shape[0]:
                            point.sigma_x = np.sqrt(Qxx[idx * 2, idx * 2])
                            point.sigma_y = np.sqrt(Qxx[idx * 2 + 1, idx * 2 + 1])
                    
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
                        
                        if 'sigma0' in result and hasattr(obs, 'weight'):
                            obs.sigma_aposteriori = result['sigma0'] / np.sqrt(obs.weight)
                        
                        self.observations_model.update_observation(row, obs)
