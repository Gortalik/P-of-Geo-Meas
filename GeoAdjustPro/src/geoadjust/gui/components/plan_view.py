"""
Графические компоненты для GeoAdjust Pro

Включает:
- PlanGraphicsView: графическое отображение плана
"""

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont
import math


class PlanGraphicsView(QGraphicsView):
    """Графическое представление плана сети"""
    
    point_clicked = pyqtSignal(str)  # signal с ID пункта
    selection_changed = pyqtSignal(list)  # signal со списком выбранных объектов
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Создание сцены
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Настройка вида
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # Масштабирование
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        # Фоновый цвет
        self.setBackgroundBrush(QBrush(QColor("#f0f0f0")))
        
        # Хранение элементов
        self.points = {}  # ID -> QGraphicsItem
        self.observations = []  # Список QGraphicsLineItem
        self.grid_lines = []  # Линии сетки
        self.grid_labels = []  # Подписи сетки
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Инициализация адаптивной сетки
        self._init_adaptive_grid()
    
    def _init_adaptive_grid(self):
        """Инициализация адаптивной сетки"""
        self._draw_adaptive_grid()
    
    def _draw_adaptive_grid(self, min_x=-500, max_x=500, min_y=-500, max_y=500):
        """Отрисовка адаптивной математической сетки"""
        # Очистка старой сетки
        for line in self.grid_lines:
            self.scene.removeItem(line)
        for label in self.grid_labels:
            self.scene.removeItem(label)
        self.grid_lines.clear()
        self.grid_labels.clear()
        
        # Если есть точки, адаптируем сетку под них
        if self.points:
            points_coords = []
            for point_item in self.points.values():
                rect = point_item.boundingRect()
                center = point_item.mapToScene(rect.center())
                points_coords.append((center.x(), center.y()))
            
            if points_coords:
                xs = [p[0] for p in points_coords]
                ys = [p[1] for p in points_coords]
                min_x, max_x = min(xs) - 100, max(xs) + 100
                min_y, max_y = min(ys) - 100, max(ys) + 100
        
        # Вычисление адаптивного шага сетки
        range_x = max_x - min_x
        range_y = max_y - min_y
        
        # Определение оптимального шага (степень 10)
        def get_grid_step(range_val):
            if range_val <= 0:
                return 100
            magnitude = 10 ** math.floor(math.log10(range_val))
            steps = [magnitude, magnitude * 2, magnitude * 5]
            for step in steps:
                if range_val / step <= 15:  # Не более 15 линий
                    return step
            return steps[-1]
        
        step_x = get_grid_step(range_x)
        step_y = get_grid_step(range_y)
        
        # Рисование вертикальных линий
        pen_major = QPen(QColor("#cccccc"), 1)
        pen_minor = QPen(QColor("#e0e0e0"), 1, Qt.DotLine)
        
        x = math.floor(min_x / step_x) * step_x
        while x <= max_x:
            pen = pen_major if x == 0 else pen_minor
            line = QGraphicsLineItem(x, min_y, x, max_y)
            line.setPen(pen)
            line.setZValue(-100)  # За всеми элементами
            self.scene.addItem(line)
            self.grid_lines.append(line)
            
            # Подпись координаты
            if x % (step_x * 2) == 0:  # Подписываем каждую вторую линию
                label = QGraphicsTextItem(f"{int(x)}")
                label.setPos(x + 5, max_y - 20)
                label.setDefaultTextColor(QColor("#888888"))
                label.setFont(QFont("Arial", 8))
                label.setZValue(-99)
                self.scene.addItem(label)
                self.grid_labels.append(label)
            
            x += step_x
        
        # Рисование горизонтальных линий
        y = math.floor(min_y / step_y) * step_y
        while y <= max_y:
            pen = pen_major if y == 0 else pen_minor
            line = QGraphicsLineItem(min_x, y, max_x, y)
            line.setPen(pen)
            line.setZValue(-100)
            self.scene.addItem(line)
            self.grid_lines.append(line)
            
            # Подпись координаты
            if y % (step_y * 2) == 0:
                label = QGraphicsTextItem(f"{int(y)}")
                label.setPos(min_x + 5, y + 5)
                label.setDefaultTextColor(QColor("#888888"))
                label.setFont(QFont("Arial", 8))
                label.setZValue(-99)
                self.scene.addItem(label)
                self.grid_labels.append(label)
            
            y += step_y
    
    def add_point(self, point_id: str, x: float, y: float, 
                  color: QColor = QColor("red"), size: int = 8,
                  point_type: str = "FIXED"):
        """Добавление пункта на план в реальном времени"""
        
        # Определение цвета по типу пункта
        if point_type == "FIXED":
            color = QColor("blue")
        elif point_type == "FREE":
            color = QColor("red")
        else:
            color = QColor("green")
        
        # Создание эллипса (круга) для пункта
        radius = size / 2.0
        ellipse = QGraphicsEllipseItem(x - radius, y - radius, size, size)
        ellipse.setPen(QPen(color, 2))
        ellipse.setBrush(QBrush(color))
        ellipse.setFlag(ellipse.ItemIsSelectable)
        ellipse.setData(0, point_id)  # Сохранение ID в элементе
        
        # Добавление на сцену
        self.scene.addItem(ellipse)
        self.points[point_id] = ellipse
        
        # Добавление подписи пункта
        text_item = QGraphicsTextItem(point_id)
        text_item.setPos(x + size/2, y - size/2)
        text_item.setDefaultTextColor(QColor("black"))
        text_item.setFont(QFont("Arial", 8))
        self.scene.addItem(text_item)
        
        # Сохранение ссылки на текст для последующего удаления
        ellipse.setData(1, text_item)
        
        # Обновление сетки при добавлении точки
        self._draw_adaptive_grid()
    
    def remove_point(self, point_id: str):
        """Удаление пункта с плана"""
        if point_id in self.points:
            item = self.points[point_id]
            # Удаление текста подписи если он есть
            text_item = item.data(1)
            if text_item:
                self.scene.removeItem(text_item)
            self.scene.removeItem(item)
            del self.points[point_id]
    
    def add_observation(self, from_point: str, to_point: str, 
                        obs_type: str = "direction"):
        """Добавление измерения на план"""
        
        if from_point not in self.points or to_point not in self.points:
            return
        
        # Получение координат пунктов
        from_item = self.points[from_point]
        to_item = self.points[to_point]
        
        from_rect = from_item.boundingRect()
        to_rect = to_item.boundingRect()
        
        from_center = from_item.mapToScene(from_rect.center())
        to_center = to_item.mapToScene(to_rect.center())
        
        # Создание линии
        line = QGraphicsLineItem(from_center.x(), from_center.y(),
                                 to_center.x(), to_center.y())
        
        # Цвет по типу измерения
        if obs_type == "direction":
            line.setPen(QPen(QColor("green"), 1))
        elif obs_type == "distance":
            line.setPen(QPen(QColor("orange"), 2))
        elif obs_type == "height_diff":
            line.setPen(QPen(QColor("purple"), 1, Qt.DashLine))
        
        line.setData(0, f"{from_point}-{to_point}")
        self.observations.append(line)
        self.scene.addItem(line)
    
    def clear_all(self):
        """Очистка плана"""
        self.scene.clear()
        self.points.clear()
        self.observations.clear()
        self.grid_lines.clear()
        self.grid_labels.clear()
        # Восстановление пустой сетки
        self._draw_adaptive_grid()
    
    def fit_to_contents(self):
        """Подгонка масштаба под содержимое"""
        if self.scene.items():
            items_rect = self.scene.itemsBoundingRect()
            self.fitInView(items_rect, Qt.KeepAspectRatio)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        zoom_in_action = menu.addAction("Приблизить")
        zoom_out_action = menu.addAction("Отдалить")
        fit_action = menu.addAction("Показать всё")
        menu.addSeparator()
        export_action = menu.addAction("Экспорт изображения...")
        
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == zoom_in_action:
            self.scale(1.2, 1.2)
        elif action == zoom_out_action:
            self.scale(1/1.2, 1/1.2)
        elif action == fit_action:
            self.fit_to_contents()
        elif action == export_action:
            self._export_image()
    
    def _export_image(self):
        """Экспорт плана в изображение"""
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtGui import QPixmap
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт изображения", "", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            pixmap = QPixmap(self.scene.sceneRect().size().toSize())
            self.scene.render(pixmap)
            pixmap.save(file_path)
    
    def mousePressEvent(self, event):
        """Обработка нажатия кнопки мыши"""
        super().mousePressEvent(event)
        
        # Проверка клика по пункту
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            items = self.scene.items(pos)
            
            for item in items:
                point_id = item.data(0)
                if point_id and isinstance(item, QGraphicsEllipseItem):
                    self.point_clicked.emit(point_id)
                    break
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.scale(1.2, 1.2)
        elif event.key() == Qt.Key_Minus:
            self.scale(1/1.2, 1/1.2)
        elif event.key() == Qt.Key_Home:
            self.fit_to_contents()
        else:
            super().keyPressEvent(event)
