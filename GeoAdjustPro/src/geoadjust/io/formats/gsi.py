#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Leica GSI (Geodetic Serial Interface)
Поддержка версий 1.0, 8.0, 8.1, 8.2 с распознаванием информационных слов 11-88
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


class CirclePosition(Enum):
    """Положение вертикального круга"""
    LEFT = "CL"
    RIGHT = "CP"
    NONE = "NONE"


class GSIVersion(Enum):
    """Версия формата GSI"""
    V1_0 = "1.0"
    V8_0 = "8.0"
    V8_1 = "8.1"
    V8_2 = "8.2"


@dataclass
class GSIWord:
    """Информационное слово GSI"""
    number: int
    sign: str
    digits: str
    decimal_places: int
    identifier: Optional[int] = None
    value: float = 0.0
    raw: str = ""


@dataclass
class GSIStation:
    """Станция в формате GSI"""
    point_id: str
    instrument_height: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    face_position: CirclePosition = CirclePosition.NONE
    reception_number: Optional[int] = None


@dataclass
class GSIObservation:
    """Измерение в формате GSI"""
    obs_type: str
    from_point: str
    to_point: str
    value: float
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    circle_position: CirclePosition = CirclePosition.NONE
    reception_number: Optional[int] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    line_number: int = 0
    raw_words: List[GSIWord] = field(default_factory=list)


