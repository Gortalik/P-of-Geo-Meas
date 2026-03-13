"""
Формат проекта GeoAdjust Pro (.gad)

Структура проекта:
- project.gadproj - XML метаданные проекта
- settings/ - настройки проекта
  - project_card.json - карточка проекта
  - crs.json - система координат
  - instruments.json - приборы
  - tolerances.json - допуски
- data/ - данные измерений
  - points.json - пункты ПВО
  - observations.json - измерения
  - traverses.json - ходы и секции
- results/ - результаты уравнивания
  - adjusted_points.json - уравненные координаты
  - residuals.json - невязки
  - accuracy.json - точностные характеристики
- history/ - история изменений
  - versions.json - версии проекта
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
import shutil
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class GADProject:
    """Проект в формате .gad"""
    
    VERSION = "1.0"
    
    def __init__(self, name: str, project_dir: Path):
        self.name = name
        self.project_dir = project_dir
        self.created = datetime.now()
        self.modified = datetime.now()
        
        # Структура проекта
        self.settings: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {
            'points': [],
            'observations': [],
            'traverses': []
        }
        self.results: Dict[str, Any] = {}
        self.metadata: Dict[str, str] = {}
    
    def create_structure(self):
        """Создание структуры папки проекта"""
        # Создание основных директорий
        (self.project_dir / "settings").mkdir(exist_ok=True)
        (self.project_dir / "data").mkdir(exist_ok=True)
        (self.project_dir / "results").mkdir(exist_ok=True)
        (self.project_dir / "history").mkdir(exist_ok=True)
        
        # Создание файла метаданных
        self._create_metadata_file()
        
        # Создание файлов настроек по умолчанию
        self._create_default_settings()
        
        # Создание файлов данных
        self._create_data_files()
        
        logger.info(f"Структура проекта создана: {self.project_dir}")
    
    def _create_metadata_file(self):
        """Создание XML-файла метаданных проекта"""
        metadata_file = self.project_dir / "project.gadproj"
        
        root = ET.Element("Project")
        
        # Метаданные
        metadata = ET.SubElement(root, "Metadata")
        ET.SubElement(metadata, "Name").text = self.name
        ET.SubElement(metadata, "Created").text = self.created.isoformat()
        ET.SubElement(metadata, "Modified").text = self.modified.isoformat()
        ET.SubElement(metadata, "Version").text = self.VERSION
        
        # Запись XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            tree.write(f, encoding='unicode', xml_declaration=True)
    
    def _create_default_settings(self):
        """Создание файлов настроек по умолчанию"""
        # Карточка проекта
        project_card = {
            "name": self.name,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "organization": "",
            "author": "",
            "description": ""
        }
        with open(self.project_dir / "settings" / "project_card.json", 'w', encoding='utf-8') as f:
            json.dump(project_card, f, indent=2, ensure_ascii=False)
        
        # Система координат (по умолчанию СК-42)
        crs_settings = {
            "base_crs": "SK42",
            "zone": 7,
            "central_meridian": 39.0,
            "scale_factor": 1.0,
            "false_easting": 7500000.0,
            "height_system": "BSV"
        }
        with open(self.project_dir / "settings" / "crs.json", 'w', encoding='utf-8') as f:
            json.dump(crs_settings, f, indent=2)
        
        # Допуски по умолчанию
        tolerances = {
            "angle_tolerance": 5.0,  # секунды
            "distance_relative_tolerance": 1e-5,
            "coordinate_tolerance": 0.01  # метры
        }
        with open(self.project_dir / "settings" / "tolerances.json", 'w', encoding='utf-8') as f:
            json.dump(tolerances, f, indent=2)
        
        logger.info("Настройки проекта по умолчанию созданы")
    
    def _create_data_files(self):
        """Создание файлов данных"""
        # Пустые файлы данных
        with open(self.project_dir / "data" / "points.json", 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        
        with open(self.project_dir / "data" / "observations.json", 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        
        with open(self.project_dir / "data" / "traverses.json", 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        
        logger.info("Файлы данных созданы")
    
    def save(self):
        """Сохранение проекта"""
        self.modified = datetime.now()
        self._create_metadata_file()
        
        # Сохранение настроек
        self._save_settings()
        
        # Сохранение данных
        self._save_data()
        
        logger.info(f"Проект сохранён: {self.name}")
    
    def save_as(self, new_path: Path):
        """Сохранение проекта в новое место"""
        # Копирование всей директории проекта
        if new_path.exists():
            shutil.rmtree(new_path)
        
        shutil.copytree(self.project_dir, new_path)
        
        # Обновление пути
        self.project_dir = new_path
        
        logger.info(f"Проект сохранён в новое место: {new_path}")
    
    def _save_settings(self):
        """Сохранение настроек проекта"""
        # Сохранение карточки проекта
        project_card = {
            "name": self.name,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            **self.settings.get('project_card', {})
        }
        with open(self.project_dir / "settings" / "project_card.json", 'w', encoding='utf-8') as f:
            json.dump(project_card, f, indent=2, ensure_ascii=False)
    
    def _save_data(self):
        """Сохранение данных проекта"""
        # Сохранение пунктов
        with open(self.project_dir / "data" / "points.json", 'w', encoding='utf-8') as f:
            json.dump(self.data['points'], f, indent=2, ensure_ascii=False)
        
        # Сохранение измерений
        with open(self.project_dir / "data" / "observations.json", 'w', encoding='utf-8') as f:
            json.dump(self.data['observations'], f, indent=2, ensure_ascii=False)
        
        # Сохранение ходов
        with open(self.project_dir / "data" / "traverses.json", 'w', encoding='utf-8') as f:
            json.dump(self.data['traverses'], f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, project_path: Path) -> 'GADProject':
        """Загрузка проекта"""
        if not project_path.exists() or not project_path.is_dir():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        # Создание экземпляра проекта
        project = cls("", project_path)
        
        # Загрузка метаданных
        metadata_file = project_path / "project.gadproj"
        if metadata_file.exists():
            tree = ET.parse(metadata_file)
            root = tree.getroot()
            
            metadata_elem = root.find('.//Metadata')
            if metadata_elem is not None:
                name_elem = metadata_elem.find('Name')
                if name_elem is not None and name_elem.text:
                    project.name = name_elem.text
                
                created_elem = metadata_elem.find('Created')
                if created_elem is not None and created_elem.text:
                    try:
                        project.created = datetime.fromisoformat(created_elem.text)
                    except ValueError:
                        pass
                
                modified_elem = metadata_elem.find('Modified')
                if modified_elem is not None and modified_elem.text:
                    try:
                        project.modified = datetime.fromisoformat(modified_elem.text)
                    except ValueError:
                        pass
                
                version_elem = metadata_elem.find('Version')
                if version_elem is not None and version_elem.text:
                    project.metadata['version'] = version_elem.text
        
        # Загрузка настроек
        project._load_settings()
        
        # Загрузка данных
        project._load_data()
        
        logger.info(f"Проект загружен: {project.name}")
        
        return project
    
    def _load_settings(self):
        """Загрузка настроек проекта"""
        settings_dir = self.project_dir / "settings"
        
        # Загрузка карточки проекта
        project_card_file = settings_dir / "project_card.json"
        if project_card_file.exists():
            with open(project_card_file, 'r', encoding='utf-8') as f:
                self.settings['project_card'] = json.load(f)
        
        # Загрузка системы координат
        crs_file = settings_dir / "crs.json"
        if crs_file.exists():
            with open(crs_file, 'r', encoding='utf-8') as f:
                self.settings['crs'] = json.load(f)
        
        # Загрузка допусков
        tolerances_file = settings_dir / "tolerances.json"
        if tolerances_file.exists():
            with open(tolerances_file, 'r', encoding='utf-8') as f:
                self.settings['tolerances'] = json.load(f)
    
    def _load_data(self):
        """Загрузка данных проекта"""
        data_dir = self.project_dir / "data"
        
        # Загрузка пунктов
        points_file = data_dir / "points.json"
        if points_file.exists():
            with open(points_file, 'r', encoding='utf-8') as f:
                self.data['points'] = json.load(f)
        
        # Загрузка измерений
        observations_file = data_dir / "observations.json"
        if observations_file.exists():
            with open(observations_file, 'r', encoding='utf-8') as f:
                self.data['observations'] = json.load(f)
        
        # Загрузка ходов
        traverses_file = data_dir / "traverses.json"
        if traverses_file.exists():
            with open(traverses_file, 'r', encoding='utf-8') as f:
                self.data['traverses'] = json.load(f)
    
    def add_point(self, point_data: Dict[str, Any]):
        """Добавление пункта"""
        self.data['points'].append(point_data)
        self.modified = datetime.now()
    
    def add_observation(self, observation_data: Dict[str, Any]):
        """Добавление измерения"""
        self.data['observations'].append(observation_data)
        self.modified = datetime.now()
    
    def get_points(self) -> List[Dict[str, Any]]:
        """Получение списка пунктов"""
        return self.data['points'].copy()
    
    def get_observations(self) -> List[Dict[str, Any]]:
        """Получение списка измерений"""
        return self.data['observations'].copy()
    
    def get_crs_settings(self) -> Dict[str, Any]:
        """Получение настроек системы координат"""
        return self.settings.get('crs', {})
    
    def get_tolerances(self) -> Dict[str, Any]:
        """Получение настроек допусков"""
        return self.settings.get('tolerances', {})
