from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass
class ColumnDefinition:
    name: str
    type: Literal['point_id', 'x', 'y', 'h', 'direction', 'distance', 'height_diff', 'instrument']
    required: bool = True


@dataclass
class ImportTemplate:
    name: str
    delimiter: Literal['space', 'tab', 'comma', 'semicolon', 'custom']
    skip_lines: int
    has_header: bool
    columns: List[ColumnDefinition]
    coordinate_system: Optional[str] = None
    coordinate_order: Literal['XYH', 'YXH', 'NEH', 'ENH'] = 'XYH'
    custom_delimiter: Optional[str] = None