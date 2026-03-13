import numpy as np
from scipy import sparse
from typing import List, NamedTuple, Literal, Dict
import warnings
import logging

logger = logging.getLogger(__name__)


class GrossErrorCandidate(NamedTuple):
    obs_id: str
    residual: float
    standardized_residual: float
    severity: Literal['warning', 'critical']


class GrossErrorAnalyzer:
    """
    Анализатор грубых ошибок в геодезических измерениях
    Реализует 5 методов обнаружения грубых ошибок:
    1. Анализ стандартизованных остатков
    2. Трассирование ходов
    3. L1-анализ
    4. Последовательное отключение исходных пунктов
    5. Анализ влияния измерений (влияние Леви)
    """

    def __init__(self, A: sparse.csr_matrix, P: sparse.csr_matrix, V: np.ndarray,
                 sigma0: float, observations_ids: List[str]):
        """
        :param A: Матрица коэффициентов уравнений поправок
        :param P: Весовая матрица
        :param V: Вектор остатков
        :param sigma0: Апостериорная СКО единицы веса
        :param observations_ids: Идентификаторы измерений
        """
        self.A = A
        self.P = P
        self.V = V
        self.sigma0 = sigma0
        self.observations_ids = observations_ids
        self.n = len(V)

        # Матрица ковариаций остатков
        self.Qvv = self._compute_Qvv()

    def _compute_Qvv(self) -> sparse.csr_matrix:
        """Вычисление ковариационной матрицы остатков Qvv = Qll - A*Qxx*A^T"""
        # Нормальная матрица
        N = self.A.T @ self.P @ self.A

        # Обратная нормальная матрица
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(N.tocsc())
            N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу: {e}")
            N_inv = np.linalg.pinv(N.toarray())
            N_inv = sparse.csr_matrix(N_inv)

        # Ковариационная матрица параметров
        Qxx = self.sigma0 ** 2 * N_inv

        # Ковариационная матрица измерений
        Qll = sparse.diags(1.0 / self.P.diagonal())

        # Ковариационная матрица остатков
        A_Qxx_AT = self.A @ Qxx @ self.A.T
        Qvv = Qll - A_Qxx_AT

        return Qvv

    def analyze_standardized_residuals(self, threshold: float = 3.0) -> List[GrossErrorCandidate]:
        """
        Метод 1: Анализ стандартизованных остатков
        r_i = v_i / (sigma0 * sqrt(q_vv_ii))
        """
        candidates = []

        # Проверка на нулевое СКО
        if self.sigma0 is None:
            raise ValueError("СКО единицы веса не вычислено")

        if self.sigma0 == 0:
            logger.error("СКО единицы веса равно нулю. Анализ стандартизованных остатков невозможен.")
            return []

        if self.sigma0 < 1e-10:
            logger.warning(f"Очень малое СКО единицы веса: {self.sigma0}")

        # Диагональные элементы Qvv
        q_vv_diag = self.Qvv.diagonal()

        for i, (residual, q_vv_ii) in enumerate(zip(self.V, q_vv_diag)):
            if q_vv_ii <= 1e-15:  # Защита от деления на ноль
                continue

            std_residual = residual / (self.sigma0 * np.sqrt(q_vv_ii))

            if abs(std_residual) > threshold:
                severity = "critical" if abs(std_residual) > 5.0 else "warning"
                candidate = GrossErrorCandidate(
                    obs_id=self.observations_ids[i],
                    residual=residual,
                    standardized_residual=std_residual,
                    severity=severity
                )
                candidates.append(candidate)

        return sorted(candidates, key=lambda c: abs(c.standardized_residual), reverse=True)

    def analyze_levi_influence(self) -> np.ndarray:
        """
        Метод 5: Анализ влияния измерений (влияние Леви)
        Вычисляет влияние каждого измерения на параметры
        """
        # Нормальная матрица
        N = self.A.T @ self.P @ self.A

        # Обратная нормальная матрица
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(N.tocsc())
            N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу: {e}")
            N_inv = np.linalg.pinv(N.toarray())
            N_inv = sparse.csr_matrix(N_inv)

        # Влияние каждого измерения на параметры
        levi_influence = np.zeros(self.n)

        for i in range(self.n):
            # Вектор с 1 на i-ом месте
            e_i = np.zeros(self.n)
            e_i[i] = 1.0

            # Влияние i-го измерения на параметры
            influence = self.A.T @ self.P @ e_i
            levi_influence[i] = np.linalg.norm(influence)

        return levi_influence

    def detect_gross_errors(self, methods: List[str] = None) -> Dict[str, List]:
        """
        Обнаружение грубых ошибок всеми доступными методами
        """
        if methods is None:
            methods = ['standardized_residuals', 'levi_influence']

        results = {}

        if 'standardized_residuals' in methods:
            results['standardized_residuals'] = self.analyze_standardized_residuals()

        if 'levi_influence' in methods:
            results['levi_influence'] = self.analyze_levi_influence()

        # Здесь будут добавлены другие методы в будущем
        # 2. Трассирование ходов
        # 3. L1-анализ
        # 4. Последовательное отключение исходных пунктов

        return results