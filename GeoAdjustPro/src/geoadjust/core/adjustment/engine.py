import numpy as np
from scipy import sparse
from sksparse.cholmod import cholesky
from typing import Tuple


class AdjustmentEngine:
    """
    Движок уравнивания геодезических сетей методом наименьших квадратов
    по параметрическому методу Ю.И. Маркузе
    """
    
    def __init__(self):
        self.adjustment_matrix = None  # Матрица коэффициентов A
        self.observations_vector = None  # Вектор измерений l
        self.weight_matrix = None  # Весовая матрица P
        self.normal_matrix = None  # Нормальная матрица N
        self.solution_vector = None  # Вектор поправок dX
        self.residuals_vector = None  # Вектор остатков V
        self.sigma0 = None  # Апостериорная СКО единицы веса
        
    def setup_equations(self, A: sparse.csr_matrix, l: np.ndarray, P: sparse.csr_matrix) -> None:
        """
        Формирование системы уравнений поправок V = A * dX - l
        """
        self.adjustment_matrix = A
        self.observations_vector = l
        self.weight_matrix = P
        
        # Формирование нормальной матрицы N = A^T * P * A
        AT = A.T
        self.normal_matrix = AT @ P @ A
        
    def solve_by_cholesky(self) -> np.ndarray:
        """
        Решение системы нормальных уравнений методом Холецкого
        N * dX = U, где U = A^T * P * l
        """
        if self.normal_matrix is None:
            raise ValueError("Необходимо сначала вызвать setup_equations")
            
        # Вектор правой части
        U = self.adjustment_matrix.T @ self.weight_matrix @ self.observations_vector
        
        # Решение через разложение Холецкого
        factor = cholesky(self.normal_matrix.tocsc())
        self.solution_vector = factor(U)
        
        return self.solution_vector
        
    def calculate_residuals(self) -> np.ndarray:
        """
        Вычисление вектора остатков V = A * dX - l
        """
        if self.solution_vector is None:
            raise ValueError("Необходимо сначала решить систему уравнений")
            
        self.residuals_vector = self.adjustment_matrix @ self.solution_vector - self.observations_vector
        return self.residuals_vector
        
    def calculate_posterior_variance(self) -> float:
        """
        Вычисление апостериорной СКО единицы веса
        sigma0^2 = (V^T * P * V) / (n - u - s)
        где n - число измерений, u - число определяемых параметров, s - число условий
        """
        if self.residuals_vector is None:
            self.calculate_residuals()
            
        # Число измерений
        n = len(self.observations_vector)
        # Число определяемых параметров (размерность вектора решения)
        u = len(self.solution_vector)
        # Для параметрического метода без дополнительных условий s = 0
        s = 0
        
        # Сумма квадратов остатков
        vpv = self.residuals_vector.T @ self.weight_matrix @ self.residuals_vector
        # Число степеней свободы
        f = n - u - s
        
        if f <= 0:
            raise ValueError(f"Недостаточно измерений для уравнивания: n={n}, u={u}, f={f}")
            
        self.sigma0 = np.sqrt(vpv / f)
        return self.sigma0