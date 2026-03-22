"""
Модуль уравнивания геодезических сетей

Включает компоненты:
- AdjustmentEngine: движок уравнивания методом наименьших квадратов
- EquationsBuilder: построение матрицы коэффициентов уравнений поправок
- WeightBuilder: формирование весовой матрицы измерений
- FreeNetworkAdjustment: свободное уравнивание
- RobustMethods: робастные методы уравнивания
- Instrument: библиотека геодезических приборов

Примечание: Все модули работают без зависимости от scikit-sparse.
Используются стандартные методы SciPy (LU-разложение, сопряжённые градиенты).
"""

from .engine import AdjustmentEngine
from .equations_builder import EquationsBuilder
from .weight_builder import WeightBuilder
from .free_network import FreeNetworkAdjustment
from .robust_methods import RobustMethods
from .instruments import Instrument

__all__ = [
    'AdjustmentEngine',
    'EquationsBuilder',
    'WeightBuilder',
    'FreeNetworkAdjustment',
    'RobustMethods',
    'Instrument'
]
