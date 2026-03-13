import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from typing import Tuple, Dict, Any, Optional
import warnings
import logging

logger = logging.getLogger(__name__)

# Попытка импорта scikit-sparse для разреженного разложения Холецкого
try:
    from sksparse.cholmod import cholesky
    HAS_SKSPARSE = True
except ImportError:
    HAS_SKSPARSE = False
    logger.warning("scikit-sparse не установлен. Используем резервный метод LU-разложения.")


class AdjustmentEngine:
    """Движок уравнивания геодезических сетей методом наименьших квадратов
    по параметрическому методу Ю.И. Маркузе"""

    def __init__(self):
        self.adjustment_matrix = None  # Матрица коэффициентов A
        self.observations_vector = None  # Вектор измерений L
        self.weight_matrix = None  # Весовая матрица P
        self.normal_matrix = None  # Нормальная матрица N = A^T · P · A
        self.solution_vector = None  # Вектор решений ΔX
        self.residuals = None  # Вектор остатков V
        self.sigma0 = None  # СКО единицы веса
        self.covariance_matrix = None  # Ковариационная матрица неизвестных

    def _is_positive_definite(self, matrix: sparse.csr_matrix) -> bool:
        """
        Проверка положительной определённости матрицы

        Параметры:
        - matrix: разреженная матрица

        Возвращает:
        - True если матрица положительно определена
        """
        # Проверка диагональных элементов
        diag = matrix.diagonal()
        if np.any(diag <= 0):
            return False

        # Проверка определителя (для небольших матриц)
        if matrix.shape[0] < 100:
            try:
                det = np.linalg.det(matrix.toarray())
                if det <= 1e-10:
                    return False
            except Exception:
                pass

        return True

    def setup_equations(self, A: sparse.csr_matrix,
                        L: np.ndarray,
                        P: sparse.csr_matrix) -> None:
        """
        Формирование системы уравнений поправок

        Параметры:
        - A: разреженная матрица коэффициентов уравнений поправок (n × u)
        - L: вектор свободных членов уравнений поправок (размерность n)
        - P: весовая матрица измерений (диагональная, размерность n × n)

        Уравнение поправок: V = A · ΔX - L
        """
        # Валидация входных данных
        if not sparse.issparse(A):
            A = sparse.csr_matrix(A)
        if not sparse.issparse(P):
            P = sparse.diags(P) if len(P.shape) == 1 else sparse.csr_matrix(P)

        # Проверка размерностей
        n, u = A.shape  # n - число измерений, u - число неизвестных
        l_len = len(L)

        # Проверка совместимости вектора измерений
        if l_len != n:
            raise ValueError(f"Несовместимые размерности: матрица A имеет {n} строк, "
                             f"а вектор измерений имеет длину {l_len}")

        # Проверка весовой матрицы
        if P.shape != (n, n):
            raise ValueError(f"Несовместимые размерности: весовая матрица P должна быть "
                             f"{n}×{n}, а имеет размерность {P.shape}")

        # Проверка весовой матрицы на положительную определённость
        if not self._is_positive_definite(P):
            logger.warning("Весовая матрица не является положительно определённой. "
                           "Это может привести к некорректным результатам.")

        self.adjustment_matrix = A
        self.observations_vector = L
        self.weight_matrix = P

        # Формирование нормальной матрицы: N = A^T · P · A
        self.normal_matrix = A.T @ P @ A

    def solve_normal_equations(self) -> np.ndarray:
        """
        Решение системы нормальных уравнений методом Холецкого
        N · ΔX = U, где U = A^T · P · L

        Возвращает:
        - ΔX: вектор поправок к приближенным координатам
        """
        if self.normal_matrix is None:
            raise ValueError("Необходимо сначала вызвать setup_equations")

        # Вектор правой части: U = A^T · P · L
        U = self.adjustment_matrix.T @ self.weight_matrix @ self.observations_vector

        # Проверка положительной определённости нормальной матрицы
        if not self._is_positive_definite(self.normal_matrix):
            logger.warning("Нормальная матрица не является положительно определённой. "
                           "Проверьте веса измерений и топологию сети.")

        # Решение через разложение Холецкого (для разреженных матриц)
        if HAS_SKSPARSE:
            try:
                factor = cholesky(self.normal_matrix.tocsc())
                self.solution_vector = factor(U)
                
                # Диагностика ранга матрицы
                try:
                    rank = factor.rank()
                    if rank < self.normal_matrix.shape[0]:
                        logger.warning(f"Нормальная матрица имеет ранг {rank} "
                                      f"(ожидалось {self.normal_matrix.shape[0]})")
                        logger.warning("Возможно, сеть вырождена или имеет недостаточное число измерений")
                except Exception:
                    pass  # Не критично, если не удалось получить ранг
            
            except Exception as e:
                logger.error(f"Ошибка при разложении Холецкого: {e}")
                logger.info("Попытка использования LU-разложения...")
                self._solve_with_lu(U)
        else:
            # scikit-sparse недоступен, используем LU-разложение
            self._solve_with_lu(U)

        return self.solution_vector
    
    def _solve_with_lu(self, U: np.ndarray):
        """Резервный метод решения через LU-разложение (scipy.sparse.linalg.splu)"""
        try:
            # LU-разложение для разреженных матриц
            lu = splu(self.normal_matrix.tocsc())
            self.solution_vector = lu.solve(U.toarray().flatten())
            logger.info("Решение получено методом LU-разложения")
        except Exception as e2:
            logger.error(f"Ошибка при LU-разложении: {e2}")
            logger.info("Попытка использования псевдообратной матрицы (плотный формат)...")
            
            try:
                N_dense = self.normal_matrix.toarray()
                N_pinv = np.linalg.pinv(N_dense)
                self.solution_vector = N_pinv @ U
                
                logger.warning("Использовано псевдообратное решение (сеть может быть вырождена)")
            except Exception as e3:
                logger.error(f"Ошибка при псевдообратном решении: {e3}")
                raise ValueError(f"Не удалось решить систему нормальных уравнений: {e3}")

    def calculate_residuals(self) -> np.ndarray:
        """
        Вычисление вектора остатков (поправок в измерения)
        V = A · ΔX - L

        Возвращает:
        - V: вектор остатков (размерность n)
        """
        if self.solution_vector is None:
            raise ValueError("Необходимо сначала вызвать solve_normal_equations")

        self.residuals = self.adjustment_matrix @ self.solution_vector - self.observations_vector
        return self.residuals

    def calculate_sigma0(self) -> float:
        """
        Вычисление апостериорного СКО единицы веса

        Формула: σ₀ = √(V^T · P · V / r)
        где:
        - V — вектор остатков
        - P — весовая матрица
        - r — число избыточных измерений (степень свободы)

        Возвращает:
        - σ₀: СКО единицы веса
        """
        if self.residuals is None:
            self.calculate_residuals()

        # Число измерений
        n = len(self.observations_vector)
        
        # Фактическое число независимых неизвестных (ранг нормальной матрицы)
        if HAS_SKSPARSE:
            try:
                factor = cholesky(self.normal_matrix.tocsc())
                u_effective = factor.rank()
            except Exception:
                # Для плотных матриц используем численный ранг
                N_dense = self.normal_matrix.toarray()
                u_effective = np.linalg.matrix_rank(N_dense, tol=1e-10)
        else:
            # Без sksparse используем численный ранг
            N_dense = self.normal_matrix.toarray()
            u_effective = np.linalg.matrix_rank(N_dense, tol=1e-10)
        
        # Степень свободы (избыточность)
        r = n - u_effective
        
        if r <= 0:
            raise ValueError(f"Недостаточное число избыточных измерений: {r} "
                            f"(измерений: {n}, независимых неизвестных: {u_effective})")

        # СКО единицы веса
        numerator = self.residuals.T @ self.weight_matrix @ self.residuals

        # Защита от отрицательных значений из-за ошибок округления
        if isinstance(numerator, np.ndarray):
            numerator = float(numerator.item())

        if numerator < 0:
            if abs(numerator) < 1e-10:
                # Пренебрежимо малое отрицательное значение - считаем нулём
                numerator = 0.0
                logger.warning("Числитель в формуле σ₀ отрицателен из-за ошибок округления. "
                               "Принимаем равным нулю.")
            else:
                raise ValueError(f"Отрицательное значение числителя в формуле σ₀: {numerator}. "
                                 "Проверьте правильность формирования весовой матрицы.")

        self.sigma0 = np.sqrt(numerator / r)
        
        logger.info(f"СКО единицы веса: {self.sigma0:.6f} (r={r}, "
                   f"ранг={u_effective}/{self.solution_vector.shape[0]})")

        return self.sigma0

    def calculate_covariance_matrix(self) -> sparse.csr_matrix:
        """
        Вычисление ковариационной матрицы уравненных неизвестных

        Формула: Q_xx = σ₀² · N⁻¹
        где:
        - σ₀ — СКО единицы веса
        - N — нормальная матрица

        Возвращает:
        - Q_xx: ковариационная матрица неизвестных (размерность u × u)
        """
        if self.sigma0 is None:
            self.calculate_sigma0()

        # Обратная нормальная матрица
        if HAS_SKSPARSE:
            try:
                factor = cholesky(self.normal_matrix.tocsc())
                N_inv = factor.inv()
            except Exception as e:
                warnings.warn(f"Используем псевдообратную матрицу: {e}")
                N_dense = self.normal_matrix.toarray()
                N_inv = np.linalg.pinv(N_dense)
                N_inv = sparse.csr_matrix(N_inv)
        else:
            # Без sksparse используем псевдообратную матрицу
            N_dense = self.normal_matrix.toarray()
            N_inv = np.linalg.pinv(N_dense)
            N_inv = sparse.csr_matrix(N_inv)

        # Ковариационная матрица
        self.covariance_matrix = (self.sigma0 ** 2) * N_inv

        return self.covariance_matrix

    def adjust(self, A: sparse.csr_matrix,
               L: np.ndarray,
               P: sparse.csr_matrix) -> Dict[str, Any]:
        """
        Полный цикл уравнивания сети

        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - L: вектор свободных членов
        - P: весовая матрица

        Возвращает:
        - Словарь с результатами уравнивания
        """
        # Формирование системы уравнений
        self.setup_equations(A, L, P)

        # Решение нормальных уравнений
        dx = self.solve_normal_equations()

        # Вычисление остатков
        residuals = self.calculate_residuals()

        # Вычисление СКО единицы веса
        sigma0 = self.calculate_sigma0()

        # Вычисление ковариационной матрицы
        Qxx = self.calculate_covariance_matrix()

        return {
            'coordinate_corrections': dx,
            'residuals': residuals,
            'sigma0': sigma0,
            'covariance_matrix': Qxx,
            'normal_matrix': self.normal_matrix,
            'iterations': 1  # Для классического МНК итерации не нужны
        }
