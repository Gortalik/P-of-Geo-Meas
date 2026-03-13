"""
Менеджер проектов GeoAdjust Pro

Управление файлами проектов .gad, включая:
- Создание новых проектов
- Открытие/сохранение проектов
- Проверка целостности данных
- История недавних проектов
"""

import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProjectMetadata:
    """Метаданные проекта"""
    name: str = "Новый проект"
    organization: str = ""
    description: str = ""
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    scale: str = "1:500"
    author: str = ""
    project_id: str = ""


class ProjectFile:
    """Управление файлом проекта .gad"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.metadata = ProjectMetadata()
        self.settings = {}
        self.checksums = {}
    
    def create_project_structure(self):
        """Создание структуры папки проекта"""
        # Создание основных папок
        (self.project_path / "settings").mkdir(exist_ok=True)
        (self.project_path / "data").mkdir(exist_ok=True)
        (self.project_path / "results").mkdir(exist_ok=True)
        (self.project_path / "history").mkdir(exist_ok=True)
        
        # Создание файлов настроек
        self._create_project_xml()
        self._create_settings_files()
    
    def _create_project_xml(self):
        """Создание XML-файла метаданных проекта"""
        project_xml = self.project_path / "project.gadproj"
        
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project>
    <Metadata>
        <Name>{self.metadata.name}</Name>
        <Organization>{self.metadata.organization}</Organization>
        <Description>{self.metadata.description}</Description>
        <Created>{self.metadata.created.isoformat()}</Created>
        <Modified>{self.metadata.modified.isoformat()}</Modified>
        <Version>{self.metadata.version}</Version>
        <Scale>{self.metadata.scale}</Scale>
        <Author>{self.metadata.author}</Author>
        <ProjectID>{self.metadata.project_id}</ProjectID>
    </Metadata>
    <Settings>
        <CoordinateSystem>
            <BaseCRS>SK42</BaseCRS>
            <Zone>7</Zone>
            <CentralMeridian>39.0</CentralMeridian>
        </CoordinateSystem>
        <Processing>
            <Preprocessing enabled="true"/>
            <Adjustment method="classic"/>
            <Robust enabled="false"/>
        </Processing>
    </Settings>
</Project>"""
        
        with open(project_xml, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def _create_settings_files(self):
        """Создание файлов настроек проекта"""
        settings_dir = self.project_path / "settings"
        
        # Карточка проекта
        project_card = {
            "name": self.metadata.name,
            "organization": self.metadata.organization,
            "author": self.metadata.author,
            "created": self.metadata.created.isoformat(),
            "modified": self.metadata.modified.isoformat()
        }
        with open(settings_dir / "project_card.json", 'w', encoding='utf-8') as f:
            json.dump(project_card, f, indent=2, ensure_ascii=False)
        
        # Система координат
        crs_settings = {
            "base_crs": "SK42",
            "zone": 7,
            "central_meridian": 39.0,
            "false_easting": 7500000.0,
            "scale_factor": 1.0
        }
        with open(settings_dir / "crs.json", 'w', encoding='utf-8') as f:
            json.dump(crs_settings, f, indent=2)
        
        # Библиотека приборов
        instruments = {
            "instruments": [
                {
                    "name": "Leica TS16",
                    "type": "total_station",
                    "manufacturer": "Leica",
                    "model": "TS16",
                    "angular_accuracy": 1.0,
                    "distance_accuracy_a": 1.0,
                    "distance_accuracy_b": 1.0,
                    "centering_error": 2.0
                }
            ]
        }
        with open(settings_dir / "instruments.json", 'w', encoding='utf-8') as f:
            json.dump(instruments, f, indent=2)
        
        # Нормативные классы
        normative_classes = {
            "classes": [
                {
                    "name": "Полигонометрия 4 класса",
                    "type": "angular_network",
                    "max_angle_sigma": 3.0,
                    "max_relative_misalignment": "1/25000",
                    "max_point_position_sigma": 50.0
                },
                {
                    "name": "Нивелирование III класса",
                    "type": "leveling",
                    "max_leveling_sigma_per_stand": 3.0,
                    "max_section_closure_formula": "12*sqrt(L)",
                    "max_height_sigma": 5.0
                }
            ]
        }
        with open(settings_dir / "normative_classes.json", 'w', encoding='utf-8') as f:
            json.dump(normative_classes, f, indent=2)
    
    def save_data(self, data_type: str, data: Any):
        """Сохранение данных проекта"""
        data_dir = self.project_path / "data"
        
        if data_type == "points":
            # Сохранение пунктов в формате Parquet
            try:
                import pandas as pd
                df = pd.DataFrame([p.to_dict() if hasattr(p, 'to_dict') else p for p in data])
                df.to_parquet(data_dir / "points.parquet")
            except ImportError:
                logger.warning("pandas не установлен, сохранение в JSON")
                with open(data_dir / "points.json", 'w', encoding='utf-8') as f:
                    json.dump([p.__dict__ if hasattr(p, '__dict__') else p for p in data], f, indent=2)
        
        elif data_type == "observations":
            # Сохранение измерений в формате Parquet
            try:
                import pandas as pd
                df = pd.DataFrame([o.to_dict() if hasattr(o, 'to_dict') else o for o in data])
                df.to_parquet(data_dir / "observations.parquet")
            except ImportError:
                logger.warning("pandas не установлен, сохранение в JSON")
                with open(data_dir / "observations.json", 'w', encoding='utf-8') as f:
                    json.dump([o.__dict__ if hasattr(o, '__dict__') else o for o in data], f, indent=2)
        
        elif data_type == "topology":
            # Сохранение топологии сети в формате GraphML
            try:
                import networkx as nx
                nx.write_graphml(data, data_dir / "topology.graphml")
            except ImportError:
                logger.warning("networkx не установлен, сохранение в JSON")
                with open(data_dir / "topology.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        
        # Обновление контрольных сумм
        self._update_checksums()
    
    def load_data(self, data_type: str) -> Any:
        """Загрузка данных проекта"""
        data_dir = self.project_path / "data"
        
        if data_type == "points":
            points_file = data_dir / "points.parquet"
            if points_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_parquet(points_file)
                    return df.to_dict('records')
                except ImportError:
                    pass
            
            # Попытка загрузки из JSON
            points_json = data_dir / "points.json"
            if points_json.exists():
                with open(points_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return []
        
        elif data_type == "observations":
            obs_file = data_dir / "observations.parquet"
            if obs_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_parquet(obs_file)
                    return df.to_dict('records')
                except ImportError:
                    pass
            
            # Попытка загрузки из JSON
            obs_json = data_dir / "observations.json"
            if obs_json.exists():
                with open(obs_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return []
        
        elif data_type == "topology":
            topo_file = data_dir / "topology.graphml"
            if topo_file.exists():
                try:
                    import networkx as nx
                    return nx.read_graphml(topo_file)
                except ImportError:
                    pass
            
            # Попытка загрузки из JSON
            topo_json = data_dir / "topology.json"
            if topo_json.exists():
                with open(topo_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {}
    
    def _update_checksums(self):
        """Обновление контрольных сумм файлов"""
        checksums = {}
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix not in ['.sha256']:
                hash_md5 = hashlib.md5()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                checksums[str(file_path.relative_to(self.project_path))] = hash_md5.hexdigest()
        
        self.checksums = checksums
        
        # Сохранение контрольных сумм
        with open(self.project_path / "checksums.sha256", 'w', encoding='utf-8') as f:
            json.dump(checksums, f, indent=2)
    
    def verify_integrity(self) -> bool:
        """Проверка целостности проекта"""
        current_checksums = {}
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix not in ['.sha256']:
                hash_md5 = hashlib.md5()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                current_checksums[str(file_path.relative_to(self.project_path))] = hash_md5.hexdigest()
        
        # Сравнение с сохранёнными контрольными суммами
        if not self.checksums:
            # Загрузка сохранённых контрольных сумм
            checksums_file = self.project_path / "checksums.sha256"
            if checksums_file.exists():
                with open(checksums_file, 'r', encoding='utf-8') as f:
                    self.checksums = json.load(f)
        
        return current_checksums == self.checksums
    
    def get_settings(self, setting_type: str) -> Dict:
        """Получение настроек проекта"""
        settings_file = self.project_path / "settings" / f"{setting_type}.json"
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def save_settings(self, setting_type: str, settings: Dict):
        """Сохранение настроек проекта"""
        settings_dir = self.project_path / "settings"
        settings_dir.mkdir(exist_ok=True)
        
        settings_file = settings_dir / f"{setting_type}.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)


class ProjectManager:
    """Менеджер проектов"""
    
    def __init__(self):
        self.current_project: Optional[ProjectFile] = None
        self.recent_projects: List[Dict[str, str]] = []
        self.load_recent_projects()
    
    def create_new_project(self, project_name: str, project_path: Path) -> ProjectFile:
        """Создание нового проекта"""
        project_dir = project_path / f"{project_name}.gad"
        project_dir.mkdir(exist_ok=True)
        
        project = ProjectFile(project_dir)
        project.metadata.name = project_name
        project.metadata.created = datetime.now()
        project.metadata.modified = datetime.now()
        
        project.create_project_structure()
        
        self.current_project = project
        self._add_to_recent_projects(project_name, str(project_dir))
        
        return project
    
    def open_project(self, project_path: Path) -> ProjectFile:
        """Открытие существующего проекта"""
        if not project_path.exists() or not project_path.is_dir():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        project = ProjectFile(project_path)
        
        # Проверка целостности проекта
        if not project.verify_integrity():
            logger.warning(f"Проект {project_path} имеет повреждённые файлы")
            # Можно предложить восстановление из резервной копии
        
        # Загрузка метаданных
        project_xml = project_path / "project.gadproj"
        if project_xml.exists():
            # Парсинг XML для загрузки метаданных
            # TODO: Реализовать парсинг XML
            pass
        
        self.current_project = project
        self._add_to_recent_projects(project.metadata.name, str(project_path))
        
        return project
    
    def save_project(self):
        """Сохранение текущего проекта"""
        if self.current_project is None:
            raise ValueError("Нет открытого проекта для сохранения")
        
        self.current_project.metadata.modified = datetime.now()
        self.current_project._create_project_xml()
        
        logger.info(f"Проект сохранён: {self.current_project.project_path}")
    
    def save_project_as(self, new_path: Path):
        """Сохранение проекта в новое место"""
        if self.current_project is None:
            raise ValueError("Нет открытого проекта для сохранения")
        
        shutil.copytree(self.current_project.project_path, new_path)
        
        self.current_project = ProjectFile(new_path)
        self._add_to_recent_projects(self.current_project.metadata.name, str(new_path))
    
    def close_project(self):
        """Закрытие проекта"""
        if self.current_project:
            self.save_project()
            self.current_project = None
    
    def load_recent_projects(self):
        """Загрузка списка недавних проектов"""
        config_file = Path.home() / ".geoadjust" / "recent_projects.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.recent_projects = json.load(f)
    
    def _add_to_recent_projects(self, project_name: str, project_path: str):
        """Добавление проекта в список недавних"""
        project_entry = {
            "name": project_name,
            "path": project_path,
            "opened": datetime.now().isoformat()
        }
        
        # Удаление дубликатов
        self.recent_projects = [p for p in self.recent_projects if p['path'] != project_path]
        
        # Добавление в начало списка
        self.recent_projects.insert(0, project_entry)
        
        # Ограничение списка 10 проектами
        self.recent_projects = self.recent_projects[:10]
        
        # Сохранение списка
        config_file = Path.home() / ".geoadjust" / "recent_projects.json"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.recent_projects, f, indent=2, ensure_ascii=False)
    
    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Получение списка недавних проектов"""
        return self.recent_projects
