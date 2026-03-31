#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата Sokkia SDR (Survey Data Recorder)
Поддержка версий SDR2x и SDR33

Реальный формат SDR33 (на основе тестовых данных):
- Каждая строка начинается с 2-значного кода записи + 2-значного флага (обычно NM, F1, F2, RS, TP)
- Данные после кода имеют фиксированную ширину полей (16 символов на число)

Коды записей:
- 00: Заголовок файла
- 01: Информация о приборе
- 02: Установка станции (координаты + высота инструмента)
- 03: Высота инструмента/цели
- 05: Константы/параметры
- 06: Масштабный коэффициент
- 07: Ориентирное направление
- 08: Горизонтальный угол
- 09: Измерение (направление, зенит, расстояние)
- 10: Имя работы
- 11: Превышение/координаты
- 13: Комментарии/удаленные точки
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
    HEADER = "00"
    INSTRUMENT = "01"
    INSTRUMENT_SETUP = "02"
    TARGET_HEIGHT = "03"
    FORESIGHT_SETUP = "04"
    CONSTANTS = "05"
    SCALE_FACTOR = "06"
    BACKSIGHT_ANGLE = "07"
    HORIZONTAL_ANGLE = "08"
    MEASUREMENT = "09"
    JOB_NAME = "10"
    COORDINATES = "11"
    COMMENT = "13"


@dataclass
class SDRStation:
    """Станция в формате SDR"""
    point_id: str
    instrument_height: Optional[float] = None
    backsight_point: Optional[str] = None
    backsight_angle: Optional[float] = None
    face_position: str = "NONE"  # F1 (CL), F2 (CP), or NONE
    x: Optional[float] = None
    y: Optional[float] = None
    h: Optional[float] = None


