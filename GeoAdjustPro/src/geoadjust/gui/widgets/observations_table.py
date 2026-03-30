#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Таблица измерений
Реализует отображение и редактирование списка измерений
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                             QAbstractItemView, QMenu, QAction, QPushButton,
                             QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDialogButtonBox, QMessageBox, QLabel, QDoubleSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class ManualObservationInputDialog(QDialog):
    """Диалог ручного ввода измерения"""
    
    def __init__(self, parent=None, obs_data=None, available_points=None):
        super().__init__(parent)
        self.setWindowTitle("Ввод измерения")
        self.resize(400, 400)
        
        layout = QFormLayout(self)
        
        # ID измерения
        self.id_edit = QLineEdit()
        if obs_data:
            self.id_edit.setText(obs_data.get('id', ''))
        layout.addRow("ID измерения:", self.id_edit)
        
        # Тип измерения
        self.type_combo = QComboBox()
        self.type_combo.addItems(["direction", "distance", "height_diff", "angle", "zenith_angle"])
        if obs_data:
            idx = self.type_combo.findText(obs_data.get('type', 'direction'))
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        layout.addRow("Тип измерения:", self.type_combo)
        
        # От пункта
        self.from_point_combo = QComboBox()
        self.from_point_combo.setEditable(True)
        if available_points:
            self.from_point_combo.addItems(available_points)
        if obs_data:
            self.from_point_combo.setCurrentText(obs_data.get('from_point', ''))
        layout.addRow("От пункта:", self.from_point_combo)
        
        # К пункту
        self.to_point_combo = QComboBox()
        self.to_point_combo.setEditable(True)
        if available_points:
            self.to_point_combo.addItems(available_points)
        if obs_data:
            self.to_point_combo.setCurrentText(obs_data.get('to_point', ''))
        layout.addRow("К пункту:", self.to_point_combo)
        
        # Значение
        self.value_edit = QLineEdit()
        if obs_data:
            self.value_edit.setText(str(obs_data.get('value', '')))
        layout.addRow("Значение:", self.value_edit)
        
        # Единица измерения
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["м", "°", "′", "″", "град", "рад", "гон"])
        if obs_data:
            idx = self.unit_combo.findText(obs_data.get('unit', 'м'))
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
        layout.addRow("Единица измерения:", self.unit_combo)
        
        # СКП
        self.std_error_edit = QLineEdit()
        if obs_data:
            self.std_error_edit.setText(str(obs_data.get('std_error', '')))
        layout.addRow("СКП:", self.std_error_edit)
        
        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "excluded", "rejected"])
        if obs_data:
            idx = self.status_combo.findText(obs_data.get('status', 'active'))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
        layout.addRow("Статус:", self.status_combo)
        
        # Прибор
        self.instrument_edit = QLineEdit()
        if obs_data:
            self.instrument_edit.setText(obs_data.get('instrument', ''))
        layout.addRow("Прибор:", self.instrument_edit)
        
        # Примечание
        self.notes_edit = QLineEdit()
        if obs_data:
            self.notes_edit.setText(obs_data.get('notes', ''))
        layout.addRow("Примечание:", self.notes_edit)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_observation_data(self):
        """Получение данных измерения"""
        return {
            'id': self.id_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'from_point': self.from_point_combo.currentText().strip(),
            'to_point': self.to_point_combo.currentText().strip(),
            'value': self.value_edit.text().strip(),
            'unit': self.unit_combo.currentText(),
            'std_error': self.std_error_edit.text().strip(),
            'status': self.status_combo.currentText(),
            'instrument': self.instrument_edit.text().strip(),
            'notes': self.notes_edit.text().strip()
        }


