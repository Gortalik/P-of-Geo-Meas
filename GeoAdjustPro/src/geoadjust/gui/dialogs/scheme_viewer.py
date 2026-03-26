"""
Окно просмотра схемы геодезической сети
"""

from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QToolBar, QAction,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPolygonItem,
    QPushButton, QLabel, QComboBox, QCheckBox, QGroupBox,
    QSlider, QSpinBox, QColorDialog, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QFont, QPolygonF,
    QTransform, QPainterPath, QImage
)
import logging
import math

logger = logging.getLogger(__name__)


class NetworkGraphicsView(QGraphicsView):
    """Графическое представление геодезической сети"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Настройки отображения
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Параметры отображения
        self.show_point_names = True
        self.show_point_coords = False
        self.show_observations = True
        self.show_error_ellipses = False
        self.show_grid = True
        
        self.point_size = 8
        self.line_width = 2
        self.font_size = 10
        
        # Цвета
        self.color_fixed_point = QColor(255, 0, 0)  # Красный
        self.color_free_point = QColor(0, 0, 255)   # Синий
        self.color_approximate_point = QColor(255, 165, 0)  # Оранжевый
        self.color_observation = QColor(0, 128, 0)  # Зеленый
        self.color_grid = QColor(200, 200, 200)     # Светло-серый
        
        self._zoom_factor = 1.0
    
    def wheelEvent(self, event):
        """Обработка прокрутки колеса мыши для масштабирования"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self._zoom_factor *= zoom_factor
        else:
            zoom_factor = zoom_out_factor
            self._zoom_factor *= zoom_factor
        
        self.scale(zoom_factor, zoom_factor)
    
    def draw_network(self, points: List[Dict], observations: List[Dict] = None):
        """Отрисовка геодезической сети"""
        self.scene.clear()
        
        if not points:
            return
        
        # Определение границ сети
        min_x = min(p['x'] for p in points)
        max_x = max(p['x'] for p in points)
        min_y = min(p['y'] for p in points)
        max_y = max(p['y'] for p in points)
        
        # Добавление отступов
        margin = max((max_x - min_x), (max_y - min_y)) * 0.1
        min_x -= margin
        max_x += margin
        min_y -= margin
        max_y += margin
        
        # Установка размера сцены
        self.scene.setSceneRect(min_x, min_y, max_x - min_x, max_y - min_y)
        
        # Отрисовка сетки
        if self.show_grid:
            self._draw_grid(min_x, max_x, min_y, max_y)
        
        # Отрисовка измерений (линий)
        if self.show_observations and observations:
            self._draw_observations(observations, points)
        
        # Отрисовка пунктов
        self._draw_points(points)
        
        # Подгонка масштаба
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def _draw_grid(self, min_x: float, max_x: float, min_y: float, max_y: float):
        """Отрисовка координатной сетки"""
        pen = QPen(self.color_grid, 0.5, Qt.DotLine)
        
        # Определение шага сетки
        range_x = max_x - min_x
        range_y = max_y - min_y
        
        # Выбор подходящего шага
        step = self._calculate_grid_step(max(range_x, range_y))
        
        # Вертикальные линии
        x = math.ceil(min_x / step) * step
        while x <= max_x:
            line = self.scene.addLine(x, min_y, x, max_y, pen)
            line.setZValue(-2)
            x += step
        
        # Горизонтальные линии
        y = math.ceil(min_y / step) * step
        while y <= max_y:
            line = self.scene.addLine(min_x, y, max_x, y, pen)
            line.setZValue(-2)
            y += step
    
    def _calculate_grid_step(self, range_val: float) -> float:
        """Расчет шага сетки"""
        magnitude = 10 ** math.floor(math.log10(range_val))
        
        if range_val / magnitude < 2:
            return magnitude / 5
        elif range_val / magnitude < 5:
            return magnitude / 2
        else:
            return magnitude
    
    def _draw_observations(self, observations: List[Dict], points: List[Dict]):
        """Отрисовка измерений"""
        # Создание словаря пунктов для быстрого поиска
        points_dict = {p['name']: p for p in points}
        
        pen = QPen(self.color_observation, self.line_width)
        
        for obs in observations:
            from_point_name = obs.get('from_point')
            to_point_name = obs.get('to_point')
            
            if from_point_name not in points_dict or to_point_name not in points_dict:
                continue
            
            from_point = points_dict[from_point_name]
            to_point = points_dict[to_point_name]
            
            # Отрисовка линии
            line = self.scene.addLine(
                from_point['x'], from_point['y'],
                to_point['x'], to_point['y'],
                pen
            )
            line.setZValue(0)
            
            # Добавление стрелки для направлений
            if obs.get('type') == 'direction':
                self._draw_arrow(from_point, to_point)
    
    def _draw_arrow(self, from_point: Dict, to_point: Dict):
        """Отрисовка стрелки на линии"""
        # Вычисление направления
        dx = to_point['x'] - from_point['x']
        dy = to_point['y'] - from_point['y']
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0:
            return
        
        # Нормализация
        dx /= length
        dy /= length
        
        # Размер стрелки
        arrow_size = length * 0.1
        arrow_angle = math.pi / 6  # 30 градусов
        
        # Точка стрелки (80% от длины линии)
        arrow_x = from_point['x'] + dx * length * 0.8
        arrow_y = from_point['y'] + dy * length * 0.8
        
        # Вычисление точек стрелки
        angle = math.atan2(dy, dx)
        
        p1_x = arrow_x - arrow_size * math.cos(angle - arrow_angle)
        p1_y = arrow_y - arrow_size * math.sin(angle - arrow_angle)
        
        p2_x = arrow_x - arrow_size * math.cos(angle + arrow_angle)
        p2_y = arrow_y - arrow_size * math.sin(angle + arrow_angle)
        
        # Отрисовка стрелки
        polygon = QPolygonF([
            QPointF(arrow_x, arrow_y),
            QPointF(p1_x, p1_y),
            QPointF(p2_x, p2_y)
        ])
        
        brush = QBrush(self.color_observation)
        pen = QPen(self.color_observation)
        arrow_item = self.scene.addPolygon(polygon, pen, brush)
        arrow_item.setZValue(1)
    
    def _draw_points(self, points: List[Dict]):
        """Отрисовка пунктов"""
        for point in points:
            x = point['x']
            y = point['y']
            point_type = point.get('type', 'free')
            name = point.get('name', '')
            
            # Выбор цвета в зависимости от типа
            if point_type == 'fixed':
                color = self.color_fixed_point
                symbol = 'triangle'
            elif point_type == 'approximate':
                color = self.color_approximate_point
                symbol = 'square'
            else:
                color = self.color_free_point
                symbol = 'circle'
            
            # Отрисовка символа пункта
            self._draw_point_symbol(x, y, color, symbol)
            
            # Отрисовка названия
            if self.show_point_names:
                self._draw_point_label(x, y, name)
            
            # Отрисовка координат
            if self.show_point_coords:
                coord_text = f"({x:.3f}, {y:.3f})"
                self._draw_point_coords(x, y, coord_text)
            
            # Отрисовка эллипса ошибок
            if self.show_error_ellipses and 'error_ellipse' in point:
                self._draw_error_ellipse(x, y, point['error_ellipse'])
    
    def _draw_point_symbol(self, x: float, y: float, color: QColor, symbol: str):
        """Отрисовка символа пункта"""
        pen = QPen(color, 2)
        brush = QBrush(color)
        
        size = self.point_size
        
        if symbol == 'circle':
            item = self.scene.addEllipse(
                x - size/2, y - size/2, size, size,
                pen, brush
            )
        elif symbol == 'square':
            item = self.scene.addRect(
                x - size/2, y - size/2, size, size,
                pen, brush
            )
        elif symbol == 'triangle':
            h = size * math.sqrt(3) / 2
            polygon = QPolygonF([
                QPointF(x, y - h * 2/3),
                QPointF(x - size/2, y + h * 1/3),
                QPointF(x + size/2, y + h * 1/3)
            ])
            item = self.scene.addPolygon(polygon, pen, brush)
        
        item.setZValue(2)
    
    def _draw_point_label(self, x: float, y: float, text: str):
        """Отрисовка названия пункта"""
        label = self.scene.addText(text)
        label.setDefaultTextColor(Qt.black)
        
        font = QFont()
        font.setPointSize(self.font_size)
        font.setBold(True)
        label.setFont(font)
        
        # Позиционирование справа-сверху от пункта
        offset = self.point_size
        label.setPos(x + offset, y - offset - label.boundingRect().height())
        label.setZValue(3)
    
    def _draw_point_coords(self, x: float, y: float, text: str):
        """Отрисовка координат пункта"""
        label = self.scene.addText(text)
        label.setDefaultTextColor(QColor(100, 100, 100))
        
        font = QFont()
        font.setPointSize(self.font_size - 2)
        label.setFont(font)
        
        # Позиционирование снизу от пункта
        offset = self.point_size
        label.setPos(x + offset, y + offset)
        label.setZValue(3)
    
    def _draw_error_ellipse(self, x: float, y: float, ellipse_data: Dict):
        """Отрисовка эллипса ошибок"""
        a = ellipse_data.get('semi_major', 0.1)  # Большая полуось
        b = ellipse_data.get('semi_minor', 0.05)  # Малая полуось
        angle = ellipse_data.get('azimuth', 0.0)  # Азимут большой полуоси
        
        # Масштабирование эллипса для видимости
        scale_factor = 100  # Увеличение в 100 раз для видимости
        a *= scale_factor
        b *= scale_factor
        
        pen = QPen(QColor(255, 0, 0, 128), 1.5)
        brush = QBrush(QColor(255, 0, 0, 30))
        
        ellipse = self.scene.addEllipse(
            -a, -b, 2*a, 2*b,
            pen, brush
        )
        
        # Поворот эллипса
        ellipse.setPos(x, y)
        ellipse.setRotation(math.degrees(angle))
        ellipse.setZValue(1)
    
    def export_to_image(self, file_path: str):
        """Экспорт схемы в изображение"""
        rect = self.scene.sceneRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
        image.fill(Qt.white)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        self.scene.render(painter)
        painter.end()
        
        image.save(file_path)


