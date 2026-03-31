#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер формата RTKLIB POS (RTKPOST solution)

Формат файла POS (на основе тестовых данных):
- Заголовочные строки начинаются с %
- Данные содержат координаты ECEF (X, Y, Z) с оценками точности
- Формат данных:
  GPST  x-ecef(m)  y-ecef(m)  z-ecef(m)  Q  ns  sdx  sdy  sdz  sdxy  sdyz  sdzx  age  ratio

Поля заголовка:
- % program   : имя программы и версия
- % inp file  : входные файлы (RINEX наблюдений и навигации)
- % obs start : время начала наблюдений
- % obs end   : время окончания наблюдений
- % pos mode  : режим позиционирования (static, kinematic, etc.)
- % freqs     : используемые частоты
- % solution  : тип решения (combined, forward, backward)
- % elev mask : маска угла возвышения
- % ref pos   : координаты базовой станции (X, Y, Z)

Поля данных:
- GPST: дата и время (YYYY/MM/DD hh:mm:ss.s)
- x/y/z-ecef: координаты в WGS84 (метры)
- Q: качество решения (1=fix, 2=float, 3=sbas, 4=dgps, 5=single, 6=ppp)
- ns: число спутников
- sdx/sdy/sdz: СКО по осям (метры)
- sdxy/sdyz/sdzx: корреляции СКО
- age: возраст поправки (секунды)
- ratio: отношение фиктивного отношения
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import chardet

logger = logging.getLogger(__name__)


@dataclass
class POSEpoch:
    """Эпоха решения в формате POS"""
    gpst_time: str  # Время в формате GPST
    x_ecef: float  # Координата X ECEF (м)
    y_ecef: float  # Координата Y ECEF (м)
    z_ecef: float  # Координата Z ECEF (м)
    quality: int  # Качество решения (1=fix, 2=float, etc.)
    n_satellites: int  # Число спутников
    sdx: float  # СКО по X (м)
    sdy: float  # СКО по Y (м)
    sdz: float  # СКО по Z (м)
    sdxy: float  # Корреляция СКО XY
    sdyz: float  # Корреляция СКО YZ
    sdzx: float  # Корреляция СКО ZX
    age: float  # Возраст поправки (с)
    ratio: float  # Отношение
    line_number: int = 0


@dataclass
class GNSSVector:
    """GNSS вектор между двумя станциями"""
    from_station: str  # Имя базовой станции
    to_station: str  # Имя подвижной станции
    dx: float  # Разность координат X (м)
    dy: float  # Разность координат Y (м)
    dz: float  # Разность координат Z (м)
    sigma_dx: float  # СКО разности X (м)
    sigma_dy: float  # СКО разности Y (м)
    sigma_dz: float  # СКО разности Z (м)
    quality: int  # Качество решения
    n_satellites: int  # Число спутников
    epoch: str  # Время эпохи


