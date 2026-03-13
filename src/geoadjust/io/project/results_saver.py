#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль сохранения результатов уравнивания в проект
"""

import json
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

from geoadjust.core.network.models import NetworkPoint, Observation


class ResultsSaver:
    """Сохранение результатов уравнивания в проект"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.results_dir = project_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def save_adjustment_results(self, adjustment_result: Dict[str, Any],
                                points: List[NetworkPoint],
                                observations: List[Observation]):
        """Сохранение результатов уравнивания"""
        
        # Сохранение статистики уравнивания
        stats_file = self.results_dir / "adjustment_statistics.json"
        stats = {
            'sigma0': adjustment_result.get('sigma0', 0.0),
            'iterations': adjustment_result.get('iterations', 1),
            'num_observations': len(observations),
            'num_unknowns': adjustment_result.get('coordinate_corrections', []).shape[0] if hasattr(adjustment_result.get('coordinate_corrections'), 'shape') else len(adjustment_result.get('coordinate_corrections', [])),
            'redundancy': len(observations) - (adjustment_result.get('coordinate_corrections', []).shape[0] if hasattr(adjustment_result.get('coordinate_corrections'), 'shape') else len(adjustment_result.get('coordinate_corrections', []))),
            'convergence': adjustment_result.get('convergence', True),
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        # Сохранение координат пунктов
        points_data = []
        for p in points:
            points_data.append({
                'point_id': p.point_id,
                'point_type': p.coord_type,
                'x': p.x,
                'y': p.y,
                'h': p.h,
                'sigma_x': p.sigma_x,
                'sigma_y': p.sigma_y,
                'sigma_h': p.sigma_h,
                'normative_class': p.normative_class
            })
        
        points_df = pd.DataFrame(points_data)
        
        points_file = self.results_dir / "adjusted_coordinates.parquet"
        points_df.to_parquet(points_file, index=False)
        
        # Сохранение поправок в измерениях
        observations_data = []
        for o in observations:
            observations_data.append({
                'obs_id': o.obs_id,
                'obs_type': o.obs_type,
                'from_point': o.from_point,
                'to_point': o.to_point,
                'value': o.value,
                'residual': getattr(o, 'residual', 0.0),
                'weight': getattr(o, 'weight', 1.0),
                'sigma_aposteriori': getattr(o, 'sigma_aposteriori', 0.0),
                'is_active': o.is_active
            })
        
        observations_df = pd.DataFrame(observations_data)
        
        observations_file = self.results_dir / "observation_corrections.parquet"
        observations_df.to_parquet(observations_file, index=False)
        
        # Сохранение ковариационной матрицы (если есть)
        if 'covariance_matrix' in adjustment_result:
            cov_matrix = adjustment_result['covariance_matrix']
            
            # Преобразование в массив numpy если это sparse матрица
            if hasattr(cov_matrix, 'toarray'):
                cov_array = cov_matrix.toarray()
            else:
                cov_array = np.array(cov_matrix)
            
            cov_file = self.results_dir / "covariance_matrix.npz"
            np.savez_compressed(cov_file, covariance=cov_array)
