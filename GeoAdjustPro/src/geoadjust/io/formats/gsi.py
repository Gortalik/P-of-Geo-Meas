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
class GSIObservation:
    """Измерение в формате GSI"""
    obs_type: str
    from_point: str
    to_point: str
    value: float
    station_session_id: str = ""
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    circle_position: CirclePosition = CirclePosition.NONE
    reception_number: Optional[int] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    line_number: int = 0
    raw_words: List[GSIWord] = field(default_factory=list)


@dataclass
class GSIStationSession:
    """Одна установка (сессия) станции.
    
    Каждая установка инструмента создаёт новую сессию,
    даже если имя станции совпадает с предыдущей.
    """
    session_id: str
    station_name: str
    instrument_height: Optional[float] = None
    target_height: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    face_position: CirclePosition = CirclePosition.NONE
    observations: List[GSIObservation] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


class GSIParser:
    """Парсер формата Leica GSI
    
    Ключевые принципы:
    1. Станция объявляется прямо в данных (слово 84 или первое слово с высотой инструмента)
    2. Каждая новая установка = новая сессия с уникальным ID
    3. Измерения группируются по сессиям станций
    4. Одинаковые имена станций НЕ объединяются — это разные сессии
    """

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
        # Нивелирные слова Leica GSI
        '571': 'leveling_backsight_point',
        '572': 'leveling_foresight_point',
        '573': 'leveling_height_diff',
        '574': 'leveling_distance',
    }

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.version = GSIVersion.V8_0
        self.encoding = 'cp1251'
        
        # Сессии станций — каждая установка отдельная сессия
        self.station_sessions: List[GSIStationSession] = []
        self.current_session: Optional[GSIStationSession] = None
        
        # Все измерения (плоский список)
        self.observations: List[GSIObservation] = []
        
        # Все уникальные точки (без дубликатов по имени)
        self.points: Dict[str, Dict[str, Any]] = {}
        
        # Счётчик сессий для генерации уникальных ID
        self._session_counter = 0
        
        # Текущее состояние
        self._current_station_name: Optional[str] = None
        self._current_setup: Dict[str, Any] = {}
        self._has_station_declaration = False

    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)

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
        
        Поддержка 2-значных и 3-значных номеров слов.
        Для нивелирных слов Leica (571-574) используется 3-значный номер.
        """
        word_str = word_str.strip()
        if len(word_str) < 8:
            return None
        
        try:
            # Определяем длину номера слова (2 или 3 цифры)
            # Для слов 57x используем 3 цифры
            if word_str[:3].isdigit() and word_str[:3].startswith('57'):
                word_num_str = word_str[:3]
                identifier_start = 3
            else:
                word_num_str = word_str[:2]
                identifier_start = 2
            
            if not word_num_str.isdigit():
                return None
            word_num = int(word_num_str)
            
            identifier_str = word_str[identifier_start:identifier_start+4]
            
            sign_pos = word_str.find('+', identifier_start+4)
            if sign_pos == -1:
                sign_pos = word_str.find('-', identifier_start+4)
            
            if sign_pos == -1:
                return None
            
            sign = word_str[sign_pos]
            value_str = word_str[sign_pos + 1:]
            
            clean_value = ''.join(c for c in value_str if c.isdigit())
            if not clean_value:
                return None
            
            decimal_places = 0
            if word_num in [11, 12]:
                decimal_places = 5
            elif word_num in [15, 16, 17, 18, 33, 34, 35]:
                decimal_places = 3
            elif word_num == 7:
                decimal_places = 3
            elif word_num in [31, 32, 36]:
                decimal_places = 5
            elif word_num in [81, 82]:
                decimal_places = 3
            elif word_num in [83, 87, 88]:
                decimal_places = 4
            elif word_num in [571, 572, 573, 574]:
                # Нивелирные слова: 573 - превышение (4 знака после запятой), 574 - расстояние
                if word_num == 573:
                    decimal_places = 4
                elif word_num == 574:
                    decimal_places = 4
                else:
                    decimal_places = 0
            
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

    def _get_point_id_from_words(self, words: List[GSIWord]) -> str:
        """Извлечение идентификатора точки из слов"""
        for word in words:
            if word.identifier and word.identifier.strip('.'):
                return word.identifier.strip('.')
        return "UNKNOWN"

    def _create_new_session(self, station_name: str, line_num: int):
        """Создание новой сессии станции.
        
        Каждая установка инструмента = новая сессия,
        даже если station_name совпадает с предыдущей.
        """
        self._session_counter += 1
        session_id = f"{station_name}_S{self._session_counter:04d}"
        
        self.current_session = GSIStationSession(
            session_id=session_id,
            station_name=station_name,
            line_start=line_num
        )
        
        self.station_sessions.append(self.current_session)
        self._current_station_name = station_name
        self._has_station_declaration = True
        
        # Обновляем конец предыдущей сессии
        if len(self.station_sessions) > 1:
            self.station_sessions[-2].line_end = line_num - 1
        
        # Добавляем точку станции в points (если ещё нет)
        if station_name not in self.points:
            self.points[station_name] = {
                'point_id': station_name,
                'point_type': 'station',
                'x': None,
                'y': None,
                'h': None
            }
        
        logger.debug(f"Создана сессия станции: {session_id} (станция: {station_name})")

    def _process_station_word(self, word: GSIWord):
        """Обработка слова объявления станции (84)"""
        station_name = word.identifier.strip('.') if word.identifier else f"STA_{self._session_counter + 1}"
        
        # Всегда создаём новую сессию при объявлении станции
        self._create_new_session(station_name, word.raw)
        self._current_setup = {}

    def _process_instrument_height(self, word: GSIWord, line_num: int):
        """Обработка слова высоты инструмента (83, 87)
        
        Если нет активной сессии — создаём новую.
        Высота инструмента = признак начала новой установки.
        """
        if not self.current_session:
            # Определяем имя станции из идентификатора
            station_name = word.identifier.strip('.') if word.identifier else f"STA_{self._session_counter + 1}"
            self._create_new_session(station_name, line_num)
        
        self.current_session.instrument_height = word.value
        self._current_setup['instrument_height'] = word.value

    def _process_target_height(self, word: GSIWord):
        """Обработка слова высоты цели (88)"""
        if self.current_session:
            self.current_session.target_height = word.value
        self._current_setup['target_height'] = word.value

    def _process_temperature(self, word: GSIWord):
        """Обработка слова температуры (41)"""
        if self.current_session:
            self.current_session.temperature = word.value
        self._current_setup['temperature'] = word.value

    def _process_pressure(self, word: GSIWord):
        """Обработка слова давления (42)"""
        if self.current_session:
            self.current_session.pressure = word.value
        self._current_setup['pressure'] = word.value

    def _add_observation(self, obs_type: str, from_point: str, to_point: str, 
                         value: float, line_num: int, words: List[GSIWord]):
        """Добавление измерения в текущую сессию"""
        if not self.current_session:
            station_name = from_point if from_point != "UNKNOWN" else f"STA_{self._session_counter + 1}"
            self._create_new_session(station_name, line_num)
        
        obs = GSIObservation(
            obs_type=obs_type,
            from_point=from_point,
            to_point=to_point,
            value=value,
            station_session_id=self.current_session.session_id,
            instrument_height=self.current_session.instrument_height,
            target_height=self.current_session.target_height,
            circle_position=self.current_session.face_position,
            temperature=self.current_session.temperature,
            pressure=self.current_session.pressure,
            line_number=line_num,
            raw_words=words
        )
        
        self.observations.append(obs)
        self.current_session.observations.append(obs)
        
        # Обновляем конец сессии
        self.current_session.line_end = line_num
        
        # Добавляем целевую точку
        if to_point not in self.points:
            self.points[to_point] = {
                'point_id': to_point,
                'point_type': 'target',
                'x': None,
                'y': None,
                'h': None
            }

    def _process_direction(self, words: List[GSIWord], line_num: int):
        """Обработка направления (слова 11/12)"""
        direction_word = None
        for word in words:
            if word.number in [11, 12]:
                direction_word = word
                break

        if not direction_word:
            return

        from_point = self._current_station_name or self._get_point_id_from_words(words)
        to_point = direction_word.identifier.strip('.') if direction_word.identifier else "UNKNOWN"
        
        self._add_observation(
            obs_type='direction',
            from_point=from_point,
            to_point=to_point,
            value=direction_word.value,
            line_num=line_num,
            words=words
        )

    def _process_distance(self, words: List[GSIWord], line_num: int):
        """Обработка расстояния (слова 15/16/17/18/33/34)"""
        distance_word = None
        distance_type = 'slope_distance'

        for word in words:
            if word.number in [15, 34]:
                distance_word = word
                distance_type = 'slope_distance'
                break
            elif word.number in [16, 33]:
                distance_word = word
                distance_type = 'horizontal_distance'
                break
            elif word.number == 17:
                distance_word = word
                distance_type = 'vertical_distance'
                break
            elif word.number in [18, 35]:
                distance_word = word
                distance_type = 'height_difference'
                break

        if not distance_word:
            return

        from_point = self._current_station_name or "UNKNOWN"
        to_point = distance_word.identifier.strip('.') if distance_word.identifier else "UNKNOWN"
        
        self._add_observation(
            obs_type=distance_type,
            from_point=from_point,
            to_point=to_point,
            value=distance_word.value,
            line_num=line_num,
            words=words
        )

    def _process_height_diff(self, words: List[GSIWord], line_num: int):
        """Обработка превышения (слово 7 или 35)"""
        height_word = None
        for word in words:
            if word.number in [7, 35]:
                height_word = word
                break

        if not height_word:
            return

        from_point = self._current_station_name or "UNKNOWN"
        to_point = height_word.identifier.strip('.') if height_word.identifier else "UNKNOWN"
        
        self._add_observation(
            obs_type='height_diff',
            from_point=from_point,
            to_point=to_point,
            value=height_word.value,
            line_num=line_num,
            words=words
        )

    def _process_zenith_angle(self, words: List[GSIWord], line_num: int):
        """Обработка зенитного угла (слова 31/32)"""
        zenith_word = None
        for word in words:
            if word.number in [31, 32]:
                zenith_word = word
                break

        if not zenith_word:
            return

        from_point = self._current_station_name or "UNKNOWN"
        to_point = zenith_word.identifier.strip('.') if zenith_word.identifier else "UNKNOWN"
        
        self._add_observation(
            obs_type='zenith_angle',
            from_point=from_point,
            to_point=to_point,
            value=zenith_word.value,
            line_num=line_num,
            words=words
        )

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла GSI"""
        # Сброс состояния
        self.station_sessions = []
        self.observations = []
        self.points = {}
        self.current_session = None
        self._session_counter = 0
        self._current_station_name = None
        self._current_setup = {}
        self._has_station_declaration = False
        self.errors = []
        self.warnings = []
        
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
                        self._process_instrument_height(word, line_num)
                    elif word_type == 'target_height':
                        self._process_target_height(word)
                    elif word_type == 'temperature':
                        self._process_temperature(word)
                    elif word_type == 'pressure':
                        self._process_pressure(word)
                    elif word_type == 'humidity':
                        if self.current_session:
                            self.current_session.humidity = word.value

                # Определяем тип измерений в строке
                has_direction = any(w.number in [11, 12] for w in words)
                has_distance = any(w.number in [15, 16, 17, 18, 33, 34, 35] for w in words)
                has_height = any(w.number == 7 for w in words)
                has_zenith = any(w.number in [31, 32] for w in words)
                has_leveling = any(w.number in [571, 572, 573, 574] for w in words)

                if has_direction:
                    self._process_direction(words, line_num)
                
                if has_zenith:
                    self._process_zenith_angle(words, line_num)

                if has_distance:
                    self._process_distance(words, line_num)

                if has_height:
                    self._process_height_diff(words, line_num)
                
                if has_leveling:
                    self._process_leveling(words, line_num)

            except Exception as e:
                error_msg = f"Ошибка разбора строки {line_num}: {str(e)}"
                logger.error(error_msg)
                self.errors.append({
                    'line': line_num,
                    'message': error_msg,
                    'raw_line': line[:100]
                })

        # Закрываем последнюю сессию
        if self.current_session:
            self.current_session.line_end = len(lines)

        result = {
            'format': 'GSI',
            'version': self.version.value,
            'encoding': self.encoding,
            'total_lines': len(lines),
            'observations': self.observations,
            'station_sessions': self.station_sessions,
            'points': list(self.points.values()),
            'num_observations': len(self.observations),
            'num_points': len(self.points),
            'num_station_sessions': len(self.station_sessions),
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

        logger.info(f"Парсинг завершён: {result['num_observations']} измерений, "
                    f"{result['num_points']} пунктов, {result['num_station_sessions']} сессий станций")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по распарсенным данным"""
        stats = {
            'total_observations': len(self.observations),
            'by_type': {},
            'num_station_sessions': len(self.station_sessions),
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
        print(f"Сессий станций: {result['num_station_sessions']}")
        for session in result['station_sessions']:
            print(f"  Сессия: {session.session_id} — {len(session.observations)} измерений")
    else:
        print(f"Файл {file_path} не найден!")