class POSParser:
    """Парсер формата RTKLIB POS"""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.header_info: Dict[str, Any] = {}
        self.epochs: List[POSEpoch] = []
        self.encoding = 'cp1251'
        self.ref_position: Optional[Tuple[float, float, float]] = None
        self.from_station: str = ""
        self.to_station: str = ""

    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)

        # RTKLIB файлы обычно в ASCII или cp1251 (для русских путей)
        try:
            text = raw_data.decode('ascii')
            return 'ascii'
        except UnicodeDecodeError:
            pass

        try:
            text = raw_data.decode('cp1251')
            return 'cp1251'
        except UnicodeDecodeError:
            pass

        return 'utf-8'

    def _parse_header_line(self, line: str) -> bool:
        """Парсинг строки заголовка"""
        line = line.strip()
        if not line.startswith('%'):
            return False

        content = line[1:].strip()

        try:
            if ':' in content:
                key, value = content.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'program':
                    self.header_info['program'] = value
                elif key == 'inp file':
                    if 'inp_files' not in self.header_info:
                        self.header_info['inp_files'] = []
                    self.header_info['inp_files'].append(value)
                elif key == 'obs start':
                    self.header_info['obs_start'] = value
                elif key == 'obs end':
                    self.header_info['obs_end'] = value
                elif key == 'pos mode':
                    self.header_info['pos_mode'] = value
                elif key == 'freqs':
                    self.header_info['freqs'] = value
                elif key == 'solution':
                    self.header_info['solution'] = value
                elif key == 'elev mask':
                    self.header_info['elev_mask'] = float(value.replace('deg', '').strip())
                elif key == 'dynamics':
                    self.header_info['dynamics'] = value
                elif key == 'tidecorr':
                    self.header_info['tidecorr'] = value
                elif key == 'ionos opt':
                    self.header_info['ionos_opt'] = value
                elif key == 'tropo opt':
                    self.header_info['tropo_opt'] = value
                elif key == 'ephemeris':
                    self.header_info['ephemeris'] = value
                elif key == 'navi sys':
                    self.header_info['navi_sys'] = value
                elif key == 'amb res':
                    self.header_info['amb_res'] = value
                elif key == 'amb glo':
                    self.header_info['amb_glo'] = value
                elif key == 'val thres':
                    self.header_info['val_thres'] = float(value.strip())
                elif key == 'antenna1':
                    self.header_info['antenna1'] = value
                elif key == 'antenna2':
                    self.header_info['antenna2'] = value
                elif key == 'ref pos':
                    # Парсим координаты базовой станции
                    coords = value.strip().split()
                    if len(coords) >= 3:
                        self.ref_position = (
                            float(coords[0]),
                            float(coords[1]),
                            float(coords[2])
                        )
                        self.header_info['ref_position'] = self.ref_position
                return True
        except Exception as e:
            logger.warning(f"Ошибка парсинга заголовка '{line}': {e}")
            self.warnings.append({
                'line': line[:100],
                'message': str(e)
            })

        return False

    def _parse_data_line(self, line: str, line_num: int) -> Optional[POSEpoch]:
        """Парсинг строки данных
        
        Формат:
        GPST  x-ecef(m)  y-ecef(m)  z-ecef(m)  Q  ns  sdx  sdy  sdz  sdxy  sdyz  sdzx  age  ratio
        """
        line = line.strip()
        if not line or line.startswith('%'):
            return None

        try:
            parts = line.split()
            if len(parts) < 14:
                return None

            # Парсим время GPST (первые два поля: дата и время)
            gpst_time = f"{parts[0]} {parts[1]}"

            # Парсим координаты и параметры
            x_ecef = float(parts[2])
            y_ecef = float(parts[3])
            z_ecef = float(parts[4])
            quality = int(parts[5])
            n_satellites = int(parts[6])
            sdx = float(parts[7])
            sdy = float(parts[8])
            sdz = float(parts[9])
            sdxy = float(parts[10])
            sdyz = float(parts[11])
            sdzx = float(parts[12])
            age = float(parts[13]) if len(parts) > 13 else 0.0
            ratio = float(parts[14]) if len(parts) > 14 else 0.0

            return POSEpoch(
                gpst_time=gpst_time,
                x_ecef=x_ecef,
                y_ecef=y_ecef,
                z_ecef=z_ecef,
                quality=quality,
                n_satellites=n_satellites,
                sdx=sdx,
                sdy=sdy,
                sdz=sdz,
                sdxy=sdxy,
                sdyz=sdyz,
                sdzx=sdzx,
                age=age,
                ratio=ratio,
                line_number=line_num
            )

        except Exception as e:
            logger.debug(f"Ошибка парсинга строки данных {line_num}: {e}")
            return None

    def _extract_station_names(self) -> Tuple[str, str]:
        """Извлечение имён станций из имён файлов
        
        Извлекает имена станций из путей к файлам RINEX в заголовке
        """
        from_station = ""
        to_station = ""

        inp_files = self.header_info.get('inp_files', [])
        for f in inp_files:
            # Извлекаем имя файла из пути
            filename = Path(f).stem
            # RINEX имена: <station><doy><year>.<type>
            # Пример: bshm0320.22o -> bshm
            match = re.match(r'^([a-zA-Z0-9]{4})\d+', filename)
            if match:
                if not from_station:
                    from_station = match.group(1).upper()
                else:
                    to_station = match.group(1).upper()

        # Если не удалось извлечь из файлов, используем имя файла POS
        if not from_station or not to_station:
            # Будет установлено позже из имени файла
            pass

        return from_station, to_station

    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг файла POS"""
        self.encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            lines = f.readlines()

        logger.info(f"Парсинг файла POS")
        logger.info(f"Кодировка: {self.encoding}")
        logger.info(f"Строк в файле: {len(lines)}")

        in_header = True
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            if line.startswith('%'):
                self._parse_header_line(line)
            else:
                in_header = False
                epoch = self._parse_data_line(line, line_num)
                if epoch:
                    self.epochs.append(epoch)

        # Извлекаем имена станций
        self.from_station, self.to_station = self._extract_station_names()

        # Если не удалось извлечь, используем имя файла
        if not self.from_station or not self.to_station:
            # Имя файла формата: station1-station2.pos
            stem = file_path.stem
            if '-' in stem:
                parts = stem.split('-', 1)
                if not self.from_station:
                    self.from_station = parts[0].upper()[:4]
                if not self.to_station:
                    self.to_station = parts[1].upper()[:4]

        result = {
            'format': 'POS',
            'encoding': self.encoding,
            'total_lines': len(lines),
            'header_info': self.header_info,
            'epochs': self.epochs,
            'from_station': self.from_station,
            'to_station': self.to_station,
            'ref_position': self.ref_position,
            'num_epochs': len(self.epochs),
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }

        if len(self.errors) > 0:
            logger.error(f"Обнаружено {len(self.errors)} ошибок при парсинге")
            for error in self.errors[:10]:
                logger.error(f"  {error.get('message', 'Неизвестная ошибка')}")

        logger.info(f"Парсинг завершён: {result['num_epochs']} эпох")

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по распарсенным данным"""
        stats = {
            'total_epochs': len(self.epochs),
            'quality_counts': {},
            'avg_satellites': 0,
            'avg_sdx': 0.0,
            'avg_sdy': 0.0,
            'avg_sdz': 0.0,
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }

        if self.epochs:
            # Подсчёт по качеству
            for epoch in self.epochs:
                q = epoch.quality
                stats['quality_counts'][q] = stats['quality_counts'].get(q, 0) + 1

            # Средние значения
            stats['avg_satellites'] = sum(e.n_satellites for e in self.epochs) / len(self.epochs)
            stats['avg_sdx'] = sum(e.sdx for e in self.epochs) / len(self.epochs)
            stats['avg_sdy'] = sum(e.sdy for e in self.epochs) / len(self.epochs)
            stats['avg_sdz'] = sum(e.sdz for e in self.epochs) / len(self.epochs)

        return stats

    def get_gnss_vector(self) -> Optional[GNSSVector]:
        """Получение усреднённого GNSS вектора между станциями
        
        Вычисляет средний вектор по всем эпохам с фиксированным решением
        """
        # Фильтруем только эпохи с фиксированным решением (Q=1)
        fixed_epochs = [e for e in self.epochs if e.quality == 1]

        if not fixed_epochs:
            # Если нет фиксированных, используем все
            fixed_epochs = self.epochs

        if not fixed_epochs:
            return None

        # Средние координаты
        n = len(fixed_epochs)
        avg_x = sum(e.x_ecef for e in fixed_epochs) / n
        avg_y = sum(e.y_ecef for e in fixed_epochs) / n
        avg_z = sum(e.z_ecef for e in fixed_epochs) / n

        # Средние СКО
        avg_sdx = sum(e.sdx for e in fixed_epochs) / n
        avg_sdy = sum(e.sdy for e in fixed_epochs) / n
        avg_sdz = sum(e.sdz for e in fixed_epochs) / n

        # Вычисляем вектор относительно базовой станции
        if self.ref_position:
            dx = avg_x - self.ref_position[0]
            dy = avg_y - self.ref_position[1]
            dz = avg_z - self.ref_position[2]
        else:
            dx = avg_x
            dy = avg_y
            dz = avg_z

        return GNSSVector(
            from_station=self.from_station,
            to_station=self.to_station,
            dx=dx,
            dy=dy,
            dz=dz,
            sigma_dx=avg_sdx,
            sigma_dy=avg_sdy,
            sigma_dz=avg_sdz,
            quality=fixed_epochs[0].quality,
            n_satellites=int(sum(e.n_satellites for e in fixed_epochs) / n),
            epoch=fixed_epochs[0].gpst_time
        )


