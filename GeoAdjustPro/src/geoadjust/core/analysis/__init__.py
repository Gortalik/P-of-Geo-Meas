"""
Модуль анализа результатов уравнивания.

Включает:
- Расчёт эллипсов ошибок
- Анализ грубых ошибок
- Контроль нормативных классов
- Визуализация результатов
"""

from .visualization import Visualization

# EllipseErrorCalculator может быть недоступен в некоторых версиях
try:
    from .ellipse_errors import ErrorEllipseAnalyzer as EllipseErrorCalculator
except ImportError:
    EllipseErrorCalculator = None

try:
    from .gross_errors import GrossErrorAnalyzer
except ImportError:
    GrossErrorAnalyzer = None

try:
    from .normative_classes import NormativeClass, NormativeClassLibrary
except ImportError:
    NormativeClass = None
    NormativeClassLibrary = None

__all__ = [
    'Visualization',
    'EllipseErrorCalculator',
    'GrossErrorAnalyzer',
    'NormativeClass',
    'NormativeClassLibrary',
]
