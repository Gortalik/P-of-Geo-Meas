import numpy as np
from scipy import sparse
from typing import Literal


class FreeNetworkAdjustment:
    """
    Уравнивание свободных геодезических сетей (сети без исходных пунктов)
    Реализует минимальные ограничения (метод Гаусса-Маркова):
    2D: ΣΔx = 0, ΣΔy = 0
    3D: ΣΔx = 0, ΣΔy = 0, ΣΔh = 0
    """
    
    def __init__(self, dimension: Literal['2d', '3d'] = '2d'):
        self.dimension = dimension
        self.constraint_matrix = None
        self.constraint_values = None
        
    def apply_minimum_constraints(self, A: sparse.csr_matrix, l: sparse.csr_matrix, 
                                 coordinates: np.ndarray) -> tuple:
        """
        Применение минимальных ограничений к системе уравнений
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
        
        # Вектор значений ограничений (все нули для минимальных ограничений)
        w = np.zeros(constraint_rows)
        
        # Формируем расширенную систему уравнений
        # [P*A   C^T] [dx]   [P*l]
        # [C     0  ] [k ] = [w  ]
        
        # Создаем блочную матрицу
        top_row = sparse.hstack([A.T @ A, C.T])
        bottom_row = sparse.hstack([C, sparse.csr_matrix((constraint_rows, constraint_rows))])
        extended_matrix = sparse.vstack([top_row, bottom_row])
        
        # Создаем расширенный вектор правой части
        top_part = A.T @ l
        bottom_part = w
        extended_rhs = np.concatenate([top_part, bottom_part])
        
        # Решаем расширенную систему
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(extended_matrix.tocsc())
            solution = factor(extended_rhs)
        except Exception as e:
            print(f"Используем плотное решение: {e}")
            extended_dense = extended_matrix.toarray()
            solution = np.linalg.solve(extended_dense, extended_rhs)
        
        # Извлекаем решения
        dx = solution[:u]
        lambda_multipliers = solution[u:]
        
        return dx, lambda_multipliers, C, w
    
    def adjust_free_network(self, A: sparse.csr_matrix, l: np.ndarray, 
                           initial_coordinates: np.ndarray) -> dict:
        """
        Выполнение уравнивания свободной сети
        """
        dx, lambda_multipliers, C, w = self.apply_minimum_constraints(
            A, l, initial_coordinates
        )
        
        # Вычисляем уравненные координаты
        adjusted_coordinates = initial_coordinates + dx
        
        # Вычисляем остатки
        residuals = A @ dx - l
        
        return {
            'adjusted_coordinates': adjusted_coordinates,
            'coordinate_corrections': dx,
            'residuals': residuals,
            'lambda_multipliers': lambda_multipliers,
            'constraint_matrix': C,
            'constraint_values': w
        }