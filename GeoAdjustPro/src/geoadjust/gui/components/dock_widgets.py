"""
Компоненты док-виджетов для GeoAdjust Pro

Включает:
- PointsDockWidget: док-панель пунктов ПВО
- ObservationsDockWidget: док-панель измерений
- TraversesDockWidget: док-панель ходов и секций
"""

from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QTreeView, QHeaderView, QPushButton,
    QMenu, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class PointsDockWidget(QDockWidget):
    """Док-панель пунктов ПВО"""
    
    point_selected = pyqtSignal(str)  # signal с ID пункта
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        
        self.widget = QWidget()
        self.setWidget(self.widget)
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Таблица пунктов
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        
        layout.addWidget(self.table_view)
        
        # Панель инструментов - компактная
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(2)
        
        add_btn = QPushButton("+")
        add_btn.setToolTip("Добавить пункт")
        add_btn.setMaximumWidth(28)
        add_btn.setMaximumHeight(24)
        toolbar.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setToolTip("Удалить пункт")
        remove_btn.setMaximumWidth(28)
        remove_btn.setMaximumHeight(24)
        toolbar.addWidget(remove_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Установка минимального размера виджета
        self.widget.setMinimumWidth(180)


class ObservationsDockWidget(QDockWidget):
    """Док-панель измерений"""
    
    observation_selected = pyqtSignal(str)  # signal с ID измерения
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        
        self.widget = QWidget()
        self.setWidget(self.widget)
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Таблица измерений
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        
        layout.addWidget(self.table_view)
        
        # Панель инструментов - компактная
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(2)
        
        add_btn = QPushButton("+")
        add_btn.setToolTip("Добавить измерение")
        add_btn.setMaximumWidth(28)
        add_btn.setMaximumHeight(24)
        toolbar.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setToolTip("Удалить измерение")
        remove_btn.setMaximumWidth(28)
        remove_btn.setMaximumHeight(24)
        toolbar.addWidget(remove_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Установка минимального размера виджета
        self.widget.setMinimumWidth(180)


class TraversesDockWidget(QDockWidget):
    """Док-панель ходов и секций"""
    
    traverse_selected = pyqtSignal(str)  # signal с ID хода/секции
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        
        self.widget = QWidget()
        self.setWidget(self.widget)
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Дерево ходов и секций
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(False)
        self.tree_view.header().setStretchLastSection(True)
        
        layout.addWidget(self.tree_view)
        
        # Панель инструментов - компактная
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(2)
        
        add_btn = QPushButton("+")
        add_btn.setToolTip("Добавить ход/секцию")
        add_btn.setMaximumWidth(28)
        add_btn.setMaximumHeight(24)
        toolbar.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setToolTip("Удалить ход/секцию")
        remove_btn.setMaximumWidth(28)
        remove_btn.setMaximumHeight(24)
        toolbar.addWidget(remove_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Установка минимального размера виджета
        self.widget.setMinimumWidth(180)
