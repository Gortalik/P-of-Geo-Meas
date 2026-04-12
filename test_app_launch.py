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
    """Test zapuska prilozhenija"""
    print("Test zapuska prilozhenija P-of-Geo-Meas...")

    try:
        # Importiruem osnovnoj modul
        from geoadjust import __main__

        print("[OK] Import modulia vypolnen uspeshno")
        print("Zapusk prilozhenija...")

        # Zapuskaem prilozhenie
        __main__.main()

    except ImportError as e:
        print(f"[ERROR] Oshibka importa: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Oshibka zapuska prilozhenija: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_application_launch()
    if success:
        print("\n[OK] Test zapuska prilozhenija zavershen uspeshno")
    else:
        print("\n[ERROR] Test zapuska prilozhenija zavershilsia s oshibkoj")
        sys.exit(1)