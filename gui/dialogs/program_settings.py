"""
GeoAdjust Pro - Диалог параметров программы
"""

from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QLabel,
    QDialogButtonBox, QCheckBox, QPushButton, QColorDialog, QFontComboBox,
    QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont


class ProgramSettingsDialog(QDialog):
    """Диалог параметров программы"""
    
    settings_changed = pyqtSignal(dict)  # Сигнал изменения настроек
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры программы")
        self.resize(750, 550)
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создание вкладок
        tab_widget = QTabWidget()
        
        # Вкладка "Общие настройки"
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "Общие")
        
        # Вкладка "Схема"
        scheme_tab = self._create_scheme_tab()
        tab_widget.addTab(scheme_tab, "Схема")
        
        # Вкладка "Таблицы"
        tables_tab = self._create_tables_tab()
        tab_widget.addTab(tables_tab, "Таблицы")
        
        # Вкладка "Цвета"
        colors_tab = self._create_colors_tab()
        tab_widget.addTab(colors_tab, "Цвета")
        
        layout.addWidget(tab_widget)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Создание вкладки общих настроек"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        # Язык интерфейса
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Русский", "English"])
        layout.addRow("Язык интерфейса:", self.language_combo)
        
        # Тип интерфейса
        self.interface_type_combo = QComboBox()
        self.interface_type_combo.addItems(["Ленточный", "Классический"])
        layout.addRow("Тип интерфейса:", self.interface_type_combo)
        
        # Тема
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Системная"])
        layout.addRow("Тема:", self.theme_combo)
        
        layout.addRow(QLabel(""))  # Пустая строка
        
        # Группа автосохранения
        autosave_group = QGroupBox("Автосохранение")
        autosave_layout = QFormLayout(autosave_group)
        
        self.autosave_check = QCheckBox("Включить автосохранение")
        self.autosave_check.setChecked(True)
        autosave_layout.addRow("", self.autosave_check)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(" минут")
        autosave_layout.addRow("Интервал автосохранения:", self.autosave_interval_spin)
        
        layout.addRow(autosave_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_scheme_tab(self) -> QWidget:
        """Создание вкладки настроек схемы"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        # Пункты ПВО
        points_group = QGroupBox("Пункты ПВО")
        points_layout = QFormLayout(points_group)
        
        self.point_color_btn = QPushButton("Выбрать цвет")
        self.point_color_btn.setStyleSheet("background-color: red; min-height: 25px;")
        self.point_color_btn.clicked.connect(lambda: self._choose_color(self.point_color_btn, Qt.red))
        points_layout.addRow("Цвет пунктов:", self.point_color_btn)
        
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 20)
        self.point_size_spin.setValue(8)
        self.point_size_spin.setSuffix(" px")
        points_layout.addRow("Размер пунктов:", self.point_size_spin)
        
        self.point_shape_combo = QComboBox()
        self.point_shape_combo.addItems(["Круг", "Квадрат", "Треугольник", "Ромб"])
        points_layout.addRow("Форма:", self.point_shape_combo)
        
        layout.addRow(points_group)
        
        # Эллипсы ошибок
        ellipse_group = QGroupBox("Эллипсы ошибок")
        ellipse_layout = QFormLayout(ellipse_group)
        
        self.ellipse_color_btn = QPushButton("Выбрать цвет")
        self.ellipse_color_btn.setStyleSheet("background-color: blue; min-height: 25px;")
        self.ellipse_color_btn.clicked.connect(lambda: self._choose_color(self.ellipse_color_btn, Qt.blue))
        ellipse_layout.addRow("Цвет эллипсов:", self.ellipse_color_btn)
        
        self.ellipse_opacity_spin = QDoubleSpinBox()
        self.ellipse_opacity_spin.setRange(0.1, 1.0)
        self.ellipse_opacity_spin.setValue(0.5)
        self.ellipse_opacity_spin.setSingleStep(0.1)
        ellipse_layout.addRow("Прозрачность заливки:", self.ellipse_opacity_spin)
        
        self.ellipse_scale_spin = QDoubleSpinBox()
        self.ellipse_scale_spin.setRange(0.5, 3.0)
        self.ellipse_scale_spin.setValue(1.0)
        self.ellipse_scale_spin.setSuffix(" σ")
        ellipse_layout.addRow("Масштаб эллипсов:", self.ellipse_scale_spin)
        
        layout.addRow(ellipse_group)
        
        # Измерения
        observations_group = QGroupBox("Измерения")
        observations_layout = QFormLayout(observations_group)
        
        self.observation_color_btn = QPushButton("Выбрать цвет")
        self.observation_color_btn.setStyleSheet("background-color: #0000FF; min-height: 25px;")
        self.observation_color_btn.clicked.connect(lambda: self._choose_color(self.observation_color_btn, QColor(0, 0, 255)))
        observations_layout.addRow("Цвет линий:", self.observation_color_btn)
        
        self.observation_width_spin = QSpinBox()
        self.observation_width_spin.setRange(1, 5)
        self.observation_width_spin.setValue(1)
        observations_layout.addRow("Толщина линий:", self.observation_width_spin)
        
        layout.addRow(observations_group)
        
        return tab
    
    def _create_tables_tab(self) -> QWidget:
        """Создание вкладки настроек таблиц"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        # Шрифт таблиц
        font_group = QGroupBox("Шрифт таблиц")
        font_layout = QFormLayout(font_group)
        
        self.table_font_combo = QFontComboBox()
        self.table_font_combo.setCurrentFont(QFont("Segoe UI", 10))
        font_layout.addRow("Семейство шрифтов:", self.table_font_combo)
        
        self.table_font_size_spin = QSpinBox()
        self.table_font_size_spin.setRange(8, 24)
        self.table_font_size_spin.setValue(10)
        font_layout.addRow("Размер шрифта:", self.table_font_size_spin)
        
        layout.addRow(font_group)
        
        # Отображение
        display_group = QGroupBox("Отображение")
        display_layout = QVBoxLayout(display_group)
        
        self.alternate_rows_check = QCheckBox("Чередовать цвет строк")
        self.alternate_rows_check.setChecked(True)
        display_layout.addWidget(self.alternate_rows_check)
        
        self.show_grid_check = QCheckBox("Показывать сетку таблицы")
        self.show_grid_check.setChecked(True)
        display_layout.addWidget(self.show_grid_check)
        
        self.highlight_selected_row_check = QCheckBox("Подсвечивать выбранную строку")
        self.highlight_selected_row_check.setChecked(True)
        display_layout.addWidget(self.highlight_selected_row_check)
        
        layout.addRow(display_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_colors_tab(self) -> QWidget:
        """Создание вкладки настроек цветов"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignRight)
        
        # Цвета интерфейса
        interface_group = QGroupBox("Цвета интерфейса")
        interface_layout = QFormLayout(interface_group)
        
        self.bg_color_btn = QPushButton("Фон")
        self.bg_color_btn.setStyleSheet("background-color: white; min-height: 25px;")
        self.bg_color_btn.clicked.connect(lambda: self._choose_color(self.bg_color_btn, Qt.white))
        interface_layout.addRow("Цвет фона:", self.bg_color_btn)
        
        self.text_color_btn = QPushButton("Текст")
        self.text_color_btn.setStyleSheet("background-color: black; min-height: 25px;")
        self.text_color_btn.clicked.connect(lambda: self._choose_color(self.text_color_btn, Qt.black))
        interface_layout.addRow("Цвет текста:", self.text_color_btn)
        
        self.selection_color_btn = QPushButton("Выделение")
        self.selection_color_btn.setStyleSheet("background-color: #0078D7; min-height: 25px;")
        self.selection_color_btn.clicked.connect(lambda: self._choose_color(self.selection_color_btn, QColor(0, 120, 215)))
        interface_layout.addRow("Цвет выделения:", self.selection_color_btn)
        
        self.grid_color_btn = QPushButton("Сетка")
        self.grid_color_btn.setStyleSheet("background-color: #DCDCDC; min-height: 25px;")
        self.grid_color_btn.clicked.connect(lambda: self._choose_color(self.grid_color_btn, QColor(220, 220, 220)))
        interface_layout.addRow("Цвет сетки:", self.grid_color_btn)
        
        layout.addRow(interface_group)
        
        # Цвета для различных типов объектов
        objects_group = QGroupBox("Цвета объектов")
        objects_layout = QFormLayout(objects_group)
        
        self.fixed_point_color_btn = QPushButton("Жёсткие пункты")
        self.fixed_point_color_btn.setStyleSheet("background-color: darkblue; min-height: 25px; color: white;")
        self.fixed_point_color_btn.clicked.connect(lambda: self._choose_color(self.fixed_point_color_btn, Qt.darkBlue))
        objects_layout.addRow("", self.fixed_point_color_btn)
        
        self.new_point_color_btn = QPushButton("Новые пункты")
        self.new_point_color_btn.setStyleSheet("background-color: red; min-height: 25px;")
        self.new_point_color_btn.clicked.connect(lambda: self._choose_color(self.new_point_color_btn, Qt.red))
        objects_layout.addRow("", self.new_point_color_btn)
        
        self.error_line_btn = QPushButton("Невязки")
        self.error_line_btn.setStyleSheet("background-color: magenta; min-height: 25px;")
        self.error_line_btn.clicked.connect(lambda: self._choose_color(self.error_line_btn, Qt.magenta))
        objects_layout.addRow("", self.error_line_btn)
        
        layout.addRow(objects_group)
        
        layout.addStretch()
        
        return tab
    
    def _choose_color(self, button: QPushButton, default_color):
        """Выбор цвета"""
        if isinstance(default_color, QColor):
            initial = default_color
        else:
            initial = QColor(default_color)
        
        color = QColorDialog.getColor(initial, self, "Выберите цвет")
        
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}; min-height: 25px;")
            if color.lightness() < 128:
                button.setStyleSheet(button.styleSheet() + " color: white;")
    
    def _load_settings(self):
        """Загрузка настроек из конфигурации"""
        # Загрузка из файла конфигурации или реестра
        # Пока используем значения по умолчанию
        pass
    
    def accept(self):
        """Подтверждение изменений"""
        # Сохранение настроек
        self._save_settings()
        super().accept()
    
    def _save_settings(self):
        """Сохранение настроек"""
        # Сохранение в файл конфигурации или реестр
        settings = {
            'language': self.language_combo.currentText(),
            'interface_type': self.interface_type_combo.currentText(),
            'theme': self.theme_combo.currentText(),
            'autosave_enabled': self.autosave_check.isChecked(),
            'autosave_interval': self.autosave_interval_spin.value(),
            'point_size': self.point_size_spin.value(),
            'table_font': self.table_font_combo.currentFont().family(),
            'table_font_size': self.table_font_size_spin.value(),
            'alternate_rows': self.alternate_rows_check.isChecked(),
            'show_grid': self.show_grid_check.isChecked(),
        }
        
        # Сохранение в файл конфигурации
        try:
            import json
            from pathlib import Path
            
            config_dir = Path.home() / ".geoadjust"
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / "program_settings.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass  # Игнорируем ошибки сохранения
        
        self.settings_changed.emit(settings)
    
    def get_settings(self) -> Dict[str, Any]:
        """Получение текущих настроек"""
        return {
            'language': self.language_combo.currentText(),
            'interface_type': self.interface_type_combo.currentText(),
            'theme': self.theme_combo.currentText(),
            'autosave': {
                'enabled': self.autosave_check.isChecked(),
                'interval_minutes': self.autosave_interval_spin.value()
            },
            'scheme': {
                'point_size': self.point_size_spin.value(),
                'point_color': self._get_button_color(self.point_color_btn),
                'ellipse_color': self._get_button_color(self.ellipse_color_btn),
                'ellipse_opacity': self.ellipse_opacity_spin.value(),
            },
            'tables': {
                'font_family': self.table_font_combo.currentFont().family(),
                'font_size': self.table_font_size_spin.value(),
                'alternate_rows': self.alternate_rows_check.isChecked(),
                'show_grid': self.show_grid_check.isChecked(),
            }
        }
    
    def _get_button_color(self, button: QPushButton) -> str:
        """Получение цвета кнопки"""
        style = button.styleSheet()
        if "background-color:" in style:
            start = style.find("background-color:") + len("background-color:")
            end = style.find(";", start)
            if end > start:
                return style[start:end].strip()
        return "#FFFFFF"
