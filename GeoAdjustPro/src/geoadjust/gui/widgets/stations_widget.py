#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Виджет отображения станций с раскрывающимися измерениями.

Каждая станция (сессия) отображается как отдельный элемент.
При нажатии на станцию раскрываются все измерения на этой станции.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                              QHeaderView, QLabel, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from typing import List, Dict, Any, Optional


class StationsTreeWidget(QTreeWidget):
    """Дерево станций с раскрывающимися измерениями"""
    
    station_selected = pyqtSignal(str)  # session_id
    observation_selected = pyqtSignal(dict)  # observation data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderLabels(["Станция", "Тип", "Значение", "Цель"])
        self.setSelectionBehavior(QTreeWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setIndentation(20)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(self._on_item_expanded)
        
        self._sessions_data = []
    
    def set_station_sessions(self, sessions: List[Dict[str, Any]]):
        """Установка данных о сессиях станций"""
        self.clear()
        self._sessions_data = sessions
        
        type_names = {
            'direction': 'Направление',
            'zenith_angle': 'Зен. угол',
            'vertical_angle': 'Верт. угол',
            'slope_distance': 'Накл. расст.',
            'horizontal_distance': 'Гор. расст.',
            'height_diff': 'Превышение',
        }
        
        for session in sessions:
            session_id = session.get('session_id', '')
            station_name = session.get('station_name', '')
            num_obs = session.get('num_observations', 0)
            instr_h = session.get('instrument_height')
            
            # Создаём элемент станции
            station_item = QTreeWidgetItem(self)
            station_item.setData(0, Qt.UserRole, {'type': 'station', 'session_id': session_id})
            
            # Формируем текст станции
            station_text = f"{station_name} ({num_obs} изм.)"
            if instr_h is not None:
                station_text += f" | i={instr_h:.4f}"
            
            station_item.setText(0, station_text)
            station_item.setText(1, f"Сессия")
            station_item.setText(2, "")
            station_item.setText(3, "")
            
            # Жирный шрифт для станции
            font = station_item.font(0)
            font.setBold(True)
            station_item.setFont(0, font)
            
            # Цвет фона
            station_item.setBackground(0, QColor(230, 240, 250))
            station_item.setBackground(1, QColor(230, 240, 250))
            station_item.setBackground(2, QColor(230, 240, 250))
            station_item.setBackground(3, QColor(230, 240, 250))
            
            # Добавляем измерения как дочерние элементы
            observations = session.get('observations', [])
            for obs in observations:
                obs_item = QTreeWidgetItem(station_item)
                obs_type = obs.get('obs_type', '')
                obs_value = obs.get('value', 0)
                to_point = obs.get('to_point', '')
                
                obs_item.setData(0, Qt.UserRole, {
                    'type': 'observation',
                    'session_id': session_id,
                    'observation': obs
                })
                
                obs_item.setText(0, f"  -> {to_point}")
                obs_item.setText(1, type_names.get(obs_type, obs_type))
                obs_item.setText(2, f"{obs_value:.5f}")
                obs_item.setText(3, to_point)
                
                # Цвет для разных типов измерений
                if obs_type in ['direction', 'zenith_angle']:
                    obs_item.setForeground(1, QColor(0, 100, 200))
                elif obs_type in ['slope_distance', 'horizontal_distance']:
                    obs_item.setForeground(1, QColor(0, 150, 0))
                elif obs_type == 'height_diff':
                    obs_item.setForeground(1, QColor(200, 100, 0))
        
        self.expandAll()
    
    def _on_item_clicked(self, item, column):
        """Обработка клика по элементу"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        
        if data.get('type') == 'station':
            self.station_selected.emit(data.get('session_id', ''))
        elif data.get('type') == 'observation':
            self.observation_selected.emit(data.get('observation', {}))
    
    def _on_item_expanded(self, item):
        """Обработка раскрытия элемента"""
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'station':
            self.station_selected.emit(data.get('session_id', ''))
    
    def get_selected_session_id(self) -> Optional[str]:
        """Получение ID выбранной сессии"""
        selected = self.selectedItems()
        if not selected:
            return None
        
        data = selected[0].data(0, Qt.UserRole)
        if data and data.get('type') == 'station':
            return data.get('session_id')
        return None
    
    def clear_data(self):
        """Очистка данных"""
        self.clear()
        self._sessions_data = []


class StationsDockContent(QWidget):
    """Виджет содержимого для dock-панели станций"""
    
    station_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Заголовок
        header_label = QLabel("Станции измерений")
        header_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(header_label)
        
        # Дерево станций
        self.tree = StationsTreeWidget(self)
        self.tree.station_selected.connect(self.station_selected)
        layout.addWidget(self.tree)
        
        # Кнопки
        btn_layout = QHBoxLayout()

        self.show_all_btn = QPushButton("Показать все")
        self.expand_all_btn = QPushButton("Развернуть все")
        self.collapse_all_btn = QPushButton("Свернуть все")

        btn_layout.addWidget(self.show_all_btn)
        btn_layout.addWidget(self.expand_all_btn)
        btn_layout.addWidget(self.collapse_all_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self.show_all_btn.clicked.connect(lambda: self.station_selected.emit(""))
        self.expand_all_btn.clicked.connect(self.tree.expandAll)
        self.collapse_all_btn.clicked.connect(self.tree.collapseAll)
    
    def set_station_sessions(self, sessions: List[Dict[str, Any]]):
        """Установка данных о сессиях станций"""
        if not sessions:
            self.clear()
            return

        self.tree.set_station_sessions(sessions)

        # Автоматически выбираем первую станцию и применяем фильтр
        if sessions:
            first_session = sessions[0]
            first_session_id = first_session.get('session_id', '')
            if first_session_id:
                self.station_selected.emit(first_session_id)
    
    def clear(self):
        """Очистка данных"""
        self.tree.clear_data()
