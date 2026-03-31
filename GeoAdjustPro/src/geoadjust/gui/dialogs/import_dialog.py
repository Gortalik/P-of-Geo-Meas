"""
Диалог импорта данных из различных форматов
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QDialogButtonBox, QGroupBox, QMessageBox, QFileDialog,
    QProgressBar, QTabWidget, QWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import logging

logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Рабочий поток для импорта данных"""
    
    progress_updated = pyqtSignal(int, str)
    import_finished = pyqtSignal(dict)
    import_error = pyqtSignal(str)
    
    def __init__(self, file_path: str, format_type: str, options: Dict):
        super().__init__()
        self.file_path = file_path
        self.format_type = format_type
        self.options = options
    
    def run(self):
        """Выполнение импорта"""
        try:
            self.progress_updated.emit(10, "Открытие файла...")
            
            if self.format_type == 'dat':
                result = self._import_dat()
            elif self.format_type == 'gsi':
                result = self._import_gsi()
            elif self.format_type == 'sdr':
                result = self._import_sdr()
            elif self.format_type == 'pos':
                result = self._import_pos()
            elif self.format_type == 'csv':
                result = self._import_csv()
            elif self.format_type == 'txt':
                result = self._import_txt()
            else:
                raise ValueError(f"Неподдерживаемый формат: {self.format_type}")
            
            self.progress_updated.emit(100, "Импорт завершен")
            self.import_finished.emit(result)
            
        except Exception as e:
            logger.error(f"Ошибка импорта: {e}", exc_info=True)
            self.import_error.emit(str(e))
    
    def _import_dat(self) -> Dict:
        """Импорт из формата DAT (цифровые нивелиры)"""
        from geoadjust.io.formats.dat import DATParser
        from pathlib import Path
        
        self.progress_updated.emit(30, "Парсинг DAT файла...")
        
        parser = DATParser()
        data = parser.parse(Path(self.file_path))
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        # Конвертация в формат, ожидаемый приложением
        points = []
        for p in data.get('points', []):
            points.append({
                'name': p.get('point_id', ''),
                'x': p.get('x', 0) or 0,
                'y': p.get('y', 0) or 0,
                'h': p.get('h', 0) or 0,
                'type': p.get('point_type', 'free')
            })
        
        observations = []
        for obs in data.get('observations', []):
            observations.append({
                'from_point': getattr(obs, 'from_point', ''),
                'to_point': getattr(obs, 'to_point', ''),
                'type': getattr(obs, 'obs_type', 'height_diff'),
                'value': getattr(obs, 'value', 0),
                'sigma': getattr(obs, 'std_dev', 0.005)
            })
        
        return {
            'points': points,
            'observations': observations,
            'metadata': data.get('header_info', {})
        }
    
    def _import_gsi(self) -> Dict:
        """Импорт из формата GSI (Leica)"""
        from geoadjust.io.formats.gsi import GSIParser
        from pathlib import Path
        
        self.progress_updated.emit(30, "Парсинг GSI файла...")
        
        parser = GSIParser()
        data = parser.parse(Path(self.file_path))
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        # Конвертация в формат, ожидаемый приложением
        points = []
        for p in data.get('points', []):
            points.append({
                'name': p.get('point_id', ''),
                'x': p.get('x', 0) or 0,
                'y': p.get('y', 0) or 0,
                'h': p.get('h', 0) or 0,
                'type': p.get('point_type', 'free')
            })
        
        observations = []
        for obs in data.get('observations', []):
            observations.append({
                'from_point': getattr(obs, 'from_point', ''),
                'to_point': getattr(obs, 'to_point', ''),
                'type': getattr(obs, 'obs_type', 'direction'),
                'value': getattr(obs, 'value', 0),
                'sigma': getattr(obs, 'std_dev', 0.00005)
            })
        
        return {
            'points': points,
            'observations': observations,
            'metadata': {'version': data.get('version', ''), 'encoding': data.get('encoding', '')}
        }
    
    def _import_sdr(self) -> Dict:
        """Импорт из формата SDR (Sokkia)"""
        from geoadjust.io.formats.sdr import SDRParser
        from pathlib import Path
        
        self.progress_updated.emit(30, "Парсинг SDR файла...")
        
        parser = SDRParser()
        data = parser.parse(Path(self.file_path))
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        # Конвертация в формат, ожидаемый приложением
        points = []
        for p in data.get('points', []):
            points.append({
                'name': p.get('point_id', ''),
                'x': p.get('x', 0) or 0,
                'y': p.get('y', 0) or 0,
                'h': p.get('h', 0) or 0,
                'type': p.get('point_type', 'free')
            })
        
        observations = []
        for obs in data.get('observations', []):
            observations.append({
                'from_point': getattr(obs, 'from_point', ''),
                'to_point': getattr(obs, 'to_point', ''),
                'type': getattr(obs, 'obs_type', 'direction'),
                'value': getattr(obs, 'value', 0),
                'sigma': getattr(obs, 'std_dev', 0.00005)
            })
        
        return {
            'points': points,
            'observations': observations,
            'metadata': {'job_name': data.get('job_name', ''), 'encoding': data.get('encoding', '')}
        }
    
    def _import_pos(self) -> Dict:
        """Импорт из формата POS (RTKLIB GNSS векторы)"""
        from geoadjust.io.formats.pos import POSParser
        from pathlib import Path
        
        self.progress_updated.emit(30, "Парсинг POS файла...")
        
        parser = POSParser()
        data = parser.parse(Path(self.file_path))
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        # Получаем GNSS вектор
        vector = parser.get_gnss_vector()
        
        points = []
        observations = []
        
        if vector:
            # Добавляем точки
            points.append({
                'name': vector.from_station,
                'x': 0, 'y': 0, 'h': 0,
                'type': 'fixed'
            })
            points.append({
                'name': vector.to_station,
                'x': 0, 'y': 0, 'h': 0,
                'type': 'free'
            })
            
            # Добавляем GNSS вектор как измерение
            observations.append({
                'from_point': vector.from_station,
                'to_point': vector.to_station,
                'type': 'gnss_vector',
                'value': 0,  # Базовое значение
                'sigma': (vector.sigma_dx + vector.sigma_dy + vector.sigma_dz) / 3,
                'delta_x': vector.dx,
                'delta_y': vector.dy,
                'delta_z': vector.dz,
                'sigma_x': vector.sigma_dx,
                'sigma_y': vector.sigma_dy,
                'sigma_z': vector.sigma_dz
            })
        
        return {
            'points': points,
            'observations': observations,
            'metadata': {
                'from_station': data.get('from_station', ''),
                'to_station': data.get('to_station', ''),
                'ref_position': data.get('ref_position', None),
                'num_epochs': data.get('num_epochs', 0)
            }
        }
    
    def _import_csv(self) -> Dict:
        """Импорт из CSV файла"""
        import csv
        
        self.progress_updated.emit(30, "Чтение CSV файла...")
        
        points = []
        observations = []
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Определение типа данных по наличию полей
                if 'x' in row and 'y' in row:
                    # Это пункт
                    points.append({
                        'name': row.get('name', row.get('id', '')),
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'h': float(row.get('h', row.get('z', 0))),
                        'type': row.get('type', 'free')
                    })
                elif 'from_point' in row and 'to_point' in row:
                    # Это измерение
                    observations.append({
                        'from_point': row['from_point'],
                        'to_point': row['to_point'],
                        'type': row.get('type', 'direction'),
                        'value': float(row.get('value', 0)),
                        'sigma': float(row.get('sigma', 5.0))
                    })
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        return {
            'points': points,
            'observations': observations,
            'metadata': {}
        }
    
    def _import_txt(self) -> Dict:
        """Импорт из текстового файла"""
        self.progress_updated.emit(30, "Чтение текстового файла...")
        
        points = []
        observations = []
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Простой парсинг: каждая строка - пункт или измерение
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            
            if len(parts) >= 3:
                # Попытка распознать как пункт (имя x y [h])
                try:
                    name = parts[0]
                    x = float(parts[1])
                    y = float(parts[2])
                    h = float(parts[3]) if len(parts) > 3 else 0.0
                    
                    points.append({
                        'name': name,
                        'x': x,
                        'y': y,
                        'h': h,
                        'type': 'free'
                    })
                except ValueError:
                    # Не удалось распознать
                    pass
        
        self.progress_updated.emit(80, "Обработка данных...")
        
        return {
            'points': points,
            'observations': observations,
            'metadata': {}
        }


