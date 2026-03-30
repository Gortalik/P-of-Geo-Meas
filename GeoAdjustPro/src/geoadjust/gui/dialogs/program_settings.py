"""
Диалог параметров программы GeoAdjust Pro

Настройка общих параметров программы:
- Общие настройки (язык, тема, автосохранение)
- Настройки схемы (цвета, размеры элементов)
- Настройки таблиц (шрифты, отображение)
- Цвета интерфейса
"""

from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QPushButton, QDialogButtonBox,
    QColorDialog, QFontComboBox, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import logging

logger = logging.getLogger(__name__)


class ProgramSettingsDialog(QDialog):
    """Диалог параметров программы"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Параметры программы")
        self.resize(700, 550)
        
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
        
        # Разделитель
        layout.addRow(QLabel("<hr>"))
        
        # Автосохранение
        self.autosave_check = QCheckBox("Включить автосохранение")
        self.autosave_check.setChecked(True)
        layout.addRow("", self.autosave_check)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(" минут")
        layout.addRow("Интервал автосохранения:", self.autosave_interval_spin)
        
        # Разделитель
        layout.addRow(QLabel("<hr>"))
        
        # Последние проекты
        self.recent_projects_spin = QSpinBox()
        self.recent_projects_spin.setRange(0, 20)
        self.recent_projects_spin.setValue(10)
        layout.addRow("Количество последних проектов:", self.recent_projects_spin)
        
        # Показывать экран приветствия
        self.splash_check = QCheckBox("Показывать экран приветствия при запуске")
        self.splash_check.setChecked(True)
        layout.addRow("", self.splash_check)
        
        # QFormLayout не имеет метода addStretch, используем spacer
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)
        
        return tab
    
    def _create_scheme_tab(self) -> QWidget:
        """Создание вкладки настроек схемы"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Пункты ПВО
        points_group = QGroupBox("Пункты ПВО")
        points_layout = QFormLayout(points_group)
        
        self.point_color_btn = QPushButton("Выбрать цвет")
        self.point_color_btn.setStyleSheet("background-color: red;")
        self.point_color_btn.clicked.connect(lambda: self._choose_color(self.point_color_btn))
        points_layout.addRow("Цвет пунктов:", self.point_color_btn)
        
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 20)
        self.point_size_spin.setValue(8)
        points_layout.addRow("Размер пунктов:", self.point_size_spin)
        
        self.point_shape_combo = QComboBox()
        self.point_shape_combo.addItems(["Круг", "Квадрат", "Треугольник", "Ромб"])
        points_layout.addRow("Форма:", self.point_shape_combo)
        
        layout.addRow(points_group)
        
        # Эллипсы ошибок
        ellipse_group = QGroupBox("Эллипсы ошибок")
        ellipse_layout = QFormLayout(ellipse_group)
        
        self.ellipse_color_btn = QPushButton("Выбрать цвет")
        self.ellipse_color_btn.setStyleSheet("background-color: blue;")
        self.ellipse_color_btn.clicked.connect(lambda: self._choose_color(self.ellipse_color_btn))
        ellipse_layout.addRow("Цвет эллипсов:", self.ellipse_color_btn)
        
        self.ellipse_opacity_spin = QDoubleSpinBox()
        self.ellipse_opacity_spin.setRange(0.1, 1.0)
        self.ellipse_opacity_spin.setValue(0.5)
        self.ellipse_opacity_spin.setSingleStep(0.1)
        ellipse_layout.addRow("Прозрачность:", self.ellipse_opacity_spin)
        
        self.ellipse_line_spin = QSpinBox()
        self.ellipse_line_spin.setRange(1, 5)
        self.ellipse_line_spin.setValue(2)
        ellipse_layout.addRow("Толщина линии:", self.ellipse_line_spin)
        
        layout.addRow(ellipse_group)
        
        # Измерения
        obs_group = QGroupBox("Измерения")
        obs_layout = QFormLayout(obs_group)
        
        self.direction_color_btn = QPushButton("Выбрать цвет")
        self.direction_color_btn.setStyleSheet("background-color: green;")
        self.direction_color_btn.clicked.connect(lambda: self._choose_color(self.direction_color_btn))
        obs_layout.addRow("Цвет направлений:", self.direction_color_btn)
        
        self.distance_color_btn = QPushButton("Выбрать цвет")
        self.distance_color_btn.setStyleSheet("background-color: orange;")
        self.distance_color_btn.clicked.connect(lambda: self._choose_color(self.distance_color_btn))
        obs_layout.addRow("Цвет расстояний:", self.distance_color_btn)
        
        self.obs_line_spin = QSpinBox()
        self.obs_line_spin.setRange(1, 5)
        self.obs_line_spin.setValue(1)
        obs_layout.addRow("Толщина линии:", self.obs_line_spin)
        
        layout.addRow(obs_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_tables_tab(self) -> QWidget:
        """Создание вкладки настроек таблиц"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Шрифт таблиц
        font_group = QGroupBox("Шрифт")
        font_layout = QFormLayout(font_group)
        
        self.table_font_combo = QFontComboBox()
        font_layout.addRow("Семейство шрифтов:", self.table_font_combo)
        
        self.table_font_size_spin = QSpinBox()
        self.table_font_size_spin.setRange(8, 24)
        self.table_font_size_spin.setValue(10)
        font_layout.addRow("Размер шрифта:", self.table_font_size_spin)
        
        layout.addRow(font_group)
        
        # Отображение
        display_group = QGroupBox("Отображение")
        display_layout = QVBoxLayout(display_group)
        
        # Чередование строк
        self.alternate_rows_check = QCheckBox("Чередовать цвет строк")
        self.alternate_rows_check.setChecked(True)
        display_layout.addWidget(self.alternate_rows_check)
        
        # Показывать сетку
        self.show_grid_check = QCheckBox("Показывать сетку таблицы")
        self.show_grid_check.setChecked(True)
        display_layout.addWidget(self.show_grid_check)
        
        # Показывать заголовки
        self.show_headers_check = QCheckBox("Показывать заголовки столбцов")
        self.show_headers_check.setChecked(True)
        display_layout.addWidget(self.show_headers_check)
        
        # Выделение строки при наведении
        self.highlight_row_check = QCheckBox("Подсвечивать строку при наведении")
        self.highlight_row_check.setChecked(True)
        display_layout.addWidget(self.highlight_row_check)
        
        layout.addRow(display_group)
        
        # Поведение
        behavior_group = QGroupBox("Поведение")
        behavior_layout = QVBoxLayout(behavior_group)
        
        # Подтверждение удаления
        self.confirm_delete_check = QCheckBox("Запрашивать подтверждение при удалении")
        self.confirm_delete_check.setChecked(True)
        behavior_layout.addWidget(self.confirm_delete_check)
        
        # Автосохранение при редактировании
        self.auto_save_edit_check = QCheckBox("Автосохранение при редактировании")
        self.auto_save_edit_check.setChecked(False)
        behavior_layout.addWidget(self.auto_save_edit_check)
        
        layout.addRow(behavior_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_colors_tab(self) -> QWidget:
        """Создание вкладки настроек цветов"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Цвета элементов интерфейса
        interface_group = QGroupBox("Цвета интерфейса")
        interface_layout = QFormLayout(interface_group)
        
        self.bg_color_btn = QPushButton("Фон")
        self.bg_color_btn.setStyleSheet("background-color: white;")
        self.bg_color_btn.clicked.connect(lambda: self._choose_color(self.bg_color_btn))
        interface_layout.addRow("Цвет фона:", self.bg_color_btn)
        
        self.text_color_btn = QPushButton("Текст")
        self.text_color_btn.setStyleSheet("background-color: black;")
        self.text_color_btn.clicked.connect(lambda: self._choose_color(self.text_color_btn))
        interface_layout.addRow("Цвет текста:", self.text_color_btn)
        
        self.selection_color_btn = QPushButton("Выделение")
        self.selection_color_btn.setStyleSheet("background-color: #0078D7;")
        self.selection_color_btn.clicked.connect(lambda: self._choose_color(self.selection_color_btn))
        interface_layout.addRow("Цвет выделения:", self.selection_color_btn)
        
        self.highlight_color_btn = QPushButton("Подсветка")
        self.highlight_color_btn.setStyleSheet("background-color: #FFFF00;")
        self.highlight_color_btn.clicked.connect(lambda: self._choose_color(self.highlight_color_btn))
        interface_layout.addRow("Цвет подсветки:", self.highlight_color_btn)
        
        layout.addRow(interface_group)
        
        # Цвета статусов
        status_group = QGroupBox("Цвета статусов")
        status_layout = QFormLayout(status_group)
        
        self.success_color_btn = QPushButton("Успех")
        self.success_color_btn.setStyleSheet("background-color: green;")
        self.success_color_btn.clicked.connect(lambda: self._choose_color(self.success_color_btn))
        status_layout.addRow("Успешное выполнение:", self.success_color_btn)
        
        self.warning_color_btn = QPushButton("Предупреждение")
        self.warning_color_btn.setStyleSheet("background-color: orange;")
        self.warning_color_btn.clicked.connect(lambda: self._choose_color(self.warning_color_btn))
        status_layout.addRow("Предупреждение:", self.warning_color_btn)
        
        self.error_color_btn = QPushButton("Ошибка")
        self.error_color_btn.setStyleSheet("background-color: red;")
        self.error_color_btn.clicked.connect(lambda: self._choose_color(self.error_color_btn))
        status_layout.addRow("Ошибка:", self.error_color_btn)
        
        layout.addRow(status_group)
        
        layout.addStretch()
        
        return tab
    
    def _choose_color(self, button: QPushButton):
        """Выбор цвета через диалог"""
        current_color = button.styleSheet().split("background-color: ")[1].split(";")[0]
        color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет")
        
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
    
    def _load_settings(self):
        """Загрузка настроек из конфигурации"""
        from PyQt5.QtCore import QSettings
        
        settings = QSettings("GeoAdjustPro", "Settings")
        
        # Загрузка общих настроек
        self.language_combo.setCurrentIndex(settings.value("general/language_index", 0, type=int))
        self.interface_type_combo.setCurrentIndex(settings.value("general/interface_type_index", 0, type=int))
        self.theme_combo.setCurrentIndex(settings.value("general/theme_index", 0, type=int))
        self.autosave_check.setChecked(settings.value("general/autosave_enabled", True, type=bool))
        self.autosave_interval_spin.setValue(settings.value("general/autosave_interval", 5, type=int))
        self.recent_projects_spin.setValue(settings.value("general/recent_projects_count", 10, type=int))
        self.splash_check.setChecked(settings.value("general/show_splash", True, type=bool))
        
        # Загрузка настроек схемы
        self.point_color_btn.setStyleSheet(f"background-color: {settings.value('scheme/point_color', 'red')};")
        self.point_size_spin.setValue(settings.value("scheme/point_size", 8, type=int))
        self.point_shape_combo.setCurrentIndex(settings.value("scheme/point_shape_index", 0, type=int))
        self.ellipse_color_btn.setStyleSheet(f"background-color: {settings.value('scheme/ellipse_color', 'blue')};")
        self.ellipse_opacity_spin.setValue(settings.value("scheme/ellipse_opacity", 0.5, type=float))
        self.direction_color_btn.setStyleSheet(f"background-color: {settings.value('scheme/direction_color', 'green')};")
        self.distance_color_btn.setStyleSheet(f"background-color: {settings.value('scheme/distance_color', 'orange')};")
        
        # Загрузка настроек таблиц
        font_family = settings.value("tables/font_family", "Arial")
        self.table_font_combo.setCurrentFont(QFont(font_family))
        self.table_font_size_spin.setValue(settings.value("tables/font_size", 10, type=int))
        self.alternate_rows_check.setChecked(settings.value("tables/alternate_rows", True, type=bool))
        self.show_grid_check.setChecked(settings.value("tables/show_grid", True, type=bool))
        self.show_headers_check.setChecked(settings.value("tables/show_headers", True, type=bool))
        self.highlight_row_check.setChecked(settings.value("tables/highlight_row", True, type=bool))
        self.confirm_delete_check.setChecked(settings.value("tables/confirm_delete", True, type=bool))
        self.auto_save_edit_check.setChecked(settings.value("tables/auto_save_edit", False, type=bool))
        
        logger.info("Настройки программы загружены")
    
    def accept(self):
        """Подтверждение изменений"""
        # Сохранение настроек
        self._save_settings()
        super().accept()
    
    def _save_settings(self):
        """Сохранение настроек"""
        from PyQt5.QtCore import QSettings
        
        settings_dict = self._collect_settings()
        qsettings = QSettings("GeoAdjustPro", "Settings")
        
        # Сохранение общих настроек
        qsettings.setValue("general/language_index", self.language_combo.currentIndex())
        qsettings.setValue("general/interface_type_index", self.interface_type_combo.currentIndex())
        qsettings.setValue("general/theme_index", self.theme_combo.currentIndex())
        qsettings.setValue("general/autosave_enabled", self.autosave_check.isChecked())
        qsettings.setValue("general/autosave_interval", self.autosave_interval_spin.value())
        qsettings.setValue("general/recent_projects_count", self.recent_projects_spin.value())
        qsettings.setValue("general/show_splash", self.splash_check.isChecked())
        
        # Сохранение настроек схемы
        qsettings.setValue("scheme/point_color", settings_dict['scheme']['point_color'])
        qsettings.setValue("scheme/point_size", self.point_size_spin.value())
        qsettings.setValue("scheme/point_shape_index", self.point_shape_combo.currentIndex())
        qsettings.setValue("scheme/ellipse_color", settings_dict['scheme']['ellipse_color'])
        qsettings.setValue("scheme/ellipse_opacity", self.ellipse_opacity_spin.value())
        qsettings.setValue("scheme/direction_color", settings_dict['scheme']['direction_color'])
        qsettings.setValue("scheme/distance_color", settings_dict['scheme']['distance_color'])
        
        # Сохранение настроек таблиц
        qsettings.setValue("tables/font_family", self.table_font_combo.currentFont().family())
        qsettings.setValue("tables/font_size", self.table_font_size_spin.value())
        qsettings.setValue("tables/alternate_rows", self.alternate_rows_check.isChecked())
        qsettings.setValue("tables/show_grid", self.show_grid_check.isChecked())
        qsettings.setValue("tables/show_headers", self.show_headers_check.isChecked())
        qsettings.setValue("tables/highlight_row", self.highlight_row_check.isChecked())
        qsettings.setValue("tables/confirm_delete", self.confirm_delete_check.isChecked())
        qsettings.setValue("tables/auto_save_edit", self.auto_save_edit_check.isChecked())
        
        qsettings.sync()
        logger.info("Настройки программы сохранены")
    
    def _collect_settings(self) -> Dict[str, Any]:
        """Сбор всех настроек в словарь"""
        settings = {
            "general": {
                "language": self.language_combo.currentText(),
                "interface_type": self.interface_type_combo.currentText(),
                "theme": self.theme_combo.currentText(),
                "autosave_enabled": self.autosave_check.isChecked(),
                "autosave_interval": self.autosave_interval_spin.value(),
                "recent_projects_count": self.recent_projects_spin.value(),
                "show_splash": self.splash_check.isChecked()
            },
            "scheme": {
                "point_color": self.point_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "point_size": self.point_size_spin.value(),
                "point_shape": self.point_shape_combo.currentText(),
                "ellipse_color": self.ellipse_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "ellipse_opacity": self.ellipse_opacity_spin.value(),
                "direction_color": self.direction_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "distance_color": self.distance_color_btn.styleSheet().split("background-color: ")[1].split(";")[0]
            },
            "tables": {
                "font_family": self.table_font_combo.currentFont().family(),
                "font_size": self.table_font_size_spin.value(),
                "alternate_rows": self.alternate_rows_check.isChecked(),
                "show_grid": self.show_grid_check.isChecked(),
                "show_headers": self.show_headers_check.isChecked(),
                "highlight_row": self.highlight_row_check.isChecked(),
                "confirm_delete": self.confirm_delete_check.isChecked(),
                "auto_save_edit": self.auto_save_edit_check.isChecked()
            },
            "colors": {
                "background": self.bg_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "text": self.text_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "selection": self.selection_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "highlight": self.highlight_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "success": self.success_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "warning": self.warning_color_btn.styleSheet().split("background-color: ")[1].split(";")[0],
                "error": self.error_color_btn.styleSheet().split("background-color: ")[1].split(";")[0]
            }
        }
        
        return settings
