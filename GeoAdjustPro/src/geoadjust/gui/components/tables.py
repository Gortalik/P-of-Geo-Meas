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
        if self.model() and row >= 0:
            point_id = self.model().index(row, 0).data()
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
        if self.model() and row >= 0:
            obs_id = self.model().index(row, 0).data()
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
