#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для GeoAdjust-Pro
"""

import os
import sys
import logging
from pathlib import Path
import math


def setup_logging(level=logging.INFO, log_file=None):
    """Настройка логирования
    
    Args:
        level: Уровень логирования
        log_file: Путь к файлу лога (опционально)
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger('geoadjust')


def get_resource_path(relative_path: str) -> str:
    """Получить путь к ресурсу (работает и в dev, и в PyInstaller)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def dms_to_decimal(degrees: float, minutes: float = 0, seconds: float = 0) -> float:
    """Конвертация DMS в десятичные градусы"""
    sign = 1 if degrees >= 0 else -1
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def decimal_to_dms(decimal_degrees: float) -> tuple:
    """Конвертация десятичных градусов в DMS
    
    Returns:
        tuple: (degrees, minutes, seconds, sign)
    """
    sign = 1 if decimal_degrees >= 0 else -1
    abs_deg = abs(decimal_degrees)
    degrees = int(abs_deg)
    minutes_float = (abs_deg - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return degrees, minutes, seconds, sign


def format_dms(decimal_degrees: float, include_sign: bool = True) -> str:
    """Форматирование угла в DMS строку
    
    Args:
        decimal_degrees: Угол в десятичных градусах
        include_sign: Включать ли знак (N/S/E/W или +/-)
    
    Returns:
        str: Форматированная строка "DD°MM'SS.SS\""
    """
    degrees, minutes, seconds, sign = decimal_to_dms(decimal_degrees)
    
    if include_sign:
        sign_str = "-" if sign < 0 else ""
        return f"{sign_str}{degrees}°{minutes:02d}'{seconds:05.2f}\""
    else:
        return f"{degrees}°{minutes:02d}'{seconds:05.2f}\""


def format_dms_compact(decimal_degrees: float) -> str:
    """Компактное форматирование DMS"""
    degrees, minutes, seconds, sign = decimal_to_dms(decimal_degrees)
    return f"{degrees:3d}°{minutes:02d}'{seconds:05.2f}\""


def parse_dms(dms_string: str) -> float:
    """Парсинг DMS строки в десятичные градусы
    
    Поддерживаемые форматы:
    - "DD°MM'SS.SS\""
    - "DD MM SS.SS"
    - "DD.MMSS" (геодезический формат)
    """
    dms_string = dms_string.strip()
    
    # Геодезический формат DD.MMSS
    if '.' in dms_string and '°' not in dms_string:
        parts = dms_string.split('.')
        if len(parts) == 2:
            degrees = int(parts[0])
            mmss = parts[1].zfill(4)
            minutes = int(mmss[:2])
            seconds = float(mmss[2:]) if len(mmss) > 2 else 0
            return dms_to_decimal(degrees, minutes, seconds)
    
    # Формат DD°MM'SS.SS"
    if '°' in dms_string:
        dms_string = dms_string.replace('°', ' ').replace("'", ' ').replace('"', '').strip()
    
    parts = dms_string.split()
    if len(parts) >= 3:
        degrees = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return dms_to_decimal(degrees, minutes, seconds)
    
    # Просто число
    try:
        return float(dms_string)
    except ValueError:
        return 0.0


def gons_to_degrees(gons: float) -> float:
    """Конвертация гон в градусы"""
    return gons * 0.9


def degrees_to_gons(degrees: float) -> float:
    """Конвертация градусов в гоны"""
    return degrees / 0.9


def radians_to_degrees(radians: float) -> float:
    """Конвертация радиан в градусы"""
    return radians * 180.0 / math.pi


def degrees_to_radians(degrees: float) -> float:
    """Конвертация градусов в радианы"""
    return degrees * math.pi / 180.0


def format_coordinate(value: float, precision: int = 4) -> str:
    """Форматирование координаты"""
    return f"{value:.{precision}f}"


def format_height(value: float, precision: int = 4) -> str:
    """Форматирование высоты"""
    return f"{value:.{precision}f}"


def format_distance(value: float, precision: int = 3) -> str:
    """Форматирование расстояния"""
    return f"{value:.{precision}f}"


def format_sigma(value: float, precision: int = 2) -> str:
    """Форматирование СКО"""
    if value < 0.001:
        return f"{value * 1000:.{precision}f} мм"
    return f"{value:.{precision}f} м"