class GSIParser:
    """Парсер формата Leica GSI"""

    WORD_TYPES = {
        '11': 'direction',
        '12': 'direction',
        '15': 'slope_distance',
        '16': 'horizontal_distance',
        '17': 'vertical_distance',
        '18': 'height_difference',
        '7': 'height_diff',
        '84': 'station',
        '85': 'target',
        '87': 'instrument_height',
        '88': 'target_height',
        '41': 'temperature',
        '42': 'pressure',
        '43': 'humidity',
        '81': 'point_coordinates',
        '82': 'point_coordinates',
        '83': 'point_coordinates',
    }

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.version = GSIVersion.V8_0
        self.current_station: Optional[GSIStation] = None
        self.current_setup: Dict[str, Any] = {}
        self.observations: List[GSIObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'

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

    def _detect_version(self, first_lines: List[str]) -> GSIVersion:
        """Определение версии формата GSI"""
        first_content = ' '.join(first_lines[:5]).upper()

        if 'GSI' in first_content or 'LEICA' in first_content:
            return GSIVersion.V8_0
        elif '8.1' in first_content or '8.2' in first_content:
            return GSIVersion.V8_1
        else:
            return GSIVersion.V1_0

    def _parse_gsi_word(self, word_str: str) -> Optional[GSIWord]:
        """Разбор информационного слова GSI"""
        pattern = r'(\d{2})\.(\d{6})([+-])(\d+)'

        match = re.match(pattern, word_str.strip())
        if not match:
            return None

        try:
            word_num = int(match.group(1))
            identifier = int(match.group(2))
            sign = match.group(3)
            digits = match.group(4)

            decimal_places = 0
            if word_num in [11, 12]:
                decimal_places = 5
            elif word_num in [15, 16, 17, 18]:
                decimal_places = 3
            elif word_num == 7:
                decimal_places = 3

            value = float(digits) / (10 ** decimal_places)
            if sign == '-':
                value = -value

            return GSIWord(
                number=word_num,
                sign=sign,
                digits=digits,
                decimal_places=decimal_places,
                identifier=identifier,
                value=value,
                raw=word_str
            )
        except Exception as e:
            logger.debug(f"Ошибка разбора слова '{word_str}': {e}")
            return None

    def _parse_gsi_line(self, line: str) -> List[GSIWord]:
        """Разбор строки на информационные слова"""
        words = []
        word_strings = line.strip().split()

        for word_str in word_strings:
            word = self._parse_gsi_word(word_str)
            if word:
                words.append(word)

        return words

    def _process_station_word(self, word: GSIWord) -> str:
        """Обработка слова объявления станции (84)"""
        station_id = f"STA_{word.identifier}"

        self.current_station = GSIStation(point_id=station_id)

        if station_id not in self.points:
            self.points[station_id] = {
                'point_id': station_id,
                'point_type': 'station',
                'x': None,
                'y': None,
                'h': None
            }

        return station_id

    def _process_instrument_height(self, word: GSIWord):
        """Обработка слова высоты инструмента (87)"""
        if self.current_station:
            self.current_station.instrument_height = word.value / 1000.0
            self.current_setup['instrument_height'] = self.current_station.instrument_height

    def _process_target_height(self, word: GSIWord):
        """Обработка слова высоты цели (88)"""
        if self.current_station:
            self.current_setup['target_height'] = word.value / 1000.0

    def _process_temperature(self, word: GSIWord):
        """Обработка слова температуры (41)"""
        if self.current_station:
            self.current_station.temperature = word.value
            self.current_setup['temperature'] = word.value

    def _process_pressure(self, word: GSIWord):
        """Обработка слова давления (42)"""
        if self.current_station:
            self.current_station.pressure = word.value
            self.current_setup['pressure'] = word.value

    def _process_direction(self, words: List[GSIWord], line_num: int):
        """Обработка направления (слова 11/12)"""
        if not self.current_station:
            return

        direction_word = None
        for word in words:
            if word.number in [11, 12]:
                direction_word = word
                break

        if not direction_word:
            return

        direction_degrees = direction_word.value / 100000.0

        obs = GSIObservation(
            obs_type='direction',
            from_point=self.current_station.point_id,
            to_point=f"TGT_{direction_word.identifier}",
            value=direction_degrees,
            instrument_height=self.current_station.instrument_height,
            circle_position=self.current_station.face_position,
            reception_number=self.current_station.reception_number,
            temperature=self.current_station.temperature,
            pressure=self.current_station.pressure,
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)

    def _process_distance(self, words: List[GSIWord], line_num: int):
        """Обработка расстояния (слова 15/16/17/18)"""
        if not self.current_station:
            return

        distance_word = None
        distance_type = 'slope'

        for word in words:
            if word.number == 15:
                distance_word = word
                distance_type = 'slope'
                break
            elif word.number == 16:
                distance_word = word
                distance_type = 'horizontal'
                break
            elif word.number == 17:
                distance_word = word
                distance_type = 'vertical'
                break
            elif word.number == 18:
                distance_word = word
                distance_type = 'height'
                break

        if not distance_word:
            return

        distance_meters = distance_word.value / 1000.0

        obs = GSIObservation(
            obs_type='distance',
            from_point=self.current_station.point_id,
            to_point=f"TGT_{distance_word.identifier}",
            value=distance_meters,
            instrument_height=self.current_station.instrument_height,
            target_height=self.current_setup.get('target_height'),
            circle_position=self.current_station.face_position,
            reception_number=self.current_station.reception_number,
            temperature=self.current_station.temperature,
            pressure=self.current_station.pressure,
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)

    def _process_height_diff(self, words: List[GSIWord], line_num: int):
        """Обработка превышения (слово 7)"""
        if not self.current_station:
            return

        height_word = None
        for word in words:
            if word.number == 7:
                height_word = word
                break

        if not height_word:
            return

        height_diff = height_word.value / 1000.0

        obs = GSIObservation(
            obs_type='height_diff',
            from_point=self.current_station.point_id,
            to_point=f"TGT_{height_word.identifier}",
            value=height_diff,
            instrument_height=self.current_station.instrument_height,
            target_height=self.current_setup.get('target_height'),
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла GSI"""
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()

        self.version = self._detect_version(lines)

        logger.info(f"Парсинг файла GSI версии {self.version.value}")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                words = self._parse_gsi_line(line)

                if not words:
                    continue

                for word in words:
                    word_type = self.WORD_TYPES.get(str(word.number))

                    if word_type == 'station':
                        self._process_station_word(word)
                    elif word_type == 'instrument_height':
                        self._process_instrument_height(word)
                    elif word_type == 'target_height':
                        self._process_target_height(word)
                    elif word_type == 'temperature':
                        self._process_temperature(word)
                    elif word_type == 'pressure':
                        self._process_pressure(word)
                    elif word_type == 'humidity':
                        if self.current_station:
                            self.current_station.humidity = word.value

                has_direction = any(w.number in [11, 12] for w in words)
                has_distance = any(w.number in [15, 16, 17, 18] for w in words)
                has_height = any(w.number == 7 for w in words)

                if has_direction:
                    self._process_direction(words, line_num)

                if has_distance:
                    self._process_distance(words, line_num)

                if has_height:
                    self._process_height_diff(words, line_num)

            except Exception as e:
                error_msg = f"Ошибка разбора строки {line_num}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    'line': line_num,
                    'message': error_msg,
                    'raw_line': line[:100]
                })

        result = {
            'format': 'GSI',
            'version': self.version.value,
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
    parser = GSIParser()
    file_path = Path("Пример_GSI.txt")

    if file_path.exists():
        result = parser.parse(file_path)
        print(f"Формат: {result['format']} версия {result['version']}")
        print(f"Измерений: {result['num_observations']}")
        print(f"Пунктов: {result['num_points']}")
    else:
        print(f"Файл {file_path} не найден!")
