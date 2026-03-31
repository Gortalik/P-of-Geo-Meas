#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата цифровых нивелиров (Leica DNA/Trimble DiNi DAT)

Реальный формат DAT (на основе тестовых данных):
- Файл содержит данные цифрового нивелирования
- Формат строк с разделителями | (pipe)
- Типы измерений:
  - Rb: Отсчёт по задней рейке (Backsight reading)
  - Rf: Отсчёт по передней рейке (Foresight reading)
  - Rz: Отсчёт по промежуточной рейке (Intermediate sight reading)
  - HD: Горизонтальное расстояние
  - Z: Превышение

Структура нивелирного хода:
- Станция (KD1) с задней (Rb) и передней (Rf) рейками
- Промежуточные точки (Rz)
- Превышения (Z) вычисляются
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
    HEADER = "header"
    STATION = "station"
    BACKSIGHT = "backsight"
    FORESIGHT = "foresight"
    INTERMEDIATE = "intermediate"
    HEIGHT_DIFF = "height_diff"
    LINE_START = "line_start"
    LINE_END = "line_end"


@dataclass
class DATStation:
    """Станция нивелирования"""
    station_number: int
    backsight_point: str
    foresight_point: str
    backsight_reading: Optional[float] = None
    foresight_reading: Optional[float] = None
    backsight_distance: Optional[float] = None
    foresight_distance: Optional[float] = None
    height_diff: Optional[float] = None


@dataclass
class DATObservation:
    """Измерение в формате DAT"""
    obs_type: str  # 'backsight', 'foresight', 'intermediate', 'height_diff'
    from_point: str
    to_point: str
    value: float  # Отсчёт по рейке или превышение
    distance: Optional[float] = None
    line_number: int = 0
    raw_data: str = ""


