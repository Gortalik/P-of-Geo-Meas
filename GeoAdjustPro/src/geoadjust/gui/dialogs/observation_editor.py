"""
Диалог редактирования измерений
"""

from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton,
    QDialogButtonBox, QGroupBox, QMessageBox, QTabWidget, QWidget, QTimeEdit
)
from PyQt5.QtCore import Qt, QTime
import logging
import math

logger = logging.getLogger(__name__)


class ObservationEditorDialog(QDialog):
    """Диалог для создания/редактирования измерения"""
    
    def __init__(self, observation_data: Optional[Dict[str, Any]] = None, 
                 available_points: list = None, parent=None):
        super().__init__(parent)
        
        self.observation_data = observation_data or {}
        self.available_points = available_points or []
        self.is_edit_mode = bool(observation_data)
        
        self.setWindowTitle("Редактирование измерения" if self.is_edit_mode else "Новое измерение")
        self.setMinimumWidth(550)
        
        self._create_ui()
        self._load_data()
    
    def _create_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка "Основные"
        main_tab = self._create_main_tab()
        tabs.addTab(main_tab, "Основные")
        
        # Вкладка "Значения"
        values_tab = self._create_values_tab()
        tabs.addTab(values_tab, "Значения")
        
        # Вкладка "Точность"
        accuracy_tab = self._create_accuracy_tab()
        tabs.addTab(accuracy_tab, "Точность")
        
        # Вкладка "Дополнительно"
        extra_tab = self._create_extra_tab()
        tabs.addTab(extra_tab, "Дополнительно")
        
        layout.addWidget(tabs)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_main_tab(self) -> QWidget:
        """Создание вкладки основных параметров"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Тип измерения
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Горизонтальное направление",
            "Горизонтальный угол",
            "Наклонное расстояние",
            "Горизонтальное расстояние",
            "Превышение",
            "Зенитное расстояние",
            "Вертикальный угол"
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addRow("Тип измерения:", self.type_combo)
        
        # Станция (пункт наблюдения)
        self.station_combo = QComboBox()
        self.station_combo.setEditable(True)
        self.station_combo.addItems(self.available_points)
        layout.addRow("Станция:", self.station_combo)
        
        # Цель (наблюдаемый пункт)
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.addItems(self.available_points)
        layout.addRow("Цель:", self.target_combo)
        
        # Для углов - второй пункт
        self.target2_label = QLabel("Цель 2:")
        self.target2_combo = QComboBox()
        self.target2_combo.setEditable(True)
        self.target2_combo.addItems(self.available_points)
        layout.addRow(self.target2_label, self.target2_combo)
        self.target2_label.setVisible(False)
        self.target2_combo.setVisible(False)
        
        # Номер приёма
        self.set_number_spin = QSpinBox()
        self.set_number_spin.setRange(1, 99)
        self.set_number_spin.setValue(1)
        layout.addRow("Номер приёма:", self.set_number_spin)
        
        return widget
    
    def _create_values_tab(self) -> QWidget:
        """Создание вкладки значений"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Угловые измерения
        self.angle_group = QGroupBox("Угловое значение")
        angle_layout = QFormLayout(self.angle_group)
        
        # Градусы
        self.degrees_spin = QSpinBox()
        self.degrees_spin.setRange(0, 359)
        self.degrees_spin.setSuffix("°")
        angle_layout.addRow("Градусы:", self.degrees_spin)
        
        # Минуты
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setSuffix("'")
        angle_layout.addRow("Минуты:", self.minutes_spin)
        
        # Секунды
        self.seconds_spin = QDoubleSpinBox()
        self.seconds_spin.setRange(0.0, 59.9999)
        self.seconds_spin.setDecimals(4)
        self.seconds_spin.setSuffix('"')
        angle_layout.addRow("Секунды:", self.seconds_spin)
        
        # Десятичные градусы
        self.decimal_degrees_spin = QDoubleSpinBox()
        self.decimal_degrees_spin.setRange(0.0, 359.999999)
        self.decimal_degrees_spin.setDecimals(6)
        self.decimal_degrees_spin.setSuffix("°")
        self.decimal_degrees_spin.valueChanged.connect(self._update_dms_from_decimal)
        angle_layout.addRow("Десятичные градусы:", self.decimal_degrees_spin)
        
        layout.addWidget(self.angle_group)
        
        # Линейные измерения
        self.distance_group = QGroupBox("Линейное значение")
        distance_layout = QFormLayout(self.distance_group)
        
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.0001, 999999.9999)
        self.distance_spin.setDecimals(4)
        self.distance_spin.setSuffix(" м")
        distance_layout.addRow("Расстояние:", self.distance_spin)
        
        layout.addWidget(self.distance_group)
        
        # Превышение
        self.height_diff_group = QGroupBox("Превышение")
        height_diff_layout = QFormLayout(self.height_diff_group)
        
        self.height_diff_spin = QDoubleSpinBox()
        self.height_diff_spin.setRange(-9999.9999, 9999.9999)
        self.height_diff_spin.setDecimals(4)
        self.height_diff_spin.setSuffix(" м")
        height_diff_layout.addRow("Превышение:", self.height_diff_spin)
        
        layout.addWidget(self.height_diff_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_accuracy_tab(self) -> QWidget:
        """Создание вкладки точности"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # СКО измерения
        self.sigma_spin = QDoubleSpinBox()
        self.sigma_spin.setRange(0.0001, 999.9999)
        self.sigma_spin.setDecimals(4)
        self.sigma_spin.setValue(5.0)
        self.sigma_spin.setSuffix(' "')
        layout.addRow("СКО измерения:", self.sigma_spin)
        
        # Вес измерения
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.01, 1000.0)
        self.weight_spin.setDecimals(2)
        self.weight_spin.setValue(1.0)
        layout.addRow("Вес:", self.weight_spin)
        
        # Автоматический расчет веса
        self.auto_weight_check = QCheckBox("Автоматический расчет веса")
        self.auto_weight_check.setChecked(True)
        self.auto_weight_check.toggled.connect(self._on_auto_weight_toggled)
        layout.addRow("", self.auto_weight_check)
        
        return widget
    
    def _create_extra_tab(self) -> QWidget:
        """Создание вкладки дополнительных параметров"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Высота прибора
        self.instrument_height_spin = QDoubleSpinBox()
        self.instrument_height_spin.setRange(0.0, 99.9999)
        self.instrument_height_spin.setDecimals(4)
        self.instrument_height_spin.setValue(1.5)
        self.instrument_height_spin.setSuffix(" м")
        layout.addRow("Высота прибора:", self.instrument_height_spin)
        
        # Высота цели
        self.target_height_spin = QDoubleSpinBox()
        self.target_height_spin.setRange(0.0, 99.9999)
        self.target_height_spin.setDecimals(4)
        self.target_height_spin.setValue(1.5)
        self.target_height_spin.setSuffix(" м")
        layout.addRow("Высота цели:", self.target_height_spin)
        
        # Температура
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(-50.0, 50.0)
        self.temperature_spin.setDecimals(1)
        self.temperature_spin.setValue(20.0)
        self.temperature_spin.setSuffix(" °C")
        layout.addRow("Температура:", self.temperature_spin)
        
        # Давление
        self.pressure_spin = QDoubleSpinBox()
        self.pressure_spin.setRange(500.0, 1100.0)
        self.pressure_spin.setDecimals(1)
        self.pressure_spin.setValue(1013.25)
        self.pressure_spin.setSuffix(" мбар")
        layout.addRow("Давление:", self.pressure_spin)
        
        # Примечание
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Дополнительная информация")
        layout.addRow("Примечание:", self.note_edit)
        
        return widget
    
    def _on_type_changed(self, index: int):
        """Обработчик изменения типа измерения"""
        # 0: Направление, 1: Угол, 2: Наклонное расст., 3: Гориз. расст., 
        # 4: Превышение, 5: Зенитное расст., 6: Верт. угол
        
        is_angle = index in [0, 1, 5, 6]
        is_distance = index in [2, 3]
        is_height_diff = index == 4
        is_horizontal_angle = index == 1
        
        # Показать/скрыть группы
        self.angle_group.setVisible(is_angle)
        self.distance_group.setVisible(is_distance)
        self.height_diff_group.setVisible(is_height_diff)
        
        # Для горизонтального угла нужен второй пункт
        self.target2_label.setVisible(is_horizontal_angle)
        self.target2_combo.setVisible(is_horizontal_angle)
        
        # Обновить единицы СКО
        if is_angle:
            self.sigma_spin.setSuffix(' "')
            self.sigma_spin.setValue(5.0)
        else:
            self.sigma_spin.setSuffix(' м')
            self.sigma_spin.setValue(0.005)
    
    def _on_auto_weight_toggled(self, checked: bool):
        """Обработчик переключения автоматического расчета веса"""
        self.weight_spin.setEnabled(not checked)
    
    def _update_dms_from_decimal(self, decimal_degrees: float):
        """Обновление градусов/минут/секунд из десятичных градусов"""
        degrees = int(decimal_degrees)
        minutes_decimal = (decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        self.degrees_spin.blockSignals(True)
        self.minutes_spin.blockSignals(True)
        self.seconds_spin.blockSignals(True)
        
        self.degrees_spin.setValue(degrees)
        self.minutes_spin.setValue(minutes)
        self.seconds_spin.setValue(seconds)
        
        self.degrees_spin.blockSignals(False)
        self.minutes_spin.blockSignals(False)
        self.seconds_spin.blockSignals(False)
    
    def _dms_to_decimal(self) -> float:
        """Преобразование градусов/минут/секунд в десятичные градусы"""
        degrees = self.degrees_spin.value()
        minutes = self.minutes_spin.value()
        seconds = self.seconds_spin.value()
        
        return degrees + minutes / 60.0 + seconds / 3600.0
    
    def _load_data(self):
        """Загрузка данных в форму"""
        if not self.observation_data:
            return
        
        # Тип измерения
        obs_type = self.observation_data.get('type', 'direction')
        type_map = {
            'direction': 0,
            'angle': 1,
            'slope_distance': 2,
            'horizontal_distance': 3,
            'height_difference': 4,
            'zenith_angle': 5,
            'vertical_angle': 6
        }
        self.type_combo.setCurrentIndex(type_map.get(obs_type, 0))
        
        # Пункты
        self.station_combo.setCurrentText(self.observation_data.get('from_point', ''))
        self.target_combo.setCurrentText(self.observation_data.get('to_point', ''))
        
        if 'to_point2' in self.observation_data:
            self.target2_combo.setCurrentText(self.observation_data['to_point2'])
        
        # Значение
        value = self.observation_data.get('value', 0.0)
        if self.type_combo.currentIndex() in [0, 1, 5, 6]:  # Угловые
            self.decimal_degrees_spin.setValue(math.degrees(value))
        elif self.type_combo.currentIndex() in [2, 3]:  # Расстояния
            self.distance_spin.setValue(value)
        elif self.type_combo.currentIndex() == 4:  # Превышение
            self.height_diff_spin.setValue(value)
        
        # Точность
        self.sigma_spin.setValue(self.observation_data.get('sigma', 5.0))
        self.weight_spin.setValue(self.observation_data.get('weight', 1.0))
        
        # Дополнительно
        self.instrument_height_spin.setValue(self.observation_data.get('instrument_height', 1.5))
        self.target_height_spin.setValue(self.observation_data.get('target_height', 1.5))
        self.temperature_spin.setValue(self.observation_data.get('temperature', 20.0))
        self.pressure_spin.setValue(self.observation_data.get('pressure', 1013.25))
        self.note_edit.setText(self.observation_data.get('note', ''))
        self.set_number_spin.setValue(self.observation_data.get('set_number', 1))
    
    def _validate_and_accept(self):
        """Валидация данных и принятие"""
        # Проверка станции
        station = self.station_combo.currentText().strip()
        if not station:
            QMessageBox.warning(self, "Ошибка", "Выберите станцию")
            self.station_combo.setFocus()
            return
        
        # Проверка цели
        target = self.target_combo.currentText().strip()
        if not target:
            QMessageBox.warning(self, "Ошибка", "Выберите цель")
            self.target_combo.setFocus()
            return
        
        # Проверка, что станция и цель разные
        if station == target:
            QMessageBox.warning(self, "Ошибка", "Станция и цель должны быть разными пунктами")
            return
        
        # Для углов - проверка второй цели
        if self.type_combo.currentIndex() == 1:  # Горизонтальный угол
            target2 = self.target2_combo.currentText().strip()
            if not target2:
                QMessageBox.warning(self, "Ошибка", "Выберите вторую цель для угла")
                self.target2_combo.setFocus()
                return
            if target2 == station or target2 == target:
                QMessageBox.warning(self, "Ошибка", "Все три пункта должны быть разными")
                return
        
        self.accept()
    
    def get_observation_data(self) -> Dict[str, Any]:
        """Получение данных измерения"""
        type_map = {
            0: 'direction',
            1: 'angle',
            2: 'slope_distance',
            3: 'horizontal_distance',
            4: 'height_difference',
            5: 'zenith_angle',
            6: 'vertical_angle'
        }
        
        obs_type = type_map[self.type_combo.currentIndex()]
        
        # Получение значения в зависимости от типа
        if self.type_combo.currentIndex() in [0, 1, 5, 6]:  # Угловые
            value = math.radians(self._dms_to_decimal())
        elif self.type_combo.currentIndex() in [2, 3]:  # Расстояния
            value = self.distance_spin.value()
        else:  # Превышение
            value = self.height_diff_spin.value()
        
        data = {
            'type': obs_type,
            'from_point': self.station_combo.currentText().strip(),
            'to_point': self.target_combo.currentText().strip(),
            'value': value,
            'sigma': self.sigma_spin.value(),
            'weight': self.weight_spin.value(),
            'set_number': self.set_number_spin.value(),
            'instrument_height': self.instrument_height_spin.value(),
            'target_height': self.target_height_spin.value(),
            'temperature': self.temperature_spin.value(),
            'pressure': self.pressure_spin.value(),
            'note': self.note_edit.text().strip()
        }
        
        # Для углов - добавить вторую цель
        if self.type_combo.currentIndex() == 1:
            data['to_point2'] = self.target2_combo.currentText().strip()
        
        return data
