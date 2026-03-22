"""
Модуль анализа надёжности геодезической сети.

Включает:
- BaardaReliability: анализ по теории В. Баарда
- ReliabilityAnalysis: псевдоним для совместимости
"""

from .baarda_method import BaardaReliability

# Псевдоним для совместимости
ReliabilityAnalysis = BaardaReliability

__all__ = [
    'BaardaReliability',
    'ReliabilityAnalysis',
]