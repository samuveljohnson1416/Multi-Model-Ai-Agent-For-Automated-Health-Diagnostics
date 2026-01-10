"""
Model 1: Parameter Interpretation Model
Compares individual parameter values against standard/personalized reference ranges
Classifies parameters as: Normal, High, Low, Borderline, Critical
"""

import json
import os


class ParameterInterpreter:
    """Model 1 - Individual Parameter Analysis against Reference Ranges"""
    
    def __init__(self):
        self.reference_ranges = self._load_e