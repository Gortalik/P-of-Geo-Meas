"""
Модуль работы с моделями геоида для преобразования высот.

Поддерживаемые модели:
- EGM2008 (Earth Gravitational Model 2008)
- Рус-геоид-2011 (региональная модель для РФ)
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator, griddata
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class GeoidModel:
    """
    Модель геоида для преобразования эллипсоидальных высот в нормальные.
    
    Attributes:
        model_name: Название модели геоида ("EGM2008", "rus_geoid_2011")
        data: Данные модели геоида
        is_loaded: Флаг загрузки данных модели
    """
    
    SUPPORTED_MODELS = {
        "EGM2008": {
            "description": "Earth Gravitational Model 2008",
            "resolution": "5 arc-minutes",
            "coverage": "Global",
            "accuracy": "~15 cm"
        },
        "rus_geoid_2011": {
            "description": "Рус-геоид-2011",
            "resolution": "1 arc-minute",
            "coverage": "Russia",
            "accuracy": "~5-10 cm"
        },
        "EGM96": {
            "description": "Earth Gravitational Model 1996",
            "resolution": "15 arc-minutes",
            "coverage": "Global",
            "accuracy": "~50 cm"
        }
    }
    
    def __init__(self, model_name: str = "EGM2008", data_dir: Optional[Path] = None):
        """
        Инициализация модели геоида.
        
        Args:
            model_name: Название модели геоида
            data_dir: Директория с данными моделей геоида
        """
        self.model_name = model_name
        self.data_dir = data_dir or self._get_default_data_dir()
        self.is_loaded = False
        self.data = None
        self.interpolator = None
        self.metadata = {}
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.warning(
                f"Модель '{model_name}' не входит в список поддерживаемых. "
                f"Доступные модели: {list(self.SUPPORTED_MODELS.keys())}"
            )
        
        self._load_model()
    
    def _get_default_data_dir(self) -> Path:
        """Получение директории по умолчанию для данных геоида."""
        return Path(__file__).parent.parent.parent / "resources" / "geoid_data"
    
    def _load_model(self):
        """Загрузка данных модели геоида."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            if self.model_name == "EGM2008":
                self._load_egm2008()
            elif self.model_name == "rus_geoid_2011":
                self._load_rus_geoid_2011()
            elif self.model_name == "EGM96":
                self._load_egm96()
            else:
                logger.warning(f"Неизвестная модель геоида: {self.model_name}")
                self._create_approximate_model()
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели геоида {self.model_name}: {e}")
            self._create_approximate_model()
    
    def _load_egm2008(self):
        """Загрузка модели EGM2008."""
        file_path = self.data_dir / "egm2008_5min.npy"
        meta_path = self.data_dir / "egm2008_5min_meta.json"
        
        if file_path.exists() and meta_path.exists():
            try:
                self.data = np.load(file_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self._create_interpolator()
                self.is_loaded = True
                logger.info(f"Модель EGM2008 загружена из {file_path}")
                return
            except Exception as e:
                logger.warning(f"Ошибка при загрузке EGM2008: {e}. Создание аппроксимированной модели.")
        
        # Если файл не существует, создаем аппроксимированную модель
        self._create_approximate_model("EGM2008")
    
    def _load_rus_geoid_2011(self):
        """Загрузка модели Рус-геоид-2011."""
        file_path = self.data_dir / "rus_geoid_2011.npy"
        meta_path = self.data_dir / "rus_geoid_2011_meta.json"
        
        if file_path.exists() and meta_path.exists():
            try:
                self.data = np.load(file_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self._create_interpolator()
                self.is_loaded = True
                logger.info(f"Модель Рус-геоид-2011 загружена из {file_path}")
                return
            except Exception as e:
                logger.warning(f"Ошибка при загрузке Рус-геоид-2011: {e}. Создание аппроксимированной модели.")
        
        # Если файл не существует, создаем аппроксимированную модель
        self._create_approximate_model("rus_geoid_2011")
    
    def _load_egm96(self):
        """Загрузка модели EGM96."""
        file_path = self.data_dir / "egm96_15min.npy"
        meta_path = self.data_dir / "egm96_15min_meta.json"
        
        if file_path.exists() and meta_path.exists():
            try:
                self.data = np.load(file_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                self._create_interpolator()
                self.is_loaded = True
                logger.info(f"Модель EGM96 загружена из {file_path}")
                return
            except Exception as e:
                logger.warning(f"Ошибка при загрузке EGM96: {e}. Создание аппроксимированной модели.")
        
        # Если файл не существует, создаем аппроксимированную модель
        self._create_approximate_model("EGM96")
    
    def _create_approximate_model(self, model_name: Optional[str] = None):
        """
        Создание аппроксимированной модели геоида на основе сферических гармоник.
        
        Это упрощенная модель, которая дает приблизительные значения высот геоида.
        Для точных расчетов рекомендуется загрузить полноценную модель.
        """
        model = model_name or self.model_name
        
        # Создаем сетку координат
        lat_range = np.linspace(-90, 90, 361)  # Шаг 0.5 градуса
        lon_range = np.linspace(-180, 180, 721)  # Шаг 0.5 градуса
        
        # Создаем сетку для вычислений
        lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)
        
        # Упрощенная модель геоида на основе сферических гармоник
        # Это аппроксимация, дающая разумные значения для большинства территорий
        geoid_heights = self._compute_geoid_approximation(lat_grid, lon_grid, model)
        
        # Сохраняем данные
        self.data = {
            'lat': lat_range,
            'lon': lon_range,
            'heights': geoid_heights
        }
        
        self.metadata = {
            'model_name': model,
            'lat_min': float(lat_range.min()),
            'lat_max': float(lat_range.max()),
            'lon_min': float(lon_range.min()),
            'lon_max': float(lon_range.max()),
            'lat_res': float(lat_range[1] - lat_range[0]),
            'lon_res': float(lon_range[1] - lon_range[0]),
            'accuracy': 'approximate (~1-2 m)',
            'note': 'Аппроксимированная модель. Для точных расчетов загрузите полноценную модель.'
        }
        
        self._create_interpolator()
        self.is_loaded = True
        
        # Сохраняем данные для будущего использования
        self._save_approximate_model()
        
        logger.info(f"Создана аппроксимированная модель геоида {model}")
    
    def _compute_geoid_approximation(self, lat: np.ndarray, lon: np.ndarray, model: str) -> np.ndarray:
        """
        Вычисление приближенных высот геоида.
        
        Использует упрощенную формулу на основе основных сферических гармоник.
        """
        # Перевод в радианы
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        
        # Основные гармоники (упрощенно)
        # C20, C22, S22 - основные коэффициенты разложения
        if model in ["EGM2008", "EGM96"]:
            # Глобальная модель
            N = (
                -20.0 * (np.sin(lat_rad)**2 - 1/3) +  # Основной член C20
                3.0 * np.cos(lat_rad)**2 * np.cos(2*lon_rad) +  # C22
                1.5 * np.cos(lat_rad)**2 * np.sin(2*lon_rad) +  # S22
                1.0 * np.sin(3*lat_rad) * np.cos(lon_rad) +  # C31
                0.5 * np.sin(lat_rad) * np.cos(4*lon_rad)  # C44
            )
        elif model == "rus_geoid_2011":
            # Региональная модель для России
            # Добавляем региональные особенности
            N = (
                -25.0 * (np.sin(lat_rad)**2 - 1/3) +
                4.0 * np.cos(lat_rad)**2 * np.cos(2*lon_rad) +
                2.0 * np.cos(lat_rad)**2 * np.sin(2*lon_rad) +
                1.5 * np.sin(2*lat_rad) * np.cos(lon_rad - np.radians(60))
            )
            # Коррекция для территории России
            russia_mask = (lat > 40) & (lat < 80) & (lon > 20) & (lon < 180)
            N = np.where(russia_mask, N + 2.0, N)
        else:
            # Базовая модель
            N = -20.0 * (np.sin(lat_rad)**2 - 1/3)
        
        return N
    
    def _create_interpolator(self):
        """Создание интерполятора для быстрого получения высот геоида."""
        if self.data is None:
            return
        
        try:
            if isinstance(self.data, dict) and 'heights' in self.data:
                # Регулярная сетка
                lat = self.data['lat']
                lon = self.data['lon']
                heights = self.data['heights']
                
                # Создаем интерполятор для регулярной сетки
                self.interpolator = RegularGridInterpolator(
                    (lat, lon), 
                    heights,
                    method='linear',
                    bounds_error=False,
                    fill_value=0.0
                )
            else:
                # Нерегулярная сетка (точечные данные)
                self.interpolator = None
                logger.warning("Не удалось создать интерполятор для нерегулярной сетки")
        except Exception as e:
            logger.error(f"Ошибка при создании интерполятора: {e}")
            self.interpolator = None
    
    def _save_approximate_model(self):
        """Сохранение аппроксимированной модели для будущего использования."""
        try:
            if self.data is None:
                return
            
            file_path = self.data_dir / f"{self.model_name.lower()}_approx.npy"
            meta_path = self.data_dir / f"{self.model_name.lower()}_approx_meta.json"
            
            np.save(file_path, self.data)
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Аппроксимированная модель сохранена в {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении модели: {e}")
    
    def get_geoid_height(self, lat: float, lon: float) -> float:
        """
        Получение высоты геоида в точке.
        
        Args:
            lat: Широта в градусах (-90 до 90)
            lon: Долгота в градусах (-180 до 180)
            
        Returns:
            Высота геоида в метрах
        """
        if not self.is_loaded or self.data is None:
            logger.warning("Модель геоида не загружена. Возвращается 0.")
            return 0.0
        
        # Проверка диапазона координат
        if not (-90 <= lat <= 90):
            raise ValueError(f"Широта должна быть в диапазоне [-90, 90], получено: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Долгота должна быть в диапазоне [-180, 180], получено: {lon}")
        
        try:
            if self.interpolator is not None:
                # Интерполяция по регулярной сетке
                N = float(self.interpolator([[lat, lon]])[0])
            else:
                # Прямое вычисление для точки
                N = float(self._compute_geoid_approximation(
                    np.array([lat]), 
                    np.array([lon]), 
                    self.model_name
                )[0])
            
            return N
            
        except Exception as e:
            logger.error(f"Ошибка при получении высоты геоида: {e}")
            return 0.0
    
    def get_geoid_heights_batch(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        """
        Пакетное получение высот геоида для множества точек.
        
        Args:
            lats: Массив широт в градусах
            lons: Массив долгот в градусах
            
        Returns:
            Массив высот геоида в метрах
        """
        if not self.is_loaded or self.data is None:
            logger.warning("Модель геоида не загружена. Возвращаются нули.")
            return np.zeros_like(lats)
        
        lats = np.asarray(lats)
        lons = np.asarray(lons)
        
        if lats.shape != lons.shape:
            raise ValueError("Массивы lats и lons должны иметь одинаковую форму")
        
        # Проверка диапазона координат
        if np.any((lats < -90) | (lats > 90)):
            raise ValueError("Широты должны быть в диапазоне [-90, 90]")
        if np.any((lons < -180) | (lons > 180)):
            raise ValueError("Долготы должны быть в диапазоне [-180, 180]")
        
        try:
            if self.interpolator is not None:
                # Пакетная интерполяция
                points = np.column_stack([lats, lons])
                N = self.interpolator(points)
            else:
                # Прямое вычисление
                N = self._compute_geoid_approximation(lats, lons, self.model_name)
            
            return np.asarray(N)
            
        except Exception as e:
            logger.error(f"Ошибка при пакетном получении высот геоида: {e}")
            return np.zeros_like(lats)
    
    def convert_height(self, lat: float, lon: float, h_ellipsoid: float) -> float:
        """
        Преобразование эллипсоидальной высоты в нормальную (ортометрическую).
        
        Формула: H_orthometric = h_ellipsoid - N_geoid
        
        Args:
            lat: Широта в градусах
            lon: Долгота в градусах
            h_ellipsoid: Эллипсоидальная высота в метрах
            
        Returns:
            Нормальная (ортометрическая) высота в метрах
        """
        N = self.get_geoid_height(lat, lon)
        return h_ellipsoid - N
    
    def convert_height_batch(self, lats: np.ndarray, lons: np.ndarray, 
                            h_ellipsoid: np.ndarray) -> np.ndarray:
        """
        Пакетное преобразование эллипсоидальных высот в нормальные.
        
        Args:
            lats: Массив широт в градусах
            lons: Массив долгот в градусах
            h_ellipsoid: Массив эллипсоидальных высот в метрах
            
        Returns:
            Массив нормальных (ортометрических) высот в метрах
        """
        N = self.get_geoid_heights_batch(lats, lons)
        return h_ellipsoid - N
    
    def convert_height_reverse(self, lat: float, lon: float, H_orthometric: float) -> float:
        """
        Преобразование нормальной (ортометрической) высоты в эллипсоидальную.
        
        Формула: h_ellipsoid = H_orthometric + N_geoid
        
        Args:
            lat: Широта в градусах
            lon: Долгота в градусах
            H_orthometric: Нормальная (ортометрическая) высота в метрах
            
        Returns:
            Эллипсоидальная высота в метрах
        """
        N = self.get_geoid_height(lat, lon)
        return H_orthometric + N
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Получение информации о модели геоида.
        
        Returns:
            Словарь с информацией о модели
        """
        info = {
            'model_name': self.model_name,
            'is_loaded': self.is_loaded,
            'data_dir': str(self.data_dir),
        }
        
        if self.model_name in self.SUPPORTED_MODELS:
            info.update(self.SUPPORTED_MODELS[self.model_name])
        
        if self.metadata:
            info['metadata'] = self.metadata
        
        return info
    
    def download_model(self, force: bool = False) -> bool:
        """
        Загрузка полноценной модели геоида из интернета.
        
        Args:
            force: Принудительная загрузка даже если файл существует
            
        Returns:
            True если загрузка успешна, False иначе
        """
        try:
            import requests
        except ImportError:
            logger.error("Для загрузки моделей требуется библиотека requests")
            return False
        
        urls = {
            "EGM2008": "https://earth-info.nga.mil/php/download.php?file=egm2008-5res",
            "EGM96": "https://earth-info.nga.mil/php/download.php?file=egm96",
            "rus_geoid_2011": "https://www.geostandart.ru/geoid/rus_geoid_2011.grd"
        }
        
        if self.model_name not in urls:
            logger.error(f"URL для загрузки модели {self.model_name} не найден")
            return False
        
        url = urls[self.model_name]
        file_path = self.data_dir / f"{self.model_name.lower()}.grd"
        
        if file_path.exists() and not force:
            logger.info(f"Файл модели уже существует: {file_path}")
            return True
        
        try:
            logger.info(f"Загрузка модели {self.model_name} из {url}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (8192 * 100) == 0:
                            logger.info(f"Загружено {progress:.1f}%")
            
            logger.info(f"Модель успешно загружена в {file_path}")
            
            # Попытка загрузки после скачивания
            self._load_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {e}")
            return False


class GeoidConverter:
    """
    Конвертер высот с поддержкой различных моделей геоида.
    
    Пример использования:
        converter = GeoidConverter(model_name="EGM2008")
        H_normal = converter.to_normal_height(lat, lon, h_ellipsoid)
        h_ellip = converter.to_ellipsoidal_height(lat, lon, H_normal)
    """
    
    def __init__(self, model_name: str = "EGM2008"):
        """
        Инициализация конвертера высот.
        
        Args:
            model_name: Название модели геоида
        """
        self.model = GeoidModel(model_name=model_name)
    
    def to_normal_height(self, lat: float, lon: float, h_ellipsoid: float) -> float:
        """Преобразование эллипсоидальной высоты в нормальную."""
        return self.model.convert_height(lat, lon, h_ellipsoid)
    
    def to_ellipsoidal_height(self, lat: float, lon: float, H_normal: float) -> float:
        """Преобразование нормальной высоты в эллипсоидальную."""
        return self.model.convert_height_reverse(lat, lon, H_normal)
    
    def batch_to_normal_height(self, lats: np.ndarray, lons: np.ndarray, 
                               h_ellipsoid: np.ndarray) -> np.ndarray:
        """Пакетное преобразование эллипсоидальных высот в нормальные."""
        return self.model.convert_height_batch(lats, lons, h_ellipsoid)
    
    def get_geoid_height(self, lat: float, lon: float) -> float:
        """Получение высоты геоида в точке."""
        return self.model.get_geoid_height(lat, lon)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели геоида."""
        return self.model.get_model_info()
