from dataclasses import dataclass


@dataclass
class Instrument:
    """
    Структура прибора (полностью настраиваемая)
    """
    # Угловые измерения
    angular_accuracy: float = 1.0          # СКО угла, сек (диапазон 0.1–60.0)
    angular_repeatability: float = 0.5
    circle_division: float = 1.0
    compensator_accuracy: float = 0.3
    
    # Линейные измерения
    distance_accuracy_a: float = 1.0       # мм (диапазон 0.1–100.0)
    distance_accuracy_b: float = 1.0       # мм/км (диапазон 0.0–10.0)
    distance_min: float = 1.5
    distance_max: float = 1000.0
    
    # Нивелирные измерения
    leveling_accuracy: float = 0.8         # мм/станц (диапазон 0.1–10.0)
    max_sight_distance: float = 100.0      # м (диапазон 10.0–150.0)
    
    # Ошибки установки
    centering_error: float = 2.0           # мм (диапазон 0.1–50.0)
    target_centering_error: float = 2.0
    height_measurement_error: float = 1.0  # мм (диапазон 0.1–10.0)
    
    # Атмосферные условия
    temperature_default: float = 15.0      # °C (диапазон -50.0–+50.0)
    pressure_default: float = 1013.25      # гПа (диапазон 700.0–1100.0)
    refraction_coefficient_default: float = 0.14  # (диапазон 0.08–0.25)
    
    def calculate_angle_sigma(self) -> float:
        """
        Расчёт СКО углового измерения
        """
        return self.angular_accuracy
    
    def calculate_distance_sigma(self, distance_km: float, temperature: float = None, 
                                pressure: float = None) -> float:
        """
        Расчёт СКО линейного измерения с учётом атмосферных условий
        
        Формула: σ = √(a² + (b·D)²) · k_atm
        где k_atm - поправочный коэффициент за атмосферные условия
        
        Параметры:
        - distance_km: расстояние в километрах
        - temperature: температура воздуха (°C)
        - pressure: атмосферное давление (гПа)
        
        Возвращает:
        - sigma: СКО линейного измерения в мм
        """
        if temperature is None:
            temperature = self.temperature_default
        if pressure is None:
            pressure = self.pressure_default
            
        # Базовое СКО без учёта атмосферы
        sigma_squared = (self.distance_accuracy_a)**2 + \
                       (self.distance_accuracy_b * distance_km)**2
        
        # Поправка за атмосферные условия (упрощённая модель)
        # Стандартные условия
        t0 = self.temperature_default
        p0 = self.pressure_default
        
        # Отклонение от стандартных условий
        delta_t = temperature - t0
        delta_p = pressure - p0
        
        # Коэффициент поправки (эмпирическая формула)
        # Увеличение СКО при отклонении от стандартных условий
        k_atm = 1.0 + 0.001 * (abs(delta_t) / 10.0 + abs(delta_p) / 50.0)
        
        sigma_squared *= k_atm**2
        
        return sigma_squared**0.5
    
    def calculate_leveling_sigma(self, num_stands: int) -> float:
        """
        Расчёт СКО нивелирного измерения
        """
        return self.leveling_accuracy * (num_stands**0.5)


class InstrumentLibrary:
    """
    Библиотека приборов
    """
    
    def __init__(self):
        self.instruments = {}
        self._load_default_instruments()
        
    def _load_default_instruments(self):
        """
        Загрузка стандартных приборов
        """
        # Leica TS16
        self.instruments['leica_ts16'] = Instrument(
            angular_accuracy=1.0,
            distance_accuracy_a=1.0,
            distance_accuracy_b=1.0,
            leveling_accuracy=0.8
        )
        
        # Sokkia SET1M
        self.instruments['sokkia_set1m'] = Instrument(
            angular_accuracy=1.0,
            distance_accuracy_a=1.5,
            distance_accuracy_b=2.0,
            leveling_accuracy=1.0
        )
        
        # Trimble S10
        self.instruments['trimble_s10'] = Instrument(
            angular_accuracy=0.5,
            distance_accuracy_a=1.0,
            distance_accuracy_b=1.0,
            leveling_accuracy=0.7
        )
        
        # Nikon Nivo
        self.instruments['nikon_nivo'] = Instrument(
            angular_accuracy=2.0,
            distance_accuracy_a=2.0,
            distance_accuracy_b=2.0,
            leveling_accuracy=1.5
        )
        
        # 3ТА5 (УОМЗ)
        self.instruments['3ta5'] = Instrument(
            angular_accuracy=5.0,
            distance_accuracy_a=5.0,
            distance_accuracy_b=5.0,
            leveling_accuracy=3.0
        )
        
        # FOIF KTS-440
        self.instruments['foif_kts440'] = Instrument(
            angular_accuracy=2.0,
            distance_accuracy_a=2.0,
            distance_accuracy_b=2.0,
            leveling_accuracy=2.0
        )
    
    def get_instrument(self, instrument_name: str) -> Instrument:
        """
        Получение параметров прибора по имени
        """
        return self.instruments.get(instrument_name.lower(), 
                                  self.instruments.get('leica_ts16'))  # по умолчанию