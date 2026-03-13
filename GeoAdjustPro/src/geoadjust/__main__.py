"""
Точка входа в приложение GeoAdjust Pro
"""

import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Основная функция запуска приложения"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("GeoAdjust Pro")
    app.setOrganizationName("GeoAdjust Team")
    app.setStyle('Fusion')
    
    # Настройка шрифтов
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Импорт главного окна
    from geoadjust.gui.main_window import MainWindow, MainWindowConfig, InterfaceType
    
    # Создание конфигурации
    config = MainWindowConfig(
        interface_type=InterfaceType.RIBBON,
        window_title="GeoAdjust Pro",
        window_size=(1600, 900),
        window_state="maximized",
        theme="light"
    )
    
    # Создание и показ главного окна
    window = MainWindow(config)
    window.show()
    
    logger.info("Приложение GeoAdjust Pro запущено")
    
    # Запуск цикла событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
