"""
GeoAdjust Pro - Модели данных для таблиц
"""

from typing import List, Any, Optional, Dict
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, pyqtSignal
from PyQt5.QtGui import QColor


class PointsTableModel(QAbstractTableModel):
    """Модель данных для таблицы пунктов"""
    
    HEADERS = ["№", "Имя", "Тип", "X", "Y", "σx", "σy"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
    
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._data)
    
    def columnCount(self, parent: QModelIndex = None) -> int:
        return len(self.HEADERS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data):
            return QVariant()
        
        point = self._data[row]
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0:
                return row + 1
            elif col == 1:
                return point.get('name', '')
            elif col == 2:
                return point.get('type', 'новый')
            elif col == 3:
                x = point.get('x')
                return f"{x:.4f}" if x is not None else ""
            elif col == 4:
                y = point.get('y')
                return f"{y:.4f}" if y is not None else ""
            elif col == 5:
                sx = point.get('sigma_x')
                return f"{sx:.4f}" if sx is not None else ""
            elif col == 6:
                sy = point.get('sigma_y')
                return f"{sy:.4f}" if sy is not None else ""
        
        elif role == Qt.BackgroundRole:
            # Чередование цвета строк
            if row % 2 == 0:
                return QColor(255, 255, 255)
            else:
                return QColor(245, 245, 245)
        
        elif role == Qt.TextAlignmentRole:
            if col in [3, 4, 5, 6]:  # Числовые колонки
                return Qt.AlignRight | Qt.AlignVCenter
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        # Разрешить редактирование имени и типа
        if index.column() in [1, 2]:
            flags |= Qt.ItemIsEditable
        
        return flags
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data):
            return False
        
        point = self._data[row]
        
        if col == 1:
            point['name'] = str(value)
        elif col == 2:
            point['type'] = str(value)
        
        self.dataChanged.emit(index, index, [role])
        return True
    
    def add_point(self, point_data: Optional[Dict] = None):
        """Добавление пункта"""
        if point_data is None:
            point_data = {
                'name': f"P{len(self._data) + 1}",
                'type': 'новый',
                'x': None,
                'y': None,
                'sigma_x': None,
                'sigma_y': None
            }
        
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(point_data)
        self.endInsertRows()
    
    def remove_point(self, row: int):
        """Удаление пункта"""
        if 0 <= row < len(self._data):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data[row]
            self.endRemoveRows()
    
    def load_points(self, points: List[Any]):
        """Загрузка списка пунктов"""
        self.beginResetModel()
        self._data = []
        
        for point in points:
            if hasattr(point, '__dict__'):
                self._data.append({
                    'name': getattr(point, 'name', ''),
                    'type': getattr(point, 'type', 'новый'),
                    'x': getattr(point, 'x', None),
                    'y': getattr(point, 'y', None),
                    'sigma_x': getattr(point, 'sigma_x', None),
                    'sigma_y': getattr(point, 'sigma_y', None)
                })
            elif isinstance(point, dict):
                self._data.append(point)
        
        self.endResetModel()
    
    def get_points(self) -> List[Dict]:
        """Получение списка пунктов"""
        return self._data.copy()
    
    def export_to_file(self, file_path: str):
        """Экспорт в файл"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            
            for i, point in enumerate(self._data):
                writer.writerow([
                    i + 1,
                    point.get('name', ''),
                    point.get('type', ''),
                    point.get('x', ''),
                    point.get('y', ''),
                    point.get('sigma_x', ''),
                    point.get('sigma_y', '')
                ])
    
    def copy_to_clipboard(self, indexes: List[QModelIndex]):
        """Копирование в буфер обмена"""
        from PyQt5.QtWidgets import QApplication
        
        if not indexes:
            return
        
        rows = sorted(set(idx.row() for idx in indexes))
        text = ""
        
        for row in rows:
            row_data = []
            for col in range(self.columnCount()):
                value = self.data(self.index(row, col), Qt.DisplayRole)
                row_data.append(str(value) if value is not None else "")
            text += "\t".join(row_data) + "\n"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)


class ObservationsTableModel(QAbstractTableModel):
    """Модель данных для таблицы измерений"""
    
    HEADERS = ["№", "Тип", "От", "До", "Значение", "Вес", "Поправка"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
    
    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self._data)
    
    def columnCount(self, parent: QModelIndex = None) -> int:
        return len(self.HEADERS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data):
            return QVariant()
        
        obs = self._data[row]
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 0:
                return row + 1
            elif col == 1:
                return obs.get('type', '')
            elif col == 2:
                return obs.get('from_point', '')
            elif col == 3:
                return obs.get('to_point', '')
            elif col == 4:
                value = obs.get('value')
                return f"{value:.4f}" if value is not None else ""
            elif col == 5:
                weight = obs.get('weight')
                return f"{weight:.3f}" if weight is not None else ""
            elif col == 6:
                correction = obs.get('correction')
                return f"{correction:.4f}" if correction is not None else ""
        
        elif role == Qt.BackgroundRole:
            if row % 2 == 0:
                return QColor(255, 255, 255)
            else:
                return QColor(245, 245, 245)
        
        elif role == Qt.TextAlignmentRole:
            if col in [4, 5, 6]:
                return Qt.AlignRight | Qt.AlignVCenter
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()
    
    def add_observation(self, obs_data: Optional[Dict] = None):
        """Добавление измерения"""
        if obs_data is None:
            obs_data = {
                'type': 'угол',
                'from_point': '',
                'to_point': '',
                'value': None,
                'weight': 1.0,
                'correction': None
            }
        
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(obs_data)
        self.endInsertRows()
    
    def remove_observation(self, row: int):
        """Удаление измерения"""
        if 0 <= row < len(self._data):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data[row]
            self.endRemoveRows()
    
    def load_observations(self, observations: List[Any]):
        """Загрузка списка измерений"""
        self.beginResetModel()
        self._data = []
        
        for obs in observations:
            if hasattr(obs, '__dict__'):
                self._data.append({
                    'type': getattr(obs, 'type', ''),
                    'from_point': getattr(obs, 'from_point', ''),
                    'to_point': getattr(obs, 'to_point', ''),
                    'value': getattr(obs, 'value', None),
                    'weight': getattr(obs, 'weight', 1.0),
                    'correction': getattr(obs, 'correction', None)
                })
            elif isinstance(obs, dict):
                self._data.append(obs)
        
        self.endResetModel()
    
    def export_to_file(self, file_path: str):
        """Экспорт в файл"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            
            for i, obs in enumerate(self._data):
                writer.writerow([
                    i + 1,
                    obs.get('type', ''),
                    obs.get('from_point', ''),
                    obs.get('to_point', ''),
                    obs.get('value', ''),
                    obs.get('weight', ''),
                    obs.get('correction', '')
                ])
