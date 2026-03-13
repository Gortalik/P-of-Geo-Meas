#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поток обработки для неблокирующего выполнения уравнивания
"""

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any
from .integration import ProcessingIntegration


class ProcessingThread(QThread):
    """Поток выполнения уравнивания"""
    
    # Сигналы
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, integration: ProcessingIntegration, parent=None):
        super().__init__(parent)
        self.integration = integration
        self.result: Dict[str, Any] = {}
    
    def run(self):
        """Выполнение уравнивания в отдельном потоке"""
        try:
            # Подключение сигналов прогресса
            self.integration.progress_updated.connect(self._on_progress)
            self.integration.processing_finished.connect(self._on_finished)
            self.integration.processing_error.connect(self._on_error)
            
            # Запуск уравнивания
            self.result = self.integration.run_adjustment()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _on_progress(self, percent: int, message: str):
        """Обработчик прогресса"""
        self.progress_updated.emit(percent, message)
    
    def _on_finished(self, result: Dict[str, Any]):
        """Обработчик завершения"""
        self.finished.emit(result)
    
    def _on_error(self, error_msg: str):
        """Обработчик ошибки"""
        self.error_occurred.emit(error_msg)
