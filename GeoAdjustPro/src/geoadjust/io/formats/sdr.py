#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Sokkia SDR33 (Survey Data Recorder)

Формат SDR33 (по документации RGS):
- Каждая запись (строка) начинается с 2-значного идентификатора + 2-значного кода источника
- Поля имеют фиксированную ширину 16 символов, начиная с позиции 5

Типы записей:
- 00NM: Заголовок файла
- 01NM: Спецификация прибора
- 02TP/NM: Станция (Nst, X, Y, H, i, Code)
- 03NM: Высота наведения
- 07TP: Ориентирное направление
- 08KI/TP: Координаты
- 09F1/F2: Измерение (Nst, Np, D, B, R, Code)
- 10NM: Имя работы
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


@dataclass
class SDRStation:
    """Станция в формате SDR"""
    point_id: str
    x: Optional[float] = None
    y: Optional[float] = None
    h: Optional[float] = None
    instrument_height: Optional[float] = None
    backsight_point: Optional[str] = None
    backsight_angle: Optional[float] = None
    face_position: str = "NONE"


@dataclass
class SDRObservation:
    """Измерение в формате SDR"""
    obs_type: str
    from_point: str
    to_point: str
    value: float
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    face_position: str = "NONE"
    line_number: int = 0
    raw_data: str = ""


