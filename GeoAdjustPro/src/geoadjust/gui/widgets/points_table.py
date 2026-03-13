#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Таблица пунктов ПВО
Реализует отображение и редактирование списка пунктов сети
"""

from PyQt5.QtWidgets import QTableView, QAbstractItemView, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class PointsTableView(QTableView):
    """Таблица пунктов ПВО"""
    
    # Сигналы
    point_selected = pyqtSignal(str)  # Сигнал при выборе пункта
    point_deleted = pyqtSignal(list)  # Сигнал при удалении пунктов
    point_added = pyqtSignal(dict)    # Сигнал при добавлении пункта
    
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
        self.model = QStandardItemModel(0, 8, self)
        self.model.setHorizontalHeaderLabels([
            "ID", "Наименование", "Тип", "X (м)", "Y (м)", 
            "H (м)", "Прибор", "Примечание"
        ])
        self.setModel(self.model)
    
    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu(self)
        
        # Команды редактирования
        add_action = QAction("Добавить пункт", self)
        add_action.triggered.connect(self._add_point)
        menu.addAction(add_action)
        
        delete_action = QAction("Удалить пункт", self)
        delete_action.triggered.connect(self._delete_point)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Команды экспорта
        export_action = QAction("Экспорт в файл", self)
        export_action.triggered.connect(self._export_points)
        menu.addAction(export_action)
        
        copy_action = QAction("Копировать в буфер", self)
        copy_action.triggered.connect(self._copy_to_clipboard)
        menu.addAction(copy_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def _on_double_click(self, index):
        """Обработка двойного клика"""
        row = index.row()
        if row >= 0:
            point_id = self.model.index(row, 0).data()
            if point_id:
                self.point_selected.emit(point_id)
    
    def _add_point(self):
        """Добавление пункта"""
        # Генерация нового ID
        new_id = f"P{self.model.rowCount() + 1:03d}"
        
        # Добавление строки
        row_data = [
            new_id,           # ID
            new_id,           # Наименование
            "FREE",           # Тип
            "",               # X
            "",               # Y
            "",               # H
            "",               # Прибор
            ""                # Примечание
        ]
        
        items = [QStandardItem(str(val)) for val in row_data]
        self.model.appendRow(items)
        
        # Генерация сигнала
        self.point_added.emit({
            'id': new_id,
            'name': new_id,
            'type': 'FREE'
        })
    
    def _delete_point(self):
        """Удаление пункта"""
        # Получение выбранных строк
        selected_rows = self.selectionModel().selectedRows()
        
        if selected_rows:
            point_ids = []
            # Удаление в обратном порядке чтобы индексы не смещались
            for index in sorted(selected_rows, reverse=True):
                row = index.row()
                point_id = self.model.index(row, 0).data()
                if point_id:
                    point_ids.append(point_id)
                self.model.removeRow(row)
            
            # Генерация сигнала удаления
            self.point_deleted.emit(point_ids)
    
    def _export_points(self):
        """Экспорт пунктов"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт пунктов",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;Все файлы (*)"
        )
        
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: str):
        """Сохранение в файл"""
        import json
        import csv
        
        points = []
        for row in range(self.model.rowCount()):
            point_data = {
                'id': self.model.index(row, 0).data(),
                'name': self.model.index(row, 1).data(),
                'type': self.model.index(row, 2).data(),
                'x': self.model.index(row, 3).data(),
                'y': self.model.index(row, 4).data(),
                'h': self.model.index(row, 5).data(),
                'instrument': self.model.index(row, 6).data(),
                'notes': self.model.index(row, 7).data()
            }
            points.append(point_data)
        
        if file_path.endswith('.json'):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(points, f, indent=2, ensure_ascii=False)
        elif file_path.endswith('.csv'):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Type', 'X', 'Y', 'H', 'Instrument', 'Notes'])
                for point in points:
                    writer.writerow([
                        point['id'], point['name'], point['type'],
                        point['x'], point['y'], point['h'],
                        point['instrument'], point['notes']
                    ])
    
    def _copy_to_clipboard(self):
        """Копирование в буфер обмена"""
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QMimeData
        
        clipboard = QApplication.clipboard()
        
        # Формирование текста
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            lines = []
            for index in selected_rows:
                row = index.row()
                row_data = []
                for col in range(self.model.columnCount()):
                    row_data.append(str(self.model.index(row, col).data() or ""))
                lines.append("\t".join(row_data))
            
            mime_data = QMimeData()
            mime_data.setText("\n".join(lines))
            clipboard.setMimeData(mime_data)
    
    def load_from_data(self, points: list):
        """Загрузка данных из списка"""
        self.model.setRowCount(0)
        
        for point in points:
            row_data = [
                point.get('id', ''),
                point.get('name', ''),
                point.get('type', 'FREE'),
                str(point.get('x', '')),
                str(point.get('y', '')),
                str(point.get('h', '')),
                point.get('instrument', ''),
                point.get('notes', '')
            ]
            items = [QStandardItem(str(val)) for val in row_data]
            self.model.appendRow(items)
    
    def get_selected_points(self) -> list:
        """Получение выбранных пунктов"""
        selected_rows = self.selectionModel().selectedRows()
        points = []
        
        for index in selected_rows:
            row = index.row()
            point_data = {
                'id': self.model.index(row, 0).data(),
                'name': self.model.index(row, 1).data(),
                'type': self.model.index(row, 2).data(),
                'x': self.model.index(row, 3).data(),
                'y': self.model.index(row, 4).data(),
                'h': self.model.index(row, 5).data()
            }
            points.append(point_data)
        
        return points
