"""
Диалог свойств проекта GeoAdjust Pro

Настройка параметров проекта:
- Карточка проекта
- Система координат
- Инструменты (библиотека приборов)
- Классы точности
- Предобработка
- Уравнивание
- Поиск ошибок
- Отчётность
"""

from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QWidget,
    QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QPushButton, QDialogButtonBox,
    QGroupBox, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class InstrumentDialog(QDialog):
    """Диалог добавления/редактирования прибора"""
    
    def __init__(self, parent=None, instrument_data=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка прибора")
        self.resize(500, 450)
        
        layout = QFormLayout(self)
        
        # Название прибора
        self.name_edit = QLineEdit()
        if instrument_data:
            self.name_edit.setText(instrument_data.get('name', ''))
        layout.addRow("Название:", self.name_edit)
        
        # Тип прибора
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Тахеометр",
            "Теодолит",
            "Нивелир",
            "GPS/GNSS приёмник",
            "Лазерный дальномер",
            "Другое"
        ])
        if instrument_data:
            idx = self.type_combo.findText(instrument_data.get('type', 'Тахеометр'))
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        layout.addRow("Тип:", self.type_combo)
        
        # Производитель
        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setEditable(True)
        self.manufacturer_combo.addItems([
            "Leica",
            "Trimble",
            "Topcon",
            "Sokkia",
            "Nikon",
            "Pentax",
            "South",
            "FOIF",
            "Другой"
        ])
        if instrument_data:
            self.manufacturer_combo.setCurrentText(instrument_data.get('manufacturer', ''))
        layout.addRow("Производитель:", self.manufacturer_combo)
        
        # Модель
        self.model_edit = QLineEdit()
        if instrument_data:
            self.model_edit.setText(instrument_data.get('model', ''))
        layout.addRow("Модель:", self.model_edit)
        
        # Серийный номер
        self.serial_edit = QLineEdit()
        if instrument_data:
            self.serial_edit.setText(instrument_data.get('serial_number', ''))
        layout.addRow("Серийный номер:", self.serial_edit)
        
        # Группа угловых измерений
        angular_group = QGroupBox("Угловые измерения")
        angular_layout = QFormLayout(angular_group)
        
        self.angular_accuracy_spin = QDoubleSpinBox()
        self.angular_accuracy_spin.setRange(0.1, 60.0)
        self.angular_accuracy_spin.setValue(1.0)
        self.angular_accuracy_spin.setSuffix(" \"")
        self.angular_accuracy_spin.setDecimals(1)
        if instrument_data:
            self.angular_accuracy_spin.setValue(instrument_data.get('angular_accuracy', 1.0))
        angular_layout.addRow("СКО угла:", self.angular_accuracy_spin)
        
        self.angular_repeatability_spin = QDoubleSpinBox()
        self.angular_repeatability_spin.setRange(0.1, 10.0)
        self.angular_repeatability_spin.setValue(0.5)
        self.angular_repeatability_spin.setSuffix(" \"")
        self.angular_repeatability_spin.setDecimals(1)
        if instrument_data:
            self.angular_repeatability_spin.setValue(instrument_data.get('angular_repeatability', 0.5))
        angular_layout.addRow("Повторяемость:", self.angular_repeatability_spin)
        
        self.compensator_accuracy_spin = QDoubleSpinBox()
        self.compensator_accuracy_spin.setRange(0.1, 5.0)
        self.compensator_accuracy_spin.setValue(0.3)
        self.compensator_accuracy_spin.setSuffix(" \"")
        self.compensator_accuracy_spin.setDecimals(1)
        if instrument_data:
            self.compensator_accuracy_spin.setValue(instrument_data.get('compensator_accuracy', 0.3))
        angular_layout.addRow("Компенсатор:", self.compensator_accuracy_spin)
        
        layout.addRow(angular_group)
        
        # Группа линейных измерений
        distance_group = QGroupBox("Линейные измерения")
        distance_layout = QFormLayout(distance_group)
        
        self.distance_accuracy_a_spin = QDoubleSpinBox()
        self.distance_accuracy_a_spin.setRange(0.1, 100.0)
        self.distance_accuracy_a_spin.setValue(1.0)
        self.distance_accuracy_a_spin.setSuffix(" мм")
        self.distance_accuracy_a_spin.setDecimals(1)
        if instrument_data:
            self.distance_accuracy_a_spin.setValue(instrument_data.get('distance_accuracy_a', 1.0))
        distance_layout.addRow("Постоянная (a):", self.distance_accuracy_a_spin)
        
        self.distance_accuracy_b_spin = QDoubleSpinBox()
        self.distance_accuracy_b_spin.setRange(0.0, 10.0)
        self.distance_accuracy_b_spin.setValue(1.0)
        self.distance_accuracy_b_spin.setSuffix(" ppm")
        self.distance_accuracy_b_spin.setDecimals(1)
        if instrument_data:
            self.distance_accuracy_b_spin.setValue(instrument_data.get('distance_accuracy_b', 1.0))
        distance_layout.addRow("Пропорциональная (b):", self.distance_accuracy_b_spin)
        
        self.distance_min_spin = QDoubleSpinBox()
        self.distance_min_spin.setRange(0.1, 50.0)
        self.distance_min_spin.setValue(1.5)
        self.distance_min_spin.setSuffix(" м")
        self.distance_min_spin.setDecimals(1)
        if instrument_data:
            self.distance_min_spin.setValue(instrument_data.get('distance_min', 1.5))
        distance_layout.addRow("Мин. расстояние:", self.distance_min_spin)
        
        self.distance_max_spin = QDoubleSpinBox()
        self.distance_max_spin.setRange(100.0, 10000.0)
        self.distance_max_spin.setValue(3000.0)
        self.distance_max_spin.setSuffix(" м")
        self.distance_max_spin.setDecimals(0)
        if instrument_data:
            self.distance_max_spin.setValue(instrument_data.get('distance_max', 3000.0))
        distance_layout.addRow("Макс. расстояние:", self.distance_max_spin)
        
        layout.addRow(distance_group)
        
        # Группа нивелирных измерений
        leveling_group = QGroupBox("Нивелирные измерения")
        leveling_layout = QFormLayout(leveling_group)
        
        self.leveling_accuracy_spin = QDoubleSpinBox()
        self.leveling_accuracy_spin.setRange(0.1, 10.0)
        self.leveling_accuracy_spin.setValue(0.8)
        self.leveling_accuracy_spin.setSuffix(" мм/станц")
        self.leveling_accuracy_spin.setDecimals(1)
        if instrument_data:
            self.leveling_accuracy_spin.setValue(instrument_data.get('leveling_accuracy', 0.8))
        leveling_layout.addRow("СКО нивелир.:", self.leveling_accuracy_spin)
        
        self.max_sight_distance_spin = QDoubleSpinBox()
        self.max_sight_distance_spin.setRange(10.0, 150.0)
        self.max_sight_distance_spin.setValue(100.0)
        self.max_sight_distance_spin.setSuffix(" м")
        self.max_sight_distance_spin.setDecimals(0)
        if instrument_data:
            self.max_sight_distance_spin.setValue(instrument_data.get('max_sight_distance', 100.0))
        leveling_layout.addRow("Макс. длина визир.:", self.max_sight_distance_spin)
        
        self.double_run_error_spin = QDoubleSpinBox()
        self.double_run_error_spin.setRange(0.1, 10.0)
        self.double_run_error_spin.setValue(2.0)
        self.double_run_error_spin.setSuffix(" мм/км")
        self.double_run_error_spin.setDecimals(1)
        if instrument_data:
            self.double_run_error_spin.setValue(instrument_data.get('double_run_error_per_km', 2.0))
        leveling_layout.addRow("Ошибка двойного хода:", self.double_run_error_spin)
        
        layout.addRow(leveling_group)
        
        # Группа ошибок центрирования
        centering_group = QGroupBox("Ошибки центрирования")
        centering_layout = QFormLayout(centering_group)
        
        self.centering_error_spin = QDoubleSpinBox()
        self.centering_error_spin.setRange(0.1, 10.0)
        self.centering_error_spin.setValue(2.0)
        self.centering_error_spin.setSuffix(" мм")
        self.centering_error_spin.setDecimals(1)
        if instrument_data:
            self.centering_error_spin.setValue(instrument_data.get('centering_error', 2.0))
        centering_layout.addRow("Ошибка центрирования:", self.centering_error_spin)
        
        self.target_centering_error_spin = QDoubleSpinBox()
        self.target_centering_error_spin.setRange(0.1, 10.0)
        self.target_centering_error_spin.setValue(2.0)
        self.target_centering_error_spin.setSuffix(" мм")
        self.target_centering_error_spin.setDecimals(1)
        if instrument_data:
            self.target_centering_error_spin.setValue(instrument_data.get('target_centering_error', 2.0))
        centering_layout.addRow("Ошибка центрир. цели:", self.target_centering_error_spin)
        
        layout.addRow(centering_group)
        
        # Примечание
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        if instrument_data:
            self.notes_edit.setPlainText(instrument_data.get('notes', ''))
        layout.addRow("Примечание:", self.notes_edit)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_instrument_data(self):
        """Получение данных прибора"""
        return {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'manufacturer': self.manufacturer_combo.currentText().strip(),
            'model': self.model_edit.text().strip(),
            'serial_number': self.serial_edit.text().strip(),
            'angular_accuracy': self.angular_accuracy_spin.value(),
            'angular_repeatability': self.angular_repeatability_spin.value(),
            'compensator_accuracy': self.compensator_accuracy_spin.value(),
            'distance_accuracy_a': self.distance_accuracy_a_spin.value(),
            'distance_accuracy_b': self.distance_accuracy_b_spin.value(),
            'distance_min': self.distance_min_spin.value(),
            'distance_max': self.distance_max_spin.value(),
            'leveling_accuracy': self.leveling_accuracy_spin.value(),
            'max_sight_distance': self.max_sight_distance_spin.value(),
            'double_run_error_per_km': self.double_run_error_spin.value(),
            'centering_error': self.centering_error_spin.value(),
            'target_centering_error': self.target_centering_error_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }


