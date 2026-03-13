#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс для всех парсеров форматов приборов
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ParseError:
    """Ошибка парсинга"""
    line: int
    message: str
    raw_line: str = ""


@dataclass
class ParseWarning:
    """Предупреждение парсинга"""
    line: int
    message: str
    raw_line: str = ""


class BaseParser(ABC):
    """Базовый класс для парсеров форматов приборов"""

    def __init__(self):
        self.errors: List[ParseError] = []
        self.warnings: List[ParseWarning] = []

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсинг файла с измерениями

        Возвращает:
        - Словарь с результатами парсинга
        """
        pass

    def _add_error(self, message: str, line: int = None, raw_line: str = ""):
        """Добавление ошибки в список"""
        error = ParseError(line=line or 0, message=message, raw_line=raw_line[:100])
        self.errors.append(error)
        logger.error(f"Ошибка [{line}]: {message}")

    def _add_warning(self, message: str, line: int = None, raw_line: str = ""):
        """Добавление предупреждения в список"""
        warning = ParseWarning(line=line or 0, message=message, raw_line=raw_line[:100])
        self.warnings.append(warning)
        logger.warning(f"Предупреждение [{line}]: {message}")

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по результатам парсинга"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'success': len(self.errors) == 0
        }

    def has_errors(self) -> bool:
        """Проверка наличия ошибок"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Проверка наличия предупреждений"""
        return len(self.warnings) > 0
