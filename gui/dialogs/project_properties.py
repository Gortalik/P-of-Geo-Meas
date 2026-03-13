"""
GeoAdjust Pro - Диалог свойств проекта
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QWidget, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QLabel,
    QDialogButtonBox, QGroupBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class ProjectPropertiesDialog(QDialog):
    """Диалог свойств проекта"""
    
    properties_changed = pyqtSignal(dict)  # Сигнал изменения свойств
    
    def __init__(self, project: Any, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Свойства проекта")
        self.resize(900, 650)
        
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
        self.nav_tree.setMaximumWidth(280)
        self.nav_tree.itemClicked.connect(self._on_nav_item_clicked)
        
        # Правая панель - содержимое
        self.content_stack = QStackedWidget()
        
        splitter.addWidget(self.nav_tree)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([280, 620])
        
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
        self.nav_tree.clear()
        
        # 1. Карточка проекта
        project_card = QTreeWidgetItem(["1. Карточка проекта"])
        project_card.setData(0, Qt.UserRole, 0)
        self.nav_tree.addTopLevelItem(project_card)
        
        general_info = QTreeWidgetItem(["Общие сведения"])
        general_info.setData(0, Qt.UserRole, 0)
        project_card.addChild(general_info)
        
        responsible = QTreeWidgetItem(["Ответственные лица"])
        responsible.setData(0, Qt.UserRole, 1)
        project_card.addChild(responsible)
        
        notes = QTreeWidgetItem(["Примечания"])
        notes.setData(0, Qt.UserRole, 2)
        project_card.addChild(notes)
        
        # 2. Система координат
        crs_item = QTreeWidgetItem(["2. Система координат"])
        crs_item.setData(0, Qt.UserRole, 3)
        self.nav_tree.addTopLevelItem(crs_item)
        
        base_crs = QTreeWidgetItem(["Базовая геодезическая система"])
        base_crs.setData(0, Qt.UserRole, 4)
        crs_item.addChild(base_crs)
        
        projection = QTreeWidgetItem(["Проекция на плоскость"])
        projection.setData(0, Qt.UserRole, 5)
        crs_item.addChild(projection)
        
        transformations = QTreeWidgetItem(["Параметры преобразования"])
        transformations.setData(0, Qt.UserRole, 6)
        crs_item.addChild(transformations)
        
        height_system = QTreeWidgetItem(["Система высот"])
        height_system.setData(0, Qt.UserRole, 7)
        crs_item.addChild(height_system)
        
        # 3. Инструменты (библиотека приборов)
        instruments = QTreeWidgetItem(["3. Инструменты"])
        instruments.setData(0, Qt.UserRole, 8)
        self.nav_tree.addTopLevelItem(instruments)
        
        instruments_list = QTreeWidgetItem(["Список приборов"])
        instruments_list.setData(0, Qt.UserRole, 8)
        instruments.addChild(instruments_list)
        
        # 4. Классы точности
        classes = QTreeWidgetItem(["4. Классы точности"])
        classes.setData(0, Qt.UserRole, 9)
        self.nav_tree.addTopLevelItem(classes)
        
        normative_classes = QTreeWidgetItem(["Нормативные классы"])
        normative_classes.setData(0, Qt.UserRole, 9)
        classes.addChild(normative_classes)
        
        weight_classes = QTreeWidgetItem(["Весовые классы"])
        weight_classes.setData(0, Qt.UserRole, 10)
        classes.addChild(weight_classes)
        
        # 5. Предобработка
        preprocessing = QTreeWidgetItem(["5. Предобработка"])
        preprocessing.setData(0, Qt.UserRole, 11)
        self.nav_tree.addTopLevelItem(preprocessing)
        
        corrections = QTreeWidgetItem(["Поправки"])
        corrections.setData(0, Qt.UserRole, 11)
        preprocessing.addChild(corrections)
        
        tolerances = QTreeWidgetItem(["Допуски"])
        tolerances.setData(0, Qt.UserRole, 12)
        preprocessing.addChild(tolerances)
        
        # 6. Уравнивание
        adjustment = QTreeWidgetItem(["6. Уравнивание"])
        adjustment.setData(0, Qt.UserRole, 13)
        self.nav_tree.addTopLevelItem(adjustment)
        
        method = QTreeWidgetItem(["Метод уравнивания"])
        method.setData(0, Qt.UserRole, 13)
        adjustment.addChild(method)
        
        iterations = QTreeWidgetItem(["Итерационный процесс"])
        iterations.setData(0, Qt.UserRole, 14)
        adjustment.addChild(iterations)
        
        # Развернуть все элементы
        self.nav_tree.expandAll()
    
    def _create_pages(self):
        """Создание страниц настроек"""
        
        # Страница 0: Общие сведения
        general_page = self._create_general_info_page()
        self.content_stack.addWidget(general_page)
        
        # Страница 1: Ответственные лица
        responsible_page = self._create_responsible_page()
        self.content_stack.addWidget(responsible_page)
        
        # Страница 2: Примечания
        notes_page = self._create_notes_page()
        self.content_stack.addWidget(notes_page)
        
        # Страница 3: Базовая геодезическая система
        crs_page = self._create_base_crs_page()
        self.content_stack.addWidget(crs_page)
        
        # Страница 4: Проекция на плоскость
        projection_page = self._create_projection_page()
        self.content_stack.addWidget(projection_page)
        
        # Страница 5: Параметры преобразования
        transform_page = self._create_transformation_page()
        self.content_stack.addWidget(transform_page)
        
        # Страница 6: Система высот
        height_page = self._create_height_system_page()
        self.content_stack.addWidget(height_page)
        
        # Страница 7: Инструменты
        instruments_page = self._create_instruments_page()
        self.content_stack.addWidget(instruments_page)
        
        # Страница 8: Нормативные классы
        normative_page = self._create_normative_classes_page()
        self.content_stack.addWidget(normative_page)
        
        # Страница 9: Весовые классы
        weight_page = self._create_weight_classes_page()
        self.content_stack.addWidget(weight_page)
        
        # Страница 10: Поправки
        corrections_page = self._create_corrections_page()
        self.content_stack.addWidget(corrections_page)
        
        # Страница 11: Допуски
        tolerances_page = self._create_tolerances_page()
        self.content_stack.addWidget(tolerances_page)
        
        # Страница 12: Метод уравнивания
        method_page = self._create_adjustment_method_page()
        self.content_stack.addWidget(method_page)
        
        # Страница 13: Итерационный процесс
        iterations_page = self._create_iterations_page()
        self.content_stack.addWidget(iterations_page)
    
    def _create_general_info_page(self) -> QWidget:
        """Создание страницы общих сведений"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.name_edit = QLineEdit()
        layout.addRow("Наименование проекта:", self.name_edit)
        
        self.org_edit = QLineEdit()
        layout.addRow("Организация:", self.org_edit)
        
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["1:500", "1:1000", "1:2000", "1:5000", "1:10000"])
        layout.addRow("Масштаб:", self.scale_combo)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(120)
        layout.addRow("Описание:", self.desc_edit)
        
        return page
    
    def _create_responsible_page(self) -> QWidget:
        """Создание страницы ответственных лиц"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.author_edit = QLineEdit()
        layout.addRow("Исполнитель:", self.author_edit)
        
        self.checker_edit = QLineEdit()
        layout.addRow("Проверил:", self.checker_edit)
        
        self.approver_edit = QLineEdit()
        layout.addRow("Утвердил:", self.approver_edit)
        
        return page
    
    def _create_notes_page(self) -> QWidget:
        """Создание страницы примечаний"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Введите примечания к проекту...")
        layout.addWidget(self.notes_edit)
        
        return page
    
    def _create_base_crs_page(self) -> QWidget:
        """Создание страницы базовой СК"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.crs_combo = QComboBox()
        self.crs_combo.addItems([
            "СК-42",
            "СК-95",
            "ГСК-2011",
            "WGS-84",
            "МСК (местная система координат)"
        ])
        layout.addRow("Система координат:", self.crs_combo)
        
        self.zone_spin = QSpinBox()
        self.zone_spin.setRange(1, 60)
        self.zone_spin.setValue(7)
        layout.addRow("Номер зоны:", self.zone_spin)
        
        self.central_meridian_edit = QLineEdit("39.0")
        layout.addRow("Осевой меридиан:", self.central_meridian_edit)
        
        return page
    
    def _create_projection_page(self) -> QWidget:
        """Создание страницы проекции"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.false_easting_spin = QDoubleSpinBox()
        self.false_easting_spin.setRange(-1e8, 1e8)
        self.false_easting_spin.setValue(7500000.0)
        self.false_easting_spin.setDecimals(3)
        layout.addRow("Ложное направление X:", self.false_easting_spin)
        
        self.false_northing_spin = QDoubleSpinBox()
        self.false_northing_spin.setRange(-1e8, 1e8)
        self.false_northing_spin.setValue(0.0)
        self.false_northing_spin.setDecimals(3)
        layout.addRow("Ложное направление Y:", self.false_northing_spin)
        
        self.scale_factor_spin = QDoubleSpinBox()
        self.scale_factor_spin.setRange(0.5, 1.5)
        self.scale_factor_spin.setValue(1.0)
        self.scale_factor_spin.setDecimals(6)
        layout.addRow("Масштабный коэффициент:", self.scale_factor_spin)
        
        return page
    
    def _create_transformation_page(self) -> QWidget:
        """Создание страницы параметров преобразования"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.dx_spin = QDoubleSpinBox()
        self.dx_spin.setRange(-1000, 1000)
        self.dx_spin.setValue(0.0)
        self.dx_spin.setDecimals(4)
        layout.addRow("ΔX (м):", self.dx_spin)
        
        self.dy_spin = QDoubleSpinBox()
        self.dy_spin.setRange(-1000, 1000)
        self.dy_spin.setValue(0.0)
        self.dy_spin.setDecimals(4)
        layout.addRow("ΔY (м):", self.dy_spin)
        
        self.dz_spin = QDoubleSpinBox()
        self.dz_spin.setRange(-1000, 1000)
        self.dz_spin.setValue(0.0)
        self.dz_spin.setDecimals(4)
        layout.addRow("ΔZ (м):", self.dz_spin)
        
        return page
    
    def _create_height_system_page(self) -> QWidget:
        """Создание страницы системы высот"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.height_system_combo = QComboBox()
        self.height_system_combo.addItems([
            "Балтийская система высот (БСВ)",
            "Кронштадтский футшток",
            "Нормальная система высот",
            "Геодезическая высота"
        ])
        layout.addRow("Система высот:", self.height_system_combo)
        
        return page
    
    def _create_instruments_page(self) -> QWidget:
        """Создание страницы инструментов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group = QGroupBox("Библиотека приборов")
        group_layout = QVBoxLayout(group)
        
        self.instruments_list = QTreeWidget()
        self.instruments_list.setHeaderLabels(["Наименование", "Тип", "Точность углов", "Точность расстояний"])
        group_layout.addWidget(self.instruments_list)
        
        layout.addWidget(group)
        
        return page
    
    def _create_normative_classes_page(self) -> QWidget:
        """Создание страницы нормативных классов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group = QGroupBox("Нормативные классы точности")
        group_layout = QVBoxLayout(group)
        
        self.normative_classes_list = QTreeWidget()
        self.normative_classes_list.setHeaderLabels(["Наименование", "Тип", "σ угла", "Относительная невязка"])
        group_layout.addWidget(self.normative_classes_list)
        
        layout.addWidget(group)
        
        return page
    
    def _create_weight_classes_page(self) -> QWidget:
        """Создание страницы весовых классов"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        info_label = QLabel("Весовые классы используются для назначения весов измерениям при уравнивании.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        return page
    
    def _create_corrections_page(self) -> QWidget:
        """Создание страницы поправок"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group = QGroupBox("Применяемые поправки")
        group_layout = QVBoxLayout(group)
        
        self.correction_temp_check = QCheckBox("Поправка за температуру")
        self.correction_temp_check.setChecked(True)
        group_layout.addWidget(self.correction_temp_check)
        
        self.correction_pressure_check = QCheckBox("Поправка за давление")
        self.correction_pressure_check.setChecked(True)
        group_layout.addWidget(self.correction_pressure_check)
        
        self.correction_curvature_check = QCheckBox("Поправка за кривизну Земли и рефракцию")
        self.correction_curvature_check.setChecked(True)
        group_layout.addWidget(self.correction_curvature_check)
        
        self.correction_projection_check = QCheckBox("Поправка за приведение к плоскости проекции")
        self.correction_projection_check.setChecked(True)
        group_layout.addWidget(self.correction_projection_check)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return page
    
    def _create_tolerances_page(self) -> QWidget:
        """Создание страницы допусков"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.max_angle_residual_spin = QDoubleSpinBox()
        self.max_angle_residual_spin.setRange(0.1, 60.0)
        self.max_angle_residual_spin.setValue(10.0)
        self.max_angle_residual_spin.setSuffix("″")
        layout.addRow("Максимальная угловая невязка:", self.max_angle_residual_spin)
        
        self.max_distance_residual_spin = QDoubleSpinBox()
        self.max_distance_residual_spin.setRange(0.001, 1.0)
        self.max_distance_residual_spin.setValue(0.020)
        self.max_distance_residual_spin.setSuffix(" м")
        layout.addRow("Максимальная линейная невязка:", self.max_distance_residual_spin)
        
        return page
    
    def _create_adjustment_method_page(self) -> QWidget:
        """Создание страницы метода уравнивания"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.adjustment_method_combo = QComboBox()
        self.adjustment_method_combo.addItems([
            "Классический МНК",
            "Робастное уравнивание",
            "Поэтапное уравнивание"
        ])
        layout.addRow("Метод уравнивания:", self.adjustment_method_combo)
        
        self.use_weights_check = QCheckBox("Использовать веса измерений")
        self.use_weights_check.setChecked(True)
        layout.addRow("", self.use_weights_check)
        
        return page
    
    def _create_iterations_page(self) -> QWidget:
        """Создание страницы итерационного процесса"""
        page = QWidget()
        layout = QFormLayout(page)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(1, 100)
        self.max_iterations_spin.setValue(10)
        layout.addRow("Максимум итераций:", self.max_iterations_spin)
        
        self.convergence_spin = QDoubleSpinBox()
        self.convergence_spin.setRange(1e-10, 1e-2)
        self.convergence_spin.setValue(1e-6)
        self.convergence_spin.setDecimals(10)
        layout.addRow("Критерий сходимости:", self.convergence_spin)
        
        return page
    
    def _on_nav_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработчик клика по элементу навигации"""
        page_index = item.data(0, Qt.UserRole)
        if page_index >= 0:
            self.content_stack.setCurrentIndex(page_index)
    
    def _load_project_data(self):
        """Загрузка данных проекта в диалог"""
        if not self.project:
            return
        
        # Загрузка метаданных
        metadata = self.project.metadata
        self.name_edit.setText(metadata.name)
        self.org_edit.setText(metadata.organization)
        self.author_edit.setText(metadata.author)
        self.desc_edit.setText(metadata.description)
        
        # Загрузка настроек из файлов проекта
        self._load_settings_files()
    
    def _load_settings_files(self):
        """Загрузка настроек из файлов проекта"""
        try:
            import json
            from pathlib import Path
            
            settings_dir = self.project.project_path / "settings"
            
            # Загрузка настроек СК
            crs_file = settings_dir / "crs.json"
            if crs_file.exists():
                with open(crs_file, 'r', encoding='utf-8') as f:
                    crs_settings = json.load(f)
                    self.zone_spin.setValue(crs_settings.get('zone', 7))
                    self.central_meridian_edit.setText(str(crs_settings.get('central_meridian', 39.0)))
                    self.false_easting_spin.setValue(crs_settings.get('false_easting', 7500000.0))
        except Exception as e:
            pass  # Игнорируем ошибки загрузки
    
    def _apply_changes(self):
        """Применение изменений"""
        if not self.project:
            return
        
        # Сохранение метаданных
        self.project.metadata.name = self.name_edit.text()
        self.project.metadata.organization = self.org_edit.text()
        self.project.metadata.author = self.author_edit.text()
        self.project.metadata.description = self.desc_edit.toPlainText()
        self.project.metadata.modified = self.project.metadata.__class__.now()
        
        # Обновление XML-файла проекта
        self.project._create_project_xml()
        
        # Сохранение настроек СК
        self._save_crs_settings()
        
        self.properties_changed.emit({
            'name': self.project.metadata.name,
            'organization': self.project.metadata.organization
        })
    
    def _save_crs_settings(self):
        """Сохранение настроек системы координат"""
        try:
            import json
            from pathlib import Path
            
            settings_dir = self.project.project_path / "settings"
            settings_dir.mkdir(exist_ok=True)
            
            crs_settings = {
                "base_crs": self.crs_combo.currentText(),
                "zone": self.zone_spin.value(),
                "central_meridian": float(self.central_meridian_edit.text()),
                "false_easting": self.false_easting_spin.value(),
                "false_northing": self.false_northing_spin.value(),
                "scale_factor": self.scale_factor_spin.value()
            }
            
            with open(settings_dir / "crs.json", 'w', encoding='utf-8') as f:
                json.dump(crs_settings, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки СК: {e}")
    
    def accept(self):
        """Подтверждение изменений"""
        self._apply_changes()
        super().accept()
    
    def get_project_properties(self) -> Dict[str, Any]:
        """Получение свойств проекта"""
        return {
            'name': self.name_edit.text(),
            'organization': self.org_edit.text(),
            'author': self.author_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'scale': self.scale_combo.currentText(),
            'crs': self.crs_combo.currentText(),
            'zone': self.zone_spin.value(),
        }
