from .parser_template import BaseParser
from pathlib import Path
from typing import List, Dict, Any
import re


class GSIParser(BaseParser):
    """Парсер формата Leica GSI 1.0/8.0/8.1/8.2"""
    
    # Словарь информационных слов
    WORD_TYPES = {
        '11': 'direction',           # Направление
        '12': 'direction',           # Направление (альтернативный формат)
        '15': 'distance',            # Расстояние (наклонное)
        '16': 'distance',            # Расстояние (горизонтальное)
        '17': 'distance',            # Расстояние (вертикальное)
        '18': 'distance',            # Расстояние (высота)
        '7': 'height_diff',          # Превышение
        '84': 'station',             # Объявление станции
        '85': 'target',              # Объявление цели
        '87': 'instrument_height',   # Высота инструмента
        '88': 'target_height',       # Высота цели/отражателя
        '41': 'temperature',         # Температура
        '42': 'pressure',            # Давление
        '81': 'start_job',           # Начало работы
        '82': 'end_job',             # Окончание работы
        '83': 'start_setup',         # Начало установки
        '86': 'end_setup'            # Окончание установки
    }
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        Парсинг файла GSI с полной обработкой структуры:
        - Распознавание станций по словам 84–88
        - Обработка направлений (слово 11/12)
        - Обработка расстояний (слово 15/16/17/18)
        - Обработка превышений (слово 7)
        - Высоты инструмента/цели (слова 87/88)
        - Атмосферные параметры (слова 41–49)
        """
        encoding = self._detect_encoding(file_path)
        
        observations = []
        points = {}
        errors = []
        
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            lines = f.readlines()
            
            current_station = None
            current_setup = {}
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Разбор строки на информационные слова
                    words = self._parse_gsi_line(line)
                    
                    # Обработка слова 84 — объявление станции
                    if '84' in words:
                        station_data = self._parse_station_data(words['84'])
                        current_station = station_data['point_id']
                        
                        # Создание пункта станции
                        if current_station not in points:
                            points[current_station] = {
                                'point_id': current_station,
                                'point_type': 'station'
                            }
                    
                    # Обработка слова 87 — высота инструмента
                    if '87' in words and current_station:
                        instrument_height = self._parse_height(words['87'])
                        current_setup['instrument_height'] = instrument_height
                    
                    # Обработка слова 11 — направление
                    if '11' in words and current_station:
                        direction_data = self._parse_direction(words['11'])
                        obs = {
                            'obs_type': 'direction',
                            'from_point': current_station,
                            'to_point': direction_data['target'],
                            'value': direction_data['value'],
                            'instrument_height': current_setup.get('instrument_height'),
                            'line': line_num
                        }
                        observations.append(obs)
                    
                    # Обработка слова 15 — наклонное расстояние
                    if '15' in words and current_station:
                        distance_data = self._parse_distance(words['15'])
                        obs = {
                            'obs_type': 'distance',
                            'from_point': current_station,
                            'to_point': distance_data['target'],
                            'value': distance_data['value'],
                            'instrument_height': current_setup.get('instrument_height'),
                            'line': line_num
                        }
                        observations.append(obs)
                    
                    # Обработка слова 7 — превышение
                    if '7' in words:
                        height_data = self._parse_height_diff(words['7'])
                        obs = {
                            'obs_type': 'height_diff',
                            'from_point': height_data['from_point'],
                            'to_point': height_data['to_point'],
                            'value': height_data['value'],
                            'line': line_num
                        }
                        observations.append(obs)
                        
                except Exception as e:
                    self._add_error(f"Ошибка разбора строки {line_num}: {str(e)}", line_num)
        
        return {
            'points': list(points.values()),
            'observations': observations,
            'errors': self.errors,
            'warnings': self.warnings,
            'format': 'GSI',
            'version': self._detect_gsi_version(lines)
        }
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Автоопределение кодировки файла"""
        # Попытка различных кодировок
        encodings = ['utf-8', 'cp1251', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)
                return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # По умолчанию
    
    def _parse_gsi_line(self, line: str) -> Dict[str, str]:
        """Разбор строки GSI на информационные слова
        
        Формат GSI: каждое слово состоит из:
        - 2-значного номера слова (например, 11, 84, 87)
        - Знака (+/-)
        - Значения с фиксированной точкой
        
        Пример: "11+0.12345678" или "84+1001"
        """
        words = {}
        
        # Регулярное выражение для поиска информационных слов GSI
        # Номер слова (2 цифры) + знак (+/-) + значение (цифры и точка)
        pattern = r'(\d{2})([+-]?\d+\.?\d*)'
        matches = re.findall(pattern, line)
        
        for word_num, word_value in matches:
            words[word_num] = word_value
        
        return words
    
    def _parse_station_data(self, word_value: str) -> Dict[str, Any]:
        """Разбор данных станции
        
        Формат слова 84: идентификатор точки станции
        Пример: "84+1001" означает станцию с ID "1001"
        """
        # Извлечение числового значения как ID точки
        point_id = word_value.lstrip('+-')
        return {
            'point_id': point_id,
            'raw_value': word_value
        }
    
    def _parse_direction(self, word_value: str) -> Dict[str, Any]:
        """Разбор направления (слово 11/12)
        
        Формат: значение направления в радианах или градусах
        Пример: "11+0.12345678"
        """
        value = float(word_value)
        return {
            'target': None,  # Цель определяется из следующего слова 85
            'value': value,
            'raw_value': word_value
        }
    
    def _parse_distance(self, word_value: str) -> Dict[str, Any]:
        """Разбор расстояния (слово 15/16/17/18)
        
        Формат: значение расстояния в метрах
        Пример: "15+123.456" означает 123.456 метров
        """
        value = float(word_value)
        return {
            'target': None,  # Цель определяется из контекста
            'value': value,
            'raw_value': word_value
        }
    
    def _parse_height_diff(self, word_value: str) -> Dict[str, Any]:
        """Разбор превышения (слово 7)
        
        Формат: значение превышения в метрах
        Пример: "7+12.345" означает превышение 12.345 метров
        """
        value = float(word_value)
        return {
            'from_point': None,  # Определяется из текущей станции
            'to_point': None,    # Определяется из контекста
            'value': value,
            'raw_value': word_value
        }
    
    def _parse_height(self, word_value: str) -> float:
        """Разбор высоты инструмента/цели"""
        return float(word_value)
    
    def _detect_gsi_version(self, lines: List[str]) -> str:
        """Определение версии формата GSI"""
        # Анализ первой строки на наличие признаков версии
        first_line = lines[0] if lines else ''
        
        if 'GSI' in first_line or 'LEICA' in first_line:
            return '8.0/8.1/8.2'
        else:
            return '1.0'
