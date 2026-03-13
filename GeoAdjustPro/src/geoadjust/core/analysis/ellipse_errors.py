"""Калькулятор эллипсов ошибок положения"""

import numpy as np
from typing import Tuple, Dict, Any
import math


def calculate_error_ellipse_parameters(q_xx: float, q_yy: float,
                                       q_xy: float) -> Tuple[float, float, float]:
    """
    Расчёт параметров эллипса ошибок положения по формуле Маркузе

    Параметры:
    - q_xx: элемент ковариационной матрицы (дисперсия по X)
    - q_yy: элемент ковариационной матрицы (дисперсия по Y)
    - q_xy: элемент ковариационной матрицы (ковариация между X и Y)

    Возвращает:
    - a: большая полуось эллипса
    - b: малая полуось эллипса
    - alpha: азимут большой оси (в радианах)
    """
    # Среднее значение диагональных элементов
    mean_q = (q_xx + q_yy) / 2

    # Разность диагональных элементов
    diff_q = (q_xx - q_yy) / 2

    # Подкоренное выражение для вычисления полуосей
    sqrt_term = math.sqrt(diff_q ** 2 + q_xy ** 2)

    # Полуоси
    a_squared = mean_q + sqrt_term
    b_squared = mean_q - sqrt_term

    # Проверка на отрицательные значения (может возникнуть из-за погрешностей вычислений)
    a = math.sqrt(max(0, a_squared))
    b = math.sqrt(max(0, b_squared))

    # Азимут большой оси
    if abs(q_xx - q_yy) < 1e-12 and abs(q_xy) < 1e-12:
        # Если ковариационная матрица диагональная и дисперсии равны
        alpha = 0.0
    else:
        alpha = 0.5 * math.atan2(2 * q_xy, q_xx - q_yy)

    return a, b, alpha


class ErrorEllipseCalculator:
    """Калькулятор эллипсов ошибок положения"""

    def __init__(self, q_xx_matrix: np.ndarray, sigma0: float):
        """
        Инициализация калькулятора

        Параметры:
        - q_xx_matrix: обратная весовая матрица неизвестных (u × u)
        - sigma0: СКО единицы веса
        """
        self.q_xx_matrix = q_xx_matrix
        self.sigma0 = sigma0
        self.num_points = q_xx_matrix.shape[0] // 2

    def get_ellipse_for_point(self, point_index: int) -> Tuple[float, float, float]:
        """
        Получение параметров эллипса для конкретного пункта

        Параметры:
        - point_index: индекс пункта (0-based)

        Возвращает:
        - a: большая полуось (в единицах координат)
        - b: малая полуось (в единицах координат)
        - alpha: азимут большой оси (в радианах)
        """
        # Индексы элементов ковариационной матрицы для данного пункта
        idx_x = 2 * point_index
        idx_y = 2 * point_index + 1

        # Извлечение элементов ковариационной матрицы
        q_xx = float(self.q_xx_matrix[idx_x, idx_x])
        q_yy = float(self.q_xx_matrix[idx_y, idx_y])
        q_xy = float(self.q_xx_matrix[idx_x, idx_y])

        # Расчёт параметров эллипса
        a, b, alpha = calculate_error_ellipse_parameters(q_xx, q_yy, q_xy)

        # Масштабирование на СКО единицы веса
        a *= self.sigma0
        b *= self.sigma0

        return a, b, alpha

    def get_all_ellipses(self) -> Dict[int, Dict[str, float]]:
        """
        Получение параметров эллипсов для всех пунктов

        Возвращает:
        - Словарь: {индекс_пункта: {a, b, alpha, sigma_position}}
        """
        ellipses = {}

        for i in range(self.num_points):
            a, b, alpha = self.get_ellipse_for_point(i)

            # СКО положения пункта
            sigma_position = math.sqrt(a ** 2 + b ** 2)

            ellipses[i] = {
                'a': a,
                'b': b,
                'alpha': alpha,
                'alpha_degrees': alpha * 180 / math.pi,
                'sigma_position': sigma_position
            }

        return ellipses

    def get_statistics(self) -> Dict[str, float]:
        """
        Получение статистики по эллипсам ошибок

        Возвращает:
        - Словарь со статистикой
        """
        ellipses = self.get_all_ellipses()

        if not ellipses:
            return {
                'max_a': 0.0,
                'min_a': 0.0,
                'avg_a': 0.0,
                'max_b': 0.0,
                'min_b': 0.0,
                'avg_b': 0.0,
                'max_sigma_position': 0.0,
                'min_sigma_position': 0.0,
                'avg_sigma_position': 0.0
            }

        a_values = [e['a'] for e in ellipses.values()]
        b_values = [e['b'] for e in ellipses.values()]
        sigma_values = [e['sigma_position'] for e in ellipses.values()]

        return {
            'max_a': max(a_values),
            'min_a': min(a_values),
            'avg_a': sum(a_values) / len(a_values),
            'max_b': max(b_values),
            'min_b': min(b_values),
            'avg_b': sum(b_values) / len(a_values),
            'max_sigma_position': max(sigma_values),
            'min_sigma_position': min(sigma_values),
            'avg_sigma_position': sum(sigma_values) / len(sigma_values)
        }

    def get_ellipse_summary(self) -> str:
        """
        Получение текстовой сводки по эллипсам ошибок

        Возвращает:
        - Строка с описанием статистики
        """
        stats = self.get_statistics()

        summary = (
            f"Статистика эллипсов ошибок положения:\n"
            f"  Большая полуось (a):\n"
            f"    Макс: {stats['max_a']:.4f} м\n"
            f"    Мин:  {stats['min_a']:.4f} м\n"
            f"    Сред: {stats['avg_a']:.4f} м\n"
            f"  Малая полуось (b):\n"
            f"    Макс: {stats['max_b']:.4f} м\n"
            f"    Мин:  {stats['min_b']:.4f} м\n"
            f"    Сред: {stats['avg_b']:.4f} м\n"
            f"  СКО положения:\n"
            f"    Макс: {stats['max_sigma_position']:.4f} м\n"
            f"    Мин:  {stats['min_sigma_position']:.4f} м\n"
            f"    Сред: {stats['avg_sigma_position']:.4f} м"
        )

        return summary