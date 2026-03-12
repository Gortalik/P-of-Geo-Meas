#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для парсеров форматов приборов
"""

import pytest
from pathlib import Path
import sys

# Добавляем путь к исходному коду
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from geoadjust.io.formats.gsi import GSIParser
from geoadjust.io.formats.dat import DATParser
from geoadjust.io.formats.sdr import SDRParser


class TestGSIParser:
    """Тесты для парсера формата Leica GSI"""
    
    def test_gsi_parser_initialization(self):
        """Тест инициализации парсера"""
        parser = GSIParser()
        assert parser is not None
        assert parser.errors == []
        assert parser.warnings == []
    
    def test_gsi_statistics_empty(self):
        """Тест статистики пустого парсера"""
        parser = GSIParser()
        stats = parser.get_statistics()
        
        assert stats['total_observations'] == 0
        assert stats['stations'] == 0
        assert stats['errors'] == 0
        assert stats['warnings'] == 0


class TestDATParser:
    """Тесты для парсера формата Leica DAT"""
    
    def test_dat_parser_initialization(self):
        """Тест инициализации парсера DAT"""
        parser = DATParser()
        assert parser is not None
    
    def test_dat_statistics_empty(self):
        """Тест статистики пустого парсера DAT"""
        parser = DATParser()
        stats = parser.get_statistics()
        
        assert stats['total_observations'] == 0
        assert stats['stations'] == 0


class TestSDRParser:
    """Тесты для парсера формата Sokkia SDR"""
    
    def test_sdr_parser_initialization(self):
        """Тест инициализации парсера SDR"""
        parser = SDRParser()
        assert parser is not None
    
    def test_sdr_statistics_empty(self):
        """Тест статистики пустого парсера SDR"""
        parser = SDRParser()
        stats = parser.get_statistics()
        
        assert stats['total_observations'] == 0
        assert stats['stations'] == 0
    
    def test_sdr_job_name_empty(self):
        """Тест имени работы по умолчанию"""
        parser = SDRParser()
        assert parser.job_name == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
