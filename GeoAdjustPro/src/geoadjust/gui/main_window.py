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
        self.setWindowIcon(QIcon("resources/icons/app_icon.ico"))
        
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
        edit_toolbar.addAction("Отменить", None)
        edit_toolbar.addAction("Повторить", None)
        edit_toolbar.addAction("Копировать", None)
        edit_toolbar.addAction("Вставить", None)
        self.addToolBar(Qt.TopToolBarArea, edit_toolbar)
        
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
        
        # Окно "План"
        self.plan_dock = QDockWidget("План", self)
        self.plan_view = PlanGraphicsView()
        self.plan_dock.setWidget(self.plan_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.plan_dock)
        
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
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Левая панель - таблицы данных
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.points_dock)
        left_layout.addWidget(self.observations_dock)
        
        # Правая панель - графика и свойства
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.plan_dock)
        right_layout.addWidget(self.properties_dock)
        
        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(right_panel)
        
        # Установка начальных размеров
        self.main_splitter.setSizes([400, 800])
    
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
            project = project_manager.create_project(
                project_data['name'],
                Path(project_data['path'])
            )
            self.current_project = project
            
            # Обновление интерфейса
            self.project_label.setText(f"Проект: {project_data['name']}")
            self.statusBar().showMessage(f"Проект '{project_data['name']}' создан", 3000)
            
            logger.info(f"Проект создан: {project_data['name']}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать проект:\n{str(e)}")
            logger.error(f"Ошибка при создании проекта: {e}")
    
    def _open_project(self):
        """Открытие существующего проекта"""
        logger.info("Открытие проекта")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть проект",
            "",
            "GeoAdjust Project (*.gad);;Все файлы (*)"
        )
        
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
        logger.info("Запуск классического МНК уравнивания")
        
        if not self.current_project:
            QMessageBox.warning(self, "Предупреждение", "Нет открытого проекта")
            return
        
        try:
            self.mode_label.setText("Режим: уравнивание")
            self.statusBar().showMessage("Выполняется уравнивание...", 0)
            self.progress_bar.setVisible(True)
            
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
            
            # Запуск уравнивания в отдельном потоке
            from geoadjust.gui.processing.processing_thread import ProcessingThread
            self.processing_thread = ProcessingThread(self.processing_integration)
            self.processing_thread.finished.connect(self._on_adjustment_finished)
            self.processing_thread.error_occurred.connect(self._on_adjustment_error)
            self.processing_thread.progress_updated.connect(self._on_progress_updated)
            self.processing_thread.start()
            
        except Exception as e:
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
            self.progress_bar.setRange(0, 0)
            
            from geoadjust.core.adjustment.robust_methods import RobustAdjustment
            
            # Получение данных из проекта
            observations = self.current_project.get_observations()
            control_points = self.current_project.get_points()
            
            if not observations:
                QMessageBox.warning(self, "Предупреждение", "В проекте нет измерений")
                self._reset_ui_state()
                return
            
            # Робастное уравнивание
            robust = RobustAdjustment()
            result = robust.adjust(observations, control_points)
            
            # Сохранение результатов в проект
            self.current_project.save_adjustment_result(result)
            
            # Обновление интерфейса
            self._update_ui_with_results(result)
            
            sigma0 = result.get('sigma0', 0)
            self.statusBar().showMessage(f"Робастное уравнивание выполнено: μ₀ = {sigma0:.6f}", 5000)
            self._reset_ui_state()
            
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
    
    def _import_from_instrument(self):
        """Импорт данных из прибора"""
        logger.info("Импорт данных из прибора")
    
    def _import_file(self):
        """Импорт данных из файла"""
        logger.info("Импорт данных из файла")
    
    def _export_file(self):
        """Экспорт данных в файл"""
        logger.info("Экспорт данных в файл")
    
    def _export_to_credo(self):
        """Экспорт данных в КРЕДО"""
        logger.info("Экспорт данных в КРЕДО")
    
    def _check_tolerances(self):
        """Контроль допусков"""
        logger.info("Контроль допусков")
    
    def _apply_corrections(self):
        """Применение редукций"""
        logger.info("Применение редукций")
    
    def _baarda_analysis(self):
        """Анализ надёжности по Баарду"""
        logger.info("Анализ надёжности по Баарду")
    
    def _gross_error_search(self):
        """Поиск грубых ошибок"""
        logger.info("Поиск грубых ошибок")
    
    def _error_ellipses(self):
        """Визуализация эллипсов ошибок"""
        logger.info("Визуализация эллипсов ошибок")
    
    def _heatmaps(self):
        """Визуализация тепловых карт"""
        logger.info("Визуализация тепловых карт")
    
    def _coordinate_schedule(self):
        """Формирование ведомости координат"""
        logger.info("Формирование ведомости координат")
    
    def _correction_schedule(self):
        """Формирование ведомости поправок"""
        logger.info("Формирование ведомости поправок")
    
    def _gost_report(self):
        """Формирование отчёта по ГОСТ"""
        logger.info("Формирование отчёта по ГОСТ 7.32-2017")
    
    def _compliance_certificate(self):
        """Формирование сертификата соответствия"""
        logger.info("Формирование сертификата соответствия")
    
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
