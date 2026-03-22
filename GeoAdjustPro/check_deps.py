#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка установки критических зависимостей для GeoAdjust Pro

Запустите этот скрипт перед сборкой приложения, чтобы убедиться,
что все необходимые зависимости установлены корректно.
"""

import sys
import importlib

CRITICAL_DEPS = [
    ('numpy', 'numpy'),
    ('scipy', 'scipy'),
    ('PyQt5', 'PyQt5.QtWidgets'),
    ('scikit-sparse', 'sksparse.cholmod'),
    ('pyproj', 'pyproj'),
    ('networkx', 'networkx'),
    ('matplotlib', 'matplotlib'),
    ('pandas', 'pandas'),
    ('python-docx', 'docx'),
    ('openpyxl', 'openpyxl'),
    ('Pillow', 'PIL'),
    ('chardet', 'chardet'),
    ('PyYAML', 'yaml'),
    ('ezdxf', 'ezdxf'),
]

print("=" * 80)
print("ПРОВЕРКА УСТАНОВКИ КРИТИЧЕСКИХ ЗАВИСИМОСТЕЙ")
print("=" * 80)
print()

all_ok = True
critical_missing = []

for package_name, module_name in CRITICAL_DEPS:
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name:25s} - УСТАНОВЛЕН")
    except ImportError as e:
        print(f"❌ {package_name:25s} - ОТСУТСТВУЕТ ({e})")
        all_ok = False
        critical_missing.append(package_name)

print()
print("=" * 80)

if all_ok:
    print("✅ ВСЕ КРИТИЧЕСКИЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ")
    print()
    print("Можно запускать сборку:")
    print("  cd GeoAdjustPro")
    print("  pyinstaller P-of-Geo-Meas.spec --clean --noconfirm")
else:
    print("⚠️  НЕКОТОРЫЕ КРИТИЧЕСКИЕ ЗАВИСИМОСТИ ОТСУТСТВУЮТ")
    print()
    print("Отсутствующие пакеты:")
    for pkg in critical_missing:
        print(f"  - {pkg}")
    print()
    print("Рекомендуемые действия:")
    
    if 'scikit-sparse' in critical_missing:
        print()
        print("🔴 ВАЖНО: scikit-sparse требует особого подхода:")
        print("   Вариант 1 (рекомендуется): Использовать Conda")
        print("     conda install -c conda-forge scikit-sparse")
        print()
        print("   Вариант 2: Скачать .whl файл")
        print("     https://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-sparse")
        print("     pip install путь\\к\\файлу.whl")
        print()
    
    if 'ezdxf' in critical_missing or 'PyYAML' in critical_missing:
        print()
        print("📦 Остальные пакеты можно установить через pip:")
        print("   pip install ezdxf PyYAML")
        print()
        print("   С использованием китайского зеркала (если проблемы с сетью):")
        print("   pip install ezdxf PyYAML --index-url https://pypi.tuna.tsinghua.edu.cn/simple")
        print()

print("=" * 80)

sys.exit(0 if all_ok else 1)
