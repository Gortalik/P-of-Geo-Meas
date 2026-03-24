import numpy as np
from scipy import sparse
from typing import Dict, List, Tuple, Any
import warnings
import logging

logger = logging.getLogger(__name__)


class BaardaReliability:
    """Анализ надёжности геодезической сети по теории В. Баарда"""

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
        self.N = None  # Нормальная матриция

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
            logger.warning(f"Используем псевдообратную матрицу: {e}", exc_info=True)
            N_inv = np.linalg.pinv(self.N.toarray())
            N_inv = sparse.csr_matrix(N_inv)

        # Ковариационная матрица неизвестных
        self.Qxx = self.sigma0 ** 2 * N_inv

        # Ковариационная матрица измерений: Qll = P⁻¹
        P_diag = self.P.diagonal()
        valid_mask = P_diag > 1e-15
        Qll_diag = np.zeros_like(P_diag)
        Qll_diag[valid_mask] = 1.0 / P_diag[valid_mask]
        Qll = sparse.diags(Qll_diag)

        # Ковариационная матрица остатков: Qvv = Qll - A · Qxx · A^T
        # Для экономии памяти вычисляем только диагональные элементы для больших матриц
        try:
            # Попытка полного вычисления для небольших матриц
            if self.A.shape[0] < 1000:
                A_Qxx_AT = self.A @ self.Qxx @ self.A.T
                self.Qvv = Qll - A_Qxx_AT
            else:
                # Для больших матриц вычисляем только диагональ
                logger.info("Вычисление полной матрицы Qvv пропущено (слишком большая система)")
                logger.info("Будут использоваться только диагональные элементы")
                # Диагональные элементы: q_vv_ii = q_ll_ii - Σ(a_ij² · q_xx_jj)
                diag_Qvv = Qll_diag.copy()
                for i in range(self.A.shape[0]):
                    row = self.A[i].toarray().flatten()
                    diag_Qvv[i] -= np.sum(row**2 * self.Qxx.diagonal())
                self.Qvv = sparse.diags(diag_Qvv)
        except MemoryError:
            logger.warning("Недостаточно памяти для вычисления полной матрицы Qvv")
            # Используем только диагональные элементы
            diag_Qvv = Qll_diag.copy()
            for i in range(self.A.shape[0]):
                row = self.A[i].toarray().flatten()
                diag_Qvv[i] -= np.sum(row**2 * self.Qxx.diagonal())
            self.Qvv = sparse.diags(diag_Qvv)

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

        # Защита от отрицательных значений из-за ошибок округления
        negative_indices = np.where(q_vv_diag < 0)[0]
        if len(negative_indices) > 0:
            # Исправление незначительных отрицательных значений
            small_negative = np.abs(q_vv_diag[negative_indices]) < 1e-10
            if np.all(small_negative):
                q_vv_diag[negative_indices] = 0.0
                logger.warning(f"Исправлены {len(negative_indices)} незначительных отрицательных "
                               f"значений в диагонали Qvv")
            else:
                logger.error(f"Обнаружены значительные отрицательные значения в диагонали Qvv: "
                             f"{q_vv_diag[negative_indices]}")
                raise ValueError("Матрица ковариаций остатков содержит отрицательные дисперсии")

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

        # Проверка на нулевое СКО
        if self.sigma0 is None or self.sigma0 == 0:
            raise ValueError("СКО единицы веса не вычислено или равно нулю")

        if self.sigma0 < 1e-10:
            logger.warning(f"Очень малое СКО единицы веса: {self.sigma0}. "
                           "Возможны проблемы с масштабированием весов.")

        # Вычисление стандартизованных остатков с защитой от деления на ноль
        q_vv_diag = self.Qvv.diagonal()

        # Защита от отрицательных и нулевых значений
        valid_mask = (q_vv_diag > 1e-15) & np.isfinite(q_vv_diag)

        standardized_residuals = np.zeros_like(self.residuals)
        standardized_residuals[valid_mask] = (
                self.residuals[valid_mask] /
                (self.sigma0 * np.sqrt(q_vv_diag[valid_mask]))
        )

        # Отметка недействительных остатков
        standardized_residuals[~valid_mask] = np.nan

        # Обнаружение грубых ошибок (только для действительных остатков)
        blunder_indices = np.where(
            valid_mask & (np.abs(standardized_residuals) > threshold)
        )[0]

        blunders = []
        for idx in blunder_indices:
            severity = 'critical' if abs(standardized_residuals[idx]) > 5.0 else 'warning'
            blunders.append({
                'index': idx,
                'residual': self.residuals[idx],
                'standardized_residual': standardized_residuals[idx],
                'q_vv': q_vv_diag[idx],
                'severity': severity
            })

        return {
            'num_blunders': len(blunders),
            'blunders': blunders,
            'threshold': threshold,
            'standardized_residuals': standardized_residuals,
            'num_invalid': np.sum(~valid_mask)
        }

    def calculate_reliability_metrics(self, Qxx: np.ndarray = None) -> Dict[str, Any]:
        """
        Расширенный анализ надёжности по методике DynAdjust
        
        Вычисляет:
        1. Ковариационную матрицу остатков (полная формула)
        2. Внутреннюю надёжность (обнаружение грубых ошибок)
        3. Внешнюю надёжность (влияние незамеченных грубых ошибок)
        4. Статистический критерий обнаружения грубых ошибок
        5. Анализ влияния измерений на координаты (влияние Леви)
        
        Параметры:
        - Qxx: Ковариационная матрица неизвестных (если уже вычислена)
        
        Возвращает:
        - Словарь с метриками надёжности
        """
        n = self.n  # Число измерений
        
        # 1. Ковариационная матрица измерений: Qll = P⁻¹
        P_diag = self.P.diagonal()
        valid_mask = P_diag > 1e-15
        Qll_diag = np.zeros_like(P_diag)
        Qll_diag[valid_mask] = 1.0 / P_diag[valid_mask]
        
        # 2. Ковариационная матрица остатков (полная формула)
        # Qvv = Qll - A · Qxx · A^T
        if Qxx is None:
            Qxx = self.Qxx if self.Qxx is not None else None
        
        if Qxx is None:
            self.compute_matrices()
            Qxx = self.Qxx
        
        # Вычисляем только диагональные элементы для эффективности
        diag_Qvv = Qll_diag.copy()
        for i in range(min(n, 10000)):  # Ограничение для больших сетей
            row = self.A[i].toarray().flatten()
            diag_Qvv[i] -= np.sum(row**2 * Qxx.diagonal())
        
        # 3. Внутренняя надёжность (redundancy numbers по Баарду)
        # r_i = 1 - q_vv_ii / q_ll_ii
        redundancy = np.ones(n)
        valid_qll = Qll_diag > 1e-15
        redundancy[valid_qll] = 1.0 - diag_Qvv[valid_qll] / Qll_diag[valid_qll]
        
        # Ограничение диапазона [0, 1]
        redundancy = np.clip(redundancy, 0.0, 1.0)
        
        # 4. Внешняя надёжность (влияние незамеченных грубых ошибок)
        # δx_i = σ0 · √((1 - r_i) / r_i) для r_i > 0
        external_reliability = np.zeros(n)
        valid_r = redundancy > 0.001  # Избегаем деления на ноль
        external_reliability[valid_r] = self.sigma0 * np.sqrt((1.0 - redundancy[valid_r]) / redundancy[valid_r])
        
        # 5. Статистический критерий обнаружения грубых ошибок
        # Критическое значение для уровня значимости α=0.05 и β=0.001
        # Используем нормальное распределение для больших сетей
        critical_value = 3.0  # Для больших сетей (n > 100)
        if n < 100:
            critical_value = 3.5  # Для малых сетей
        
        # 6. Анализ влияния измерений на координаты (влияние Леви)
        # influence[i, j] = влияние i-го измерения на j-й параметр
        num_params = Qxx.shape[0] if Qxx is not None else 0
        influence = np.zeros((n, num_params))
        
        if num_params > 0 and Qxx is not None:
            for i in range(n):
                row = self.A[i].toarray().flatten()
                influence[i] = Qxx @ row.T
        
        # 7. Определение кандидатов на грубые ошибки
        # Измерения с низкой избыточностью (r_i < 0.1)
        gross_error_candidates = np.where(redundancy < 0.1)[0].tolist()
        
        # 8. Измерения с высокой внешней надёжностью (потенциально опасные)
        unreliable_threshold = 0.05  # 5 см
        unreliable_measurements = np.where(external_reliability > unreliable_threshold)[0].tolist()
        
        return {
            'redundancy': redundancy,
            'external_reliability': external_reliability,
            'critical_value': critical_value,
            'influence_matrix': influence,
            'gross_error_candidates': gross_error_candidates,
            'unreliable_measurements': unreliable_measurements,
            'diag_Qvv': diag_Qvv,
            'Qll_diag': Qll_diag,
            'mean_redundancy': np.mean(redundancy),
            'min_redundancy': np.min(redundancy),
            'max_external_reliability': np.max(external_reliability),
            'num_gross_error_candidates': len(gross_error_candidates),
            'num_unreliable_measurements': len(unreliable_measurements)
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Полный анализ надёжности сети (расширенная версия по методике DynAdjust)"""
        # Вычисление матриц
        self.compute_matrices()
        
        # Внутренняя надёжность (классическая)
        internal_reliability = self.calculate_internal_reliability()
        
        # Внешняя надёжность (классическая)
        external_reliability_classic = self.calculate_external_reliability()
        
        # Расширенные метрики надёжности по методике DynAdjust
        reliability_metrics = self.calculate_reliability_metrics()
        
        # Обнаружение грубых ошибок
        blunder_detection = self.detect_blunders(threshold=3.0)
        
        # Статистика
        avg_internal_reliability = np.mean(internal_reliability)
        max_internal_reliability = np.max(internal_reliability)
        min_internal_reliability = np.min(internal_reliability)
        
        return {
            'internal_reliability': internal_reliability,
            'external_reliability': external_reliability_classic,
            'avg_internal_reliability': avg_internal_reliability,
            'max_internal_reliability': max_internal_reliability,
            'min_internal_reliability': min_internal_reliability,
            'blunder_detection': blunder_detection,
            'num_measurements': self.n,
            'num_unknowns': self.u,
            'redundancy': self.r,
            # Расширенные метрики DynAdjust
            'redundancy_numbers': reliability_metrics['redundancy'],
            'external_reliability_dynadjust': reliability_metrics['external_reliability'],
            'critical_value': reliability_metrics['critical_value'],
            'influence_matrix': reliability_metrics['influence_matrix'],
            'gross_error_candidates': reliability_metrics['gross_error_candidates'],
            'unreliable_measurements': reliability_metrics['unreliable_measurements'],
            'mean_redundancy': reliability_metrics['mean_redundancy'],
            'min_redundancy': reliability_metrics['min_redundancy'],
            'max_external_reliability': reliability_metrics['max_external_reliability']
        }


# Класс-обёртка для обратной совместимости
BaardaMethod = BaardaReliability
