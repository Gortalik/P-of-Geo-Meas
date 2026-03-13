from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
import re


class BaseParser(ABC):
    """Базовый класс для парсеров форматов приборов"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсинг файла с измерениями

        Возвращает:
        - Словарь с пунктами и измерениями
        """
        pass

    def _add_error(self, message: str, line: int = None):
        """Добавление ошибки в список"""
        error = {'message': message, 'line': line}
        self.errors.append(error)

    def _add_warning(self, message: str, line: int = None):
        """Добавление предупреждения в список"""
        warning = {'message': message, 'line': line}
        self.warnings.append(warning)