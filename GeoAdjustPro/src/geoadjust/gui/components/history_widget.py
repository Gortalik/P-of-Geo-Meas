"""
Виджет истории изменений для GeoAdjust Pro

Отслеживает все изменения в проекте и позволяет:
- Просматривать историю изменений
- Отменять/повторять действия
- Перемещаться по истории проекта
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HistoryEntry:
    """Запись в истории изменений"""
    
    def __init__(self, action_type: str, description: str, data: Dict[str, Any] = None):
        self.timestamp = datetime.now()
        self.action_type = action_type  # 'add_point', 'edit_point', 'delete_point', etc.
        self.description = description
        self.data = data or {}
        self.undo_data = {}  # Данные для отмены действия
    
    def __repr__(self):
        return f"HistoryEntry({self.action_type}, {self.description}, {self.timestamp})"


class HistoryManager:
    """Менеджер истории изменений"""
    
    def __init__(self, max_history: int = 100, project_dir: Optional[Path] = None):
        self.max_history = max_history
        self.project_dir = project_dir
        self.history: List[HistoryEntry] = []
        self.current_index: int = -1  # -1 означает "нет действий"
        self._load_from_file()  # Загрузка истории при инициализации
    
    def add_entry(self, entry: HistoryEntry):
        """Добавление записи в историю"""
        # Если мы не в конце истории, удаляем все записи после текущей позиции
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(entry)
        self.current_index = len(self.history) - 1
        
        # Ограничиваем размер истории
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
            self.current_index = len(self.history) - 1
        
        self._save_to_file()  # Сохранение в файл
        logger.info(f"История: {entry.description}")
    
    def _save_to_file(self):
        """Сохранение истории в JSON файл"""
        if not self.project_dir:
            return
        
        history_file = self.project_dir / 'history' / 'history.json'
        history_file.parent.mkdir(exist_ok=True)
        
        try:
            import json
            entries_data = []
            for entry in self.history:
                entries_data.append({
                    'timestamp': entry.timestamp.isoformat(),
                    'action_type': entry.action_type,
                    'description': entry.description,
                    'data': entry.data,
                    'undo_data': entry.undo_data
                })
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(entries_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {e}")
    
    def _load_from_file(self):
        """Загрузка истории из JSON файла"""
        if not self.project_dir:
            return
        
        history_file = self.project_dir / 'history' / 'history.json'
        if not history_file.exists():
            return
        
        try:
            import json
            with open(history_file, 'r', encoding='utf-8') as f:
                entries_data = json.load(f)
            
            self.history = []
            for data in entries_data:
                entry = HistoryEntry(
                    action_type=data['action_type'],
                    description=data['description'],
                    data=data.get('data', {}),
                )
                entry.timestamp = datetime.fromisoformat(data['timestamp'])
                entry.undo_data = data.get('undo_data', {})
                self.history.append(entry)
            
            if self.history:
                self.current_index = len(self.history) - 1
        except Exception as e:
            logger.error(f"Ошибка загрузки истории: {e}")
            self.history = []
            self.current_index = -1
    
    def can_undo(self) -> bool:
        """Можно ли отменить действие"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """Можно ли повторить действие"""
        return self.current_index < len(self.history) - 1
    
    def undo(self) -> Optional[HistoryEntry]:
        """Отмена последнего действия"""
        if not self.can_undo():
            return None
        
        entry = self.history[self.current_index]
        self.current_index -= 1
        return entry
    
    def redo(self) -> Optional[HistoryEntry]:
        """Повтор отменённого действия"""
        if not self.can_redo():
            return None
        
        self.current_index += 1
        return self.history[self.current_index]
    
    def get_entries(self) -> List[HistoryEntry]:
        """Получение всех записей истории"""
        return self.history
    
    def get_entry_at(self, index: int) -> Optional[HistoryEntry]:
        """Получение записи по индексу"""
        if 0 <= index < len(self.history):
            return self.history[index]
        return None
    
    def clear(self):
        """Очистка истории"""
        self.history.clear()
        self.current_index = -1


class HistoryWidget(QWidget):
    """Виджет отображения истории изменений"""
    
    # Сигналы
    undo_requested = pyqtSignal(object)  # HistoryEntry для отмены
    redo_requested = pyqtSignal(object)  # HistoryEntry для повтора
    jump_to_entry = pyqtSignal(int)  # Индекс записи для перехода
    
    def __init__(self, parent=None, project_dir: Optional[Path] = None):
        super().__init__(parent)
        self.history_manager = HistoryManager(project_dir=project_dir)
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Заголовок
        self.title_label = QLabel("История изменений")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px;")
        layout.addWidget(self.title_label)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)
        
        self.undo_btn = QPushButton("↩ Отменить")
        self.undo_btn.clicked.connect(self._on_undo)
        self.undo_btn.setMaximumHeight(24)
        self.undo_btn.setEnabled(False)
        btn_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("↪ Повторить")
        self.redo_btn.clicked.connect(self._on_redo)
        self.redo_btn.setMaximumHeight(24)
        self.redo_btn.setEnabled(False)
        btn_layout.addWidget(self.redo_btn)
        
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.clicked.connect(self._on_clear)
        self.clear_btn.setMaximumHeight(24)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Дерево истории
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderHidden(False)
        self.history_tree.setHeaderLabels(["Время", "Действие", "Описание"])
        self.history_tree.setRootIsDecorated(False)
        self.history_tree.setAlternatingRowColors(True)
        self.history_tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.history_tree)
        
        # Установка минимального размера
        self.setMinimumSize(180, 200)
    
    def add_entry(self, entry: HistoryEntry):
        """Добавление записи в историю"""
        self.history_manager.add_entry(entry)
        self._refresh_tree()
        self._update_buttons()
    
    def _refresh_tree(self):
        """Обновление дерева истории"""
        self.history_tree.clear()
        
        for i, entry in enumerate(self.history_manager.get_entries()):
            time_str = entry.timestamp.strftime("%H:%M:%S")
            
            item = QTreeWidgetItem([time_str, entry.action_type, entry.description])
            item.setData(0, Qt.UserRole, i)  # Сохраняем индекс
            
            # Подсвечиваем текущую позицию
            if i <= self.history_manager.current_index:
                item.setForeground(0, Qt.darkGray)
                item.setForeground(1, Qt.darkGray)
                item.setForeground(2, Qt.darkGray)
            else:
                item.setForeground(0, Qt.lightGray)
                item.setForeground(1, Qt.lightGray)
                item.setForeground(2, Qt.lightGray)
            
            self.history_tree.addTopLevelItem(item)
        
        # Прокручиваем к последней записи
        if self.history_tree.topLevelItemCount() > 0:
            self.history_tree.scrollToItem(
                self.history_tree.topLevelItem(self.history_tree.topLevelItemCount() - 1)
            )
    
    def _update_buttons(self):
        """Обновление состояния кнопок"""
        self.undo_btn.setEnabled(self.history_manager.can_undo())
        self.redo_btn.setEnabled(self.history_manager.can_redo())
    
    def _on_undo(self):
        """Обработка нажатия кнопки отмены"""
        entry = self.history_manager.undo()
        if entry:
            self.undo_requested.emit(entry)
            self._refresh_tree()
            self._update_buttons()
    
    def _on_redo(self):
        """Обработка нажатия кнопки повтора"""
        entry = self.history_manager.redo()
        if entry:
            self.redo_requested.emit(entry)
            self._refresh_tree()
            self._update_buttons()
    
    def _on_clear(self):
        """Обработка нажатия кнопки очистки"""
        self.history_manager.clear()
        self._refresh_tree()
        self._update_buttons()
    
    def _on_item_clicked(self, item, column):
        """Обработка клика по записи в истории"""
        index = item.data(0, Qt.UserRole)
        if index is not None:
            self.jump_to_entry.emit(index)
    
    def get_history_manager(self) -> HistoryManager:
        """Получение менеджера истории"""
        return self.history_manager


class PropertiesHistoryTabWidget(QTabWidget):
    """Виджет с вкладками Свойства и История"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabPosition(QTabWidget.South)
        self.setMovable(False)
        
        # Создаём виджеты
        from .properties_widget import PropertiesWidget
        self.properties_widget = PropertiesWidget(self)
        self.history_widget = HistoryWidget(self)
        
        # Добавляем вкладки
        self.addTab(self.properties_widget, "Свойства")
        self.addTab(self.history_widget, "История")
        
        # Установка минимального размера
        self.setMinimumSize(180, 200)
