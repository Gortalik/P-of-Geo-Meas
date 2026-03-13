"""
Ядро системы GeoAdjust-Pro

Включает модули:
- network: модели данных (пункты, измерения)
- preprocessing: предварительная обработка данных
- adjustment: уравнивание сетей
- reliability: анализ надёжности
- analysis: анализ результатов
- processing_pipeline: полный цикл обработки
"""

from .network.models import NetworkPoint, Observation
from .preprocessing.module import PreprocessingModule

# Эти модули требуют sksparse, импортируем с обработкой ошибок
try:
    from .adjustment.engine import AdjustmentEngine
    from .adjustment.equations_builder import EquationsBuilder
    from .adjustment.weight_builder import WeightBuilder
    ADJUSTMENT_AVAILABLE = True
except ImportError as e:
    AdjustmentEngine = None
    EquationsBuilder = None
    WeightBuilder = None
    ADJUSTMENT_AVAILABLE = False
    import warnings
    warnings.warn(f"Модули adjustment недоступны: {e}. Установите scikit-sparse.")

try:
    from .processing_pipeline import ProcessingPipeline
    PROCESSING_PIPELINE_AVAILABLE = True
except ImportError as e:
    ProcessingPipeline = None
    PROCESSING_PIPELINE_AVAILABLE = False
    import warnings
    warnings.warn(f"ProcessingPipeline недоступен: {e}")

__all__ = [
    'NetworkPoint',
    'Observation',
    'PreprocessingModule',
    'AdjustmentEngine',
    'EquationsBuilder',
    'WeightBuilder',
    'ProcessingPipeline'
]
