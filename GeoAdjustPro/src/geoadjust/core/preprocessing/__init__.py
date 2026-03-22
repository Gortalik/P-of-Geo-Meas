"""
Модуль предобработки геодезических данных.

Включает:
- PreprocessingModule: 9 этапов предобработки
- ToleranceChecker: контроль 27 допусков
"""

from .module import PreprocessingModule
from .tolerances import ToleranceChecker

# Псевдоним для совместимости
DataPreprocessor = PreprocessingModule

__all__ = [
    'PreprocessingModule',
    'DataPreprocessor',
    'ToleranceChecker',
]