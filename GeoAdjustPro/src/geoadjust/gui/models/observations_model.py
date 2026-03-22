#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модель данных для таблицы измерений
Реализует QAbstractTableModel для интеграции с QTableView
"""

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from typing import List, Dict, Any, Optional
from src.geoadjust.core.network.models import Observation

class ObservationsTableModel(QAbstractTableModel):
    """Модель данных для таблицы измерений"""
    
    # Заголовки столбцов
    HEADERS = [
        "№",              # 0
        "Тип",            # 1
        "От",             # 2
        "До",             # 3
        "Значение",       # 4
        "Вес",            # 5
        "Поправка",       # 6
        "σ апост",        # 7
        "Активен"         # 8
    ]
    
    # Форматы отображения для разных типов измерений
    VALUE_FORMATS = {
        'direction': "{:.4f}°",      # Направления в градусах
        'angle': "{:.4f}°",          # Углы в градусах
        'distance': "{:.3f} м",      # Расстояния в метрах
        'height_diff': "{:.3f} м",   # Превышения в метрах
        'azimuth': "{:.4f}°",        # Азимуты в градусах
        'vertical_angle': "{:.4f}°", # Вертикальные углы в градусах
        'zenith_angle': "{:.4f}°",   # Зенитные расстояния в градусах
        'gnss_vector': "{:.3f} м"    # Векторы ГНСС в метрах
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.observations: List[Observation] = []
        self.observation_ids: List[str] = []
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Количество строк"""
        return len(self.observations)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Количество столбцов"""
        return len(self.HEADERS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Данные для ячейки"""
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        obs = self.observations[row]
        
        if role == Qt.DisplayRole:
            if col == 0:
                return row + 1
            elif col == 1:
                return obs.obs_type
            elif col == 2:
                return obs.from_point
            elif col == 3:
                return obs.to_point
            elif col == 4:
                # Форматирование значения в зависимости от типа
                fmt = self.VALUE_FORMATS.get(obs.obs_type, "{:.3f}")
                return fmt.format(obs.value)
            elif col == 5:
                return f"{obs.weight_multiplier:.4f}" if hasattr(obs, 'weight_multiplier') else ""
            elif col == 6:
                return f"{obs.residual:.4f}" if hasattr(obs, 'residual') else ""
            elif col == 7:
                return f"{obs.sigma_aposteriori * 1000:.3f}" if hasattr(obs, 'sigma_aposteriori') else ""
            elif col == 8:
                return "Да" if obs.is_active else "Нет"
        
        elif role == Qt.CheckStateRole and col == 8:
            return Qt.Checked if obs.is_active else Qt.Unchecked
        
        elif role == Qt.TextAlignmentRole:
            if col in [0, 4, 5, 6, 7]:
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        elif role == Qt.BackgroundRole:
            # Цвет фона для отключенных измерений
            if not obs.is_active:
                return Qt.lightGray
        
        return QVariant()
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """Установка данных в ячейку"""
        if not index.isValid():
            return False
        
        row = index.row()
        col = index.column()
        obs = self.observations[row]
        
        if role == Qt.CheckStateRole and col == 8:
            obs.is_active = (value == Qt.Checked)
            self.dataChanged.emit(index, index)
            return True
        
        return False
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Флаги ячейки"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        if index.column() == 8:  # Столбец "Активен"
            flags |= Qt.ItemIsUserCheckable
        
        return flags
    
    def headerData(self, section: int, orientation: Qt.Orientation, 
                   role: int = Qt.DisplayRole) -> Any:
        """Заголовки таблицы"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()
    
    def add_observation(self, obs: Observation):
        """Добавление измерения в модель"""
        self.beginInsertRows(QModelIndex(), len(self.observations), len(self.observations))
        self.observations.append(obs)
        self.observation_ids.append(obs.obs_id)
        self.endInsertRows()
    
    def remove_observation(self, row: int):
        """Удаление измерения из модели"""
        if 0 <= row < len(self.observations):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.observations[row]
            del self.observation_ids[row]
            self.endRemoveRows()
    
    def update_observation(self, row: int, obs: Observation):
        """Обновление измерения в модели"""
        if 0 <= row < len(self.observations):
            self.observations[row] = obs
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.columnCount() - 1)
            )
    
    def get_observation(self, row: int) -> Optional[Observation]:
        """Получение измерения по индексу строки"""
        if 0 <= row < len(self.observations):
            return self.observations[row]
        return None
    
    def find_observation_row(self, obs_id: str) -> int:
        """Поиск строки по идентификатору измерения"""
        try:
            return self.observation_ids.index(obs_id)
        except ValueError:
            return -1
    
    def clear(self):
        """Очистка модели"""
        self.beginResetModel()
        self.observations.clear()
        self.observation_ids.clear()
        self.endResetModel()
