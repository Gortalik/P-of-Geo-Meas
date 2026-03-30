"""
Табличные компоненты для GeoAdjust Pro

Включает:
- PointsTableView: таблица пунктов ПВО
- ObservationsTableView: таблица измерений
"""

from PyQt5.QtWidgets import QTableView, QHeaderView, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class PointsTableView(QTableView):
    """Таблица пунктов ПВО"""
    
    point_double_clicked = pyqtSignal(str)  # signal с ID пункта
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Настройка заголовков
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setVisible(False)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Двойной клик
        self.doubleClicked.connect(self._on_double_click)
        
        # Модель данных
        self._setup_model()
    
    def _setup_model(self):
        """Настройка модели данных"""
        from PyQt5.QtGui import QStandardItemModel, QStandardItem
        self.model = QStandardItemModel(0, 8, self)
        self.model.setHorizontalHeaderLabels([
            "ID", "Наименование", "Тип", "X (м)", "Y (м)", 
            "H (м)", "Прибор", "Примечание"
        ])
        self.setModel(self.model)
    
    def update_data(self, points: list):
        """Обновление данных таблицы"""
        from PyQt5.QtGui import QStandardItem
        self.model.setRowCount(0)
        
        for point in points:
            row_data = [
                point.get('id', ''),
                point.get('name', ''),
                point.get('type', 'FREE'),
                str(point.get('x', '')),
                str(point.get('y', '')),
                str(point.get('h', '')),
                point.get('instrument', ''),
                point.get('notes', '')
            ]
            items = [QStandardItem(str(val)) for val in row_data]
            self.model.appendRow(items)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        menu.addSeparator()
        properties_action = menu.addAction("Свойства")
        
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == edit_action:
            self._edit_point()
        elif action == delete_action:
            self._delete_point()
        elif action == properties_action:
            self._show_properties()
    
    def _on_double_click(self, index):
        """Обработка двойного клика"""
        row = index.row()
        if self.model and row >= 0:
            point_id = self.model.index(row, 0).data()
            if point_id:
                self.point_double_clicked.emit(point_id)
    
    def _edit_point(self):
        """Редактирование пункта"""
        pass
    
    def _delete_point(self):
        """Удаление пункта"""
        pass
    
    def _show_properties(self):
        """Показ свойств пункта"""
        pass


class ObservationsTableView(QTableView):
    """Таблица измерений"""
    
    observation_double_clicked = pyqtSignal(str)  # signal с ID измерения
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        
        # Настройка заголовков
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setVisible(False)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Двойной клик
        self.doubleClicked.connect(self._on_double_click)
        
        # Модель данных
        self._setup_model()
    
    def _setup_model(self):
        """Настройка модели данных"""
        from PyQt5.QtGui import QStandardItemModel, QStandardItem
        self.model = QStandardItemModel(0, 10, self)
        self.model.setHorizontalHeaderLabels([
            "ID", "Откуда", "Куда", "Тип", "Значение", 
            "σ (априорная)", "Прибор", "Дата", "Время", "Примечание"
        ])
        self.setModel(self.model)
    
    def update_data(self, observations: list):
        """Обновление данных таблицы"""
        from PyQt5.QtGui import QStandardItem
        self.model.setRowCount(0)
        
        for obs in observations:
            row_data = [
                str(obs.get('id', '')),
                obs.get('from_point', ''),
                obs.get('to_point', ''),
                obs.get('obs_type', ''),
                str(obs.get('value', '')),
                str(obs.get('sigma_apriori', '')),
                obs.get('instrument_name', ''),
                obs.get('date', ''),
                obs.get('time', ''),
                obs.get('notes', '')
            ]
            items = [QStandardItem(str(val)) for val in row_data]
            self.model.appendRow(items)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        edit_action = menu.addAction("Редактировать")
        delete_action = menu.addAction("Удалить")
        menu.addSeparator()
        exclude_action = menu.addAction("Исключить")
        
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == edit_action:
            self._edit_observation()
        elif action == delete_action:
            self._delete_observation()
        elif action == exclude_action:
            self._exclude_observation()
    
    def _on_double_click(self, index):
        """Обработка двойного клика"""
        row = index.row()
        if self.model and row >= 0:
            obs_id = self.model.index(row, 0).data()
            if obs_id:
                self.observation_double_clicked.emit(obs_id)
    
    def _edit_observation(self):
        """Редактирование измерения"""
        pass
    
    def _delete_observation(self):
        """Удаление измерения"""
        pass
    
    def _exclude_observation(self):
        """Исключение измерения из уравнивания"""
        pass
