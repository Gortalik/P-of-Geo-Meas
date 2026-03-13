#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Leica DAT (Data ASCII Transfer)
Поддержка версий v1.0 - v4.0
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


@dataclass
class DATStation:
    """Станция в формате DAT"""
    point_id: str
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    instrument_type: Optional[str] = None
    instrument_serial: Optional[str] = None


@dataclass
class DATObservation:
    """Измерение в формате DAT"""
    obs_type: str
    from_point: str
    to_point: str
    value: float
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    reception_number: Optional[int] = None
    line_number: int = 0
    raw_data: str = ""


class DATParser:
    """Парсер формата Leica DAT"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.current_station: Optional[str] = None
        self.current_setup: Dict[str, Any] = {}
        self.observations: List[DATObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'
        self.version = "unknown"

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

    def _parse_header(self, line: str) -> Dict[str, Any]:
        """Парсинг заголовка файла (запись 00)"""
        try:
            version_match = re.search(r'SDR(\d+)', line)
            if version_match:
                self.version = f"SDR{version_match.group(1)}"

            date_match = re.search(r'(\d{2}-[А-ЯЁ]{3}-\d{2})', line)
            time_match = re.search(r'(\d{2}:\d{2})', line)

            header_info = {
                'version': self.version,
                'date': date_match.group(1) if date_match else None,
                'time': time_match.group(1) if time_match else None
            }

            return header_info
        except Exception as e:
            logger.warning(f"Ошибка парсинга заголовка: {e}")
            return {}

    def _parse_instrument_info(self, line: str) -> Dict[str, Any]:
        """Парсинг информации о приборе (запись 01)"""
        try:
            parts = line[4:].strip().split()

            instrument_info = {
                'model': parts[0] if len(parts) > 0 else 'unknown',
                'serial_number': parts[1] if len(parts) > 1 else 'unknown'
            }

            return instrument_info
        except Exception as e:
            logger.warning(f"Ошибка парсинга информации о приборе: {e}")
            return {}

    def _parse_station(self, line: str) -> str:
        """Парсинг информации о станции (запись 02)"""
        try:
            station_name = line[4:].strip()

            if station_name not in self.points:
                self.points[station_name] = {
                    'point_id': station_name,
                    'point_type': 'station'
                }

            self.current_station = station_name
            self.current_setup = {}

            return station_name
        except Exception as e:
            logger.warning(f"Ошибка парсинга станции: {e}")
            return "unknown"

    def _parse_instrument_height(self, line: str) -> float:
        """Парсинг высоты инструмента (запись 03)"""
        try:
            height_str = line[4:].strip()
            height = float(height_str)

            if self.current_station:
                self.current_setup['instrument_height'] = height

            return height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты инструмента: {e}")
            return 0.0

    def _parse_target_height(self, line: str) -> float:
        """Парсинг высоты цели (запись 04)"""
        try:
            height_str = line[4:].strip()
            height = float(height_str)

            if self.current_station:
                self.current_setup['target_height'] = height

            return height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты цели: {e}")
            return 0.0

    def _parse_measurement(self, line: str, line_num: int) -> Optional[DATObservation]:
        """Парсинг измерения (запись 09)"""
        if not self.current_station:
            return None

        try:
            parts = line[4:].strip().split()

            if len(parts) < 6:
                return None

            from_point = parts[0] + " " + parts[1]
            to_point = parts[2] + " " + parts[3]
            azimuth = float(parts[4])
            zenith = float(parts[5])
            distance = float(parts[6]) if len(parts) > 6 else None

            obs = DATObservation(
                obs_type='direction',
                from_point=self.current_station,
                to_point=to_point,
                value=azimuth,
                instrument_height=self.current_setup.get('instrument_height'),
                target_height=self.current_setup.get('target_height'),
                reception_number=self.current_setup.get('reception_number'),
                line_number=line_num,
                raw_data=line
            )

            if distance is not None:
                obs_distance = DATObservation(
                    obs_type='distance',
                    from_point=self.current_station,
                    to_point=to_point,
                    value=distance,
                    instrument_height=self.current_setup.get('instrument_height'),
                    target_height=self.current_setup.get('target_height'),
                    reception_number=self.current_setup.get('reception_number'),
                    line_number=line_num,
                    raw_data=line
                )
                return obs_distance

            return obs

        except Exception as e:
            logger.warning(f"Ошибка парсинга измерения в строке {line_num}: {e}")
            return None

    def _parse_reception_number(self, line: str) -> int:
        """Парсинг номера приёма (запись 10)"""
        try:
            reception_str = line[4:].strip()
            reception_num = int(reception_str)

            if self.current_station:
                self.current_setup['reception_number'] = reception_num

            return reception_num
        except Exception as e:
            logger.warning(f"Ошибка парсинга номера приёма: {e}")
            return 1

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла DAT"""
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()

        logger.info(f"Парсинг файла DAT")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                if len(line) < 4:
                    continue

                record_id = line[:2]

                if record_id == '00':
                    self._parse_header(line)
                elif record_id == '01':
                    self._parse_instrument_info(line)
                elif record_id == '02':
                    self._parse_station(line)
                elif record_id == '03':
                    self._parse_instrument_height(line)
                elif record_id == '04':
                    self._parse_target_height(line)
                elif record_id == '09':
                    obs = self._parse_measurement(line, line_num)
                    if obs:
                        self.observations.append(obs)
                elif record_id == '10':
                    self._parse_reception_number(line)

            except Exception as e:
                error_msg = f"Ошибка разбора строки {line_num}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    'line': line_num,
                    'message': error_msg,
                    'raw_line': line[:100]
                })

        result = {
            'format': 'DAT',
            'version': self.version,
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
    parser = DATParser()
    file_path = Path("Пример_DAT.txt")

    if file_path.exists():
        result = parser.parse(file_path)
        print(f"Формат: {result['format']} версия {result['version']}")
        print(f"Измерений: {result['num_observations']}")
        print(f"Пунктов: {result['num_points']}")
    else:
        print(f"Файл {file_path} не найден!")
