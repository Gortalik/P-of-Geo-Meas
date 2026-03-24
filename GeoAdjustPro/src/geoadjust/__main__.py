#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точка входа в приложение P-of-Geo-Meas

Запуск приложения:
    python -m geoadjust
    или
    geoadjust (после установки)
"""

import sys
import os
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
    print("P-of-Geo-Meas - Запуск приложения")
    print("=" * 60)
    print(f"Версия Python: {sys.version}")
    print(f"Платформа: {sys.platform}")
    print()
    
    try:
        # Проверка зависимостей
        print("Проверка зависимостей...")
        check_dependencies()
        print("✅ Все зависимости найдены")
        print()
        
        # Импорт утилит из центрального модуля
        from geoadjust.utils import get_resource_path, setup_logging
        
        # Настройка логирования
        logger = setup_logging()
        logger.info("=" * 60)
        logger.info("ЗАПУСК P-OF-GEO-MEAS")
        logger.info("=" * 60)
        logger.info(f"Версия Python: {sys.version}")
        logger.info(f"Платформа: {sys.platform}")
        logger.info(f"Текущая директория: {Path.cwd()}")
        logger.info("=" * 60)
        print("Настройка логирования завершена")
        print()
        
        try:
            from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QIcon
        except ImportError as e:
            print(f"❌ Ошибка импорта PyQt5: {e}")
            print("Установите PyQt5: pip install PyQt5")
            print("\nНажмите Enter для выхода...")
            try:
                input()
            except:
                pass
            sys.exit(1)
        
        # Создание приложения
        print("Создание QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("P-of-Geo-Meas")
        app.setOrganizationName("GeoAdjust Team")
        app.setApplicationVersion("1.0.0")
        app.setStyle('Fusion')
        print("✅ QApplication создан")
        print()
        
        # Настройка шрифтов
        font = app.font()
        font.setPointSize(10)
        app.setFont(font)
        
        # Импорт менеджера проектов и приветственного диалога
        try:
            from geoadjust.io.project.project_manager import ProjectManager
            from geoadjust.gui.welcome_dialog import WelcomeDialog
            from geoadjust.gui.main_window import MainWindow, MainWindowConfig, InterfaceType
        except ImportError as e:
            logger.error(f"Ошибка импорта компонентов: {e}")
            print(f"❌ Ошибка импорта: {e}")
            print("\nНажмите Enter для выхода...")
            try:
                input()
            except:
                pass
            sys.exit(1)
        
        # Создание менеджера проектов
        project_manager = ProjectManager()
        
        # Получение списка недавних проектов
        recent_projects = [p['path'] for p in project_manager.get_recent_projects()]
        
        # Создание и показ приветственного диалога
        print("Отображение приветственного диалога...")
        welcome_dialog = WelcomeDialog(recent_projects=recent_projects)
        
        # Обработчики сигналов приветственного диалога
        def create_new_project():
            """Создание нового проекта с настройками по умолчанию"""
            logger.info("Создание нового проекта с настройками по умолчанию")
            
            try:
                # Создание директории по умолчанию
                default_project_path = Path.home() / "P-of-Geo-Meas Projects"
                default_project_path.mkdir(parents=True, exist_ok=True)
                
                # Создание проекта с настройками по умолчанию
                project = project_manager.create_project(
                    project_path=default_project_path,
                    project_name="Новый проект"
                )
                
                # Сохранение проекта для создания всех файлов
                project.save()
                
                # Создание главного окна с проектом
                config = MainWindowConfig(
                    interface_type=InterfaceType.RIBBON,
                    window_title=f"P-of-Geo-Meas • Проект: {project.name}",
                    window_size=(1600, 900),
                    window_state="maximized",
                    theme="light"
                )
                main_window = MainWindow(config)
                main_window.current_project = project
                main_window.show()
                
                logger.info("Новый проект создан и отображён в главном окне")
                
            except Exception as e:
                logger.error(f"Ошибка создания проекта: {e}", exc_info=True)
                QMessageBox.critical(
                    None,
                    "Ошибка создания проекта",
                    f"Не удалось создать проект:\n{str(e)}"
                )
        
        def open_existing_project():
            """Открытие существующего проекта"""
            # Используем getExistingDirectory для выбора папки .gad
            # Так как проект - это директория с расширением .gad
            dir_path = QFileDialog.getExistingDirectory(
                None,
                "Открыть проект (выберите папку .gad)",
                str(Path.home()),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if dir_path:
                project_path = Path(dir_path)
                # Проверяем, что выбранная директория имеет расширение .gad или содержит project.gadproj
                if not (project_path.suffix == '.gad' or (project_path / 'project.gadproj').exists()):
                    QMessageBox.warning(
                        None,
                        "Неверный формат проекта",
                        "Выбранная папка не является проектом P-of-Geo-Meas.\n"
                        "Проект должен быть папкой с расширением .gad и содержать файл project.gadproj."
                    )
                    return
                
                try:
                    project = project_manager.open_project(project_path)
                    
                    # Создание главного окна с проектом
                    config = MainWindowConfig(
                        interface_type=InterfaceType.RIBBON,
                        window_title=f"P-of-Geo-Meas • Проект: {project.name}",
                        window_size=(1600, 900),
                        window_state="maximized",
                        theme="light"
                    )
                    main_window = MainWindow(config)
                    main_window.current_project = project
                    main_window.show()
                    
                    logger.info(f"Проект открыт: {dir_path}")
                    
                except Exception as e:
                    logger.error(f"Ошибка открытия проекта: {e}", exc_info=True)
                    QMessageBox.critical(
                        None,
                        "Ошибка открытия проекта",
                        f"Не удалось открыть проект:\n{str(e)}"
                    )
        
        def open_recent_project(project_path):
            """Открытие недавнего проекта"""
            try:
                project = project_manager.open_project(Path(project_path))
                
                # Создание главного окна с проектом
                config = MainWindowConfig(
                    interface_type=InterfaceType.RIBBON,
                    window_title=f"P-of-Geo-Meas • Проект: {project.name}",
                    window_size=(1600, 900),
                    window_state="maximized",
                    theme="light"
                )
                main_window = MainWindow(config)
                main_window.current_project = project
                main_window.show()
                
                logger.info(f"Недавний проект открыт: {project_path}")
                
            except Exception as e:
                logger.error(f"Ошибка открытия недавнего проекта: {e}", exc_info=True)
                QMessageBox.critical(
                    None,
                    "Ошибка открытия проекта",
                    f"Не удалось открыть проект:\n{str(e)}"
                )
        
        # Подключение сигналов
        welcome_dialog.new_project_requested.connect(create_new_project)
        welcome_dialog.open_project_requested.connect(open_existing_project)
        welcome_dialog.recent_project_requested.connect(open_recent_project)
        
        # Отображение приветственного диалога
        logger.info("Отображение приветственного диалога")
        welcome_dialog.exec_()
        
        # Если диалог закрыт без выбора действия - выйти
        if not welcome_dialog.result():
            logger.info("Приложение закрыто пользователем из приветственного диалога")
            print("=" * 60)
            print("Приложение закрыто")
            print("=" * 60)
            sys.exit(0)
        
        # Запуск главного цикла приложения
        logger.info("Запуск главного цикла приложения Qt")
        print("=" * 60)
        print("🎉 ПРИЛОЖЕНИЕ УСПЕШНО ЗАПУЩЕНО!")
        print("=" * 60)
        exit_code = app.exec_()
        
        # Если произошла ошибка, оставляем консоль открытой для просмотра ошибки
        if exit_code != 0:
            print(f"\n❌ Приложение завершилось с кодом ошибки: {exit_code}")
            print("Нажмите Enter для выхода...")
            try:
                input()
            except:
                pass
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        print("\nНажмите Enter для выхода...")
        try:
            input()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
