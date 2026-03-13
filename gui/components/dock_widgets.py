"""
GeoAdjust Pro - Компоненты док-виджетов
Таблицы, деревья и графические представления
"""

from typing import Optional, List, Any
from PyQt5.QtWidgets import (
    QTableView, QTreeView, QGraphicsView, QGraphicsScene, QWidget,
    QVBoxLayout, QMenu, QAction, QAbstractItemView, QApplication,
    QMessageBox, QFileDialog, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import QPen, QColor, QPainter, QFont


class PointsTableView(QTableView):
    """Таблица пунктов ПВО"""
    
    point_selected = pyqtSignal(str)  # Сигнал выбора пункта
    points_changed = pyqtSignal()     # Сигнал изменения данных
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._init_ui()
        self._setup_model()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        # Настройка таблицы
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        # Настройка внешнего вида
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _setup_model(self):
        """Настройка модели данных"""
        from gui.models.points_model import PointsTableModel
        
        self.model = PointsTableModel()
        self.setModel(self.model)
        
        # Настройка столбцов
        header = self.horizontalHeader()
        header.resizeSection(0, 60)   # №
        header.resizeSection(1, 120)  # Имя
        header.resizeSection(2, 100)  # Тип
        header.resizeSection(3, 120)  # X
        header.resizeSection(4, 120)  # Y
        header.resizeSection(5, 80)   # σx
        header.resizeSection(6, 80)   # σy
    
    def _show_context_menu(self, position: QPoint):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        # Команды редактирования
        add_action = menu.addAction("Добавить пункт", self._add_point)
        add_action.setIcon(self.style().standardIcon(100))  # Plus icon
        
        delete_action = menu.addAction("Удалить пункт", self._delete_point)
        delete_action.setIcon(self.style().standardIcon(16))  # Trash icon
        
        menu.addSeparator()
        
        # Команды навигации
        select_on_plan = menu.addAction("Показать на плане", self._select_on_plan)
        
        menu.addSeparator()
        
        # Команды экспорта
        export_action = menu.addAction("Экспорт в файл", self._export_points)
        copy_action = menu.addAction("Копировать в буфер", self._copy_to_clipboard)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _add_point(self):
        """Добавление пункта"""
        self.model.add_point()
        self.points_changed.emit()
    
    def _delete_point(self):
        """Удаление пункта"""
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Предупреждение", "Выберите пункты для удаления")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить выбранные пункты ({len(indexes)})?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for index in sorted(indexes, reverse=True):
                self.model.remove_point(index.row())
            self.points_changed.emit()
    
    def _select_on_plan(self):
        """Показать выбранные пункты на плане"""
        indexes = self.selectionModel().selectedRows()
        for index in indexes:
            point_name = self.model.data(self.model.index(index.row(), 1))
            self.point_selected.emit(point_name)
    
    def _export_points(self):
        """Экспорт пунктов"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт пунктов",
            "",
            "CSV файлы (*.csv);;TXT файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            self.model.export_to_file(file_path)
    
    def _copy_to_clipboard(self):
        """Копирование в буфер обмена"""
        self.model.copy_to_clipboard(self.selectionModel().selectedRows())
    
    def load_data(self, points: List[Any]):
        """Загрузка данных пунктов"""
        self.model.load_points(points)


class ObservationsTableView(QTableView):
    """Таблица измерений"""
    
    observations_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._init_ui()
        self._setup_model()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        self.verticalHeader().setVisible(True)
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _setup_model(self):
        """Настройка модели данных"""
        from gui.models.observations_model import ObservationsTableModel
        
        self.model = ObservationsTableModel()
        self.setModel(self.model)
        
        # Настройка столбцов
        header = self.horizontalHeader()
        header.resizeSection(0, 60)   # №
        header.resizeSection(1, 80)   # Тип
        header.resizeSection(2, 100)  # От
        header.resizeSection(3, 100)  # До
        header.resizeSection(4, 120)  # Значение
        header.resizeSection(5, 80)   # Вес
        header.resizeSection(6, 100)  # Поправка
    
    def _show_context_menu(self, position: QPoint):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        menu.addAction("Добавить измерение", self._add_observation)
        menu.addAction("Удалить измерение", self._delete_observation)
        menu.addSeparator()
        menu.addAction("Показать на плане", self._select_on_plan)
        menu.addSeparator()
        menu.addAction("Экспорт в файл", self._export_observations)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _add_observation(self):
        """Добавление измерения"""
        self.model.add_observation()
        self.observations_changed.emit()
    
    def _delete_observation(self):
        """Удаление измерения"""
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Предупреждение", "Выберите измерения для удаления")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить выбранные измерения ({len(indexes)})?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for index in sorted(indexes, reverse=True):
                self.model.remove_observation(index.row())
            self.observations_changed.emit()
    
    def _select_on_plan(self):
        """Показать выбранные измерения на плане"""
        pass
    
    def _export_observations(self):
        """Экспорт измерений"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт измерений",
            "",
            "CSV файлы (*.csv);;TXT файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            self.model.export_to_file(file_path)
    
    def load_data(self, observations: List[Any]):
        """Загрузка данных измерений"""
        self.model.load_observations(observations)


class TraversesTreeView(QTreeView):
    """Дерево ходов и секций"""
    
    traverse_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._init_ui()
        self._setup_model()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _setup_model(self):
        """Настройка модели данных"""
        from gui.models.traverses_model import TraversesTreeModel
        
        self.model = TraversesTreeModel()
        self.setModel(self.model)
        
        self.expandAll()
    
    def _show_context_menu(self, position: QPoint):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        menu.addAction("Добавить ход", self._add_traverse)
        menu.addAction("Добавить секцию", self._add_section)
        menu.addSeparator()
        menu.addAction("Удалить", self._delete_item)
        menu.addSeparator()
        menu.addAction("Показать на плане", self._show_on_plan)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _add_traverse(self):
        """Добавление хода"""
        pass
    
    def _add_section(self):
        """Добавление секции"""
        pass
    
    def _delete_item(self):
        """Удаление элемента"""
        pass
    
    def _show_on_plan(self):
        """Показать на плане"""
        index = self.currentIndex()
        if index.isValid():
            traverse_id = self.model.data(index)
            self.traverse_selected.emit(traverse_id)


class PlanGraphicsView(QGraphicsView):
    """Графическое окно плана"""
    
    point_clicked = pyqtSignal(str)  # Сигнал клика по пункту
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scale_factor = 1.0
        self.dragging = False
        self.last_mouse_pos = None
        
        self._init_ui()
        self._setup_scene()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setOptimizationFlags(QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Включение прокрутки
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Фон
        self.setStyleSheet("""
            QGraphicsView {
                background-color: white;
                border: 1px solid #c0c0c0;
            }
        """)
    
    def _setup_scene(self):
        """Настройка сцены"""
        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        self.setScene(self.scene)
        
        # Установка размеров сцены
        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        
        # Сетка
        self._draw_grid()
    
    def _draw_grid(self):
        """Отрисовка сетки"""
        pen = QPen(QColor(220, 220, 220), 1)
        
        # Вертикальные линии
        for x in range(-10000, 10001, 100):
            self.scene.addLine(x, -10000, x, 10000, pen)
        
        # Горизонтальные линии
        for y in range(-10000, 10001, 100):
            self.scene.addLine(-10000, y, 10000, y, pen)
    
    def wheelEvent(self, event):
        """Обработка прокрутки колеса мыши (масштабирование)"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        self.scale(zoom_factor, zoom_factor)
        self.scale_factor *= zoom_factor
    
    def mousePressEvent(self, event):
        """Обработка нажатия кнопки мыши"""
        if event.button() == Qt.MiddleButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            # Проверка клика по пункту
            item = self.itemAt(event.pos())
            if item and hasattr(item, 'data') and item.data.get('type') == 'point':
                point_name = item.data.get('name', '')
                self.point_clicked.emit(point_name)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Обработка движения мыши"""
        if self.dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            
            # Прокрутка сцены
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            # Обновление координат в статусной строке
            scene_pos = self.mapToScene(event.pos())
            coords_str = f"X: {scene_pos.x():.3f}, Y: {scene_pos.y():.3f}"
            if hasattr(self.parent().parent(), 'coords_label'):
                self.parent().parent().coords_label.setText(coords_str)
            
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if event.button() == Qt.MiddleButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def draw_network(self, network: Any):
        """Отрисовка сети"""
        self.scene.clear()
        self._draw_grid()
        
        # Отрисовка пунктов
        for point in network.points:
            self._draw_point(point)
        
        # Отрисовка измерений
        for obs in network.observations:
            self._draw_observation(obs)
        
        # Отрисовка эллипсов ошибок
        for point in network.points:
            if point.has_adjusted_coordinates:
                self._draw_error_ellipse(point)
    
    def _draw_point(self, point: Any):
        """Отрисовка пункта"""
        # Создание графического элемента пункта
        item = self.scene.addEllipse(-4, -4, 8, 8, QPen(Qt.red, 2), QColor(Qt.red))
        item.setPos(point.x, -point.y)  # Инверсия Y для системы координат
        
        # Добавление данных
        item.data = {'type': 'point', 'name': point.name, 'point': point}
        item.setToolTip(f"{point.name}\nX: {point.x:.3f}\nY: {point.y:.3f}")
        
        # Добавление подписи
        label = self.scene.addText(point.name)
        label.setPos(point.x + 5, -point.y - 10)
        label.setDefaultTextColor(Qt.black)
    
    def _draw_observation(self, obs: Any):
        """Отрисовка измерения"""
        from_point = obs.from_point
        to_point = obs.to_point
        
        line = self.scene.addLine(
            from_point.x, -from_point.y,
            to_point.x, -to_point.y,
            QPen(QColor(0, 0, 255, 150), 1)
        )
        line.setPen(QPen(Qt.blue, 1, Qt.DashLine))
    
    def _draw_error_ellipse(self, point: Any):
        """Отрисовка эллипса ошибок"""
        import math
        
        # Расчёт параметров эллипса
        a, b, alpha = point.calculate_error_ellipse()
        
        # Создание эллипса
        ellipse = self.scene.addEllipse(-a, -b, 2*a, 2*b)
        ellipse.setPos(point.x, -point.y)
        
        # Поворот эллипса
        ellipse.setRotation(alpha * 180 / math.pi)
        
        # Настройка стиля
        ellipse.setPen(QPen(Qt.blue, 1, Qt.DashDotLine))
        ellipse.setBrush(QColor(0, 0, 255, 50))  # Полупрозрачная заливка
    
    def fit_view(self):
        """Подогнать масштаб по содержимому"""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    def clear(self):
        """Очистка сцены"""
        self.scene.clear()
        self._draw_grid()


class LogWidget(QTextEdit):
    """Виджет журнала событий"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        
        # Настройка форматирования
        font = QFont("Courier New", 9)
        self.setFont(font)
        
        self.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #c0c0c0;
            }
        """)
        
        # Создание обработчика логов
        self.log_handler = LogWidgetHandler(self)
    
    def append_message(self, message: str, level: str = "INFO"):
        """Добавление сообщения в журнал"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "DEBUG": "gray",
            "INFO": "black",
            "WARNING": "orange",
            "ERROR": "red",
            "CRITICAL": "darkred"
        }
        
        color = color_map.get(level, "black")
        html_message = f'<span style="color:{color}">[{timestamp}] [{level}] {message}</span><br>'
        
        self.insertHtml(html_message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def clear_log(self):
        """Очистка журнала"""
        self.clear()


class LogWidgetHandler:
    """Обработчик логов для виджета журнала"""
    
    def __init__(self, widget: LogWidget):
        self.widget = widget
        self.level = 0  # DEBUG
    
    def emit(self, record):
        """Вывод записи лога"""
        msg = self.format(record) if hasattr(self, 'format') else record.getMessage()
        self.widget.append_message(msg, record.levelname)


class PropertiesWidget(QWidget):
    """Панель свойств объектов"""
    
    property_changed = pyqtSignal(str, Any)  # имя свойства, значение
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_object = None
        self.property_fields = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        self.header_label = QLabel("Свойства")
        self.header_label.setStyleSheet("""
            font-weight: bold;
            font-size: 11px;
            padding: 5px;
            background-color: #e0e0e0;
            border-radius: 3px;
        """)
        layout.addWidget(self.header_label)
        
        # Контейнер свойств
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(0, 5, 0, 0)
        self.properties_layout.setSpacing(5)
        layout.addWidget(self.properties_container)
        
        layout.addStretch()
    
    def set_object(self, obj: Any, obj_type: str = "object"):
        """Установка объекта для редактирования"""
        self.current_object = obj
        self.header_label.setText(f"Свойства: {obj_type}")
        
        # Очистка старых полей
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Создание новых полей
        self._create_property_fields(obj)
    
    def _create_property_fields(self, obj: Any):
        """Создание полей свойств"""
        from PyQt5.QtWidgets import QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox
        
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Получение свойств объекта
        if hasattr(obj, '__dict__'):
            for name, value in obj.__dict__.items():
                if not name.startswith('_'):
                    self._add_property_field(form_layout, name, value)
        
        self.properties_layout.addLayout(form_layout)
    
    def _add_property_field(self, layout, name: str, value: Any):
        """Добавление поля свойства"""
        from PyQt5.QtWidgets import QLineEdit, QDoubleSpinBox, QComboBox, QLabel
        
        label = QLabel(f"{name}:")
        
        if isinstance(value, bool):
            widget = QComboBox()
            widget.addItem("Да", True)
            widget.addItem("Нет", False)
            widget.setCurrentIndex(0 if value else 1)
            widget.currentIndexChanged.connect(
                lambda idx: self._on_property_changed(name, widget.itemData(idx))
            )
        elif isinstance(value, (int, float)):
            widget = QDoubleSpinBox()
            widget.setRange(-1e10, 1e10)
            widget.setValue(float(value))
            widget.valueChanged.connect(
                lambda v: self._on_property_changed(name, v)
            )
        elif isinstance(value, str):
            widget = QLineEdit(str(value))
            widget.textChanged.connect(
                lambda t: self._on_property_changed(name, t)
            )
        else:
            widget = QLabel(str(value))
        
        layout.addRow(label, widget)
        self.property_fields[name] = widget
    
    def _on_property_changed(self, name: str, value: Any):
        """Обработчик изменения свойства"""
        if self.current_object and hasattr(self.current_object, name):
            setattr(self.current_object, name, value)
            self.property_changed.emit(name, value)
