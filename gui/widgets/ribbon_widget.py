"""
GeoAdjust Pro - Виджет ленточного интерфейса (Ribbon)
В стиле Microsoft Office
"""

from typing import List, Tuple, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QToolButton,
    QMenu, QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy,
    QAction, QApplication, QStylePainter, QStyleOptionTab
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPalette


class RibbonTab(QFrame):
    """Вкладка ленты"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.groups: List[RibbonGroup] = []
        self.is_active = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setFrameShape(QFrame.NoFrame)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Панель групп
        self.groups_layout = QHBoxLayout()
        self.groups_layout.setSpacing(4)
        layout.addLayout(self.groups_layout)
    
    def add_group(self, name: str, actions: List[Tuple[str, str, Optional[str]]]) -> 'RibbonGroup':
        """Добавление группы кнопок"""
        group = RibbonGroup(name, self)
        
        for action_data in actions:
            if len(action_data) == 3:
                text, icon_name, shortcut = action_data
            else:
                text, icon_name = action_data
                shortcut = None
            
            group.add_action(text, icon_name, shortcut)
        
        self.groups.append(group)
        self.groups_layout.addWidget(group)
        
        return group
    
    def set_active(self, active: bool):
        """Установка активности вкладки"""
        self.is_active = active
        self.setVisible(active)
        
        if active:
            self.setStyleSheet("""
                RibbonTab {
                    background-color: #f0f0f0;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                }
            """)
        else:
            self.setStyleSheet("")


class RibbonGroup(QFrame):
    """Группа кнопок на ленте"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.actions: List[QAction] = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Кнопки действий
        self.buttons_layout = QVBoxLayout()
        self.buttons_layout.setSpacing(2)
        layout.addLayout(self.buttons_layout)
        
        # Название группы
        self.label = QLabel(self.title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.label)
    
    def add_action(self, text: str, icon_name: str, shortcut: Optional[str] = None):
        """Добавление действия"""
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setIconSize(QSize(32, 32))
        button.setAutoRaise(True)
        button.setPopupMode(QToolButton.InstantPopup)
        
        if shortcut:
            button.setToolTip(f"{text} ({shortcut})")
        else:
            button.setToolTip(text)
        
        # Создание действия
        action = QAction(text, button)
        if shortcut:
            action.setShortcut(shortcut)
        button.setDefaultAction(action)
        
        self.actions.append(action)
        self.buttons_layout.addWidget(button)


class RibbonQuickAccessToolbar(QToolBar):
    """Панель быстрого доступа"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setStyleSheet("""
            QToolBar {
                background-color: transparent;
                border: none;
                spacing: 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #e5f3ff;
                border: 1px solid #cce8ff;
            }
        """)
    
    def add_action(self, text: str, action_name: str):
        """Добавление действия"""
        # Здесь должна быть логика получения иконки по имени действия
        action = QAction(text, self)
        action.setObjectName(action_name)
        self.addAction(action)


class RibbonWidget(QWidget):
    """Ленточный интерфейс (Ribbon)"""
    
    tab_changed = pyqtSignal(str)  # Сигнал смены вкладки
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs: Dict[str, RibbonTab] = {}
        self.current_tab: Optional[str] = None
        self.quick_access_toolbar: Optional[RibbonQuickAccessToolbar] = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setMinimumHeight(150)
        self.setMaximumHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Верхняя часть: панель быстрого доступа и заголовки вкладок
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 5, 5, 0)
        top_layout.setSpacing(5)
        
        # Панель быстрого доступа
        self.quick_access_container = QWidget()
        self.quick_access_layout = QHBoxLayout(self.quick_access_container)
        self.quick_access_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_access_layout.setSpacing(2)
        top_layout.addWidget(self.quick_access_container)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFixedWidth(2)
        separator.setStyleSheet("background-color: #c0c0c0;")
        top_layout.addWidget(separator)
        
        # Вкладки
        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(2)
        self.tabs_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        top_layout.addLayout(self.tabs_layout)
        
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # Контейнер для содержимого вкладок
        self.content_area = QScrollArea()
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_area.setWidgetResizable(True)
        layout.addWidget(self.content_area)
        
        # Контейнер для вкладок
        self.tabs_container = QWidget()
        self.tabs_layout_widget = QHBoxLayout(self.tabs_container)
        self.tabs_layout_widget.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout_widget.setSpacing(0)
        self.content_area.setWidget(self.tabs_container)
    
    def add_tab(self, title: str) -> RibbonTab:
        """Добавление вкладки"""
        tab = RibbonTab(title, self)
        self.tabs[title] = tab
        
        # Создание кнопки вкладки
        tab_button = QPushButton(title)
        tab_button.setCheckable(True)
        tab_button.setChecked(False)
        tab_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-bottom: none;
                border-radius: 3px 3px 0 0;
                padding: 5px 15px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #e5f3ff;
                border: 1px solid #cce8ff;
                border-bottom: none;
            }
            QPushButton:checked {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-bottom: 1px solid #f0f0f0;
                font-weight: bold;
            }
        """)
        
        tab_button.clicked.connect(lambda: self._on_tab_clicked(title))
        
        self.tabs_layout_widget.addWidget(tab_button)
        
        # Добавление вкладки в контейнер
        self.tabs_layout_widget.addWidget(tab)
        tab.setVisible(False)
        
        # Установка первой вкладки активной
        if len(self.tabs) == 1:
            self._on_tab_clicked(title)
            tab_button.setChecked(True)
        
        return tab
    
    def add_quick_access_toolbar(self) -> RibbonQuickAccessToolbar:
        """Добавление панели быстрого доступа"""
        self.quick_access_toolbar = RibbonQuickAccessToolbar()
        
        # Очистка контейнера
        while self.quick_access_layout.count():
            item = self.quick_access_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.quick_access_layout.addWidget(self.quick_access_toolbar)
        
        return self.quick_access_toolbar
    
    def _on_tab_clicked(self, title: str):
        """Обработчик клика по вкладке"""
        if self.current_tab and self.current_tab != title:
            self.tabs[self.current_tab].set_active(False)
        
        self.current_tab = title
        self.tabs[title].set_active(True)
        
        self.tab_changed.emit(title)
    
    def get_current_tab(self) -> Optional[str]:
        """Получение текущей вкладки"""
        return self.current_tab
    
    def set_current_tab(self, title: str):
        """Установка текущей вкладки"""
        if title in self.tabs:
            # Находим кнопку вкладки и кликаем по ней
            for i in range(self.tabs_layout_widget.count()):
                widget = self.tabs_layout_widget.itemAt(i).widget()
                if isinstance(widget, QPushButton) and widget.text() == title:
                    widget.click()
                    break
