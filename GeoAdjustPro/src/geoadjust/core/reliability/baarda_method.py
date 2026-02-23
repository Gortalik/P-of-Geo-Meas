import numpy as np
from scipy import sparse
from typing import Dict, List, Tuple
import warnings


class BaardaMethod:
    """
    Метод Баарда для анализа надёжности геодезических сетей
    """
    
    def __init__(self, A: sparse.csr_matrix, P: sparse.csr_matrix, sigma0: float = 1.0):
        """
        :param A: Матрица коэффициентов уравнений поправок
        :param P: Весовая матрица
        :param sigma0: Апостериорная СКО единицы веса
        """
        self.A = A
        self.P = P
        self.sigma0 = sigma0
        
        # Размерности
        self.n = A.shape[0]  # число измерений
        self.u = A.shape[1]  # число неизвестных
        
        # Вычисляем необходимые матрицы
        self.N_inv = None  # обратная нормальная матрица
        self.Qxx = None    # ковариационная матрица параметров
        self.Qvv = None    # ковариационная матрица остатков
        self.compute_matrices()
        
    def compute_matrices(self):
        """Вычисление основных матриц метода"""
        # Нормальная матрица
        N = self.A.T @ self.P @ self.A
        
        # Обращение нормальной матрицы
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(N.tocsc())
            self.N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу вместо обычной: {e}")
            self.N_inv = np.linalg.pinv(N.toarray())
            self.N_inv = sparse.csr_matrix(self.N_inv)
        
        # Ковариационная матрица параметров
        self.Qxx = self.sigma0**2 * self.N_inv
        
        # Матрица влияния
        Qll = sparse.diags(1.0 / self.P.diagonal())  # Qll = P^(-1)
        A_Qxx_AT = self.A @ self.Qxx @ self.A.T
        self.Qvv = Qll - A_Qxx_AT
        
    def calculate_reliability_numbers(self) -> np.ndarray:
        """
        Вычисление надёжностей (reliability numbers) измерений
        r_ii = p_ii * q_vv_ii, где p_ii - вес измерения, q_vv_ii - диагональный элемент Qvv
        """
        if self.Qvv is None:
            self.compute_matrices()
            
        # Диагональные элементы ковариационной матрицы остатков
        q_vv_diag = self.Qvv.diagonal()
        
        # Веса измерений
        p_diag = self.P.diagonal()
        
        # Надёжности
        r_ii = p_diag * q_vv_diag
        
        return r_ii
    
    def calculate_internal_reliability(self) -> np.ndarray:
        """
        Вычисление внутренней надёжности (влияние грубой ошибки в измерении на себя)
        rho_ii = r_ii / (1 + r_ii)
        """
        r_ii = self.calculate_reliability_numbers()
        rho_ii = r_ii / (1 + r_ii)
        
        return rho_ii
    
    def calculate_external_reliability(self) -> np.ndarray:
        """
        Вычисление внешней надёжности (влияние грубой ошибки в измерении на параметры)
        Delta_x = Qxx * A.T * P * e_i
        где e_i - единичный вектор для i-го измерения
        """
        if self.Qxx is None:
            self.compute_matrices()
            
        external_reliability = np.zeros((self.n, self.u))
        
        for i in range(self.n):
            # Единичный вектор для i-го измерения
            e_i = np.zeros(self.n)
            e_i[i] = 1.0
            
            # Влияние ошибки в i-ом измерении на параметры
            delta_x = self.Qxx @ self.A.T @ self.P @ e_i
            external_reliability[i, :] = delta_x
            
        return external_reliability
    
    def calculate_bounding_error(self) -> np.ndarray:
        """
        Вычисление граничной ошибки (предел, до которого можно обнаружить грубую ошибку)
        tau_i = sqrt(r_ii) * sigma0
        """
        r_ii = self.calculate_reliability_numbers()
        tau_i = np.sqrt(r_ii) * self.sigma0
        
        return tau_i
    
    def analyze_reliability(self) -> Dict[str, np.ndarray]:
        """
        Полный анализ надёжности
        """
        return {
            'reliability_numbers': self.calculate_reliability_numbers(),
            'internal_reliability': self.calculate_internal_reliability(),
            'external_reliability': self.calculate_external_reliability(),
            'bounding_error': self.calculate_bounding_error()
        }