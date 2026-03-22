# Инструкция по сборке P-of-Geo-Meas

## Требования

- Python 3.8 или выше
- Windows 10/11 или Linux
- Установленный pip

## Шаги по сборке

### 1. Установка зависимостей

```bash
cd GeoAdjustPro
pip install -r requirements.txt
```

### 2. Установка дополнительных инструментов

```bash
pip install pyinstaller
```

### 3. Сборка приложения

#### Вариант 1: Использование скрипта сборки
```bash
python scripts/build_release.py
```

#### Вариант 2: Ручная сборка с PyInstaller
```bash
# Создание spec-файла
pyi-makespec --name P-of-Geo-Meas --windowed \
  --hidden-import PyQt5.QtPrintSupport \
  --hidden-import PyQt5.QtSvg \
  --hidden-import scipy.sparse.csgraph._validation \
  --hidden-import sksparse \
  --hidden-import sksparse.cholmod \
  --hidden-import yaml \
  --hidden-import chardet \
  --hidden-import docx \
  --hidden-import matplotlib.backends.backend_qt5agg \
  --hidden-import pandas._libs \
  --hidden-import numpy.random._common \
  --hidden-import openpyxl \
  --hidden-import ezdxf \
  src/geoadjust/__main__.py

# Сборка
pyinstaller P-of-Geo-Meas.spec --clean --noconfirm
```

### 4. Результаты сборки

После успешной сборки в директории `dist` будет создано приложение:
- `dist/P-of-Geo-Meas/` - каталог с исполняемым файлом и всеми необходимыми ресурсами
- `dist/P-of-Geo-Meas.exe` - исполняемый файл (Windows)

## Структура проекта

### Основные директории:
- `src/geoadjust/` - основной код приложения
- `gui/` - графический интерфейс
- `resources/` - ресурсы (базы данных CRS, геоидальные данные)
- `examples/` - примеры использования
- `scripts/` - вспомогательные скрипты

### Зависимости:
Проект использует следующие основные библиотеки:
- numpy, scipy - математические вычисления
- PyQt5 - графический интерфейс
- pyproj, networkx - геодезические расчеты
- matplotlib, seaborn - визуализация
- pandas, openpyxl, python-docx - работа с данными
- chardet, requests - работа с файлами и сетью

## Тестирование

После сборки можно проверить работоспособность:
1. Запустить `dist/P-of-Geo-Meas/P-of-Geo-Meas.exe`
2. Убедиться, что приложение запускается без ошибок
3. Проверить работу основных функций

## Примечания

- Для полноценной работы необходимы все ресурсы из `resources/` и `src/geoadjust/resources/`
- Некоторые зависимости (например, `scikit-sparse`) могут не собираться на Windows без специальных инструментов
- При необходимости можно создать установщик с помощью Inno Setup