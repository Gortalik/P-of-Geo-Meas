# Инструкция по сборке GeoAdjust Pro в .exe

## 📋 Требования перед сборкой

### 1. Проверка зависимостей

Перед сборкой обязательно проверьте наличие всех зависимостей:

```bash
cd GeoAdjustPro
python check_deps.py
```

Если все зависимости установлены, вы увидите:
```
✅ ВСЕ КРИТИЧЕСКИЕ ЗАВИСИМОСТИ УСТАНОВЛЕНЫ
```

### 2. Установка отсутствующих зависимостей

#### Если отсутствует scikit-sparse (критично!)

**Способ 1: Через Conda (рекомендуется)**
```bash
conda install -c conda-forge scikit-sparse
```

**Способ 2: Через .whl файл**
1. Скачайте файл с https://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-sparse
2. Выберите версию для вашей версии Python и архитектуры (обычно cp311-win_amd64)
3. Установите:
```bash
pip install путь\к\файлу\scikit_sparse‑0.4.8‑cp311‑cp311‑win_amd64.whl
```

#### Если отсутствуют другие пакеты

```bash
pip install ezdxf PyYAML
```

Или с использованием китайского зеркала (при проблемах с сетью):
```bash
pip install ezdxf PyYAML --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 🔨 Сборка приложения

### Быстрая сборка

```bash
cd GeoAdjustPro
pyinstaller P-of-Geo-Meas.spec --clean --noconfirm
```

### Подробная сборка с логами

```bash
cd GeoAdjustPro
pyinstaller P-of-Geo-Meas.spec --clean --noconfirm --log-level DEBUG > build_log.txt 2>&1
```

## 📁 Результат сборки

После успешной сборки исполняемый файл будет находиться по адресу:
```
dist/P-of-Geo-Meas/P-of-Geo-Meas.exe
```

## 🚀 Запуск приложения

### Запуск из консоли (для отладки)

```bash
dist/P-of-Geo-Meas/P-of-Geo-Meas.exe
```

При запуске вы увидите консольное окно со следующей информацией:
- Версия Python
- Платформа
- Статус проверки зависимостей
- Этапы запуска приложения
- Сообщения об ошибках (если есть)

### Запуск без консоли (продакшн)

Для отключения консоли измените в файле `P-of-Geo-Meas.spec`:
```python
console=False  # вместо console=True
```

Затем пересоберите приложение.

## 🐛 Отладка проблем

### Приложение не запускается

1. Запустите .exe файл из командной строки:
```bash
cd dist/P-of-Geo-Meas
P-of-Geo-Meas.exe
```

2. Проверьте логи в файле `geoadjust.log`

3. Проверьте вывод консоли на наличие ошибок

### Ошибки импорта

Если видите ошибки вида "Hidden import not found":
1. Добавьте недостающий импорт в `P-of-Geo-Meas.spec` в список `hiddenimports`
2. Пересоберите приложение

### Проблемы с ресурсами

Если приложение запускается, но не находит ресурсы:
1. Проверьте структуру папок в `dist/P-of-Geo-Meas/`
2. Убедитесь, что папки `resources`, `crs_database`, `gui/resources` существуют
3. Проверьте пути в функции `get_resource_path()` в `src/geoadjust/utils.py`

## 📝 Структура собранного приложения

```
dist/P-of-Geo-Meas/
├── P-of-Geo-Meas.exe      # Исполняемый файл
├── python311.dll          # Библиотека Python
├── PyQt5/                 # Библиотеки Qt
├── numpy/                 # Научные библиотеки
├── scipy/
├── sksparse/              # Модуль Холецкого (критично!)
├── resources/             # Ресурсы приложения
├── crs_database/          # Базы данных систем координат
├── gui/resources/         # Ресурсы GUI
└── *.log                  # Файлы логов
```

## ⚙️ Настройки сборщика

Файл `P-of-Geo-Meas.spec` содержит следующие важные настройки:

- `console=True` - показывает консоль для отладки
- `upx=True` - сжатие исполняемого файла
- `icon=...` - иконка приложения
- `hiddenimports` - скрытые импорты для PyQt5 и научных библиотек
- `datas` - файлы данных (ресурсы, базы данных)

## 🔄 Обновление сборки

При внесении изменений в код:

```bash
cd GeoAdjustPro
pyinstaller P-of-Geo-Meas.spec --clean --noconfirm
```

Флаг `--clean` удаляет временные файлы предыдущей сборки.
