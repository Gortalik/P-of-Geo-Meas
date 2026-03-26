"""
Модуль утилит для GeoAdjust Pro

Предоставляет общие функции для работы с ресурсами, логирования и другие вспомогательные функции.
"""

from datetime import datetime
import sys
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
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Настройка логирования приложения.
    
    Args:
        log_file: Имя файла для логов или None для авто-создания в temp
        level: Уровень логирования
        console_output: Выводить ли логи в консоль
        
    Returns:
        Logger: Настроенный логгер
    """
    import tempfile
    import os
    
    logger = logging.getLogger('geoadjust')
    logger.setLevel(logging.DEBUG)  # Всегда устанавливаем DEBUG для полной записи
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаем более подробный форматтер с информацией о файле и строке
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Определяем путь к файлу логов
    if log_file is None:
        # Автоматическое создание файла во временной директории
        log_dir = Path(tempfile.gettempdir()) / 'geoadjust_logs'
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = str(log_dir / f'geoadjust_{timestamp}.log')
        print(f"+ Логи сохраняются в: {log_file}")
    elif log_file == '':
        log_file = None
    
    # Обработчик для файла - всегда создаем для отладки
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            print(f"+ Файловое логирование включено: {log_file}")
        except Exception as e:
            print(f"- Warning: Could not create log file: {e}")
    
    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(detailed_formatter)
        logger.addHandler(console_handler)
    
    # Добавляем обработчик исключений для перехвата всех ошибок
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = exception_handler
    
    return logger


__all__ = ['get_resource_path', 'setup_logging']
