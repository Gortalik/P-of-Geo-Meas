"""
Модуль утилит для GeoAdjust Pro

Предоставляет общие функции для работы с ресурсами, логирования и другие вспомогательные функции.
"""

from pathlib import Path
from typing import Optional
import logging


def get_resource_path(resource_name: str) -> Path:
    """
    Получение пути к ресурсу независимо от режима установки.
    
    Работает как в режиме разработки, так и после установки пакета,
    а также в собранном приложении PyInstaller.
    
    Args:
        resource_name: Относительный путь к ресурсу внутри пакета
        
    Returns:
        Path: Путь к ресурсу
        
    Examples:
        >>> get_resource_path("gui/resources/icons/app_icon.ico")
        Path('/path/to/geoadjust/gui/resources/icons/app_icon.ico')
    """
    # Проверка режима PyInstaller
    import sys
    if getattr(sys, 'frozen', False):
        # Режим исполняемого файла PyInstaller
        application_path = Path(sys.executable).parent
        return application_path / resource_name
    
    try:
        # Для Python 3.9+ с использованием importlib.resources
        from importlib.resources import files
        return files('geoadjust').joinpath(resource_name)
    except (ImportError, Exception):
        # Попытка использовать backports
        try:
            from importlib_resources import files
            return files('geoadjust').joinpath(resource_name)
        except Exception:
            # Фоллбэк для режима разработки
            # Определяем базовый путь относительно этого файла
            current_file = Path(__file__).resolve()
            package_root = current_file.parent.parent  # geoadjust directory
            return package_root / resource_name


def setup_logging(
    log_file: Optional[str] = 'geoadjust.log',
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Настройка логирования приложения.
    
    Args:
        log_file: Имя файла для логов или None для отключения файлового логгера
        level: Уровень логирования
        console_output: Выводить ли логи в консоль
        
    Returns:
        Logger: Настроенный логгер
    """
    logger = logging.getLogger('geoadjust')
    logger.setLevel(level)
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
    
    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


__all__ = ['get_resource_path', 'setup_logging']
