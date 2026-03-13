"""
Графические компоненты для GeoAdjust Pro

Включает:
- PlanGraphicsView: графическое отображение плана
"""

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPen, QBrush, QColor


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
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setViewportUpdateMode(self.SmartViewportUpdate)
        self.setDragMode(self.RubberBandDrag)
        
        # Масштабирование
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setResizeAnchor(self.AnchorViewCenter)
        
        # Фоновый цвет
        self.setBackgroundBrush(QBrush(QColor("#f0f0f0")))
        
        # Хранение элементов
        self.points = {}  # ID -> QGraphicsItem
        self.observations = []  # Список QGraphicsLineItem
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def add_point(self, point_id: str, x: float, y: float, 
                  color: QColor = QColor("red"), size: int = 8,
                  point_type: str = "FIXED"):
        """Добавление пункта на план"""
        
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
        
        # Добавление подписи
        # TODO: Добавить текст с ID пункта
    
    def remove_point(self, point_id: str):
        """Удаление пункта с плана"""
        if point_id in self.points:
            item = self.points[point_id]
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
