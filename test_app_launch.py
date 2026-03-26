#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки запуска приложения P-of-Geo-Meas
"""

import sys
import os
from pathlib import Path

# Добавляем путь к исходному коду
src_path = Path("GeoAdjustPro/src").absolute()
sys.path.insert(0, str(src_path))

def test_application_launch():
    """Тест запуска приложения"""
    print("Тест запуска приложения P-of-Geo-Meas...")
    
    try:
        # Импортируем основной модуль
        from geoadjust import __main__
        
        print("✓ Импорт модуля выполнен успешно")
        print("Запуск приложения...")
        
        # Запускаем приложение
        __main__.main()
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"✗ Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_application_launch()
    if success:
        print("\n✓ Тест запуска приложения завершён успешно")
    else:
        print("\n✗ Тест запуска приложения завершился с ошибкой")
        sys.exit(1)