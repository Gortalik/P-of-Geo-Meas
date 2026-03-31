#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Leica GSI (Geodetic Serial Interface)
Поддержка версий 1.0, 8.0, 8.1, 8.2 с распознаванием информационных слов 11-88

Реальный формат GSI (на основе тестовых данных):
- Каждая строка содержит одно или несколько информационных слов
- Формат слова: NNXXXXSDDDDDDDD где:
  - NN - номер слова (2 цифры)
  - XXXX - идентификатор точки (4 символа, может содержать точки)
  - S - знак (+ или -)
  - DDDDDDDD - значение (8 цифр)
  
Основные типы слов:
- 11, 12: Направления (в гонах * 100000)
- 31, 32: Зенитные расстояния/вертикальные углы
- 33: Горизонтальные расстояния
- 83: Высота инструмента
- 87, 88: Высоты инструмента/цели
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
    identifier: Optional[str] = None
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

    # Типы слов GSI для нивелирных данных
    WORD_TYPES = {
        '11': 'direction',
        '12': 'direction',
        '15': 'slope_distance',
        '16': 'horizontal_distance',
        '17': 'vertical_distance',
        '18': 'height_difference',
        '7': 'height_diff',
        '31': 'zenith_angle',
        '32': 'zenith_angle',
        '33': 'horizontal_distance',
        '34': 'slope_distance',
        '35': 'height_difference',
        '36': 'vertical_angle',
        '81': 'point_coordinates',
        '82': 'point_coordinates',
        '83': 'instrument_height',
        '84': 'station',
        '85': 'target',
        '87': 'instrument_height',
        '88': 'target_height',
        '41': 'temperature',
        '42': 'pressure',
        '43': 'humidity',
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
        self.current_point_id: Optional[str] = None
        self.current_target_id: Optional[str] = None

    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)

        # GSI файлы обычно в ASCII или cp1251
        try:
            text = raw_data.decode('ascii')
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
        """Разбор информационного слова GSI
        
        Реальный формат GSI:
        - Позиции 1-2: номер слова (word number)
        - Позиции 3-6: идентификатор точки
        - Позиция 7: знак (+/-)
        - Позиции 8-15: значение (8 цифр)
        
        Примеры:
        - "110002+00R52267" -> word=11, id=0002, value=+00R52267
        - "83..58+00000000" -> word=83, id=..58, value=+00000000
        - "32...8+02293263" -> word=32, id=...8, value=+02293263
        """
        word_str = word_str.strip()
        if len(word_str) < 8:
            return None
        
        try:
            # Извлекаем номер слова (первые 2 символа)
            word_num_str = word_str[:2]
            if not word_num_str.isdigit():
                return None
            word_num = int(word_num_str)
            
            # Извлекаем идентификатор (символы 3-6)
            identifier_str = word_str[2:6]
            
            # Ищем знак и значение
            sign_pos = word_str.find('+', 6)
            if sign_pos == -1:
                sign_pos = word_str.find('-', 6)
            
            if sign_pos == -1:
                return None
            
            sign = word_str[sign_pos]
            value_str = word_str[sign_pos + 1:]
            
            # Очищаем значение от нечисловых символов кроме цифр
            clean_value = ''.join(c for c in value_str if c.isdigit())
            if not clean_value:
                return None
            
            # Определяем количество десятичных знаков в зависимости от номера слова
            decimal_places = 0
            if word_num in [11, 12]:  # Направления (в гонах * 100000)
                decimal_places = 5
            elif word_num in [15, 16, 17, 18, 33, 34, 35]:  # Расстояния (в мм)
                decimal_places = 3
            elif word_num == 7:  # Превышения (в мм)
                decimal_places = 3
            elif word_num in [31, 32, 36]:  # Углы (в гонах * 100000)
                decimal_places = 5
            elif word_num in [81, 82]:  # Координаты
                decimal_places = 3
            elif word_num in [83, 87, 88]:  # Высоты инструмента/цели
                decimal_places = 4
            
            # Преобразуем значение
            value = int(clean_value) / (10 ** decimal_places)
            if sign == '-':
                value = -value
            
            return GSIWord(
                number=word_num,
                sign=sign,
                digits=clean_value,
                decimal_places=decimal_places,
                identifier=identifier_str,
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
        self.current_point_id = station_id

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
        """Обработка слова высоты инструмента (83, 87)"""
        if self.current_station:
            self.current_station.instrument_height = word.value
            self.current_setup['instrument_height'] = word.value

    def _process_target_height(self, word: GSIWord):
        """Обработка слова высоты цели (88)"""
        if self.current_station:
            self.current_setup['target_height'] = word.value

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

    def _get_point_id_from_words(self, words: List[GSIWord]) -> str:
        """Извлечение идентификатора точки из слов"""
        # Ищем первое слово с идентификатором
        for word in words:
            if word.identifier and word.identifier.strip('.'):
                return word.identifier.strip('.')
        return "UNKNOWN"

    def _process_direction(self, words: List[GSIWord], line_num: int):
        """Обработка направления (слова 11/12)"""
        direction_word = None
        for word in words:
            if word.number in [11, 12]:
                direction_word = word
                break

        if not direction_word:
            return

        # Определяем точку стояния и точку визирования
        from_point = self._get_point_id_from_words(words)
        
        # Если есть слово 83 (высота инструмента), это точка стояния
        for word in words:
            if word.number == 83:
                self.current_point_id = from_point
                break
        
        # Определяем точку визирования по идентификатору
        to_point = f"TGT_{direction_word.identifier}" if direction_word.identifier else "UNKNOWN"
        
        # Значение направления в гонах
        direction_gon = direction_word.value

        obs = GSIObservation(
            obs_type='direction',
            from_point=self.current_point_id or from_point,
            to_point=to_point,
            value=direction_gon,
            instrument_height=self.current_setup.get('instrument_height'),
            circle_position=self.current_station.face_position if self.current_station else CirclePosition.NONE,
            reception_number=self.current_station.reception_number if self.current_station else None,
            temperature=self.current_station.temperature if self.current_station else None,
            pressure=self.current_station.pressure if self.current_station else None,
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)
        
        # Добавляем точки
        if self.current_point_id and self.current_point_id not in self.points:
            self.points[self.current_point_id] = {
                'point_id': self.current_point_id,
                'point_type': 'station',
                'x': None,
                'y': None,
                'h': None
            }
        if to_point not in self.points:
            self.points[to_point] = {
                'point_id': to_point,
                'point_type': 'target',
                'x': None,
                'y': None,
                'h': None
            }

    def _process_distance(self, words: List[GSIWord], line_num: int):
        """Обработка расстояния (слова 15/16/17/18/33/34)"""
        distance_word = None
        distance_type = 'slope'

        for word in words:
            if word.number == 15 or word.number == 34:
                distance_word = word
                distance_type = 'slope_distance'
                break
            elif word.number == 16 or word.number == 33:
                distance_word = word
                distance_type = 'horizontal_distance'
                break
            elif word.number == 17:
                distance_word = word
                distance_type = 'vertical_distance'
                break
            elif word.number == 18 or word.number == 35:
                distance_word = word
                distance_type = 'height_difference'
                break

        if not distance_word:
            return

        distance_meters = distance_word.value
        to_point = f"TGT_{distance_word.identifier}" if distance_word.identifier else "UNKNOWN"

        obs = GSIObservation(
            obs_type=distance_type,
            from_point=self.current_point_id or "UNKNOWN",
            to_point=to_point,
            value=distance_meters,
            instrument_height=self.current_setup.get('instrument_height'),
            target_height=self.current_setup.get('target_height'),
            circle_position=self.current_station.face_position if self.current_station else CirclePosition.NONE,
            reception_number=self.current_station.reception_number if self.current_station else None,
            temperature=self.current_station.temperature if self.current_station else None,
            pressure=self.current_station.pressure if self.current_station else None,
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)
        
        if to_point not in self.points:
            self.points[to_point] = {
                'point_id': to_point,
                'point_type': 'target',
                'x': None,
                'y': None,
                'h': None
            }

    def _process_height_diff(self, words: List[GSIWord], line_num: int):
        """Обработка превышения (слово 7 или 35)"""
        height_word = None
        for word in words:
            if word.number == 7 or word.number == 35:
                height_word = word
                break

        if not height_word:
            return

        height_diff = height_word.value
        to_point = f"TGT_{height_word.identifier}" if height_word.identifier else "UNKNOWN"

        obs = GSIObservation(
            obs_type='height_diff',
            from_point=self.current_point_id or "UNKNOWN",
            to_point=to_point,
            value=height_diff,
            instrument_height=self.current_setup.get('instrument_height'),
            target_height=self.current_setup.get('target_height'),
            line_number=line_num,
            raw_words=words
        )

        self.observations.append(obs)
        
        if to_point not in self.points:
            self.points[to_point] = {
                'point_id': to_point,
                'point_type': 'target',
                'x': None,
                'y': None,
                'h': None
            }

    def _process_zenith_angle(self, words: List[GSIWord], line_num: int):
        """Обработка зенитного угла (слова 31/32)"""
        zenith_word = None
        for word in words:
            if word.number in [31, 32]:
                zenith_word = word
                break

        if not zenith_word:
            return

        zenith_angle = zenith_word.value
        to_point = f"TGT_{zenith_word.identifier}" if zenith_word.identifier else "UNKNOWN"

        obs = GSIObservation(
            obs_type='zenith_angle',
            from_point=self.current_point_id or "UNKNOWN",
            to_point=to_point,
            value=zenith_angle,
            instrument_height=self.current_setup.get('instrument_height'),
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

                # Обрабатываем специальные слова
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

                # Определяем тип измерений в строке
                has_direction = any(w.number in [11, 12] for w in words)
                has_distance = any(w.number in [15, 16, 17, 18, 33, 34, 35] for w in words)
                has_height = any(w.number == 7 for w in words)
                has_zenith = any(w.number in [31, 32] for w in words)

                if has_direction:
                    self._process_direction(words, line_num)
                
                if has_zenith:
                    self._process_zenith_angle(words, line_num)

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
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }

        if len(self.errors) > 0:
            logger.error(f"Обнаружено {len(self.errors)} ошибок при парсинге")
            if len(self.errors) > 10:
                logger.error(f"Первые 10 ошибок:")
                for error in self.errors[:10]:
                    logger.error(f"  Строка {error['line']}: {error['message']}")

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
