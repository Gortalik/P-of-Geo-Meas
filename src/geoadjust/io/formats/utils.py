#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вспомогательные утилиты для парсеров форматов приборов
"""

import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def dms_to_decimal(degrees: float, minutes: float = 0, seconds: float = 0) -> float:
    """
    Преобразование градусов, минут, секунд в десятичные градусы
    
    Параметры:
    - degrees: градусы
    - minutes: минуты (опционально)
    - seconds: секунды (опционально)
    
    Возвращает:
    - Угол в десятичных градусах
    """
    sign = 1 if degrees >= 0 else -1
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def decimal_to_dms(decimal_degrees: float) -> Tuple[int, int, float]:
    """
    Преобразование десятичных градусов в градусы, минуты, секунды
    
    Параметры:
    - decimal_degrees: угол в десятичных градусах
    
    Возвращает:
    - Кортеж (градусы, минуты, секунды)
    """
    sign = 1 if decimal_degrees >= 0 else -1
    decimal_degrees = abs(decimal_degrees)
    
    degrees = int(decimal_degrees)
    minutes = int((decimal_degrees - degrees) * 60)
    seconds = (decimal_degrees - degrees - minutes / 60.0) * 3600
    
    return (sign * degrees, minutes, seconds)


def parse_angle_string(angle_str: str) -> Optional[float]:
    """
    Парсинг строки с углом в различных форматах
    
    Поддерживаемые форматы:
    - "90.000833" - десятичные градусы
    - "90°00'03\"" - градусы, минуты, секунды
    - "90 00 03" - разделитель пробел
    - "90:00:03" - разделитель двоеточие
    
    Возвращает:
    - Угол в десятичных градусах или None при ошибке
    """
    angle_str = angle_str.strip()
    
    # Формат: десятичные градусы
    try:
        return float(angle_str)
    except ValueError:
        pass
    
    # Формат: градусы°минуты'секунды"
    dms_match = re.match(r'(\d+)[°dD](\d+)[\'mM](\d+(?:\.\d+)?)["sS]?', angle_str)
    if dms_match:
        degrees = float(dms_match.group(1))
        minutes = float(dms_match.group(2))
        seconds = float(dms_match.group(3))
        return dms_to_decimal(degrees, minutes, seconds)
    
    # Формат: градусы минуты секунды (разделитель пробел или :)
    parts = re.split(r'[ :]', angle_str)
    if len(parts) >= 3:
        try:
            degrees = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return dms_to_decimal(degrees, minutes, seconds)
        except ValueError:
            pass
    
    logger.warning(f"Не удалось распарсить угол: {angle_str}")
    return None


def parse_coordinate_string(coord_str: str) -> Optional[float]:
    """
    Парсинг строки с координатой
    
    Поддерживаемые форматы:
    - "2458721.345" - десятичные метры
    - "2 458 721.345" - с пробелами-разделителями
    - "2458721,345" - запятая как десятичный разделитель
    
    Возвращает:
    - Координату в метрах или None при ошибке
    """
    # Удаление пробелов-разделителей тысяч
    coord_str = coord_str.replace(' ', '').replace('\xa0', '')
    
    # Замена запятой на точку для десятичного разделителя
    coord_str = coord_str.replace(',', '.')
    
    try:
        return float(coord_str)
    except ValueError:
        logger.warning(f"Не удалось распарсить координату: {coord_str}")
        return None


def detect_angle_format(angle_value: float) -> str:
    """
    Определение формата угла по его значению
    
    Параметры:
    - angle_value: значение угла
    
    Возвращает:
    - "degrees" - десятичные градусы
    - "gons" - грады (гоны)
    - "mils" - тысячные
    """
    if 0 <= angle_value <= 360:
        return "degrees"
    elif 0 <= angle_value <= 400:
        return "gons"
    elif 0 <= angle_value <= 6400:
        return "mils"
    else:
        return "unknown"


def validate_coordinate_range(coord: float, coord_type: str = 'x') -> bool:
    """
    Валидация диапазона координаты
    
    Параметры:
    - coord: значение координаты
    - coord_type: 'x', 'y', или 'h'
    
    Возвращает:
    - True если координата в допустимом диапазоне
    """
    # Типичные диапазоны для РФ
    if coord_type in ['x', 'y']:
        # Плановые координаты в метрах
        return -10000000 <= coord <= 10000000
    elif coord_type == 'h':
        # Высоты в метрах
        return -500 <= coord <= 10000
    return False
