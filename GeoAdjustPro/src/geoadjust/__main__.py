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
    'chardet': 'chardet',
    'networkx': 'networkx',
    # pyproj удалён - используются собственные модули проекта (crs.transformer, crs.projection)
    # Все преобразования координат работают через встроенные реализации без внешних зависимостей
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


def main():
    """Основная функция запуска приложения"""
    # Вывод информации о запуске в консоль
    print("=" * 60)
    print("GeoAdjust Pro - Запуск приложения")
    print("=" * 60)
    print(f"Версия Python: {sys.version}")
    print(f"Платформа: {sys.platform}")
    print()
    
    # Проверка зависимостей
    print("Проверка зависимостей...")
    check_dependencies()
    print("✅ Все зависимости найдены")
    print()
    
    # Импорт утилит из центрального модуля
    from src.geoadjust.utils import get_resource_path, setup_logging
    
    # Настройка логирования
    logger = setup_logging()
    logger.info("Запуск GeoAdjust Pro...")
    print("Настройка логирования завершена")
    print()
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
    except ImportError as e:
        print(f"❌ Ошибка импорта PyQt5: {e}")
        print("Установите PyQt5: pip install PyQt5")
        sys.exit(1)
    
    # Создание приложения
    print("Создание QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("GeoAdjust Pro")
    app.setOrganizationName("GeoAdjust Team")
    app.setApplicationVersion("1.0.0")
    app.setStyle('Fusion')
    print("✅ QApplication создан")
    print()
    
    # Настройка шрифтов
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Импорт главного окна
    try:
        from src.geoadjust.gui.main_window import MainWindow, MainWindowConfig, InterfaceType
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
        print("Создание главного окна...")
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
        
        print("✅ Главное окно создано")
        print()
        print("Показ окна приложения...")
        window.show()
        logger.info("Приложение GeoAdjust Pro запущено")
        print("=" * 60)
        print("🎉 ПРИЛОЖЕНИЕ УСПЕШНО ЗАПУЩЕНО!")
        print("=" * 60)
    except Exception as e:
        logger.error(f"Ошибка создания главного окна: {e}")
        print(f"❌ Ошибка создания окна: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Запуск цикла событий
    print("Запуск цикла событий Qt...")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
