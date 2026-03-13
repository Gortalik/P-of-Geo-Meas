"""
GUI модуль для GeoAdjust Pro

Включает:
- widgets: кастомные виджеты (ribbon, таблицы, графика)
- dialogs: диалоговые окна (настройки, свойства проекта)
- components: компоненты интерфейса (док-панели, статус бар)
"""

from .main_window import MainWindow
from .project_manager import ProjectManager, ProjectFile, ProjectMetadata
from .dialogs.project_properties import ProjectPropertiesDialog
from .dialogs.program_settings import ProgramSettingsDialog

__all__ = [
    'MainWindow',
    'ProjectManager',
    'ProjectFile',
    'ProjectMetadata',
    'ProjectPropertiesDialog',
    'ProgramSettingsDialog'
]