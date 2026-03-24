# Улучшения P-of-Geo-Meas на основе DynAdjust

## Обзор изменений

Данный документ описывает улучшения, внедрённые в систему P-of-Geo-Meas на основе анализа профессиональной системы уравнивания **DynAdjust** (Geoscience Australia).

---

## ✅ Реализованные улучшения

### 1. Модель данных (models.py)

**Файл:** `src/geoadjust/core/network/models.py`

#### Добавлено для класса `NetworkPoint`:
- `latitude`, `longitude` — географические координаты для работы с моделями геоида

#### Добавлено для класса `Observation`:
- Поддержка **полной ковариационной матрицы 3×3** для ГНСС векторов:
  - `delta_x`, `delta_y`, `delta_z` — компоненты вектора
  - `sigma_x`, `sigma_y`, `sigma_z` — СКО компонент
  - `covariance_matrix` — полная ковариационная матрица
- Расширенные типы измерений: `azimuth`, `vertical_angle`, `zenith_angle`
- Атрибуты для угловых измерений: `angle_unit`, `reception_number`, `datetime`
- Атрибуты для превышений: `instrument_height`, `target_height`, `num_stands`
- Атрибуты для линейных измерений: `temperature`, `pressure`

---

### 2. Расширенный анализ надёжности (baarda_method.py)

**Файл:** `src/geoadjust/core/reliability/baarda_method.py`

#### Новый метод `calculate_reliability_metrics()`:
Реализует расширенную методику DynAdjust:

1. **Ковариационная матрица остатков** (полная формула)
   - Qvv = Qll - A · Qxx · A^T

2. **Внутренняя надёжность** (redundancy numbers)
   - r_i = 1 - q_vv_ii / q_ll_ii

3. **Внешняя надёжность** (влияние незамеченных грубых ошибок)
   - δx_i = σ₀ · √((1 - r_i) / r_i)

4. **Статистический критерий обнаружения грубых ошибок**
   - Критическое значение для α=0.05

5. **Анализ влияния измерений на координаты** (влияние Леви)
   - influence[i, j] = влияние i-го измерения на j-й параметр

6. **Определение кандидатов на грубые ошибки**
   - Измерения с избыточностью < 0.1

7. **Определение ненадёжных измерений**
   - Измерения с внешней надёжностью > 5 см

#### Обновлённый метод `analyze()`:
Возвращает расширенный словарь с метриками:
```python
{
    'redundancy_numbers': [...],           # Числа избыточности
    'external_reliability_dynadjust': [...], # Внешняя надёжность
    'critical_value': 3.0,                  # Критическое значение
    'influence_matrix': [...],              # Матрица влияния
    'gross_error_candidates': [...],        # Кандидаты на грубые ошибки
    'unreliable_measurements': [...],       # Ненадёжные измерения
    'mean_redundancy': 0.5,                 # Средняя избыточность
    'min_redundancy': 0.1,                  # Минимальная избыточность
    'max_external_reliability': 0.05        # Макс. внешняя надёжность
}
```

---

### 3. Улучшенное свободное уравнивание (free_network.py)

**Файл:** `src/geoadjust/core/adjustment/free_network.py`

#### Новый метод `detect_network_type()`:
Автоматическое определение типа сети по наблюдениям:
- **1D сеть** — только нивелирование (height_diff)
- **2D сеть** — плановые измерения (direction, distance, azimuth)
- **3D сеть** — комбинация плановых и высотных измерений

#### Улучшенный метод `apply_minimum_constraints()`:
Реализует теорию Бомфорда с минимальными ограничениями:

**Для 1D сети (нивелирной):**
- Фиксация центра тяжести по высоте: ΣΔh = 0

**Для 2D сети (плановой):**
- Фиксация центра тяжести по X: ΣΔx = 0
- Фиксация центра тяжести по Y: ΣΔy = 0
- Фиксация ориентации (вращение вокруг Z): Σ(-y_i·Δx_i + x_i·Δy_i) = 0

**Для 3D сети:**
- Фиксация центра тяжести по X, Y, Z
- Фиксация вращения вокруг осей X, Y, Z
- Фиксация масштаба (для ГНСС сетей)

#### Параметры метода:
- `points` — список пунктов для улучшенной фиксации
- `observations` — список наблюдений для автоопределения типа сети

---

### 4. Обработка круговых приемов (direction_processor.py)

**Новый файл:** `src/geoadjust/core/preprocessing/direction_processor.py`

#### Класс `DirectionSetProcessor`:
Профессиональная обработка направлений по методике DynAdjust с адаптацией под СП 11-104-97 РФ.

##### Допуски по классам точности:
```python
CLOSURE_TOLERANCES = {
    '1_class': 2.0",      # 1 класс
    '2_class': 3.0",      # 2 класс
    '3_class': 4.0",      # 3 класс
    '4_class': 5.0",      # 4 класс
    '1st_rank': 8.0",     # 1 разряд
    '2nd_rank': 12.0"     # 2 разряд
}
```

##### Основные методы:
- `process_direction_set()` — обработка одного приема
  - Расчёт невязки замыкания горизонта
  - Проверка допуска
  - Усреднение направлений с весами
  - Оценка качества ('excellent', 'good', 'acceptable', 'poor')

- `process_multiple_receptions()` — обработка нескольких приемов
  - Контроль сходимости между приемами
  - Объединение результатов
  - Итоговая оценка

