import numpy as np
from scipy import sparse
from typing import Literal, Tuple, Dict, Any
import warnings
import logging

logger = logging.getLogger(__name__)


class RobustMethods:
    """Реализация робастных методов уравнивания:
    - IRLS с функцией Хьюбера
    - IRLS с функцией Тьюки
    - L1-минимизация
    
    Примечание: Класс переименован из RobustEstimator в RobustMethods
    для соответствия имени модуля.
    """
    
    def __init__(self, method: Literal['huber', 'tukey', 'l1'] = 'huber'):
        self.method = method
        self.weights = None
        self.iterations = 0
    
    def huber_weights(self, residuals: np.ndarray, c: float = 1.345) -> np.ndarray:
        """
        Веса по функции потерь Хьюбера

        Формула:
        если |r_i| ≤ c: w_i = 1
        если |r_i| > c: w_i = c / |r_i|

        Параметр c = 1.345 обеспечивает 95% асимптотической эффективности
        при нормальном распределении ошибок.

        Параметры:
        - residuals: стандартизованные остатки
        - c: параметр функции Хьюбера (по умолчанию 1.345)

        Возвращает:
        - weights: массив весов для каждого измерения
        """
        abs_res = np.abs(residuals)
        # Защита от деления на ноль
        abs_res = np.maximum(abs_res, 1e-10)
        weights = np.where(abs_res <= c, 1.0, c / abs_res)
        return weights

    def tukey_weights(self, residuals: np.ndarray, c: float = 4.685) -> np.ndarray:
        """
        Веса по функции потерь Тьюки (би-вес)

        Формула:
        если |r_i| ≤ c: w_i = (1 - (r_i/c)^2)^2
        если |r_i| > c: w_i = 0

        Параметр c = 4.685 обеспечивает 95% эффективности.
        Полностью подавляет влияние грубых ошибок (вес = 0 при |r_i| > c).

        Параметры:
        - residuals: стандартизованные остатки
        - c: параметр функции Тьюки (по умолчанию 4.685)

        Возвращает:
        - weights: массив весов для каждого измерения
        """
        abs_res = np.abs(residuals)
        normalized_res = abs_res / c
        weights = np.where(normalized_res <= 1.0, (1 - normalized_res ** 2) ** 2, 0.0)
        return weights

    def irls_adjustment(self, A: sparse.csr_matrix,
                        L: np.ndarray,
                        initial_weights: np.ndarray = None,
                        max_iter: int = 20,
                        tolerance: float = 1e-6) -> Dict[str, Any]:
        """
        Итеративно-перевзвешенный метод наименьших квадратов (IRLS)

        Алгоритм:
        1. Начальное решение получается классическим МНК
        2. Вычисляются стандартизованные остатки: r_i = v_i / (σ0 · √q_vv_i)
        3. Обновление весов по выбранной функции потерь (Хьюбер/Тьюки)
        4. Формирование новой весовой матрицы: P = diag(w) · P0 · diag(w)
        5. Повторное решение нормальных уравнений
        6. Итерации продолжаются до достижения сходимости

        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - L: вектор свободных членов
        - initial_weights: начальные веса (по умолчанию все = 1)
        - max_iter: максимальное число итераций
        - tolerance: критерий сходимости

        Возвращает:
        - Словарь с результатами уравнивания
        """
        n = len(L)

        # Начальные веса
        if initial_weights is None:
            W = np.ones(n)
        else:
            W = initial_weights.copy()

        # Начальная весовая матрица
        P = sparse.diags(W)

        # Хранение истории итераций
        history = {
            'sigma0': [],
            'max_correction': [],
            'weights': []
        }

        dx = None
        residuals = None
        sigma0 = None

        for iteration in range(max_iter):
            # Сохраняем предыдущие веса для проверки сходимости
            prev_weights = W.copy()

            # Решение взвешенной задачи МНК
            AT = A.T
            N = AT @ P @ A
            U = AT @ P @ L

            try:
                # Используем LU-разложение SciPy вместо sksparse.cholmod
                from scipy.sparse.linalg import splu
                factor = splu(N.tocsc())
                dx = factor.solve(U)
            except Exception as e:
                logger.warning(f"Используем плотное решение на итерации {iteration}: {e}")
                N_dense = N.toarray()
                try:
                    dx = np.linalg.solve(N_dense, U)
                except np.linalg.LinAlgError:
                    # При вырожденности используем lstsq
                    logger.warning(f"Матрица вырождена на итерации {iteration}, используем lstsq")
                    dx, _, _, _ = np.linalg.lstsq(N_dense, U, rcond=None)

            # Вычисление остатков
            residuals = A @ dx - L

            # Вычисление СКО единицы веса
            r = n - dx.shape[0]  # степень свободы
            sigma0 = np.sqrt((residuals.T @ P @ residuals) / r) if r > 0 else 0.0

            # Сохранение истории
            history['sigma0'].append(sigma0)
            history['max_correction'].append(np.max(np.abs(dx)))
            history['weights'].append(W.copy())

            # Проверка сходимости по максимальной поправке
            if iteration > 0 and np.max(np.abs(dx)) < tolerance:
                break

            # Вычисление стандартизованных остатков
            # q_vv = diag(P⁻¹ - A · N⁻¹ · A^T)
            try:
                # Используем LU-разложение SciPy для вычисления обратной матрицы
                from scipy.sparse.linalg import splu
                factor = splu(N.tocsc())
                # Для вычисления обратной матрицы через LU-разложение
                N_inv = np.linalg.inv(N.toarray())
                N_inv = sparse.csr_matrix(N_inv)
            except Exception as e:
                logger.warning(f"Используем псевдообратную матрицу для стандартизации: {e}")
                N_inv = np.linalg.pinv(N.toarray())
                N_inv = sparse.csr_matrix(N_inv)

            # Ковариационная матрица неизвестных
            Qxx = (sigma0 ** 2) * N_inv if sigma0 > 0 else N_inv

            # Ковариационная матрица измерений: Qll = P⁻¹
            P_diag = P.diagonal()
            valid_mask = P_diag > 1e-15
            Qll_diag = np.zeros_like(P_diag)
            Qll_diag[valid_mask] = 1.0 / P_diag[valid_mask]

            # Ковариационная матрица остатков: Qvv = Qll - A · Qxx · A^T
            # Для эффективности вычисляем только диагональные элементы
            A_Qxx_AT_diag = np.zeros(n)
            if sparse.issparse(Qxx):
                Qxx_dense = Qxx.toarray()
            else:
                Qxx_dense = Qxx
            
            for i in range(min(n, 1000)):  # Ограничение для больших сетей
                row_i = A.getrow(i).toarray().flatten()
                A_Qxx_AT_diag[i] = row_i @ Qxx_dense @ row_i.T

            q_vv_diag = Qll_diag - A_Qxx_AT_diag

            # Стандартизованные остатки: r_i = v_i / (σ0 · √q_vv_i)
            standardized_residuals = np.zeros_like(residuals)
            valid_qvv_mask = q_vv_diag > 1e-15
            if sigma0 > 0:
                standardized_residuals[valid_qvv_mask] = (
                    residuals[valid_qvv_mask] / (sigma0 * np.sqrt(q_vv_diag[valid_qvv_mask]))
                )
            else:
                standardized_residuals = residuals / (np.sqrt(q_vv_diag) + 1e-15)

            # Обновление весов в зависимости от выбранного метода
            if self.method == 'huber':
                W = self.huber_weights(standardized_residuals, c=1.345)
            elif self.method == 'tukey':
                W = self.tukey_weights(standardized_residuals, c=4.685)
            else:
                raise ValueError(f"Неизвестный метод: {self.method}")

            # Формирование новой весовой матрицы
            P = sparse.diags(W)

            # Проверка сходимости по весам
            weight_change = np.max(np.abs(W - prev_weights))
            if weight_change < tolerance:
                break

        self.iterations = iteration + 1
        self.weights = W

        # Финальные вычисления
        final_residuals = A @ dx - L
        final_sigma0 = np.sqrt((final_residuals.T @ P @ final_residuals) / r) if r > 0 else 0.0

        return {
            'coordinate_corrections': dx,
            'residuals': final_residuals,
            'sigma0': final_sigma0,
            'weights': W,
            'iterations': self.iterations,
            'history': history,
            'method': self.method
        }

    def l1_minimization(self, A: sparse.csr_matrix,
                        L: np.ndarray,
                        P: sparse.csr_matrix) -> Dict[str, Any]:
        """
        L1-минимизация для обнаружения грубых ошибок

        Формулировка задачи:
        минимизировать ||W · v||_1
        при условии A^T · P · v = 0

        Реализуется через преобразование в задачу линейного программирования.

        Параметры:
        - A: матрица коэффициентов
        - L: вектор свободных членов
        - P: весовая матрица

        Возвращает:
        - Словарь с результатами
        """
        try:
            from scipy.optimize import linprog
        except ImportError:
            raise ImportError("Для L1-минимизации требуется scipy.optimize")

        n = A.shape[0]  # число измерений
        u = A.shape[1]  # число неизвестных

        # Преобразование в задачу линейного программирования
        # Минимизируем: 1^T · t
        # При условиях:
        # -t ≤ W · v ≤ t
        # A^T · P · v = 0

        W = sparse.diags(np.sqrt(P.diagonal())) if sparse.issparse(P) else np.sqrt(np.diag(P))

        # Матрица ограничений неравенств
        A_ub = np.vstack([
            np.hstack([W.toarray() if sparse.issparse(W) else W, -np.eye(n)]),
            np.hstack([-W.toarray() if sparse.issparse(W) else W, -np.eye(n)])
        ])

        # Вектор правой части ограничений неравенств
        b_ub = np.hstack([np.zeros(n), np.zeros(n)])

        # Матрица ограничений равенств
        A_eq = np.hstack([A.T @ P.toarray() if sparse.issparse(P) else A.T @ P, np.zeros((u, n))])

        # Вектор правой части ограничений равенств
        b_eq = np.zeros(u)

        # Целевая функция
        c = np.hstack([np.zeros(n), np.ones(n)])

        # Решение задачи линейного программирования
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='highs')

        if result.success:
            v = result.x[:n]
            dx = np.linalg.lstsq(A.toarray() if sparse.issparse(A) else A, L + v, rcond=None)[0]

            # Вычисление СКО единицы веса
            r = n - u
            sigma0 = np.sqrt((v.T @ P @ v) / r) if r > 0 else 0.0

            return {
                'coordinate_corrections': dx,
                'residuals': v,
                'sigma0': sigma0,
                'method': 'l1_minimization',
                'success': True
            }
        else:
            return {
                'success': False,
                'message': result.message
            }