class SDRParser:
    """Парсер формата Sokkia SDR33"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.current_station: Optional[SDRStation] = None
        self.current_setup: Dict[str, Any] = {}
        self.observations: List[SDRObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'
        self.job_name = ""
        self.current_face = "NONE"

    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)
        try:
            raw_data.decode('ascii')
            return 'ascii'
        except UnicodeDecodeError:
            pass
        try:
            text = raw_data.decode('cp1251')
            if any(c in text for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
                return 'cp1251'
        except UnicodeDecodeError:
            pass
        return 'utf-8'

    def _parse_field(self, data: str, start: int, end: int) -> str:
        """Извлечение поля из строки (1-индексация по документации)"""
        # start и end - 1-индексированные позиции
        return data[start-1:end].strip()

    def _parse_float_field(self, data: str, start: int, end: int) -> Optional[float]:
        """Извлечение числового поля из строки"""
        s = self._parse_field(data, start, end)
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    def _parse_header(self, line: str):
        """Парсинг заголовка (00NM)"""
        try:
            version = self._parse_field(line, 5, 20)
            logger.info(f"Заголовок: {version}")
        except Exception as e:
            logger.warning(f"Ошибка парсинга заголовка: {e}")

    def _parse_job_name(self, line: str):
        """Парсинг имени работы (10NM)"""
        try:
            self.job_name = self._parse_field(line, 5, 20)
            logger.info(f"Имя работы: {self.job_name}")
        except Exception as e:
            logger.warning(f"Ошибка парсинга имени работы: {e}")

    def _parse_instrument_setup(self, line: str) -> str:
        """Парсинг установки станции (02TP/NM)
        
        Формат: 02TP Nst(5-20) X(21-36) Y(37-52) H(53-68) i(69-84) Code(85-100)
        """
        try:
            point_id = self._parse_field(line, 5, 20)
            if not point_id:
                return "unknown"
            
            x = self._parse_float_field(line, 21, 36)
            y = self._parse_float_field(line, 37, 52)
            h = self._parse_float_field(line, 53, 68)
            ih = self._parse_float_field(line, 69, 84)
            
            self.current_station = SDRStation(
                point_id=point_id,
                x=x, y=y, h=h,
                instrument_height=ih,
                face_position=self.current_face
            )
            
            if point_id not in self.points:
                self.points[point_id] = {
                    'point_id': point_id,
                    'point_type': 'station',
                    'x': x, 'y': y, 'h': h
                }
            else:
                self.points[point_id].update({'x': x, 'y': y, 'h': h})
            
            if ih is not None:
                self.current_setup['instrument_height'] = ih
            
            return point_id
        except Exception as e:
            logger.warning(f"Ошибка парсинга станции: {e}")
            return "unknown"

    def _parse_target_height(self, line: str):
        """Парсинг высоты наведения (03NM)"""
        try:
            height = self._parse_float_field(line, 5, 20)
            if height is not None:
                self.current_setup['target_height'] = height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты наведения: {e}")

    def _parse_backsight_angle(self, line: str):
        """Парсинг ориентирного направления (07TP)
        
        Формат: 07TP Nst(5-20) Ntr(21-36) A(37-52) R(53-68)
        """
        if not self.current_station:
            return
        try:
            backsight = self._parse_field(line, 21, 36)
            angle = self._parse_float_field(line, 53, 68)
            
            if backsight:
                self.current_station.backsight_point = backsight
                if backsight not in self.points:
                    self.points[backsight] = {
                        'point_id': backsight,
                        'point_type': 'backsight'
                    }
            
            if angle is not None:
                self.current_station.backsight_angle = angle
        except Exception as e:
            logger.warning(f"Ошибка парсинга ориентирного направления: {e}")

    def _parse_coordinates(self, line: str):
        """Парсинг координат (08KI/TP)
        
        Формат: 08KI Np(5-20) X(21-36) Y(37-52) H(53-68) Code(69-84)
        """
        try:
            point_id = self._parse_field(line, 5, 20)
            x = self._parse_float_field(line, 21, 36)
            y = self._parse_float_field(line, 37, 52)
            h = self._parse_float_field(line, 53, 68)
            
            if point_id:
                if point_id not in self.points:
                    self.points[point_id] = {
                        'point_id': point_id,
                        'point_type': 'coordinate',
                        'x': x, 'y': y, 'h': h
                    }
                else:
                    self.points[point_id].update({'x': x, 'y': y, 'h': h})
        except Exception as e:
            logger.warning(f"Ошибка парсинга координат: {e}")

    def _parse_measurement(self, line: str, line_num: int):
        """Парсинг измерения (09F1/F2)
        
        Формат: 09F1 Nst(5-20) Np(21-36) D(37-52) B(53-68) R(69-84) Code(85-100)
        D - наклонное расстояние
        B - вертикальный угол
        R - отсчёт по горизонтальному кругу
        """
        if not self.current_station:
            return None
        
        try:
            # Определяем полуприём
            face = line[2:4].strip()
            if face == 'F1':
                self.current_face = 'CL'
            elif face == 'F2':
                self.current_face = 'CP'
            
            station = self._parse_field(line, 5, 20)
            target = self._parse_field(line, 21, 36)
            slope_dist = self._parse_float_field(line, 37, 52)
            vert_angle = self._parse_float_field(line, 53, 68)
            h_angle = self._parse_float_field(line, 69, 84)
            
            if not target:
                return None
            
            # Добавляем горизонтальное направление
            if h_angle is not None:
                obs = SDRObservation(
                    obs_type='direction',
                    from_point=self.current_station.point_id,
                    to_point=target,
                    value=h_angle,
                    instrument_height=self.current_station.instrument_height,
                    target_height=self.current_setup.get('target_height'),
                    face_position=self.current_face,
                    line_number=line_num,
                    raw_data=line
                )
                self.observations.append(obs)
            
            # Добавляем вертикальный угол
            if vert_angle is not None:
                obs = SDRObservation(
                    obs_type='zenith_angle',
                    from_point=self.current_station.point_id,
                    to_point=target,
                    value=vert_angle,
                    instrument_height=self.current_station.instrument_height,
                    target_height=self.current_setup.get('target_height'),
                    face_position=self.current_face,
                    line_number=line_num,
                    raw_data=line
                )
                self.observations.append(obs)
            
            # Добавляем наклонное расстояние
            if slope_dist is not None and slope_dist > 0:
                obs = SDRObservation(
                    obs_type='slope_distance',
                    from_point=self.current_station.point_id,
                    to_point=target,
                    value=slope_dist,
                    instrument_height=self.current_station.instrument_height,
                    target_height=self.current_setup.get('target_height'),
                    face_position=self.current_face,
                    line_number=line_num,
                    raw_data=line
                )
                self.observations.append(obs)
            
            # Добавляем точку
            if target not in self.points:
                self.points[target] = {
                    'point_id': target,
                    'point_type': 'target',
                    'x': None, 'y': None, 'h': None
                }
        except Exception as e:
            logger.warning(f"Ошибка парсинга измерения в строке {line_num}: {e}")
            self.errors.append({
                'line': line_num,
                'message': str(e),
                'raw_line': line[:100]
            })

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла SDR"""
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()

        logger.info(f"Парсинг файла SDR")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line or len(line) < 4:
                continue

            try:
                record_code = line[:2]
                source_code = line[2:4]
                
                if record_code == '00':
                    self._parse_header(line)
                elif record_code == '01':
                    logger.info(f"Прибор: {line[4:50]}")
                elif record_code == '02':
                    self._parse_instrument_setup(line)
                elif record_code == '03':
                    self._parse_target_height(line)
                elif record_code == '07':
                    self._parse_backsight_angle(line)
                elif record_code == '08':
                    self._parse_coordinates(line)
                elif record_code == '09':
                    self._parse_measurement(line, line_num)
                elif record_code == '10':
                    self._parse_job_name(line)
                # Остальные записи пропускаем

            except Exception as e:
                error_msg = f"Ошибка разбора строки {line_num}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    'line': line_num,
                    'message': error_msg,
                    'raw_line': line[:100]
                })

        result = {
            'format': 'SDR',
            'job_name': self.job_name,
            'encoding': self.encoding,
            'total_lines': len(lines),
            'observations': self.observations,
            'points': list(self.points.values()),
            'num_observations': len(self.observations),
            'num_points': len(self.points),
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }

        logger.info(f"Парсинг завершён: {result['num_observations']} измерений, {result['num_points']} пунктов")
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        stats = {
            'total_observations': len(self.observations),
            'by_type': {},
            'stations': len(self.points),
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }
        for obs in self.observations:
            obs_type = obs.obs_type
            stats['by_type'][obs_type] = stats['by_type'].get(obs_type, 0) + 1
        return stats


if __name__ == "__main__":
    parser = SDRParser()
    from pathlib import Path
    file_path = Path("../test_real_mes/b_g/plan/badgro16093_const.sdr")
    
    if file_path.exists():
        result = parser.parse(file_path)
        print(f"Points: {result['num_points']}")
        print(f"Observations: {result['num_observations']}")
        print("\nFirst 5 points:")
        for p in result['points'][:5]:
            print(f"  {p['point_id']:15}: X={p.get('x', 0)}, Y={p.get('y', 0)}, H={p.get('h', 0)}")
        print("\nFirst 5 observations:")
        for obs in result['observations'][:5]:
            print(f"  {obs.obs_type:20} {obs.from_point:15} -> {obs.to_point:15} = {obs.value:.6f}")
    else:
        print(f"File {file_path} not found!")
