#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Таблица измерений с разделением по типам:
- Нивелирование (ходы с превышениями и боковые измерения)
- Тахеометрия (станции с горизонтальными/вертикальными углами и расстояниями)
- GNSS векторы (с СКП по средне-взвешенному)

Угловые величины отображаются в градусах, минутах и секундах.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                             QAbstractItemView, QMenu, QAction, QHeaderView,
                             QPushButton, QTabWidget)
from PyQt5.QtCore import Qt, QAbstractTableModel, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from typing import List, Dict, Any, Optional

from geoadjust.utils import decimal_to_dms, format_dms_compact


class ObservationsTableModel(QAbstractTableModel):
    """Модель таблицы измерений с разделением по типам"""
    
    # Типы измерений для каждой вкладки
    LEVELING_TYPES = ['height_diff', 'backsight', 'foresight', 'intermediate']
    TOTAL_STATION_TYPES = ['direction', 'zenith_angle', 'vertical_angle', 'distance', 
                          'slope_distance', 'horizontal_distance']
    GNSS_TYPES = ['gnss_vector']
    
    HEADERS = {
        'leveling': ['№', 'Тип', 'От пункта', 'К пункту', 'Превышение (м)', 
                     'Расстояние (м)', 'Статус'],
        'total_station': ['№', 'Станция', 'Цель', 'Гор. угол', 'Зен. угол', 
                         'Накл. расст.', 'Гор. расст.', 'Статус'],
        'gnss': ['№', 'От станции', 'К станции', 'dX (м)', 'dY (м)', 'dZ (м)',
                 'σdX (мм)', 'σdY (мм)', 'σdZ (мм)', 'Качество', 'Спутников']
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._observations: List[Any] = []
        self._filtered_observations: List[Any] = []
        self._current_tab = 'total_station'  # По умолчанию тахеометрия
    
    def set_observations(self, observations: List[Any]):
        """Установка списка измерений"""
        self.beginResetModel()
        self._observations = observations
        self._filter_observations()
        self.endResetModel()
    
    def set_tab(self, tab: str):
        """Переключение вкладки
        
        Args:
            tab: 'leveling', 'total_station', или 'gnss'
        """
        self._current_tab = tab
        self.beginResetModel()
        self._filter_observations()
        self.endResetModel()
    
    def _filter_observations(self):
        """Фильтрация измерений по текущей вкладке"""
        if self._current_tab == 'leveling':
            self._filtered_observations = [
                obs for obs in self._observations 
                if self._get_obs_type(obs) in self.LEVELING_TYPES
            ]
        elif self._current_tab == 'total_station':
            self._filtered_observations = [
                obs for obs in self._observations 
                if self._get_obs_type(obs) in self.TOTAL_STATION_TYPES
            ]
        elif self._current_tab == 'gnss':
            self._filtered_observations = [
                obs for obs in self._observations 
                if self._get_obs_type(obs) in self.GNSS_TYPES
            ]
        else:
            self._filtered_observations = self._observations
    
    def _get_obs_type(self, obs) -> str:
        """Получение типа измерения из объекта или словаря"""
        if isinstance(obs, dict):
            return obs.get('type', obs.get('obs_type', ''))
        return getattr(obs, 'obs_type', '')
    
    def _get_from_point(self, obs) -> str:
        """Получение начальной точки"""
        if isinstance(obs, dict):
            return obs.get('from_point', '')
        return getattr(obs, 'from_point', '')
    
    def _get_to_point(self, obs) -> str:
        """Получение конечной точки"""
        if isinstance(obs, dict):
            return obs.get('to_point', '')
        return getattr(obs, 'to_point', '')
    
    def _get_value(self, obs) -> float:
        """Получение значения измерения"""
        if isinstance(obs, dict):
            return obs.get('value', 0)
        return getattr(obs, 'value', 0)
    
    def rowCount(self, parent=None):
        return len(self._filtered_observations)
    
    def columnCount(self, parent=None):
        return len(self.HEADERS.get(self._current_tab, []))
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = self.HEADERS.get(self._current_tab, [])
            if section < len(headers):
                return headers[section]
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._filtered_observations):
            return None
        
        obs = self._filtered_observations[row]
        
        if self._current_tab == 'leveling':
            return self._leveling_data(obs, col)
        elif self._current_tab == 'total_station':
            return self._total_station_data(obs, col)
        elif self._current_tab == 'gnss':
            return self._gnss_data(obs, col)
        
        return None
    
    def _leveling_data(self, obs, col):
        """Данные для вкладки нивелирования"""
        obs_type = self._get_obs_type(obs)
        row = self._filtered_observations.index(obs)
        
        if col == 0:  # №
            return str(row + 1)
        elif col == 1:  # Тип
            type_names = {
                'height_diff': 'Превышение',
                'backsight': 'Задняя рейка',
                'foresight': 'Передняя рейка',
                'intermediate': 'Промежуточная'
            }
            return type_names.get(obs_type, obs_type)
        elif col == 2:  # От пункта
            return self._get_from_point(obs)
        elif col == 3:  # К пункту
            return self._get_to_point(obs)
        elif col == 4:  # Превышение
            value = self._get_value(obs)
            return f"{value:.5f}"
        elif col == 5:  # Расстояние
            dist = obs.get('distance') if isinstance(obs, dict) else getattr(obs, 'distance', None)
            if dist is not None:
                return f"{dist:.3f}"
            return "-"
        elif col == 6:  # Статус
            is_active = obs.get('is_active', True) if isinstance(obs, dict) else getattr(obs, 'is_active', True)
            return "Активно" if is_active else "Исключено"
        return None
    
    def _total_station_data(self, obs, col):
        """Данные для вкладки тахеометрии"""
        obs_type = self._get_obs_type(obs)
        row = self._filtered_observations.index(obs)
        
        if col == 0:  # №
            return str(row + 1)
        elif col == 1:  # Станция
            return self._get_from_point(obs)
        elif col == 2:  # Цель
            return self._get_to_point(obs)
        elif col == 3:  # Горизонтальный угол (DMS)
            if obs_type in ['direction', 'azimuth']:
                value = self._get_value(obs)
                # Конвертация из гон в градусы если нужно
                angle_unit = obs.get('angle_unit', 'gons') if isinstance(obs, dict) else getattr(obs, 'angle_unit', 'gons')
                if angle_unit == 'gons':
                    value = value * 0.9  # гоны -> градусы
                return format_dms_compact(value)
            return "-"
        elif col == 4:  # Зенитный угол (DMS)
            if obs_type in ['zenith_angle', 'vertical_angle']:
                value = self._get_value(obs)
                angle_unit = obs.get('angle_unit', 'gons') if isinstance(obs, dict) else getattr(obs, 'angle_unit', 'gons')
                if angle_unit == 'gons':
                    value = value * 0.9
                return format_dms_compact(value)
            return "-"
        elif col == 5:  # Наклонное расстояние
            if obs_type in ['slope_distance', 'distance']:
                value = self._get_value(obs)
                return f"{value:.4f}"
            return "-"
        elif col == 6:  # Горизонтальное расстояние
            if obs_type == 'horizontal_distance':
                value = self._get_value(obs)
                return f"{value:.4f}"
            return "-"
        elif col == 7:  # Статус
            is_active = obs.get('is_active', True) if isinstance(obs, dict) else getattr(obs, 'is_active', True)
            return "Активно" if is_active else "Исключено"
        return None
    
    def _gnss_data(self, obs, col):
        """Данные для вкладки GNSS векторов"""
        row = self._filtered_observations.index(obs)
        
        if col == 0:  # №
            return str(row + 1)
        elif col == 1:  # От станции
            return self._get_from_point(obs)
        elif col == 2:  # К станции
            return self._get_to_point(obs)
        elif col == 3:  # dX
            dx = obs.get('delta_x') if isinstance(obs, dict) else getattr(obs, 'delta_x', None)
            if dx is not None:
                return f"{dx:.4f}"
            return "-"
        elif col == 4:  # dY
            dy = obs.get('delta_y') if isinstance(obs, dict) else getattr(obs, 'delta_y', None)
            if dy is not None:
                return f"{dy:.4f}"
            return "-"
        elif col == 5:  # dZ
            dz = obs.get('delta_z') if isinstance(obs, dict) else getattr(obs, 'delta_z', None)
            if dz is not None:
                return f"{dz:.4f}"
            return "-"
        elif col == 6:  # σdX
            sx = obs.get('sigma_x') if isinstance(obs, dict) else getattr(obs, 'sigma_x', None)
            if sx is not None:
                return f"{sx * 1000:.2f}"
            return "-"
        elif col == 7:  # σdY
            sy = obs.get('sigma_y') if isinstance(obs, dict) else getattr(obs, 'sigma_y', None)
            if sy is not None:
                return f"{sy * 1000:.2f}"
            return "-"
        elif col == 8:  # σdZ
            sz = obs.get('sigma_z') if isinstance(obs, dict) else getattr(obs, 'sigma_z', None)
            if sz is not None:
                return f"{sz * 1000:.2f}"
            return "-"
        elif col == 9:  # Качество
            quality_map = {1: 'Fix', 2: 'Float', 3: 'SBAS', 4: 'DGPS', 5: 'Single'}
            q = obs.get('quality') if isinstance(obs, dict) else getattr(obs, 'quality', None)
            return quality_map.get(q, str(q) if q else "-")
        elif col == 10:  # Спутников
            ns = obs.get('n_satellites') if isinstance(obs, dict) else getattr(obs, 'n_satellites', None)
            return str(ns) if ns is not None else "-"
        return None
    
    def get_observation(self, row: int) -> Optional[Any]:
        """Получение измерения по строке"""
        if 0 <= row < len(self._filtered_observations):
            return self._filtered_observations[row]
        return None
    
    def update_observation(self, row: int, obs: Any):
        """Обновление измерения"""
        if 0 <= row < len(self._filtered_observations):
            self._filtered_observations[row] = obs
            self.dataChanged.emit(self.index(row, 0), 
                                 self.index(row, self.columnCount() - 1))


