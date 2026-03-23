#!/usr/bin/env python3
"""
Создание минимального набора SVG иконок-заглушек для работы интерфейса
"""

import os
from pathlib import Path

# Создаем структуру папок
base_dir = Path("resources/icons")
base_dir.mkdir(parents=True, exist_ok=True)

toolbar_dir = base_dir / "toolbar"
toolbar_dir.mkdir(exist_ok=True)

table_dir = base_dir / "table"
table_dir.mkdir(exist_ok=True)

# SVG шаблон для иконок
SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    {content}
</svg>
"""

# Иконки для тулбара
toolbar_icons = {
    "new_project": '<rect x="4" y="4" width="16" height="16" fill="#4a90e2" stroke="#2c5da8" stroke-width="2"/>',
    "open_project": '<circle cx="12" cy="12" r="8" fill="#5cb85c" stroke="#3d8b3d" stroke-width="2"/>',
    "save_project": '<path d="M4 20H20V18H4V20ZM18 4H14V10H10V4H6V20H18V4Z" fill="#d9534f"/>',
    "import_data": '<path d="M12 2L12 14M12 14L16 10M12 14L8 10" stroke="#f0ad4e" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    "preprocessing": '<circle cx="12" cy="12" r="9" fill="none" stroke="#5bc0de" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="#5bc0de"/>',
    "adjustment": '<rect x="3" y="3" width="18" height="18" fill="none" stroke="#9b59b6" stroke-width="2"/><line x1="3" y1="9" x2="21" y2="9" stroke="#9b59b6" stroke-width="2"/><line x1="3" y1="15" x2="21" y2="15" stroke="#9b59b6" stroke-width="2"/>',
    "error_search": '<circle cx="12" cy="12" r="10" fill="none" stroke="#e74c3c" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="#e74c3c" stroke-width="2"/><circle cx="12" cy="16" r="1" fill="#e74c3c"/>',
    "reporting": '<rect x="5" y="3" width="14" height="18" fill="#3498db" stroke="#2980b9" stroke-width="2"/><line x1="9" y1="9" x2="15" y2="9" stroke="white" stroke-width="2"/><line x1="9" y1="13" x2="15" y2="13" stroke="white" stroke-width="2"/><line x1="9" y1="17" x2="15" y2="17" stroke="white" stroke-width="2"/>',
}

# Иконки для таблицы
table_icons = {
    "point_fixed": '<circle cx="12" cy="12" r="8" fill="#95a5a6" stroke="#7f8c8d" stroke-width="2"/>',
    "point_approximate": '<circle cx="12" cy="12" r="8" fill="#f39c12" stroke="#d35400" stroke-width="2"/>',
    "point_free": '<circle cx="12" cy="12" r="8" fill="#e74c3c" stroke="#c0392b" stroke-width="2"/>',
    "obs_direction": '<line x1="4" y1="12" x2="20" y2="12" stroke="#3498db" stroke-width="2" stroke-linecap="round"/><polygon points="16,8 20,12 16,16" fill="#3498db"/>',
    "obs_distance": '<line x1="4" y1="12" x2="20" y2="12" stroke="#2ecc71" stroke-width="2" stroke-linecap="round"/><circle cx="4" cy="12" r="2" fill="#2ecc71"/><circle cx="20" cy="12" r="2" fill="#2ecc71"/>',
    "obs_height_diff": '<path d="M4 20L12 4L20 20" stroke="#9b59b6" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
}

# Создаем иконки для тулбара
for name, content in toolbar_icons.items():
    svg_content = SVG_TEMPLATE.format(content=content)
    file_path = toolbar_dir / f"{name}.svg"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Создана иконка: {file_path}")

# Создаем иконки для таблицы
for name, content in table_icons.items():
    svg_content = SVG_TEMPLATE.format(content=content)
    file_path = table_dir / f"{name}.svg"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Создана иконка: {file_path}")

# Создаем простую иконку приложения (ICO заглушка - простой PNG переименованный в ico для теста)
# Для полноценной ICO нужен PIL/Pillow, но создадим минимальный бинарный файл
ico_path = base_dir / "app_icon.ico"
# Минимальный ICO файл (16x16, 1 цвет)
ico_header = bytes([
    0x00, 0x00, 0x01, 0x00,  # ICO header
    0x01, 0x00,              # 1 image
    0x10, 0x10,              # 16x16 width/height
    0x01,                    # 1 color plane
    0x20,                    # 32 bits per pixel (RGBA)
    0x68, 0x04, 0x00, 0x00,  # data size
    0x16, 0x00, 0x00, 0x00,  # data offset
])
# Простые данные изображения (синий квадрат)
img_data = bytes([0x00, 0x80, 0xFF, 0xFF] * 256)  # RGBA pixels
with open(ico_path, 'wb') as f:
    f.write(ico_header + img_data)
print(f"Создана иконка приложения: {ico_path}")

# Создаем файлы стилей
styles_dir = Path("resources/styles")
styles_dir.mkdir(parents=True, exist_ok=True)

styles_content = """/* Стиль по умолчанию для P-of-Geo-Meas */

/* Главное окно */
QMainWindow {
    background-color: #f0f0f0;
}

/* Меню */
QMenuBar {
    background-color: #e0e0e0;
    border-bottom: 1px solid #c0c0c0;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background-color: #d0d0d0;
}

/* Статус бар */
QStatusBar {
    background-color: #e0e0e0;
    border-top: 1px solid #c0c0c0;
}

/* Кнопки панели инструментов */
QToolButton {
    border: 1px solid #c0c0c0;
    border-radius: 2px;
    padding: 4px;
    background-color: #f5f5f5;
}

QToolButton:hover {
    background-color: #e8e8e8;
    border: 1px solid #a0a0a0;
}

QToolButton:pressed {
    background-color: #d0d0d0;
}

/* Таблицы */
QTableView {
    background-color: white;
    alternate-background-color: #f8f8f8;
    gridline-color: #d0d0d0;
    selection-background-color: #4a90e2;
    selection-color: white;
}

QHeaderView::section {
    background-color: #e8e8e8;
    padding: 4px;
    border: 1px solid #c0c0c0;
    font-weight: bold;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #c0c0c0;
    background-color: white;
}

QTabBar::tab {
    background-color: #e8e8e8;
    border: 1px solid #c0c0c0;
    padding: 6px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 1px solid white;
}

QTabBar::tab:hover {
    background-color: #d8d8d8;
}
"""

styles_file = styles_dir / "styles.qss"
with open(styles_file, 'w', encoding='utf-8') as f:
    f.write(styles_content)
print(f"Создан файл стилей: {styles_file}")

# Также копируем стили в gui/resources если нужно
gui_styles_dir = Path("src/geoadjust/gui/resources/styles")
gui_styles_dir.mkdir(parents=True, exist_ok=True)
gui_styles_file = gui_styles_dir / "default.qss"
with open(gui_styles_file, 'w', encoding='utf-8') as f:
    f.write(styles_content)
print(f"Создан файл стилей GUI: {gui_styles_file}")

print("\n✅ Все ресурсы созданы успешно!")
print("Теперь можно запускать сборку проекта.")
