from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class NormativeClass:
    name: str
    type: Literal['gnss_network', 'angular_network', 'leveling', 'traverse']
    normative_document: str
    
    # Параметры для анализа угловых измерений
    max_angle_sigma: Optional[float] = None          # СКО угла, секунды
    max_angle_closure_formula: Optional[str] = None  # Формула замыкания горизонта
    
    # Параметры для анализа линейных измерений
    max_distance_sigma_a: Optional[float] = None     # мм
    max_distance_sigma_b: Optional[float] = None     # мм/км
    max_relative_misalignment_formula: Optional[str] = None
    
    # Параметры для анализа нивелирных измерений
    max_leveling_sigma_per_stand: Optional[float] = None  # мм/станц
    max_section_closure_formula: Optional[str] = None    # Формула замыкания секции
    
    # Параметры для анализа точности положения пунктов
    max_point_position_sigma: Optional[float] = None     # мм
    max_height_sigma: Optional[float] = None             # мм


class NormativeClassLibrary:
    """
    Библиотека нормативных классов РФ (ТОЛЬКО ДЛЯ АНАЛИЗА)
    """
    
    def __init__(self):
        self.classes = {}
        self._load_russian_normative_classes()
        
    def _load_russian_normative_classes(self):
        """
        Загрузка полного набора нормативных классов РФ
        """
        # СГС
        self.classes['sgs-1'] = NormativeClass(
            name='СГС-1',
            type='gnss_network',
            normative_document='ГОСТ 32453-2013',
            max_point_position_sigma=5.0,
            max_distance_sigma_a=5.0,
            max_distance_sigma_b=0.5
        )
        
        self.classes['sgs-2'] = NormativeClass(
            name='СГС-2',
            type='gnss_network',
            normative_document='ГОСТ 32453-2013',
            max_point_position_sigma=10.0,
            max_distance_sigma_a=10.0,
            max_distance_sigma_b=1.0
        )
        
        self.classes['sgs-3'] = NormativeClass(
            name='СГС-3',
            type='gnss_network',
            normative_document='ГОСТ 32453-2013',
            max_point_position_sigma=15.0,
            max_distance_sigma_a=15.0,
            max_distance_sigma_b=2.0
        )
        
        # Полигонометрия
        self.classes['poly-1'] = NormativeClass(
            name='1 класс',
            type='angular_network',
            normative_document='СП 11-104-97',
            max_angle_sigma=0.5,
            max_point_position_sigma=3.0
        )
        
        self.classes['poly-2'] = NormativeClass(
            name='2 класс',
            type='angular_network',
            normative_document='СП 11-104-97',
            max_angle_sigma=1.0,
            max_point_position_sigma=5.0
        )
        
        self.classes['poly-3'] = NormativeClass(
            name='3 класс',
            type='angular_network',
            normative_document='СП 11-104-97',
            max_angle_sigma=2.0,
            max_point_position_sigma=10.0
        )
        
        self.classes['poly-4'] = NormativeClass(
            name='4 класс',
            type='angular_network',
            normative_document='СП 11-104-97',
            max_angle_sigma=3.0,
            max_point_position_sigma=15.0
        )
        
        # Нивелирование
        self.classes['level-i'] = NormativeClass(
            name='I класс',
            type='leveling',
            normative_document='Инстр. ГГС',
            max_leveling_sigma_per_stand=0.8,
            max_section_closure_formula='3*sqrt(L)'
        )
        
        self.classes['level-ii'] = NormativeClass(
            name='II класс',
            type='leveling',
            normative_document='Инстр. ГГС',
            max_leveling_sigma_per_stand=1.5,
            max_section_closure_formula='5*sqrt(L)'
        )
        
        self.classes['level-iii'] = NormativeClass(
            name='III класс',
            type='leveling',
            normative_document='Инстр. ГГС',
            max_leveling_sigma_per_stand=3.0,
            max_section_closure_formula='12*sqrt(L)'
        )
        
        self.classes['level-iv'] = NormativeClass(
            name='IV класс',
            type='leveling',
            normative_document='Инстр. ГГС',
            max_leveling_sigma_per_stand=5.0,
            max_section_closure_formula='20*sqrt(L)'
        )
        
        self.classes['level-tech'] = NormativeClass(
            name='Техническое нивелирование',
            type='leveling',
            normative_document='СП 11-104-97',
            max_leveling_sigma_per_stand=10.0,
            max_section_closure_formula='50*sqrt(L)'
        )
        
    def get_class(self, class_id: str) -> Optional[NormativeClass]:
        """
        Получение нормативного класса по ID
        """
        return self.classes.get(class_id)
        
    def list_classes(self) -> list:
        """
        Получение списка всех доступных классов
        """
        return list(self.classes.keys())