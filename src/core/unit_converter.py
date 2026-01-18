"""
Unit Conversion System for Blood Parameters
Converts between different units to standardize values
"""

from typing import Dict, Optional, Tuple
import re


class UnitConverter:
    """
    Converts blood parameter values between different units.
    Standardizes all values to a common unit system.
    """
    
    def __init__(self):
        # Standard units for each parameter
        self.standard_units = {
            'Hemoglobin': 'g/dL',
            'RBC': 'mill/cumm',
            'WBC': '/cumm',
            'Platelet': '/cumm',
            'Glucose': 'mg/dL',
            'Cholesterol': 'mg/dL',
            'HDL': 'mg/dL',
            'LDL': 'mg/dL',
            'Triglycerides': 'mg/dL',
            'Creatinine': 'mg/dL',
            'Urea': 'mg/dL',
            'BUN': 'mg/dL',
            'Uric_Acid': 'mg/dL',
            'Sodium': 'mEq/L',
            'Potassium': 'mEq/L',
            'Chloride': 'mEq/L',
            'Calcium': 'mg/dL',
            'Iron': 'mcg/dL',
            'Ferritin': 'ng/mL',
            'Vitamin_B12': 'pg/mL',
            'Vitamin_D': 'ng/mL',
            'TSH': 'mIU/L',
            'T3': 'ng/dL',
            'T4': 'mcg/dL',
            'HbA1c': '%',
            'ESR': 'mm/hr',
            'CRP': 'mg/L',
            'Bilirubin_Total': 'mg/dL',
            'ALT': 'U/L',
            'AST': 'U/L',
            'ALP': 'U/L'
        }
        
        # Conversion factors: {from_unit: {to_unit: factor}}
        # value_in_to_unit = value_in_from_unit * factor
        self.conversions = {
            # Hemoglobin
            'g/dL_to_g/L': 10.0,
            'g/L_to_g/dL': 0.1,
            'g/dL_to_mmol/L': 0.6206,  # Hemoglobin specific
            'mmol/L_to_g/dL': 1.611,
            
            # Glucose
            'mg/dL_to_mmol/L': 0.0555,
            'mmol/L_to_mg/dL': 18.018,
            
            # Cholesterol (Total, HDL, LDL) - Correct factor: 38.67 mg/dL = 1 mmol/L
            'mg/dL_to_mmol/L_chol': 0.02586,
            'mmol/L_to_mg/dL_chol': 38.67,
            
            # Triglycerides - Correct factor: 88.57 mg/dL = 1 mmol/L
            'mg/dL_to_mmol/L_tg': 0.01129,
            'mmol/L_to_mg/dL_tg': 88.57,
            
            # Creatinine
            'mg/dL_to_umol/L': 88.4,
            'umol/L_to_mg/dL': 0.0113,
            'mg/dL_to_mmol/L_creat': 0.0884,
            'mmol/L_to_mg/dL_creat': 11.31,
            
            # Urea/BUN
            'mg/dL_to_mmol/L_urea': 0.357,
            'mmol/L_to_mg/dL_urea': 2.8,
            
            # Uric Acid
            'mg/dL_to_umol/L_ua': 59.48,
            'umol/L_to_mg/dL_ua': 0.0168,
            
            # Bilirubin
            'mg/dL_to_umol/L_bili': 17.1,
            'umol/L_to_mg/dL_bili': 0.0585,
            
            # Iron
            'mcg/dL_to_umol/L': 0.179,
            'umol/L_to_mcg/dL': 5.587,
            
            # Calcium
            'mg/dL_to_mmol/L_ca': 0.25,
            'mmol/L_to_mg/dL_ca': 4.0,
            
            # Sodium/Potassium/Chloride (mEq/L = mmol/L for monovalent ions)
            'mEq/L_to_mmol/L': 1.0,
            'mmol/L_to_mEq/L': 1.0,
            
            # TSH
            'mIU/L_to_uIU/mL': 1.0,
            'uIU/mL_to_mIU/L': 1.0,
            
            # Vitamin D
            'ng/mL_to_nmol/L': 2.496,
            'nmol/L_to_ng/mL': 0.401,
            
            # Vitamin B12
            'pg/mL_to_pmol/L': 0.738,
            'pmol/L_to_pg/mL': 1.355,
            
            # Ferritin
            'ng/mL_to_ug/L': 1.0,
            'ug/L_to_ng/mL': 1.0,
            'ng/mL_to_pmol/L': 2.247,
            'pmol/L_to_ng/mL': 0.445,
            
            # Cell counts
            '/cumm_to_10^9/L': 0.001,
            '10^9/L_to_/cumm': 1000,
            '/uL_to_/cumm': 1.0,
            '/cumm_to_/uL': 1.0,
            'mill/cumm_to_10^12/L': 1.0,
            '10^12/L_to_mill/cumm': 1.0,
            'M/uL_to_mill/cumm': 1.0,
            'mill/cumm_to_M/uL': 1.0,
            
            # Volume units
            'fL_to_um3': 1.0,
            'um3_to_fL': 1.0,
            
            # Mass units
            'pg_to_fg': 1000,
            'fg_to_pg': 0.001
        }

    def normalize_unit(self, unit: str) -> str:
        """Normalize unit string for comparison"""
        if not unit:
            return ''
        
        # Lowercase and remove spaces
        unit = unit.lower().strip()
        
        # Common normalizations
        normalizations = {
            'g/dl': 'g/dL',
            'g/l': 'g/L',
            'mg/dl': 'mg/dL',
            'mmol/l': 'mmol/L',
            'umol/l': 'umol/L',
            'meq/l': 'mEq/L',
            'miu/l': 'mIU/L',
            'uiu/ml': 'uIU/mL',
            'ng/ml': 'ng/mL',
            'pg/ml': 'pg/mL',
            'nmol/l': 'nmol/L',
            'pmol/l': 'pmol/L',
            'ug/l': 'ug/L',
            'mcg/dl': 'mcg/dL',
            'u/l': 'U/L',
            'iu/l': 'IU/L',
            '/cumm': '/cumm',
            '/ul': '/uL',
            'cells/ul': '/uL',
            'cells/cumm': '/cumm',
            '10^9/l': '10^9/L',
            '10^12/l': '10^12/L',
            'x10^9/l': '10^9/L',
            'x10^12/l': '10^12/L',
            'mill/cumm': 'mill/cumm',
            'million/cumm': 'mill/cumm',
            'm/ul': 'M/uL',
            'million/ul': 'M/uL',
            'fl': 'fL',
            'pg': 'pg',
            '%': '%',
            'mm/hr': 'mm/hr',
            'mm/hour': 'mm/hr'
        }
        
        return normalizations.get(unit, unit)
    
    def get_conversion_factor(self, from_unit: str, to_unit: str, parameter: str = None) -> Optional[float]:
        """Get conversion factor between two units"""
        from_norm = self.normalize_unit(from_unit)
        to_norm = self.normalize_unit(to_unit)
        
        if from_norm == to_norm:
            return 1.0
        
        # Build conversion key
        key = f"{from_norm}_to_{to_norm}"
        
        # Check parameter-specific conversions FIRST (before generic)
        if parameter:
            param_lower = parameter.lower()
            if 'cholesterol' in param_lower or 'hdl' in param_lower or 'ldl' in param_lower:
                key_chol = f"{from_norm}_to_{to_norm}_chol"
                if key_chol in self.conversions:
                    return self.conversions[key_chol]
            elif 'triglyceride' in param_lower:
                key_tg = f"{from_norm}_to_{to_norm}_tg"
                if key_tg in self.conversions:
                    return self.conversions[key_tg]
            elif 'creatinine' in param_lower:
                key_creat = f"{from_norm}_to_{to_norm}_creat"
                if key_creat in self.conversions:
                    return self.conversions[key_creat]
            elif 'urea' in param_lower or 'bun' in param_lower:
                key_urea = f"{from_norm}_to_{to_norm}_urea"
                if key_urea in self.conversions:
                    return self.conversions[key_urea]
            elif 'uric' in param_lower:
                key_ua = f"{from_norm}_to_{to_norm}_ua"
                if key_ua in self.conversions:
                    return self.conversions[key_ua]
            elif 'bilirubin' in param_lower:
                key_bili = f"{from_norm}_to_{to_norm}_bili"
                if key_bili in self.conversions:
                    return self.conversions[key_bili]
            elif 'calcium' in param_lower:
                key_ca = f"{from_norm}_to_{to_norm}_ca"
                if key_ca in self.conversions:
                    return self.conversions[key_ca]
        
        # Check direct conversion (generic)
        if key in self.conversions:
            return self.conversions[key]
        
        return None
    
    def convert(self, value: float, from_unit: str, to_unit: str, parameter: str = None) -> Tuple[Optional[float], str]:
        """
        Convert a value from one unit to another.
        
        Returns:
            Tuple of (converted_value, status_message)
        """
        factor = self.get_conversion_factor(from_unit, to_unit, parameter)
        
        if factor is None:
            return None, f"No conversion available from {from_unit} to {to_unit}"
        
        converted = round(value * factor, 4)
        return converted, "Converted successfully"
    
    def convert_to_standard(self, parameter: str, value: float, current_unit: str) -> Dict:
        """
        Convert a parameter value to its standard unit.
        
        Returns:
            Dict with converted_value, standard_unit, original_value, original_unit, conversion_applied
        """
        standard_unit = self.standard_units.get(parameter)
        
        if not standard_unit:
            return {
                'converted_value': value,
                'standard_unit': current_unit,
                'original_value': value,
                'original_unit': current_unit,
                'conversion_applied': False,
                'note': 'No standard unit defined for this parameter'
            }
        
        current_norm = self.normalize_unit(current_unit)
        standard_norm = self.normalize_unit(standard_unit)
        
        if current_norm == standard_norm:
            return {
                'converted_value': value,
                'standard_unit': standard_unit,
                'original_value': value,
                'original_unit': current_unit,
                'conversion_applied': False,
                'note': 'Already in standard unit'
            }
        
        converted, status = self.convert(value, current_unit, standard_unit, parameter)
        
        if converted is not None:
            return {
                'converted_value': converted,
                'standard_unit': standard_unit,
                'original_value': value,
                'original_unit': current_unit,
                'conversion_applied': True,
                'note': f'Converted from {current_unit} to {standard_unit}'
            }
        else:
            return {
                'converted_value': value,
                'standard_unit': current_unit,
                'original_value': value,
                'original_unit': current_unit,
                'conversion_applied': False,
                'note': status
            }
    
    def detect_and_convert(self, parameter: str, value: float, unit: str) -> Dict:
        """
        Detect unit type and convert to standard if needed.
        Also handles common unit variations.
        """
        # Clean up unit string
        unit_clean = self.normalize_unit(unit)
        
        # Try to convert to standard
        result = self.convert_to_standard(parameter, value, unit_clean)
        
        return result


# Singleton instance
_converter = UnitConverter()

def convert_to_standard_unit(parameter: str, value: float, unit: str) -> Dict:
    """Convert a parameter value to standard unit"""
    return _converter.convert_to_standard(parameter, value, unit)

def convert_units(value: float, from_unit: str, to_unit: str, parameter: str = None) -> Tuple[Optional[float], str]:
    """Convert between any two units"""
    return _converter.convert(value, from_unit, to_unit, parameter)

def get_standard_unit(parameter: str) -> str:
    """Get the standard unit for a parameter"""
    return _converter.standard_units.get(parameter, 'N/A')
