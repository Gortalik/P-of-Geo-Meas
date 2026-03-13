#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поток обработки для выполнения уравнивания в фоновом режиме
"""

import logging
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any

from .integration import ProcessingIntegration

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """Поток для выполнения уравнивания без блокировки интерфейса"""
    
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, integration: ProcessingIntegration, parent=None):
        super().__init__(parent)
        self.integration = integration
    
    def run(self):
        """Выполнение уравнивания в отдельном потоке"""
        try:
            result = self.integration.run_adjustment()
            self.finished.emit(result)
        except Exception as e:
            error_msg = f"Ошибка в потоке обработки: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
