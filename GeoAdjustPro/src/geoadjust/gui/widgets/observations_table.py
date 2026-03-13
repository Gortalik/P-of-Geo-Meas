#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Таблица измерений
Реализует отображение и редактирование списка измерений
"""

from PyQt5.QtWidgets import QTableView, QAbstractItemView, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class ObservationsTableView(QTableView):
    """Таблица измерений"""
    
    # Сигналы
    observation_selected = pyqtSignal(str)
    observation_toggled = pyqtSignal(str, bool)  # Сигнал при отключении/включении измерения
    observation_deleted = pyqtSignal(list)
    observation_imported = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Настройка таблицы
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
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
        self.model = QStandardItemModel(0, 10, self)
        self.model.setHorizontalHeaderLabels([
            "ID", "Тип", "От пункта", "К пункту", 
            "Значение", "Ед. изм.", "СКП", "Статус",
            "Прибор", "Примечание"
        ])
        self.setModel(self.model)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        # Команды импорта
        import_action = QAction("Импорт из файла", self)
        import_action.triggered.connect(self._import_observations)
        menu.addAction(import_action)
        
        menu.addSeparator()
        
        # Команды редактирования
        delete_action = QAction("Удалить измерение", self)
        delete_action.triggered.connect(self._delete_observation)
        menu.addAction(delete_action)
        
        toggle_action = QAction("Отключить измерение", self)
        toggle_action.triggered.connect(self._toggle_observation)
        menu.addAction(toggle_action)
        
        menu.addSeparator()
        
        # Команды экспорта
        export_action = QAction("Экспорт в файл", self)
        export_action.triggered.connect(self._export_observations)
        menu.addAction(export_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _on_double_click(self, index):
        """Обработка двойного клика"""
        row = index.row()
        if row >= 0:
            obs_id = self.model.index(row, 0).data()
            if obs_id:
                self.observation_selected.emit(obs_id)
    
    def _import_observations(self):
        """Импорт измерений"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт измерений",
            "",
            "All Supported Files (*.gsi *.sdr *.dat);;"
            "Leica GSI (*.gsi);;Sokkia SDR (*.sdr);;DAT Files (*.dat);;"
            "Все файлы (*)"
        )
        
        if file_path:
            # Здесь будет логика импорта в зависимости от формата
            imported_data = self._parse_file(file_path)
            if imported_data:
                self._add_observations(imported_data)
                self.observation_imported.emit(imported_data)
    
    def _parse_file(self, file_path: str) -> list:
        """Парсинг файла измерений"""
        # Заглушка для примера
        # В реальной реализации здесь будет вызов соответствующего парсера
        return []
    
    def _add_observations(self, observations: list):
        """Добавление измерений в таблицу"""
        for obs in observations:
            row_data = [
                obs.get('id', ''),
                obs.get('type', 'direction'),
                obs.get('from_point', ''),
                obs.get('to_point', ''),
                str(obs.get('value', '')),
                obs.get('unit', ''),
                str(obs.get('std_error', '')),
                obs.get('status', 'active'),
                obs.get('instrument', ''),
                obs.get('notes', '')
            ]
            items = [QStandardItem(str(val)) for val in row_data]
            self.model.appendRow(items)
    
    def _delete_observation(self):
        """Удаление измерения"""
        selected_rows = self.selectionModel().selectedRows()
        
        if selected_rows:
            obs_ids = []
            for index in sorted(selected_rows, reverse=True):
                row = index.row()
                obs_id = self.model.index(row, 0).data()
                if obs_id:
                    obs_ids.append(obs_id)
                self.model.removeRow(row)
            
            self.observation_deleted.emit(obs_ids)
    
    def _toggle_observation(self):
        """Отключение/включение измерения"""
        selected_rows = self.selectionModel().selectedRows()
        
        if selected_rows:
            for index in selected_rows:
                row = index.row()
                obs_id = self.model.index(row, 0).data()
                status = self.model.index(row, 7).data()
                
                # Переключение статуса
                new_status = "excluded" if status == "active" else "active"
                self.model.setItem(row, 7, QStandardItem(new_status))
                
                if obs_id:
                    is_active = new_status == "active"
                    self.observation_toggled.emit(obs_id, is_active)
    
    def _export_observations(self):
        """Экспорт измерений"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт измерений",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;Все файлы (*)"
        )
        
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: str):
        """Сохранение в файл"""
        import json
        import csv
        
        observations = []
        for row in range(self.model.rowCount()):
            obs_data = {
                'id': self.model.index(row, 0).data(),
                'type': self.model.index(row, 1).data(),
                'from_point': self.model.index(row, 2).data(),
                'to_point': self.model.index(row, 3).data(),
                'value': self.model.index(row, 4).data(),
                'unit': self.model.index(row, 5).data(),
                'std_error': self.model.index(row, 6).data(),
                'status': self.model.index(row, 7).data(),
                'instrument': self.model.index(row, 8).data(),
                'notes': self.model.index(row, 9).data()
            }
            observations.append(obs_data)
        
        if file_path.endswith('.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(observations, f, indent=2, ensure_ascii=False)
        elif file_path.endswith('.csv'):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Type', 'From', 'To', 'Value', 'Unit', 'StdError', 'Status', 'Instrument', 'Notes'])
                for obs in observations:
                    writer.writerow([
                        obs['id'], obs['type'], obs['from_point'], obs['to_point'],
                        obs['value'], obs['unit'], obs['std_error'], obs['status'],
                        obs['instrument'], obs['notes']
                    ])
    
    def load_from_data(self, observations: list):
        """Загрузка данных из списка"""
        self.model.setRowCount(0)
        
        for obs in observations:
            row_data = [
                obs.get('id', ''),
                obs.get('type', 'direction'),
                obs.get('from_point', ''),
                obs.get('to_point', ''),
                str(obs.get('value', '')),
                obs.get('unit', ''),
                str(obs.get('std_error', '')),
                obs.get('status', 'active'),
                obs.get('instrument', ''),
                obs.get('notes', '')
            ]
            items = [QStandardItem(str(val)) for val in row_data]
            self.model.appendRow(items)
    
    def get_selected_observations(self) -> list:
        """Получение выбранных измерений"""
        selected_rows = self.selectionModel().selectedRows()
        observations = []
        
        for index in selected_rows:
            row = index.row()
            obs_data = {
                'id': self.model.index(row, 0).data(),
                'type': self.model.index(row, 1).data(),
                'from_point': self.model.index(row, 2).data(),
                'to_point': self.model.index(row, 3).data(),
                'value': self.model.index(row, 4).data(),
                'status': self.model.index(row, 7).data()
            }
            observations.append(obs_data)
        
        return observations
    
    def update_observation_status(self, obs_id: str, status: str):
        """Обновление статуса измерения"""
        for row in range(self.model.rowCount()):
            if self.model.index(row, 0).data() == obs_id:
                self.model.setItem(row, 7, QStandardItem(status))
                break
