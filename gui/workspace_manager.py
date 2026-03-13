"""
GeoAdjust Pro - Менеджер конфигураций рабочей области
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import QDockWidget


class WorkspaceManager:
    """Менеджер конфигураций рабочей области"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.configurations: Dict[str, Dict] = {}
        self.current_config: str = "default"
        
        self._load_configurations()
    
    def _load_configurations(self):
        """Загрузка конфигураций из файла"""
        config_file = Path.home() / ".geoadjust" / "workspaces.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configurations = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки конфигураций: {e}")
                self._create_default_configurations()
        else:
            self._create_default_configurations()
    
    def _create_default_configurations(self):
        """Создание конфигураций по умолчанию"""
        # Конфигурация "Измерения и ходы"
        self.configurations["measurements_traverses"] = {
            "name": "Измерения и ходы",
            "docks": {
                "left": ["points_dock", "observations_dock"],
                "right": ["traverses_dock", "properties_dock"],
                "bottom": ["log_dock"],
                "right_bottom": ["plan_dock"]
            },
            "visibility": {
                "points_dock": True,
                "observations_dock": True,
                "traverses_dock": True,
                "plan_dock": True,
                "log_dock": True,
                "properties_dock": True
            },
            "sizes": {
                "main_splitter": [400, 800],
                "left_splitter": [300, 300],
                "right_splitter": [400, 200]
            }
        }
        
        # Конфигурация "Одно окно"
        self.configurations["single_window"] = {
            "name": "Одно окно",
            "docks": {
                "center": ["plan_dock"]
            },
            "visibility": {
                "points_dock": False,
                "observations_dock": False,
                "traverses_dock": False,
                "plan_dock": True,
                "log_dock": False,
                "properties_dock": False
            }
        }
        
        # Конфигурация "Таблицы"
        self.configurations["tables"] = {
            "name": "Таблицы",
            "docks": {
                "left": ["points_dock", "observations_dock"],
                "right": ["properties_dock"]
            },
            "visibility": {
                "points_dock": True,
                "observations_dock": True,
                "traverses_dock": False,
                "plan_dock": False,
                "log_dock": True,
                "properties_dock": True
            },
            "sizes": {
                "main_splitter": [600, 600],
                "left_splitter": [300, 300]
            }
        }
        
        # Конфигурация "Анализ"
        self.configurations["analysis"] = {
            "name": "Анализ",
            "docks": {
                "left": ["points_dock"],
                "right": ["plan_dock", "properties_dock"],
                "bottom": ["log_dock"]
            },
            "visibility": {
                "points_dock": True,
                "observations_dock": False,
                "traverses_dock": False,
                "plan_dock": True,
                "log_dock": True,
                "properties_dock": True
            },
            "sizes": {
                "main_splitter": [300, 900],
                "right_splitter": [600, 300]
            }
        }
        
        # Сохранение конфигураций по умолчанию
        self._save_configurations()
    
    def apply_configuration(self, config_name: str):
        """Применение конфигурации"""
        if config_name not in self.configurations:
            print(f"Конфигурация '{config_name}' не найдена")
            return
        
        config = self.configurations[config_name]
        self.current_config = config_name
        
        # Применение видимости доков
        for dock_name, visible in config.get("visibility", {}).items():
            dock = self._get_dock_by_name(dock_name)
            if dock:
                dock.setVisible(visible)
        
        # Применение размеров
        if "sizes" in config:
            self._apply_sizes(config["sizes"])
        
        print(f"Применена конфигурация: {config_name}")
    
    def save_current_configuration(self, config_name: str):
        """Сохранение текущей конфигурации"""
        config = {
            "name": config_name,
            "docks": self._get_current_docks_layout(),
            "visibility": self._get_current_visibility(),
            "sizes": self._get_current_sizes()
        }
        
        self.configurations[config_name] = config
        self._save_configurations()
        
        print(f"Конфигурация сохранена: {config_name}")
    
    def _get_dock_by_name(self, dock_name: str) -> Optional[QDockWidget]:
        """Получение дока по имени"""
        if hasattr(self.main_window, dock_name):
            return getattr(self.main_window, dock_name)
        return None
    
    def _get_current_docks_layout(self) -> Dict[str, List[str]]:
        """Получение текущей раскладки доков"""
        layout = {
            "left": [],
            "right": [],
            "top": [],
            "bottom": []
        }
        
        # Определение расположения доков
        dock_areas = {
            "points_dock": None,
            "observations_dock": None,
            "traverses_dock": None,
            "plan_dock": None,
            "log_dock": None,
            "properties_dock": None
        }
        
        for dock_name in dock_areas.keys():
            dock = self._get_dock_by_name(dock_name)
            if dock:
                area = self.main_window.dockWidgetArea(dock)
                if area == 1:  # LeftDockWidgetArea
                    layout["left"].append(dock_name)
                elif area == 2:  # RightDockWidgetArea
                    layout["right"].append(dock_name)
                elif area == 4:  # TopDockWidgetArea
                    layout["top"].append(dock_name)
                elif area == 8:  # BottomDockWidgetArea
                    layout["bottom"].append(dock_name)
        
        return layout
    
    def _get_current_visibility(self) -> Dict[str, bool]:
        """Получение текущей видимости доков"""
        visibility = {}
        
        dock_names = [
            "points_dock",
            "observations_dock",
            "traverses_dock",
            "plan_dock",
            "log_dock",
            "properties_dock"
        ]
        
        for dock_name in dock_names:
            dock = self._get_dock_by_name(dock_name)
            if dock:
                visibility[dock_name] = dock.isVisible()
        
        return visibility
    
    def _get_current_sizes(self) -> Dict[str, List[int]]:
        """Получение текущих размеров"""
        sizes = {}
        
        if hasattr(self.main_window, 'main_splitter'):
            sizes["main_splitter"] = self.main_window.main_splitter.sizes()
        
        return sizes
    
    def _apply_sizes(self, sizes: Dict[str, List[int]]):
        """Применение размеров"""
        for splitter_name, size_list in sizes.items():
            if hasattr(self.main_window, splitter_name):
                splitter = getattr(self.main_window, splitter_name)
                splitter.setSizes(size_list)
    
    def _save_configurations(self):
        """Сохранение конфигураций в файл"""
        config_file = Path.home() / ".geoadjust" / "workspaces.json"
        config_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configurations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигураций: {e}")
    
    def get_available_configurations(self) -> List[str]:
        """Получение списка доступных конфигураций"""
        return [config["name"] for config in self.configurations.values()]
    
    def delete_configuration(self, config_name: str) -> bool:
        """Удаление конфигурации"""
        if config_name in ["measurements_traverses", "single_window"]:
            print("Нельзя удалить встроенную конфигурацию")
            return False
        
        if config_name in self.configurations:
            del self.configurations[config_name]
            self._save_configurations()
            return True
        
        return False
