#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер систем координат проекта
Управляет настройками СК для конкретного проекта
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from ...crs.database import CRSDatabase
from ...crs.transformer import CoordinateTransformer
from ...crs.projection import GaussKrugerProjection

class CRSManager:
    """Менеджер систем координат проекта"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.crs_db = CRSDatabase()
        self.transformer = CoordinateTransformer(self.crs_db)
        self.projection = GaussKrugerProjection(self.crs_db)
        
        self.settings_file = project_dir / "settings" / "crs.json"
        self.settings: Dict[str, Any] = {}
        
        self._load_settings()
    
    def _load_settings(self):
        """Загрузка настроек СК из файла"""
        if self.settings_file.exists():
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            # Настройки по умолчанию
            self.settings = {
                'base_crs': 'sk42',
                'zone': 7,
                'central_meridian': 39.0,
                'false_easting': 7500000.0,
                'false_northing': 0.0,
                'scale_factor': 1.0,
                'height_system': 'normal',
                'geoid_model': 'EGM2008'
            }
    
    def save_settings(self):
        """Сохранение настроек СК в файл"""
        self.settings_file.parent.mkdir(exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    def set_base_crs(self, crs_name: str):
        """Установка базовой системы координат"""
        if crs_name not in self.crs_db.datums:
            raise ValueError(f"СК {crs_name} не найдена в базе данных")
        
        self.settings['base_crs'] = crs_name
        self.save_settings()
    
    def set_zone(self, zone_number: int):
        """Установка номера зоны Гаусса-Крюгера"""
        zone = self.crs_db.get_zone(self.settings['base_crs'], zone_number)
        if zone is None:
            raise ValueError(f"Зона {zone_number} не найдена для СК {self.settings['base_crs']}")
        
        self.settings['zone'] = zone_number
        self.settings['central_meridian'] = zone.central_meridian
        self.settings['false_easting'] = zone.false_easting
        self.save_settings()
    
    def transform_point(self, x: float, y: float, z: float,
                       from_crs: str, to_crs: str) -> Tuple[float, float, float]:
        """
        Преобразование координат точки между СК
        
        Параметры:
        - x, y, z: координаты в исходной СК
        - from_crs: исходная СК
        - to_crs: целевая СК
        
        Возвращает:
        - x_new, y_new, z_new: координаты в целевой СК
        """
        return self.transformer.transform_between_datums(x, y, z, from_crs, to_crs)
    
    def project_to_plane(self, lat: float, lon: float) -> Tuple[float, float]:
        """
        Проецирование геодезических координат на плоскость
        
        Параметры:
        - lat, lon: геодезические координаты, градусы
        
        Возвращает:
        - x, y: плоские координаты, м
        """
        return self.projection.geodetic_to_gauss_kruger(
            lat, lon,
            self.settings['zone'],
            self.settings['base_crs']
        )
    
    def unproject_from_plane(self, x: float, y: float) -> Tuple[float, float]:
        """
        Обратное проецирование плоских координат на эллипсоид
        
        Параметры:
        - x, y: плоские координаты, м
        
        Возвращает:
        - lat, lon: геодезические координаты, градусы
        """
        return self.projection.gauss_kruger_to_geodetic(
            x, y,
            self.settings['zone'],
            self.settings['base_crs']
        )
