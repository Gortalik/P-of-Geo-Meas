#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль преобразования координат между системами
Реализует 7-параметрическое преобразование Гельмерта
"""

import numpy as np
from typing import Tuple, Optional
from .database import CRSDatabase, Datum

class CoordinateTransformer:
    """Преобразование координат между системами координат"""
    
    def __init__(self, crs_db: Optional[CRSDatabase] = None):
        self.crs_db = crs_db or CRSDatabase()
    
    def helmert_7param_transform(self,
                                 x: float, y: float, z: float,
                                 dx: float, dy: float, dz: float,
                                 rx: float, ry: float, rz: float,
                                 scale: float) -> Tuple[float, float, float]:
        """
        7-параметрическое преобразование Гельмерта
        
        Параметры:
        - x, y, z: координаты в исходной системе, м
        - dx, dy, dz: линейные сдвиги, м
        - rx, ry, rz: угловые повороты, радианы
        - scale: масштабный множитель (в частях на миллион)
        
        Возвращает:
        - x_new, y_new, z_new: координаты в целевой системе, м
        """
        # Матрица поворота (малые углы)
        R = np.array([
            [1, -rz, ry],
            [rz, 1, -rx],
            [-ry, rx, 1]
        ])
        
        # Масштабный множитель (в долях)
        s = 1.0 + scale / 1e6
        
        # Вектор координат
        X = np.array([x, y, z])
        
        # Преобразование
        X_new = np.array([dx, dy, dz]) + s * R @ X
        
        return X_new[0], X_new[1], X_new[2]
    
    def transform_between_datums(self,
                                 x: float, y: float, z: float,
                                 from_datum: str, to_datum: str) -> Tuple[float, float, float]:
        """
        Преобразование координат между датумами
        
        Параметры:
        - x, y, z: координаты в исходном датуме, м
        - from_datum: исходный датум (например, 'sk42')
        - to_datum: целевой датум (например, 'sk95')
        
        Возвращает:
        - x_new, y_new, z_new: координаты в целевом датуме, м
        """
        from_d = self.crs_db.get_datum(from_datum)
        to_d = self.crs_db.get_datum(to_datum)
        
        if from_d is None:
            raise ValueError(f"Датум {from_datum} не найден")
        if to_d is None:
            raise ValueError(f"Датум {to_datum} не найден")
        
        # Параметры преобразования from_datum → to_datum
        dx = to_d.dx - from_d.dx
        dy = to_d.dy - from_d.dy
        dz = to_d.dz - from_d.dz
        rx = (to_d.rx - from_d.rx) / 3600.0 * np.pi / 180.0  # в радианы
        ry = (to_d.ry - from_d.ry) / 3600.0 * np.pi / 180.0
        rz = (to_d.rz - from_d.rz) / 3600.0 * np.pi / 180.0
        scale = to_d.scale - from_d.scale
        
        return self.helmert_7param_transform(x, y, z, dx, dy, dz, rx, ry, rz, scale)
    
    def geodetic_to_cartesian(self,
                              lat: float, lon: float, h: float,
                              datum: str) -> Tuple[float, float, float]:
        """
        Преобразование геодезических координат в прямоугольные
        
        Параметры:
        - lat: широта, градусы
        - lon: долгота, градусы
        - h: высота над эллипсоидом, м
        - datum: датум (например, 'sk42')
        
        Возвращает:
        - X, Y, Z: прямоугольные координаты, м
        """
        d = self.crs_db.get_datum(datum)
        if d is None:
            raise ValueError(f"Датум {datum} не найден")
        
        ell = d.ellipsoid
        
        # Перевод в радианы
        lat_rad = np.deg2rad(lat)
        lon_rad = np.deg2rad(lon)
        
        # Вспомогательные вычисления
        sin_lat = np.sin(lat_rad)
        cos_lat = np.cos(lat_rad)
        sin_lon = np.sin(lon_rad)
        cos_lon = np.cos(lon_rad)
        
        # Радиус кривизны первого вертикала
        N = ell.a / np.sqrt(1 - ell.f * (2 - ell.f) * sin_lat**2)
        
        # Прямоугольные координаты
        X = (N + h) * cos_lat * cos_lon
        Y = (N + h) * cos_lat * sin_lon
        Z = (N * (1 - ell.f * (2 - ell.f)) + h) * sin_lat
        
        return X, Y, Z
    
    def cartesian_to_geodetic(self,
                              X: float, Y: float, Z: float,
                              datum: str) -> Tuple[float, float, float]:
        """
        Преобразование прямоугольных координат в геодезические
        (итеративный метод)
        
        Параметры:
        - X, Y, Z: прямоугольные координаты, м
        - datum: датум (например, 'sk42')
        
        Возвращает:
        - lat, lon, h: геодезические координаты (широта, долгота в градусах, высота в м)
        """
        d = self.crs_db.get_datum(datum)
        if d is None:
            raise ValueError(f"Датум {datum} не найден")
        
        ell = d.ellipsoid
        
        # Долгота
        lon = np.arctan2(Y, X)
        
        # Начальное приближение для широты
        p = np.sqrt(X**2 + Y**2)
        lat = np.arctan2(Z, p * (1 - ell.f * (2 - ell.f)))
        
        # Итеративное уточнение
        for _ in range(10):
            N = ell.a / np.sqrt(1 - ell.f * (2 - ell.f) * np.sin(lat)**2)
            h = p / np.cos(lat) - N
            lat_new = np.arctan2(Z, p * (1 - ell.f * (2 - ell.f) * N / (N + h)))
            
            if abs(lat_new - lat) < 1e-12:
                break
            
            lat = lat_new
        
        # Высота
        N = ell.a / np.sqrt(1 - ell.f * (2 - ell.f) * np.sin(lat)**2)
        h = p / np.cos(lat) - N
        
        # Перевод в градусы
        lat_deg = np.rad2deg(lat)
        lon_deg = np.rad2deg(lon)
        
        return lat_deg, lon_deg, h
