"""
Модуль компонентов интерфейса
"""

from .dock_widgets import PointsDockWidget, ObservationsDockWidget, TraversesDockWidget
from .tables import PointsTableView, ObservationsTableView

__all__ = [
    'PointsDockWidget',
    'ObservationsDockWidget', 
    'TraversesDockWidget',
    'PointsTableView',
    'ObservationsTableView'
]
