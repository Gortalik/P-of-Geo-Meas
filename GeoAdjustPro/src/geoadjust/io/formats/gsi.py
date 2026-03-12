#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Leica GSI (Geodetic Serial Interface)
Поддержка версий 1.0, 8.0, 8.1, 8.2 с распознаванием информационных слов 11-88

Формат строки:
- Каждая строка содержит одно или несколько информационных слов
- Информационное слово: 2 цифры (номер слова) + 6-16 цифр (значение)
- Пример: "11.100000+0000000 84.110000+2458721345000"

Информационные слова:
- 11/12: направления
- 15/16/17/18: расстояния (наклонное, горизонтальное, вертикальное, высота)
- 7: превышения
- 84: объявление станции
- 85: объявление цели
- 87: высота инструмента
- 88: высота цели/отражателя
- 41-49: атмосферные параметры
- 81-83: координаты пунктов
- 85/86: начало/окончание полуприёма (КЛ/КП)
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


class CirclePosition(Enum):
    """Положение вертикального круга"""
    LEFT = "CL"  # Круг слева
    RIGHT = "CP"  # Круг справа
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
    number: int  # Номер слова (11, 12, 15, 84 и т.д.)
    sign: str  # Знак значения (+/-)
    digits: str  # Цифровое значение
    decimal_places: int  # Число знаков после запятой
    identifier: Optional[int] = None  # Идентификатор (если есть)
    value: float = 0.0  # Расшифрованное значение
    raw: str = ""  # Исходная строка слова


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
    obs_type: str  # 'direction', 'distance', 'height_diff'
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
    """Парсер формата Leica GSI с полной обработкой структуры"""
    
    # Словарь информационных слов
    WORD_TYPES = {
        '11': 'direction',  # Направление (градусы)
        '12': 'direction',  # Направление (грады)
        '15': 'slope_distance',  # Наклонное расстояние
        '16': 'horizontal_distance',  # Горизонтальное расстояние
        '17': 'vertical_distance',  # Вертикальное расстояние
        '18': 'height_difference',  # Превышение
        '7': 'height_diff',  # Превышение (альтернативный формат)
        '84': 'station',  # Объявление станции
        '85': 'target',  # Объявление цели
        '87': 'instrument_height',  # Высота инструмента
        '88': 'target_height',  # Высота цели/отражателя
        '41': 'temperature',  # Температура
        '42': 'pressure',  # Давление
        '43': 'humidity',  # Влажность
        '81': 'point_coordinates',  # Координаты пункта
        '82': 'point_coordinates',  # Координаты пункта
        '83': 'point_coordinates',  # Координаты пункта
        '85': 'start_face',  # Начало полуприёма (КЛ)
        '86': 'end_face',  # Окончание полуприёма (КП)
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
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
        
        # Коррекция для типичных геодезических форматов
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
        """
        Разбор информационного слова GSI
        
        Формат слова:
        - Версия 1.0: 2 цифры + точка + 6-16 цифр
        - Версия 8.0+: 2 цифры + точка + 6-16 цифр + знак + значение
        
        Примеры:
        - "11.100000+0000000" - направление 0°
        - "84.110000+2458721345000" - станция с координатами
        """
        # Регулярное выражение для поиска информационных слов
        # Формат: номер.идентификатор+значение или номер.идентификатор-значение
        pattern = r'(\d{2})\.(\d{6})([+-])(\d+)'
        
        match = re.match(pattern, word_str.strip())
        if not match:
            return None
        
        try:
            word_num = int(match.group(1))
            identifier = int(match.group(2))
            sign = match.group(3)
            digits = match.group(4)
            
            # Определение числа знаков после запятой
            decimal_places = 0
            if word_num in [11, 12]:  # Направления
                decimal_places = 5  # Секунды с точностью до 0.00001"
            elif word_num in [15, 16, 17, 18]:  # Расстояния
                decimal_places = 3  # Миллиметры
            elif word_num == 7:  # Превышения
                decimal_places = 3
            
            # Расчёт значения
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
        
        # Разделение строки на слова (разделитель - пробел)
        word_strings = line.strip().split()
        
        for word_str in word_strings:
            word = self._parse_gsi_word(word_str)
            if word:
                words.append(word)
        
        return words
    
    def _process_station_word(self, word: GSIWord) -> str:
        """Обработка слова объявления станции (84)"""
        # Идентификатор станции закодирован в поле идентификатора
        station_id = f"STA_{word.identifier}"
        
        # Создание станции
        self.current_station = GSIStation(
            point_id=station_id,
            instrument_height=None,
            temperature=None,
            pressure=None,
            humidity=None,
            face_position=CirclePosition.NONE,
            reception_number=None
        )
        
        # Добавление пункта в список
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
            # Значение в метрах
            self.current_station.instrument_height = word.value / 1000.0
            self.current_setup['instrument_height'] = self.current_station.instrument_height
    
    def _process_target_height(self, word: GSIWord):
        """Обработка слова высоты цели (88)"""
        if self.current_station:
            # Значение в метрах
            self.current_setup['target_height'] = word.value / 1000.0
    
    def _process_temperature(self, word: GSIWord):
        """Обработка слова температуры (41)"""
        if self.current_station:
            # Значение в градусах Цельсия
            self.current_station.temperature = word.value
            self.current_setup['temperature'] = word.value
    
    def _process_pressure(self, word: GSIWord):
        """Обработка слова давления (42)"""
        if self.current_station:
            # Значение в гПа
            self.current_station.pressure = word.value
            self.current_setup['pressure'] = word.value
    
    def _process_direction(self, words: List[GSIWord], line_num: int):
        """Обработка направления (слова 11/12)"""
        if not self.current_station:
            return
        
        # Поиск слова направления
        direction_word = None
        for word in words:
            if word.number in [11, 12]:
                direction_word = word
                break
        
        if not direction_word:
            return
        
        # Расчёт направления в градусах
        direction_degrees = direction_word.value / 100000.0  # из секунд в градусы
        
        # Создание измерения
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
        
        # Поиск слова расстояния
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
        
        # Расстояние в метрах
        distance_meters = distance_word.value / 1000.0
        
        # Создание измерения
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
        
        # Поиск слова превышения
        height_word = None
        for word in words:
            if word.number == 7:
                height_word = word
                break
        
        if not height_word:
            return
        
        # Превышение в метрах
        height_diff = height_word.value / 1000.0
        
        # Создание измерения
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
        """
        Парсинг файла GSI с полной обработкой структуры:
        - Распознавание станций по словам 84-88
        - Обработка направлений (слово 11/12)
        - Обработка расстояний (слово 15/16/17/18)
        - Обработка превышений (слово 7)
        - Высоты инструмента/цели (слова 87/88)
        - Атмосферные параметры (слова 41-49)
        """
        # Определение кодировки
        self.encoding = self._detect_encoding(file_path)
        
        # Чтение файла
        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()
        
        # Определение версии формата
        self.version = self._detect_version(lines)
        
        logger.info(f"Парсинг файла GSI версии {self.version.value}")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")
        
        # Обработка строк
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Разбор строки на информационные слова
                words = self._parse_gsi_line(line)
                
                if not words:
                    continue
                
                # Обработка каждого слова в строке
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
                    
                    elif word_type == 'start_face':
                        if self.current_station:
                            self.current_station.face_position = CirclePosition.LEFT
                    
                    elif word_type == 'end_face':
                        if self.current_station:
                            self.current_station.face_position = CirclePosition.RIGHT
                
                # Обработка измерений (направления, расстояния, превышения)
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
        
        # Формирование результата
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
        
        # Статистика по типам измерений
        for obs in self.observations:
            obs_type = obs.obs_type
            stats['by_type'][obs_type] = stats['by_type'].get(obs_type, 0) + 1
        
        return stats


# Пример использования
if __name__ == "__main__":
    # Пример использования парсера
    parser = GSIParser()
    
    # Путь к файлу (замените на ваш путь)
    file_path = Path("Пример_GSI.txt")
    
    if file_path.exists():
        result = parser.parse(file_path)
        
        print(f"\n{'='*60}")
        print(f"Результаты парсинга файла {file_path.name}")
        print(f"{'='*60}")
        print(f"Формат: {result['format']} версия {result['version']}")
        print(f"Кодировка: {result['encoding']}")
        print(f"Всего строк: {result['total_lines']}")
        print(f"Измерений: {result['num_observations']}")
        print(f"Пунктов: {result['num_points']}")
        print(f"Ошибок: {result['errors']}")
        
        print(f"\nСтатистика по типам измерений:")
        stats = parser.get_statistics()
        for obs_type, count in stats['by_type'].items():
            print(f"  {obs_type}: {count}")
        
        # Вывод первых 5 измерений
        if result['observations']:
            print(f"\nПервые 5 измерений:")
            for i, obs in enumerate(result['observations'][:5], 1):
                print(f"  {i}. {obs.obs_type:15} {obs.from_point} → {obs.to_point:10} = {obs.value:.6f}")
        
        # Вывод ошибок
        if result['errors']:
            print(f"\nОшибки парсинга:")
            for error in result['errors'][:5]:  # Первые 5 ошибок
                print(f"  Строка {error['line']}: {error['message']}")
    else:
        print(f"Файл {file_path} не найден!")
