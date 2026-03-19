#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа в приложение GeoAdjust Pro

Запуск приложения:
    python -m geoadjust
    или
    geoadjust (после установки)
"""

import sys
import logging
from pathlib import Path

# Проверка версии Python
if sys.version_info < (3, 8):
    print("❌ ТРЕБУЕТСЯ PYTHON 3.8 ИЛИ ВЫШЕ")
    print(f"   Установлена версия: {sys.version}")
    sys.exit(1)


# Проверка зависимостей при запуске
REQUIRED_PACKAGES = {
    'numpy': 'numpy',
    'scipy': 'scipy',
    'PyQt5': 'PyQt5',
    'scikit-sparse': 'sksparse',
    'chardet': 'chardet',
    'networkx': 'networkx',
    'pyproj': 'pyproj',
    'pandas': 'pandas'
}


def check_dependencies():
    """Проверка наличия всех зависимостей"""
    missing = []
    for package_name, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("❌ ОТСУТСТВУЮТ НЕОБХОДИМЫЕ ЗАВИСИМОСТИ:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nУстановите зависимости командой:")
        print("   pip install -r requirements.txt")
        sys.exit(1)


def get_resource_path(resource_name: str) -> Path:
    """
    Получение пути к ресурсу независимо от режима установки.
    
    Работает как в режиме разработки, так и после установки пакета.
    
    Args:
        resource_name: Относительный путь к ресурсу внутри пакета
        
    Returns:
        Path: Путь к ресурсу
    """
    try:
        # Для Python 3.9+ с использованием importlib.resources
        from importlib.resources import files
        return files('geoadjust').joinpath(resource_name)
    except (ImportError, Exception):
        # Резервный вариант для разработки или старых версий Python
        try:
            # Попытка использовать backports
            from importlib_resources import files
            return files('geoadjust').joinpath(resource_name)
        except Exception:
            # Фоллбэк для режима разработки
            return Path(__file__).parent.parent / resource_name


def setup_logging(log_file: str = 'geoadjust.log') -> logging.Logger:
    """
    Настройка логирования приложения.
    
    Args:
        log_file: Имя файла для логов
        
    Returns:
        Logger: Настроенный логгер
    """
    logger = logging.getLogger('geoadjust')
    logger.setLevel(logging.INFO)
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def main():
    """Основная функция запуска приложения"""
    # Проверка зависимостей
    check_dependencies()
    
    # Настройка логирования
    logger = setup_logging()
    logger.info("Запуск GeoAdjust Pro...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
    except ImportError as e:
        print(f"❌ Ошибка импорта PyQt5: {e}")
        print("Установите PyQt5: pip install PyQt5")
        sys.exit(1)
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("GeoAdjust Pro")
    app.setOrganizationName("GeoAdjust Team")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')
    
    # Настройка шрифтов
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Импорт главного окна
    try:
        from geoadjust.gui.main_window import MainWindow, MainWindowConfig, InterfaceType
    except ImportError as e:
        logger.error(f"Ошибка импорта главного окна: {e}")
        print(f"❌ Ошибка импорта: {e}")
        sys.exit(1)
    
    # Создание конфигурации
    config = MainWindowConfig(
        interface_type=InterfaceType.RIBBON,
        window_title="GeoAdjust Pro",
        window_size=(1600, 900),
        window_state="maximized",
        theme="light"
    )
    
    # Создание и показ главного окна
    try:
        window = MainWindow(config)
        
        # Попытка установить иконку приложения
        try:
            icon_path = get_resource_path("gui/resources/icons/app_icon.ico")
            if hasattr(icon_path, 'exists') and icon_path.exists():
                window.setWindowIcon(QIcon(str(icon_path)))
            else:
                # Использовать стандартную иконку
                window.setWindowIcon(QIcon.fromTheme("applications-science"))
                logger.warning(f"Иконка не найдена: {icon_path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
            # Продолжить без иконки
        
        window.show()
        logger.info("Приложение GeoAdjust Pro запущено")
    except Exception as e:
        logger.error(f"Ошибка создания главного окна: {e}")
        print(f"❌ Ошибка создания окна: {e}")
        sys.exit(1)
    
    # Запуск цикла событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
