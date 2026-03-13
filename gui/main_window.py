"""
GeoAdjust Pro - Графический интерфейс
Модуль главного окна приложения
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QMenu,
    QToolBar, QStatusBar, QLabel, QProgressBar, QSplitter,
    QDockWidget, QApplication, QAction, QShortcut
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence

from gui.widgets.ribbon_widget import RibbonWidget
from gui.components.dock_widgets import (
    PointsTableView, ObservationsTableView, TraversesTreeView,
    PlanGraphicsView, LogWidget, PropertiesWidget
)


class InterfaceType(Enum):
    """Тип интерфейса программы"""
    CLASSIC = "classic"  # Меню и тулбары (как в КРЕДО ДАТ 3.x)
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
    
    def __init__(self, config: Optional[MainWindowConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or MainWindowConfig()
        self.current_project = None
        
        # Настройка основного окна
        self._setup_window()
        
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
        self._create_shortcuts()
        
        # Загрузка конфигурации рабочей области
        self._load_workspace_config()
    
    def _setup_window(self):
        """Настройка окна"""
        self.setWindowTitle(self.config.window_title)
        self.setWindowIcon(QIcon("resources/icons/app_icon.ico"))
        
        # Установка размера окна
        self.resize(*self.config.window_size)
        
        # Установка состояния окна
        if self.config.window_state == "maximized":
            self.setWindowState(Qt.WindowMaximized)
        elif self.config.window_state == "fullscreen":
            self.setWindowState(Qt.WindowFullScreen)
    
    def _create_menu_bar(self):
        """Создание главного меню"""
        menu_bar = self.menuBar()
        
        # Меню Файл
        file_menu = menu_bar.addMenu("Файл")
        
        self.action_new_project = QAction("Создать проект", self)
        self.action_new_project.setShortcut("Ctrl+N")
        self.action_new_project.triggered.connect(self._create_project)
        file_menu.addAction(self.action_new_project)
        
        self.action_open_project = QAction("Открыть проект", self)
        self.action_open_project.setShortcut("Ctrl+O")
        self.action_open_project.triggered.connect(self._open_project)
        file_menu.addAction(self.action_open_project)
        
        self.action_save_project = QAction("Сохранить проект", self)
        self.action_save_project.setShortcut("Ctrl+S")
        self.action_save_project.triggered.connect(self._save_project)
        file_menu.addAction(self.action_save_project)
        
        self.action_save_as = QAction("Сохранить как...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self._save_project_as)
        file_menu.addAction(self.action_save_as)
        
        file_menu.addSeparator()
        
        self.action_project_properties = QAction("Свойства проекта", self)
        self.action_project_properties.triggered.connect(self._project_properties)
        file_menu.addAction(self.action_project_properties)
        
        file_menu.addSeparator()
        
        self.action_program_settings = QAction("Параметры программы", self)
        self.action_program_settings.setShortcut("Ctrl+P")
        self.action_program_settings.triggered.connect(self._program_settings)
        file_menu.addAction(self.action_program_settings)
        
        file_menu.addSeparator()
        
        self.action_exit = QAction("Выход", self)
        self.action_exit.setShortcut("Alt+F4")
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)
        
        # Меню Редактирование
        edit_menu = menu_bar.addMenu("Редактирование")
        
        self.action_undo = QAction("Отменить", self)
        self.action_undo.setShortcut("Ctrl+Z")
        edit_menu.addAction(self.action_undo)
        
        self.action_redo = QAction("Повторить", self)
        self.action_redo.setShortcut("Ctrl+Y")
        edit_menu.addAction(self.action_redo)
        
        edit_menu.addSeparator()
        
        self.action_copy = QAction("Копировать", self)
        self.action_copy.setShortcut("Ctrl+C")
        edit_menu.addAction(self.action_copy)
        
        self.action_paste = QAction("Вставить", self)
        self.action_paste.setShortcut("Ctrl+V")
        edit_menu.addAction(self.action_paste)
        
        self.action_delete = QAction("Удалить", self)
        self.action_delete.setShortcut("Delete")
        edit_menu.addAction(self.action_delete)
        
        edit_menu.addSeparator()
        
        self.action_select_all = QAction("Выделить всё", self)
        self.action_select_all.setShortcut("Ctrl+A")
        edit_menu.addAction(self.action_select_all)
        
        # Меню Обработка
        process_menu = menu_bar.addMenu("Обработка")
        
        self.action_check_tolerances = QAction("Контроль допусков", self)
        self.action_check_tolerances.triggered.connect(self._check_tolerances)
        process_menu.addAction(self.action_check_tolerances)
        
        self.action_apply_corrections = QAction("Применение редукций", self)
        self.action_apply_corrections.triggered.connect(self._apply_corrections)
        process_menu.addAction(self.action_apply_corrections)
        
        process_menu.addSeparator()
        
        self.action_adjust_classic = QAction("Классический МНК", self)
        self.action_adjust_classic.triggered.connect(self._adjust_classic)
        process_menu.addAction(self.action_adjust_classic)
        
        self.action_adjust_robust = QAction("Робастное уравнивание", self)
        self.action_adjust_robust.triggered.connect(self._adjust_robust)
        process_menu.addAction(self.action_adjust_robust)
        
        # Меню Отчёты
        report_menu = menu_bar.addMenu("Отчёты")
        
        self.action_coordinate_schedule = QAction("Ведомость координат", self)
        self.action_coordinate_schedule.triggered.connect(self._coordinate_schedule)
        report_menu.addAction(self.action_coordinate_schedule)
        
        self.action_correction_schedule = QAction("Ведомость поправок", self)
        self.action_correction_schedule.triggered.connect(self._correction_schedule)
        report_menu.addAction(self.action_correction_schedule)
        
        report_menu.addSeparator()
        
        self.action_gost_report = QAction("Отчёт по ГОСТ 7.32-2017", self)
        self.action_gost_report.triggered.connect(self._gost_report)
        report_menu.addAction(self.action_gost_report)
        
        self.action_compliance_certificate = QAction("Сертификат соответствия", self)
        self.action_compliance_certificate.triggered.connect(self._compliance_certificate)
        report_menu.addAction(self.action_compliance_certificate)
        
        # Меню Справка
        help_menu = menu_bar.addMenu("Справка")
        
        self.action_help = QAction("Содержание", self)
        self.action_help.setShortcut("F1")
        self.action_help.triggered.connect(self._show_help)
        help_menu.addAction(self.action_help)
        
        help_menu.addSeparator()
        
        self.action_about = QAction("О программе", self)
        self.action_about.triggered.connect(self._about_program)
        help_menu.addAction(self.action_about)
    
    def _create_ribbon_interface(self):
        """Создание ленточного интерфейса"""
        self.ribbon = RibbonWidget(self)
        
        # Вкладка "Главная"
        home_tab = self.ribbon.add_tab("Главная")
        home_tab.add_group("Проект", [
            ("Новый проект", "new_project", "Ctrl+N"),
            ("Открыть", "open_project", "Ctrl+O"),
            ("Сохранить", "save_project", "Ctrl+S"),
        ])
        home_tab.add_group("Буфер обмена", [
            ("Копировать", "copy", "Ctrl+C"),
            ("Вставить", "paste", "Ctrl+V"),
            ("Удалить", "delete", "Delete"),
        ])
        
        # Вкладка "Данные"
        data_tab = self.ribbon.add_tab("Данные")
        data_tab.add_group("Импорт", [
            ("Импорт из прибора", "import_from_instrument"),
            ("Импорт файла", "import_file"),
            ("Импорт из КРЕДО", "import_from_credo"),
        ])
        data_tab.add_group("Экспорт", [
            ("Экспорт в файл", "export_file"),
            ("Экспорт в КРЕДО", "export_to_credo"),
            ("Экспорт в DXF", "export_to_dxf"),
        ])
        
        # Вкладка "Обработка"
        process_tab = self.ribbon.add_tab("Обработка")
        process_tab.add_group("Предобработка", [
            ("Контроль допусков", "check_tolerances"),
            ("Применение редукций", "apply_corrections"),
            ("Фильтрация измерений", "filter_observations"),
        ])
        process_tab.add_group("Уравнивание", [
            ("Классический МНК", "adjust_classic"),
            ("Робастное уравнивание", "adjust_robust"),
            ("Поэтапное уравнивание", "adjust_step_by_step"),
        ])
        
        # Вкладка "Анализ"
        analysis_tab = self.ribbon.add_tab("Анализ")
        analysis_tab.add_group("Надёжность", [
            ("Анализ по Баарду", "baarda_analysis"),
            ("Поиск грубых ошибок", "gross_error_search"),
            ("Анализ чувствительности", "sensitivity_analysis"),
        ])
        analysis_tab.add_group("Визуализация", [
            ("Эллипсы ошибок", "error_ellipses"),
            ("Тепловые карты", "heatmaps"),
            ("Графики невязок", "residual_plots"),
        ])
        
        # Вкладка "Отчёты"
        report_tab = self.ribbon.add_tab("Отчёты")
        report_tab.add_group("Ведомости", [
            ("Ведомость координат", "coordinate_schedule"),
            ("Ведомость поправок", "correction_schedule"),
            ("Ведомость длин линий", "distance_schedule"),
        ])
        report_tab.add_group("ГОСТ", [
            ("Отчёт по ГОСТ 7.32-2017", "gost_report"),
            ("Сертификат соответствия", "compliance_certificate"),
            ("Технический отчёт", "technical_report"),
        ])
        
        # Панель быстрого доступа
        quick_access = self.ribbon.add_quick_access_toolbar()
        quick_access.add_action("Сохранить", "save_project")
        quick_access.add_action("Отменить", "undo")
        quick_access.add_action("Повторить", "redo")
        
        self.addToolBar(Qt.TopToolBarArea, self.ribbon)
    
    def _create_classic_toolbars(self):
        """Создание классических панелей инструментов"""
        # Панель стандартных операций
        standard_toolbar = QToolBar("Стандартная", self)
        standard_toolbar.setIconSize(QSize(24, 24))
        standard_toolbar.addAction(self.action_new_project)
        standard_toolbar.addAction(self.action_open_project)
        standard_toolbar.addAction(self.action_save_project)
        standard_toolbar.addSeparator()
        standard_toolbar.addAction(self.action_undo)
        standard_toolbar.addAction(self.action_redo)
        standard_toolbar.addSeparator()
        standard_toolbar.addAction(self.action_print)
        self.addToolBar(Qt.TopToolBarArea, standard_toolbar)
        
        # Панель редактирования
        edit_toolbar = QToolBar("Редактирование", self)
        edit_toolbar.setIconSize(QSize(24, 24))
        edit_toolbar.addAction(self.action_copy)
        edit_toolbar.addAction(self.action_paste)
        edit_toolbar.addAction(self.action_delete)
        edit_toolbar.addSeparator()
        edit_toolbar.addAction(self.action_select_all)
        self.addToolBar(Qt.TopToolBarArea, edit_toolbar)
        
        # Панель обработки
        process_toolbar = QToolBar("Обработка", self)
        process_toolbar.setIconSize(QSize(24, 24))
        process_toolbar.addAction(self.action_check_tolerances)
        process_toolbar.addAction(self.action_apply_corrections)
        process_toolbar.addSeparator()
        process_toolbar.addAction(self.action_adjust_classic)
        process_toolbar.addAction(self.action_adjust_robust)
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
        
        # Разделитель
        status_bar.addPermanentWidget(QLabel(" | "))
        
        # Прогресс выполнения операций
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        
        # Разделитель
        status_bar.addPermanentWidget(QLabel(" | "))
        
        # Информация о координатах (для графического окна)
        self.coords_label = QLabel("")
        status_bar.addPermanentWidget(self.coords_label)
    
    def _create_dock_widgets(self):
        """Создание док-виджетов"""
        
        # Окно "Пункты ПВО"
        self.points_dock = QDockWidget("Пункты ПВО", self)
        self.points_dock.setObjectName("points_dock")
        self.points_table = PointsTableView()
        self.points_dock.setWidget(self.points_table)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.points_dock)
        
        # Окно "Измерения"
        self.observations_dock = QDockWidget("Измерения", self)
        self.observations_dock.setObjectName("observations_dock")
        self.observations_table = ObservationsTableView()
        self.observations_dock.setWidget(self.observations_table)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.observations_dock)
        
        # Окно "Ходы и секции"
        self.traverses_dock = QDockWidget("Ходы и секции", self)
        self.traverses_dock.setObjectName("traverses_dock")
        self.traverses_tree = TraversesTreeView()
        self.traverses_dock.setWidget(self.traverses_tree)
        self.addDockWidget(Qt.RightDockWidgetArea, self.traverses_dock)
        
        # Окно "План"
        self.plan_dock = QDockWidget("План", self)
        self.plan_dock.setObjectName("plan_dock")
        self.plan_view = PlanGraphicsView()
        self.plan_dock.setWidget(self.plan_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.plan_dock)
        
        # Окно "Журнал"
        self.log_dock = QDockWidget("Журнал", self)
        self.log_dock.setObjectName("log_dock")
        self.log_widget = LogWidget()
        self.log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        
        # Окно "Свойства"
        self.properties_dock = QDockWidget("Свойства", self)
        self.properties_dock.setObjectName("properties_dock")
        self.properties_widget = PropertiesWidget()
        self.properties_dock.setWidget(self.properties_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
    
    def _create_main_area(self):
        """Создание центральной области"""
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Левая панель - таблицы данных
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.points_dock)
        left_layout.addWidget(self.observations_dock)
        
        # Правая панель - графика и свойства
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.plan_dock)
        right_layout.addWidget(self.traverses_dock)
        right_layout.addWidget(self.properties_dock)
        
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(right_container)
        
        # Установка начальных размеров
        self.main_splitter.setSizes([400, 800])
    
    def _create_shortcuts(self):
        """Создание горячих клавиш"""
        # F5 - обновление
        QShortcut(QKeySequence("F5"), self).activated.connect(self._refresh_view)
        
        # Ctrl+Plus - увеличить масштаб
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._zoom_in)
        
        # Ctrl+Minus - уменьшить масштаб
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoom_out)
        
        # F9 - показать/скрыть эллипсы ошибок
        QShortcut(QKeySequence("F9"), self).activated.connect(self._toggle_error_ellipses)
    
    def _load_workspace_config(self):
        """Загрузка конфигурации рабочей области"""
        from gui.workspace_manager import WorkspaceManager
        
        self.workspace_manager = WorkspaceManager(self)
        self.workspace_manager.apply_configuration("measurements_traverses")
    
    # Обработчики действий меню
    def _create_project(self):
        """Создание нового проекта"""
        from gui.dialogs.new_project_dialog import NewProjectDialog
        
        dialog = NewProjectDialog(self)
        if dialog.exec_():
            project_data = dialog.get_project_data()
            # Логика создания проекта
            pass
    
    def _open_project(self):
        """Открытие проекта"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть проект",
            "",
            "Проекты GeoAdjust (*.gad);;Все файлы (*)"
        )
        
        if file_path:
            # Логика открытия проекта
            pass
    
    def _save_project(self):
        """Сохранение проекта"""
        # Логика сохранения проекта
        pass
    
    def _save_project_as(self):
        """Сохранение проекта как"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить проект как",
            "",
            "Проекты GeoAdjust (*.gad);;Все файлы (*)"
        )
        
        if file_path:
            # Логика сохранения проекта в новое место
            pass
    
    def _project_properties(self):
        """Свойства проекта"""
        from gui.dialogs.project_properties import ProjectPropertiesDialog
        
        if self.current_project:
            dialog = ProjectPropertiesDialog(self.current_project, self)
            dialog.exec_()
    
    def _program_settings(self):
        """Параметры программы"""
        from gui.dialogs.program_settings import ProgramSettingsDialog
        
        dialog = ProgramSettingsDialog(self)
        dialog.exec_()
    
    def _check_tolerances(self):
        """Контроль допусков"""
        pass
    
    def _apply_corrections(self):
        """Применение редукций"""
        pass
    
    def _adjust_classic(self):
        """Классическое уравнивание МНК"""
        pass
    
    def _adjust_robust(self):
        """Робастное уранивание"""
        pass
    
    def _coordinate_schedule(self):
        """Ведомость координат"""
        pass
    
    def _correction_schedule(self):
        """Ведомость поправок"""
        pass
    
    def _gost_report(self):
        """Отчёт по ГОСТ"""
        pass
    
    def _compliance_certificate(self):
        """Сертификат соответствия"""
        pass
    
    def _show_help(self):
        """Показать справку"""
        pass
    
    def _about_program(self):
        """О программе"""
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "О программе GeoAdjust Pro",
            "GeoAdjust Pro v1.0\n\n"
            "Программа для уравнивания геодезических сетей.\n\n"
            "© 2024 Все права защищены."
        )
    
    def _refresh_view(self):
        """Обновление вида"""
        pass
    
    def _zoom_in(self):
        """Увеличить масштаб"""
        if hasattr(self, 'plan_view'):
            self.plan_view.scale(1.2, 1.2)
    
    def _zoom_out(self):
        """Уменьшить масштаб"""
        if hasattr(self, 'plan_view'):
            self.plan_view.scale(0.8, 0.8)
    
    def _toggle_error_ellipses(self):
        """Показать/скрыть эллипсы ошибок"""
        pass
