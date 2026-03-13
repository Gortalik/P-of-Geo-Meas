#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модули интеграции обработки и сохранения результатов
"""

from .integration import ProcessingIntegration
from .processing_thread import ProcessingThread

__all__ = ['ProcessingIntegration', 'ProcessingThread']