@dataclass
class SDRObservation:
    """Измерение в формате SDR"""
    obs_type: str  # 'direction', 'distance', 'zenith_angle', 'slope_distance', 'height_diff'
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
        '00': 'header',
        '01': 'instrument',
        '02': 'instrument_setup',
        '03': 'target_height',
        '04': 'foresight_setup',
        '05': 'constants',
        '06': 'scale_factor',
        '07': 'backsight_angle',
        '08': 'horizontal_angle',
        '09': 'measurement',
        '10': 'job_name',
        '11': 'coordinates',
        '13': 'comment'
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
        self.current_face = "NONE"  # F1 или F2

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

    def _parse_fixed_float(self, s: str) -> Optional[float]:
        """Парсинг числа с фиксированной шириной поля (16 символов)
        
        Формат: 16 символов, последние 10 - десятичная часть
        Пример: '163.215660000000' -> 163.21566
        """
        s = s.strip()
        if not s:
            return None
        
        try:
            # Пробуем прямой парсинг
            return float(s)
        except ValueError:
            pass
        
        # Если не получилось, пробуем разделить на целую и дробную части
        # Формат SDR: первые 6 символов - целая часть, последние 10 - дробная
        if len(s) >= 16:
            try:
                int_part = s[:6].strip()
                dec_part = s[6:].strip()
                if int_part and dec_part:
                    return float(f"{int_part}.{dec_part}")
            except ValueError:
                pass
        
        return None

    def _parse_job_name(self, line: str):
        """Парсинг имени работы (код 10)"""
        try:
            # Формат: 10NM<имя работы><пробелы><число>
            data = line[4:].strip()
            parts = data.split()
            if parts:
                self.job_name = parts[0]
                logger.info(f"Имя работы: {self.job_name}")
        except Exception as e:
            logger.warning(f"Ошибка парсинга имени работы: {e}")

    def _parse_instrument_setup(self, line: str) -> str:
        """Парсинг установки станции (код 02)
        
        Формат: 02NM<point_id><Y><X><H><instrument_height>
        Каждое число - 16 символов
        """
        try:
            data = line[4:].strip()
            
            # Извлекаем имя точки (первые 16 символов, обычно имя слева)
            point_id = data[:16].strip()
            if not point_id:
                return "unknown"
            
            # Парсим координаты (каждая 16 символов)
            y_str = data[16:32].strip()
            x_str = data[32:48].strip()
            h_str = data[48:64].strip()
            ih_str = data[64:80].strip()
            
            y = self._parse_fixed_float(y_str)
            x = self._parse_fixed_float(x_str)
            h = self._parse_fixed_float(h_str)
            ih = self._parse_fixed_float(ih_str)
            
            self.current_station = SDRStation(
                point_id=point_id,
                instrument_height=ih,
                x=x,
                y=y,
                h=h,
                face_position=self.current_face
            )
            
            if point_id not in self.points:
                self.points[point_id] = {
                    'point_id': point_id,
                    'point_type': 'station',
                    'x': x,
                    'y': y,
                    'h': h
                }
            else:
                self.points[point_id].update({
                    'x': x,
                    'y': y,
                    'h': h
                })
            
            if ih is not None:
                self.current_setup['instrument_height'] = ih
            
            return point_id
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга установки станции: {e}")
            return "unknown"

    def _parse_target_height(self, line: str):
        """Парсинг высоты цели (код 03)"""
        try:
            data = line[4:].strip()
            height = self._parse_fixed_float(data)
            if height is not None:
                self.current_setup['target_height'] = height
        except Exception as e:
            logger.warning(f"Ошибка парсинга высоты цели: {e}")

    def _parse_backsight_angle(self, line: str):
        """Парсинг ориентирного направления (код 07)"""
        if not self.current_station:
            return
        
        try:
            data = line[4:].strip()
            # Формат: <station><backsight><angle1><angle2>
            station = data[:16].strip()
            backsight = data[16:32].strip()
            angle1_str = data[32:48].strip()
            angle2_str = data[48:64].strip()
            
            angle1 = self._parse_fixed_float(angle1_str)
            angle2 = self._parse_fixed_float(angle2_str)
            
            if backsight:
                self.current_station.backsight_point = backsight
                if backsight not in self.points:
                    self.points[backsight] = {
                        'point_id': backsight,
                        'point_type': 'backsight'
                    }
            
            if angle1 is not None:
                self.current_station.backsight_angle = angle1
                
        except Exception as e:
            logger.warning(f"Ошибка парсинга ориентирного направления: {e}")

    def _parse_measurement(self, line: str, line_num: int):
        """Парсинг измерения (код 09)
        
        Формат: 09F1/F2<station><target><horizontal_angle><zenith_angle><slope_distance>
        Каждое число - 16 символов
        """
        if not self.current_station:
            return None
        
        try:
            # Определяем полуприем (F1 или F2)
            face = line[2:4].strip()
            if face == 'F1':
                self.current_face = 'CL'
            elif face == 'F2':
                self.current_face = 'CP'
            
            data = line[4:]
            
            # Парсим поля (каждое 16 символов)
            station = data[:16].strip()
            target = data[16:32].strip()
            h_angle_str = data[32:48].strip()
            z_angle_str = data[48:64].strip()
            s_dist_str = data[64:80].strip()
            
            h_angle = self._parse_fixed_float(h_angle_str)
            z_angle = self._parse_fixed_float(z_angle_str)
            s_dist = self._parse_fixed_float(s_dist_str)
            
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
            
            # Добавляем зенитный угол
            if z_angle is not None:
                obs = SDRObservation(
                    obs_type='zenith_angle',
                    from_point=self.current_station.point_id,
                    to_point=target,
                    value=z_angle,
                    instrument_height=self.current_station.instrument_height,
                    target_height=self.current_setup.get('target_height'),
                    face_position=self.current_face,
                    line_number=line_num,
                    raw_data=line
                )
                self.observations.append(obs)
            
            # Добавляем наклонное расстояние
            if s_dist is not None and s_dist > 0:
                obs = SDRObservation(
                    obs_type='slope_distance',
                    from_point=self.current_station.point_id,
                    to_point=target,
                    value=s_dist,
                    instrument_height=self.current_station.instrument_height,
                    target_height=self.current_setup.get('target_height'),
                    face_position=self.current_face,
                    line_number=line_num,
                    raw_data=line
                )
                self.observations.append(obs)
            
            # Добавляем точку в список
            if target not in self.points:
                self.points[target] = {
                    'point_id': target,
                    'point_type': 'target',
                    'x': None,
                    'y': None,
                    'h': None
                }
                
        except Exception as e:
            logger.warning(f"Ошибка парсинга измерения в строке {line_num}: {e}")
            self.errors.append({
                'line': line_num,
                'message': str(e),
                'raw_line': line[:100]
            })

    def _parse_coordinates(self, line: str):
        """Парсинг координат (код 11)"""
        try:
            data = line[4:].strip()
            # Формат: <point_id><Y><X><H>
            point_id = data[:16].strip()
            y_str = data[16:32].strip()
            x_str = data[32:48].strip()
            h_str = data[48:64].strip()
            
            y = self._parse_fixed_float(y_str)
            x = self._parse_fixed_float(x_str)
            h = self._parse_fixed_float(h_str)
            
            if point_id:
                if point_id not in self.points:
                    self.points[point_id] = {
                        'point_id': point_id,
                        'point_type': 'coordinate',
                        'x': x,
                        'y': y,
                        'h': h
                    }
                else:
                    self.points[point_id].update({
                        'x': x,
                        'y': y,
                        'h': h
                    })
        except Exception as e:
            logger.warning(f"Ошибка парсинга координат: {e}")

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла SDR"""
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
                if len(line) < 4:
                    continue

                record_code = line[:2]
                record_type = self.RECORD_TYPES.get(record_code)

                if not record_type:
                    continue

                if record_type == 'job_name':
                    self._parse_job_name(line)
                elif record_type == 'instrument_setup':
                    self._parse_instrument_setup(line)
                elif record_type == 'target_height':
                    self._parse_target_height(line)
                elif record_type == 'backsight_angle':
                    self._parse_backsight_angle(line)
                elif record_type == 'measurement':
                    self._parse_measurement(line, line_num)
                elif record_type == 'coordinates':
                    self._parse_coordinates(line)
                elif record_type == 'comment':
                    # Пропускаем комментарии
                    pass
                elif record_type == 'header':
                    logger.info(f"Заголовок: {line[4:]}")
                elif record_type == 'instrument':
                    logger.info(f"Прибор: {line[4:]}")

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
