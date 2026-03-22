"""
Ленточный интерфейс (Ribbon) для GeoAdjust Pro

Современный ленточный интерфейс в стиле Microsoft Office
"""

from typing import List, Tuple, Optional, Callable
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QAction, QMenu,
    QTabWidget, QFrame, QLabel, QPushButton, QToolButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

# Импорт центральной функции для работы с ресурсами
from src.geoadjust.utils import get_resource_path



class RibbonGroup(QFrame):
    """Группа кнопок в ленте"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setFrameStyle(QFrame.StyledPanel)
        
        # Основной макет
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Панель кнопок
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(2)
        layout.addLayout(self.buttons_layout)
        
        # Подпись группы
        self.label = QLabel(title)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(self.label)
        
        self.actions = []
    
    def add_action(self, text: str, icon_name: Optional[str] = None, 
                   shortcut: Optional[str] = None, callback: Optional[Callable] = None):
        """Добавление действия в группу"""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(text + (f" ({shortcut})" if shortcut else ""))
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        if icon_name:
            try:
                icon_path = get_resource_path(f"gui/resources/icons/{icon_name}.png")
                if hasattr(icon_path, 'exists') and icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
                else:
                    # Использовать стандартную иконку если файл не найден
                    button.setIcon(QIcon.fromTheme("applications-science"))
            except Exception:
                # Продолжить без иконки при ошибке
                pass
        
        if shortcut:
            button.setShortcut(shortcut)
        
        if callback:
            button.clicked.connect(callback)
        
        self.buttons_layout.addWidget(button)
        self.actions.append(button)
        
        return button


class RibbonTab(QWidget):
    """Вкладка ленты"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.groups = []
    
    def add_group(self, title: str, actions: List[Tuple] = None) -> RibbonGroup:
        """Добавление группы на вкладку"""
        group = RibbonGroup(title, self)
        
        if actions:
            for action_data in actions:
                if len(action_data) >= 4:
                    text, icon_name, shortcut, callback = action_data[:4]
                    group.add_action(text, icon_name, shortcut, callback)
                elif len(action_data) == 3:
                    text, icon_name, shortcut = action_data
                    group.add_action(text, icon_name, shortcut)
                else:
                    text = action_data[0]
                    group.add_action(text)
        
        self.groups.append(group)
        self.layout().addWidget(group)
        
        return group


class RibbonWidget(QTabWidget):
    """Ленточный виджет"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Настройка стиля
        self.setDocumentMode(True)
        self.setMovable(False)
        self.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 20px;
                font-size: 12px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-radius: 3px 3px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
            }
            QTabBar::tab:!selected {
                background-color: #e0e0e0;
            }
        """)
        
        self.tabs = {}
        self.quick_access_toolbar = None
    
    def add_tab(self, title: str) -> RibbonTab:
        """Добавление вкладки"""
        tab = RibbonTab(title, self)
        self.addTab(tab, title)
        self.tabs[title] = tab
        return tab
    
    def add_quick_access_toolbar(self):
        """Добавление панели быстрого доступа"""
        if self.quick_access_toolbar is None:
            self.quick_access_toolbar = QuickAccessToolbar(self.parent())
            
            # Размещение над лентой
            if self.parent():
                main_layout = self.parent().layout()
                if main_layout:
                    main_layout.insertWidget(0, self.quick_access_toolbar)
        
        return self.quick_access_toolbar


class QuickAccessToolbar(QToolBar):
    """Панель быстрого доступа"""
    
    def __init__(self, parent=None):
        super().__init__("Quick Access", parent)
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))
    
    def add_action(self, text: str, callback: Optional[Callable] = None, 
                   icon_name: Optional[str] = None):
        """Добавление действия"""
        action = QAction(text, self)
        if icon_name:
            try:
                icon_path = get_resource_path(f"gui/resources/icons/{icon_name}.png")
                if hasattr(icon_path, 'exists') and icon_path.exists():
                    action.setIcon(QIcon(str(icon_path)))
                else:
                    action.setIcon(QIcon.fromTheme("applications-science"))
            except Exception:
                pass
        
        if callback:
            action.triggered.connect(callback)
        
        self.addAction(action)
        return action