if __name__ == "__main__":
    parser = POSParser()
    
    # Тестирование на реальном файле
    import sys
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        file_path = Path("test_real_mes/gnss/bshm-ramo.pos")

    if file_path.exists():
        result = parser.parse(file_path)

        print(f"\n{'=' * 70}")
        print(f"Результаты парсинга файла {file_path.name}")
        print(f"{'=' * 70}")
        print(f"Формат: {result['format']}")
        print(f"Кодировка: {result['encoding']}")
        print(f"Всего строк: {result['total_lines']}")
        print(f"Эпох: {result['num_epochs']}")
        print(f"Базовая станция: {result['from_station']}")
        print(f"Подвижная станция: {result['to_station']}")
        print(f"Опорная позиция: {result['ref_position']}")
        print(f"Ошибок: {len(result['errors'])}")

        print(f"\nИнформация из заголовка:")
        for key, value in result['header_info'].items():
            if key != 'inp_files':
                print(f"  {key}: {value}")

        print(f"\nСтатистика:")
        stats = parser.get_statistics()
        print(f"  Среднее число спутников: {stats['avg_satellites']:.1f}")
        print(f"  Средний СКО X: {stats['avg_sdx']*1000:.2f} мм")
        print(f"  Средний СКО Y: {stats['avg_sdy']*1000:.2f} мм")
        print(f"  Средний СКО Z: {stats['avg_sdz']*1000:.2f} мм")
        print(f"  Качество решений: {stats['quality_counts']}")

        vector = parser.get_gnss_vector()
        if vector:
            print(f"\nGNSS вектор {vector.from_station} -> {vector.to_station}:")
            print(f"  dX = {vector.dx:.4f} м (σ={vector.sigma_dx*1000:.2f} мм)")
            print(f"  dY = {vector.dy:.4f} м (σ={vector.sigma_dy*1000:.2f} мм)")
            print(f"  dZ = {vector.dz:.4f} м (σ={vector.sigma_dz*1000:.2f} мм)")
            print(f"  Качество: {vector.quality}, Спутников: {vector.n_satellites}")

        if result['epochs']:
            print(f"\nПервые 5 эпох:")
            for i, epoch in enumerate(result['epochs'][:5], 1):
                print(f"  {i}. {epoch.gpst_time}: X={epoch.x_ecef:.4f}, Y={epoch.y_ecef:.4f}, Z={epoch.z_ecef:.4f}, Q={epoch.quality}")
    else:
        print(f"Файл {file_path} не найден!")