class ObservationsTableView(QTableView):
    """Таблица измерений с вкладками по типам"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.model = ObservationsTableModel(self)
        self.setModel(self.model)
        
        # Настройка отображения
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(False)
        
        # Настройка заголовков
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_observations(self, observations: List[Any]):
        """Установка списка измерений"""
        self.model.set_observations(observations)
    
    def set_tab(self, tab: str):
        """Переключение вкладки"""
        self.model.set_tab(tab)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        exclude_action = menu.addAction("Исключить измерение")
        include_action = menu.addAction("Включить измерение")
        menu.addSeparator()
        show_all_action = menu.addAction("Показать все измерения")
        
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == exclude_action:
            self._exclude_selected()
        elif action == include_action:
            self._include_selected()
        elif action == show_all_action:
            self.set_tab('total_station')  # По умолчанию
    
    def _exclude_selected(self):
        """Исключение выбранных измерений"""
        for index in self.selectedIndexes():
            if index.column() == 0:
                obs = self.model.get_observation(index.row())
                if obs:
                    obs.is_active = False
        self.model.set_observations(self.model._observations)
    
    def _include_selected(self):
        """Включение выбранных измерений"""
        for index in self.selectedIndexes():
            if index.column() == 0:
                obs = self.model.get_observation(index.row())
                if obs:
                    obs.is_active = True
        self.model.set_observations(self.model._observations)


class ObservationsTableWidget(QWidget):
    """Виджет таблицы измерений с кнопками управления и вкладками по типам"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Вкладки по типам измерений
        from PyQt5.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        
        self.leveling_table = ObservationsTableView()
        self.total_station_table = ObservationsTableView()
        self.gnss_table = ObservationsTableView()
        
        self.tabs.addTab(self.leveling_table, "Нивелирование")
        self.tabs.addTab(self.total_station_table, "Тахеометрия")
        self.tabs.addTab(self.gnss_table, "GNSS")
        
        layout.addWidget(self.tabs)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить")
        self.exclude_btn = QPushButton("Исключить")
        self.include_btn = QPushButton("Включить")
        self.delete_btn = QPushButton("Удалить")
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.exclude_btn)
        btn_layout.addWidget(self.include_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Подключение сигналов переключения вкладок
        self.tabs.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index):
        """Обработка переключения вкладки"""
        tab_names = ['leveling', 'total_station', 'gnss']
        if index < len(tab_names):
            table = [self.leveling_table, self.total_station_table, self.gnss_table][index]
            table.set_tab(tab_names[index])
    
    def set_observations(self, observations):
        """Установка списка измерений"""
        self.leveling_table.set_observations(observations)
        self.total_station_table.set_observations(observations)
        self.gnss_table.set_observations(observations)
        
        # Устанавливаем правильные вкладки
        self.leveling_table.set_tab('leveling')
        self.total_station_table.set_tab('total_station')
        self.gnss_table.set_tab('gnss')
    
    def update_data(self, observations):
        """Обновление данных (алиас для set_observations)"""
        self.set_observations(observations)
    
    def model(self):
        """Возврат модели текущей вкладки"""
        current_table = self.tabs.currentWidget()
        if hasattr(current_table, 'model'):
            return current_table.model()
        return None
