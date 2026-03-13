#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль проекции координат на плоскость (проекция Гаусса-Крюгера)
"""

import numpy as np
from typing import Tuple, Optional
from .database import CRSDatabase, ZoneParameters

class GaussKrugerProjection:
    """Проекция Гаусса-Крюгера"""
    
    def __init__(self, crs_db: Optional[CRSDatabase] = None):
        self.crs_db = crs_db or CRSDatabase()
    
    def geodetic_to_gauss_kruger(self,
                                  lat: float, lon: float,
                                  zone: int, base_crs: str = 'sk42') -> Tuple[float, float]:
        """
        Преобразование геодезических координат в плоские (Гаусс-Крюгер)
        
        Параметры:
        - lat: широта, градусы
        - lon: долгота, градусы
        - zone: номер зоны Гаусса-Крюгера
        - base_crs: базовая система координат ('sk42', 'sk95', 'gsk2011')
        
        Возвращает:
        - x, y: плоские координаты, м
        """
        # Получение параметров зоны
        zone_params = self.crs_db.get_zone(base_crs, zone)
        if zone_params is None:
            raise ValueError(f"Зона {zone} для СК {base_crs} не найдена")
        
        # Параметры эллипсоида
        datum = self.crs_db.get_datum(base_crs)
        if datum is None:
            raise ValueError(f"Датум {base_crs} не найден")
        
        ell = datum.ellipsoid
        
        # Перевод в радианы
        lat_rad = np.deg2rad(lat)
        lon_rad = np.deg2rad(lon)
        central_meridian_rad = np.deg2rad(zone_params.central_meridian)
        
        # Разность долгот от осевого меридиана
        delta_lon = lon_rad - central_meridian_rad
        
        # Вспомогательные вычисления
        sin_lat = np.sin(lat_rad)
        cos_lat = np.cos(lat_rad)
        
        # Радиус кривизны меридиана
        M = ell.a * (1 - ell.f * (2 - ell.f)) / (1 - ell.f * (2 - ell.f) * sin_lat**2)**1.5
        
        # Радиус кривизны первого вертикала
        N = ell.a / np.sqrt(1 - ell.f * (2 - ell.f) * sin_lat**2)
        
        # Длина дуги меридиана от экватора
        # Упрощённая формула (для точности < 1 м достаточно)
        A0 = 1 - ell.f * (2 - ell.f) / 4 - 3 * (ell.f * (2 - ell.f))**2 / 64 - 5 * (ell.f * (2 - ell.f))**3 / 256
        A2 = 3 * (ell.f * (2 - ell.f)) / 8 + 3 * (ell.f * (2 - ell.f))**2 / 32 + 45 * (ell.f * (2 - ell.f))**3 / 1024
        A4 = 15 * (ell.f * (2 - ell.f))**2 / 256 + 45 * (ell.f * (2 - ell.f))**3 / 1024
        A6 = 35 * (ell.f * (2 - ell.f))**3 / 3072
        
        S = ell.a * (A0 * lat_rad - A2 * np.sin(2 * lat_rad) + 
                     A4 * np.sin(4 * lat_rad) - A6 * np.sin(6 * lat_rad))
        
        # Плоские координаты (формулы Гаусса-Крюгера)
        t = np.tan(lat_rad)
        eta2 = ell.f * (2 - ell.f) * cos_lat**2 / (1 - ell.f * (2 - ell.f) * sin_lat**2)
        
        x = S + N * t * delta_lon**2 / 2 + N * t * (5 - t**2 + 9 * eta2 + 4 * eta2**2) * delta_lon**4 / 24
        
        y = N * cos_lat * delta_lon + N * cos_lat**3 * (1 - t**2 + eta2) * delta_lon**3 / 6
        
        # Применение параметров зоны
        x = x * zone_params.scale_factor
        y = y * zone_params.scale_factor + zone_params.false_easting
        
        return x, y
    
    def gauss_kruger_to_geodetic(self,
                                  x: float, y: float,
                                  zone: int, base_crs: str = 'sk42') -> Tuple[float, float]:
        """
        Преобразование плоских координат в геодезические (обратная задача)
        
        Параметры:
        - x, y: плоские координаты, м
        - zone: номер зоны Гаусса-Крюгера
        - base_crs: базовая система координат ('sk42', 'sk95', 'gsk2011')
        
        Возвращает:
        - lat, lon: геодезические координаты, градусы
        """
        # Получение параметров зоны
        zone_params = self.crs_db.get_zone(base_crs, zone)
        if zone_params is None:
            raise ValueError(f"Зона {zone} для СК {base_crs} не найдена")
        
        # Параметры эллипсоида
        datum = self.crs_db.get_datum(base_crs)
        if datum is None:
            raise ValueError(f"Датум {base_crs} не найден")
        
        ell = datum.ellipsoid
        
        # Коррекция координат
        y_corrected = (y - zone_params.false_easting) / zone_params.scale_factor
        x_corrected = x / zone_params.scale_factor
        
        # Начальное приближение для широты (на экваторе)
        lat_rad = x_corrected / ell.a
        
        # Итеративное уточнение широты
        for _ in range(5):
            # Радиус кривизны меридиана
            sin_lat = np.sin(lat_rad)
            M = ell.a * (1 - ell.f * (2 - ell.f)) / (1 - ell.f * (2 - ell.f) * sin_lat**2)**1.5
            
            # Уточнение широты
            lat_rad_new = lat_rad + (x_corrected - ell.a * lat_rad) / M
            
            if abs(lat_rad_new - lat_rad) < 1e-12:
                break
            
            lat_rad = lat_rad_new
        
        # Вычисление долготы
        sin_lat = np.sin(lat_rad)
        cos_lat = np.cos(lat_rad)
        N = ell.a / np.sqrt(1 - ell.f * (2 - ell.f) * sin_lat**2)
        
        delta_lon = y_corrected / (N * cos_lat)
        central_meridian_rad = np.deg2rad(zone_params.central_meridian)
        lon_rad = central_meridian_rad + delta_lon
        
        # Перевод в градусы
        lat_deg = np.rad2deg(lat_rad)
        lon_deg = np.rad2deg(lon_rad)
        
        return lat_deg, lon_deg
