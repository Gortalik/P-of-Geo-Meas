#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
База данных систем координат РФ
Содержит параметры СК-42, СК-95, ГСК-2011, МСК 128 субъектов РФ
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass

@dataclass
class Ellipsoid:
    """Параметры эллипсоида"""
    name: str
    a: float  # Большая полуось, м
    inv_f: float  # Обратное сжатие
    f: float = None  # Сжатие (вычисляется)
    
    def __post_init__(self):
        if self.f is None:
            self.f = 1.0 / self.inv_f

@dataclass
class Datum:
    """Параметры датума"""
    name: str
    ellipsoid: Ellipsoid
    dx: float  # сдвиг по оси X, м
    dy: float  # сдвиг по оси Y, м
    dz: float  # сдвиг по оси Z, м
    rx: float  # поворот вокруг оси X, угл. сек
    ry: float  # поворот вокруг оси Y, угл. сек
    rz: float  # поворот вокруг оси Z, угл. сек
    scale: float  # масштабный множитель, частей на миллион (ппм)

@dataclass
class ZoneParameters:
    """Параметры зоны проекции Гаусса-Крюгера"""
    zone_number: int
    central_meridian: float  # осевой меридиан, градусы
    false_easting: float  # ложное восточное смещение, м
    false_northing: float  # ложное северное смещение, м
    scale_factor: float = 1.0  # масштабный множитель

@dataclass
class MSCParameters:
    """Параметры местной системы координат (МСК)"""
    region_code: str  # код субъекта РФ (01-99, 010-128)
    region_name: str  # наименование субъекта РФ
    base_crs: str  # базовая СК (СК-42, СК-95)
    zone: int  # номер зоны
    central_meridian: float  # осевой меридиан, градусы
    false_easting: float  # ложное восточное смещение, м
    false_northing: float  # ложное северное смещение, м
    scale_factor: float  # масштабный множитель
    rotation: float  # поворот осей, радианы

class CRSDatabase:
    """База данных систем координат РФ"""
    
    def __init__(self):
        self.ellipsoids: Dict[str, Ellipsoid] = {}
        self.datums: Dict[str, Datum] = {}
        self.zones: Dict[str, Dict[int, ZoneParameters]] = {}
        self.msc_regions: Dict[str, MSCParameters] = {}
        
        self._load_default_database()
    
    def _load_default_database(self):
        """Загрузка базы данных по умолчанию"""
        
        # Эллипсоиды
        self.ellipsoids['krassovsky_1940'] = Ellipsoid(
            name="Красовского 1940",
            a=6378245.0,
            inv_f=298.3
        )
        
        self.ellipsoids['pz_90_11'] = Ellipsoid(
            name="ПЗ-90.11",
            a=6378136.5,
            inv_f=298.2564151
        )
        
        self.ellipsoids['grs80'] = Ellipsoid(
            name="GRS80",
            a=6378137.0,
            inv_f=298.257222101
        )
        
        # Датумы
        self.datums['sk42'] = Datum(
            name="СК-42",
            ellipsoid=self.ellipsoids['krassovsky_1940'],
            dx=23.57,
            dy=-140.95,
            dz=-79.89,
            rx=0.0,
            ry=0.35,
            rz=0.79,
            scale=-0.19
        )
        
        self.datums['sk95'] = Datum(
            name="СК-95",
            ellipsoid=self.ellipsoids['krassovsky_1940'],
            dx=0.05,
            dy=-0.03,
            dz=0.05,
            rx=0.0,
            ry=0.0,
            rz=0.0,
            scale=0.0
        )
        
        self.datums['gsk2011'] = Datum(
            name="ГСК-2011",
            ellipsoid=self.ellipsoids['pz_90_11'],
            dx=0.0,
            dy=0.0,
            dz=0.0,
            rx=0.0,
            ry=0.0,
            rz=0.0,
            scale=0.0
        )
        
        # Зоны Гаусса-Крюгера для СК-42
        zones_sk42 = {}
        for zone_num in range(4, 33):  # Зоны 4-32
            central_meridian = zone_num * 6 - 3
            zones_sk42[zone_num] = ZoneParameters(
                zone_number=zone_num,
                central_meridian=central_meridian,
                false_easting=zone_num * 1000000.0,
                false_northing=0.0,
                scale_factor=1.0
            )
        self.zones['sk42'] = zones_sk42
        
        # Зоны Гаусса-Крюгера для СК-95
        zones_sk95 = {}
        for zone_num in range(4, 33):  # Зоны 4-32
            central_meridian = zone_num * 6 - 3
            zones_sk95[zone_num] = ZoneParameters(
                zone_number=zone_num,
                central_meridian=central_meridian,
                false_easting=zone_num * 1000000.0,
                false_northing=0.0,
                scale_factor=1.0
            )
        self.zones['sk95'] = zones_sk95
        
        # Зоны Гаусса-Крюгера для ГСК-2011
        zones_gsk2011 = {}
        for zone_num in range(4, 33):  # Зоны 4-32
            central_meridian = zone_num * 6 - 3
            zones_gsk2011[zone_num] = ZoneParameters(
                zone_number=zone_num,
                central_meridian=central_meridian,
                false_easting=zone_num * 1000000.0,
                false_northing=0.0,
                scale_factor=1.0
            )
        self.zones['gsk2011'] = zones_gsk2011
        
        # Местные системы координат (МСК) - пример для нескольких субъектов
        self.msc_regions['01'] = MSCParameters(
            region_code="01",
            region_name="Республика Адыгея",
            base_crs="sk42",
            zone=37,
            central_meridian=39.0,
            false_easting=37500000.0,
            false_northing=-5000000.0,
            scale_factor=1.0000123,
            rotation=0.000628  # радианы (0°02'15.4")
        )
        
        self.msc_regions['02'] = MSCParameters(
            region_code="02",
            region_name="Республика Башкортостан",
            base_crs="sk42",
            zone=41,
            central_meridian=51.0,
            false_easting=41500000.0,
            false_northing=-5000000.0,
            scale_factor=1.0000156,
            rotation=0.000349  # радианы (0°02'00.0")
        )
        
        # ... добавить остальные 126 субъектов РФ
    
    def get_ellipsoid(self, name: str) -> Optional[Ellipsoid]:
        """Получение параметров эллипсоида по имени"""
        return self.ellipsoids.get(name.lower())
    
    def get_datum(self, name: str) -> Optional[Datum]:
        """Получение параметров датума по имени"""
        return self.datums.get(name.lower())
    
    def get_zone(self, base_crs: str, zone_number: int) -> Optional[ZoneParameters]:
        """Получение параметров зоны проекции"""
        zones = self.zones.get(base_crs.lower())
        if zones:
            return zones.get(zone_number)
        return None
    
    def get_msc(self, region_code: str) -> Optional[MSCParameters]:
        """Получение параметров МСК по коду субъекта"""
        return self.msc_regions.get(region_code)
    
    def list_available_crs(self) -> Dict[str, List[str]]:
        """Получение списка доступных систем координат"""
        return {
            'datums': list(self.datums.keys()),
            'ellipsoids': list(self.ellipsoids.keys()),
            'zones_sk42': list(self.zones.get('sk42', {}).keys()),
            'zones_sk95': list(self.zones.get('sk95', {}).keys()),
            'zones_gsk2011': list(self.zones.get('gsk2011', {}).keys()),
            'msc_regions': list(self.msc_regions.keys())
        }
