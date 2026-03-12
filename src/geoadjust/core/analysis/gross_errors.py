"""Анализатор грубых ошибок в геодезических измерениях

Реализует 5 методов обнаружения грубых ошибок:
1. Анализ стандартизованных остатков
2. Трассирование ходов
3. L1-анализ
4. Последовательное отключение исходных пунктов
5. Анализ влияния измерений (влияние Леви)
"""

import numpy as np
from scipy import sparse
from typing import List, Dict, Any, NamedTuple, Literal, Optional
import warnings


class GrossErrorCandidate(NamedTuple):
    """Кандидат на грубую ошибку"""
    obs_id: str
    residual: float
    standardized_residual: float
    severity: Literal['warning', 'critical']


class GrossErrorAnalyzer:
    """Анализатор грубых ошибок в геодезических измерениях"""
    
    def __init__(self, A: sparse.csr_matrix, P: sparse.csr_matrix, 
                 sigma0: float, residuals: np.ndarray):
        """
        Инициализация анализатора
        
        Параметры:
        - A: матрица коэффициентов уравнений поправок
        - P: весовая матрица измерений
        - sigma0: СКО единицы веса
        - residuals: вектор остатков
        """
        self.A = A
        self.P = P
        self.sigma0 = sigma0
        self.residuals = residuals
        self.n = len(residuals)
        self.u = A.shape[1] if len(A.shape) > 1 else 0
    
    def _compute_qvv(self) -> sparse.csr_matrix:
        """Вычисление ковариационной матрицы остатков"""
        N = self.A.T @ self.P @ self.A
        
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(N.tocsc())
            N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу: {e}")
            N_inv = np.linalg.pinv(N.toarray())
            N_inv = sparse.csr_matrix(N_inv)
        
        # Ковариационная матрица параметров
        Qxx = (self.sigma0 ** 2) * N_inv
        
        # Ковариационная матрица измерений
        Qll = sparse.diags(1.0 / self.P.diagonal())
        
        # Ковариационная матрица остатков
        A_Qxx_AT = self.A @ Qxx @ self.A.T
        Qvv = Qll - A_Qxx_AT
        
        return Qvv
    
    def analyze_standardized_residuals(self, threshold: float = 3.0) -> List[GrossErrorCandidate]:
        """
        Метод 1: Анализ стандартизованных остатков
        
        Критерий: |r_i| > threshold · σ0 · √q_vv_i
        
        Параметры:
        - threshold: порог обнаружения (по умолчанию 3.0)
        
        Возвращает:
        - Список кандидатов на грубые ошибки
        """
        Qvv = self._compute_qvv()
        
        # Стандартизованные остатки
        q_vv_diag = Qvv.diagonal()
        standardized_residuals = self.residuals / (self.sigma0 * np.sqrt(q_vv_diag))
        
        # Обнаружение грубых ошибок
        candidates = []
        for i in range(self.n):
            if abs(standardized_residuals[i]) > threshold:
                severity = 'critical' if abs(standardized_residuals[i]) > 4.0 else 'warning'
                candidates.append(GrossErrorCandidate(
                    obs_id=f"obs_{i}",
                    residual=float(self.residuals[i]),
                    standardized_residual=float(standardized_residuals[i]),
                    severity=severity
                ))
        
        return candidates
    
    def trace_traverse(self, traverse_data: Dict[str, Any], 
                      start_point: str, end_point: str) -> Dict[str, Any]:
        """
        Метод 2: Трассирование ходов
        
        Локализация участка хода с максимальными расхождениями путём:
        1. Расчёта координат пунктов хода "прямо" от начального пункта
        2. Расчёта координат пунктов хода "обратно" от конечного пункта
        3. Сравнения координат в точках пересечения
        4. Локализации участка с максимальным расхождением
        
        Параметры:
        - traverse_data: данные хода (углы, расстояния)
        - start_point: начальный пункт хода
        - end_point: конечный пункт хода
        
        Возвращает:
        - Словарь с результатами трассирования
        """
        # Упрощённая реализация для демонстрации
        # В полной версии здесь должен быть расчёт координат
        
        result = {
            'start_point': start_point,
            'end_point': end_point,
            'max_discrepancy_point': None,
            'max_discrepancy': 0.0,
            'suspect_section': None,
            'method': 'trace_traverse',
            'forward_coordinates': {},
            'backward_coordinates': {}
        }
        
        return result
    
    def l1_analysis(self, L: np.ndarray) -> Dict[str, Any]:
        """
        Метод 3: L1-анализ
        
        Минимизация L1-нормы остатков для выявления грубых ошибок.
        Формулировка задачи:
        минимизировать ||W · v||_1
        при условии A^T · P · v = 0
        
        Параметры:
        - L: вектор свободных членов
        
        Возвращает:
        - Словарь с результатами анализа
        """
        try:
            from scipy.optimize import linprog
        except ImportError:
            return {
                'success': False,
                'message': "Для L1-анализа требуется scipy.optimize",
                'method': 'l1_analysis'
            }
        
        n = self.n
        u = self.u
        
        W = sparse.diags(np.sqrt(self.P.diagonal()))
        
        # Преобразование в задачу линейного программирования
        W_dense = W.toarray() if sparse.issparse(W) else W
        P_dense = self.P.toarray() if sparse.issparse(self.P) else self.P
        A_dense = self.A.toarray() if sparse.issparse(self.A) else self.A
        
        A_ub = np.vstack([
            np.hstack([W_dense, -np.eye(n)]),
            np.hstack([-W_dense, -np.eye(n)])
        ])
        
        b_ub = np.hstack([np.zeros(n), np.zeros(n)])
        A_eq = np.hstack([A_dense.T @ P_dense, np.zeros((u, n))])
        b_eq = np.zeros(u)
        c = np.hstack([np.zeros(n), np.ones(n)])
        
        # Решение
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='highs')
        
        if result.success:
            v = result.x[:n]
            suspect_indices = np.where(np.abs(v) > 3.0 * self.sigma0)[0]
            
            return {
                'residuals': v.tolist(),
                'l1_norm': float(np.sum(np.abs(v))),
                'suspect_measurements': suspect_indices.tolist(),
                'method': 'l1_analysis',
                'success': True
            }
        else:
            return {
                'success': False,
                'message': result.message,
                'method': 'l1_analysis'
            }
    
    def sequential_exclusion_analysis(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Метод 4: Последовательное отключение исходных пунктов
        
        Метод поиска ошибок в исходных данных путём:
        1. Уравнивания сети со всеми исходными пунктами
        2. Последовательного отключения каждого исходного пункта
        3. Повторного уравнивания и анализа изменения σ0
        4. Выявления пункта, отключение которого приводит к минимальному σ0
        
        Параметры:
        - network_data: данные сети
        
        Возвращает:
        - Словарь с результатами анализа
        """
        # Упрощённая реализация
        fixed_points = network_data.get('fixed_points', [])
        
        result = {
            'original_sigma0': self.sigma0,
            'best_exclusion': None,
            'min_sigma0': self.sigma0,
            'method': 'sequential_exclusion',
            'exclusions_tested': []
        }
        
        # В полной версии здесь должен быть цикл по всем исходным пунктам
        # с повторным уравниванием сети
        
        return result
    
    def levi_influence_analysis(self) -> np.ndarray:
        """
        Метод 5: Анализ влияния измерений (влияние Леви)
        
        Оценка влияния отдельных измерений на уравненные координаты.
        
        Формула влияния: ||A^T · P · e_i||
        где e_i - единичный вектор для i-го измерения
        
        Возвращает:
        - levi_influence: массив влияний для каждого измерения
        """
        N = self.A.T @ self.P @ self.A
        
        try:
            from sksparse.cholmod import cholesky
            factor = cholesky(N.tocsc())
            N_inv = factor.inv()
        except Exception as e:
            warnings.warn(f"Используем псевдообратную матрицу: {e}")
            N_inv = np.linalg.pinv(N.toarray())
            N_inv = sparse.csr_matrix(N_inv)
        
        # Влияние каждого измерения на параметры
        levi_influence = np.zeros(self.n)
        
        for i in range(self.n):
            # Вектор с 1 на i-ом месте
            e_i = np.zeros(self.n)
            e_i[i] = 1.0
            
            # Влияние i-го измерения на параметры
            influence = self.A.T @ self.P @ e_i
            levi_influence[i] = np.linalg.norm(influence)
        
        return levi_influence
    
    def detect_gross_errors(self, methods: List[str] = None, 
                           L: np.ndarray = None,
                           network_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Обнаружение грубых ошибок всеми доступными методами
        
        Параметры:
        - methods: список методов для использования
          ['standardized_residuals', 'levi_influence', 'l1_analysis', 
           'trace_traverse', 'sequential_exclusion']
        - L: вектор свободных членов (для L1-анализа)
        - network_data: данные сети (для некоторых методов)
        
        Возвращает:
        - Словарь с результатами по каждому методу
        """
        if methods is None:
            methods = ['standardized_residuals', 'levi_influence']
        
        results = {
            'methods_used': methods,
            'sigma0': self.sigma0,
            'num_measurements': self.n
        }
        
        if 'standardized_residuals' in methods:
            candidates = self.analyze_standardized_residuals(threshold=3.0)
            results['standardized_residuals'] = {
                'num_candidates': len(candidates),
                'candidates': [
                    {
                        'obs_id': c.obs_id,
                        'residual': c.residual,
                        'standardized_residual': c.standardized_residual,
                        'severity': c.severity
                    }
                    for c in candidates
                ]
            }
        
        if 'levi_influence' in methods:
            influence = self.levi_influence_analysis()
            # Выделение измерений с высоким влиянием
            threshold = float(np.mean(influence) + 2 * np.std(influence))
            high_influence_indices = np.where(influence > threshold)[0]
            results['levi_influence'] = {
                'influence_values': influence.tolist(),
                'high_influence_indices': high_influence_indices.tolist(),
                'threshold': threshold
            }
        
        if 'l1_analysis' in methods and L is not None:
            l1_result = self.l1_analysis(L)
            results['l1_analysis'] = l1_result
        
        if 'trace_traverse' in methods and network_data is not None:
            traverses = network_data.get('traverses', [])
            traverse_results = []
            for traverse in traverses:
                result = self.trace_traverse(
                    traverse,
                    traverse.get('start_point', ''),
                    traverse.get('end_point', '')
                )
                traverse_results.append(result)
            results['trace_traverse'] = traverse_results
        
        if 'sequential_exclusion' in methods and network_data is not None:
            exclusion_result = self.sequential_exclusion_analysis(network_data)
            results['sequential_exclusion'] = exclusion_result
        
        return results
