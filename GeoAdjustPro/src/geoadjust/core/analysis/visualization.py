"""
Модуль визуализации результатов уравнивания геодезических сетей.

Поддерживает:
- Построение эллипсов ошибок положения пунктов
- Тепловые карты корреляций между неизвестными
- Графики распределения остатков (гистограммы, QQ-plot)
- Карты точности сети
- Графики надежности по Баарду
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Visualization:
    """
    Визуализация результатов уравнивания геодезических сетей.
    
    Пример использования:
        viz = Visualization()
        viz.plot_error_ellipses(points, output_path="ellipses.png")
        viz.plot_correlation_heatmap(cov_matrix, output_path="correlation.png")
    """
    
    # Цветовые схемы для различных типов визуализаций
    COLOR_SCHEMES = {
        'error_ellipses': {'edge': 'blue', 'face': 'none', 'linewidth': 1.5},
        'correlation': {'cmap': 'coolwarm', 'center': 0},
        'residuals': {'hist': 'steelblue', 'qq': 'darkorange'},
        'accuracy': {'cmap': 'RdYlGn_r'},
        'reliability': {'cmap': 'YlOrRd'},
    }
    
    # Стандартные размеры фигур
    FIG_SIZES = {
        'error_ellipses': (14, 12),
        'correlation': (16, 14),
        'residuals': (14, 6),
        'accuracy': (14, 12),
        'reliability': (14, 10),
    }
    
    # DPI для сохранения
    DEFAULT_DPI = 300
    
    def __init__(self, style: str = 'seaborn-v0_8'):
        """
        Инициализация визуализатора.
        
        Args:
            style: Стиль matplotlib ('seaborn-v0_8', 'ggplot', 'classic', etc.)
        """
        try:
            plt.style.use(style)
        except Exception:
            plt.style.use('seaborn-v0_8')
        
        # Настройка шрифтов
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
    
    def plot_error_ellipses(self, 
                           points: List[Dict[str, Any]],
                           title: str = 'Эллипсы ошибок положения пунктов',
                           output_path: Optional[Path] = None,
                           show: bool = True,
                           figsize: Tuple[int, int] = None,
                           scale_factor: float = 1.0,
                           **kwargs) -> plt.Figure:
        """
        Построение эллипсов ошибок положения пунктов.
        
        Args:
            points: Список пунктов с параметрами эллипсов
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры (ширина, высота)
            scale_factor: Масштабный коэффициент для эллипсов
            **kwargs: Дополнительные параметры для matplotlib
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['error_ellipses']
        
        fig, ax = plt.subplots(figsize=figsize)
        
        colors = kwargs.get('edge_color', self.COLOR_SCHEMES['error_ellipses']['edge'])
        linewidth = kwargs.get('linewidth', self.COLOR_SCHEMES['error_ellipses']['linewidth'])
        
        # Словарь для легенды
        ellipses_added = False
        
        for point in points:
            ellipse_params = point.get('ellipse') or point.get('error_ellipse')
            
            if ellipse_params is None:
                # Попытка найти параметры в других полях
                a = point.get('a', None)
                b = point.get('b', None)
                alpha = point.get('alpha', 0.0)
                
                if a is None or b is None:
                    continue
                
                ellipse_params = {'a': a, 'b': b, 'alpha': alpha}
            
            x = point.get('x') or point.get('X')
            y = point.get('y') or point.get('Y')
            point_id = point.get('point_id', '')
            
            if x is None or y is None:
                continue
            
            a = ellipse_params.get('a', 0.01) * scale_factor
            b = ellipse_params.get('b', 0.01) * scale_factor
            alpha = ellipse_params.get('alpha', 0.0)
            
            # Преобразование угла из радиан в градусы
            angle_deg = np.degrees(alpha) if isinstance(alpha, float) else 0.0
            
            # Создание эллипса
            ellipse = Ellipse(
                (x, y),
                width=2*a,
                height=2*b,
                angle=angle_deg,
                fill=False,
                edgecolor=colors,
                linewidth=linewidth,
                linestyle='-',
                alpha=0.8
            )
            
            if not ellipses_added:
                ellipse.set_label('Эллипсы ошибок')
                ellipses_added = True
            
            ax.add_patch(ellipse)
            
            # Подпись пункта
            if point_id:
                ax.text(x, y, point_id,
                       ha='center', va='center', fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                edgecolor='gray', alpha=0.7))
        
        # Настройка осей
        ax.set_xlabel('X, м', fontsize=11)
        ax.set_ylabel('Y, м', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_aspect('equal')
        
        # Легенда
        if ellipses_added:
            ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"График эллипсов ошибок сохранен в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def plot_correlation_heatmap(self,
                                 cov_matrix: np.ndarray,
                                 labels: Optional[List[str]] = None,
                                 title: str = 'Тепловая карта корреляций между неизвестными',
                                 output_path: Optional[Path] = None,
                                 show: bool = True,
                                 figsize: Tuple[int, int] = None,
                                 **kwargs) -> plt.Figure:
        """
        Построение тепловой карты корреляций.
        
        Args:
            cov_matrix: Ковариационная матрица
            labels: Метки строк/столбцов (имена пунктов)
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры
            **kwargs: Дополнительные параметры для seaborn.heatmap
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['correlation']
        
        # Вычисление матрицы корреляций из ковариационной
        if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
            raise ValueError("Ковариационная матрица должна быть квадратной")
        
        # Нормализация для получения корреляционной матрицы
        std_devs = np.sqrt(np.diag(cov_matrix))
        if np.any(std_devs == 0):
            logger.warning("Обнаружены нулевые стандартные отклонения")
            std_devs[std_devs == 0] = 1e-10
        
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
        
        # Ограничение значений [-1, 1]
        corr_matrix = np.clip(corr_matrix, -1, 1)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        cmap = kwargs.get('cmap', self.COLOR_SCHEMES['correlation']['cmap'])
        center = kwargs.get('center', self.COLOR_SCHEMES['correlation']['center'])
        
        # Построение тепловой карты
        sns.heatmap(
            corr_matrix,
            annot=kwargs.get('annot', True),
            fmt=kwargs.get('fmt', '.2f'),
            cmap=cmap,
            center=center,
            square=kwargs.get('square', True),
            cbar_kws={'label': 'Коэффициент корреляции'},
            ax=ax,
            xticklabels=labels if labels else kwargs.get('xticklabels', 'auto'),
            yticklabels=labels if labels else kwargs.get('yticklabels', 'auto'),
        )
        
        ax.set_title(title, fontsize=13, fontweight='bold')
        
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"Тепловая карта корреляций сохранена в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def plot_residuals_distribution(self,
                                    residuals: np.ndarray,
                                    title: str = 'Распределение остатков уравнивания',
                                    output_path: Optional[Path] = None,
                                    show: bool = True,
                                    figsize: Tuple[int, int] = None,
                                    bins: int = 30,
                                    **kwargs) -> plt.Figure:
        """
        Построение распределения остатков уравнивания.
        
        Args:
            residuals: Массив остатков (поправок к измерениям)
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры
            bins: Количество бинов для гистограммы
            **kwargs: Дополнительные параметры
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['residuals']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        residuals = np.asarray(residuals).flatten()
        
        # Гистограмма
        hist_color = kwargs.get('hist_color', self.COLOR_SCHEMES['residuals']['hist'])
        ax1.hist(residuals, bins=bins, edgecolor='black', alpha=0.7, color=hist_color)
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Нулевая линия')
        ax1.set_xlabel('Остатки', fontsize=11)
        ax1.set_ylabel('Частота', fontsize=11)
        ax1.set_title('Гистограмма распределения остатков', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.legend()
        
        # Статистика на гистограмме
        mean_val = np.mean(residuals)
        std_val = np.std(residuals)
        stats_text = f'Среднее: {mean_val:.4f}\nСКО: {std_val:.4f}'
        ax1.text(0.98, 0.95, stats_text, transform=ax1.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # QQ-plot
        from scipy import stats
        
        sorted_residuals = np.sort(residuals)
        n = len(sorted_residuals)
        theoretical_quantiles = stats.norm.ppf((np.arange(n) + 0.5) / n)
        
        qq_color = kwargs.get('qq_color', self.COLOR_SCHEMES['residuals']['qq'])
        ax2.plot(theoretical_quantiles, sorted_residuals, 'o', 
                color=qq_color, alpha=0.6, markersize=5, label='Остатки')
        
        # Линия идеального соответствия
        min_val = min(theoretical_quantiles.min(), sorted_residuals.min())
        max_val = max(theoretical_quantiles.max(), sorted_residuals.max())
        ax2.plot([min_val, max_val], [min_val, max_val], 'r--', 
                linewidth=2, label='Теоретическое распределение')
        
        ax2.set_xlabel('Теоретические квантили', fontsize=11)
        ax2.set_ylabel('Выборочные квантили', fontsize=11)
        ax2.set_title('QQ-plot остатков', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend()
        
        # R-квадрат для QQ-plot
        if len(residuals) > 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                theoretical_quantiles, sorted_residuals
            )
            r_squared = r_value ** 2
            r2_text = f'R² = {r_squared:.4f}'
            ax2.text(0.02, 0.98, r2_text, transform=ax2.transAxes,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        fig.suptitle(title, fontsize=13, fontweight='bold')
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"График распределения остатков сохранен в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def plot_accuracy_map(self,
                         points: List[Dict[str, Any]],
                         title: str = 'Карта точности сети',
                         output_path: Optional[Path] = None,
                         show: bool = True,
                         figsize: Tuple[int, int] = None,
                         parameter: str = 'ms',
                         **kwargs) -> plt.Figure:
        """
        Построение карты точности сети.
        
        Args:
            points: Список пунктов с параметрами точности
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры
            parameter: Параметр для визуализации ('ms', 'sigma_x', 'sigma_y', 'sigma_h')
            **kwargs: Дополнительные параметры
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['accuracy']
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Сбор данных
        x_coords = []
        y_coords = []
        values = []
        labels = []
        
        for point in points:
            x = point.get('x') or point.get('X')
            y = point.get('y') or point.get('Y')
            
            if x is None or y is None:
                continue
            
            # Получение значения параметра
            if parameter == 'ms':
                # Среднеквадратическая ошибка положения
                sigma_x = point.get('sigma_x', 0) or 0
                sigma_y = point.get('sigma_y', 0) or 0
                value = np.sqrt(sigma_x**2 + sigma_y**2)
            elif parameter == 'sigma_x':
                value = point.get('sigma_x', 0) or 0
            elif parameter == 'sigma_y':
                value = point.get('sigma_y', 0) or 0
            elif parameter == 'sigma_h':
                value = point.get('sigma_h', 0) or 0
            else:
                value = point.get(parameter, 0) or 0
            
            x_coords.append(x)
            y_coords.append(y)
            values.append(value)
            labels.append(point.get('point_id', ''))
        
        if not values:
            logger.warning("Нет данных для построения карты точности")
            plt.close(fig)
            return fig
        
        values = np.array(values)
        
        # Интерполяция для создания непрерывной карты
        from scipy.interpolate import griddata
        
        # Создание сетки
        xi = np.linspace(min(x_coords), max(x_coords), 100)
        yi = np.linspace(min(y_coords), max(y_coords), 100)
        xi_grid, yi_grid = np.meshgrid(xi, yi)
        
        # Интерполяция
        zi = griddata(
            (x_coords, y_coords), values,
            (xi_grid, yi_grid),
            method='cubic',
            fill_value=np.nan
        )
        
        # Построение контурного графика
        cmap = kwargs.get('cmap', self.COLOR_SCHEMES['accuracy']['cmap'])
        
        contourf = ax.contourf(xi_grid, yi_grid, zi, levels=20, cmap=cmap, alpha=0.8)
        contour = ax.contour(xi_grid, yi_grid, zi, levels=10, colors='black', 
                            linewidths=0.5, alpha=0.5)
        
        # Добавление пунктов
        scatter = ax.scatter(x_coords, y_coords, c=values, cmap=cmap, 
                           s=100, edgecolors='black', linewidths=1.5, zorder=5)
        
        # Подписи пунктов
        for i, label in enumerate(labels):
            if label:
                ax.text(x_coords[i], y_coords[i], label,
                       ha='center', va='center', fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                alpha=0.7))
        
        # Цветовая шкала
        cbar = plt.colorbar(contourf, ax=ax)
        cbar.set_label('СКО, мм', fontsize=11)
        
        ax.set_xlabel('X, м', fontsize=11)
        ax.set_ylabel('Y, м', fontsize=11)
        ax.set_title(f'{title}\n({parameter})', fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"Карта точности сохранена в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def plot_reliability_measures(self,
                                  reliability_data: Dict[str, Any],
                                  title: str = 'Показатели надежности сети',
                                  output_path: Optional[Path] = None,
                                  show: bool = True,
                                  figsize: Tuple[int, int] = None,
                                  **kwargs) -> plt.Figure:
        """
        Построение графиков показателей надежности по Баарду.
        
        Args:
            reliability_data: Данные о надежности
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры
            **kwargs: Дополнительные параметры
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['reliability']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Внутренняя надежность
        internal_rel = reliability_data.get('internal_reliability', [])
        obs_ids = reliability_data.get('observation_ids', list(range(len(internal_rel))))
        
        if internal_rel:
            cmap = kwargs.get('cmap', self.COLOR_SCHEMES['reliability']['cmap'])
            
            ax1.bar(range(len(internal_rel)), internal_rel, color='steelblue', alpha=0.7)
            ax1.axhline(y=0.5, color='green', linestyle='--', linewidth=2, 
                       label='Порог 0.5')
            ax1.axhline(y=0.3, color='orange', linestyle='--', linewidth=2, 
                       label='Порог 0.3')
            ax1.set_xlabel('Номер измерения', fontsize=11)
            ax1.set_ylabel('Внутренняя надежность (ρ)', fontsize=11)
            ax1.set_title('Внутренняя надежность измерений', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
            ax1.legend()
        
        # Внешняя надежность
        external_rel = reliability_data.get('external_reliability', [])
        
        if external_rel:
            ax2.bar(range(len(external_rel)), external_rel, color='darkorange', alpha=0.7)
            ax2.axhline(y=np.mean(external_rel), color='red', linestyle='-', linewidth=2,
                       label=f'Среднее: {np.mean(external_rel):.3f}')
            ax2.set_xlabel('Номер измерения', fontsize=11)
            ax2.set_ylabel('Внешняя надежность', fontsize=11)
            ax2.set_title('Внешняя надежность измерений', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
            ax2.legend()
        
        fig.suptitle(title, fontsize=13, fontweight='bold')
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"Графики надежности сохранены в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def plot_network_sketch(self,
                           points: List[Dict[str, Any]],
                           observations: List[Dict[str, Any]],
                           title: str = 'Схема геодезической сети',
                           output_path: Optional[Path] = None,
                           show: bool = True,
                           figsize: Tuple[int, int] = None,
                           **kwargs) -> plt.Figure:
        """
        Построение схемы геодезической сети.
        
        Args:
            points: Список пунктов
            observations: Список измерений
            title: Заголовок графика
            output_path: Путь для сохранения изображения
            show: Показывать график после построения
            figsize: Размер фигуры
            **kwargs: Дополнительные параметры
            
        Returns:
            Figure объект matplotlib
        """
        figsize = figsize or self.FIG_SIZES['error_ellipses']
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Отрисовка измерений (линий)
        points_dict = {p.get('point_id'): p for p in points}
        
        for obs in observations:
            from_id = obs.get('from_point')
            to_id = obs.get('to_point')
            
            if from_id not in points_dict or to_id not in points_dict:
                continue
            
            from_point = points_dict[from_id]
            to_point = points_dict[to_id]
            
            x1 = from_point.get('x') or from_point.get('X')
            y1 = from_point.get('y') or from_point.get('Y')
            x2 = to_point.get('x') or to_point.get('X')
            y2 = to_point.get('y') or to_point.get('Y')
            
            if any(v is None for v in [x1, y1, x2, y2]):
                continue
            
            # Определение типа измерения для цвета
            obs_type = obs.get('obs_type', '').lower()
            if 'direction' in obs_type or 'angle' in obs_type:
                color = 'green'
                alpha = 0.3
            elif 'distance' in obs_type:
                color = 'blue'
                alpha = 0.5
            elif 'leveling' in obs_type or 'height' in obs_type:
                color = 'red'
                alpha = 0.4
            else:
                color = 'gray'
                alpha = 0.3
            
            ax.plot([x1, x2], [y1, y2], '-', color=color, alpha=alpha, linewidth=1)
        
        # Отрисовка пунктов
        x_coords = []
        y_coords = []
        labels = []
        is_fixed = []
        
        for point in points:
            x = point.get('x') or point.get('X')
            y = point.get('y') or point.get('Y')
            
            if x is None or y is None:
                continue
            
            x_coords.append(x)
            y_coords.append(y)
            labels.append(point.get('point_id', ''))
            is_fixed.append(
                point.get('coord_type') in ['fixed', 'initial', 'исходный'] or
                point.get('is_fixed', False)
            )
        
        # Раздельная отрисовка исходных и определяемых пунктов
        fixed_mask = np.array(is_fixed)
        
        if np.any(fixed_mask):
            ax.scatter(
                np.array(x_coords)[fixed_mask],
                np.array(y_coords)[fixed_mask],
                c='red', s=150, marker='^', edgecolors='black', 
                linewidths=1.5, zorder=5, label='Исходные пункты'
            )
        
        if np.any(~fixed_mask):
            ax.scatter(
                np.array(x_coords)[~fixed_mask],
                np.array(y_coords)[~fixed_mask],
                c='blue', s=100, marker='o', edgecolors='black',
                linewidths=1.5, zorder=5, label='Определяемые пункты'
            )
        
        # Подписи пунктов
        for i, label in enumerate(labels):
            if label:
                ax.text(x_coords[i], y_coords[i], label,
                       ha='center', va='bottom', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                alpha=0.8))
        
        ax.set_xlabel('X, м', fontsize=11)
        ax.set_ylabel('Y, м', fontsize=11)
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        # Сохранение
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=self.DEFAULT_DPI, bbox_inches='tight')
            logger.info(f"Схема сети сохранена в {output_path}")
        
        if not show:
            plt.close(fig)
        
        return fig
    
    def create_summary_plot(self,
                           adjustment_result: Dict[str, Any],
                           points: List[Dict[str, Any]],
                           observations: List[Dict[str, Any]],
                           output_dir: Optional[Path] = None,
                           **kwargs) -> Dict[str, Path]:
        """
        Создание набора всех основных графиков для отчета.
        
        Args:
            adjustment_result: Результаты уравнивания
            points: Список пунктов
            observations: Список измерений
            output_dir: Директория для сохранения графиков
            **kwargs: Дополнительные параметры
            
        Returns:
            Словарь с путями к сохраненным файлам
        """
        output_dir = Path(output_dir) if output_dir else Path('./plots')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # 1. Схема сети
        try:
            path = output_dir / 'network_sketch.png'
            self.plot_network_sketch(points, observations, output_path=path, show=False)
            saved_files['network_sketch'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении схемы сети: {e}")
        
        # 2. Эллипсы ошибок
        try:
            path = output_dir / 'error_ellipses.png'
            self.plot_error_ellipses(points, output_path=path, show=False)
            saved_files['error_ellipses'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении эллипсов ошибок: {e}")
        
        # 3. Распределение остатков
        try:
            residuals = np.array([obs.get('residual', 0) for obs in observations])
            path = output_dir / 'residuals_distribution.png'
            self.plot_residuals_distribution(residuals, output_path=path, show=False)
            saved_files['residuals_distribution'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении распределения остатков: {e}")
        
        # 4. Карта точности
        try:
            path = output_dir / 'accuracy_map.png'
            self.plot_accuracy_map(points, output_path=path, show=False)
            saved_files['accuracy_map'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении карты точности: {e}")
        
        # 5. Ковариационная матрица (если есть)
        try:
            if 'covariance_matrix' in adjustment_result:
                cov_matrix = adjustment_result['covariance_matrix']
                if hasattr(cov_matrix, 'toarray'):
                    cov_matrix = cov_matrix.toarray()
                
                path = output_dir / 'correlation_heatmap.png'
                self.plot_correlation_heatmap(cov_matrix, output_path=path, show=False)
                saved_files['correlation_heatmap'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении тепловой карты корреляций: {e}")
        
        # 6. Надежность (если есть)
        try:
            if 'reliability' in adjustment_result:
                path = output_dir / 'reliability_measures.png'
                self.plot_reliability_measures(
                    adjustment_result['reliability'],
                    output_path=path, show=False
                )
                saved_files['reliability_measures'] = path
        except Exception as e:
            logger.error(f"Ошибка при построении графиков надежности: {e}")
        
        logger.info(f"Создано {len(saved_files)} графиков в директории {output_dir}")
        
        return saved_files
