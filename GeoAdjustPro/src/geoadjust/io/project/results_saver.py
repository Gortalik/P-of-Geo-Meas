#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль сохранения результатов уравнивания в проект
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class ResultsSaver:
    """Полное сохранение результатов уравнивания в проект"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.results_dir = project_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def save_adjustment_results(self, adjustment_result: Dict[str, Any],
                                points: List,
                                observations: List):
        """Полное сохранение результатов уравнивания
        
        Args:
            adjustment_result: Результаты уравнивания
            points: Список пунктов сети
            observations: Список измерений
        """
        
        # 1. Сохранение статистики уравнивания
        stats = {
            'sigma0': adjustment_result.get('sigma0', 0.0),
            'iterations': adjustment_result.get('iterations', 1),
            'num_observations': len(observations),
            'num_unknowns': len(adjustment_result.get('coordinate_corrections', [])) // 2 if 'coordinate_corrections' in adjustment_result else 0,
            'redundancy': len(observations) - (len(adjustment_result.get('coordinate_corrections', [])) // 2) if 'coordinate_corrections' in adjustment_result else 0,
            'convergence': adjustment_result.get('convergence', True),
            'timestamp': adjustment_result.get('timestamp', ''),
            'method': adjustment_result.get('method', 'classic')
        }
        
        stats_file = self.results_dir / "adjustment_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Статистика уравнивания сохранена: {stats_file}")
        
        # 2. Сохранение координат пунктов
        points_data = []
        for p in points:
            point_dict = {
                'point_id': getattr(p, 'point_id', ''),
                'point_type': getattr(p, 'coord_type', ''),
                'x': getattr(p, 'x', None),
                'y': getattr(p, 'y', None),
                'h': getattr(p, 'h', None),
                'sigma_x': getattr(p, 'sigma_x', None),
                'sigma_y': getattr(p, 'sigma_y', None),
                'sigma_h': getattr(p, 'sigma_h', None),
                'normative_class': getattr(p, 'normative_class', ''),
                'is_active': getattr(p, 'is_active', True)
            }
            points_data.append(point_dict)
        
        points_file = self.results_dir / "adjusted_coordinates.json"
        with open(points_file, 'w', encoding='utf-8') as f:
            json.dump(points_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Координаты пунктов сохранены: {points_file}")
        
        # 3. Сохранение поправок в измерениях
        observations_data = []
        for o in observations:
            obs_dict = {
                'obs_id': getattr(o, 'obs_id', ''),
                'obs_type': getattr(o, 'obs_type', ''),
                'from_point': getattr(o, 'from_point', ''),
                'to_point': getattr(o, 'to_point', ''),
                'value': getattr(o, 'value', 0.0),
                'residual': getattr(o, 'residual', 0.0),
                'weight': getattr(o, 'weight', getattr(o, 'weight_multiplier', 1.0)),
                'sigma_aposteriori': getattr(o, 'sigma_aposteriori', 0.0),
                'is_active': getattr(o, 'is_active', True)
            }
            observations_data.append(obs_dict)
        
        observations_file = self.results_dir / "observation_corrections.json"
        with open(observations_file, 'w', encoding='utf-8') as f:
            json.dump(observations_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Поправки измерений сохранены: {observations_file}")
        
        # 4. Сохранение ковариационной матрицы
        if 'covariance_matrix' in adjustment_result:
            cov_matrix = adjustment_result['covariance_matrix']
            cov_file = self.results_dir / "covariance_matrix.npz"
            
            # Преобразование в массив numpy если это разреженная матрица
            if hasattr(cov_matrix, 'toarray'):
                cov_array = cov_matrix.toarray()
            else:
                cov_array = np.array(cov_matrix)
            
            np.savez_compressed(cov_file, covariance=cov_array)
            logger.info(f"Ковариационная матрица сохранена: {cov_file}")
        
        # 5. Сохранение эллипсов ошибок
        if 'ellipse_errors' in adjustment_result:
            ellipses_file = self.results_dir / "error_ellipses.json"
            with open(ellipses_file, 'w', encoding='utf-8') as f:
                json.dump(adjustment_result['ellipse_errors'], f, indent=2, ensure_ascii=False)
            logger.info(f"Эллипсы ошибок сохранены: {ellipses_file}")
        
        # 6. Сохранение надежности по Баарду
        if 'reliability' in adjustment_result:
            reliability_file = self.results_dir / "reliability.json"
            with open(reliability_file, 'w', encoding='utf-8') as f:
                json.dump(adjustment_result['reliability'], f, indent=2, ensure_ascii=False)
            logger.info(f"Надежность сохранена: {reliability_file}")
        
        logger.info("Все результаты уравнивания успешно сохранены")
