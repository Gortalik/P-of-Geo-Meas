"""
Виджет журнала событий для GeoAdjust Pro
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QColor


class QtLogHandler(logging.Handler, QObject):
    """Обработчик логов для Qt виджета"""
    
    log_signal = pyqtSignal(str, str)  # message, level
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
    def emit(self, record):
        """Отправка лог-записи"""
        try:
            msg = self.format(record)
            level = record.levelname
            self.log_signal.emit(msg, level)
        except Exception:
            self.handleError(record)


class LogWidget(QWidget):
    """Виджет журнала событий"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Текстовое поле журнала
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setFontPointSize(9)
        
        layout.addWidget(self.log_text)
        
        # Создание обработчика логов
        self.log_handler = None
        self._setup_logging()
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)
        
        save_btn = QPushButton("Сохранить...")
        save_btn.clicked.connect(self.save_log)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        
        # Фильтры
        self.filter_info_check = QPushButton("INFO")
        self.filter_info_check.setCheckable(True)
        self.filter_info_check.setChecked(True)
        self.filter_info_check.setMaximumWidth(50)
        toolbar.addWidget(self.filter_info_check)
        
        self.filter_warning_check = QPushButton("WARN")
        self.filter_warning_check.setCheckable(True)
        self.filter_warning_check.setChecked(True)
        self.filter_warning_check.setMaximumWidth(50)
        toolbar.addWidget(self.filter_warning_check)
        
        self.filter_error_check = QPushButton("ERROR")
        self.filter_error_check.setCheckable(True)
        self.filter_error_check.setChecked(True)
        self.filter_error_check.setMaximumWidth(50)
        toolbar.addWidget(self.filter_error_check)
        
        layout.addLayout(toolbar)
    
    def _setup_logging(self):
        """Настройка перехвата логов Python"""
        self.log_handler = QtLogHandler()
        self.log_handler.log_signal.connect(self._handle_log_message)
        
        # Добавление обработчика к корневому логгеру
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        
        # Форматирование
        formatter = logging.Formatter('%(name)s - %(message)s')
        self.log_handler.setFormatter(formatter)
    
    def _handle_log_message(self, message: str, level: str):
        """Обработка лог-сообщения из Python logging"""
        self.log_message(message, level)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Добавление сообщения в журнал"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Определение цвета по уровню
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        else:
            color = "black"
        
        # Форматирование сообщения
        html_message = f'<span style="color: gray;">[{timestamp}]</span> '
        html_message += f'<span style="color: {color}; font-weight: bold;">{level}:</span> '
        html_message += f'<span style="color: black;">{message}</span><br>'
        
        # Добавление в конец
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html_message)
        self.log_text.setTextCursor(cursor)
        
        # Автопрокрутка
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def info(self, message: str):
        """Добавление информационного сообщения"""
        self.log_message(message, "INFO")
    
    def warning(self, message: str):
        """Добавление предупреждения"""
        self.log_message(message, "WARNING")
    
    def error(self, message: str):
        """Добавление ошибки"""
        self.log_message(message, "ERROR")
    
    def success(self, message: str):
        """Добавление сообщения об успехе"""
        self.log_message(message, "SUCCESS")
    
    def clear_log(self):
        """Очистка журнала"""
        self.log_text.clear()
    
    def save_log(self):
        """Сохранение журнала в файл"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить журнал", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
