# 📦 РУКОВОДСТВО ПО СБОРКЕ И УСТАНОВКЕ P-OF-GEO-MEAS

## 🎯 ОБЗОР

Этот документ описывает процесс сборки автономного исполняемого файла и установщика для проекта **P-of-Geo-Meas** с использованием **Poetry** и **PyInstaller**.

---

## 📋 ТРЕБОВАНИЯ

### Для разработки:
- Python 3.8 - 3.12
- Poetry 1.8+
- Git

### Для сборки исполняемого файла:
- PyInstaller 5.13+ (устанавливается автоматически)
- Доступ к интернету для загрузки зависимостей

### Для создания установщика Windows:
- Inno Setup 6.0+ (только Windows)

---

## 🚀 БЫСТРЫЙ СТАРТ

### 1. Установка Poetry

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -

# Проверка установки
poetry --version
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/geoadjust/P-of-Geo-Meas.git
cd P-of-Geo-Meas
```

### 3. Установка зависимостей

```bash
# Установка всех зависимостей
poetry install

# Активация виртуального окружения
poetry shell
```

---

## 🔨 СБОРКА ПРИЛОЖЕНИЯ

### Автоматическая сборка (рекомендуется)

```bash
# Запуск автоматической сборки
poetry run build-release
```

Этот скрипт выполнит:
1. Очистку директорий сборки
2. Создание spec-файла для PyInstaller
3. Сборку приложения
4. Тестирование собранного приложения
5. Создание портативного ZIP-архива
6. Создание установщика (только Windows с Inno Setup)

### Ручная сборка

#### Шаг 1: Создание spec-файла

```bash
# Windows
poetry run pyi-makespec ^
  --name P-of-Geo-Meas ^
  --windowed ^
  --add-data "resources;resources" ^
  --add-data "src/geoadjust/crs;crs_database" ^
  --add-data "src/geoadjust/gui/resources;gui/resources" ^
  --hidden-import PyQt5.QtPrintSupport ^
  --hidden-import PyQt5.QtSvg ^
  --hidden-import sksparse ^
  src/geoadjust/__main__.py

# Linux/macOS
poetry run pyi-makespec \
  --name P-of-Geo-Meas \
  --windowed \
  --add-data "resources:resources" \
  --add-data "src/geoadjust/crs:crs_database" \
  --add-data "src/geoadjust/gui/resources:gui/resources" \
  --hidden-import PyQt5.QtPrintSupport \
  --hidden-import PyQt5.QtSvg \
  --hidden-import sksparse \
  src/geoadjust/__main__.py
```

#### Шаг 2: Сборка приложения

```bash
poetry run pyinstaller P-of-Geo-Meas.spec --clean --noconfirm
```

#### Шаг 3: Проверка результата

```bash
# Перейдите в папку с результатом
cd dist/P-of-Geo-Meas

# Запустите приложение
./P-of-Geo-Meas  # Linux/macOS
P-of-Geo-Meas.exe  # Windows
```

---

## 📦 СОЗДАНИЕ УСТАНОВЩИКА (WINDOWS)

### 1. Установите Inno Setup

Скачайте с официального сайта: https://jrsoftware.org/isdl.php

### 2. Скомпилируйте установщик

```bash
# Через командную строку
iscc P-of-Geo-Meas.iss

# Или откройте файл в Inno Setup Compiler и нажмите F9
```

Готовый установщик появится в папке `Output/`.

---

## 🧪 ТЕСТИРОВАНИЕ

### Проверка на чистой системе

1. Создайте виртуальную машину с чистой ОС
2. Установите только что созданный установщик
3. Проверьте:
   - Запуск приложения
   - Работу всех функций
   - Импорт/экспорт данных
   - Сохранение проектов

### Проверка портативной версии

1. Распакуйте ZIP-архив в новую папку
2. Запустите executable-файл
3. Убедитесь, что все функции работают

---

## 📊 СТРУКТУРА РЕЛИЗА

```
P-of-Geo-Meas-Release-1.0.0/
├── P-of-Geo-Meas-Setup-1.0.0.exe    # Установщик Windows (~400 МБ)
├── P-of-Geo-Meas-1.0.0-portable.zip # Портативная версия (~350 МБ)
├── INSTALL.txt                       # Инструкция по установке
├── README.md                         # Описание проекта
├── LICENSE                           # Лицензия MIT
└── BUILD_GUIDE.md                    # Это руководство
```

---

## ⚙️ НАСТРОЙКА PYINSTALLER

### Spec-файл

Файл `P-of-Geo-Meas.spec` содержит настройки сборки:

```python
# Основные параметры
name = 'P-of-Geo-Meas'
windowed = True  # Без консоли
icon = 'resources/icons/app_icon.ico'

# Данные для включения
datas = [
    ('resources', 'resources'),
    ('src/geoadjust/crs', 'crs_database'),
    ('src/geoadjust/gui/resources', 'gui/resources'),
]

# Скрытые импорты
hiddenimports = [
    'PyQt5.QtPrintSupport',
    'PyQt5.QtSvg',
    'sksparse',
    'sksparse.cholmod',
    # ... другие модули
]
```

### Общие проблемы и решения

| Проблема | Решение |
|----------|---------|
| Missing module error | Добавьте модуль в `hiddenimports` |
| Resources not found | Проверьте пути в `datas` |
| Большой размер exe | Включите сжатие UPX (`upx=True`) |
| Антивирус блокирует | Подпишите цифровой подписью |

---

## 🔄 АВТОМАТИЗАЦИЯ ЧЕРЕЗ CI/CD

### GitHub Actions пример

Создайте файл `.github/workflows/build.yml`:

```yaml
name: Build Release

on:
  release:
    types: [created]

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install Poetry
      run: pip install poetry
      
    - name: Install dependencies
      run: poetry install
      
    - name: Build executable
      run: poetry run build-release
      
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: P-of-Geo-Meas-Windows
        path: |
          dist/P-of-Geo-Meas/
          *.zip
```

---

## 💡 СОВЕТЫ POETRY

### Управление зависимостями

```bash
# Добавить новую зависимость
poetry add package-name

# Добавить зависимость для разработки
poetry add --group dev package-name

# Обновить зависимости
poetry update

# Экспорт в requirements.txt
poetry export -f requirements.txt --output requirements.txt
```

### Проверка проекта

```bash
# Проверка конфигурации
poetry check

# Показать зависимости
poetry show

# Построить пакет
poetry build
```

---

## 🐛 ОТЛАДКА

### Включение логов PyInstaller

```bash
poetry run pyinstaller --log-level DEBUG P-of-Geo-Meas.spec
```

### Проверка содержимого exe

Используйте утилиту `pyi-archive_viewer`:

```bash
poetry run pyi-archive_viewer dist/P-of-Geo-Meas/P-of-Geo-Meas.exe
```

### Запуск с консолью для отладки

Измените в spec-файле:
```python
console=True  # Вместо False
```

---

## 📞 ПОДДЕРЖКА

- Документация: https://github.com/geoadjust/P-of-Geo-Meas/wiki
- Issues: https://github.com/geoadjust/P-of-Geo-Meas/issues
- Email: support@geoadjust.pro

---

## 📝 ЛИЦЕНЗИЯ

MIT License - см. файл LICENSE

© 2024 GeoAdjust Team