class DATParser:
    """Парсер формата цифровых нивелиров DAT"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.observations: List[DATObservation] = []
        self.points: Dict[str, Dict[str, Any]] = {}
        self.encoding = 'cp1251'
        self.version = "unknown"
        self.header_info: Dict[str, Any] = {}
        self.current_station: Optional[DATStation] = None
        self.current_backsight_point: Optional[str] = None
        self.current_foresight_point: Optional[str] = None
        self.station_counter = 0
        self.line_name: str = ""

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

    def _parse_float(self, s: str) -> Optional[float]:
        """Парсинг числа из строки с удалением единиц измерения"""
        if not s:
            return None
        s = s.strip()
        # Удаляем единицы измерения
        s = re.sub(r'\s*m\s*$', '', s)
        s = s.strip()
        try:
            return float(s)
        except ValueError:
            return None

    def _parse_field(self, line: str, field_num: int) -> str:
        """Извлечение поля из строки с разделителями |"""
        parts = line.split('|')
        if field_num < len(parts):
            return parts[field_num].strip()
        return ""

    def _parse_header(self, line: str):
        """Парсинг заголовка"""
        try:
            # Формат: For M5|Adr     1|TO  <имя файла>
            field3 = self._parse_field(line, 2)
            if field3.startswith('TO'):
                self.line_name = field3[2:].strip()
                self.header_info['line_name'] = self.line_name
        except Exception as e:
            logger.warning(f"Ошибка парсинга заголовка: {e}")

    def _parse_station_line(self, line: str):
        """Парсинг строки станции (KD1)
        
        Формат: For M5|Adr     3|KD1       R3                  1|...|Z         0.00000 m   |
        """
        try:
            field3 = self._parse_field(line, 2)
            parts = field3.split()
            
            if len(parts) >= 2 and parts[0] == 'KD1':
                point_id = parts[1]
                self.current_backsight_point = point_id
                
                if point_id not in self.points:
                    self.points[point_id] = {
                        'point_id': point_id,
                        'point_type': 'benchmark',
                        'h': None
                    }
        except Exception as e:
            logger.warning(f"Ошибка парсинга станции: {e}")

    def _parse_backsight(self, line: str, line_num: int):
        """Парсинг отсчёта по задней рейке
        
        Формат: For M5|Adr     5|KD1       R3      03:16:181   1|Rb        1.80631 m   |HD         28.535 m   |
        """
        try:
            field3 = self._parse_field(line, 2)
            field4 = self._parse_field(line, 3)
            field5 = self._parse_field(line, 4)
            
            parts = field3.split()
            if len(parts) >= 2:
                point_id = parts[1]
            
            # Парсим отсчёт по рейке
            if field4.startswith('Rb'):
                reading_str = field4[2:].strip()
                reading = self._parse_float(reading_str)
                
                # Парсим расстояние
                distance = None
                if field5.startswith('HD'):
                    dist_str = field5[2:].strip()
                    distance = self._parse_float(dist_str)
                
                if reading is not None:
                    obs = DATObservation(
                        obs_type='backsight',
                        from_point='STATION',
                        to_point=point_id,
                        value=reading,
                        distance=distance,
                        line_number=line_num,
                        raw_data=line
                    )
                    self.observations.append(obs)
                    
                    if point_id not in self.points:
                        self.points[point_id] = {
                            'point_id': point_id,
                            'point_type': 'benchmark',
                            'h': None
                        }
                    
                    self.current_backsight_point = point_id
                    
        except Exception as e:
            logger.warning(f"Ошибка парсинга задней рейки в строке {line_num}: {e}")

    def _parse_foresight(self, line: str, line_num: int):
        """Парсинг отсчёта по передней рейке
        
        Формат: For M5|Adr     6|KD1        1      03:16:521   1|Rf        1.07539 m   |HD         28.524 m   |
        """
        try:
            field3 = self._parse_field(line, 2)
            field4 = self._parse_field(line, 3)
            field5 = self._parse_field(line, 4)
            
            parts = field3.split()
            if len(parts) >= 2:
                point_id = parts[1]
            
            if field4.startswith('Rf'):
                reading_str = field4[2:].strip()
                reading = self._parse_float(reading_str)
                
                distance = None
                if field5.startswith('HD'):
                    dist_str = field5[2:].strip()
                    distance = self._parse_float(dist_str)
                
                if reading is not None:
                    obs = DATObservation(
                        obs_type='foresight',
                        from_point='STATION',
                        to_point=point_id,
                        value=reading,
                        distance=distance,
                        line_number=line_num,
                        raw_data=line
                    )
                    self.observations.append(obs)
                    
                    if point_id not in self.points:
                        self.points[point_id] = {
                            'point_id': point_id,
                            'point_type': 'turning_point',
                            'h': None
                        }
                    
                    self.current_foresight_point = point_id
                    
        except Exception as e:
            logger.warning(f"Ошибка парсинга передней рейки в строке {line_num}: {e}")

    def _parse_intermediate(self, line: str, line_num: int):
        """Парсинг промежуточной точки
        
        Формат: For M5|Adr    12|KD1      3.1      03:19:301   1|Rz        1.04744 m   |HD          9.964 m   |Z         1.21187 m   |
        """
        try:
            field3 = self._parse_field(line, 2)
            field4 = self._parse_field(line, 3)
            field5 = self._parse_field(line, 4)
            field6 = self._parse_field(line, 5)
            
            parts = field3.split()
            if len(parts) >= 2:
                point_id = parts[1]
            
            if field4.startswith('Rz'):
                reading_str = field4[2:].strip()
                reading = self._parse_float(reading_str)
                
                distance = None
                if field5.startswith('HD'):
                    dist_str = field5[2:].strip()
                    distance = self._parse_float(dist_str)
                
                height_diff = None
                if field6.startswith('Z'):
                    z_str = field6[1:].strip()
                    height_diff = self._parse_float(z_str)
                
                if reading is not None:
                    obs = DATObservation(
                        obs_type='intermediate',
                        from_point='STATION',
                        to_point=point_id,
                        value=reading,
                        distance=distance,
                        line_number=line_num,
                        raw_data=line
                    )
                    self.observations.append(obs)
                    
                    if height_diff is not None:
                        obs_h = DATObservation(
                            obs_type='height_diff',
                            from_point=self.current_backsight_point or 'UNKNOWN',
                            to_point=point_id,
                            value=height_diff,
                            line_number=line_num,
                            raw_data=line
                        )
                        self.observations.append(obs_h)
                    
                    if point_id not in self.points:
                        self.points[point_id] = {
                            'point_id': point_id,
                            'point_type': 'intermediate',
                            'h': None
                        }
                    
        except Exception as e:
            logger.warning(f"Ошибка парсинга промежуточной точки в строке {line_num}: {e}")

    def _parse_height_diff(self, line: str, line_num: int):
        """Парсинг превышения
        
        Формат: For M5|Adr     7|KD1        1      03:16:52    1|                      |                      |Z         0.73092 m   |
        """
        try:
            field6 = self._parse_field(line, 5)
            
            if field6.startswith('Z'):
                z_str = field6[1:].strip()
                height_diff = self._parse_float(z_str)
                
                if height_diff is not None and self.current_backsight_point and self.current_foresight_point:
                    obs = DATObservation(
                        obs_type='height_diff',
                        from_point=self.current_backsight_point,
                        to_point=self.current_foresight_point,
                        value=height_diff,
                        line_number=line_num,
                        raw_data=line
                    )
                    self.observations.append(obs)
                    
        except Exception as e:
            logger.warning(f"Ошибка парсинга превышения в строке {line_num}: {e}")

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
                # Определяем тип строки по содержимому
                if 'TO' in line and '|' in line:
                    # Это может быть заголовок или начало/конец хода
                    field3 = self._parse_field(line, 2)
                    if 'Start-Line' in field3:
                        self._parse_header(line)
                    elif 'End-Line' in field3:
                        pass  # Конец хода
                    else:
                        self._parse_header(line)
                elif 'KD1' in line and '|' in line:
                    field3 = self._parse_field(line, 2)
                    field4 = self._parse_field(line, 3)
                    
                    if 'Rb' in field4:
                        self._parse_backsight(line, line_num)
                    elif 'Rf' in field4:
                        self._parse_foresight(line, line_num)
                    elif 'Rz' in field4:
                        self._parse_intermediate(line, line_num)
                    elif field3.strip().startswith('KD1'):
                        # Строка станции без отсчёта
                        self._parse_station_line(line)
                    
                    # Проверяем на превышение
                    if 'Z' in self._parse_field(line, 5):
                        self._parse_height_diff(line, line_num)
                elif 'Intermediate sight' in line:
                    pass  # Начало/конец промежуточных точек
                elif 'Reading' in line:
                    pass  # Информация о считывании

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
            'warnings': self.warnings,
            'header_info': self.header_info,
            'success': len(self.errors) == 0
        }

        if len(self.errors) > 0:
            logger.error(f"Обнаружено {len(self.errors)} ошибок при парсинге")
            if len(self.errors) > 10:
                logger.error(f"Первые 10 ошибок:")
                for error in self.errors[:10]:
                    logger.error(f"  Строка {error.get('line', '?')}: {error.get('message', 'Неизвестная ошибка')}")

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

        print(f"\n{'=' * 60}")
        print(f"Результаты парсинга файла {file_path.name}")
        print(f"{'=' * 60}")
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

        if result['observations']:
            print(f"\nПервые 5 измерений:")
            for i, obs in enumerate(result['observations'][:5], 1):
                print(f"  {i}. {obs.obs_type:15} {obs.from_point} → {obs.to_point:10} = {obs.value:.6f}")

        if result['errors']:
            print(f"\nОшибки парсинга:")
            for error in result['errors'][:5]:
                print(f"  Строка {error['line']}: {error['message']}")
    else:
        print(f"Файл {file_path} не найден!")