##### Пример использования:
```python
from geoadjust.core.preprocessing.direction_processor import process_direction_set

directions = [
    {'to_point': 'A', 'value': 0.0},
    {'to_point': 'B', 'value': 45.5},
    {'to_point': 'C', 'value': 120.3},
    {'to_point': 'A', 'value': 360.002}  # Замыкание
]

result = process_direction_set(directions, class_name='4_class')
print(f"Невязка: {result['closure_seconds']}\"")
print(f"Допуск: {result['tolerance_seconds']}\"")
print(f"Соответствует: {result['is_closure_compliant']}")
```

---

### 5. Генерация отчётов (dynadjust_report.py)

**Новый файл:** `src/geoadjust/io/export/dynadjust_report.py`

#### Класс `ReportGenerator`:
Генерация структурированных отчётов по аналогии с DynAdjust с адаптацией под ГОСТ 7.32-2017.

##### Структура отчёта:
1. **Заголовок** — название проекта, дата, метод
2. **Статистика сети** — число пунктов, измерений, степень свободы
3. **Результаты уравнивания** — σ₀, итерации, сходимость
4. **Анализ надёжности** (по методике DynAdjust):
   - Средняя/минимальная избыточность
   - Максимальная внешняя надёжность
   - Кандидаты на грубые ошибки
   - Критическое значение
5. **Ведомость уравненных координат** — с СКО
6. **Анализ остатков измерений** — статистика, выбросы
7. **Заключение** — итоговая оценка

##### Пример использования:
```python
from geoadjust.io.export.dynadjust_report import generate_report

report = generate_report(project, result, output_file='report.txt')
print(report)
```

##### Краткий отчёт:
```python
from geoadjust.io.export.dynadjust_report import ReportGenerator

generator = ReportGenerator()
short_report = generator.generate_short_report(result)
```

---

## 📊 Сравнительная таблица

| Функция | До улучшений | После улучшений |
|---------|-------------|-----------------|
| **Ковариационная матрица ГНСС** | Упрощённая (отдельные СКО) | Полная 3×3 матрица |
| **Анализ надёжности** | Базовый (внутренняя) | Расширенный (внутренняя + внешняя + влияние) |
| **Свободное уравнивание** | Базовое (2D/3D) | Автоопределение типа + мин. ограничения |
| **Обработка приемов** | Базовая | По классам точности СП 11-104-97 |
| **Отчёты** | Базовый экспорт | Структурированные (DynAdjust-style) |

---

## 🔧 Как использовать новые возможности

### 1. Работа с полной ковариационной матрицей ГНСС:
```python
from geoadjust.core.network.models import Observation
import numpy as np

# Создание ГНСС вектора с полной ковариационной матрицей
cov_matrix = np.array([
    [0.0001, 0.00001, 0.0],
    [0.00001, 0.0001, 0.0],
    [0.0, 0.0, 0.0002]
])

gnss_obs = Observation(
    obs_id='GNSS1',
    obs_type='gnss_vector',
    from_point='A',
    to_point='B',
    value=100.0,
    instrument_name='GPS',
    sigma_apriori=0.01,
    delta_x=50.0,
    delta_y=70.0,
    delta_z=40.0,
    covariance_matrix=cov_matrix
)
```

### 2. Расширенный анализ надёжности:
```python
from geoadjust.core.reliability.baarda_method import BaardaReliability

baarda = BaardaReliability(A, P, sigma0, residuals)
results = baarda.analyze()

print(f"Средняя избыточность: {results['mean_redundancy']:.4f}")
print(f"Кандидаты на грубые ошибки: {results['num_gross_error_candidates']}")
print(f"Макс. внешняя надёжность: {results['max_external_reliability']*1000:.2f} мм")
```

### 3. Свободное уравнивание с автоопределением:
```python
from geoadjust.core.adjustment.free_network import FreeNetworkAdjustment

adjuster = FreeNetworkAdjustment()
network_type = adjuster.detect_network_type(observations)
print(f"Тип сети: {network_type}")

dx, lambdas, C, w = adjuster.apply_minimum_constraints(
    A, L, initial_coords,
    points=points,
    observations=observations
)
```

### 4. Обработка круговых приемов:
```python
from geoadjust.core.preprocessing.direction_processor import DirectionSetProcessor

processor = DirectionSetProcessor(class_name='2_class')
result = processor.process_direction_set(directions)

if result['is_closure_compliant']:
    print(f"✓ Прием соответствует 2 классу")
    print(f"Невязка: {result['closure_seconds']}\"")
    print(f"Качество: {result['quality_score']}")
```

### 5. Генерация отчёта:
```python
from geoadjust.io.export.dynadjust_report import generate_report

report = generate_report(project, result, output_file='adjustment_report.txt')
print(report)
```

---

## 📝 Примечания

1. **Обратная совместимость**: Все изменения обратно совместимы со старым кодом
2. **Производительность**: Для больших сетей (>10000 измерений) используются оптимизированные алгоритмы
3. **Документация**: Каждый новый метод содержит подробные docstring на русском языке
4. **Тестирование**: Рекомендуется протестировать новые функции на ваших данных

---

## 🚀 Следующие шаги

Для полноценного использования новых возможностей рекомендуется:

1. **Интегрировать полную ковариационную матрицу** в `WeightBuilder` и `EquationsBuilder`
2. **Добавить поддержку моделей геоида** в преобразования координат
3. **Расширить GUI** для отображения новых метрик надёжности
4. **Добавить экспорт** в форматы DynAdjust (.dna, .dnx)

---

**Дата обновления:** Март 2024  
**Версия:** 1.0  
**На основе:** DynAdjust (Geoscience Australia) + СП 11-104-97 РФ
