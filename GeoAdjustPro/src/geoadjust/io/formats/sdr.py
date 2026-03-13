#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Sokkia SDR (Survey Data Recorder)
Поддержка версий SDR2x и SDR33

Формат файла SDR:
- Каждая строка начинается с двухзначного кода записи
- Структура: код записи + данные
- Пример: "01JOB NAME"

Коды записей:
- 01: Имя работы
- 02: Установка прибора
- 03: Задняя визирная точка
- 04: Передняя визирная точка
- 05: Координаты пункта
- 07: Угол на заднюю точку (ориентирное направление)
- 08: Горизонтальный угол
- 09: Наклонное расстояние
- 10: Вертикальный угол
- 11: Горизонтальное расстояние
- 12: Превышение
- 84: Начало станции
- 85: Начало полуприёма (КЛ)
- 86: Окончание полуприёма (КП)
- 87: Начало кругового приёма
- 88: Окончание кругового приёма
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


class SDRRecordType(Enum):
    """Тип записи в файле SDR"""
    JOB_NAME = "01"
    INSTRUMENT_SETUP = "02"
    BACKSIGHT_SETUP = "03"
    FORESIGHT_SETUP = "04"
    COORDINATES = "05"
    BACKSIGHT_ANGLE = "07"
    HORIZONTAL_ANGLE = "08"
    SLOPE_DISTANCE = "09"
    VERTICAL_ANGLE = "10"
    HORIZONTAL_DISTANCE = "11"
    ELEVATION_DIFFERENCE = "12"
    START_STATION = "84"
    START_FACE = "85"
    END_FACE = "86"
    START_CIRCLE = "87"
    END_CIRCLE = "88"


@dataclass
class SDRStation:
    """Станция в формате SDR"""
    point_id: str
    instrument_height: Optional[float] = None
    backsight_point: Optional[str] = None
    backsight_angle: Optional[float] = None
    face_position: str = "NONE"  # CL, CP, or NONE


@dataclass
class SDRObservation:
    """Измерение в формате SDR"""
    obs_type: str  # 'angle', 'distance', 'height_diff'
    from_point: str
    to_point: str
    value: float
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    face_position: str = "NONE"
    line_number: int = 0
    raw_data: str = ""


