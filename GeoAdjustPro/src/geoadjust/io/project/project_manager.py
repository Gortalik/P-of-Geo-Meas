"""
Менеджер проектов GeoAdjust Pro

Управление жизненным циклом проектов:
- Создание новых проектов
- Открытие существующих проектов
- Сохранение и загрузка
- Список недавних проектов
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ProjectManager:
    """Менеджер проектов GeoAdjust Pro"""
    
    def __init__(self):
        self.current_project: Optional['GADProject'] = None
        self.recent_projects: List[Dict[str, str]] = []
        self.config_dir = Path.home() / ".geoadjust"
        self.config_dir.mkdir(exist_ok=True)
        
        self._load_recent_projects()
    
    def create_project(self, project_path: Path, project_name: str) -> 'GADProject':
        """Создание нового проекта"""
        from src.geoadjust.io.project.gad_format import GADProject
        
        # Создание директории проекта
        project_dir = Path(project_path) / f"{project_name}.gad"
        if project_dir.exists():
            raise FileExistsError(f"Проект уже существует: {project_dir}")
        
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Создание проекта
        project = GADProject(project_name, project_dir)
        project.create_structure()
        
        # Добавление в список недавних проектов
        self._add_to_recent_projects(project_name, str(project_dir))
        
        self.current_project = project
        logger.info(f"Создан новый проект: {project_name}")
        
        return project
    
    def open_project(self, project_path: Path) -> 'GADProject':
        """Открытие существующего проекта"""
        from src.geoadjust.io.project.gad_format import GADProject
        
        if not project_path.exists():
            raise FileNotFoundError(f"Проект не найден: {project_path}")
        
        project = GADProject.load(project_path)
        
        # Добавление в список недавних проектов
        self._add_to_recent_projects(project.name, str(project_path))
        
        self.current_project = project
        logger.info(f"Открыт проект: {project.name}")
        
        return project
    
    def save_project(self):
        """Сохранение текущего проекта"""
        if self.current_project:
            self.current_project.save()
            logger.info(f"Проект сохранён: {self.current_project.name}")
        else:
            logger.warning("Нет открытого проекта для сохранения")
    
    def save_project_as(self, new_path: Path):
        """Сохранение проекта в новое место"""
        if self.current_project:
            self.current_project.save_as(new_path)
            logger.info(f"Проект сохранён как: {new_path}")
    
    def close_project(self):
        """Закрытие проекта"""
        if self.current_project:
            self.save_project()
            self.current_project = None
            logger.info("Проект закрыт")
    
    def get_recent_projects(self) -> List[Dict[str, str]]:
        """Получение списка недавних проектов"""
        return self.recent_projects.copy()
    
    def clear_recent_projects(self):
        """Очистка списка недавних проектов"""
        self.recent_projects.clear()
        self._save_recent_projects()
        logger.info("Список недавних проектов очищен")
    
    def _load_recent_projects(self):
        """Загрузка списка недавних проектов"""
        recent_file = self.config_dir / "recent_projects.json"
        
        if recent_file.exists():
            try:
                with open(recent_file, 'r', encoding='utf-8') as f:
                    self.recent_projects = json.load(f)
                logger.debug(f"Загружено {len(self.recent_projects)} недавних проектов")
            except Exception as e:
                logger.error(f"Ошибка загрузки списка недавних проектов: {e}")
                self.recent_projects = []
        else:
            self.recent_projects = []
    
    def _add_to_recent_projects(self, project_name: str, project_path: str):
        """Добавление проекта в список недавних"""
        # Удаление дубликатов
        self.recent_projects = [
            p for p in self.recent_projects 
            if p.get('path') != project_path
        ]
        
        # Добавление в начало списка
        self.recent_projects.insert(0, {
            'name': project_name,
            'path': project_path,
            'timestamp': datetime.now().isoformat()
        })
        
        # Ограничение списка 10 проектами
        self.recent_projects = self.recent_projects[:10]
        
        # Сохранение списка
        self._save_recent_projects()
    
    def _save_recent_projects(self):
        """Сохранение списка недавних проектов"""
        recent_file = self.config_dir / "recent_projects.json"
        
        try:
            with open(recent_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения списка недавних проектов: {e}")


# Глобальный экземпляр менеджера проектов
project_manager = ProjectManager()