class ObservationsTableWidget(QWidget):
    """Виджет таблицы измерений с кнопками управления"""
    
    # Сигналы
    observation_selected = pyqtSignal(str)
    observation_deleted = pyqtSignal(list)
    observation_added = pyqtSignal(dict)
    observation_edited = pyqtSignal(dict)
    observation_toggled = pyqtSignal(str, bool)
    observation_imported = pyqtSignal(list)
    
    def __init__(self, parent=None, available_points=None):
        super().__init__(parent)
        self.available_points = available_points or []
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Панель кнопок
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить измерение")
        self.add_btn.clicked.connect(self._add_observation_manual)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self._edit_observation_manual)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self._delete_observation)
        button_layout.addWidget(self.delete_btn)
        
        self.toggle_btn = QPushButton("🔄 Вкл/Выкл")
        self.toggle_btn.clicked.connect(self._toggle_observation)
        button_layout.addWidget(self.toggle_btn)
        
        button_layout.addStretch()
        
        self.import_btn = QPushButton("📂 Импорт")
        self.import_btn.clicked.connect(self._import_observations)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
        
        # Таблица
        self.table_view = ObservationsTableView(self)
        self.table_view.observation_selected.connect(self.observation_selected)
        self.table_view.observation_deleted.connect(self.observation_deleted)
        self.table_view.observation_toggled.connect(self.observation_toggled)
        self.table_view.observation_imported.connect(self.observation_imported)
        layout.addWidget(self.table_view)
    
    def set_available_points(self, points):
        """Установка доступных пунктов"""
        self.available_points = points
    
    def _add_observation_manual(self):
        """Ручное добавление измерения"""
        dialog = ManualObservationInputDialog(self, available_points=self.available_points)
        if dialog.exec_() == QDialog.Accepted:
            obs_data = dialog.get_observation_data()
            if not obs_data['id']:
                QMessageBox.warning(self, "Ошибка", "ID измерения не может быть пустым")
                return
            if not obs_data['from_point'] or not obs_data['to_point']:
                QMessageBox.warning(self, "Ошибка", "Необходимо указать начальный и конечный пункты")
                return
            
            # Добавление в таблицу
            self.table_view.add_observation_from_data(obs_data)
            self.observation_added.emit(obs_data)
    
    def _edit_observation_manual(self):
        """Ручное редактирование измерения"""
        selected = self.table_view.get_selected_observations()
        if not selected:
            QMessageBox.information(self, "Информация", "Выберите измерение для редактирования")
            return
        
        obs_data = selected[0]
        dialog = ManualObservationInputDialog(self, obs_data, self.available_points)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_observation_data()
            self.table_view.update_observation(obs_data['id'], updated_data)
            self.observation_edited.emit(updated_data)
    
    def _delete_observation(self):
        """Удаление измерения"""
        self.table_view._delete_observation()
    
    def _toggle_observation(self):
        """Переключение статуса измерения"""
        self.table_view._toggle_observation()
    
    def _import_observations(self):
        """Импорт измерений"""
        self.table_view._import_observations()
    
    def load_from_data(self, observations):
        """Загрузка данных"""
        self.table_view.load_from_data(observations)
    
    def update_data(self, observations):
        """Обновление данных"""
        self.table_view.update_data(observations)


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
    
    def update_data(self, observations: list):
        """Обновление данных таблицы (алиас для load_from_data)"""
        self.load_from_data(observations)
    
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
    
    def add_observation_from_data(self, obs_data: dict):
        """Добавление измерения из данных"""
        row_data = [
            obs_data.get('id', ''),
            obs_data.get('type', 'direction'),
            obs_data.get('from_point', ''),
            obs_data.get('to_point', ''),
            str(obs_data.get('value', '')),
            obs_data.get('unit', ''),
            str(obs_data.get('std_error', '')),
            obs_data.get('status', 'active'),
            obs_data.get('instrument', ''),
            obs_data.get('notes', '')
        ]
        items = [QStandardItem(str(val)) for val in row_data]
        self.model.appendRow(items)
    
    def update_observation(self, obs_id: str, updated_data: dict):
        """Обновление данных измерения"""
        for row in range(self.model.rowCount()):
            if self.model.index(row, 0).data() == obs_id:
                self.model.setItem(row, 0, QStandardItem(updated_data.get('id', '')))
                self.model.setItem(row, 1, QStandardItem(updated_data.get('type', 'direction')))
                self.model.setItem(row, 2, QStandardItem(updated_data.get('from_point', '')))
                self.model.setItem(row, 3, QStandardItem(updated_data.get('to_point', '')))
                self.model.setItem(row, 4, QStandardItem(str(updated_data.get('value', ''))))
                self.model.setItem(row, 5, QStandardItem(updated_data.get('unit', '')))
                self.model.setItem(row, 6, QStandardItem(str(updated_data.get('std_error', ''))))
                self.model.setItem(row, 7, QStandardItem(updated_data.get('status', 'active')))
                self.model.setItem(row, 8, QStandardItem(updated_data.get('instrument', '')))
                self.model.setItem(row, 9, QStandardItem(updated_data.get('notes', '')))
                break
