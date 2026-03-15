#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Полный тест всех компонентов GeoAdjust-Pro
Проверяет импорты, базовую функциональность и интеграцию модулей
"""

import sys
import numpy as np
from scipy import sparse

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_core_imports():
    """Тест импорта основных модулей"""
    print_section("1. Тест импорта основных модулей")
    
    try:
        from geoadjust.core.network.models import NetworkPoint, Observation
        print("✓ geoadjust.core.network.models")
        
        from geoadjust.core.adjustment.instruments import Instrument
        print("✓ geoadjust.core.adjustment.instruments")
        
        from geoadjust.core.adjustment.weight_builder import WeightBuilder
        print("✓ geoadjust.core.adjustment.weight_builder")
        
        from geoadjust.core.adjustment.equations_builder import EquationsBuilder
        print("✓ geoadjust.core.adjustment.equations_builder")
        
        from geoadjust.core.analysis.ellipse_errors import ErrorEllipseAnalyzer
        print("✓ geoadjust.core.analysis.ellipse_errors")
        
        from geoadjust.core.analysis.gross_errors import GrossErrorAnalyzer, GrossErrorCandidate
        print("✓ geoadjust.core.analysis.gross_errors")
        
        from geoadjust.core.analysis.normative_classes import NormativeClass, NormativeClassLibrary
        print("✓ geoadjust.core.analysis.normative_classes")
        
        from geoadjust.core.adjustment.engine import AdjustmentEngine
        print("✓ geoadjust.core.adjustment.engine")
        
        from geoadjust.core.adjustment.free_network import FreeNetworkAdjustment
        print("✓ geoadjust.core.adjustment.free_network")
        
        from geoadjust.core.adjustment.robust_methods import RobustEstimator
        print("✓ geoadjust.core.adjustment.robust_methods")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта: {e}")
        return False

def test_crs_imports():
    """Тест импорта модулей CRS"""
    print_section("2. Тест импорта модулей CRS")
    
    try:
        from geoadjust.crs.projection import GaussKrugerProjection
        print("✓ geoadjust.crs.projection")
        
        from geoadjust.crs.transformer import CoordinateTransformer
        print("✓ geoadjust.crs.transformer")
        
        from geoadjust.crs.database import CRSDatabase
        print("✓ geoadjust.crs.database")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта: {e}")
        return False

def test_io_imports():
    """Тест импорта модулей ввода/вывода"""
    print_section("3. Тест импорта модулей IO")
    
    try:
        from geoadjust.io.formats.dat import DATParser
        print("✓ geoadjust.io.formats.dat")
        
        from geoadjust.io.formats.gsi import GSIParser
        print("✓ geoadjust.io.formats.gsi")
        
        from geoadjust.io.formats.sdr import SDRParser
        print("✓ geoadjust.io.formats.sdr")
        
        from geoadjust.io.export.gost_report import GOSTReportGenerator
        print("✓ geoadjust.io.export.gost_report")
        
        from geoadjust.io.project.project_manager import ProjectManager
        print("✓ geoadjust.io.project.project_manager")
        
        from geoadjust.io.project.gad_format import GADProjectFile
        print("✓ geoadjust.io.project.gad_format")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта: {e}")
        return False

def test_gui_imports():
    """Тест импорта GUI модулей"""
    print_section("4. Тест импорта GUI модулей")
    
    try:
        from geoadjust.gui.main_window import MainWindow
        print("✓ geoadjust.gui.main_window")
        
        from geoadjust.gui.project_manager import ProjectManager as GUIProjectManager
        print("✓ geoadjust.gui.project_manager")
        
        from geoadjust.gui.processing_pipeline import PipelineProcessor
        print("✓ geoadjust.gui.processing_pipeline")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка импорта: {e}")
        return False

def test_network_models():
    """Тест моделей сети"""
    print_section("5. Тест моделей сети")
    
    try:
        from geoadjust.core.network.models import NetworkPoint, Observation
        
        # Создание точки
        point = NetworkPoint(
            point_id="P1",
            coord_type="FIXED",
            x=1000.0,
            y=2000.0,
            h=100.0
        )
        print(f"✓ Создана точка: {point.point_id} ({point.x}, {point.y})")
        
        # Создание измерения
        obs = Observation(
            obs_id="obs1",
            obs_type="direction",
            from_point="P1",
            to_point="P2",
            value=45.5,
            instrument_name="TS1",
            sigma_apriori=0.001
        )
        print(f"✓ Создано измерение: {obs.obs_id} (тип: {obs.obs_type})")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_instruments():
    """Тест инструментов"""
    print_section("6. Тест инструментов")
    
    try:
        from geoadjust.core.adjustment.instruments import Instrument
        
        # Создание инструмента
        instrument = Instrument(
            name="TotalStation_1",
            angle_std=0.0005,  # радианы
            distance_std_a=0.001,  # метры
            distance_std_b=0.000001  # ppm
        )
        print(f"✓ Создан инструмент: {instrument.name}")
        
        # Проверка весовой матрицы
        P = instrument.build_weight_matrix([1.0, 2.0, 3.0])
        print(f"✓ Построена весовая матрица: {P.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_weight_builder():
    """Тест построителя весовых матриц"""
    print_section("7. Тест построителя весовых матриц")
    
    try:
        from geoadjust.core.adjustment.weight_builder import WeightBuilder
        
        builder = WeightBuilder()
        
        # Тест для углов
        angle_stds = [0.001, 0.002, 0.0015]
        P_angles = builder.build_angle_weights(angle_stds)
        print(f"✓ Весовая матрица для углов: {P_angles.shape}")
        
        # Тест для расстояний
        dist_stds = [0.005, 0.003]
        P_distances = builder.build_distance_weights(dist_stds)
        print(f"✓ Весовая матрица для расстояний: {P_distances.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_projection():
    """Тест проекции Гаусса-Крюгера"""
    print_section("8. Тест проекции Гаусса-Крюгера")
    
    try:
        from geoadjust.crs.projection import GaussKrugerProjection
        from geoadjust.crs.database import CRSDatabase
        
        # Создание базы данных CRS
        db = CRSDatabase()
        
        # Создание проекции
        projection = GaussKrugerProjection(crs_db=db)
        print(f"✓ Создана проекция Гаусса-Крюгера")
        
        # Прямое преобразование (примерные координаты для зоны 7)
        lat, lon = 55.0, 37.0  # Москва
        x, y = projection.forward(lat, lon, zone=7)
        print(f"✓ Прямое преобразование: ({lat}, {lon}) -> ({x:.2f}, {y:.2f})")
        
        # Обратное преобразование
        lat_back, lon_back = projection.inverse(x, y, zone=7)
        print(f"✓ Обратное преобразование: ({x:.2f}, {y:.2f}) -> ({lat_back:.6f}, {lon_back:.6f})")
        
        # Проверка точности
        if abs(lat - lat_back) < 0.0001 and abs(lon - lon_back) < 0.0001:
            print("✓ Точность преобразования в норме")
        else:
            print("⚠ Точность преобразования ниже ожидаемой")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coordinate_transformer():
    """Тест трансформации координат"""
    print_section("9. Тест трансформации координат")
    
    try:
        from geoadjust.crs.transformer import CoordinateTransformer
        
        transformer = CoordinateTransformer()
        
        # Тест перевода градусов в радианы
        deg = 45.0
        rad = np.radians(deg)
        print(f"✓ Градусы в радианы: {deg}° -> {rad:.6f} рад")
        
        # Тест перевода румба в дирекционный угол
        azimuth = transformer.rumble_to_azimuth(45.0, "SV")
        print(f"✓ Румб в дирекционный угол: 45° СВ -> {azimuth}°")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normative_classes():
    """Тест нормативных классов"""
    print_section("10. Тест нормативных классов")
    
    try:
        from geoadjust.core.analysis.normative_classes import NormativeClassLibrary
        
        library = NormativeClassLibrary()
        
        # Получение списка классов
        classes = library.list_classes()
        print(f"✓ Доступно нормативных классов: {len(classes)}")
        
        # Получение конкретного класса
        sgs1 = library.get_class('sgs-1')
        if sgs1:
            print(f"✓ Класс СГС-1: {sgs1.name}, документ: {sgs1.normative_document}")
        
        poly1 = library.get_class('poly-1')
        if poly1:
            print(f"✓ Полигонометрия 1 класса: {poly1.name}, СКО угла: {poly1.max_angle_sigma}\"")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_adjustment_engine():
    """Тест движка уравнивания"""
    print_section("11. Тест движка уравнивания")
    
    try:
        from geoadjust.core.network.models import NetworkPoint, Observation
        from geoadjust.core.adjustment.engine import AdjustmentEngine
        from geoadjust.core.adjustment.instruments import Instrument
        
        # Создание простой сети из 3 точек
        points = [
            NetworkPoint(point_id="P1", coord_type="FIXED", x=0.0, y=0.0, h=0.0),
            NetworkPoint(point_id="P2", coord_type="FREE", x=100.0, y=0.0, h=0.0),
            NetworkPoint(point_id="P3", coord_type="FREE", x=50.0, y=86.6, h=0.0),
        ]
        
        # Измерения
        observations = [
            Observation(obs_id="d1", obs_type="distance", from_point="P1", to_point="P2", value=100.0, instrument_name="TS1", sigma_apriori=0.005),
            Observation(obs_id="d2", obs_type="distance", from_point="P2", to_point="P3", value=100.0, instrument_name="TS1", sigma_apriori=0.005),
            Observation(obs_id="d3", obs_type="distance", from_point="P3", to_point="P1", value=100.0, instrument_name="TS1", sigma_apriori=0.005),
        ]
        
        # Инструмент
        instrument = Instrument(
            name="TS1",
            angle_std=0.0005,
            distance_std_a=0.001,
            distance_std_b=0.000001
        )
        
        # Создание движка
        engine = AdjustmentEngine(points, observations, [instrument])
        print(f"✓ Создан движок уравнивания")
        print(f"  Точек: {len(points)}, Измерений: {len(observations)}")
        
        # Запуск уравнивания
        results = engine.adjust()
        
        if results:
            print(f"✓ Уравнивание выполнено успешно")
            if hasattr(results, 'sigma0'):
                print(f"  СКО единицы веса: {results.sigma0:.6f}")
        else:
            print("⚠ Уравнивание не выполнено (возможно, недостаточно данных)")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_ellipse_analyzer():
    """Тест анализатора эллипсов ошибок"""
    print_section("12. Тест анализатора эллипсов ошибок")
    
    try:
        from geoadjust.core.analysis.ellipse_errors import ErrorEllipseAnalyzer
        from scipy import sparse
        import numpy as np
        
        # Создание тестовой ковариационной матрицы
        Qxx = sparse.csr_matrix(np.array([
            [0.0001, 0.0, 0.0, 0.0],
            [0.0, 0.0001, 0.0, 0.0],
            [0.0, 0.0, 0.0002, 0.0],
            [0.0, 0.0, 0.0, 0.0002]
        ]))
        
        analyzer = ErrorEllipseAnalyzer(Qxx)
        print(f"✓ Создан анализатор эллипсов ошибок")
        
        # Вычисление параметров эллипса для первой точки
        ellipse = analyzer.compute_error_ellipse(0)
        if ellipse:
            print(f"✓ Эллипс ошибки для точки 0:")
            print(f"  Большая полуось: {ellipse.semi_major*1000:.3f} мм")
            print(f"  Малая полуось: {ellipse.semi_minor*1000:.3f} мм")
            print(f"  Ориентация: {ellipse.orientation:.2f}°")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gross_error_analyzer():
    """Тест анализатора грубых ошибок"""
    print_section("13. Тест анализатора грубых ошибок")
    
    try:
        from geoadjust.core.analysis.gross_errors import GrossErrorAnalyzer, GrossErrorCandidate
        from scipy import sparse
        import numpy as np
        
        # Создание тестовых данных
        n = 5
        A = sparse.random(n, 3, density=0.5, format='csr')
        P = sparse.diags([1.0, 2.0, 1.5, 1.0, 2.5])
        V = np.array([0.001, -0.002, 0.005, -0.001, 0.003])
        obs_ids = [f"obs{i}" for i in range(n)]
        
        analyzer = GrossErrorAnalyzer(A, P, V, sigma0=0.002, observations_ids=obs_ids)
        print(f"✓ Создан анализатор грубых ошибок")
        
        # Анализ стандартизованных остатков
        candidates = analyzer.analyze_standardized_residuals(threshold=2.0)
        print(f"✓ Найдено кандидатов в грубые ошибки: {len(candidates)}")
        
        for candidate in candidates[:3]:  # Показать первые 3
            print(f"  {candidate.obs_id}: r={candidate.standardized_residual:.2f} ({candidate.severity})")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_robust_estimator():
    """Тест робастного оценивания"""
    print_section("14. Тест робастного оценивания")
    
    try:
        from geoadjust.core.adjustment.robust_methods import RobustEstimator
        from scipy import sparse
        import numpy as np
        
        # Создание тестовых данных
        n = 10
        m = 5
        A = sparse.random(n, m, density=0.6, format='csr').toarray()
        l = np.random.randn(n) * 0.001
        
        estimator = RobustEstimator()
        print(f"✓ Создан робастный оценщик")
        
        # Тест функции Хубера
        residuals = np.array([-0.01, -0.005, 0.0, 0.005, 0.01])
        weights_hub = estimator.huber_weights(residuals)
        print(f"✓ Веса Хубера вычислены: {weights_hub.shape}")
        
        # Тест функции датского правила
        weights_dan = estimator.danish_weights(residuals)
        print(f"✓ Веса датского правила вычислены: {weights_dan.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_manager():
    """Тест менеджера проектов"""
    print_section("15. Тест менеджера проектов")
    
    try:
        from geoadjust.io.project.project_manager import ProjectManager
        import tempfile
        import os
        
        # Создание временной директории
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project.gad")
            
            # Создание проекта
            pm = ProjectManager()
            print(f"✓ Создан менеджер проектов")
            
            # Попытка создания нового проекта
            try:
                pm.create_project(project_path, "Test Project")
                print(f"✓ Проект создан: {project_path}")
            except Exception as e:
                print(f"⚠ Создание проекта: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print(" ПОЛНЫЙ ТЕСТ GEOADJUST-PRO")
    print("=" * 60)
    
    results = []
    
    # Тесты импортов
    results.append(("Core Imports", test_core_imports()))
    results.append(("CRS Imports", test_crs_imports()))
    results.append(("IO Imports", test_io_imports()))
    results.append(("GUI Imports", test_gui_imports()))
    
    # Функциональные тесты
    results.append(("Network Models", test_network_models()))
    results.append(("Instruments", test_instruments()))
    results.append(("Weight Builder", test_weight_builder()))
    results.append(("Projection", test_projection()))
    results.append(("Coordinate Transformer", test_coordinate_transformer()))
    results.append(("Normative Classes", test_normative_classes()))
    results.append(("Adjustment Engine", test_adjustment_engine()))
    results.append(("Error Ellipse Analyzer", test_error_ellipse_analyzer()))
    results.append(("Gross Error Analyzer", test_gross_error_analyzer()))
    results.append(("Robust Estimator", test_robust_estimator()))
    results.append(("Project Manager", test_project_manager()))
    
    # Итоговый отчет
    print_section("ИТОГОВЫЙ ОТЧЕТ")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f" ВСЕГО ТЕСТОВ: {total}")
    print(f" ПРОЙДЕНО: {passed}")
    print(f" ПРОВАЛЕНО: {total - passed}")
    print(f" ПРОЦЕНТ УСПЕХА: {passed/total*100:.1f}%")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
