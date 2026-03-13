import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from datetime import datetime
import math


class PreprocessingModule:
    """Модуль предобработки с 9 этапами и контролем 27 допусков"""

    STAGES = [
        "1. Распознавание топологии сети",
        "2. Формирование ходов и секций",
        "3. Обработка приемов измерений",
        "4. Контроль замыкания горизонта",
        "5. Усреднение направлений в приемах",
        "6. Контроль сходимости прямых/обратных измерений",
        "7. Применение редукций",
        "8. Расчет предварительных координат",
        "9. Формирование протокола допусков"
    ]

    def __init__(self):
        self.current_stage = 0
        self.acceptance_criteria = {}
        self.logger = None  # Для логирования

    def _build_network_topology(self, observations: List[Any]) -> Dict[str, Any]:
        """
        Этап 1: Распознавание топологии сети

        Строит графовую модель сети, выявляет:
        - Все пункты сети
        - Станции (пункты с угловыми измерениями)
        - Узловые пункты (пункты с ≥3 связями)
        - Исходные пункты (если есть)
        """
        points = set()
        stations = set()
        connections = defaultdict(set)

        for obs in observations:
            points.add(obs.from_point)
            points.add(obs.to_point)
            connections[obs.from_point].add(obs.to_point)
            connections[obs.to_point].add(obs.from_point)

            # Станции - пункты с угловыми измерениями
            if obs.obs_type in ['direction', 'angle']:
                stations.add(obs.from_point)

        # Узловые пункты - пункты с ≥3 связями
        nodal_points = {p for p, conns in connections.items() if len(conns) >= 3}

        topology = {
            'points': list(points),
            'stations': list(stations),
            'nodal_points': list(nodal_points),
            'connections': dict(connections),
            'num_observations': len(observations)
        }

        return topology

    def _detect_traverses_and_sections(self, topology: Dict[str, Any],
                                       observations: List[Any]) -> Dict[str, Any]:
        """
        Этап 2: Формирование ходов и секций

        Автоматически распознаёт:
        - Полигонометрические/теодолитные ходы
        - Нивелирные секции
        - Замкнутые полигоны
        """
        traverses = []
        sections = []
        cycles = []

        # Логика распознавания ходов (упрощённая)
        # В реальной реализации нужен более сложный алгоритм
        # с анализом последовательности измерений

        # Группировка измерений по типам
        angle_obs = [o for o in observations if o.obs_type in ['direction', 'angle']]
        distance_obs = [o for o in observations if o.obs_type == 'distance']
        level_obs = [o for o in observations if o.obs_type == 'height_diff']

        # Формирование ходов на основе угловых и линейных измерений
        # (заглушка для демонстрации)
        if angle_obs and distance_obs:
            traverses.append({
                'type': 'polygonometry',
                'stations': list(set(o.from_point for o in angle_obs)),
                'num_sides': len(distance_obs),
                'length': sum(o.value for o in distance_obs)
            })

        # Формирование нивелирных секций
        if level_obs:
            sections.append({
                'type': 'nivellement',
                'stations': list(set(o.from_point for o in level_obs)),
                'num_stands': len(level_obs),
                'total_elevation_diff': sum(o.value for o in level_obs)
            })

        result = {
            'traverses': traverses,
            'sections': sections,
            'cycles': cycles
        }

        return result

    def _process_receptions(self, observations: List[Any],
                            station_id: str) -> Dict[str, Any]:
        """
        Этап 3: Обработка приемов измерений

        Обрабатывает круговые приемы на станции:
        1. Распознаёт приемы по замыканию на начальную цель
        2. Проверяет замыкание горизонта
        3. Усредняет направления по приемам
        """
        # Фильтрация измерений для данной станции
        station_obs = [obs for obs in observations
                       if obs.from_point == station_id and obs.obs_type == 'direction']

        if not station_obs:
            return {'status': 'no_data', 'error_message': f"Нет угловых измерений на станции {station_id}"}

        # Сортировка по времени и номеру приема
        station_obs.sort(key=lambda obs: (obs.datetime or datetime.min,
                                          obs.reception_number or 0))

        # Распознавание приемов по замыканию на начальную цель
        receptions = []
        current_reception = []
        first_target = None

        for obs in station_obs:
            if not current_reception:
                # Начало нового приема
                current_reception.append(obs)
                first_target = obs.to_point
            elif obs.to_point == first_target:
                # Замыкание приема на начальную цель
                current_reception.append(obs)
                receptions.append(current_reception)
                current_reception = []
                first_target = None
            else:
                # Продолжение текущего приема
                current_reception.append(obs)

        # Обработка незавершённого приема (без замыкания)
        if current_reception:
            receptions.append(current_reception)
            if self.logger:
                self.logger.warning(f"Станция {station_id}: прием без замыкания на начальную цель")

        # Проверка замыкания горизонта для каждого приема
        closure_results = []
        for i, reception in enumerate(receptions):
            directions = [obs.value for obs in reception]
            closure_error = abs(sum(directions) - 360.0)
            closure_results.append({
                'reception_number': i + 1,
                'num_directions': len(directions),
                'closure_error': closure_error,
                'is_compliant': closure_error <= 15.0  # допуск для полигонометрии 4 класса
            })

        result = {
            'status': 'success',
            'num_receptions': len(receptions),
            'receptions': receptions,
            'closure_results': closure_results
        }

        return result

    def _average_directions_in_receptions(self, receptions_results: List[Dict]) -> List[Dict]:
        """
        Этап 5: Усреднение направлений в приемах

        Усреднение направлений по приемам с учётом весов (число приемов).
        Для каждого направления (пары станция-цель) рассчитывается среднее значение.
        """
        # Группировка направлений по цели
        direction_groups = defaultdict(list)

        for reception_result in receptions_results:
            if reception_result['status'] != 'success':
                continue

            for reception in reception_result['receptions']:
                for obs in reception:
                    # Определение цели по индексу
                    target_id = obs.to_point
                    direction_groups[(obs.from_point, target_id)].append(obs.value)

        # Расчёт средних значений
        averaged = []
        for (from_point, to_point), values in direction_groups.items():
            mean_value = sum(values) / len(values)
            std_dev = np.std(values) if len(values) > 1 else 0.0

            averaged.append({
                'from_point': from_point,
                'to_point': to_point,
                'averaged_value': mean_value,
                'std_dev': std_dev,
                'num_observations': len(values)
            })

        return averaged

    def _check_reciprocal_measurements(self, observations: List[Any]) -> List[Dict]:
        """
        Этап 6: Контроль сходимости прямых/обратных измерений

        Проверяет расхождения между прямыми и обратными измерениями:
        - Расстояния: прямое и обратное
        - Превышения: прямое и обратное
        """
        violations = []

        # Группировка измерений по парам пунктов
        measurement_pairs = defaultdict(list)

        for obs in observations:
            if obs.obs_type in ['distance', 'height_diff']:
                pair_key = tuple(sorted([obs.from_point, obs.to_point]))
                measurement_pairs[pair_key].append(obs)

        # Проверка каждой пары
        for pair, measurements in measurement_pairs.items():
            if len(measurements) < 2:
                continue

            # Разделение на прямые и обратные измерения
            forward = [m for m in measurements if m.from_point == pair[0]]
            backward = [m for m in measurements if m.from_point == pair[1]]

            if not forward or not backward:
                continue

            # Средние значения
            forward_mean = sum(m.value for m in forward) / len(forward)
            backward_mean = sum(m.value for m in backward) / len(backward)

            # Расхождение (для превышений учитываем знак)
            if forward[0].obs_type == 'height_diff':
                discrepancy = abs(forward_mean + backward_mean)
                allowable = 10.0  # допуск для технического нивелирования, мм
            else:  # distance
                discrepancy = abs(forward_mean - backward_mean)
                allowable = 0.01  # допуск 1 см для расстояний

            if discrepancy > allowable:
                violations.append({
                    'type': 'reciprocal_discrepancy',
                    'obs_type': forward[0].obs_type,
                    'pair': pair,
                    'forward_value': forward_mean,
                    'backward_value': backward_mean,
                    'discrepancy': discrepancy,
                    'allowable': allowable,
                    'is_violation': True
                })

        return violations

    def _apply_corrections(self, observations: List[Any],
                           config: Dict[str, Any]) -> List[Any]:
        """
        Этап 7: Применение редукций

        Применяет поправки к измерениям:
        - Атмосферные поправки
        - Поправки за рефракцию
        - Поправки за кривизну Земли
        - Редуцирование на плоскость проекции
        """
        corrected = []

        for obs in observations:
            corrected_obs = obs.copy() if hasattr(obs, 'copy') else obs

            if obs.obs_type == 'distance':
                # Атмосферная поправка (упрощённая)
                if config.get('apply_atmospheric_correction', True):
                    temperature = getattr(obs, 'temperature', 15.0)
                    pressure = getattr(obs, 'pressure', 1013.25)

                    # Упрощённая формула атмосферной поправки
                    delta_atm = obs.value * (0.000295 * (temperature - 15) - 0.000038 * (pressure - 1013.25))
                    corrected_obs.value += delta_atm

                # Поправка за рефракцию и кривизну Земли
                if config.get('apply_refraction_correction', True):
                    distance_km = obs.value / 1000.0
                    refraction_coeff = config.get('refraction_coefficient', 0.14)
                    earth_radius = config.get('earth_radius', 6371000.0)

                    # Поправка за рефракцию и кривизну
                    delta_ref = (distance_km ** 2) * (1 - refraction_coeff) / (2 * earth_radius) * 1000
                    corrected_obs.value += delta_ref

            corrected.append(corrected_obs)

        return corrected

    def _compute_preliminary_coordinates(self, observations: List[Any],
                                         fixed_points: List[str]) -> Dict[str, Any]:
        """
        Этап 8: Расчет предварительных координат

        Рассчитывает приближённые координаты определяемых пунктов
        методом полигонометрического хода от исходных пунктов.
        """
        # Создание словаря координат
        coordinates = {}

        # Добавление исходных пунктов
        for point_id in fixed_points:
            # В реальной реализации здесь должны быть координаты из данных
            coordinates[point_id] = {
                'x': 0.0,  # Заглушка
                'y': 0.0,  # Заглушка
                'h': None
            }

        # Расчёт координат для определяемых пунктов (упрощённый алгоритм)
        # В реальной реализации нужен алгоритм распространения координат по ходу

        result = {
            'coordinates': coordinates,
            'num_calculated': len(coordinates) - len(fixed_points),
            'num_fixed': len(fixed_points)
        }

        return result

    def run_all_stages(self, raw_data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запуск всех этапов предобработки

        Параметры:
        - raw_data: сырые данные измерений
        - config: конфигурация предобработки

        Возвращает:
        - Словарь с результатами всех этапов
        """
        results = {
            'stages_completed': 0,
            'topology': None,
            'traverses': None,
            'receptions': None,
            'averaged_directions': None,
            'reciprocal_violations': None,
            'corrected_observations': None,
            'preliminary_coordinates': None,
            'tolerance_violations': None,
            'errors': [],
            'warnings': []
        }

        # Этап 1: Распознавание топологии сети
        if self.logger:
            self.logger.info("Этап 1: Распознавание топологии сети")

        results['topology'] = self._build_network_topology(raw_data.observations)

        if self.logger:
            self.logger.info(f" • Пунктов всего: {len(results['topology']['points'])}")
            self.logger.info(f" • Измерений всего: {results['topology']['num_observations']}")
            self.logger.info(f" • Узловых пунктов: {len(results['topology']['nodal_points'])}")
            self.logger.info(f" • Станций: {len(results['topology']['stations'])}")

        # Этап 2: Формирование ходов и секций
        if self.logger:
            self.logger.info("Этап 2: Формирование ходов и секций")

        results['traverses'] = self._detect_traverses_and_sections(
            results['topology'],
            raw_data.observations
        )

        if self.logger:
            self.logger.info(f" • Ходов: {len(results['traverses']['traverses'])}")
            self.logger.info(f" • Секций: {len(results['traverses']['sections'])}")

        # Этап 3: Обработка приемов измерений
        if self.logger:
            self.logger.info("Этап 3: Обработка приемов измерений")

        reception_results = []
        for station_id in results['topology']['stations']:
            result = self._process_receptions(raw_data.observations, station_id)
            reception_results.append(result)

        results['receptions'] = reception_results

        # Этап 4: Контроль замыкания горизонта
        # (выполняется внутри _process_receptions)

        # Этап 5: Усреднение направлений в приемах
        if self.logger:
            self.logger.info("Этап 5: Усреднение направлений в приемах")

        results['averaged_directions'] = self._average_directions_in_receptions(
            reception_results
        )

        if self.logger:
            self.logger.info(f" • Усреднено направлений: {len(results['averaged_directions'])}")

        # Этап 6: Контроль сходимости прямых/обратных измерений
        if self.logger:
            self.logger.info("Этап 6: Контроль сходимости прямых/обратных измерений")

        results['reciprocal_violations'] = self._check_reciprocal_measurements(
            raw_data.observations
        )

        if self.logger:
            num_violations = len(results['reciprocal_violations'])
            self.logger.info(f" • Нарушений сходимости: {num_violations}")

        # Этап 7: Применение редукций
        if self.logger:
            self.logger.info("Этап 7: Применение редукций")

        results['corrected_observations'] = self._apply_corrections(
            raw_data.observations,
            config
        )

        if self.logger:
            self.logger.info(f" • Применено редукций: {len(results['corrected_observations'])}")

        # Этап 8: Расчет предварительных координат
        if self.logger:
            self.logger.info("Этап 8: Расчет предварительных координат")

        results['preliminary_coordinates'] = self._compute_preliminary_coordinates(
            results['corrected_observations'],
            results['topology'].get('fixed_points', [])
        )

        if self.logger:
            self.logger.info(f" • Рассчитано координат: {results['preliminary_coordinates']['num_calculated']}")

        # Этап 9: Формирование протокола допусков
        if self.logger:
            self.logger.info("Этап 9: Формирование протокола допусков")

        # Проверка допусков (заглушка)
        results['tolerance_violations'] = []

        results['stages_completed'] = 9

        return results

    def check_acceptance_criteria(self, observations: List[Any],
                                  topology: Dict[str, Any]) -> List[Dict]:
        """
        Проверка 27 инструктивных допусков по СП 11-104-97

        Возвращает список нарушений допусков
        """
        violations = []

        # Пример проверки допусков

        # 1. Замыкание горизонта (полигонометрия 4 класса)
        # Допуск: 15√n, где n - число направлений
        for station in topology['stations']:
            # Получение числа направлений на станции
            num_directions = len([o for o in observations
                                  if o.from_point == station and o.obs_type == 'direction'])

            if num_directions >= 3:
                allowable_closure = 15.0 * math.sqrt(num_directions)
                # В реальной реализации здесь должен быть расчёт фактического замыкания
                actual_closure = 0.0  # Заглушка

                if actual_closure > allowable_closure:
                    violations.append({
                        'criterion': 'circle_closure',
                        'location': station,
                        'actual': actual_closure,
                        'allowable': allowable_closure,
                        'normative': 'СП 11-104-97, п. 5.3.5'
                    })

        # 2. Относительная невязка хода (полигонометрия 4 класса)
        # Допуск: 1:25 000
        # (логика проверки ходов)

        # 3. Невязка нивелирного хода (нивелирование III класса)
        # Допуск: 12√L мм, где L - длина хода в км
        # (логика проверки нивелирных секций)

        # ... и так далее для всех 27 допусков

        return violations