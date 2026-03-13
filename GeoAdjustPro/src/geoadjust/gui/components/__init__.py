"""
Модуль компонентов интерфейса
"""

from .dock_widgets import PointsDockWidget, ObservationsDockWidget, TraversesDockWidget
from .status_bar import StatusBar
from .tables import PointsTableView, ObservationsTableView

__all__ = [
    'PointsDockWidget',
    'ObservationsDockWidget', 
    'TraversesDockWidget',
    'StatusBar',
    'PointsTableView',
    'ObservationsTableView'
]
