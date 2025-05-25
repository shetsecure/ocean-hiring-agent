#!/usr/bin/env python3
"""
Team Compatibility Analyzer Package

A comprehensive tool for analyzing team compatibility using personality traits and AI.
"""

from .compatibility_analyzer import CompatibilityAnalyzer
from .rate_limiter import RateLimiter
from .personality_extractor import PersonalityTraitsExtractor
from .utils import print_results_summary
from .main import main

__version__ = "2.1.0"
__author__ = "Team Compatibility Analyzer"

__all__ = [
    "CompatibilityAnalyzer",
    "RateLimiter", 
    "PersonalityTraitsExtractor",
    "print_results_summary",
    "main"
] 