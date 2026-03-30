"""
Главное окно приложения GeoAdjust Pro

Поддерживает два типа интерфейса:
- Классический (меню и тулбары)
- Ленточный (современный ribbon-интерфейс)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import logging

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QMenu, QAction,
    QToolBar, QStatusBar, QLabel, QProgressBar, QDockWidget, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QTabWidget,
    QDialog, QDialogButtonBox, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QFormLayout,
    QMessageBox, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

# Импорт центральной функции для работы с ресурсами
from geoadjust.utils import get_resource_path

logger = logging.getLogger(__name__)


class InterfaceType(Enum):
    """Тип интерфейса программы"""
    CLASSIC = "classic"  # Меню и тулбары (как в КРЕДО ДАТ 3.х)
    RIBBON = "ribbon"    # Ленточный интерфейс (современный)


@dataclass
class MainWindowConfig:
    """Конфигурация главного окна"""
    interface_type: InterfaceType = InterfaceType.RIBBON
    window_title: str = "GeoAdjust Pro"
    window_size: Tuple[int, int] = (1600, 900)
    window_state: str = "maximized"  # normal, maximized, fullscreen
    theme: str = "light"  # light, dark, system


class MainWindow(QMainWindow):
    """Главное окно приложения GeoAdjust Pro"""
    
    # Сигналы
    project_created = pyqtSignal(str)
    project_opened = pyqtSignal(str)
    project_saved = pyqtSignal()
    data_imported = pyqtSignal(str)
    
    def __init__(self, config: Optional[MainWindowConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or MainWindowConfig()
        self.current_project = None
        
        # Создание интеграции обработки
        self.processing_integration = None
        
        # Настройка окна
        self.setWindowTitle(self.config.window_title)
        self._load_icon()
        
        # Установка простого стиля для надежности
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QMenuBar {
                background-color: #e0e0e0;
                border-bottom: 1px solid #cccccc;
            }
            QStatusBar {
                background-color: #e0e0e0;
                border-top: 1px solid #cccccc;
            }
        """)
        
        if self.config.window_state == "maximized":
            self.setWindowState(Qt.WindowMaximized)
        else:
            self.resize(*self.config.window_size)
        
        # Центральный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Основной макет
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создание компонентов интерфейса
        self._create_menu_bar()
        
        if self.config.interface_type == InterfaceType.RIBBON:
            self._create_ribbon_interface()
        else:
            self._create_classic_toolbars()
        
        self._create_status_bar()
        self._create_dock_widgets()
        self._create_main_area()
        
        # Загрузка конфигурации рабочей области
        self._load_workspace_config()
    
    def _load_icon(self):
        """Загрузка иконки приложения с обработкой ошибок"""
        try:
            icon_path = get_resource_path("gui/resources/icons/app_icon.ico")
            if hasattr(icon_path, 'exists') and icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # Использовать стандартную иконку
                self.setWindowIcon(QIcon.fromTheme("applications-science"))
                logger.warning(f"Иконка не найдена: {icon_path}, используется стандартная")
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
            # Продолжить без иконки или использовать стандартную
            self.setWindowIcon(QIcon.fromTheme("applications-science"))
    
    def _create_menu_bar(self):
        """Создание главного меню"""
        menu_bar = self.menuBar()
        
        # Меню Файл
        file_menu = menu_bar.addMenu("Файл")
        
        # Создание проекта
        new_project_action = QAction("Создать проект", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self._create_project)
        file_menu.addAction(new_project_action)
        
        # Открытие проекта
        open_project_action = QAction("Открыть проект", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self._open_project)
        file_menu.addAction(open_project_action)
        
        # Сохранение проекта
        save_project_action = QAction("Сохранить проект", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self._save_project)
        file_menu.addAction(save_project_action)
        
        # Сохранить как
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Свойства проекта
        properties_action = QAction("Свойства проекта", self)
        properties_action.triggered.connect(self._project_properties)
        file_menu.addAction(properties_action)
        
        file_menu.addSeparator()
        
        # Параметры программы
        settings_action = QAction("Параметры программы", self)
        settings_action.triggered.connect(self._program_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Выход
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Данные
        data_menu = menu_bar.addMenu("Данные")
        
        # Импорт
        import_file_action = QAction("Импорт из файла...", self)
        import_file_action.setShortcut("Ctrl+I")
        import_file_action.triggered.connect(self._import_file)
        data_menu.addAction(import_file_action)
        
        import_instrument_action = QAction("Импорт из прибора...", self)
        import_instrument_action.triggered.connect(self._import_from_instrument)
        data_menu.addAction(import_instrument_action)
        
        data_menu.addSeparator()
        
        # Экспорт
        export_file_action = QAction("Экспорт в файл...", self)
        export_file_action.setShortcut("Ctrl+E")
        export_file_action.triggered.connect(self._export_file)
        data_menu.addAction(export_file_action)
        
        export_credo_action = QAction("Экспорт в КРЕДО...", self)
        export_credo_action.triggered.connect(self._export_to_credo)
        data_menu.addAction(export_credo_action)
        
        # Меню Редактирование
        edit_menu = menu_bar.addMenu("Редактирование")
        
        undo_action = QAction("Отменить", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Повторить", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        copy_action = QAction("Копировать", self)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Вставить", self)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # Добавление данных
        add_point_action = QAction("Добавить пункт", self)
        add_point_action.setShortcut("Ctrl+P")
        add_point_action.triggered.connect(self._add_point)
        edit_menu.addAction(add_point_action)
        
        add_obs_action = QAction("Добавить измерение", self)
        add_obs_action.setShortcut("Ctrl+M")
        add_obs_action.triggered.connect(self._add_observation)
        edit_menu.addAction(add_obs_action)
        
        # Меню Вид
        view_menu = menu_bar.addMenu("Вид")
        
        scheme_action = QAction("Схема сети", self)
        scheme_action.setShortcut("F5")
        scheme_action.triggered.connect(self._show_scheme)
        view_menu.addAction(scheme_action)
        
        view_menu.addSeparator()
        
        # Панели
        panels_menu = view_menu.addMenu("Панели")
        panels_menu.addAction("Пункты ПВО")
        panels_menu.addAction("Измерения")
        panels_menu.addAction("План")
        panels_menu.addAction("Журнал")
        panels_menu.addAction("Свойства")
        
        # Меню Обработка
        process_menu = menu_bar.addMenu("Обработка")
        
        preprocessing_action = QAction("Предобработка", self)
        preprocessing_action.triggered.connect(self._run_preprocessing)
        process_menu.addAction(preprocessing_action)
        
        process_menu.addSeparator()
        
        adjust_classic_action = QAction("Классический МНК", self)
        adjust_classic_action.triggered.connect(self._adjust_classic)
        process_menu.addAction(adjust_classic_action)
        
        adjust_robust_action = QAction("Робастное уравнивание", self)
        adjust_robust_action.triggered.connect(self._adjust_robust)
        process_menu.addAction(adjust_robust_action)
        
        # Меню Отчёты
        report_menu = menu_bar.addMenu("Отчёты")
        
        coordinate_schedule_action = QAction("Ведомость координат", self)
        coordinate_schedule_action.triggered.connect(self._coordinate_schedule)
        report_menu.addAction(coordinate_schedule_action)
        
        correction_schedule_action = QAction("Ведомость поправок", self)
        correction_schedule_action.triggered.connect(self._correction_schedule)
        report_menu.addAction(correction_schedule_action)
        
        report_menu.addSeparator()
        
        gost_report_action = QAction("Отчёт по ГОСТ 7.32-2017", self)
        gost_report_action.triggered.connect(self._gost_report)
        report_menu.addAction(gost_report_action)
        
        # Меню Справка
        help_menu = menu_bar.addMenu("Справка")
        
        help_content_action = QAction("Содержание", self)
        help_content_action.setShortcut("F1")
        help_content_action.triggered.connect(self._show_help)
        help_menu.addAction(help_content_action)
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._about_program)
        help_menu.addAction(about_action)
    
    def _create_ribbon_interface(self):
        """Создание ленточного интерфейса"""
        from .widgets.ribbon_widget import RibbonWidget
        
        self.ribbon = RibbonWidget(self)
        
        # Вкладка "Главная"
        home_tab = self.ribbon.add_tab("Главная")
        home_tab.add_group("Проект", [
            ("Новый проект", "new_project", "Ctrl+N", self._create_project),
            ("Открыть", "open_project", "Ctrl+O", self._open_project),
            ("Сохранить", "save_project", "Ctrl+S", self._save_project),
        ])
        home_tab.add_group("Буфер обмена", [
            ("Копировать", "copy", "Ctrl+C", None),
            ("Вставить", "paste", "Ctrl+V", None),
        ])
        
        # Вкладка "Данные"
        data_tab = self.ribbon.add_tab("Данные")
        data_tab.add_group("Импорт", [
            ("Импорт из прибора", "import_from_instrument", None, self._import_from_instrument),
            ("Импорт файла", "import_file", None, self._import_file),
        ])
        data_tab.add_group("Экспорт", [
            ("Экспорт в файл", "export_file", None, self._export_file),
            ("Экспорт в КРЕДО", "export_to_credo", None, self._export_to_credo),
        ])
        
        # Вкладка "Редактирование"
        edit_tab = self.ribbon.add_tab("Редактирование")
        edit_tab.add_group("Добавление данных", [
            ("Добавить пункт", "add_point", "Ctrl+P", self._add_point),
            ("Добавить измерение", "add_observation", "Ctrl+M", self._add_observation),
        ])
        edit_tab.add_group("Буфер обмена", [
            ("Копировать", "copy", "Ctrl+C", None),
            ("Вставить", "paste", "Ctrl+V", None),
        ])
        
        # Вкладка "Обработка"
        process_tab = self.ribbon.add_tab("Обработка")
        process_tab.add_group("Предобработка", [
            ("Контроль допусков", "check_tolerances", None, self._check_tolerances),
            ("Применение редукций", "apply_corrections", None, self._apply_corrections),
        ])
        process_tab.add_group("Уравнивание", [
            ("Классический МНК", "adjust_classic", None, self._adjust_classic),
            ("Робастное уравнивание", "adjust_robust", None, self._adjust_robust),
        ])
        
        # Вкладка "Анализ"
        analysis_tab = self.ribbon.add_tab("Анализ")
        analysis_tab.add_group("Надёжность", [
            ("Анализ по Баарду", "baarda_analysis", None, self._baarda_analysis),
            ("Поиск грубых ошибок", "gross_error_search", None, self._gross_error_search),
        ])
        analysis_tab.add_group("Визуализация", [
            ("Эллипсы ошибок", "error_ellipses", None, self._error_ellipses),
            ("Тепловые карты", "heatmaps", None, self._heatmaps),
        ])
        
        # Вкладка "Отчёты"
        report_tab = self.ribbon.add_tab("Отчёты")
        report_tab.add_group("Ведомости", [
            ("Ведомость координат", "coordinate_schedule", None, self._coordinate_schedule),
            ("Ведомость поправок", "correction_schedule", None, self._correction_schedule),
        ])
        report_tab.add_group("ГОСТ", [
            ("Отчёт по ГОСТ 7.32-2017", "gost_report", None, self._gost_report),
            ("Сертификат соответствия", "compliance_certificate", None, self._compliance_certificate),
        ])
        
        # Панель быстрого доступа
        quick_access = self.ribbon.add_quick_access_toolbar()
        quick_access.add_action("Сохранить", self._save_project)
        quick_access.add_action("Отменить", None)
        quick_access.add_action("Повторить", None)
        
        # Ribbon widget уже является QTabWidget и добавляется в центральною область
    
    def _create_classic_toolbars(self):
        """Создание классических тулбаров"""
        # Тулбар "Стандартный"
        standard_toolbar = QToolBar("Стандартный", self)
        standard_toolbar.addAction("Новый проект", self._create_project)
        standard_toolbar.addAction("Открыть", self._open_project)
        standard_toolbar.addAction("Сохранить", self._save_project)
        self.addToolBar(Qt.TopToolBarArea, standard_toolbar)
        
        # Тулбар "Редактирование"
        edit_toolbar = QToolBar("Редактирование", self)
        edit_toolbar.addAction("Отменить")
        edit_toolbar.addAction("Повторить")
        edit_toolbar.addAction("Копировать")
        edit_toolbar.addAction("Вставить")
        self.addToolBar(Qt.TopToolBarArea, edit_toolbar)
        
        # Тулбар "Данные"
        data_toolbar = QToolBar("Данные", self)
        
        # Добавить пункт с иконкой
        add_point_action = QAction("Добавить пункт", self)
        add_point_icon_path = get_resource_path("icons/toolbar/add_point.svg")
        if hasattr(add_point_icon_path, 'exists') and add_point_icon_path.exists():
            add_point_action.setIcon(QIcon(str(add_point_icon_path)))
        add_point_action.triggered.connect(self._add_point)
        data_toolbar.addAction(add_point_action)
        
        # Добавить измерение с иконкой
        add_obs_action = QAction("Добавить измерение", self)
        add_obs_icon_path = get_resource_path("icons/toolbar/add_observation.svg")
        if hasattr(add_obs_icon_path, 'exists') and add_obs_icon_path.exists():
            add_obs_action.setIcon(QIcon(str(add_obs_icon_path)))
        add_obs_action.triggered.connect(self._add_observation)
        data_toolbar.addAction(add_obs_action)
        
        self.addToolBar(Qt.TopToolBarArea, data_toolbar)
        
        # Тулбар "Обработка"
        process_toolbar = QToolBar("Обработка", self)
        process_toolbar.addAction("Предобработка", self._run_preprocessing)
        process_toolbar.addAction("МНК", self._adjust_classic)
        process_toolbar.addAction("Робастное", self._adjust_robust)
        self.addToolBar(Qt.TopToolBarArea, process_toolbar)
    
    def _create_status_bar(self):
        """Создание строки состояния"""
        status_bar = self.statusBar()
        
        # Информация о проекте
        self.project_label = QLabel("Проект: не открыт")
        status_bar.addWidget(self.project_label)
        
        # Информация о текущем режиме
        self.mode_label = QLabel("Режим: ожидание")
        status_bar.addWidget(self.mode_label)
        
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(), spacer.sizePolicy().verticalPolicy())
        spacer.setMinimumWidth(20)
        status_bar.addPermanentWidget(spacer)
        
        # Прогресс выполнения операций
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # Информация о координатах (для графического окна)
        self.coords_label = QLabel("")
        status_bar.addPermanentWidget(self.coords_label)
    
    def _create_dock_widgets(self):
        """Создание док-виджетов"""
        from .components.dock_widgets import PointsDockWidget, ObservationsDockWidget, TraversesDockWidget
        from .components.tables import PointsTableView, ObservationsTableView
        from .components.plan_view import PlanGraphicsView
        from .components.log_widget import LogWidget
        from .components.properties_widget import PropertiesWidget
        
        # Окно "Пункты ПВО"
        self.points_dock = PointsDockWidget("Пункты ПВО", self)
        self.points_table = PointsTableView()
        self.points_dock.setWidget(self.points_table)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.points_dock)
        
        # Окно "Измерения"
        self.observations_dock = ObservationsDockWidget("Измерения", self)
        self.observations_table = ObservationsTableView()
        self.observations_dock.setWidget(self.observations_table)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.observations_dock)
        
        # Окно "Ходы и секции"
        self.traverses_dock = TraversesDockWidget("Ходы и секции", self)
        self.traverses_tree = QTreeWidget()
        self.traverses_dock.setWidget(self.traverses_tree)
        self.addDockWidget(Qt.RightDockWidgetArea, self.traverses_dock)
        
        # План создается как виджет для центральной области (не док-виджет)
        self.plan_view = PlanGraphicsView()
        
        # Окно "Журнал"
        self.log_dock = QDockWidget("Журнал", self)
        self.log_widget = LogWidget()
        self.log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        
        # Окно "Свойства"
        self.properties_dock = QDockWidget("Свойства", self)
        self.properties_widget = PropertiesWidget()
        self.properties_dock.setWidget(self.properties_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
    
    def _create_main_area(self):
        """Создание центральной области"""
        # Центральная область для главного окна уже создана через setCentralWidget
        # Док-виджеты уже добавлены через addDockWidget в _create_dock_widgets
        # Здесь только настраиваем splitter для центральных панелей
        
        # Создаем центральный виджет для основной рабочей области
        central_content = QWidget()
        central_layout = QVBoxLayout(central_content)
        central_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        central_layout.addWidget(self.main_splitter)
        
        # Левая панель - контейнеры для таблиц данных
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        # Центральная панель - План (основная рабочая область)
        # План добавляется напрямую в splitter для отображения по центру
        
        # Правая панель - контейнеры для графики и свойств
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(self.plan_view)  # План по центру
        self.main_splitter.addWidget(right_container)
        
        # Установка начальных размеров: левая панель, план (центр), правая панель
        self.main_splitter.setSizes([200, 800, 200])
        
        # Добавляем центральный контент в главный layout
        self.main_layout.addWidget(central_content)
    
    def _load_workspace_config(self):
        """Загрузка конфигурации рабочей области"""
        # TODO: Загрузка сохранённой конфигурации из файла
        pass
    
    # Обработчики действий меню
    def _create_project(self):
        """Создание нового проекта"""
        logger.info("Создание нового проекта")
        from .dialogs.project_wizard import ProjectWizard
        
        wizard = ProjectWizard(self)
        if wizard.exec_() == QDialog.Accepted:
            project_data = wizard.get_project_data()
            self._setup_project(project_data)
    
    def _setup_project(self, project_data: Dict[str, Any]):
        """Настройка созданного проекта"""
        try:
            from geoadjust.io.project.project_manager import ProjectManager
            
            project_manager = ProjectManager()
            # Исправлен порядок аргументов: сначала path, затем name
            project = project_manager.create_project(
                Path(project_data['path']),
                project_data['name']
            )
            self.current_project = project
            
            # Обновление интерфейса
            self.project_label.setText(f"Проект: {project_data['name']}")
            self.statusBar().showMessage(f"Проект '{project_data['name']}' создан", 3000)
            
            logger.info(f"Проект создан: {project_data['name']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать проект:\n{str(e)}")
            logger.error(f"Ошибка при создании проекта: {e}", exc_info=True)
    
    def _open_project(self):
        """Открытие существующего проекта"""
        logger.info("Открытие проекта")
        
        # Используем getExistingDirectory для выбора директории .gad
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку проекта (.gad)",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not dir_path:
            return
        
        # Проверяем, что это действительно папка проекта .gad
        path = Path(dir_path)
        if not path.suffix.lower() == '.gad':
            # Проверяем, содержит ли папка файл project.gadproj
            project_file = path / 'project.gadproj'
            if not project_file.exists():
                QMessageBox.warning(
                    self,
                    "Неверный формат",
                    f"Выбранная папка не является проектом GeoAdjust:\n{dir_path}\n\n"
                    f"Пожалуйста, выберите папку с расширением .gad или папку, содержащую файл project.gadproj"
                )
                return
            file_path = str(project_file)
        else:
            # Это папка .gad, проверяем наличие project.gadproj внутри
            project_file = path / 'project.gadproj'
            if not project_file.exists():
                QMessageBox.warning(
                    self,
                    "Ошибка проекта",
                    f"В папке проекта отсутствует файл project.gadproj:\n{dir_path}"
                )
                return
            file_path = str(project_file)
        
        if file_path:
            try:
                from geoadjust.io.project.project_manager import ProjectManager
                
                project_manager = ProjectManager()
                self.current_project = project_manager.open_project(Path(file_path))
                
                # Обновление интерфейса
                self.project_label.setText(f"Проект: {self.current_project.name}")
                self.statusBar().showMessage(f"Проект '{self.current_project.name}' загружен", 3000)
                
                logger.info(f"Проект загружен: {self.current_project.name}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть проект:\n{str(e)}")
                logger.error(f"Ошибка при открытии проекта: {e}")
    
    def _save_project(self):
        """Сохранение проекта"""
        logger.info("Сохранение проекта")
        
        if self.current_project:
            try:
                from geoadjust.io.project.project_manager import ProjectManager
                
                project_manager = ProjectManager()
                project_manager.save_project()
                
                self.statusBar().showMessage(f"Проект '{self.current_project.name}' сохранён", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить проект:\n{str(e)}")
                logger.error(f"Ошибка при сохранении проекта: {e}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
    
    def _save_project_as(self):
        """Сохранение проекта в новое место"""
        logger.info("Сохранение проекта как...")
        
        if self.current_project:
            file_path = QFileDialog.getSaveFileName(
                self,
                "Сохранить проект как...",
                "",
                "GeoAdjust Project (*.gad)"
            )[0]
            
            if file_path:
                try:
                    from pathlib import Path
                    from geoadjust.io.project.project_manager import ProjectManager
                    
                    project_manager = ProjectManager()
                    project_manager.save_project_as(Path(file_path))
                    
                    self.statusBar().showMessage(f"Проект сохранён в {file_path}", 3000)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить проект:\n{str(e)}")
                    logger.error(f"Ошибка при сохранении проекта: {e}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
    
    def _project_properties(self):
        """Открытие диалога свойств проекта"""
        from .dialogs.project_properties import ProjectPropertiesDialog
        
        dialog = ProjectPropertiesDialog(self.current_project, self)
        if dialog.exec_() == QDialog.Accepted:
            logger.info("Свойства проекта обновлены")
    
    def _program_settings(self):
        """Открытие диалога параметров программы"""
        from .dialogs.program_settings import ProgramSettingsDialog
        
        dialog = ProgramSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            logger.info("Параметры программы обновлены")
    
    def _run_preprocessing(self):
        """Запуск предобработки"""
        logger.info("Запуск предобработки")
    
    def _adjust_classic(self):
        """Классическое МНК уравнивание"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК КЛАССИЧЕСКОГО МНК УРАВНИВАНИЯ")
        logger.info("=" * 60)
        
        if not self.current_project:
            logger.error("Нет открытого проекта для уравнивания")
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            logger.info(f"Текущий проект: {self.current_project.name}")
            logger.info("Проверка данных проекта...")
            
            # Получение данных из проекта для проверки
            observations = self.current_project.get_observations()
            control_points = self.current_project.get_points()
            
            logger.info(f"Количество измерений: {len(observations) if observations else 0}")
            logger.info(f"Количество пунктов: {len(control_points) if control_points else 0}")
            
            if not observations:
                logger.error("В проекте нет измерений")
                QMessageBox.warning(self, "Предупреждение", "В проекте нет измерений")
                return
            
            self.mode_label.setText("Режим: уравнивание")
            self.statusBar().showMessage("Выполняется уравнивание...", 0)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            logger.info("Создание интеграции обработки...")
            # Создание интеграции обработки если ещё не создана
            if self.processing_integration is None:
                from geoadjust.gui.processing.integration import ProcessingIntegration
                self.processing_integration = ProcessingIntegration(self)
                
                # Подключение сигналов
                self.processing_integration.progress_updated.connect(self._on_progress_updated)
                self.processing_integration.processing_finished.connect(self._on_adjustment_finished)
                self.processing_integration.processing_error.connect(self._on_adjustment_error)
                logger.info("Интеграция обработки создана и настроена")
            
            # Установка моделей данных
            logger.info("Установка моделей данных...")
            self.processing_integration.set_models(
                self.points_table.model(),
                self.observations_table.model()
            )
            
            # Запуск уравнивания в отдельном потоке
            logger.info("Запуск потока обработки...")
            from geoadjust.gui.processing.processing_thread import ProcessingThread
            self.processing_thread = ProcessingThread(self.processing_integration)
            self.processing_thread.finished.connect(self._on_adjustment_finished)
            self.processing_thread.error_occurred.connect(self._on_adjustment_error)
            self.processing_thread.progress_updated.connect(self._on_progress_updated)
            self.processing_thread.start()
            
            logger.info("Поток обработки запущен")
            
        except Exception as e:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА при уравнивании: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при уравнивании:\n{str(e)}")
            self.statusBar().showMessage("Ошибка уравнивания", 3000)
            self._reset_ui_state()
    
    def _on_progress_updated(self, percent: int, message: str):
        """Обработчик обновления прогресса"""
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(message, 0)
    
    def _on_adjustment_finished(self, result: Dict[str, Any]):
        """Обработчик завершения уравнивания"""
        # Сохранение результатов в проект
        if self.current_project:
            self.current_project.save_adjustment_result(result)
        
        # Обновление интерфейса с результатами
        self._update_ui_with_results(result)
        
        sigma0 = result.get('sigma0', 0)
        self.statusBar().showMessage(f"Уравнивание выполнено: μ₀ = {sigma0:.6f}", 5000)
        self._reset_ui_state()
    
    def _on_adjustment_error(self, error_msg: str):
        """Обработчик ошибки уравнивания"""
        QMessageBox.critical(self, "Ошибка", f"Ошибка при уравнивании:\n{error_msg}")
        self.statusBar().showMessage("Ошибка уравнивания", 3000)
        self._reset_ui_state()
    
    def _adjust_robust(self):
        """Робастное уравнивание"""
        logger.info("Запуск робастного уравнивания")
        
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            self.mode_label.setText("Режим: робастное уравнивание")
            self.statusBar().showMessage("Выполняется робастное уравнивание...", 0)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            from geoadjust.core.adjustment.robust_methods import RobustMethods
            
            # Получение данных из проекта
            observations = self.current_project.get_observations()
            control_points = self.current_project.get_points()
            
            if not observations:
                QMessageBox.warning(self, "Предупреждение", "В проекте нет измерений")
                self._reset_ui_state()
                return
            
            # Создание интеграции обработки если ещё не создана
            if self.processing_integration is None:
                from geoadjust.gui.processing.integration import ProcessingIntegration
                self.processing_integration = ProcessingIntegration(self)
                
                # Подключение сигналов
                self.processing_integration.progress_updated.connect(self._on_progress_updated)
                self.processing_integration.processing_finished.connect(self._on_adjustment_finished)
                self.processing_integration.processing_error.connect(self._on_adjustment_error)
            
            # Установка моделей данных
            self.processing_integration.set_models(
                self.points_table.model(),
                self.observations_table.model()
            )
            
            # Запуск робастного уравнивания в отдельном потоке
            from geoadjust.gui.processing.processing_thread import ProcessingThread
            self.processing_thread = ProcessingThread(
                self.processing_integration,
                method='robust'
            )
            self.processing_thread.finished.connect(self._on_adjustment_finished)
            self.processing_thread.error_occurred.connect(self._on_adjustment_error)
            self.processing_thread.progress_updated.connect(self._on_progress_updated)
            self.processing_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при робастном уравнивании:\n{str(e)}")
            logger.error(f"Ошибка при робастном уравнивании: {e}", exc_info=True)
            self.statusBar().showMessage("Ошибка уравнивания", 3000)
            self._reset_ui_state()
    
    def _reset_ui_state(self):
        """Сброс UI в исходное состояние"""
        self.mode_label.setText("Режим: ожидание")
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
    
    def _update_ui_with_results(self, result: Dict[str, Any]):
        """Обновление интерфейса результатами уравнивания
        
        Args:
            result: Словарь с результатами уравнивания
        """
        # Обновление таблицы пунктов
        if hasattr(self, 'points_table') and 'adjusted_points' in result:
            self.points_table.update_data(result['adjusted_points'])
        
        # Обновление таблицы измерений
        if hasattr(self, 'observations_table') and 'residuals' in result:
            self.observations_table.update_residuals(result['residuals'])
        
        # Перерисовка плана
        if hasattr(self, 'plan_view'):
            self.plan_view.draw_network(self.current_project)
            
            # Отрисовка эллипсов ошибок (если есть)
            if 'accuracy' in result and 'error_ellipses' in result['accuracy']:
                self.plan_view.draw_error_ellipses(result['accuracy']['error_ellipses'])
    
    def _import_file(self):
        """Импорт данных из файла"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК ИМПОРТА ДАННЫХ ИЗ ФАЙЛА")
        logger.info("=" * 60)
        
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Сначала создайте или откройте проект")
            return
        
        try:
            from .dialogs.import_dialog import ImportDialog
            
            dialog = ImportDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                imported_data = dialog.get_imported_data()
                
                if imported_data:
                    # Добавление данных в проект
                    points = imported_data.get('points', [])
                    observations = imported_data.get('observations', [])
                    
                    # Обновление проекта
                    if points:
                        for point in points:
                            self.current_project.add_point(point)
                    
                    if observations:
                        for obs in observations:
                            self.current_project.add_observation(obs)
                    
                    # Обновление интерфейса
                    self._refresh_data_views()
                    
                    logger.info(f"Импортировано: {len(points)} пунктов, {len(observations)} измерений")
                    self.statusBar().showMessage(
                        f"Импортировано: {len(points)} пунктов, {len(observations)} измерений",
                        5000
                    )
                
        except Exception as e:
            logger.error(f"ОШИБКА при импорте файла: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте:\n{str(e)}")
    
    def _export_file(self):
        """Экспорт данных в файл"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК ЭКСПОРТА ДАННЫХ В ФАЙЛ")
        logger.info("=" * 60)
        
        if not self.current_project:
            logger.warning("Нет открытого проекта для экспорта")
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from .dialogs.export_dialog import ExportDialog
            
            dialog = ExportDialog(self.current_project, self)
            dialog.exec_()
                
        except Exception as e:
            logger.error(f"ОШИБКА при экспорте файла: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте:\n{str(e)}")
    
    def _export_to_credo(self):
        """Экспорт данных в КРЕДО"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК ЭКСПОРТА ДАННЫХ В КРЕДО")
        logger.info("=" * 60)
        
        if not self.current_project:
            logger.warning("Нет открытого проекта для экспорта в КРЕДО")
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Экспорт в КРЕДО",
                "",
                "CREDO files (*.tpf);;"
                "Все файлы (*)"
            )
            
            if file_path:
                logger.info(f"Выбран путь для экспорта в КРЕДО: {file_path}")
                # TODO: Реализация экспорта в формат КРЕДО
                QMessageBox.information(self, "Экспорт в КРЕДО", f"Данные будут экспортированы в:\n{file_path}\n\nФункция экспорта в КРЕДО в разработке")
                logger.info("Экспорт в КРЕДО завершен (заглушка)")
                
        except Exception as e:
            logger.error(f"ОШИБКА при экспорте в КРЕДО: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте в КРЕДО:\n{str(e)}")
    
    def _import_from_instrument(self):
        """Импорт данных из прибора"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК ИМПОРТА ДАННЫХ ИЗ ПРИБОРА")
        logger.info("=" * 60)
        
        try:
            # TODO: Диалог выбора прибора и порта
            QMessageBox.information(self, "Импорт из прибора", "Функция импорта из прибора в разработке")
            logger.info("Импорт из прибора завершен (заглушка)")
            
        except Exception as e:
            logger.error(f"ОШИБКА при импорте из прибора: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка при импорте из прибора:\n{str(e)}")
    
    def _add_point(self):
        """Добавление нового пункта"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Сначала создайте или откройте проект")
            return
        
        from .dialogs.point_editor import PointEditorDialog
        
        dialog = PointEditorDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            point_data = dialog.get_point_data()
            self.current_project.add_point(point_data)
            self._refresh_data_views()
            logger.info(f"Добавлен пункт: {point_data['name']}")
    
    def _edit_point(self, point_data: Dict[str, Any]):
        """Редактирование пункта"""
        from .dialogs.point_editor import PointEditorDialog
        
        dialog = PointEditorDialog(point_data=point_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_point_data()
            self.current_project.update_point(updated_data)
            self._refresh_data_views()
            logger.info(f"Обновлен пункт: {updated_data['name']}")
    
    def _delete_point(self, point_name: str):
        """Удаление пункта"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить пункт '{point_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_project.delete_point(point_name)
            self._refresh_data_views()
            logger.info(f"Удален пункт: {point_name}")
    
    def _add_observation(self):
        """Добавление нового измерения"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Сначала создайте или откройте проект")
            return
        
        from .dialogs.observation_editor import ObservationEditorDialog
        
        # Получение списка доступных пунктов
        points = self.current_project.get_points()
        point_names = [p['name'] for p in points] if points else []
        
        dialog = ObservationEditorDialog(available_points=point_names, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            obs_data = dialog.get_observation_data()
            self.current_project.add_observation(obs_data)
            self._refresh_data_views()
            logger.info(f"Добавлено измерение: {obs_data['from_point']} -> {obs_data['to_point']}")
    
    def _edit_observation(self, obs_data: Dict[str, Any]):
        """Редактирование измерения"""
        from .dialogs.observation_editor import ObservationEditorDialog
        
        points = self.current_project.get_points()
        point_names = [p['name'] for p in points] if points else []
        
        dialog = ObservationEditorDialog(
            observation_data=obs_data,
            available_points=point_names,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_observation_data()
            self.current_project.update_observation(updated_data)
            self._refresh_data_views()
            logger.info(f"Обновлено измерение")
    
    def _delete_observation(self, obs_id: int):
        """Удаление измерения"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить измерение?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_project.delete_observation(obs_id)
            self._refresh_data_views()
            logger.info(f"Удалено измерение")
    
    def _show_scheme(self):
        """Показать схему сети"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        from .dialogs.scheme_viewer import SchemeViewerDialog
        
        dialog = SchemeViewerDialog(project=self.current_project, parent=self)
        dialog.exec_()
    
    def _refresh_data_views(self):
        """Обновление представлений данных"""
        if not self.current_project:
            return
        
        # Обновление таблиц
        if hasattr(self, 'points_table'):
            points = self.current_project.get_points()
            self.points_table.update_data(points)
        
        if hasattr(self, 'observations_table'):
            observations = self.current_project.get_observations()
            self.observations_table.update_data(observations)
        
        # Обновление плана
        if hasattr(self, 'plan_view'):
            self.plan_view.draw_network(self.current_project)
    
    def _check_tolerances(self):
        """Контроль допусков"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.preprocessing.tolerances import ToleranceChecker
            
            checker = ToleranceChecker()
            observations = self.current_project.get_observations()
            
            if not observations:
                QMessageBox.information(self, "Информация", "В проекте нет измерений")
                return
            
            results = checker.check_all(observations)
            
            # Показать результаты
            violations = [r for r in results if not r['passed']]
            
            if violations:
                msg = f"Обнаружено {len(violations)} нарушений допусков:\n\n"
                for v in violations[:10]:  # Первые 10
                    msg += f"- {v['description']}\n"
                
                if len(violations) > 10:
                    msg += f"\n... и еще {len(violations) - 10}"
                
                QMessageBox.warning(self, "Нарушения допусков", msg)
            else:
                QMessageBox.information(self, "Контроль допусков", "Все измерения в пределах допусков")
            
            logger.info(f"Контроль допусков: {len(violations)} нарушений из {len(results)}")
            
        except Exception as e:
            logger.error(f"Ошибка контроля допусков: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка контроля допусков:\n{str(e)}")
    
    def _apply_corrections(self):
        """Применение редукций"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.preprocessing.module import PreprocessingModule
            
            preprocessor = PreprocessingModule()
            observations = self.current_project.get_observations()
            
            if not observations:
                QMessageBox.information(self, "Информация", "В проекте нет измерений")
                return
            
            # Применение редукций
            corrected_obs = preprocessor.apply_corrections(observations)
            
            # Обновление измерений в проекте
            for obs in corrected_obs:
                self.current_project.update_observation(obs)
            
            self._refresh_data_views()
            
            QMessageBox.information(
                self,
                "Редукции применены",
                f"Редукции применены к {len(corrected_obs)} измерениям"
            )
            
            logger.info(f"Применены редукции к {len(corrected_obs)} измерениям")
            
        except Exception as e:
            logger.error(f"Ошибка применения редукций: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка применения редукций:\n{str(e)}")
    
    def _baarda_analysis(self):
        """Анализ надёжности по Баарду"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.reliability.baarda_method import BaardaMethod
            
            # Проверка наличия результатов уравнивания
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            baarda = BaardaMethod()
            result = baarda.analyze(self.current_project.adjustment_result)
            
            # Показать результаты
            msg = f"Анализ надёжности по Баарду:\n\n"
            msg += f"Внутренняя надёжность: {result.get('internal_reliability', 'N/A')}\n"
            msg += f"Внешняя надёжность: {result.get('external_reliability', 'N/A')}\n"
            msg += f"Обнаружено подозрительных измерений: {len(result.get('suspicious', []))}"
            
            QMessageBox.information(self, "Анализ по Баарду", msg)
            
            logger.info("Выполнен анализ надёжности по Баарду")
            
        except Exception as e:
            logger.error(f"Ошибка анализа по Баарду: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка анализа:\n{str(e)}")
    
    def _gross_error_search(self):
        """Поиск грубых ошибок"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.analysis.gross_errors import GrossErrorAnalyzer
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            # Получение данных из результатов уравнивания
            result = self.current_project.adjustment_result
            A = result.get('A')
            P = result.get('P')
            V = result.get('residuals')
            sigma0 = result.get('sigma0')
            obs_ids = result.get('observations_ids', [])
            
            if A is None or P is None or V is None:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Недостаточно данных для анализа грубых ошибок"
                )
                return
            
            analyzer = GrossErrorAnalyzer(A, P, V, sigma0, obs_ids)
            errors = analyzer.detect_gross_errors()
            
            if errors:
                msg = f"Обнаружено {len(errors)} грубых ошибок:\n\n"
                for err in errors[:10]:
                    msg += f"- {err['description']}\n"
                
                if len(errors) > 10:
                    msg += f"\n... и еще {len(errors) - 10}"
                
                QMessageBox.warning(self, "Грубые ошибки", msg)
            else:
                QMessageBox.information(self, "Поиск грубых ошибок", "Грубых ошибок не обнаружено")
            
            logger.info(f"Поиск грубых ошибок: обнаружено {len(errors)}")
            
        except Exception as e:
            logger.error(f"Ошибка поиска грубых ошибок: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска:\n{str(e)}")
    
    def _error_ellipses(self):
        """Визуализация эллипсов ошибок"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.analysis.visualization import Visualization
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            # Получение данных о пунктах из результатов
            result = self.current_project.adjustment_result
            points = result.get('points', [])
            
            visualizer = Visualization()
            fig = visualizer.plot_error_ellipses(points, show=False)
            
            # Сохранение и показ
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            fig.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            
            # Открыть в системном просмотрщике
            import os
            os.startfile(temp_file.name)
            
            logger.info("Визуализация эллипсов ошибок создана")
            
        except Exception as e:
            logger.error(f"Ошибка визуализации: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка визуализации:\n{str(e)}")
    
    def _heatmaps(self):
        """Визуализация тепловых карт"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.core.analysis.visualization import Visualization
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            # Получение ковариационной матрицы из результатов
            result = self.current_project.adjustment_result
            cov_matrix = result.get('covariance_matrix')
            labels = result.get('point_ids', [])
            
            if cov_matrix is None:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Ковариационная матрица недоступна"
                )
                return
            
            visualizer = Visualization()
            fig = visualizer.plot_correlation_heatmap(cov_matrix, labels=labels, show=False)
            
            # Сохранение и показ
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            fig.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            
            # Открыть в системном просмотрщике
            import os
            os.startfile(temp_file.name)
            
            logger.info("Тепловая карта создана")
            
        except Exception as e:
            logger.error(f"Ошибка визуализации: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка визуализации:\n{str(e)}")
    
    def _coordinate_schedule(self):
        """Формирование ведомости координат"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.io.export.dynadjust_report import ReportGenerator
            
            generator = ReportGenerator()
            points = self.current_project.get_points()
            
            if not points:
                QMessageBox.information(self, "Информация", "В проекте нет пунктов")
                return
            
            # Выбор файла для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить ведомость координат",
                "",
                "PDF файлы (*.pdf);;Excel файлы (*.xlsx);;Все файлы (*)"
            )
            
            if file_path:
                generator.generate_coordinate_schedule(points, file_path)
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Ведомость координат сохранена:\n{file_path}"
                )
                logger.info(f"Ведомость координат сохранена: {file_path}")
            
        except Exception as e:
            logger.error(f"Ошибка формирования ведомости: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка формирования ведомости:\n{str(e)}")
    
    def _correction_schedule(self):
        """Формирование ведомости поправок"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.io.export.dynadjust_report import ReportGenerator
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            generator = ReportGenerator()
            
            # Выбор файла для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить ведомость поправок",
                "",
                "PDF файлы (*.pdf);;Excel файлы (*.xlsx);;Все файлы (*)"
            )
            
            if file_path:
                generator.generate_correction_schedule(
                    self.current_project.adjustment_result,
                    file_path
                )
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Ведомость поправок сохранена:\n{file_path}"
                )
                logger.info(f"Ведомость поправок сохранена: {file_path}")
            
        except Exception as e:
            logger.error(f"Ошибка формирования ведомости: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка формирования ведомости:\n{str(e)}")
    
    def _gost_report(self):
        """Формирование отчёта по ГОСТ"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.io.export.gost_report import GOSTReportGenerator
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            generator = GOSTReportGenerator()
            
            # Выбор файла для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчёт по ГОСТ",
                "",
                "PDF файлы (*.pdf);;DOCX файлы (*.docx);;Все файлы (*)"
            )
            
            if file_path:
                generator.generate_report(
                    self.current_project,
                    self.current_project.adjustment_result,
                    file_path
                )
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Отчёт по ГОСТ 7.32-2017 сохранён:\n{file_path}"
                )
                logger.info(f"Отчёт по ГОСТ сохранён: {file_path}")
            
        except Exception as e:
            logger.error(f"Ошибка формирования отчёта: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка формирования отчёта:\n{str(e)}")
    
    def _compliance_certificate(self):
        """Формирование сертификата соответствия"""
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            from geoadjust.io.export.gost_report import GOSTReportGenerator
            
            if not hasattr(self.current_project, 'adjustment_result'):
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Сначала выполните уравнивание сети"
                )
                return
            
            generator = GOSTReportGenerator()
            
            # Выбор файла для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить сертификат соответствия",
                "",
                "PDF файлы (*.pdf);;Все файлы (*)"
            )
            
            if file_path:
                generator.generate_compliance_certificate(
                    self.current_project,
                    self.current_project.adjustment_result,
                    file_path
                )
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Сертификат соответствия сохранён:\n{file_path}"
                )
                logger.info(f"Сертификат соответствия сохранён: {file_path}")
            
        except Exception as e:
            logger.error(f"Ошибка формирования сертификата: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Ошибка формирования сертификата:\n{str(e)}")
    
    def _show_help(self):
        """Показать справку"""
        QMessageBox.information(self, "Справка", "Справка по программе GeoAdjust Pro")
    
    def _about_program(self):
        """О программе"""
        QMessageBox.about(
            self,
            "О программе",
            "GeoAdjust Pro\nВерсия 1.0\n\nПрограмма для обработки геодезических измерений"
        )
