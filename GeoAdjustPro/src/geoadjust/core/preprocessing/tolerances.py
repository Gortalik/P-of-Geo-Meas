"""Контроль 27 инструктивных допусков по СП 11-104-97"""

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToleranceViolation:
    """Нарушение допуска"""
    criterion: str
    location: str
    actual: float
    allowable: float
    normative: str
    severity: str = 'warning'


class ToleranceChecker:
    """Контроль 27 инструктивных допусков по СП 11-104-97 и Инструкции по нивелированию ГГС"""

    # Допуски для полигонометрии
    POLYGONOMETRY_TOLERANCES = {
        '1_class': {
            'circle_closure': lambda n: 3.0 * math.sqrt(n),  # 3√n
            'relative_misalignment': 1 / 100000,  # 1:100 000
            'max_side_length': 10000,  # 10 км
            'max_num_sides': 25
        },
        '2_class': {
            'circle_closure': lambda n: 5.0 * math.sqrt(n),  # 5√n
            'relative_misalignment': 1 / 50000,  # 1:50 000
            'max_side_length': 5000,  # 5 км
            'max_num_sides': 20
        },
        '3_class': {
            'circle_closure': lambda n: 10.0 * math.sqrt(n),  # 10√n
            'relative_misalignment': 1 / 30000,  # 1:30 000
            'max_side_length': 3000,  # 3 км
            'max_num_sides': 15
        },
        '4_class': {
            'circle_closure': lambda n: 15.0 * math.sqrt(n),  # 15√n
            'relative_misalignment': 1 / 25000,  # 1:25 000
            'max_side_length': 2000,  # 2 км
            'max_num_sides': 12
        }
    }

    # Допуски для нивелирования
    LEVELLING_TOLERANCES = {
        'I_class': {
            'per_stand': 0.8,  # мм/станцию
            'section_closure': lambda L: 3.0 * math.sqrt(L),  # 3√L мм
            'max_sight_distance': 50  # м
        },
        'II_class': {
            'per_stand': 1.5,  # мм/станцию
            'section_closure': lambda L: 5.0 * math.sqrt(L),  # 5√L мм
            'max_sight_distance': 75  # м
        },
        'III_class': {
            'per_stand': 3.0,  # мм/станцию
            'section_closure': lambda L: 12.0 * math.sqrt(L),  # 12√L мм
            'max_sight_distance': 100  # м
        },
        'IV_class': {
            'per_stand': 5.0,  # мм/станцию
            'section_closure': lambda L: 20.0 * math.sqrt(L),  # 20√L мм
            'max_sight_distance': 150  # м
        },
        'technical': {
            'per_stand': 10.0,  # мм/станцию
            'section_closure': lambda L: 50.0 * math.sqrt(L),  # 50√L мм
            'max_sight_distance': 150  # м
        }
    }

    def check_circle_closure(self, directions: List[float],
                             class_name: str = '4_class') -> Dict[str, Any]:
        """
        Контроль замыкания горизонта

        Параметры:
        - directions: список направлений в секундах
        - class_name: класс полигонометрии

        Возвращает:
        - Словарь с результатами проверки
        """
        closure_error = abs(sum(directions) - 360.0 * 3600)  # в секундах
        n = len(directions)
        tolerances = self.POLYGONOMETRY_TOLERANCES[class_name]
        allowable_error = tolerances['circle_closure'](n)
        is_compliant = closure_error <= allowable_error

        return {
            'error': closure_error,
            'allowable_error': allowable_error,
            'is_compliant': is_compliant,
            'normative': f'СП 11-104-97, {class_name}'
        }

    def check_traverse_misalignment(self, traverse_length: float,
                                    traverse_misclosure: float,
                                    class_name: str = '4_class') -> Dict[str, Any]:
        """
        Контроль относительной невязки хода

        Параметры:
        - traverse_length: длина хода в метрах
        - traverse_misclosure: невязка хода в метрах
        - class_name: класс полигонометрии

        Возвращает:
        - Словарь с результатами проверки
        """
        tolerances = self.POLYGONOMETRY_TOLERANCES[class_name]

        # Относительная невязка
        actual_misalignment = traverse_misclosure / traverse_length if traverse_length > 0 else float('inf')
        allowable_misalignment = tolerances['relative_misalignment']

        is_compliant = actual_misalignment <= allowable_misalignment

        return {
            'actual': actual_misalignment,
            'allowable': allowable_misalignment,
            'is_compliant': is_compliant,
            'normative': f'СП 11-104-97, {class_name}',
            'traverse_length': traverse_length,
            'misclosure': traverse_misclosure
        }

    def check_leveling_section_closure(self, section_length_km: float,
                                       section_closure_mm: float,
                                       class_name: str = 'III_class') -> Dict[str, Any]:
        """
        Контроль невязки нивелирной секции

        Параметры:
        - section_length_km: длина секции в км
        - section_closure_mm: невязка секции в мм
        - class_name: класс нивелирования

        Возвращает:
        - Словарь с результатами проверки
        """
        tolerances = self.LEVELLING_TOLERANCES[class_name]

        # Допуск невязки
        allowable_closure = tolerances['section_closure'](section_length_km)

        is_compliant = abs(section_closure_mm) <= allowable_closure

        return {
            'actual': abs(section_closure_mm),
            'allowable': allowable_closure,
            'is_compliant': is_compliant,
            'normative': f'Инструкция по нивелированию ГГС, {class_name}'
        }

    def check_sight_distance(self, distance: float,
                             class_name: str = 'III_class') -> Dict[str, Any]:
        """
        Контроль длины визирного луча

        Параметры:
        - distance: длина визирного луча в метрах
        - class_name: класс нивелирования

        Возвращает:
        - Словарь с результатами проверки
        """
        max_distance = self.LEVELLING_TOLERANCES[class_name]['max_sight_distance']
        is_compliant = distance <= max_distance

        return {
            'actual': distance,
            'allowable': max_distance,
            'is_compliant': is_compliant,
            'normative': f'Инструкция по нивелированию ГГС, {class_name}'
        }

    def check_side_length(self, side_length: float,
                          class_name: str = '4_class') -> Dict[str, Any]:
        """
        Контроль длины стороны хода

        Параметры:
        - side_length: длина стороны в метрах
        - class_name: класс полигонометрии

        Возвращает:
        - Словарь с результатами проверки
        """
        max_length = self.POLYGONOMETRY_TOLERANCES[class_name]['max_side_length']
        is_compliant = side_length <= max_length

        return {
            'actual': side_length,
            'allowable': max_length,
            'is_compliant': is_compliant,
            'normative': f'СП 11-104-97, {class_name}'
        }

    def check_num_sides(self, num_sides: int,
                        class_name: str = '4_class') -> Dict[str, Any]:
        """
        Контроль числа сторон хода

        Параметры:
        - num_sides: число сторон хода
        - class_name: класс полигонометрии

        Возвращает:
        - Словарь с результатами проверки
        """
        max_sides = self.POLYGONOMETRY_TOLERANCES[class_name]['max_num_sides']
        is_compliant = num_sides <= max_sides

        return {
            'actual': num_sides,
            'allowable': max_sides,
            'is_compliant': is_compliant,
            'normative': f'СП 11-104-97, {class_name}'
        }

    def check_all_tolerances(self, network_data: Dict[str, Any]) -> List[ToleranceViolation]:
        """
        Проверка всех 27 допусков

        Параметры:
        - network_data: данные сети с измерениями и конфигурацией

        Возвращает:
        - Список нарушений допусков
        """
        violations = []

        # 1-4. Замыкание горизонта для разных классов полигонометрии
        for class_name in ['1_class', '2_class', '3_class', '4_class']:
            stations = network_data.get('stations', [])
            for station in stations:
                directions = station.get('directions', [])
                if len(directions) >= 3:
                    result = self.check_circle_closure(directions, class_name)
                    if not result['is_compliant']:
                        violations.append(ToleranceViolation(
                            criterion='circle_closure',
                            location=station.get('id', 'unknown'),
                            actual=result['error'],
                            allowable=result['allowable_error'],
                            normative=result['normative'],
                            severity='critical' if result['error'] > 2 * result['allowable_error'] else 'warning'
                        ))

        # 5-8. Относительные невязки ходов
        for class_name in ['1_class', '2_class', '3_class', '4_class']:
            traverses = network_data.get('traverses', [])
            for traverse in traverses:
                length = traverse.get('length', 0)
                misclosure = traverse.get('misclosure', 0)
                if length > 0:
                    result = self.check_traverse_misalignment(length, misclosure, class_name)
                    if not result['is_compliant']:
                        violations.append(ToleranceViolation(
                            criterion='relative_misalignment',
                            location=traverse.get('id', 'unknown'),
                            actual=result['actual'],
                            allowable=result['allowable'],
                            normative=result['normative'],
                            severity='critical' if result['actual'] > 2 * result['allowable'] else 'warning'
                        ))

        # 9-13. Невязки нивелирных ходов
        for class_name in ['I_class', 'II_class', 'III_class', 'IV_class', 'technical']:
            sections = network_data.get('nivellement_sections', [])
            for section in sections:
                length_km = section.get('length_km', 0)
                closure_mm = section.get('closure_mm', 0)
                if length_km > 0:
                    result = self.check_leveling_section_closure(length_km, closure_mm, class_name)
                    if not result['is_compliant']:
                        violations.append(ToleranceViolation(
                            criterion='section_closure',
                            location=section.get('id', 'unknown'),
                            actual=result['actual'],
                            allowable=result['allowable'],
                            normative=result['normative'],
                            severity='critical' if result['actual'] > 2 * result['allowable'] else 'warning'
                        ))

        # 14-18. Длина визирного луча
        for class_name in ['I_class', 'II_class', 'III_class', 'IV_class', 'technical']:
            sight_distances = network_data.get('sight_distances', [])
            for dist in sight_distances:
                result = self.check_sight_distance(dist, class_name)
                if not result['is_compliant']:
                    violations.append(ToleranceViolation(
                        criterion='sight_distance',
                        location=dist.get('station', 'unknown'),
                        actual=result['actual'],
                        allowable=result['allowable'],
                        normative=result['normative']
                    ))

        # 19-22. Длина сторон ходов
        for class_name in ['1_class', '2_class', '3_class', '4_class']:
            side_lengths = network_data.get('side_lengths', [])
            for length in side_lengths:
                result = self.check_side_length(length, class_name)
                if not result['is_compliant']:
                    violations.append(ToleranceViolation(
                        criterion='side_length',
                        location=length.get('segment', 'unknown'),
                        actual=result['actual'],
                        allowable=result['allowable'],
                        normative=result['normative']
                    ))

        # 23-26. Число сторон ходов
        for class_name in ['1_class', '2_class', '3_class', '4_class']:
            traverses = network_data.get('traverses', [])
            for traverse in traverses:
                num_sides = traverse.get('num_sides', 0)
                result = self.check_num_sides(num_sides, class_name)
                if not result['is_compliant']:
                    violations.append(ToleranceViolation(
                        criterion='num_sides',
                        location=traverse.get('id', 'unknown'),
                        actual=result['actual'],
                        allowable=result['allowable'],
                        normative=result['normative']
                    ))

        # 27. Расхождение направлений КЛ/КП
        kl_kp_discrepancies = network_data.get('kl_kp_discrepancies', [])
        for discrepancy in kl_kp_discrepancies:
            if abs(discrepancy) > 15.0:  # допуск 15" для теодолитных ходов
                violations.append(ToleranceViolation(
                    criterion='kl_kp_discrepancy',
                    location=discrepancy.get('station', 'unknown'),
                    actual=abs(discrepancy),
                    allowable=15.0,
                    normative='СП 11-104-97, п. 5.3.3'
                ))

        return violations
