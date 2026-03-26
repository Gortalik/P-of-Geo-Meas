#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мастер создания нового проекта GeoAdjust Pro

Пошаговый диалог для создания нового проекта:
1. Имя и расположение
2. Система координат
3. Начальные данные (пункты, измерения)
4. Параметры обработки
"""

from typing import Dict, Any, Optional
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWizard, QWizardPage,
    QLabel, QLineEdit, QTextEdit, QComboBox, QFileDialog, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QGroupBox, QRadioButton,
    QButtonGroup, QMessageBox, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
import logging

logger = logging.getLogger(__name__)


class ProjectWizard(QWizard):
    """Мастер создания нового проекта"""
    
    # ID страниц
    INTRO_PAGE = 0
    LOCATION_PAGE = 1
    CRS_PAGE = 2
    DATA_PAGE = 3
    SETTINGS_PAGE = 4
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Мастер создания проекта")
        self.resize(700, 500)
        
        # Простая и надежная стилизация
        self.setStyleSheet("""
            QWizard {
                background-color: #f0f0f0;
            }
            QWizard > QFrame {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 4px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 6px 12px;
                min-width: 75px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QRadioButton, QCheckBox {
                color: #000000;
            }
        """)
        
        # Настройка флагов
        self.setOption(QWizard.HaveHelpButton, False)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        
        # Инициализация атрибутов до создания страниц
        self.name_edit = None
        self.desc_edit = None
        self.path_edit = None
        self.crs_radio_group = None
        self.zone_spin = None
        self.meridian_edit = None
        self.files_list = None
        self.method_radio_group = None
        self.curvature_check = None
        self.refraction_check = None
        self.centering_check = None
        self.import_points_check = None
        self.import_obs_check = None
        
        # Добавление страниц
        self.addPage(self._create_intro_page())
        self.addPage(self._create_location_page())
        self.addPage(self._create_crs_page())
        self.addPage(self._create_data_page())
        self.addPage(self._create_settings_page())
        
        logger.info("Мастер создания проекта инициализирован")
    
    def _create_intro_page(self) -> QWizardPage:
        """Страница 1: Введение"""
        page = QWizardPage()
        page.setTitle("Добро пожаловать")
        page.setSubTitle("Мастер поможет вам создать новый проект GeoAdjust Pro")
        
        layout = QVBoxLayout(page)
        
        intro_label = QLabel(
            "Этот мастер проведёт вас через все этапы создания нового проекта.\n\n"
            "Вы сможете:\n"
            "• Указать имя и расположение проекта\n"
            "• Выбрать систему координат\n"
            "• Импорт начальных данных\n"
            "• Настроить параметры обработки\n\n"
            "Нажмите 'Далее' для продолжения."
        )
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        layout.addStretch()
        
        return page
    
    def _create_location_page(self) -> QWizardPage:
        """Страница 2: Имя и расположение"""
        page = QWizardPage()
        page.setTitle("Имя и расположение")
        page.setSubTitle("Укажите имя проекта и место сохранения")
        
        layout = QFormLayout(page)
        
        # Имя проекта
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите имя проекта")
        layout.addRow("Имя проекта:", self.name_edit)
        
        # Описание
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        self.desc_edit.setPlaceholderText("Краткое описание проекта (необязательно)")
        layout.addRow("Описание:", self.desc_edit)
        
        # Расположение
        location_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Выберите папку для проекта")
        location_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_btn)
        
        layout.addRow("Расположение:", location_layout)
        
        # Регистрация полей для QWizard
        page.registerField("projectName*", self.name_edit)
        page.registerField("projectPath*", self.path_edit)
        
        return page
    
    def _create_crs_page(self) -> QWizardPage:
        """Страница 3: Система координат"""
        page = QWizardPage()
        page.setTitle("Система координат")
        page.setSubTitle("Выберите систему координат для проекта")
        
        layout = QVBoxLayout(page)
        
        # Группа выбора системы координат
        crs_group = QGroupBox("Геодезическая система координат")
        crs_layout = QVBoxLayout(crs_group)
        
        self.crs_radio_group = QButtonGroup()
        
        crs_options = [
            ("СК-42 (Пулково-1942)", "SK-42"),
            ("СК-95", "SK-95"),
            ("ГСК-2011", "GSK-2011"),
            ("WGS-84", "WGS-84"),
            ("МСК (местная система)", "MSK"),
        ]
        
        for i, (text, value) in enumerate(crs_options):
            radio = QRadioButton(text)
            radio.setProperty("crsValue", value)
            if i == 0:  # Выбор по умолчанию
                radio.setChecked(True)
            self.crs_radio_group.addButton(radio, i)
            crs_layout.addWidget(radio)
        
        layout.addWidget(crs_group)
        
        # Зона
        zone_layout = QFormLayout()
        self.zone_spin = QSpinBox()
        self.zone_spin.setRange(1, 60)
        self.zone_spin.setValue(7)
        zone_layout.addRow("Номер зоны:", self.zone_spin)
        
        self.meridian_edit = QLineEdit("39.0")
        zone_layout.addRow("Осевой меридиан:", self.meridian_edit)
        
        layout.addLayout(zone_layout)
        layout.addStretch()
        
        return page
    
    def _create_data_page(self) -> QWizardPage:
        """Страница 4: Начальные данные"""
        page = QWizardPage()
        page.setTitle("Начальные данные")
        page.setSubTitle("Добавьте пункты и измерения (можно сделать позже)")
        
        layout = QVBoxLayout(page)
        
        # Опции импорта
        import_group = QGroupBox("Импорт данных")
        import_layout = QVBoxLayout(import_group)
        
        self.import_points_check = QCheckBox("Импортировать пункты ПВО")
        self.import_points_check.setChecked(False)
        import_layout.addWidget(self.import_points_check)
        
        self.import_obs_check = QCheckBox("Импортировать измерения")
        self.import_obs_check.setChecked(False)
        import_layout.addWidget(self.import_obs_check)
        
        layout.addWidget(import_group)
        
        # Кнопки импорта
        btn_layout = QHBoxLayout()
        
        import_points_btn = QPushButton("Импорт пунктов...")
        import_points_btn.clicked.connect(self._import_points)
        btn_layout.addWidget(import_points_btn)
        
        import_obs_btn = QPushButton("Импорт измерений...")
        import_obs_btn.clicked.connect(self._import_observations)
        btn_layout.addWidget(import_obs_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Список файлов
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(100)
        layout.addWidget(QLabel("Импортированные файлы:"))
        layout.addWidget(self.files_list)
        
        layout.addStretch()
        
        return page
    
    def _create_settings_page(self) -> QWizardPage:
        """Страница 5: Параметры обработки"""
        page = QWizardPage()
        page.setTitle("Параметры обработки")
        page.setSubTitle("Настройте основные параметры уравнивания")
        
        layout = QVBoxLayout(page)
        
        # Метод уравнивания
        method_group = QGroupBox("Метод уравнивания")
        method_layout = QVBoxLayout(method_group)
        
        self.method_radio_group = QButtonGroup()
        
        classic_radio = QRadioButton("Классический МНК")
        classic_radio.setChecked(True)
        classic_radio.setToolTip("Метод наименьших квадратов Гаусса")
        self.method_radio_group.addButton(classic_radio, 0)
        method_layout.addWidget(classic_radio)
        
        robust_radio = QRadioButton("Робастное уравнивание")
        robust_radio.setToolTip("Устойчивое к грубым ошибкам уравнивание")
        self.method_radio_group.addButton(robust_radio, 1)
        method_layout.addWidget(robust_radio)
        
        layout.addWidget(method_group)
        
        # Поправки
        corrections_group = QGroupBox("Применяемые поправки")
        corrections_layout = QVBoxLayout(corrections_group)
        
        self.curvature_check = QCheckBox("Поправка за кривизну Земли")
        self.curvature_check.setChecked(True)
        corrections_layout.addWidget(self.curvature_check)
        
        self.refraction_check = QCheckBox("Поправка за рефракцию")
        self.refraction_check.setChecked(True)
        corrections_layout.addWidget(self.refraction_check)
        
        self.centering_check = QCheckBox("Поправка за приведение к центру")
        self.centering_check.setChecked(True)
        corrections_layout.addWidget(self.centering_check)
        
        layout.addWidget(corrections_group)
        
        layout.addStretch()
        
        return page
    
    def _browse_location(self):
        """Выбор папки для проекта"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для проекта",
            "",
            QFileDialog.ShowDirsOnly
        )
        if directory:
            self.path_edit.setText(directory)
    
    def _import_points(self):
        """Импорт пунктов"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Импорт пунктов ПВО",
            "",
            "Текстовые файлы (*.txt);;CSV файлы (*.csv);;Все файлы (*)"
        )
        for file in files:
            item = QListWidgetItem(f"Пункты: {Path(file).name}")
            item.setData(Qt.UserRole, ("points", file))
            self.files_list.addItem(item)
    
    def _import_observations(self):
        """Импорт измерений"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Импорт измерений",
            "",
            "Файлы приборов (*.gsi *.sdr *.dat);;Текстовые файлы (*.txt);;Все файлы (*)"
        )
        for file in files:
            item = QListWidgetItem(f"Измерения: {Path(file).name}")
            item.setData(Qt.UserRole, ("observations", file))
            self.files_list.addItem(item)
    
    def get_project_data(self) -> Dict[str, Any]:
        """Получение данных проекта после завершения мастера"""
        # Получение выбранной системы координат
        selected_crs_button = self.crs_radio_group.checkedButton()
        crs_value = selected_crs_button.property("crsValue") if selected_crs_button else "SK-42"
        
        # Получение выбранного метода
        selected_method_button = self.method_radio_group.checkedButton()
        method_index = self.method_radio_group.id(selected_method_button) if selected_method_button else 0
        method = "classic" if method_index == 0 else "robust"
        
        # Сбор файлов для импорта
        files_to_import = []
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            files_to_import.append(item.data(Qt.UserRole))
        
        return {
            'name': self.name_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'path': self.path_edit.text(),
            'crs': {
                'type': crs_value,
                'zone': self.zone_spin.value(),
                'meridian': float(self.meridian_edit.text() or 0),
            },
            'method': method,
            'corrections': {
                'curvature': self.curvature_check.isChecked(),
                'refraction': self.refraction_check.isChecked(),
                'centering': self.centering_check.isChecked(),
            },
            'files_to_import': files_to_import,
        }
    
    def accept(self):
        """Завершение мастера"""
        # Валидация данных
        project_path_str = self.path_edit.text()
        project_name = self.name_edit.text()
        
        if not project_path_str or not project_name:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Необходимо указать имя проекта и путь к папке"
            )
            return
        
        project_path = Path(project_path_str)
        
        # Проверка существования файла проекта
        gad_file = project_path / f"{project_name}.gad"
        if gad_file.exists():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Файл проекта '{gad_file.name}' уже существует.\nПерезаписать?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        super().accept()
        logger.info(f"Мастер создания проекта завершён: {project_name}")
