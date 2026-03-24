import numpy as np
from scipy import sparse
from typing import Dict, Any, Optional, Literal, List, Tuple
import warnings
import logging

logger = logging.getLogger(__name__)


class FreeNetworkAdjustment:
    """Свободное уравнивание геодезических сетей с минимальными ограничениями по методике DynAdjust"""

    def __init__(self, dimension: Literal['2d', '3d'] = '2d'):
        """
        Инициализация свободного уравнивания

        Параметры:
        - dimension: '2d' или '3d' (размерность сети)
        """
        self.dimension = dimension
        self.constraint_matrix = None
        self.constraint_values = None
    
    def detect_network_type(self, observations: List[Any]) -> Literal['1d', '2d', '3d']:
        """
        Автоматическое определение типа сети по наблюдениям
        
        Типы сетей:
        - 1D сеть (нивелирная): только превышения (height_diff)
        - 2D сеть (плановая): направления (direction), расстояния (distance), азимуты (azimuth)
        - 3D сеть: комбинация плановых измерений и превышений/ГНСС векторов
        
        Параметры:
        - observations: список наблюдений
        
        Возвращает:
        - Тип сети: '1d', '2d' или '3d'
        """
        has_height_diffs = any(getattr(obs, 'obs_type', None) == 'height_diff' for obs in observations)
        has_directions = any(getattr(obs, 'obs_type', None) == 'direction' for obs in observations)
        has_distances = any(getattr(obs, 'obs_type', None) == 'distance' for obs in observations)
        has_gnss_vectors = any(getattr(obs, 'obs_type', None) == 'gnss_vector' for obs in observations)
        has_vertical_angles = any(getattr(obs, 'obs_type', None) in ['vertical_angle', 'zenith_angle'] for obs in observations)
        
        # 1D сеть - только нивелирование
        if has_height_diffs and not (has_directions or has_distances or has_gnss_vectors):
            return '1d'
        
        # 3D сеть - есть и плановые, и высотные измерения
        if (has_directions or has_distances) and (has_height_diffs or has_gnss_vectors or has_vertical_angles):
            return '3d'
        
        # 2D сеть - только плановые измерения
        if has_directions or has_distances:
            return '2d'
        
        # По умолчанию предполагаем 2D
        return '2d'
    
    def apply_minimum_constraints(self, A: sparse.csr_matrix,
                                  L: np.ndarray,
                                  initial_coordinates: np.ndarray,
                                  points: List[Any] = None,
                                  observations: List[Any] = None) -> tuple:
        """
        Применение минимальных ограничений для свободной сети по теории Бомфорда (вдохновлено DynAdjust)
        
        Типы ограничений в зависимости от размерности сети:
        - 1D сеть (нивелирная): фиксация одной точки по высоте
        - 2D сеть (плановая): фиксация двух точек (1 точка по X+Y, 1 точка по ориентации)
        - 3D сеть: фиксация трёх точек (1 точка по X+Y+Z, 1 точка по ориентации вокруг Z, 1 точка по масштабу)
        
        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - L: вектор свободных членов
        - initial_coordinates: начальные приближённые координаты
        - points: список пунктов сети (опционально, для улучшенной фиксации)
        - observations: список наблюдений (опционально, для определения типа сети)
        
        Возвращает:
        - dx: вектор поправок к координатам
        - lambda_multipliers: множители Лагранжа
        - C: матрица ограничений G
        - w: вектор правой части ограничений
        """
        n, u = A.shape  # n - число измерений, u - число неизвестных
        
        # Определение размерности сети
        if observations is not None:
            network_type = self.detect_network_type(observations)
        else:
            network_type = self.dimension.replace('d', 'd')
        
        # Определение числа параметров на точку
        if network_type == '1d':
            params_per_point = 1  # только высота h
        elif network_type == '2d':
            params_per_point = 2  # x, y
        else:  # 3d
            params_per_point = 3  # x, y, h
        
        num_points = u // params_per_point if params_per_point > 0 else u
        
        logger.info(f"Тип сети: {network_type}, число точек: {num_points}, параметров на точку: {params_per_point}")
        
        # Создание матрицы ограничений G
        constraint_rows = 0
        G_rows = []
        
        if network_type == '1d':
            # 1D сеть - фиксируем первую точку по высоте
            # Ограничение: ΣΔh = 0 (сумма поправок высот равна нулю)
            constraint_rows = 1
            G_row = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point  # индекс высоты
                if col_idx < u:
                    G_row[col_idx] = 1.0
            G_rows.append(G_row)
            
        elif network_type == '2d':
            # 2D сеть - минимальные ограничения для устранения дефекта ранга
            # 1. Фиксация центра тяжести сети по X: ΣΔx = 0
            G_row_x = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point  # индекс X
                if col_idx < u:
                    G_row_x[col_idx] = 1.0
            G_rows.append(G_row_x)
            
            # 2. Фиксация центра тяжести сети по Y: ΣΔy = 0
            G_row_y = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point + 1  # индекс Y
                if col_idx < u:
                    G_row_y[col_idx] = 1.0
            G_rows.append(G_row_y)
            
            # 3. Фиксация ориентации сети (вращение вокруг оси Z = 0)
            # Условие: Σ(-y_i · Δx_i + x_i · Δy_i) = 0
            if num_points >= 2 and points is not None and len(points) >= 2:
                G_row_rot = np.zeros(u)
                # Вычисляем координаты центра тяжести
                x_center = sum(p.x for p in points[:num_points]) / num_points if hasattr(points[0], 'x') else 0
                y_center = sum(p.y for p in points[:num_points]) / num_points if hasattr(points[0], 'y') else 0
                
                for point_idx in range(num_points):
                    if point_idx < len(points):
                        point = points[point_idx]
                        dx = getattr(point, 'x', 0) - x_center
                        dy = getattr(point, 'y', 0) - y_center
                        col_x = point_idx * params_per_point
                        col_y = point_idx * params_per_point + 1
                        if col_x < u:
                            G_row_rot[col_x] = -dy
                        if col_y < u:
                            G_row_rot[col_y] = dx
                G_rows.append(G_row_rot)
            else:
                # Упрощённая фиксация ориентации через вторую точку
                if num_points >= 2:
                    G_row_rot = np.zeros(u)
                    # Фиксируем направление на вторую точку
                    col_x_1 = 1 * params_per_point  # X второй точки
                    if col_x_1 < u:
                        G_row_rot[col_x_1] = 1.0
                    G_rows.append(G_row_rot)
            
            constraint_rows = len(G_rows)
            
        elif network_type == '3d':
            # 3D сеть - минимальные ограничения для устранения дефекта ранга (7 параметров)
            # 1. Фиксация центра тяжести по X: ΣΔx = 0
            G_row_x = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point  # индекс X
                if col_idx < u:
                    G_row_x[col_idx] = 1.0
            G_rows.append(G_row_x)
            
            # 2. Фиксация центра тяжести по Y: ΣΔy = 0
            G_row_y = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point + 1  # индекс Y
                if col_idx < u:
                    G_row_y[col_idx] = 1.0
            G_rows.append(G_row_y)
            
            # 3. Фиксация центра тяжести по Z: ΣΔh = 0
            G_row_z = np.zeros(u)
            for point_idx in range(num_points):
                col_idx = point_idx * params_per_point + 2  # индекс Z/h
                if col_idx < u:
                    G_row_z[col_idx] = 1.0
            G_rows.append(G_row_z)
            
            # 4. Фиксация вращения вокруг оси Z: Σ(-y_i · Δx_i + x_i · Δy_i) = 0
            if num_points >= 2 and points is not None and len(points) >= 2:
                G_row_rot_z = np.zeros(u)
                x_center = sum(p.x for p in points[:num_points]) / num_points if hasattr(points[0], 'x') else 0
                y_center = sum(p.y for p in points[:num_points]) / num_points if hasattr(points[0], 'y') else 0
                
                for point_idx in range(num_points):
                    if point_idx < len(points):
                        point = points[point_idx]
                        dx = getattr(point, 'x', 0) - x_center
                        dy = getattr(point, 'y', 0) - y_center
                        col_x = point_idx * params_per_point
                        col_y = point_idx * params_per_point + 1
                        if col_x < u:
                            G_row_rot_z[col_x] = -dy
                        if col_y < u:
                            G_row_rot_z[col_y] = dx
                G_rows.append(G_row_rot_z)
            
            # 5. Фиксация вращения вокруг оси X (если достаточно точек)
            if num_points >= 3 and points is not None and len(points) >= 3:
                G_row_rot_x = np.zeros(u)
                y_center = sum(getattr(p, 'y', 0) for p in points[:num_points]) / num_points
                z_center = sum(getattr(p, 'h', 0) for p in points[:num_points]) / num_points if hasattr(points[0], 'h') else 0
                
                for point_idx in range(num_points):
                    if point_idx < len(points):
                        point = points[point_idx]
                        dy = getattr(point, 'y', 0) - y_center
                        dz = getattr(point, 'h', 0) - z_center
                        col_y = point_idx * params_per_point + 1
                        col_z = point_idx * params_per_point + 2
                        if col_y < u:
                            G_row_rot_x[col_y] = -dz
                        if col_z < u:
                            G_row_rot_x[col_z] = dy
                G_rows.append(G_row_rot_x)
            
            # 6. Фиксация вращения вокруг оси Y (если достаточно точек)
            if num_points >= 3 and points is not None and len(points) >= 3:
                G_row_rot_y = np.zeros(u)
                x_center = sum(getattr(p, 'x', 0) for p in points[:num_points]) / num_points
                z_center = sum(getattr(p, 'h', 0) for p in points[:num_points]) / num_points if hasattr(points[0], 'h') else 0
                
                for point_idx in range(num_points):
                    if point_idx < len(points):
                        point = points[point_idx]
                        dx = getattr(point, 'x', 0) - x_center
                        dz = getattr(point, 'h', 0) - z_center
                        col_x = point_idx * params_per_point
                        col_z = point_idx * params_per_point + 2
                        if col_x < u:
                            G_row_rot_y[col_x] = dz
                        if col_z < u:
                            G_row_rot_y[col_z] = -dx
                G_rows.append(G_row_rot_y)
            
            # 7. Фиксация масштаба (опционально, для ГНСС сетей)
            # Условие: Σ(x_i · Δx_i + y_i · Δy_i + z_i · Δz_i) / S² = 0
            if num_points >= 2 and points is not None and len(points) >= 2:
                G_row_scale = np.zeros(u)
                x_center = sum(getattr(p, 'x', 0) for p in points[:num_points]) / num_points
                y_center = sum(getattr(p, 'y', 0) for p in points[:num_points]) / num_points
                z_center = sum(getattr(p, 'h', 0) for p in points[:num_points]) / num_points if hasattr(points[0], 'h') else 0
                
                for point_idx in range(num_points):
                    if point_idx < len(points):
                        point = points[point_idx]
                        dx = getattr(point, 'x', 0) - x_center
                        dy = getattr(point, 'y', 0) - y_center
                        dz = getattr(point, 'h', 0) - z_center
                        col_x = point_idx * params_per_point
                        col_y = point_idx * params_per_point + 1
                        col_z = point_idx * params_per_point + 2
                        if col_x < u:
                            G_row_scale[col_x] = dx
                        if col_y < u:
                            G_row_scale[col_y] = dy
                        if col_z < u:
                            G_row_scale[col_z] = dz
                G_rows.append(G_row_scale)
            
            constraint_rows = len(G_rows)
        
        # Формирование матрицы ограничений C из строк G
        if G_rows:
            C = sparse.csr_matrix(np.vstack(G_rows))
        else:
            # Если не удалось сформировать ограничения, используем простую схему
            logger.warning("Не удалось сформировать минимальные ограничения, используется упрощённая схема")
            C = sparse.lil_matrix((params_per_point, u))
            for param_idx in range(params_per_point):
                for point_idx in range(min(num_points, 1)):  # Только первая точка
                    col_idx = point_idx * params_per_point + param_idx
                    if col_idx < u:
                        C[param_idx, col_idx] = 1.0
            C = C.tocsr()
        
        # Вектор правой части ограничений (все нули для минимальных ограничений)
        w = np.zeros(C.shape[0])
        
        # Формирование расширенной системы
        # [A^T·P·A  C^T] [ΔX] = [A^T·P·L]
        # [C        0  ] [k ]   [w      ]
        
        # Нормальная матрица (без весов для свободного уравнивания)
        N = A.T @ A
        
        # Расширенная матрица
        top_row = sparse.hstack([N, C.T])
        bottom_row = sparse.hstack([C, sparse.csr_matrix((C.shape[0], C.shape[0]))])
        extended_matrix = sparse.vstack([top_row, bottom_row])
        
        # Расширенный вектор правой части
        top_part = A.T @ L
        extended_rhs = np.concatenate([top_part, w])
        
        # Проверка ранга расширенной матрицы
        try:
            rank = np.linalg.matrix_rank(extended_matrix.toarray())
            if rank < extended_matrix.shape[0]:
                logger.warning(f"Ранг расширенной матрицы ({rank}) меньше размерности ({extended_matrix.shape[0]})")
                logger.warning("Возможно, сеть вырождена или имеет недостаточное число измерений")
        except Exception as e:
            logger.warning(f"Не удалось проверить ранг матрицы: {e}")
        
        # Решение расширенной системы
        try:
            # Используем LU-разложение SciPy вместо sksparse.cholmod
            from scipy.sparse.linalg import splu
            factor = splu(extended_matrix.tocsc())
            solution = factor.solve(extended_rhs)
        except Exception as e:
            logger.warning(f"Используем плотное решение: {e}", exc_info=True)
            extended_dense = extended_matrix.toarray()
            try:
                solution = np.linalg.solve(extended_dense, extended_rhs)
            except np.linalg.LinAlgError as e:
                logger.error(f"Ошибка при решении системы: {e}")
                raise
        
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
