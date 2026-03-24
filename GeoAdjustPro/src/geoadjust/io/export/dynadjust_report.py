"""
Модуль генерации отчётов об уравнивании по структуре DynAdjust
с адаптацией под ГОСТ РФ

Вдохновлено реализацией DynAdjust с учётом российских стандартов
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np


class ReportGenerator:
    """
    Генератор отчётов об уравнивании в формате, вдохновлённом DynAdjust
    с адаптацией под ГОСТ 7.32-2017
    """
    
    def __init__(self):
        self.report_lines = []
    
    def _add_line(self, text: str = ""):
        """Добавление строки в отчёт"""
        self.report_lines.append(text)
    
    def _add_separator(self, char: str = "=", length: int = 80):
        """Добавление разделителя"""
        self._add_line(char * length)
    
    def _add_section_header(self, title: str):
        """Добавление заголовка раздела"""
        self._add_line()
        self._add_line(title.upper())
        self._add_separator("-", 80)
    
    def generate_adjustment_report(self, project: Any, result: Dict[str, Any]) -> str:
        """
        Генерация полного отчёта об уравнивании
        
        Параметры:
        - project: объект проекта с атрибутами name и points
        - result: словарь с результатами уравнивания
        
        Возвращает:
        - Текстовый отчёт
        """
        self.report_lines = []
        
        # 1. Заголовок отчёта
        self._add_separator("=")
        self._add_line("ОТЧЁТ ОБ УРАВНИВАНИИ ГЕОДЕЗИЧЕСКОЙ СЕТИ")
        self._add_line("(вдохновлено DynAdjust с адаптацией под ГОСТ РФ)")
        self._add_separator("=")
        self._add_line(f"Проект: {getattr(project, 'name', 'Неизвестно')}")
        self._add_line(f"Дата обработки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        self._add_line(f"Метод уравнивания: {result.get('method', 'Классический МНК')}")
        self._add_line(f"Тип сети: {result.get('network_type', 'Не определён')}")
        self._add_line()
        
        # 2. Статистика сети
        self._add_section_header("Статистика сети")
        self._add_line(f"Число пунктов всего: {result.get('num_points', 0)}")
        self._add_line(f"  в том числе исходных: {result.get('num_fixed_points', 0)}")
        self._add_line(f"  определяемых: {result.get('num_unknown_points', 0)}")
        self._add_line(f"Число измерений: {result.get('num_observations', 0)}")
        self._add_line(f"Число неизвестных: {result.get('num_unknowns', 0)}")
        self._add_line(f"Степень свободы (избыточность): {result.get('redundancy', 0):.2f}")
        self._add_line()
        
        # 3. Результаты уравнивания
        self._add_section_header("Результаты уравнивания")
        self._add_line(f"СКО единицы веса (апостериорное): σ₀ = {result.get('sigma0', 0.0):.6f}")
        self._add_line(f"Число итераций: {result.get('iterations', 1)}")
        self._add_line(f"Сходимость: {'ДОСТИГНУТА' if result.get('convergence', True) else 'НЕ ДОСТИГНУТА'}")
        
        # Максимальные поправки
        if 'max_corrections' in result:
            max_corr = result['max_corrections']
            self._add_line(f"Максимальная поправка по X: {max_corr.get('max_dx', 0.0)*1000:.2f} мм")
            self._add_line(f"Максимальная поправка по Y: {max_corr.get('max_dy', 0.0)*1000:.2f} мм")
            self._add_line(f"Максимальная поправка по H: {max_corr.get('max_dh', 0.0)*1000:.2f} мм")
        self._add_line()
        
        # 4. Анализ надёжности (вдохновлено DynAdjust)
        if 'reliability' in result:
            self._add_section_header("Анализ надёжности сети (по методике DynAdjust)")
            rel = result['reliability']
            
            # Основные метрики
            self._add_line(f"Средняя избыточность измерений: {rel.get('mean_redundancy', 0.0):.4f}")
            self._add_line(f"Минимальная избыточность: {rel.get('min_redundancy', 0.0):.4f}")
            self._add_line(f"Максимальная внешняя надёжность: {rel.get('max_external_reliability', 0.0)*1000:.3f} мм")
            
            # Кандидаты на грубые ошибки
            gross_candidates = rel.get('gross_error_candidates', [])
            self._add_line(f"Кандидаты на грубые ошибки (избыточность < 0.1): {len(gross_candidates)}")
            if gross_candidates and len(gross_candidates) <= 10:
                self._add_line(f"  Индексы измерений: {gross_candidates}")
            
            # Ненадёжные измерения
            unreliable = rel.get('unreliable_measurements', [])
            self._add_line(f"Измерения с высокой внешней надёжностью (>5 см): {len(unreliable)}")
            if unreliable and len(unreliable) <= 10:
                self._add_line(f"  Индексы измерений: {unreliable}")
            
            # Критическое значение
            critical_value = rel.get('critical_value', 3.0)
            self._add_line(f"Критическое значение для обнаружения грубых ошибок: {critical_value}")
            self._add_line()
        
        # 5. Ведомость уравненных координат
        self._add_section_header("Ведомость уравненных координат")
        
        # Заголовок таблицы
        header = f"{'Пункт':<15} {'Тип':<12} {'X, м':<18} {'Y, м':<18} {'H, м':<15} {'σx, мм':<10} {'σy, мм':<10} {'σh, мм':<10}"
        self._add_line(header)
        self._add_separator("-")
        
        # Вывод пунктов
        points = getattr(project, 'points', [])
        if points:
            # Сортировка по типу (исходные первыми)
            sorted_points = sorted(points, key=lambda p: (
                0 if getattr(p, 'coord_type', 'FREE') == 'FIXED' else 1,
                p.point_id
            ))
            
            for point in sorted_points[:50]:  # Ограничение на вывод (первые 50)
                coord_type = getattr(point, 'coord_type', 'FREE')
                type_str = 'Исходный' if coord_type == 'FIXED' else 'Определяемый'
                
                sigma_x_mm = getattr(point, 'sigma_x', 0.0) * 1000
                sigma_y_mm = getattr(point, 'sigma_y', 0.0) * 1000
                sigma_h_mm = getattr(point, 'sigma_h', 0.0) * 1000
                
                self._add_line(
                    f"{point.point_id:<15} {type_str:<12} "
                    f"{point.x:<18.4f} {point.y:<18.4f} {getattr(point, 'h', 0.0):<15.4f} "
                    f"{sigma_x_mm:<10.2f} {sigma_y_mm:<10.2f} {sigma_h_mm:<10.2f}"
                )
            
            if len(sorted_points) > 50:
                self._add_line(f"... и ещё {len(sorted_points) - 50} пунктов")
        else:
            self._add_line("Нет данных о пунктах")
        
        self._add_line()
        
        # 6. Анализ остатков измерений
        if 'residuals' in result or 'v' in result:
            self._add_section_header("Анализ остатков измерений")
            residuals = result.get('residuals', result.get('v', None))
            
            if residuals is not None:
                residuals = np.array(residuals)
                self._add_line(f"Число измерений: {len(residuals)}")
                self._add_line(f"Среднее остатков: {np.mean(residuals):.6f}")
                self._add_line(f"СКО остатков: {np.std(residuals):.6f}")
                self._add_line(f"Минимальный остаток: {np.min(residuals):.6f}")
                self._add_line(f"Максимальный остаток: {np.max(residuals):.6f}")
                self._add_line(f"Сумма квадратов остатков: {np.sum(residuals**2):.6f}")
                
                # Выбросы (остатки > 3σ)
                if hasattr(result, 'sigma0') and result.get('sigma0', 0) > 0:
                    sigma_threshold = 3.0 * result['sigma0']
                    outliers = np.where(np.abs(residuals) > sigma_threshold)[0]
                    self._add_line(f"Выбросы (>3σ): {len(outliers)} измерений")
                    if outliers and len(outliers) <= 10:
                        self._add_line(f"  Индексы: {outliers.tolist()}")
            self._add_line()
        
        # 7. Заключение
        self._add_section_header("Заключение")
        
        convergence_status = result.get('convergence', True)
        reliability_ok = True
        if 'reliability' in result:
            rel = result['reliability']
            if rel.get('mean_redundancy', 0) < 0.3:
                reliability_ok = False
        
        if convergence_status and reliability_ok:
            self._add_line("✓ Уравнивание выполнено успешно")
            self._add_line("✓ Сходимость достигнута")
            self._add_line("✓ Надёжность сети соответствует требованиям")
        else:
            if not convergence_status:
                self._add_line("⚠ Сходимость не достигнута - требуется проверка данных")
            if not reliability_ok:
                self._add_line("⚠ Надёжность сети недостаточна - рекомендуется добавить измерения")
        
        self._add_line()
        self._add_separator("=")
        self._add_line("Отчёт сформирован системой P-of-Geo-Meas")
        self._add_line(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        self._add_separator("=")
        
        return "\n".join(self.report_lines)
    
    def generate_short_report(self, result: Dict[str, Any]) -> str:
        """
        Генерация краткого отчёта для быстрого просмотра
        
        Параметры:
        - result: словарь с результатами уравнивания
        
        Возвращает:
        - Краткий текстовый отчёт
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append("КРАТКИЙ ОТЧЁТ ОБ УРАВНИВАНИИ")
        lines.append("=" * 60)
        
        lines.append(f"Σ₀ = {result.get('sigma0', 0.0):.4f}")
        lines.append(f"N = {result.get('num_observations', 0)} измерений")
        lines.append(f"R = {result.get('redundancy', 0):.1f} степеней свободы")
        lines.append(f"Iter = {result.get('iterations', 1)}")
        
        if 'reliability' in result:
            rel = result['reliability']
            lines.append(f"r̄ = {rel.get('mean_redundancy', 0.0):.3f} (средняя избыточность)")
            lines.append(f"Грубые ошибки: {rel.get('num_gross_error_candidates', 0)}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_report(self, filename: str, content: str):
        """
        Сохранение отчёта в файл
        
        Параметры:
        - filename: имя файла
        - content: содержимое отчёта
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)


def generate_report(project: Any, result: Dict[str, Any], 
                   output_file: Optional[str] = None) -> str:
    """
    Удобная функция для генерации отчёта
    
    Параметры:
    - project: объект проекта
    - result: результаты уравнивания
    - output_file: опционально, имя файла для сохранения
    
    Возвращает:
    - Текстовый отчёт
    """
    generator = ReportGenerator()
    report = generator.generate_adjustment_report(project, result)
    
    if output_file:
        generator.save_report(output_file, report)
    
    return report
