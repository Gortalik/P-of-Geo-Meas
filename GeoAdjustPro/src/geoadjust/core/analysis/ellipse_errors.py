import numpy as np
from typing import Tuple


def calculate_error_ellipse_parameters(q_xx: float, q_yy: float, q_xy: float) -> Tuple[float, float, float]:
    """
    Расчёт параметров эллипса ошибок положения по формуле Маркузе:
    - Большая полуось: a = μ · √[(q_xx + q_yy)/2 + √(((q_xx - q_yy)/2)² + q_xy²)]
    - Малая полуось:   b = μ · √[(q_xx + q_yy)/2 - √(((q_xx - q_yy)/2)² + q_xy²)]
    - Азимут большой оси: α = 0.5 · arctg(2 · q_xy / (q_xx - q_yy))
    
    :param q_xx: дисперсия координаты X
    :param q_yy: дисперсия координаты Y
    :param q_xy: ковариация координат X и Y
    :return: (большая_полуось, малая_полуось, азимут_большой_оси_в_радианах)
    """
    # Полуразность дисперсий
    diff_q = (q_xx - q_yy) / 2
    # Подкоренное выражение для вычисления полуосей
    sqrt_term = np.sqrt(diff_q**2 + q_xy**2)
    
    # Полуоси
    a_squared = (q_xx + q_yy) / 2 + sqrt_term
    b_squared = (q_xx + q_yy) / 2 - sqrt_term
    
    # Проверка на отрицательные значения (может возникнуть из-за погрешностей вычислений)
    a = np.sqrt(max(0, a_squared))
    b = np.sqrt(max(0, b_squared))
    
    # Азимут большой оси
    if abs(q_xx - q_yy) < 1e-12 and abs(q_xy) < 1e-12:
        # Если ковариационная матрица диагональная и дисперсии равны
        alpha = 0.0
    else:
        alpha = 0.5 * np.arctan2(2 * q_xy, q_xx - q_yy)
    
    return a, b, alpha


def plot_error_ellipses(points, q_xx_matrix, output_file, scale_factor=1000.0, confidence_level=0.683):
    """
    Построение эллипсов ошибок положения
    :param points: список точек с координатами [(x1, y1), (x2, y2), ...]
    :param q_xx_matrix: матрица ковариаций параметров (размер 2Nx2N для N точек)
    :param output_file: файл для вывода
    :param scale_factor: масштабный коэффициент
    :param confidence_level: уровень доверия (0.683 для 1 сигмы)
    """
    import matplotlib.pyplot as plt
    
    # Коэффициент для уровня доверия
    if confidence_level == 0.683:
        k = 1.0  # для 1 сигмы
    elif confidence_level == 0.95:
        k = 2.4477  # для 95% вероятности в 2D (sqrt(chi2_2D_0.95))
    else:
        # Приближенное значение для других уровней доверия
        from scipy.stats import chi2
        k = np.sqrt(chi2.ppf(confidence_level, df=2))
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    n_points = len(points)
    for i in range(n_points):
        x, y = points[i]
        
        # Извлечение элементов ковариационной матрицы для данной точки
        idx_x = 2 * i
        idx_y = 2 * i + 1
        
        q_xx = q_xx_matrix[idx_x, idx_x]
        q_yy = q_xx_matrix[idx_y, idx_y]
        q_xy = q_xx_matrix[idx_x, idx_y]
        
        # Расчёт параметров эллипса
        a, b, alpha = calculate_error_ellipse_parameters(q_xx, q_yy, q_xy)
        
        # Масштабирование
        a *= scale_factor * k
        b *= scale_factor * k
        
        # Создание точек эллипса
        theta = np.linspace(0, 2*np.pi, 100)
        ellipse_x = a * np.cos(theta)
        ellipse_y = b * np.sin(theta)
        
        # Поворот эллипса
        cos_alpha = np.cos(alpha)
        sin_alpha = np.sin(alpha)
        
        rotated_x = cos_alpha * ellipse_x - sin_alpha * ellipse_y
        rotated_y = sin_alpha * ellipse_x + cos_alpha * ellipse_y
        
        # Смещение к координатам точки
        rotated_x += x
        rotated_y += y
        
        # Отрисовка эллипса
        ax.plot(rotated_x, rotated_y, 'b-', linewidth=0.8)
        ax.fill(rotated_x, rotated_y, alpha=0.2, color='blue')
        
        # Отметка центра эллипса
        ax.plot(x, y, 'ro', markersize=3)
    
    ax.set_aspect('equal')
    ax.grid(True)
    ax.set_title(f'Эллипсы ошибок положения (уровень доверия {confidence_level*100:.1f}%)')
    ax.set_xlabel('X, м')
    ax.set_ylabel('Y, м')
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


class ErrorEllipseAnalyzer:
    """
    Класс для анализа и визуализации эллипсов ошибок
    """
    
    def __init__(self, covariance_matrix, points_coords):
        self.covariance_matrix = covariance_matrix
        self.points = points_coords
        self.n_points = len(points_coords)
        
    def get_ellipse_for_point(self, point_index: int) -> Tuple[float, float, float]:
        """
        Получение параметров эллипса ошибок для конкретной точки
        
        Параметры:
        - point_index: индекс точки (0-based)
        
        Возвращает:
        - (a, b, alpha): большая полуось, малая полуось, азимут большой оси
        
        Исключения:
        - IndexError: если индекс точки вне диапазона
        """
        if point_index >= self.n_points or point_index < 0:
            raise IndexError(f"Индекс точки {point_index} вне диапазона (0-{self.n_points-1})")
            
        idx_x = 2 * point_index
        idx_y = 2 * point_index + 1
        
        # Проверка границ матрицы
        if idx_y >= self.covariance_matrix.shape[0]:
            raise IndexError(f"Индекс {idx_y} выходит за границы ковариационной матрицы "
                           f"(размерность: {self.covariance_matrix.shape})")
        
        q_xx = self.covariance_matrix[idx_x, idx_x]
        q_yy = self.covariance_matrix[idx_y, idx_y]
        q_xy = self.covariance_matrix[idx_x, idx_y]
        
        return calculate_error_ellipse_parameters(q_xx, q_yy, q_xy)
    
    def get_max_and_min_axes(self) -> Tuple[float, float]:
        """
        Получение максимальной и минимальной полуоси среди всех эллипсов
        """
        max_a = 0
        min_b = float('inf')
        
        for i in range(self.n_points):
            a, b, _ = self.get_ellipse_for_point(i)
            max_a = max(max_a, a)
            min_b = min(min_b, b)
            
        return max_a, min_b