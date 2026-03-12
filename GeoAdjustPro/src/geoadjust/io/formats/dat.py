#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Leica DAT (Data ASCII Transfer)
Поддержка версий v1.0 - v4.0

Формат файла DAT:
- Каждая строка начинается с идентификатора записи (2 символа)
- Структура: идентификатор + данные + разделитель
- Пример: "00NMul.POKLONNAYA"

Идентификаторы записей:
- 00: Заголовок файла
- 01: Информация о приборе
- 02: Информация о станции
- 03: Высота инструмента
- 04: Высота цели
- 09: Измерение (направление, расстояние)
- 10: Номер приёма
- 50: Конец измерения
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import chardet

logger = logging.getLogger(__name__)


class DATRecordType(Enum):
    """Тип записи в файле DAT"""
    HEADER = "00"
    INSTRUMENT = "01"
    STATION = "02"
    INSTRUMENT_HEIGHT = "03"
    TARGET_HEIGHT = "04"
    MEASUREMENT = "09"
    RECEPTION_NUMBER = "10"
    END_MEASUREMENT = "50"


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
    obs_type: str  # 'direction', 'distance', 'azimuth'
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
        self.errors = []
        self.warnings = []
        self.current_station: Optional[str] = None
        self.current_setup: Dict[str, Any] = {}
        self.observations: List[DATObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'
        self.version = "unknown"
        self.header_info: Dict[str, Any] = {}
        self.instrument_info: Dict[str, Any] = {}
    
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
    
    def _parse_header(self, line: str) -> Dict[str, Any]:
        """Парсинг заголовка файла (запись 00)"""
        # Формат заголовка: 00NM<версия><серийный номер><дата><время><параметры>
        # Пример: 00NMSDR33 V04-04.02 25-ФЕВ-02 18:20 111111
        
        try:
            # Извлечение версии
            version_match = re.search(r'SDR(\d+)', line)
            if version_match:
                self.version = f"SDR{version_match.group(1)}"
            
            # Извлечение даты и времени
            date_match = re.search(r'(\d{2}-[А-ЯЁ]{3}-\d{2})', line)
            time_match = re.search(r'(\d{2}:\d{2})', line)
            
            header_info = {
                'version': self.version,
                'date': date_match.group(1) if date_match else None,
                'time': time_match.group(1) if time_match else None,
                'raw': line
            }
            
            self.header_info = header_info
            return header_info
        except Exception as e:
            logger.warning(f"Ошибка парсинга заголовка: {e}")
            self._add_warning(f"Ошибка парсинга заголовка: {e}")
            return {}
    
    def _parse_instrument_info(self, line: str) -> Dict[str, Any]:
        """Парсинг информации о приборе (запись 01)"""
        # Формат: 01NM<модель> <серийный номер>
        # Пример: 01NMul.POKLONNAYA 121111
        
        try:
            # Разделение на части
            parts = line[4:].strip().split()
            
            instrument_info = {
                'model': parts[0] if len(parts) > 0 else 'unknown',
                'serial_number': parts[1] if len(parts) > 1 else 'unknown'
            }
            
            self.instrument_info = instrument_info
            return instrument_info
        except Exception as e:
            logger.warning(f"Ошибка парсинга информации о приборе: {e}")
            self._add_warning(f"Ошибка парсинга информации о приборе: {e}")
            return {}
    
    def _parse_station(self, line: str) -> str:
        """Парсинг информации о станции (запись 02)"""
        # Формат: 02NM<имя станции>
        # Пример: 02NM1.00000000
        
        try:
            station_name = line[4:].strip()
            
            # Создание станции
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
            self._add_warning(f"Ошибка парсинга станции: {e}")
            return "unknown"
    
    def _parse_instrument_height(self, line: str) -> float:
        """Парсинг высоты инструмента (запись 03)"""
        # Формат: 03NM<высота>
        # Пример: 03NM1.522
        
        try:
            height_str = line[4:].strip()
            height = float(height_str)
            
            if self.current_station:
                self.current_setup['instrument_height'] = height
            
            return height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты инструмента: {e}")
            self._add_warning(f"Ошибка парсинга высоты инструмента: {e}")
            return 0.0
    
    def _parse_target_height(self, line: str) -> float:
        """Парсинг высоты цели (запись 04)"""
        # Формат: 04NM<высота>
        # Пример: 04NM1.500
        
        try:
            height_str = line[4:].strip()
            height = float(height_str)
            
            if self.current_station:
                self.current_setup['target_height'] = height
            
            return height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты цели: {e}")
            self._add_warning(f"Ошибка парсинга высоты цели: {e}")
            return 0.0
    
    def _parse_measurement(self, line: str, line_num: int) -> Optional[DATObservation]:
        """Парсинг измерения (запись 09)"""
        # Формат: 09F1 <станция> <цель> <азимут> <зенит> <горизонтальное расстояние>
        # Пример: 09F1 St 1 St 5155.5647 89.59222 44.14056
        
        if not self.current_station:
            return None
        
        try:
            # Разделение на части
            parts = line[4:].strip().split()
            
            if len(parts) < 6:
                return None
            
            # Извлечение данных
            from_point = parts[0] + " " + parts[1]
            to_point = parts[2] + " " + parts[3]
            azimuth = float(parts[4])  # Азимут в градусах
            zenith = float(parts[5])  # Зенитный угол в градусах
            distance = float(parts[6]) if len(parts) > 6 else None  # Горизонтальное расстояние
            
            # Создание измерения направления
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
            
            return obs
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга измерения в строке {line_num}: {e}")
            self._add_error(f"Ошибка парсинга измерения в строке {line_num}: {e}", line_num)
            return None
    
    def _parse_reception_number(self, line: str) -> int:
        """Парсинг номера приёма (запись 10)"""
        # Формат: 10NM<номер приёма>
        # Пример: 10NM1
        
        try:
            reception_str = line[4:].strip()
            reception_num = int(reception_str)
            
            if self.current_station:
                self.current_setup['reception_number'] = reception_num
            
            return reception_num
        except Exception as e:
            logger.warning(f"Ошибка парсинга номера приёма: {e}")
            self._add_warning(f"Ошибка парсинга номера приёма: {e}")
            return 1
    
    def _add_error(self, message: str, line: int = None):
        """Добавление ошибки в список"""
        error = {'message': message, 'line': line}
        self.errors.append(error)
    
    def _add_warning(self, message: str, line: int = None):
        """Добавление предупреждения в список"""
        warning = {'message': message, 'line': line}
        self.warnings.append(warning)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсинг файла DAT с полной обработкой структуры:
        - Заголовок файла (00)
        - Информация о приборе (01)
        - Станции (02)
        - Высоты инструмента/цели (03/04)
        - Измерения (09)
        - Номера приёмов (10)
        """
        # Определение кодировки
        self.encoding = self._detect_encoding(file_path)
        
        # Чтение файла
        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()
        
        logger.info(f"Парсинг файла DAT")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")
        
        # Обработка строк
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Извлечение идентификатора записи (первые 2 символа)
                if len(line) < 4:
                    continue
                
                record_id = line[:2]
                record_type = line[2:4]
                
                # Обработка записи в зависимости от типа
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
                
                elif record_id == '50':
                    # Конец измерения - сброс текущей установки
                    self.current_setup = {}
                
            except Exception as e:
                error_msg = f"Ошибка разбора строки {line_num}: {str(e)}"
                logger.error(error_msg)
                self._add_error(error_msg, line_num)
        
        # Формирование результата
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
            'warnings': self.warnings,
            'header_info': self.header_info,
            'instrument_info': self.instrument_info
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
    parser = DATParser()
    
    # Путь к файлу (замените на ваш путь)
    file_path = Path("Пример_DAT.txt")
    
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
        print(f"Ошибок: {len(result['errors'])}")
        
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
