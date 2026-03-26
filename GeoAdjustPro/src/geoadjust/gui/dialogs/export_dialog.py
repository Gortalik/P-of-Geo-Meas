"""
Диалог экспорта данных в различные форматы
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QDialogButtonBox, QGroupBox, QMessageBox, QFileDialog,
    QProgressBar, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import logging

logger = logging.getLogger(__name__)


class ExportWorker(QThread):
    """Рабочий поток для экспорта данных"""
    
    progress_updated = pyqtSignal(int, str)
    export_finished = pyqtSignal(str)
    export_error = pyqtSignal(str)
    
    def __init__(self, project, file_path: str, format_type: str, options: Dict):
        super().__init__()
        self.project = project
        self.file_path = file_path
        self.format_type = format_type
        self.options = options
    
    def run(self):
        """Выполнение экспорта"""
        try:
            self.progress_updated.emit(10, "Подготовка данных...")
            
            if self.format_type == 'dat':
                self._export_dat()
            elif self.format_type == 'gsi':
                self._export_gsi()
            elif self.format_type == 'sdr':
                self._export_sdr()
            elif self.format_type == 'csv':
                self._export_csv()
            elif self.format_type == 'dxf':
                self._export_dxf()
            elif self.format_type == 'xml':
                self._export_xml()
            elif self.format_type == 'json':
                self._export_json()
            else:
                raise ValueError(f"Неподдерживаемый формат: {self.format_type}")
            
            self.progress_updated.emit(100, "Экспорт завершен")
            self.export_finished.emit(self.file_path)
            
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}", exc_info=True)
            self.export_error.emit(str(e))
    
    def _export_dat(self):
        """Экспорт в формат DAT (КРЕДО)"""
        from geoadjust.io.formats.dat import DATParser
        
        self.progress_updated.emit(30, "Формирование DAT файла...")
        
        parser = DATParser()
        data = {
            'points': self.project.get_points() if self.options.get('export_points') else [],
            'observations': self.project.get_observations() if self.options.get('export_observations') else []
        }
        
        self.progress_updated.emit(70, "Запись файла...")
        parser.write_file(self.file_path, data)
    
    def _export_gsi(self):
        """Экспорт в формат GSI (Leica)"""
        from geoadjust.io.formats.gsi import GSIParser
        
        self.progress_updated.emit(30, "Формирование GSI файла...")
        
        parser = GSIParser()
        data = {
            'points': self.project.get_points() if self.options.get('export_points') else [],
            'observations': self.project.get_observations() if self.options.get('export_observations') else []
        }
        
        self.progress_updated.emit(70, "Запись файла...")
        parser.write_file(self.file_path, data)
    
    def _export_sdr(self):
        """Экспорт в формат SDR (Sokkia)"""
        from geoadjust.io.formats.sdr import SDRParser
        
        self.progress_updated.emit(30, "Формирование SDR файла...")
        
        parser = SDRParser()
        data = {
            'points': self.project.get_points() if self.options.get('export_points') else [],
            'observations': self.project.get_observations() if self.options.get('export_observations') else []
        }
        
        self.progress_updated.emit(70, "Запись файла...")
        parser.write_file(self.file_path, data)
    
    def _export_csv(self):
        """Экспорт в CSV"""
        import csv
        
        self.progress_updated.emit(30, "Формирование CSV файла...")
        
        with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Экспорт пунктов
            if self.options.get('export_points'):
                writer.writerow(['# Пункты'])
                writer.writerow(['name', 'x', 'y', 'h', 'type'])
                
                for point in self.project.get_points():
                    writer.writerow([
                        point.get('name', ''),
                        point.get('x', 0),
                        point.get('y', 0),
                        point.get('h', 0),
                        point.get('type', 'free')
                    ])
                
                writer.writerow([])
            
            # Экспорт измерений
            if self.options.get('export_observations'):
                writer.writerow(['# Измерения'])
                writer.writerow(['from_point', 'to_point', 'type', 'value', 'sigma'])
                
                for obs in self.project.get_observations():
                    writer.writerow([
                        obs.get('from_point', ''),
                        obs.get('to_point', ''),
                        obs.get('type', ''),
                        obs.get('value', 0),
                        obs.get('sigma', 0)
                    ])
        
        self.progress_updated.emit(70, "Запись файла...")
    
    def _export_dxf(self):
        """Экспорт в DXF"""
        from geoadjust.io.export.dxf_export import DXFExporter
        
        self.progress_updated.emit(30, "Формирование DXF файла...")
        
        exporter = DXFExporter()
        
        self.progress_updated.emit(70, "Запись файла...")
        exporter.export(
            self.project.get_points(),
            self.project.get_observations() if self.options.get('export_observations') else [],
            self.file_path
        )
    
    def _export_xml(self):
        """Экспорт в XML"""
        import xml.etree.ElementTree as ET
        
        self.progress_updated.emit(30, "Формирование XML файла...")
        
        root = ET.Element('geodetic_network')
        root.set('project', self.project.name)
        
        # Пункты
        if self.options.get('export_points'):
            points_elem = ET.SubElement(root, 'points')
            for point in self.project.get_points():
                point_elem = ET.SubElement(points_elem, 'point')
                point_elem.set('name', point.get('name', ''))
                point_elem.set('type', point.get('type', 'free'))
                
                coords = ET.SubElement(point_elem, 'coordinates')
                coords.set('x', str(point.get('x', 0)))
                coords.set('y', str(point.get('y', 0)))
                coords.set('h', str(point.get('h', 0)))
        
        # Измерения
        if self.options.get('export_observations'):
            obs_elem = ET.SubElement(root, 'observations')
            for obs in self.project.get_observations():
                observation = ET.SubElement(obs_elem, 'observation')
                observation.set('type', obs.get('type', ''))
                observation.set('from', obs.get('from_point', ''))
                observation.set('to', obs.get('to_point', ''))
                observation.set('value', str(obs.get('value', 0)))
                observation.set('sigma', str(obs.get('sigma', 0)))
        
        self.progress_updated.emit(70, "Запись файла...")
        
        tree = ET.ElementTree(root)
        tree.write(self.file_path, encoding='utf-8', xml_declaration=True)
    
    def _export_json(self):
        """Экспорт в JSON"""
        import json
        
        self.progress_updated.emit(30, "Формирование JSON файла...")
        
        data = {
            'project': {
                'name': self.project.name,
                'description': getattr(self.project, 'description', '')
            }
        }
        
        if self.options.get('export_points'):
            data['points'] = self.project.get_points()
        
        if self.options.get('export_observations'):
            data['observations'] = self.project.get_observations()
        
        self.progress_updated.emit(70, "Запись файла...")
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class ExportDialog(QDialog):
    """Диалог экспорта данных"""
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        
        self.project = project
        self.worker = None
        
        self.setWindowTitle("Экспорт данных")
        self.setMinimumSize(600, 450)
        
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Выбор файла
        file_group = QGroupBox("Файл для экспорта")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # Формат
        format_group = QGroupBox("Формат экспорта")
        format_layout = QFormLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "DAT (КРЕДО)",
            "GSI (Leica)",
            "SDR (Sokkia)",
            "CSV (разделители запятыми)",
            "DXF (AutoCAD)",
            "XML (расширяемый)",
            "JSON (JavaScript Object Notation)"
        ])
        format_layout.addRow("Формат:", self.format_combo)
        
        layout.addWidget(format_group)
        
        # Параметры экспорта
        options_group = QGroupBox("Параметры экспорта")
        options_layout = QVBoxLayout(options_group)
        
        self.export_points_check = QCheckBox("Экспортировать пункты")
        self.export_points_check.setChecked(True)
        options_layout.addWidget(self.export_points_check)
        
        self.export_observations_check = QCheckBox("Экспортировать измерения")
        self.export_observations_check.setChecked(True)
        options_layout.addWidget(self.export_observations_check)
        
        self.export_results_check = QCheckBox("Экспортировать результаты уравнивания")
        options_layout.addWidget(self.export_results_check)
        
        layout.addWidget(options_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Экспортировать")
        self.export_btn.clicked.connect(self._start_export)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_file(self):
        """Выбор файла для экспорта"""
        format_index = self.format_combo.currentIndex()
        
        filters = {
            0: "DAT файлы (*.dat);;Все файлы (*)",
            1: "GSI файлы (*.gsi);;Все файлы (*)",
            2: "SDR файлы (*.sdr);;Все файлы (*)",
            3: "CSV файлы (*.csv);;Все файлы (*)",
            4: "DXF файлы (*.dxf);;Все файлы (*)",
            5: "XML файлы (*.xml);;Все файлы (*)",
            6: "JSON файлы (*.json);;Все файлы (*)"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            "",
            filters.get(format_index, "Все файлы (*)")
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.export_btn.setEnabled(True)
    
    def _start_export(self):
        """Запуск экспорта"""
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите файл для экспорта")
            return
        
        # Определение формата
        format_map = {
            0: 'dat',
            1: 'gsi',
            2: 'sdr',
            3: 'csv',
            4: 'dxf',
            5: 'xml',
            6: 'json'
        }
        format_type = format_map[self.format_combo.currentIndex()]
        
        # Параметры экспорта
        options = {
            'export_points': self.export_points_check.isChecked(),
            'export_observations': self.export_observations_check.isChecked(),
            'export_results': self.export_results_check.isChecked()
        }
        
        # Запуск рабочего потока
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.export_btn.setEnabled(False)
        
        self.worker = ExportWorker(self.project, file_path, format_type, options)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.export_finished.connect(self._on_export_finished)
        self.worker.export_error.connect(self._on_export_error)
        self.worker.start()
    
    def _on_progress_updated(self, percent: int, message: str):
        """Обновление прогресса"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
    
    def _on_export_finished(self, file_path: str):
        """Завершение экспорта"""
        self.status_label.setText(f"Экспорт завершен: {file_path}")
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self,
            "Успех",
            f"Данные успешно экспортированы в:\n{file_path}"
        )
    
    def _on_export_error(self, error_msg: str):
        """Ошибка экспорта"""
        self.status_label.setText(f"Ошибка: {error_msg}")
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта:\n{error_msg}")
