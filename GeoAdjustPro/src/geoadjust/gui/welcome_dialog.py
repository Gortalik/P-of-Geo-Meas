#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Приветственное окно при запуске приложения P-of-Geo-Meas
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QApplication, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sys
import os
from pathlib import Path


class WelcomeDialog(QDialog):
    """Приветственное окно при запуске приложения"""
    
    # Сигналы для действий
    new_project_requested = pyqtSignal()
    open_project_requested = pyqtSignal()
    recent_project_requested = pyqtSignal(str)
    
    def __init__(self, parent=None, recent_projects=None):
        super().__init__(parent)
        self.recent_projects = recent_projects or []
        self.setWindowTitle("Добро пожаловать в P-of-Geo-Meas")
        self.setFixedSize(900, 600)
        self.setModal(True)
        
        # Установка стиля - простой и надежный стиль
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 2px solid #aaaaaa;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border: 2px solid #999999;
            }
            QPushButton#secondary {
                background-color: #f0f0f0;
            }
            QPushButton#secondary:hover {
                background-color: #e0e0e0;
            }
            QPushButton#recent {
                background-color: #ffffff;
                color: #000000;
                text-align: left;
                padding: 10px 15px 10px 20px;
                font-weight: normal;
                font-size: 12px;
                border: 1px solid #cccccc;
            }
            QPushButton#recent:hover {
                background-color: #f0f0f0;
            }
            QFrame#main_frame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #cccccc;
            }
            QLabel#title {
                font-size: 36px;
                font-weight: bold;
                color: #000000;
            }
            QLabel#subtitle {
                font-size: 16px;
                color: #666666;
            }
            QLabel#version {
                color: #888888;
                font-size: 11px;
            }
        """)
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Основной фрейм - стиль определен в родительском виджете
        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(40, 30, 40, 30)
        frame_layout.setSpacing(25)
        
        # Заголовок с явным указанием цвета
        title_label = QLabel("P-of-Geo-Meas")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; font-size: 36px; font-weight: bold;")
        frame_layout.addWidget(title_label)
        
        # Подзаголовок с явным указанием цвета
        subtitle_label = QLabel("Профессиональная система уравнивания геодезических сетей")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 16px;")
        frame_layout.addWidget(subtitle_label)
        
        frame_layout.addSpacing(10)
        
        # Кнопки основных действий
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("background: transparent;")
        buttons_layout = QVBoxLayout(buttons_frame)
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка "Создать новый проект"
        new_btn = QPushButton("Создать новый проект")
        new_btn.setMinimumHeight(60)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_project)
        buttons_layout.addWidget(new_btn)
        
        # Кнопка "Открыть проект"
        open_btn = QPushButton("Открыть проект")
        open_btn.setMinimumHeight(60)
        open_btn.setObjectName("secondary")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self._on_open_project)
        buttons_layout.addWidget(open_btn)
        
        frame_layout.addWidget(buttons_frame)
        
        # Недавние проекты (если есть)
        if self.recent_projects:
            frame_layout.addSpacing(15)
            
            recent_label = QLabel("Недавние проекты:")
            recent_label.setFont(QFont("Arial", 12, QFont.Bold))
            recent_label.setStyleSheet("color: #2c3e50; margin-top: 10px; font-weight: bold;")
            frame_layout.addWidget(recent_label)
            
            # Показываем только последние 2 проекта для лучшего отображения
            for project_path in self.recent_projects[:2]:  # Максимум 2 проекта
                project_name = os.path.basename(project_path)
                recent_btn = QPushButton(project_name)
                recent_btn.setObjectName("recent")
                recent_btn.setMinimumHeight(40)
                recent_btn.setCursor(Qt.PointingHandCursor)
                recent_btn.setToolTip(project_path)
                recent_btn.clicked.connect(
                    lambda checked, path=project_path: self._on_recent_project(path)
                )
                frame_layout.addWidget(recent_btn)
        
        # Информация о версии с явным цветом
        version_label = QLabel("Версия 1.0.0 • © 2026 GeoAdjust Team")
        version_label.setObjectName("version")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        frame_layout.addWidget(version_label)
        
        layout.addWidget(main_frame)
    
    def _on_new_project(self):
        """Обработчик создания нового проекта"""
        self.new_project_requested.emit()
        self.accept()
    
    def _on_open_project(self):
        """Обработчик открытия проекта"""
        self.open_project_requested.emit()
        self.accept()
    
    def _on_recent_project(self, project_path):
        """Обработчик открытия недавнего проекта"""
        self.recent_project_requested.emit(project_path)
        self.accept()
