"""
Dynamic Reference Ranges Module
Adjusts reference ranges based on Age and Gender
"""

from typing import Dict, Optional, Tuple


class DynamicReferenceRanges:
    """
    Provides age and gender-adjusted reference ranges for blood parameters.
    Based on clinical guidelines and medical literature.
    """
    
    def __init__(self):
        # Base reference ranges with age/gender variations
        self.dynamic_ranges = {
            'Hemoglobin': {
                'male': {
                    'child_0_12': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'teen_13_17': {'min': 13.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_18_49': {'min': 14.0, 'max': 18.0, 'unit': 'g/dL'},
                    'adult_50_64': {'min': 13.5, 'max': 17.5, 'unit': 'g/dL'},
                    'senior_65_plus': {'min': 12.5, 'max': 17.0, 'unit': 'g/dL'}
                },
                'female': {
                    'child_0_12': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'teen_13_17': {'min': 12.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_18_49': {'min': 12.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_50_64': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'senior_65_plus': {'min': 11.0, 'max': 15.0, 'unit': 'g/dL'}
                },
                'default': {'min': 12.0, 'max': 17.0, 'unit': 'g/dL'}
            },
            'RBC': {
                'male': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'teen_13_17': {'min': 4.5, 'max': 5.5, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.7, 'max': 6.1, 'unit': 'mill/cumm'},
                    'adult_50_64': {'min': 4.5, 'max': 5.9, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 4.2, 'max': 5.7, 'unit': 'mill/cumm'}
                },
                'female': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'teen_13_17': {'min': 4.0, 'max': 5.0, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.2, 'max': 5.4, 'unit': 'mill/cumm'},
                    'adult_50_64': {'min': 4.0, 'max': 5.2, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 3.8, 'max': 5.0, 'unit': 'mill/cumm'}
                },
                'default': {'min': 4.5, 'max': 5.5, 'unit': 'mill/cumm'}
            },
            'WBC': {
                'child_0_12': {'min': 5000, 'max': 15000, 'unit': '/cumm'},
                'teen_13_17': {'min': 4500, 'max': 13000, 'unit': '/cumm'},
                'adult_18_64': {'min': 4000, 'max': 11000, 'unit': '/cumm'},
                'senior_65_plus': {'min': 3500, 'max': 10500, 'unit': '/cumm'},
                'default': {'min': 4000, 'max': 11000, 'unit': '/cumm'}
            },
            'Platelet': {
                'child_0_12': {'min': 150000, 'max': 450000, 'unit': '/cumm'},
                'adult_13_plus': {'min': 150000, 'max': 400000, 'unit': '/cumm'},
                'default': {'min': 150000, 'max': 400000, 'unit': '/cumm'}
            },
            'PCV': {
                'male': {
                    'child_0_12': {'min': 35, 'max': 45, 'unit': '%'},
                    'teen_13_17': {'min': 37, 'max': 49, 'unit': '%'},
                    'adult_18_49': {'min': 40, 'max': 54, 'unit': '%'},
                    'adult_50_plus': {'min': 38, 'max': 50, 'unit': '%'}
                },
                'female': {
                    'child_0_12': {'min': 35, 'max': 45, 'unit': '%'},
                    'teen_13_17': {'min': 36, 'max': 44, 'unit': '%'},
                    'adult_18_49': {'min': 36, 'max': 48, 'unit': '%'},
                    'adult_50_plus': {'min': 34, 'max': 46, 'unit': '%'}
                },
                'default': {'min': 36, 'max': 50, 'unit': '%'}
            },
            'MCV': {
                'child_0_6': {'min': 70, 'max': 86, 'unit': 'fL'},
                'child_7_12': {'min': 77, 'max': 95, 'unit': 'fL'},
                'adult_13_plus': {'min': 80, 'max': 100, 'unit': 'fL'},
                'default': {'min': 80, 'max': 100, 'unit': 'fL'}
            },
            'MCH': {
                'child_0_12': {'min': 24, 'max': 30, 'unit': 'pg'},
                'adult_13_plus': {'min': 27, 'max': 32, 'unit': 'pg'},
                'default': {'min': 27, 'max': 32, 'unit': 'pg'}
            },
            'MCHC': {
                'default': {'min': 32, 'max': 36, 'unit': 'g/dL'}
            },
            'Glucose': {
                'child_0_12': {'min': 60, 'max': 100, 'unit': 'mg/dL'},
                'adult_13_64': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
                'senior_65_plus': {'min': 70, 'max': 110, 'unit': 'mg/dL'},  # Slightly relaxed for elderly
                'default': {'min': 70, 'max': 100, 'unit': 'mg/dL'}
            },
            'Cholesterol': {
                'child_0_17': {'min': 0, 'max': 170, 'unit': 'mg/dL'},
                'adult_18_plus': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 200, 'unit': 'mg/dL'}
            },
            'HDL': {
                'male': {
                    'default': {'min': 40, 'max': 60, 'unit': 'mg/dL'}
                },
                'female': {
                    'default': {'min': 50, 'max': 70, 'unit': 'mg/dL'}
                },
                'default': {'min': 40, 'max': 60, 'unit': 'mg/dL'}
            },
            'LDL': {
                'optimal': {'min': 0, 'max': 100, 'unit': 'mg/dL'},
                'near_optimal': {'min': 100, 'max': 129, 'unit': 'mg/dL'},
                'borderline_high': {'min': 130, 'max': 159, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 130, 'unit': 'mg/dL'}
            },
            'Triglycerides': {
                'child_0_9': {'min': 0, 'max': 75, 'unit': 'mg/dL'},
                'child_10_17': {'min': 0, 'max': 90, 'unit': 'mg/dL'},
                'adult_18_plus': {'min': 0, 'max': 150, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 150, 'unit': 'mg/dL'}
            },
            'Creatinine': {
                'male': {
                    'child_0_12': {'min': 0.3, 'max': 0.7, 'unit': 'mg/dL'},
                    'teen_13_17': {'min': 0.5, 'max': 1.0, 'unit': 'mg/dL'},
                    'adult_18_59': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.8, 'max': 1.4, 'unit': 'mg/dL'}
                },
                'female': {
                    'child_0_12': {'min': 0.3, 'max': 0.7, 'unit': 'mg/dL'},
                    'teen_13_17': {'min': 0.5, 'max': 0.9, 'unit': 'mg/dL'},
                    'adult_18_59': {'min': 0.6, 'max': 1.1, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'}
                },
                'default': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'}
            },
            'Urea': {
                'child_0_12': {'min': 5, 'max': 18, 'unit': 'mg/dL'},
                'adult_13_59': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
                'senior_60_plus': {'min': 8, 'max': 23, 'unit': 'mg/dL'},
                'default': {'min': 7, 'max': 20, 'unit': 'mg/dL'}
            },
            'Uric_Acid': {
                'male': {
                    'default': {'min': 3.5, 'max': 7.2, 'unit': 'mg/dL'}
                },
                'female': {
                    'premenopausal': {'min': 2.5, 'max': 6.0, 'unit': 'mg/dL'},
                    'postmenopausal': {'min': 3.0, 'max': 6.5, 'unit': 'mg/dL'}
                },
                'default': {'min': 3.0, 'max': 7.0, 'unit': 'mg/dL'}
            },
            'TSH': {
                'child_0_12': {'min': 0.7, 'max': 6.0, 'unit': 'mIU/L'},
                'adult_13_64': {'min': 0.4, 'max': 4.0, 'unit': 'mIU/L'},
                'senior_65_plus': {'min': 0.5, 'max': 5.0, 'unit': 'mIU/L'},
                'default': {'min': 0.4, 'max': 4.0, 'unit': 'mIU/L'}
            },
            'Ferritin': {
                'male': {
                    'default': {'min': 30, 'max': 400, 'unit': 'ng/mL'}
                },
                'female': {
                    'premenopausal': {'min': 15, 'max': 150, 'unit': 'ng/mL'},
                    'postmenopausal': {'min': 30, 'max': 300, 'unit': 'ng/mL'}
                },
                'default': {'min': 20, 'max': 300, 'unit': 'ng/mL'}
            },
            'Iron': {
                'male': {
                    'default': {'min': 65, 'max': 175, 'unit': 'mcg/dL'}
                },
                'female': {
                    'default': {'min': 50, 'max': 170, 'unit': 'mcg/dL'}
                },
                'default': {'min': 60, 'max': 170, 'unit': 'mcg/dL'}
            },
            'Vitamin_D': {
                'default': {'min': 30, 'max': 100, 'unit': 'ng/mL'},
                'senior_65_plus': {'min': 30, 'max': 80, 'unit': 'ng/mL'}
            },
            'Vitamin_B12': {
                'default': {'min': 200, 'max': 900, 'unit': 'pg/mL'},
                'senior_65_plus': {'min': 300, 'max': 900, 'unit': 'pg/mL'}  # Higher minimum for elderly
            },
            'ESR': {
                'male': {
                    'adult_under_50': {'min': 0, 'max': 15, 'unit': 'mm/hr'},
                    'adult_50_plus': {'min': 0, 'max': 20, 'unit': 'mm/hr'}
                },
                'female': {
                    'adult_under_50': {'min': 0, 'max': 20, 'unit': 'mm/hr'},
                    'adult_50_plus': {'min': 0, 'max': 30, 'unit': 'mm/hr'}
                },
                'default': {'min': 0, 'max': 20, 'unit': 'mm/hr'}
            },
            'Neutrophils': {
                'default': {'min': 40, 'max': 70, 'unit': '%'}
            },
            'Lymphocytes': {
                'default': {'min': 20, 'max': 40, 'unit': '%'}
            },
            'Monocytes': {
                'default': {'min': 2, 'max': 8, 'unit': '%'}
            },
            'Eosinophils': {
                'default': {'min': 1, 'max': 4, 'unit': '%'}
            },
            'Basophils': {
                'default': {'min': 0, 'max': 1, 'unit': '%'}
            }
        }

    def _get_age_category(self, age: int) -> str:
        """Determine age category from numeric age"""
        if age is None:
            return 'adult'
        if age <= 6:
            return 'child_0_6'
        elif age <= 9:
            return 'child_0_9'
        elif age <= 12:
            return 'child_0_12'
        elif age <= 17:
            return 'teen_13_17'
        elif age <= 49:
            return 'adult_18_49'
        elif age <= 59:
            return 'adult_50_64'
        elif age <= 64:
            return 'adult_50_64'
        else:
            return 'senior_65_plus'
    
    def get_reference_range(self, parameter: str, age: Optional[int] = None, 
                           gender: Optional[str] = None) -> Dict:
        """
        Get the appropriate reference range for a parameter based on age and gender.
        
        Args:
            parameter: Name of the blood parameter
            age: Patient's age in years
            gender: 'male' or 'female'
        
        Returns:
            Dict with 'min', 'max', 'unit' keys
        """
        param_ranges = self.dynamic_ranges.get(parameter)
        
        if not param_ranges:
            # Return default if parameter not in dynamic ranges
            return None
        
        gender_lower = gender.lower() if gender else None
        age_cat = self._get_age_category(age)
        
        # Try gender-specific ranges first
        if gender_lower and gender_lower in param_ranges:
            gender_ranges = param_ranges[gender_lower]
            
            # Try age-specific within gender
            for key in gender_ranges:
                if age_cat in key or self._age_matches_key(age, key):
                    return gender_ranges[key]
            
            # Fall back to gender default
            if 'default' in gender_ranges:
                return gender_ranges['default']
        
        # Try age-specific ranges (non-gender-specific)
        for key in param_ranges:
            if key not in ['male', 'female', 'default']:
                if age_cat in key or self._age_matches_key(age, key):
                    return param_ranges[key]
        
        # Fall back to default
        return param_ranges.get('default')
    
    def _age_matches_key(self, age: int, key: str) -> bool:
        """Check if age matches a range key like 'adult_18_49' or 'child_0_12'"""
        if age is None:
            return False
        
        # Parse key patterns
        import re
        match = re.search(r'(\d+)_(\d+)', key)
        if match:
            min_age, max_age = int(match.group(1)), int(match.group(2))
            return min_age <= age <= max_age
        
        match = re.search(r'(\d+)_plus', key)
        if match:
            min_age = int(match.group(1))
            return age >= min_age
        
        match = re.search(r'under_(\d+)', key)
        if match:
            max_age = int(match.group(1))
            return age < max_age
        
        return False
    
    def get_all_adjusted_ranges(self, age: Optional[int] = None, 
                                gender: Optional[str] = None) -> Dict:
        """
        Get all reference ranges adjusted for the given age and gender.
        
        Returns:
            Dict mapping parameter names to their adjusted reference ranges
        """
        adjusted = {}
        
        for param in self.dynamic_ranges.keys():
            ref = self.get_reference_range(param, age, gender)
            if ref:
                adjusted[param] = ref
        
        return adjusted
    
    def validate_with_dynamic_range(self, parameter: str, value: float,
                                    age: Optional[int] = None,
                                    gender: Optional[str] = None) -> Dict:
        """
        Validate a parameter value against dynamic reference range.
        
        Returns:
            Dict with status, reference_range, and adjustment_note
        """
        ref = self.get_reference_range(parameter, age, gender)
        
        if not ref:
            return {
                'status': 'UNKNOWN',
                'reference_range': 'N/A',
                'adjustment_note': 'No reference range available'
            }
        
        min_val = ref['min']
        max_val = ref['max']
        unit = ref.get('unit', '')
        
        if value < min_val:
            status = 'LOW'
        elif value > max_val:
            status = 'HIGH'
        else:
            status = 'NORMAL'
        
        # Generate adjustment note
        adjustment_note = None
        if age or gender:
            notes = []
            if age:
                notes.append(f"age {age}")
            if gender:
                notes.append(gender)
            adjustment_note = f"Range adjusted for {', '.join(notes)}"
        
        return {
            'status': status,
            'reference_range': f"{min_val} - {max_val}",
            'unit': unit,
            'adjustment_note': adjustment_note
        }


# Singleton instance
_dynamic_ranges = DynamicReferenceRanges()

def get_dynamic_reference(parameter: str, age: int = None, gender: str = None) -> Dict:
    """Get dynamic reference range for a parameter"""
    return _dynamic_ranges.get_reference_range(parameter, age, gender)

def validate_parameter_dynamic(parameter: str, value: float, age: int = None, gender: str = None) -> Dict:
    """Validate a parameter with dynamic reference ranges"""
    return _dynamic_ranges.validate_with_dynamic_range(parameter, value, age, gender)

def get_all_dynamic_ranges(age: int = None, gender: str = None) -> Dict:
    """Get all reference ranges adjusted for age/gender"""
    return _dynamic_ranges.get_all_adjusted_ranges(age, gender)
