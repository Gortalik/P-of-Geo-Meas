import numpy as np
from scipy import sparse
from typing import Dict, Any, Optional, Literal
import warnings
import logging

logger = logging.getLogger(__name__)


class FreeNetworkAdjustment:
    """Свободное уравнивание геодезических сетей с минимальными ограничениями"""
    
    def __init__(self, dimension: Literal['2d', '3d'] = '2d'):
        """
        Инициализация свободного уравнивания
        
        Параметры:
        - dimension: '2d' или '3d' (размерность сети)
        """
        self.dimension = dimension
        self.constraint_matrix = None
        self.constraint_values = None
    
    def apply_minimum_constraints(self, A: sparse.csr_matrix, 
                                 L: np.ndarray,
                                 initial_coordinates: np.ndarray) -> tuple:
        """
        Применение минимальных ограничений для свободной сети
        
        Для 2D сети ограничения:
        ΣΔx = 0, ΣΔy = 0
        
        Для 3D сети ограничения:
        ΣΔx = 0, ΣΔy = 0, ΣΔh = 0
        
        Формирование расширенной системы уравнений:
        [ N   G^T ] [ΔX]   = [U]
        [ G   0   ] [k ]     [0]
        
        где G — матрица ограничений
        
        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - L: вектор свободных членов
        - initial_coordinates: начальные приближённые координаты
        
        Возвращает:
        - dx: вектор поправок к координатам
        - lambda_multipliers: множители Лагранжа
        - C: матрица ограничений G
        - w: вектор правой части ограничений
        """
        n, u = A.shape  # n - число измерений, u - число неизвестных
        
        # Определяем размерность системы
        if self.dimension == '2d':
            params_per_point = 2  # x, y
        else:  # 3d
            params_per_point = 3  # x, y, h
        
        num_points = u // params_per_point
        
        # Создаем матрицу ограничений
        # Для 2D: сумма поправок координат по X и Y равна 0
        # Для 3D: сумма поправок координат по X, Y и H равна 0
        constraint_rows = params_per_point
        constraint_cols = u
        
        C = sparse.lil_matrix((constraint_rows, constraint_cols))
        
        # Заполняем матрицу ограничений
        for param_idx in range(params_per_point):  # 0 для X, 1 для Y, 2 для H (если 3D)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point + param_idx
                C[param_idx, col_idx] = 1.0
        
        C = C.tocsr()
        
        # Вектор правой части ограничений (все нули для минимальных ограничений)
        w = np.zeros(constraint_rows)
        
        # Формирование расширенной системы
        # [A^T·A  C^T] [ΔX] = [A^T·L]
        # [C      0  ] [k ]   [w    ]
        
        # Нормальная матрица
        N = A.T @ A
        
        # Расширенная матрица
        top_row = sparse.hstack([N, C.T])
        bottom_row = sparse.hstack([C, sparse.csr_matrix((constraint_rows, constraint_rows))])
        extended_matrix = sparse.vstack([top_row, bottom_row])
        
        # Расширенный вектор правой части
        top_part = A.T @ L
        extended_rhs = np.concatenate([top_part, w])
        
        # Решение расширенной системы
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(extended_matrix.tocsc())
            solution = factor(extended_rhs)
        except Exception as e:
            logger.warning(f"Используем плотное решение: {e}", exc_info=True)
            extended_dense = extended_matrix.toarray()
            solution = np.linalg.solve(extended_dense, extended_rhs)
        
        # Извлечение решений
        dx = solution[:u]
        lambda_multipliers = solution[u:]
        
        self.constraint_matrix = C
        self.constraint_values = w
        
        return dx, lambda_multipliers, C, w
    
    def adjust_free_network(self, A: sparse.csr_matrix, 
                           L: np.ndarray,
                           initial_coordinates: np.ndarray) -> Dict[str, Any]:
        """
        Выполнение уравнивания свободной сети
        
        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - L: вектор свободных членов
        - initial_coordinates: начальные приближённые координаты
        
        Возвращает:
        - Словарь с результатами уравнивания
        """
        # Применение минимальных ограничений
        dx, lambda_multipliers, C, w = self.apply_minimum_constraints(A, L, initial_coordinates)
        
        # Вычисление уравненных координат
        adjusted_coordinates = initial_coordinates + dx
        
        # Вычисление остатков
        residuals = A @ dx - L
        
        # Вычисление СКО единицы веса
        n = len(L)
        u = len(dx)
        r = n - u  # степень свободы
        
        if r > 0:
            sigma0 = np.sqrt((residuals.T @ residuals) / r)
        else:
            sigma0 = 0.0
        
        return {
            'adjusted_coordinates': adjusted_coordinates,
            'coordinate_corrections': dx,
            'residuals': residuals,
            'sigma0': sigma0,
            'lambda_multipliers': lambda_multipliers,
            'constraint_matrix': C,
            'constraint_values': w,
            'dimension': self.dimension
        }