class ImportDialog(QDialog):
    """Диалог импорта данных"""
    
    data_imported = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.imported_data = None
        self.worker = None
        
        self.setWindowTitle("Импорт данных")
        self.setMinimumSize(700, 500)
        
        self._create_ui()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка "Файл"
        file_tab = self._create_file_tab()
        tabs.addTab(file_tab, "Выбор файла")
        
        # Вкладка "Параметры"
        options_tab = self._create_options_tab()
        tabs.addTab(options_tab, "Параметры")
        
        # Вкладка "Предпросмотр"
        preview_tab = self._create_preview_tab()
        tabs.addTab(preview_tab, "Предпросмотр")
        
        layout.addWidget(tabs)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Импортировать")
        self.import_btn.clicked.connect(self._start_import)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        button_layout.addWidget(self.ok_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_file_tab(self) -> QWidget:
        """Создание вкладки выбора файла"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Выбор файла
        file_group = QGroupBox("Файл для импорта")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(file_group)
        
        # Формат файла
        format_group = QGroupBox("Формат данных")
        format_layout = QFormLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Автоопределение",
            "DAT (цифровые нивелиры)",
            "GSI (Leica)",
            "SDR (Sokkia)",
            "POS (RTKLIB GNSS)",
            "CSV (разделители запятыми)",
            "TXT (текстовый файл)"
        ])
        format_layout.addRow("Формат:", self.format_combo)
        
        layout.addWidget(format_group)
        
        # Информация о файле
        info_group = QGroupBox("Информация о файле")
        info_layout = QFormLayout(info_group)
        
        self.file_size_label = QLabel("-")
        info_layout.addRow("Размер:", self.file_size_label)
        
        self.file_encoding_label = QLabel("-")
        info_layout.addRow("Кодировка:", self.file_encoding_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_options_tab(self) -> QWidget:
        """Создание вкладки параметров"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Параметры импорта
        import_group = QGroupBox("Параметры импорта")
        import_layout = QVBoxLayout(import_group)
        
        self.import_points_check = QCheckBox("Импортировать пункты")
        self.import_points_check.setChecked(True)
        import_layout.addWidget(self.import_points_check)
        
        self.import_observations_check = QCheckBox("Импортировать измерения")
        self.import_observations_check.setChecked(True)
        import_layout.addWidget(self.import_observations_check)
        
        self.skip_duplicates_check = QCheckBox("Пропускать дубликаты")
        self.skip_duplicates_check.setChecked(True)
        import_layout.addWidget(self.skip_duplicates_check)
        
        self.update_existing_check = QCheckBox("Обновлять существующие данные")
        import_layout.addWidget(self.update_existing_check)
        
        layout.addWidget(import_group)
        
        # Система координат
        crs_group = QGroupBox("Система координат")
        crs_layout = QFormLayout(crs_group)
        
        self.crs_combo = QComboBox()
        self.crs_combo.addItems([
            "Из файла",
            "МСК-33",
            "МСК-50",
            "МСК-63",
            "WGS-84",
            "ПЗ-90"
        ])
        crs_layout.addRow("СК:", self.crs_combo)
        
        layout.addWidget(crs_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_preview_tab(self) -> QWidget:
        """Создание вкладки предпросмотра"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Таблица предпросмотра
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(["Тип", "Название", "X/От", "Y/До", "H/Значение"])
        layout.addWidget(self.preview_table)
        
        # Статистика
        stats_layout = QHBoxLayout()
        
        self.points_count_label = QLabel("Пунктов: 0")
        stats_layout.addWidget(self.points_count_label)
        
        self.observations_count_label = QLabel("Измерений: 0")
        stats_layout.addWidget(self.observations_count_label)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        return widget
    
    def _browse_file(self):
        """Выбор файла для импорта"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбор файла для импорта",
            "",
            "Все поддерживаемые (*.dat *.gsi *.sdr *.pos *.csv *.txt);;"
            "DAT файлы (*.dat);;"
            "GSI файлы (*.gsi);;"
            "SDR файлы (*.sdr);;"
            "POS файлы (*.pos);;"
            "CSV файлы (*.csv);;"
            "Текстовые файлы (*.txt);;"
            "Все файлы (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self._analyze_file(file_path)
            self.import_btn.setEnabled(True)
    
    def _analyze_file(self, file_path: str):
        """Анализ файла"""
        try:
            path = Path(file_path)
            
            # Размер файла
            size = path.stat().st_size
            if size < 1024:
                size_str = f"{size} байт"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} КБ"
            else:
                size_str = f"{size / (1024 * 1024):.1f} МБ"
            
            self.file_size_label.setText(size_str)
            
            # Определение кодировки
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)
            
            try:
                raw_data.decode('utf-8')
                encoding = "UTF-8"
            except:
                encoding = "Windows-1251"
            
            self.file_encoding_label.setText(encoding)
            
            # Автоопределение формата
            ext = path.suffix.lower()
            format_map = {
                '.dat': 1,
                '.gsi': 2,
                '.sdr': 3,
                '.pos': 4,
                '.csv': 5,
                '.txt': 6
            }
            
            if ext in format_map and self.format_combo.currentIndex() == 0:
                self.format_combo.setCurrentIndex(format_map[ext])
            
        except Exception as e:
            logger.error(f"Ошибка анализа файла: {e}", exc_info=True)
    
    def _start_import(self):
        """Запуск импорта"""
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Предупреждение", "Выберите файл для импорта")
            return
        
        # Определение формата
        format_index = self.format_combo.currentIndex()
        format_map = {
            0: 'auto',
            1: 'dat',
            2: 'gsi',
            3: 'sdr',
            4: 'pos',
            5: 'csv',
            6: 'txt'
        }
        format_type = format_map[format_index]
        
        # Автоопределение формата
        if format_type == 'auto':
            ext = Path(file_path).suffix.lower()
            format_type = ext[1:] if ext else 'txt'
        
        # Параметры импорта
        options = {
            'import_points': self.import_points_check.isChecked(),
            'import_observations': self.import_observations_check.isChecked(),
            'skip_duplicates': self.skip_duplicates_check.isChecked(),
            'update_existing': self.update_existing_check.isChecked()
        }
        
        # Запуск рабочего потока
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(False)
        
        self.worker = ImportWorker(file_path, format_type, options)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.import_finished.connect(self._on_import_finished)
        self.worker.import_error.connect(self._on_import_error)
        self.worker.start()
    
    def _on_progress_updated(self, percent: int, message: str):
        """Обновление прогресса"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
    
    def _on_import_finished(self, data: Dict):
        """Завершение импорта"""
        self.imported_data = data
        
        # Обновление предпросмотра
        self._update_preview(data)
        
        # Обновление статистики
        points_count = len(data.get('points', []))
        observations_count = len(data.get('observations', []))
        
        self.points_count_label.setText(f"Пунктов: {points_count}")
        self.observations_count_label.setText(f"Измерений: {observations_count}")
        
        self.status_label.setText(f"Импорт завершен: {points_count} пунктов, {observations_count} измерений")
        self.ok_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Успех",
            f"Данные успешно импортированы:\n"
            f"Пунктов: {points_count}\n"
            f"Измерений: {observations_count}"
        )
    
    def _on_import_error(self, error_msg: str):
        """Ошибка импорта"""
        self.status_label.setText(f"Ошибка: {error_msg}")
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Ошибка", f"Ошибка импорта:\n{error_msg}")
    
    def _update_preview(self, data: Dict):
        """Обновление предпросмотра"""
        self.preview_table.setRowCount(0)
        
        # Добавление пунктов
        for point in data.get('points', [])[:50]:  # Первые 50
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            
            self.preview_table.setItem(row, 0, QTableWidgetItem("Пункт"))
            self.preview_table.setItem(row, 1, QTableWidgetItem(point.get('name', '')))
            self.preview_table.setItem(row, 2, QTableWidgetItem(f"{point.get('x', 0):.4f}"))
            self.preview_table.setItem(row, 3, QTableWidgetItem(f"{point.get('y', 0):.4f}"))
            self.preview_table.setItem(row, 4, QTableWidgetItem(f"{point.get('h', 0):.4f}"))
        
        # Добавление измерений
        for obs in data.get('observations', [])[:50]:  # Первые 50
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            
            self.preview_table.setItem(row, 0, QTableWidgetItem("Измерение"))
            self.preview_table.setItem(row, 1, QTableWidgetItem(obs.get('type', '')))
            self.preview_table.setItem(row, 2, QTableWidgetItem(obs.get('from_point', '')))
            self.preview_table.setItem(row, 3, QTableWidgetItem(obs.get('to_point', '')))
            self.preview_table.setItem(row, 4, QTableWidgetItem(f"{obs.get('value', 0):.6f}"))
        
        self.preview_table.resizeColumnsToContents()
    
    def get_imported_data(self) -> Optional[Dict]:
        """Получение импортированных данных"""
        return self.imported_data
