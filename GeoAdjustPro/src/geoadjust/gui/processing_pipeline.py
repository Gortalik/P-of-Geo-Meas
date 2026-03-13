#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конвейер обработки данных для графического интерфейса
Интегрирует ядро обработки с GUI
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Этапы обработки данных"""
    LOADING = "loading"
    PREPROCESSING = "preprocessing"
    ADJUSTMENT = "adjustment"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    COMPLETE = "complete"


@dataclass
class ProcessingProgress:
    """Прогресс обработки"""
    stage: ProcessingStage
    percent: int
    message: str
    details: Optional[str] = None


class GUIProcessingPipeline:
    """
    Конвейер обработки для графического интерфейса
    
    Обеспечивает:
    - Поэтапную обработку данных
    - Обновление прогресса через callback
    - Интеграцию с проектом .gad
    - Обработку ошибок и откат изменений
    """
    
    def __init__(self, project=None):
        self.project = project
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Компоненты обработки
        self.preprocessing_engine = None
        self.adjustment_engine = None
        self.analysis_engine = None
        
    def set_project(self, project):
        """Установка текущего проекта"""
        self.project = project
    
    def run_full_processing(
        self, 
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Запуск полного цикла обработки
        
        Параметры:
            progress_callback: функция для обновления прогресса
            
        Возвращает:
            Dictionary с результатами обработки
        """
        try:
            logger.info("Начало полной обработки данных")
            
            # Этап 1: Загрузка данных (0-10%)
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.LOADING, 
                    5, 
                    "Загрузка данных из проекта..."
                ))
            
            observations = self._load_observations()
            control_points = self._load_control_points()
            approx_points = self._load_approximate_points()
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.LOADING, 
                    10, 
                    "Данные загружены",
                    f"Пунктов: {len(control_points)}, Измерений: {len(observations)}"
                ))
            
            # Этап 2: Предобработка (10-30%)
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.PREPROCESSING, 
                    15, 
                    "Предобработка данных..."
                ))
            
            preprocessing_result = self._run_preprocessing(
                observations, 
                control_points,
                progress_callback
            )
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.PREPROCESSING, 
                    30, 
                    "Предобработка завершена",
                    f"Отклонено измерений: {preprocessing_result.get('rejected_count', 0)}"
                ))
            
            # Этап 3: Уравнивание (30-70%)
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.ADJUSTMENT, 
                    35, 
                    "Уравнивание сети..."
                ))
            
            adjustment_result = self._run_adjustment(
                preprocessing_result['observations'],
                control_points,
                approx_points,
                progress_callback
            )
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.ADJUSTMENT, 
                    70, 
                    "Уравнивание завершено",
                    f"Итераций: {adjustment_result.get('iterations', 0)}, "
                    f"μ₀: {adjustment_result.get('reference_error', 'N/A')}"
                ))
            
            # Этап 4: Анализ (70-90%)
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.ANALYSIS, 
                    75, 
                    "Анализ результатов..."
                ))
            
            analysis_result = self._run_analysis(
                adjustment_result,
                progress_callback
            )
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.ANALYSIS, 
                    90, 
                    "Анализ завершён"
                ))
            
            # Этап 5: Сохранение результатов (90-100%)
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.REPORTING, 
                    95, 
                    "Сохранение результатов..."
                ))
            
            self._save_results_to_project({
                'preprocessing': preprocessing_result,
                'adjustment': adjustment_result,
                'analysis': analysis_result
            })
            
            # Объединение результатов
            self.results = {
                'success': True,
                'preprocessing': preprocessing_result,
                'adjustment': adjustment_result,
                'analysis': analysis_result,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.COMPLETE, 
                    100, 
                    "Обработка завершена успешно!"
                ))
            
            logger.info("Обработка завершена успешно")
            return self.results
            
        except Exception as e:
            logger.error(f"Ошибка при обработке данных: {e}", exc_info=True)
            self.errors.append(str(e))
            
            if progress_callback:
                progress_callback(ProcessingProgress(
                    ProcessingStage.COMPLETE, 
                    0, 
                    f"Ошибка: {str(e)}"
                ))
            
            return {
                'success': False,
                'error': str(e),
                'errors': self.errors
            }
    
    def _load_observations(self) -> List[Dict]:
        """Загрузка измерений из проекта"""
        if self.project:
            return self.project.get_observations()
        return []
    
    def _load_control_points(self) -> List[Dict]:
        """Загрузка исходных пунктов из проекта"""
        if self.project:
            points = self.project.get_points()
            return [p for p in points if p.get('type') == 'FIXED']
        return []
    
    def _load_approximate_points(self) -> List[Dict]:
        """Загрузка приближённых координат из проекта"""
        if self.project:
            points = self.project.get_points()
            return [p for p in points if p.get('type') == 'FREE']
        return []
    
    def _run_preprocessing(
        self, 
        observations: List[Dict], 
        control_points: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Запуск предобработки данных
        
        Включает:
        - Контроль допусков
        - Применение редукций
        - Отклонение грубых ошибок
        """
        from geoadjust.core.preprocessing.module import PreprocessingModule
        from geoadjust.io.project.gad_format import GADProject
        
        # Получение настроек допусков
        tolerances = {}
        if self.project:
            tolerances = self.project.get_tolerances()
        
        # Создание модуля предобработки
        preprocessor = PreprocessingModule(tolerances=tolerances)
        
        # Запуск предобработки
        result = preprocessor.process(observations, control_points)
        
        return result
    
    def _run_adjustment(
        self,
        observations: List[Dict],
        control_points: List[Dict],
        approx_points: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Запуск уравнивания сети
        
        Поддерживает:
        - Классический МНК
        - Робастное уравнивание
        - Свободные сети
        """
        from geoadjust.core.adjustment.engine import AdjustmentEngine
        
        # Получение настроек системы координат
        crs_settings = {}
        if self.project:
            crs_settings = self.project.get_crs_settings()
        
        # Создание движка уравнивания
        engine = AdjustmentEngine(crs_settings=crs_settings)
        
        # Запуск уравнивания
        result = engine.adjust(
            observations=observations,
            control_points=control_points,
            approximate_points=approx_points
        )
        
        return result
    
    def _run_analysis(
        self,
        adjustment_result: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Анализ результатов уравнивания
        
        Включает:
        - Расчёт эллипсов ошибок
        - Поиск грубых ошибок (метод Баарду)
        - Оценка точности
        """
        from geoadjust.core.analysis.ellipse_errors import EllipseErrorsCalculator
        from geoadjust.core.analysis.gross_errors import GrossErrorDetector
        
        analysis_result = {
            'ellipse_errors': [],
            'gross_errors': [],
            'accuracy_metrics': {}
        }
        
        # Расчёт эллипсов ошибок
        if 'adjusted_points' in adjustment_result:
            ellipse_calculator = EllipseErrorsCalculator()
            ellipses = ellipse_calculator.calculate(
                adjustment_result['adjusted_points'],
                adjustment_result.get('covariance_matrix')
            )
            analysis_result['ellipse_errors'] = ellipses
        
        # Поиск грубых ошибок
        detector = GrossErrorDetector()
        gross_errors = detector.detect(
            adjustment_result.get('residuals', []),
            adjustment_result.get('weights', [])
        )
        analysis_result['gross_errors'] = gross_errors
        
        # Оценка точности
        analysis_result['accuracy_metrics'] = {
            'reference_error': adjustment_result.get('reference_error'),
            'max_point_error': adjustment_result.get('max_point_error'),
            'relative_errors': adjustment_result.get('relative_errors', [])
        }
        
        return analysis_result
    
    def _save_results_to_project(self, results: Dict[str, Any]):
        """Сохранение результатов в проект"""
        if not self.project:
            logger.warning("Нет открытого проекта для сохранения результатов")
            return
        
        try:
            # Сохранение уравненных координат
            if 'adjustment' in results and 'adjusted_points' in results['adjustment']:
                for point in results['adjustment']['adjusted_points']:
                    self.project.add_point(point)
            
            # Сохранение невязок
            if 'adjustment' in results and 'residuals' in results['adjustment']:
                self.project.results['residuals'] = results['adjustment']['residuals']
            
            # Сохранение точностных характеристик
            if 'analysis' in results:
                self.project.results['accuracy'] = results['analysis'].get('accuracy_metrics', {})
                self.project.results['ellipse_errors'] = results['analysis'].get('ellipse_errors', [])
            
            # Сохранение проекта
            self.project.save()
            
            logger.info("Результаты сохранены в проект")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов: {e}")
            self.errors.append(f"Не удалось сохранить результаты: {str(e)}")
    
    def run_preprocessing_only(
        self,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Запуск только предобработки"""
        observations = self._load_observations()
        control_points = self._load_control_points()
        
        result = self._run_preprocessing(observations, control_points, progress_callback)
        return result
    
    def run_adjustment_only(
        self,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Запуск только уравнивания"""
        observations = self._load_observations()
        control_points = self._load_control_points()
        approx_points = self._load_approximate_points()
        
        result = self._run_adjustment(
            observations, 
            control_points, 
            approx_points, 
            progress_callback
        )
        return result
    
    def get_results(self) -> Dict[str, Any]:
        """Получение результатов последней обработки"""
        return self.results.copy()
    
    def get_errors(self) -> List[str]:
        """Получение списка ошибок"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Получение списка предупреждений"""
        return self.warnings.copy()
