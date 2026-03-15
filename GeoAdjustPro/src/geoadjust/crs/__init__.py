"""
Модуль работы с системами координат (CRS - Coordinate Reference System).

Включает:
- Базу данных параметров систем координат РФ
- Преобразования между различными СК
- Проекцию Гаусса-Крюгера
- Модели геоида для преобразования высот
"""

from .database import CRSDatabase
from .transformer import CoordinateTransformer
from .projection import GaussKrugerProjection
from .geoid import GeoidModel, GeoidConverter

__all__ = [
    'CRSDatabase',
    'CoordinateTransformer',
    'GaussKrugerProjection',
    'GeoidModel',
    'GeoidConverter',
]