class ProjectPropertiesDialog(QDialog):
    """Диалог свойств проекта"""
    
    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Свойства проекта")
        self.resize(950, 750)
        
        self._init_ui()
        self._load_project_data()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создание древовидной навигации
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - навигация
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setMaximumWidth(300)
        self.nav_tree.itemClicked.connect(self._on_nav_item_clicked)
        
        # Правая панель - содержимое
        self.content_stack = QStackedWidget()
        
        splitter.addWidget(self.nav_tree)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([300, 650])
        
        layout.addWidget(splitter)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_changes)
        
        layout.addWidget(button_box)
        
        # Создание страниц
        self._create_navigation_tree()
        self._create_pages()
    
    def _create_navigation_tree(self):
        """Создание дерева навигации"""
        # 1. Карточка проекта
        project_card = QTreeWidgetItem(["1. Карточка проекта"])
        self.nav_tree.addTopLevelItem(project_card)
        
        general_info = QTreeWidgetItem(["Общие сведения"])
        project_card.addChild(general_info)
        
        responsible = QTreeWidgetItem(["Ответственные лица"])
        project_card.addChild(responsible)
        
        notes = QTreeWidgetItem(["Примечания"])
        project_card.addChild(notes)
        
        # 2. Система координат
        crs_item = QTreeWidgetItem(["2. Система координат"])
        self.nav_tree.addTopLevelItem(crs_item)
        
        base_crs = QTreeWidgetItem(["Базовая геодезическая система"])
        crs_item.addChild(base_crs)
        
        projection = QTreeWidgetItem(["Проекция на плоскость"])
        crs_item.addChild(projection)
        
        height_system = QTreeWidgetItem(["Система высот"])
        crs_item.addChild(height_system)
        
        # 3. Инструменты (библиотека приборов)
        instruments = QTreeWidgetItem(["3. Инструменты"])
        self.nav_tree.addTopLevelItem(instruments)
        
        instruments_list = QTreeWidgetItem(["Список приборов"])
        instruments.addChild(instruments_list)
        
        # 4. Классы точности
        classes = QTreeWidgetItem(["4. Классы точности"])
        self.nav_tree.addTopLevelItem(classes)
        
        normative_classes = QTreeWidgetItem(["Нормативные классы"])
        classes.addChild(normative_classes)
        
        # 5. Предобработка
        preprocessing = QTreeWidgetItem(["5. Предобработка"])
        self.nav_tree.addTopLevelItem(preprocessing)
        
        corrections = QTreeWidgetItem(["Поправки"])
        preprocessing.addChild(corrections)
        
        tolerances = QTreeWidgetItem(["Допуски"])
        preprocessing.addChild(tolerances)
        
        # 6. Уравнивание
        adjustment = QTreeWidgetItem(["6. Уравнивание"])
        self.nav_tree.addTopLevelItem(adjustment)
        
        method = QTreeWidgetItem(["Метод уравнивания"])
        adjustment.addChild(method)
        
        iterations = QTreeWidgetItem(["Итерационный процесс"])
        adjustment.addChild(iterations)
        
        # 7. Поиск ошибок
        error_search = QTreeWidgetItem(["7. Поиск ошибок"])
        self.nav_tree.addTopLevelItem(error_search)
        
        # 8. Отчётность
        reporting = QTreeWidgetItem(["8. Отчётность"])
        self.nav_tree.addTopLevelItem(reporting)
        
        # Развернуть все элементы
        self.nav_tree.expandAll()
    
    def _create_pages(self):
        """Создание страниц настроек"""
        
        # Страница "Общие сведения"
        general_page = self._create_general_page()
        self.content_stack.addWidget(general_page)
        
        # Страница "Ответственные лица"
        responsible_page = self._create_responsible_page()
        self.content_stack.addWidget(responsible_page)
        
        # Страница "Примечания"
        notes_page = self._create_notes_page()
        self.content_stack.addWidget(notes_page)
        
        # Страница "Базовая геодезическая система"
        crs_page = self._create_crs_page()
        self.content_stack.addWidget(crs_page)
        
        # Страница "Проекция на плоскость"
        projection_page = self._create_projection_page()
        self.content_stack.addWidget(projection_page)
        
        # Страница "Система высот"
        height_page = self._create_height_page()
        self.content_stack.addWidget(height_page)
        
        # Страница "Список приборов"
        instruments_page = self._create_instruments_page()
        self.content_stack.addWidget(instruments_page)
        
        # Страница "Нормативные классы"
        norm_classes_page = self._create_norm_classes_page()
        self.content_stack.addWidget(norm_classes_page)
        
        # Страница "Поправки"
        corrections_page = self._create_corrections_page()
        self.content_stack.addWidget(corrections_page)
        
        # Страница "Допуски"
        tolerances_page = self._create_tolerances_page()
        self.content_stack.addWidget(tolerances_page)
        
        # Страница "Метод уравнивания"
        method_page = self._create_method_page()
        self.content_stack.addWidget(method_page)
        
        # Страница "Итерационный процесс"
        iterations_page = self._create_iterations_page()
        self.content_stack.addWidget(iterations_page)
        
        # Страница "Поиск ошибок"
        error_page = self._create_error_page()
        self.content_stack.addWidget(error_page)
        
        # Страница "Отчётность"
        reporting_page = self._create_reporting_page()
        self.content_stack.addWidget(reporting_page)
    
    def _create_general_page(self) -> QWidget:
        """Создание страницы общих сведений"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.name_edit = QLineEdit()
        layout.addRow("Наименование проекта:", self.name_edit)
        
        self.org_edit = QLineEdit()
        layout.addRow("Организация:", self.org_edit)
        
        self.author_edit = QLineEdit()
        layout.addRow("Исполнитель:", self.author_edit)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        layout.addRow("Описание:", self.desc_edit)
        
        return page
    
    def _create_responsible_page(self) -> QWidget:
        """Создание страницы ответственных лиц"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.chief_engineer_edit = QLineEdit()
        layout.addRow("Главный инженер:", self.chief_engineer_edit)
        
        self.surveyor_edit = QLineEdit()
        layout.addRow("Геодезист:", self.surveyor_edit)
        
        self.processor_edit = QLineEdit()
        layout.addRow("Обработчик:", self.processor_edit)
        
        return page
    
    def _create_notes_page(self) -> QWidget:
        """Создание страницы примечаний"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Введите дополнительные примечания к проекту...")
        layout.addWidget(self.notes_edit)
        
        return page
    
    def _create_crs_page(self) -> QWidget:
        """Создание страницы базовой геодезической системы"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.crs_combo = QComboBox()
        self.crs_combo.addItems([
            "СК-42",
            "СК-95", 
            "ГСК-2011",
            "МСК (местная система координат)",
            "WGS-84"
        ])
        layout.addRow("Система координат:", self.crs_combo)
        
        self.zone_spin = QSpinBox()
        self.zone_spin.setRange(1, 60)
        self.zone_spin.setValue(7)
        layout.addRow("Номер зоны:", self.zone_spin)
        
        self.central_meridian_edit = QLineEdit()
        self.central_meridian_edit.setText("39.0")
        layout.addRow("Осевой меридиан:", self.central_meridian_edit)
        
        return page
    
    def _create_projection_page(self) -> QWidget:
        """Создание страницы проекции"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.scale_factor_spin = QDoubleSpinBox()
        self.scale_factor_spin.setRange(0.9, 1.1)
        self.scale_factor_spin.setValue(1.0)
        self.scale_factor_spin.setDecimals(6)
        layout.addRow("Масштабный коэффициент:", self.scale_factor_spin)
        
        self.false_easting_spin = QDoubleSpinBox()
        self.false_easting_spin.setRange(0, 10000000)
        self.false_easting_spin.setValue(7500000.0)
        layout.addRow("Ложное направление на восток:", self.false_easting_spin)
        
        return page
    
    def _create_height_page(self) -> QWidget:
        """Создание страницы системы высот"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.height_system_combo = QComboBox()
        self.height_system_combo.addItems([
            "Балтийская система высот (БСВ)",
            "Кронштадтский футшток",
            "Геодезические высоты",
            "Нормальные высоты"
        ])
        layout.addRow("Система высот:", self.height_system_combo)
        
        return page
    
    def _create_instruments_page(self) -> QWidget:
        """Создание страницы списка приборов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Таблица приборов
        self.instruments_table = QTreeWidget()
        self.instruments_table.setHeaderLabels([
            "Название", "Тип", "Производитель", 
            "СКО угла", "СКО расст.", "СКО нивел."
        ])
        layout.addWidget(self.instruments_table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._add_instrument)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self._edit_instrument)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(self._remove_instrument)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return page
    
    def _create_norm_classes_page(self) -> QWidget:
        """Создание страницы нормативных классов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Группа полигонометрии
        polygon_group = QGroupBox("Полигонометрия")
        polygon_layout = QFormLayout(polygon_group)
        
        self.polygon_class_combo = QComboBox()
        self.polygon_class_combo.addItems(["1 класс", "2 класс", "3 класс", "4 класс"])
        self.polygon_class_combo.setCurrentIndex(3)  # 4 класс по умолчанию
        polygon_layout.addRow("Класс:", self.polygon_class_combo)
        
        layout.addWidget(polygon_group)
        
        # Группа нивелирования
        leveling_group = QGroupBox("Нивелирование")
        leveling_layout = QFormLayout(leveling_group)
        
        self.leveling_class_combo = QComboBox()
        self.leveling_class_combo.addItems(["I класс", "II класс", "III класс", "IV класс"])
        self.leveling_class_combo.setCurrentIndex(2)  # III класс по умолчанию
        leveling_layout.addRow("Класс:", self.leveling_class_combo)
        
        layout.addWidget(leveling_group)
        
        layout.addStretch()
        
        return page
    
    def _create_corrections_page(self) -> QWidget:
        """Создание страницы поправок"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Группа поправок
        corrections_group = QGroupBox("Применяемые поправки")
        corrections_layout = QVBoxLayout(corrections_group)
        
        self.curvature_check = QCheckBox("Поправка за кривизну Земли")
        self.curvature_check.setChecked(True)
        corrections_layout.addWidget(self.curvature_check)
        
        self.refraction_check = QCheckBox("Поправка за рефракцию")
        self.refraction_check.setChecked(True)
        corrections_layout.addWidget(self.refraction_check)
        
        self.elevation_check = QCheckBox("Поправка за высоту над эллипсоидом")
        self.elevation_check.setChecked(False)
        corrections_layout.addWidget(self.elevation_check)
        
        self.gauge_check = QCheckBox("Поправка за приведение к центру")
        self.gauge_check.setChecked(True)
        corrections_layout.addWidget(self.gauge_check)
        
        self.atmospheric_check = QCheckBox("Атмосферная поправка")
        self.atmospheric_check.setChecked(True)
        corrections_layout.addWidget(self.atmospheric_check)
        
        layout.addWidget(corrections_group)
        
        # Группа параметров атмосферы
        atmosphere_group = QGroupBox("Параметры атмосферы")
        atmosphere_layout = QFormLayout(atmosphere_group)
        
        self.refraction_coeff_spin = QDoubleSpinBox()
        self.refraction_coeff_spin.setRange(0.10, 0.20)
        self.refraction_coeff_spin.setValue(0.14)
        self.refraction_coeff_spin.setDecimals(2)
        atmosphere_layout.addRow("Коэффициент рефракции:", self.refraction_coeff_spin)
        
        self.earth_radius_spin = QDoubleSpinBox()
        self.earth_radius_spin.setRange(6370000, 6380000)
        self.earth_radius_spin.setValue(6371000)
        self.earth_radius_spin.setSuffix(" м")
        self.earth_radius_spin.setDecimals(0)
        atmosphere_layout.addRow("Радиус Земли:", self.earth_radius_spin)
        
        layout.addWidget(atmosphere_group)
        
        layout.addStretch()
        
        return page
    
    def _create_tolerances_page(self) -> QWidget:
        """Создание страницы допусков"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.max_angle_tolerance_spin = QDoubleSpinBox()
        self.max_angle_tolerance_spin.setRange(0.1, 60.0)
        self.max_angle_tolerance_spin.setValue(5.0)
        self.max_angle_tolerance_spin.setSuffix("″")
        layout.addRow("Макс. расходимость углов:", self.max_angle_tolerance_spin)
        
        self.max_relative_tolerance_edit = QLineEdit("1/25000")
        layout.addRow("Макс. относительная невязка:", self.max_relative_tolerance_edit)
        
        self.coordinate_tolerance_spin = QDoubleSpinBox()
        self.coordinate_tolerance_spin.setRange(0.001, 1.0)
        self.coordinate_tolerance_spin.setValue(0.01)
        self.coordinate_tolerance_spin.setSuffix(" м")
        self.coordinate_tolerance_spin.setDecimals(3)
        layout.addRow("Допуск координат:", self.coordinate_tolerance_spin)
        
        return page
    
    def _create_method_page(self) -> QWidget:
        """Создание страницы метода уравнивания"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "Классический МНК",
            "Робастное уравнивание (Хубер)",
            "Робастное уравнивание (датчанин)",
            "Метод наименьших модулей"
        ])
        layout.addRow("Метод уравнивания:", self.method_combo)
        
        self.priori_weights_check = QCheckBox("Использовать априорные веса")
        self.priori_weights_check.setChecked(True)
        layout.addRow("", self.priori_weights_check)
        
        return page
    
    def _create_iterations_page(self) -> QWidget:
        """Создание страницы итерационного процесса"""
        page = QWidget()
        layout = QFormLayout(page)
        
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(1, 100)
        self.max_iterations_spin.setValue(10)
        layout.addRow("Макс. количество итераций:", self.max_iterations_spin)
        
        self.convergence_threshold_spin = QDoubleSpinBox()
        self.convergence_threshold_spin.setRange(0.0001, 1.0)
        self.convergence_threshold_spin.setValue(0.001)
        self.convergence_threshold_spin.setDecimals(6)
        layout.addRow("Порог сходимости:", self.convergence_threshold_spin)
        
        return page
    
    def _create_error_page(self) -> QWidget:
        """Создание страницы поиска ошибок"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Группа параметров поиска
        search_group = QGroupBox("Параметры поиска грубых ошибок")
        search_layout = QFormLayout(search_group)
        
        self.sigma_threshold_spin = QDoubleSpinBox()
        self.sigma_threshold_spin.setRange(1.0, 10.0)
        self.sigma_threshold_spin.setValue(3.0)
        self.sigma_threshold_spin.setSingleStep(0.5)
        search_layout.addRow("Порог σ для отбраковки:", self.sigma_threshold_spin)
        
        self.baarda_test_check = QCheckBox("Использовать тест Баарда")
        self.baarda_test_check.setChecked(True)
        search_layout.addRow("", self.baarda_test_check)
        
        layout.addWidget(search_group)
        layout.addStretch()
        
        return page
    
    def _create_reporting_page(self) -> QWidget:
        """Создание страницы отчётности"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Группа форматов отчётов
        formats_group = QGroupBox("Форматы отчётов")
        formats_layout = QVBoxLayout(formats_group)
        
        self.gost_check = QCheckBox("ГОСТ 7.32-2017")
        self.gost_check.setChecked(True)
        formats_layout.addWidget(self.gost_check)
        
        self.pdf_check = QCheckBox("PDF")
        self.pdf_check.setChecked(True)
        formats_layout.addWidget(self.pdf_check)
        
        self.docx_check = QCheckBox("DOCX")
        self.docx_check.setChecked(False)
        formats_layout.addWidget(self.docx_check)
        
        self.html_check = QCheckBox("HTML")
        self.html_check.setChecked(False)
        formats_layout.addWidget(self.html_check)
        
        layout.addWidget(formats_group)
        layout.addStretch()
        
        return page
    
    def _on_nav_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработчик клика по элементу навигации"""
        # Определение индекса страницы на основе пути в дереве
        path = []
        current = item
        while current:
            parent = current.parent()
            if parent is None:
                break
            index = parent.indexOfChild(current)
            path.insert(0, index)
            current = parent
        
        # Простое сопоставление для примера
        page_index = sum(path)
        if page_index < self.content_stack.count():
            self.content_stack.setCurrentIndex(page_index)
    
    def _load_project_data(self):
        """Загрузка данных проекта в диалог"""
        if self.project is None:
            return
        
        # Загрузка метаданных из project_card
        project_card = self.project.settings.get('project_card', {})
        self.name_edit.setText(project_card.get('name', self.project.name))
        self.org_edit.setText(project_card.get('organization', ''))
        self.author_edit.setText(project_card.get('author', ''))
        self.desc_edit.setPlainText(project_card.get('description', ''))
        
        # Загрузка настроек СК
        crs_settings = self.project.settings.get('crs', {})
        if crs_settings:
            # Установка базовой СК
            base_crs = crs_settings.get('base_crs', 'SK42')
            crs_map = {
                'SK42': 0,  # СК-42
                'SK95': 1,  # СК-95
                'GSK2011': 2,  # ГСК-2011
                'MSK': 3,  # МСК
                'WGS84': 4  # WGS-84
            }
            self.crs_combo.setCurrentIndex(crs_map.get(base_crs, 0))
            
            self.zone_spin.setValue(crs_settings.get("zone", 7))
            self.central_meridian_edit.setText(str(crs_settings.get("central_meridian", 39.0)))
            self.false_easting_spin.setValue(crs_settings.get("false_easting", 7500000.0))
            self.scale_factor_spin.setValue(crs_settings.get("scale_factor", 1.0))
        
        # Загрузка инструментов
        instruments_settings = self.project.settings.get('instruments', {})
        if instruments_settings and "instruments" in instruments_settings:
            for instr in instruments_settings["instruments"]:
                item = QTreeWidgetItem([
                    instr.get("name", ""),
                    instr.get("type", ""),
                    instr.get("manufacturer", ""),
                    f"{instr.get('angular_accuracy', 0)}\"",
                    f"{instr.get('distance_accuracy_a', 0)}+{instr.get('distance_accuracy_b', 0)}ppm",
                    f"{instr.get('leveling_accuracy', 0)}мм/ст"
                ])
                self.instruments_table.addTopLevelItem(item)
        
        # Загрузка допусков
        tolerances = self.project.settings.get('tolerances', {})
        if tolerances:
            self.max_angle_tolerance_spin.setValue(tolerances.get('angle_tolerance', 5.0))
            rel_tol = tolerances.get('distance_relative_tolerance', 1e-5)
            self.max_relative_tolerance_edit.setText(f"1/{int(1/rel_tol)}")
            self.coordinate_tolerance_spin.setValue(tolerances.get('coordinate_tolerance', 0.01))
        
        # Загрузка параметров уравнивания
        adjustment = self.project.settings.get('adjustment', {})
        if adjustment:
            method_map = {
                'classic': 0,
                'huber': 1,
                'danish': 2,
                'l1': 3
            }
            self.method_combo.setCurrentIndex(method_map.get(adjustment.get('method', 'classic'), 0))
            self.priori_weights_check.setChecked(adjustment.get('priori_weights', True))
            self.max_iterations_spin.setValue(adjustment.get('max_iterations', 10))
            self.convergence_threshold_spin.setValue(adjustment.get('convergence_threshold', 0.001))
        
        # Загрузка параметров предобработки
        preprocessing = self.project.settings.get('preprocessing', {})
        if preprocessing:
            self.curvature_check.setChecked(preprocessing.get('apply_curvature_correction', True))
            self.refraction_check.setChecked(preprocessing.get('apply_refraction_correction', True))
            self.atmospheric_check.setChecked(preprocessing.get('apply_atmospheric_correction', True))
            self.refraction_coeff_spin.setValue(preprocessing.get('refraction_coefficient', 0.14))
            self.earth_radius_spin.setValue(preprocessing.get('earth_radius', 6371000))
        
        # Загрузка параметров поиска ошибок
        error_search = self.project.settings.get('error_search', {})
        if error_search:
            self.sigma_threshold_spin.setValue(error_search.get('sigma_threshold', 3.0))
            self.baarda_test_check.setChecked(error_search.get('baarda_test', True))
    
    def _apply_changes(self):
        """Применение изменений"""
        if self.project is None:
            return
        
        # Сохранение карточки проекта
        project_card = {
            'name': self.name_edit.text(),
            'organization': self.org_edit.text(),
            'author': self.author_edit.text(),
            'description': self.desc_edit.toPlainText()
        }
        self.project.settings['project_card'] = project_card
        
        # Сохранение настроек СК
        crs_map = ['SK42', 'SK95', 'GSK2011', 'MSK', 'WGS84']
        crs_settings = {
            "base_crs": crs_map[self.crs_combo.currentIndex()],
            "zone": self.zone_spin.value(),
            "central_meridian": float(self.central_meridian_edit.text() or 39.0),
            "false_easting": self.false_easting_spin.value(),
            "scale_factor": self.scale_factor_spin.value(),
            "height_system": self.height_system_combo.currentText()
        }
        self.project.settings['crs'] = crs_settings
        
        # Сохранение допусков
        rel_tol_text = self.max_relative_tolerance_edit.text()
        try:
            if '/' in rel_tol_text:
                rel_tol = 1.0 / float(rel_tol_text.split('/')[1])
            else:
                rel_tol = float(rel_tol_text)
        except (ValueError, ZeroDivisionError):
            rel_tol = 1e-5
        
        tolerances = {
            'angle_tolerance': self.max_angle_tolerance_spin.value(),
            'distance_relative_tolerance': rel_tol,
            'coordinate_tolerance': self.coordinate_tolerance_spin.value()
        }
        self.project.settings['tolerances'] = tolerances
        
        # Сохранение параметров уравнивания
        method_map = ['classic', 'huber', 'danish', 'l1']
        adjustment = {
            'method': method_map[self.method_combo.currentIndex()],
            'priori_weights': self.priori_weights_check.isChecked(),
            'max_iterations': self.max_iterations_spin.value(),
            'convergence_threshold': self.convergence_threshold_spin.value()
        }
        self.project.settings['adjustment'] = adjustment
        
        # Сохранение параметров предобработки
        preprocessing = {
            'apply_curvature_correction': self.curvature_check.isChecked(),
            'apply_refraction_correction': self.refraction_check.isChecked(),
            'apply_atmospheric_correction': self.atmospheric_check.isChecked(),
            'apply_elevation_correction': self.elevation_check.isChecked(),
            'apply_centering_correction': self.gauge_check.isChecked(),
            'refraction_coefficient': self.refraction_coeff_spin.value(),
            'earth_radius': self.earth_radius_spin.value()
        }
        self.project.settings['preprocessing'] = preprocessing
        
        # Сохранение параметров поиска ошибок
        error_search = {
            'sigma_threshold': self.sigma_threshold_spin.value(),
            'baarda_test': self.baarda_test_check.isChecked()
        }
        self.project.settings['error_search'] = error_search
        
        # Сохранение проекта на диск
        self.project.save()
        
        logger.info("Настройки проекта применены")
    
    def accept(self):
        """Подтверждение изменений"""
        self._apply_changes()
        super().accept()
    
    # Обработчики кнопок управления приборами
    def _add_instrument(self):
        """Добавление прибора"""
        logger.info("Добавление прибора")
        dialog = InstrumentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            instr_data = dialog.get_instrument_data()
            item = QTreeWidgetItem([
                instr_data['name'],
                instr_data['type'],
                instr_data['manufacturer'],
                f"{instr_data['angular_accuracy']}\"",
                f"{instr_data['distance_accuracy_a']}+{instr_data['distance_accuracy_b']}ppm",
                f"{instr_data['leveling_accuracy']}мм/ст"
            ])
            self.instruments_table.addTopLevelItem(item)
            
            # Сохранение в настройки проекта
            if 'instruments' not in self.project.settings:
                self.project.settings['instruments'] = {'instruments': []}
            self.project.settings['instruments']['instruments'].append(instr_data)
    
    def _edit_instrument(self):
        """Редактирование прибора"""
        logger.info("Редактирование прибора")
        selected = self.instruments_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Информация", "Выберите прибор для редактирования")
            return
        
        item = self.instruments_table.currentItem()
        if item:
            # Получение данных из строки
            instr_data = {
                'name': item.text(0),
                'type': item.text(1),
                'manufacturer': item.text(2),
                'angular_accuracy': float(item.text(3).replace('"', '')),
                'distance_accuracy_a': float(item.text(4).split('+')[0]),
                'distance_accuracy_b': float(item.text(4).split('+')[1].replace('ppm', '')),
                'leveling_accuracy': float(item.text(5).replace('мм/ст', ''))
            }
            
            dialog = InstrumentDialog(self, instr_data)
            if dialog.exec_() == QDialog.Accepted:
                updated_data = dialog.get_instrument_data()
                item.setText(0, updated_data['name'])
                item.setText(1, updated_data['type'])
                item.setText(2, updated_data['manufacturer'])
                item.setText(3, f"{updated_data['angular_accuracy']}\"")
                item.setText(4, f"{updated_data['distance_accuracy_a']}+{updated_data['distance_accuracy_b']}ppm")
                item.setText(5, f"{updated_data['leveling_accuracy']}мм/ст")
    
    def _remove_instrument(self):
        """Удаление прибора"""
        logger.info("Удаление прибора")
        selected = self.instruments_table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Информация", "Выберите прибор для удаления")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение", 
            "Удалить выбранный прибор?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected:
                index = self.instruments_table.indexOfTopLevelItem(item)
                self.instruments_table.takeTopLevelItem(index)