class SchemeViewerDialog(QDialog):
    """Диалог просмотра схемы геодезической сети"""
    
    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        
        self.project = project
        
        self.setWindowTitle("Схема геодезической сети")
        self.setMinimumSize(1000, 700)
        
        self._create_ui()
        
        if project:
            self._load_network()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Основная область
        main_layout = QHBoxLayout()
        
        # Графическое представление
        self.graphics_view = NetworkGraphicsView()
        main_layout.addWidget(self.graphics_view, stretch=4)
        
        # Панель настроек
        settings_panel = self._create_settings_panel()
        main_layout.addWidget(settings_panel, stretch=1)
        
        layout.addLayout(main_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Экспорт в изображение")
        export_btn.clicked.connect(self._export_image)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_toolbar(self) -> QToolBar:
        """Создание панели инструментов"""
        toolbar = QToolBar()
        
        # Масштабирование
        zoom_in_action = QAction("Увеличить", self)
        zoom_in_action.triggered.connect(lambda: self.graphics_view.scale(1.2, 1.2))
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Уменьшить", self)
        zoom_out_action.triggered.connect(lambda: self.graphics_view.scale(1/1.2, 1/1.2))
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction("По размеру окна", self)
        fit_action.triggered.connect(lambda: self.graphics_view.fitInView(
            self.graphics_view.scene.sceneRect(), Qt.KeepAspectRatio
        ))
        toolbar.addAction(fit_action)
        
        toolbar.addSeparator()
        
        # Обновление
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self._load_network)
        toolbar.addAction(refresh_action)
        
        return toolbar
    
    def _create_settings_panel(self) -> QGroupBox:
        """Создание панели настроек"""
        group = QGroupBox("Настройки отображения")
        layout = QVBoxLayout(group)
        
        # Чекбоксы
        self.show_names_check = QCheckBox("Показывать названия пунктов")
        self.show_names_check.setChecked(True)
        self.show_names_check.toggled.connect(self._update_display)
        layout.addWidget(self.show_names_check)
        
        self.show_coords_check = QCheckBox("Показывать координаты")
        self.show_coords_check.toggled.connect(self._update_display)
        layout.addWidget(self.show_coords_check)
        
        self.show_obs_check = QCheckBox("Показывать измерения")
        self.show_obs_check.setChecked(True)
        self.show_obs_check.toggled.connect(self._update_display)
        layout.addWidget(self.show_obs_check)
        
        self.show_ellipses_check = QCheckBox("Показывать эллипсы ошибок")
        self.show_ellipses_check.toggled.connect(self._update_display)
        layout.addWidget(self.show_ellipses_check)
        
        self.show_grid_check = QCheckBox("Показывать сетку")
        self.show_grid_check.setChecked(True)
        self.show_grid_check.toggled.connect(self._update_display)
        layout.addWidget(self.show_grid_check)
        
        layout.addStretch()
        
        return group
    
    def _load_network(self):
        """Загрузка данных сети"""
        if not self.project:
            return
        
        try:
            points = self.project.get_points()
            observations = self.project.get_observations()
            
            if not points:
                QMessageBox.information(self, "Информация", "В проекте нет пунктов")
                return
            
            self.graphics_view.draw_network(points, observations)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки сети: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сеть:\n{str(e)}")
    
    def _update_display(self):
        """Обновление отображения"""
        self.graphics_view.show_point_names = self.show_names_check.isChecked()
        self.graphics_view.show_point_coords = self.show_coords_check.isChecked()
        self.graphics_view.show_observations = self.show_obs_check.isChecked()
        self.graphics_view.show_error_ellipses = self.show_ellipses_check.isChecked()
        self.graphics_view.show_grid = self.show_grid_check.isChecked()
        
        self._load_network()
    
    def _export_image(self):
        """Экспорт схемы в изображение"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт схемы",
            "",
            "PNG изображение (*.png);;JPEG изображение (*.jpg);;Все файлы (*)"
        )
        
        if file_path:
            try:
                self.graphics_view.export_to_image(file_path)
                QMessageBox.information(self, "Успех", f"Схема экспортирована в:\n{file_path}")
            except Exception as e:
                logger.error(f"Ошибка экспорта: {e}", exc_info=True)
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать схему:\n{str(e)}")