class SDRParser:
    """Парсер формата Sokkia SDR"""

    RECORD_TYPES = {
        '01': 'job_name',
        '02': 'instrument_setup',
        '03': 'backsight_setup',
        '04': 'foresight_setup',
        '05': 'coordinates',
        '07': 'backsight_angle',
        '08': 'horizontal_angle',
        '09': 'slope_distance',
        '10': 'vertical_angle',
        '11': 'horizontal_distance',
        '12': 'elevation_difference',
        '84': 'start_station',
        '85': 'start_face',
        '86': 'end_face',
        '87': 'start_circle',
        '88': 'end_circle'
    }

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.current_station: Optional[SDRStation] = None
        self.current_setup: Dict[str, Any] = {}
        self.observations: List[SDRObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'
        self.job_name = ""

    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)

        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']

        if encoding in ['windows-1251', 'cp1251'] or (encoding == 'ascii' and confidence < 0.9):
            try:
                text = raw_data.decode('cp1251')
                if any(c in text for c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
                    return 'cp1251'
            except:
                pass

        if encoding is None or confidence < 0.6:
            return 'utf-8'

        return encoding.lower()

    def _parse_job_name(self, line: str):
        """Парсинг имени работы (код 01)"""
        try:
            self.job_name = line[2:].strip()
            logger.info(f"Имя работы: {self.job_name}")
        except Exception as e:
            logger.warning(f"Ошибка парсинга имени работы: {e}")

    def _parse_instrument_setup(self, line: str) -> str:
        """Парсинг установки прибора (код 02)"""
        try:
            parts = [p.strip() for p in line[2:].split(',') if p.strip()]

            if len(parts) < 1:
                raise ValueError("Недостаточно данных для установки прибора")

            station_id = parts[0]

            self.current_station = SDRStation(
                point_id=station_id,
                instrument_height=float(parts[2]) if len(parts) > 2 and parts[2] else None,
                backsight_point=None,
                backsight_angle=None,
                face_position="NONE"
            )

            if station_id not in self.points:
                self.points[station_id] = {
                    'point_id': station_id,
                    'point_type': 'station',
                    'x': None,
                    'y': None,
                    'h': None
                }

            if self.current_station.instrument_height:
                self.current_setup['instrument_height'] = self.current_station.instrument_height

            return station_id

        except Exception as e:
            logger.warning(f"Ошибка парсинга установки прибора: {e}")
            return "unknown"

    def _parse_backsight_setup(self, line: str) -> str:
        """Парсинг задней визирной точки (код 03)"""
        try:
            parts = [p.strip() for p in line[2:].split(',') if p.strip()]

            if len(parts) < 1:
                raise ValueError("Недостаточно данных для задней точки")

            backsight_id = parts[0]

            if self.current_station:
                self.current_station.backsight_point = backsight_id

            if backsight_id not in self.points:
                self.points[backsight_id] = {
                    'point_id': backsight_id,
                    'point_type': 'backsight'
                }

            return backsight_id

        except Exception as e:
            logger.warning(f"Ошибка парсинга задней точки: {e}")
            return "unknown"

    def _parse_coordinates(self, line: str):
        """Парсинг координат пункта (код 05)"""
        try:
            parts = [p.strip() for p in line[2:].split(',') if p.strip()]

            if len(parts) < 5:
                raise ValueError("Недостаточно данных для координат")

            point_id = parts[0]
            northing = float(parts[2])
            easting = float(parts[3])
            elevation = float(parts[4]) if len(parts) > 4 and parts[4] else None

            if point_id not in self.points:
                self.points[point_id] = {
                    'point_id': point_id,
                    'point_type': 'coordinate',
                    'x': easting,
                    'y': northing,
                    'h': elevation
                }
            else:
                self.points[point_id].update({
                    'x': easting,
                    'y': northing,
                    'h': elevation
                })

        except Exception as e:
            logger.warning(f"Ошибка парсинга координат: {e}")

    def _parse_angle(self, line: str, angle_type: str, line_num: int) -> Optional[SDRObservation]:
        """Парсинг углового измерения"""
        if not self.current_station:
            return None

        try:
            angle_str = line[2:].strip()
            angle_degrees = float(angle_str)

            obs = SDRObservation(
                obs_type=angle_type,
                from_point=self.current_station.point_id,
                to_point=self.current_station.backsight_point or "unknown",
                value=angle_degrees,
                instrument_height=self.current_station.instrument_height,
                face_position=self.current_station.face_position,
                line_number=line_num,
                raw_data=line
            )

            return obs

        except Exception as e:
            logger.warning(f"Ошибка парсинга угла в строке {line_num}: {e}")
            return None

    def _parse_distance(self, line: str, distance_type: str, line_num: int) -> Optional[SDRObservation]:
        """Парсинг линейного измерения"""
        if not self.current_station:
            return None

        try:
            distance_str = line[2:].strip()
            distance_meters = float(distance_str)

            obs = SDRObservation(
                obs_type=distance_type,
                from_point=self.current_station.point_id,
                to_point=self.current_station.backsight_point or "unknown",
                value=distance_meters,
                instrument_height=self.current_station.instrument_height,
                face_position=self.current_station.face_position,
                line_number=line_num,
                raw_data=line
            )

            return obs

        except Exception as e:
            logger.warning(f"Ошибка парсинга расстояния в строке {line_num}: {e}")
            return None

    def _parse_height_difference(self, line: str, line_num: int) -> Optional[SDRObservation]:
        """Парсинг превышения"""
        if not self.current_station:
            return None

        try:
            height_str = line[2:].strip()
            height_diff = float(height_str)

            obs = SDRObservation(
                obs_type='height_diff',
                from_point=self.current_station.point_id,
                to_point=self.current_station.backsight_point or "unknown",
                value=height_diff,
                instrument_height=self.current_station.instrument_height,
                line_number=line_num,
                raw_data=line
            )

            return obs

        except Exception as e:
            logger.warning(f"Ошибка парсинга превышения в строке {line_num}: {e}")
            return None

    def _parse_start_face(self, line: str):
        """Парсинг начала полуприёма (КЛ)"""
        if self.current_station:
            self.current_station.face_position = "CL"

    def _parse_end_face(self, line: str):
        """Парсинг окончания полуприёма (КП)"""
        if self.current_station:
            self.current_station.face_position = "CP"

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсинг файла SDR с полной обработкой структуры
        """
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()

        logger.info(f"Парсинг файла SDR")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                if len(line) < 2:
                    continue

                record_code = line[:2]
                record_type = self.RECORD_TYPES.get(record_code)

                if not record_type:
                    continue

                if record_type == 'job_name':
                    self._parse_job_name(line)

                elif record_type == 'instrument_setup':
                    self._parse_instrument_setup(line)

                elif record_type == 'backsight_setup':
                    self._parse_backsight_setup(line)

                elif record_type == 'foresight_setup':
                    self._parse_backsight_setup(line)

                elif record_type == 'coordinates':
                    self._parse_coordinates(line)

                elif record_type == 'backsight_angle':
                    obs = self._parse_angle(line, 'backsight_angle', line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'horizontal_angle':
                    obs = self._parse_angle(line, 'horizontal_angle', line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'vertical_angle':
                    obs = self._parse_angle(line, 'vertical_angle', line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'slope_distance':
                    obs = self._parse_distance(line, 'slope_distance', line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'horizontal_distance':
                    obs = self._parse_distance(line, 'horizontal_distance', line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'elevation_difference':
                    obs = self._parse_height_difference(line, line_num)
                    if obs:
                        self.observations.append(obs)

                elif record_type == 'start_station':
                    self.current_setup = {}

                elif record_type == 'start_face':
                    self._parse_start_face(line)

                elif record_type == 'end_face':
                    self._parse_end_face(line)

                elif record_type == 'start_circle':
                    if self.current_station:
                        self.current_station.face_position = "CL"

                elif record_type == 'end_circle':
                    if self.current_station:
                        self.current_station.face_position = "NONE"

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
            'warnings': self.warnings
        }

        logger.info(f"Парсинг завершён: {result['num_observations']} измерений, {result['num_points']} пунктов")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по распарсенным данным"""
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
    file_path = Path("Пример_SDR.txt")

    if file_path.exists():
        result = parser.parse(file_path)

        print(f"\n{'=' * 60}")
        print(f"Результаты парсинга файла {file_path.name}")
        print(f"{'=' * 60}")
        print(f"Формат: {result['format']}")
        print(f"Имя работы: {result['job_name']}")
        print(f"Кодировка: {result['encoding']}")
        print(f"Всего строк: {result['total_lines']}")
        print(f"Измерений: {result['num_observations']}")
        print(f"Пунктов: {result['num_points']}")
        print(f"Ошибок: {len(result['errors'])}")

        print(f"\nСтатистика по типам измерений:")
        stats = parser.get_statistics()
        for obs_type, count in stats['by_type'].items():
            print(f"  {obs_type}: {count}")

        if result['observations']:
            print(f"\nПервые 5 измерений:")
            for i, obs in enumerate(result['observations'][:5], 1):
                print(f"  {i}. {obs.obs_type:20} {obs.from_point} → {obs.to_point:10} = {obs.value:.6f}")

        if result['errors']:
            print(f"\nОшибки парсинга:")
            for error in result['errors'][:5]:
                print(f"  Строка {error['line']}: {error['message']}")
    else:
        print(f"Файл {file_path} не найден!")
