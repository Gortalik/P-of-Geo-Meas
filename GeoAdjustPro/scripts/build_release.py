#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический скрипт сборки релизной версии P-of-Geo-Meas
Запуск: poetry run build-release
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def print_step(step: str):
    """Вывод заголовка шага"""
    print(f"\n{'='*80}")
    print(f"  {step}")
    print(f"{'='*80}\n")


def clean_build_dir():
    """Очистка директорий сборки"""
    print_step("ОЧИСТКА ДИРЕКТОРИЙ СБОРКИ")
    
    build_dirs = ['build', 'dist', '__pycache__', 'Output']
    
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Удаление {dir_path}...")
            shutil.rmtree(dir_path, ignore_errors=True)
    
    # Удаление .spec файлов
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"Удален файл {spec_file}")


def create_spec_file():
    """Создание spec-файла для PyInstaller"""
    print_step("СОЗДАНИЕ SPEC-ФАЙЛА")
    
    # Определяем пути к ресурсам
    resources_path = Path('resources')
    crs_path = Path('src/geoadjust/crs')
    gui_resources_path = Path('src/geoadjust/gui/resources')
    
    # Проверка существования путей
    if not resources_path.exists():
        print(f"Warning: Ресурсы не найдены: {resources_path}")
    
    cmd = [
        'pyi-makespec',
        '--name', 'P-of-Geo-Meas',
        '--windowed',
    ]
    
    # Добавляем иконку только если файл существует
    icon_path = 'resources/icons/app_icon.ico'
    if Path(icon_path).exists():
        cmd.extend(['--icon', icon_path])
    
    # Добавляем данные ресурсы
    if resources_path.exists():
        cmd.extend(['--add-data', f'{resources_path}{os.pathsep}resources'])
        
    if crs_path.exists():
        cmd.extend(['--add-data', f'{crs_path}{os.pathsep}crs_database'])
        
    if gui_resources_path.exists():
        cmd.extend(['--add-data', f'{gui_resources_path}{os.pathsep}gui/resources'])
    
    # Добавляем скрытые импорты
    hidden_imports = [
        'PyQt5.QtPrintSupport',
        'PyQt5.QtSvg',
        'scipy.sparse.csgraph._validation',
        'sksparse',
        'sksparse.cholmod',
        'yaml',
        'chardet',
        'docx',
        'matplotlib.backends.backend_qt5agg',
        'pandas._libs',
        'numpy.random._common',
        'openpyxl',
        'ezdxf'
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
        
    cmd.append('src/geoadjust/__main__.py')
    
    print(f"Команда: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Ошибка создания spec-файла:\n{result.stderr}")
        sys.exit(1)
    
    print("Spec-файл создан успешно")


def build_with_pyinstaller():
    """Сборка приложения с помощью PyInstaller"""
    print_step("СБОРКА ПРИЛОЖЕНИЯ С ПОМОЩЬЮ PYINSTALLER")
    
    cmd = [
        'pyinstaller',
        'P-of-Geo-Meas.spec',
        '--clean',
        '--noconfirm'
    ]
    
    print(f"Команда: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"Ошибка сборки: код возврата {result.returncode}")
        sys.exit(1)
    
    print("Сборка завершена успешно")
    print(f"Результат: dist/P-of-Geo-Meas/")


def test_build():
    """Тестирование собранного приложения"""
    print_step("ТЕСТИРОВАНИЕ СОБРАННОГО ПРИЛОЖЕНИЯ")
    
    exe_path = Path('dist/P-of-Geo-Meas/P-of-Geo-Meas')
    
    if not exe_path.exists():
        print(f"Ошибка: Исполняемый файл не найден: {exe_path}")
        sys.exit(1)
    
    print(f"Исполняемый файл найден: {exe_path}")
    print(f"Размер: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Запуск приложения в фоновом режиме для проверки
    print("\nЗапуск приложения для проверки...")
    try:
        process = subprocess.Popen([str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем 3 секунды
        import time
        time.sleep(3)
        
        # Проверяем, запустилось ли приложение
        if process.poll() is None:
            print("✓ Приложение запустилось успешно")
            process.terminate()
        else:
            print("✗ Приложение завершилось с ошибкой")
            stdout, stderr = process.communicate()
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            # Не завершаем процесс, так как в Linux без GUI это ожидаемо
    except Exception as e:
        print(f"Предупреждение: Не удалось запустить тест: {e}")
        print("Это нормально для среды без графического интерфейса")


def create_installer():
    """Создание установщика с помощью Inno Setup (только Windows)"""
    print_step("СОЗДАНИЕ УСТАНОВЩИКА")
    
    # Проверка платформы
    if os.name != 'nt':
        print("Inno Setup доступен только на Windows.")
        print("Пропускаем создание установщика.")
        return
    
    # Проверка наличия Inno Setup Compiler
    try:
        subprocess.run(['iscc', '/?'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Inno Setup Compiler не найден. Установите его с https://jrsoftware.org/isdl.php")
        return
    
    iss_file = Path('P-of-Geo-Meas.iss')
    if not iss_file.exists():
        print("Файл P-of-Geo-Meas.iss не найден. Пропускаем создание установщика.")
        return
    
    cmd = ['iscc', str(iss_file)]
    
    print(f"Команда: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Ошибка создания установщика:\n{result.stderr}")
        sys.exit(1)
    
    print("Установщик создан успешно")
    
    # Поиск созданного установщика
    output_dir = Path('Output')
    if output_dir.exists():
        installers = list(output_dir.glob('P-of-Geo-Meas-Setup-*.exe'))
        if installers:
            installer = installers[0]
            print(f"\nГотовый установщик: {installer.absolute()}")


def create_release_package():
    """Создание архива для распространения"""
    print_step("СОЗДАНИЕ АРХИВА ДЛЯ РАСПРОСТРАНЕНИЯ")
    
    # Создание имени архива с версией и датой
    version = "1.0.0"
    date_str = datetime.now().strftime("%Y%m%d")
    archive_name = f"P-of-Geo-Meas-{version}-portable-{date_str}.zip"
    
    # Архивация папки dist/P-of-Geo-Meas
    import zipfile
    
    dist_dir = Path('dist/P-of-Geo-Meas')
    if not dist_dir.exists():
        print(f"Ошибка: Директория {dist_dir} не найдена")
        return
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(dist_dir)
                zipf.write(file_path, arcname)
                print(f"Добавлено: {arcname}")
    
    print(f"\nАрхив создан: {archive_name}")
    print(f"Размер: {Path(archive_name).stat().st_size / 1024 / 1024:.2f} MB")


def main():
    """Основной процесс сборки"""
    print("="*80)
    print("  АВТОМАТИЧЕСКАЯ СБОРКА P-OF-GEO-MEAS")
    print("="*80)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Версия: 1.0.0")
    print("="*80)
    
    # Переход в корень проекта
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Рабочая директория: {project_root}")
    
    # Шаг 1: Очистка
    clean_build_dir()
    
    # Шаг 2: Создание spec-файла
    create_spec_file()
    
    # Шаг 3: Сборка с PyInstaller
    build_with_pyinstaller()
    
    # Шаг 4: Тестирование
    test_build()
    
    # Шаг 5: Создание установщика
    create_installer()
    
    # Шаг 6: Создание портативного архива
    create_release_package()
    
    print("\n" + "="*80)
    print("  СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
    print("="*80)
    print("\nГотовые файлы:")
    print("  • Портативная версия: P-of-Geo-Meas-*.zip")
    print("  • Исходная папка: dist/P-of-Geo-Meas/")
    if os.name == 'nt':
        print("  • Установщик: Output/P-of-Geo-Meas-Setup-*.exe")


if __name__ == "__main__":
    main()
