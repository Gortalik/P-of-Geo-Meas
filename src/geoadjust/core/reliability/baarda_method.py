"""Анализ надёжности геодезической сети по теории В. Баарда"""

import numpy as np
from scipy import sparse
from typing import Dict, Any, Optional
import warnings


class BaardaReliability:
    """Анализ надёжности геодезической сети по теории В. Баарда
    
    Теория надёжности Баарда включает:
    - Внутреннюю надёжность: способность сети обнаруживать грубые ошибки
    - Внешнюю надёжность: влияние незамеченной грубой ошибки на уравненные координаты
    """
    
    def __init__(self, A: sparse.csr_matrix, P: sparse.csr_matrix, 
                 sigma0: float, residuals: np.ndarray):
        """
        Инициализация анализа надёжности
        
        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - P: весовая матрица измерений
        - sigma0: СКО единицы веса
        - residuals: вектор остатков
        """
        self.A = A
        self.P = P
        self.sigma0 = sigma0
        self.residuals = residuals
        
        self.n = A.shape[0]  # число измерений
        self.u = A.shape[1]  # число неизвестных
        self.r = self.n - self.u  # степень свободы
        
        self.Qvv = None  # Ковариационная матрица остатков
        self.Qxx = None  # Ковариационная матрица неизвестных
        self.N = None  # Нормальная матрица
    
    def compute_matrices(self):
        """Вычисление ковариационных матриц"""
        if self.N is None:
            self.N = self.A.T @ self.P @ self.A
        
        # Обратная нормальная матрица
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(self.N.tocsc())
            N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу: {e}")
            N_inv = np.linalg.pinv(self.N.toarray())
            N_inv = sparse.csr_matrix(N_inv)
        
        # Ковариационная матрица неизвестных
        self.Qxx = (self.sigma0 ** 2) * N_inv
        
        # Ковариационная матрица измерений
        Qll = sparse.diags(1.0 / self.P.diagonal())
        
        # Ковариационная матрица остатков: Qvv = Qll - A · Qxx · A^T
        A_Qxx_AT = self.A @ self.Qxx @ self.A.T
        self.Qvv = Qll - A_Qxx_AT
    
    def calculate_reliability_numbers(self) -> np.ndarray:
        """
        Вычисление надёжностей (reliability numbers) измерений
        
        Формула: r_ii = p_ii · q_vv_ii
        где:
        - p_ii - вес измерения
        - q_vv_ii - диагональный элемент Qvv
        
        Возвращает:
        - r_ii: массив надёжностей для каждого измерения
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
        Вычисление внутренней надёжности
        
        Внутренняя надёжность показывает влияние грубой ошибки в измерении на себя.
        
        Формула: ρ_ii = r_ii / (1 + r_ii)
        
        Возвращает:
        - rho_ii: массив внутренних надёжностей (0 ≤ ρ_ii ≤ 1)
        """
        r_ii = self.calculate_reliability_numbers()
        rho_ii = r_ii / (1 + r_ii)
        return rho_ii
    
    def calculate_external_reliability(self) -> np.ndarray:
        """
        Вычисление внешней надёжности
        
        Внешняя надёжность показывает влияние грубой ошибки в измерении на параметры.
        
        Формула: Δx = Qxx · A^T · P · e_i
        где e_i - единичный вектор для i-го измерения
        
        Возвращает:
        - external_reliability: матрица влияния (n × u)
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
            external_reliability[i] = delta_x
        
        return external_reliability
    
    def detect_blunders(self, threshold: float = 3.0) -> Dict[str, Any]:
        """
        Обнаружение грубых ошибок по критерию Баарда
        
        Критерий: |r_i| > k · σ0 · √q_vv_i
        где:
        - r_i - остаток измерения
        - k - порог (обычно 3.0 для 99.7% доверительной вероятности)
        - σ0 - СКО единицы веса
        - q_vv_i - диагональный элемент Qvv
        
        Параметры:
        - threshold: порог обнаружения (по умолчанию 3.0)
        
        Возвращает:
        - Словарь с результатами обнаружения
        """
        if self.Qvv is None:
            self.compute_matrices()
        
        # Стандартизованные остатки
        q_vv_diag = self.Qvv.diagonal()
        standardized_residuals = self.residuals / (self.sigma0 * np.sqrt(q_vv_diag))
        
        # Обнаружение грубых ошибок
        blunder_indices = np.where(np.abs(standardized_residuals) > threshold)[0]
        
        blunders = []
        for idx in blunder_indices:
            blunders.append({
                'index': int(idx),
                'residual': float(self.residuals[idx]),
                'standardized_residual': float(standardized_residuals[idx]),
                'q_vv': float(self.Qvv[idx, idx]),
                'severity': 'critical' if abs(standardized_residuals[idx]) > 4.0 else 'warning'
            })
        
        return {
            'num_blunders': len(blunders),
            'blunders': blunders,
            'threshold': threshold,
            'standardized_residuals': standardized_residuals.tolist()
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Полный анализ надёжности сети
        
        Возвращает:
        - Словарь с результатами анализа
        """
        # Вычисление матриц
        self.compute_matrices()
        
        # Внутренняя надёжность
        internal_reliability = self.calculate_internal_reliability()
        
        # Внешняя надёжность
        external_reliability = self.calculate_external_reliability()
        
        # Обнаружение грубых ошибок
        blunder_detection = self.detect_blunders(threshold=3.0)
        
        # Статистика
        avg_internal_reliability = float(np.mean(internal_reliability))
        max_internal_reliability = float(np.max(internal_reliability))
        min_internal_reliability = float(np.min(internal_reliability))
        
        return {
            'internal_reliability': internal_reliability.tolist(),
            'external_reliability': external_reliability.tolist(),
            'avg_internal_reliability': avg_internal_reliability,
            'max_internal_reliability': max_internal_reliability,
            'min_internal_reliability': min_internal_reliability,
            'blunder_detection': blunder_detection,
            'num_measurements': int(self.n),
            'num_unknowns': int(self.u),
            'redundancy': int(self.r)
        }
