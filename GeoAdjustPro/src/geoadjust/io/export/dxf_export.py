"""
Модуль экспорта схемы сети в формат DXF для работы в AutoCAD.

Поддерживает экспорт:
- Пунктов сети (точки и подписи)
- Измерений (линии между пунктами)
- Эллипсов ошибок положения пунктов
- Слои для различных типов объектов
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

try:
    import ezdxf
    from ezdxf import units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    ezdxf = None
    units = None

logger = logging.getLogger(__name__)


class DXFExporter:
    """
    Экспорт результатов уравнивания геодезической сети в формат DXF.
    
    Пример использования:
        exporter = DXFExporter()
        exporter.export_network(network_data, output_path="network.dxf")
    """
    
    # Цвета для различных типов объектов
    COLORS = {
        'points': 1,          # Красный - пункты
        'directions': 2,      # Зеленый - направления
        'distances': 3,       # Желтый - расстояния
        'leveling': 4,        # Голубой - нивелирование
        'gnss_vectors': 5,    # Синий - векторы ГНСС
        'error_ellipses': 6,  # Пурпурный - эллипсы ошибок
        'fixed_points': 7,    # Белый - исходные пункты
        'text': 0,            # Черный - текст
    }
    
    # Толщины линий для различных типов объектов
    LINEWEIGHTS = {
        'points': 0,
        'directions': 18,
        'distances': 25,
        'leveling': 18,
        'gnss_vectors': 30,
        'error_ellipses': 15,
        'fixed_points': 0,
        'text': 0,
    }
    
    def __init__(self, dxf_version: str = 'R2010'):
        """
        Инициализация DXF экспортера.
        
        Args:
            dxf_version: Версия формата DXF ('R2010', 'R2007', 'R2004', etc.)
        """
        if not EZDXF_AVAILABLE:
            raise ImportError(
                "Библиотека ezdxf не установлена. "
                "Установите её командой: pip install ezdxf"
            )
        
        self.dxf_version = dxf_version
        self.doc = ezdxf.new(dxf_version)
        self.msp = self.doc.modelspace()
        
        # Настройка единиц измерения (используем M для метров в ezdxf 1.x)
        try:
            self.doc.units = units.M
        except AttributeError:
            # Для старых версий ezdxf
            self.doc.units = 4  # 4 = метры
        
        # Создание слоёв
        self._create_layers()
    
    def _create_layers(self):
        """Создание слоёв для различных типов объектов."""
        layers_config = [
            ('POINTS', self.COLORS['points']),
            ('FIXED_POINTS', self.COLORS['fixed_points']),
            ('DIRECTIONS', self.COLORS['directions']),
            ('DISTANCES', self.COLORS['distances']),
            ('LEVELING', self.COLORS['leveling']),
            ('GNSS_VECTORS', self.COLORS['gnss_vectors']),
            ('ERROR_ELLIPSES', self.COLORS['error_ellipses']),
            ('TEXT', self.COLORS['text']),
            ('COORDINATE_GRID', 8),
        ]
        
        for layer_name, color in layers_config:
            if layer_name not in self.doc.layers:
                self.doc.layers.add(layer_name, color=color)
    
    def export_network(self, network_data: Dict[str, Any], 
                      output_path: Path,
                      export_options: Optional[Dict[str, bool]] = None) -> bool:
        """
        Экспорт геодезической сети в DXF файл.
        
        Args:
            network_data: Данные сети (пункты, измерения, результаты уравнивания)
            output_path: Путь к выходному DXF файлу
            export_options: Опции экспорта (какие объекты экспортировать)
            
        Returns:
            True если экспорт успешен, False иначе
        """
        try:
            options = {
                'export_points': True,
                'export_observations': True,
                'export_error_ellipses': True,
                'export_text_labels': True,
                'export_coordinate_grid': False,
                **(export_options or {})
            }
            
            # Экспорт пунктов
            if options.get('export_points', True):
                self._export_points(network_data)
            
            # Экспорт измерений
            if options.get('export_observations', True):
                self._export_observations(network_data)
            
            # Экспорт эллипсов ошибок
            if options.get('export_error_ellipses', True):
                self._export_error_ellipses(network_data)
            
            # Экспорт текстовых подписей
            if options.get('export_text_labels', True):
                self._export_text_labels(network_data)
            
            # Экспорт координатной сетки
            if options.get('export_coordinate_grid', False):
                self._export_coordinate_grid(network_data)
            
            # Сохранение файла
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.doc.saveas(str(output_path))
            
            logger.info(f"Сеть успешно экспортирована в {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте в DXF: {e}", exc_info=True)
            return False
    
    def _export_points(self, network_data: Dict[str, Any]):
        """Экспорт пунктов сети."""
        points = network_data.get('points', [])
        points_dict = network_data.get('points_dict', {})
        
        for point in points:
            x = point.get('x') or point.get('X')
            y = point.get('y') or point.get('Y')
            h = point.get('h') or point.get('H') or 0.0
            
            if x is None or y is None:
                continue
            
            # Определение типа пункта
            coord_type = point.get('coord_type', 'unknown')
            is_fixed = coord_type in ['fixed', 'initial', 'исходный'] or point.get('is_fixed', False)
            
            # Слой и стиль
            layer = 'FIXED_POINTS' if is_fixed else 'POINTS'
            
            # Создание точки
            self.msp.add_point(
                (x, y, h),
                dxfattribs={'layer': layer}
            )
            
            # Создание маркера пункта (круг)
            marker_size = 0.5 if is_fixed else 0.3
            self.msp.add_circle(
                (x, y, h),
                radius=marker_size,
                dxfattribs={
                    'layer': layer,
                    'lineweight': self.LINEWEIGHTS['points']
                }
            )
    
    def _export_observations(self, network_data: Dict[str, Any]):
        """Экспорт измерений."""
        observations = network_data.get('observations', [])
        points_dict = network_data.get('points_dict', {})
        
        for obs in observations:
            from_point_id = obs.get('from_point')
            to_point_id = obs.get('to_point')
            
            if not from_point_id or not to_point_id:
                continue
            
            from_point = points_dict.get(from_point_id)
            to_point = points_dict.get(to_point_id)
            
            if not from_point or not to_point:
                continue
            
            x1 = from_point.get('x') or from_point.get('X')
            y1 = from_point.get('y') or from_point.get('Y')
            z1 = from_point.get('h') or from_point.get('H') or 0.0
            
            x2 = to_point.get('x') or to_point.get('X')
            y2 = to_point.get('y') or to_point.get('Y')
            z2 = to_point.get('h') or to_point.get('H') or 0.0
            
            if any(v is None for v in [x1, y1, x2, y2]):
                continue
            
            # Определение типа измерения
            obs_type = obs.get('obs_type', 'unknown').lower()
            
            if 'direction' in obs_type or 'angle' in obs_type or 'azimuth' in obs_type:
                layer = 'DIRECTIONS'
            elif 'distance' in obs_type or 'length' in obs_type:
                layer = 'DISTANCES'
            elif 'height_diff' in obs_type or 'leveling' in obs_type or 'elevation' in obs_type:
                layer = 'LEVELING'
            elif 'gnss' in obs_type or 'vector' in obs_type or 'baseline' in obs_type:
                layer = 'GNSS_VECTORS'
            else:
                layer = 'DIRECTIONS'  # По умолчанию
            
            # Создание линии
            self.msp.add_line(
                (x1, y1),
                (x2, y2),
                dxfattribs={
                    'layer': layer,
                    'lineweight': self.LINEWEIGHTS.get(layer, 18)
                }
            )
            
            # Добавление стрелки направления
            self._add_arrow(x1, y1, x2, y2, layer)
    
    def _add_arrow(self, x1: float, y1: float, x2: float, y2: float, layer: str):
        """Добавление стрелки на линию направления."""
        import math
        
        # Вычисление середины линии
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Вычисление угла направления
        dx = x2 - x1
        dy = y2 - y1
        angle = math.degrees(math.atan2(dy, dx))
        
        # Размер стрелки
        arrow_size = 0.3
        
        # Создание треугольной стрелки
        arrow_points = [
            (mid_x + arrow_size * math.cos(math.radians(angle)),
             mid_y + arrow_size * math.sin(math.radians(angle))),
            (mid_x - arrow_size * math.cos(math.radians(angle - 30)),
             mid_y - arrow_size * math.sin(math.radians(angle - 30))),
            (mid_x - arrow_size * math.cos(math.radians(angle + 30)),
             mid_y - arrow_size * math.sin(math.radians(angle + 30))),
        ]
        
        self.msp.add_lwpolyline(
            arrow_points + [arrow_points[0]],  # Замыкаем полилинию
            dxfattribs={
                'layer': layer,
                'fillcolor': self.COLORS.get(layer, 0)
            }
        )
    
    def _export_error_ellipses(self, network_data: Dict[str, Any]):
        """Экспорт эллипсов ошибок положения пунктов."""
        error_ellipses = network_data.get('error_ellipses', [])
        points = network_data.get('points', [])
        
        # Если эллипсы не предоставлены отдельно, ищем их в данных пунктов
        if not error_ellipses:
            for point in points:
                if 'ellipse' in point or 'error_ellipse' in point:
                    ellipse_data = point.get('ellipse') or point.get('error_ellipse')
                    if ellipse_data:
                        error_ellipses.append({
                            'point_id': point.get('point_id'),
                            **ellipse_data
                        })
        
        for ellipse in error_ellipses:
            center_x = ellipse.get('center_x')
            center_y = ellipse.get('center_y')
            
            # Если координаты центра не указаны, пытаемся найти пункт
            if center_x is None or center_y is None:
                point_id = ellipse.get('point_id')
                for point in points:
                    if point.get('point_id') == point_id:
                        center_x = point.get('x') or point.get('X')
                        center_y = point.get('y') or point.get('Y')
                        break
            
            if center_x is None or center_y is None:
                continue
            
            # Параметры эллипса
            a = ellipse.get('a', 0.01)  # Большая полуось
            b = ellipse.get('b', 0.01)  # Малая полуось
            alpha = ellipse.get('alpha', 0.0)  # Угол поворота в радианах
            
            # Преобразование угла в градусы для DXF
            rotation_angle = math.degrees(alpha) if isinstance(alpha, float) else 0.0
            
            # Создание эллипса
            try:
                ellipse_entity = self.msp.add_ellipse(
                    center=(center_x, center_y),
                    major_axis=(a, 0),
                    ratio=b / a if a > 0 else 1.0,
                    rotation=rotation_angle,
                    dxfattribs={
                        'layer': 'ERROR_ELLIPSES',
                        'lineweight': self.LINEWEIGHTS['error_ellipses'],
                        'linetype': 'DASHED'
                    }
                )
            except Exception as e:
                logger.warning(f"Не удалось создать эллипс ошибки: {e}")
                
                # Альтернатива: создание круга вместо эллипса
                avg_radius = (a + b) / 2
                self.msp.add_circle(
                    (center_x, center_y),
                    radius=avg_radius,
                    dxfattribs={
                        'layer': 'ERROR_ELLIPSES',
                        'linetype': 'DASHED'
                    }
                )
    
    def _export_text_labels(self, network_data: Dict[str, Any]):
        """Экспорт текстовых подписей пунктов."""
        points = network_data.get('points', [])
        
        for point in points:
            x = point.get('x') or point.get('X')
            y = point.get('y') or point.get('Y')
            point_id = point.get('point_id', '')
            
            if x is None or y is None or not point_id:
                continue
            
            # Смещение текста относительно пункта
            offset_x = 0.5
            offset_y = 0.5
            
            # Создание текста
            text = self.msp.add_text(
                point_id,
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 0.4,
                    'rotation': 0
                }
            )
            
            # Позиционирование текста
            text.set_pos((x + offset_x, y + offset_y), align='LEFT_BOTTOM')
            
            # Дополнительно: экспорт координат
            h = point.get('h') or point.get('H')
            if h is not None:
                coord_text = f"H={h:.3f}"
                h_text = self.msp.add_text(
                    coord_text,
                    dxfattribs={
                        'layer': 'TEXT',
                        'height': 0.3,
                        'rotation': 0
                    }
                )
                h_text.set_pos((x + offset_x, y + offset_y - 0.4), align='LEFT_TOP')
    
    def _export_coordinate_grid(self, network_data: Dict[str, Any]):
        """Экспорт координатной сетки."""
        points = network_data.get('points', [])
        
        if not points:
            return
        
        # Определение границ сети
        xs = [p.get('x') or p.get('X') or 0 for p in points if p.get('x') or p.get('X')]
        ys = [p.get('y') or p.get('Y') or 0 for p in points if p.get('y') or p.get('Y')]
        
        if not xs or not ys:
            return
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Добавление отступов
        margin_x = (max_x - min_x) * 0.1
        margin_y = (max_y - min_y) * 0.1
        
        min_x -= margin_x
        max_x += margin_x
        min_y -= margin_y
        max_y += margin_y
        
        # Определение шага сетки
        dx = (max_x - min_x) / 10
        dy = (max_y - min_y) / 10
        
        step = max(dx, dy)
        
        # Округление шага до удобного значения
        for round_val in [1000, 500, 100, 50, 10, 5, 1, 0.5, 0.1]:
            if step >= round_val:
                step = round_val
                break
        
        # Создание вертикальных линий
        x = min_x
        while x <= max_x:
            self.msp.add_line(
                (x, min_y),
                (x, max_y),
                dxfattribs={
                    'layer': 'COORDINATE_GRID',
                    'lineweight': 9,
                    'linetype': 'DOTTED'
                }
            )
            x += step
        
        # Создание горизонтальных линий
        y = min_y
        while y <= max_y:
            self.msp.add_line(
                (min_x, y),
                (max_x, y),
                dxfattribs={
                    'layer': 'COORDINATE_GRID',
                    'lineweight': 9,
                    'linetype': 'DOTTED'
                }
            )
            y += step
    
    def create_summary_report(self, network_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Создание сводного отчета о количестве экспортируемых объектов.
        
        Args:
            network_data: Данные сети
            
        Returns:
            Словарь с количеством объектов по типам
        """
        report = {
            'points': len(network_data.get('points', [])),
            'fixed_points': sum(
                1 for p in network_data.get('points', [])
                if p.get('coord_type') in ['fixed', 'initial', 'исходный'] or p.get('is_fixed', False)
            ),
            'observations': len(network_data.get('observations', [])),
            'error_ellipses': len(network_data.get('error_ellipses', [])),
        }
        
        # Подсчет по типам измерений
        obs_types = {}
        for obs in network_data.get('observations', []):
            obs_type = obs.get('obs_type', 'unknown')
            obs_types[obs_type] = obs_types.get(obs_type, 0) + 1
        
        report['observation_types'] = obs_types
        
        return report


# Импорт math для функции _add_arrow
import math
