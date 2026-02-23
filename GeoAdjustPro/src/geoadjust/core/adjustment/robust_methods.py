import numpy as np
from scipy import sparse
from typing import Literal
import warnings


class RobustEstimator:
    """
    Реализация робастных методов уравнивания:
    - IRLS с функцией Хьюбера
    - IRLS с функцией Тьюки
    - L1-минимизация
    """
    
    def __init__(self, method: Literal['huber', 'tukey', 'l1'] = 'huber'):
        self.method = method
        self.weights = None
        
    def huber_weights(self, residuals: np.ndarray, c: float = 1.345) -> np.ndarray:
        """
        Веса Хьюбера:
        если |r_i| ≤ c: w_i = 1
        если |r_i| > c: w_i = c / |r_i|
        """
        abs_res = np.abs(residuals)
        weights = np.where(abs_res <= c, 1.0, c / abs_res)
        return weights
    
    def tukey_weights(self, residuals: np.ndarray, c: float = 4.685) -> np.ndarray:
        """
        Веса Тьюки:
        если |r_i| ≤ c: w_i = (1 - (r_i/c)^2)^2
        если |r_i| > c: w_i = 0
        """
        abs_res = np.abs(residuals)
        normalized_res = abs_res / c
        weights = np.where(normalized_res <= 1.0, 
                          (1 - normalized_res**2)**2, 
                          0.0)
        return weights
    
    def irls_adjustment(self, A: sparse.csr_matrix, l: np.ndarray, 
                        initial_weights: np.ndarray = None, max_iter: int = 50, 
                        tolerance: float = 1e-6) -> tuple:
        """
        Итеративно-переоценённый метод наименьших квадратов (IRLS)
        """
        n = len(l)
        
        # Начальные веса
        if initial_weights is None:
            W = np.ones(n)
        else:
            W = initial_weights.copy()
            
        P = sparse.diags(W)
        
        for iteration in range(max_iter):
            # Сохраняем предыдущие веса для проверки сходимости
            prev_weights = W.copy()
            
            # Решение взвешенной задачи МНК
            AT = A.T
            N = AT @ P @ A
            U = AT @ P @ l
            
            try:
                from sksparse.cholmod import cholesky
                factor = cholesky(N.tocsc())
                dx = factor(U)
            except Exception as e:
                warnings.warn(f"Используем плотное решение: {e}")
                N_dense = N.toarray()
                U_dense = U
                dx = np.linalg.solve(N_dense, U_dense)
            
            # Вычисление остатков
            residuals = A @ dx - l
            
            # Обновление весов в зависимости от метода
            if self.method == 'huber':
                W = self.huber_weights(residuals)
            elif self.method == 'tukey':
                W = self.tukey_weights(residuals)
            else:
                raise ValueError(f"Неизвестный метод: {self.method}")
                
            P = sparse.diags(W)
            
            # Проверка сходимости
            weight_change = np.max(np.abs(W - prev_weights))
            if weight_change < tolerance:
                break
                
        return dx, residuals, W
    
    def l1_minimization(self, A: sparse.csr_matrix, l: np.ndarray) -> np.ndarray:
        """
        L1-минимизация для обнаружения грубых ошибок
        Решает задачу min ||Ax - l||_1
        """
        try:
            from scipy.optimize import linprog
        except ImportError:
            raise ImportError("Для L1-минимизации требуется scipy.optimize.linprog")
            
        n, m = A.shape
        
        # Формулировка задачи линейного программирования
        # min sum(t_i), при |Ax - l| <= t
        # Это эквивалентно: min c^T * [x, t], при:
        # [A, -I; -A, -I] * [x; t] <= [l; -l]
        
        # Вектор целевой функции
        c = np.concatenate([np.zeros(m), np.ones(n)])
        
        # Ограничения
        A_ub = sparse.vstack([
            sparse.hstack([A, -sparse.eye(n)]),
            sparse.hstack([-A, -sparse.eye(n)])
        ]).toarray()
        
        b_ub = np.concatenate([l, -l])
        
        # Решение задачи линейного программирования
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, method='highs')
        
        if result.success:
            x_solution = result.x[:m]
            return x_solution
        else:
            raise RuntimeError(f"L1-минимизация не сошлась: {result.message}")
    
    def estimate(self, A: sparse.csr_matrix, l: np.ndarray, 
                 initial_weights: np.ndarray = None) -> tuple:
        """
        Выполнение робастного оценивания
        """
        if self.method == 'huber' or self.method == 'tukey':
            return self.irls_adjustment(A, l, initial_weights)
        elif self.method == 'l1':
            dx = self.l1_minimization(A, l)
            residuals = A @ dx - l
            return dx, residuals, np.ones(len(residuals))
        else:
            raise ValueError(f"Неизвестный метод: {self.method}")