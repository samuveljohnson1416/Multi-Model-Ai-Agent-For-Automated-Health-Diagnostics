"""
Medical Logic Module
Rule-based medical reasoning for parameter classification, pattern detection, and risk scoring.
All logic is deterministic and auditable.
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ParameterStatus(Enum):
    """Parameter classification status"""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    BORDERLINE = "Borderline"
    MISSING = "Missing"
    UNKNOWN = "Unknown"


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class MedicalLogic:
    """Core medical reasoning engine with rule-based logic"""
    
    # Reference ranges by parameter
    REFERENCE_RANGES = {
        "hemoglobin": {"male": (13.5, 17.5), "female": (12.0, 16.0), "unit": "g/dL"},
        "hematocrit": {"male": (41, 53), "female": (36, 46), "unit": "%"},
        "rbc": {"male": (4.7, 6.1), "female": (4.2, 5.4), "unit": "M/µL"},
        "wbc": {"min": 4.5, "max": 11.0, "unit": "K/µL"},
        "platelet": {"min": 150, "max": 400, "unit": "K/µL"},
        "mcv": {"min": 80, "max": 100, "unit": "fL"},
        "mch": {"min": 27, "max": 33, "unit": "pg"},
        "mchc": {"min": 32, "max": 36, "unit": "g/dL"},
        "rdw": {"min": 11.5, "max": 14.5, "unit": "%"},
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
        "glucose_fasting": {"min": 70, "max": 100, "unit": "mg/dL"},
        "glucose_random": {"min": 0, "max": 140, "unit": "mg/dL"},
        "total_cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
        "ldl": {"min": 0, "max": 100, "unit": "mg/dL"},
        "hdl": {"min": 40, "max": 300, "unit": "mg/dL"},
        "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
        "urea": {"min": 7, "max": 20, "unit": "mg/dL"},
        "creatinine": {"male": (0.7, 1.3), "female": (0.6, 1.1), "unit": "mg/dL"},
        "sodium": {"min": 135, "max": 145, "unit": "mEq/L"},
        "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
        "chloride": {"min": 96, "max": 106, "unit": "mEq/L"},
        "bicarbonate": {"min": 23, "max": 29, "unit": "mEq/L"},
        "bilirubin": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
        "ast": {"min": 10, "max": 40, "unit": "U/L"},
        "alt": {"min": 7, "max": 56, "unit": "U/L"},
        "albumin": {"min": 3.5, "max": 5.0, "unit": "g/dL"},
        "calcium": {"min": 8.5, "max": 10.5, "unit": "mg/dL"},
        "phosphorus": {"min": 2.5, "max": 4.5, "unit": "mg/dL"},
        "magnesium": {"min": 1.8, "max": 2.3, "unit": "mg/dL"},
        "iron": {"male": (60, 170), "female": (50, 170), "unit": "µg/dL"},
        "protein": {"min": 6.0, "max": 8.3, "unit": "g/dL"},
        "alkaline_phosphatase": {"min": 30, "max": 120, "unit": "U/L"},
    }
    
    def __init__(self, age: Optional[int] = None, gender: Optional[str] = None):
        """Initialize medical logic with optional demographics"""
        self.age = age
        self.gender = gender or "unknown"
    
    # ========== PARAMETER STATUS LOGIC ==========
    
    def classify_parameter(self, test_name: str, value: float) -> Dict[str, Any]:
        """
        Classify a parameter as Low/Normal/High based on reference ranges.
        
        Args:
            test_name: Name of the test parameter
            value: Numeric value of the parameter
            
        Returns:
            Dict with status, deviation, and reasoning
        """
        test_name_lower = test_name.lower().strip()
        
        # Handle missing/unknown
        if value is None:
            return {
                "status": ParameterStatus.MISSING.value,
                "deviation_percent": 0,
                "reasoning": "Value is missing",
                "rule": "missing_value_rule"
            }
        
        try:
            value = float(value)
        except (ValueError, TypeError):
            return {
                "status": ParameterStatus.UNKNOWN.value,
                "deviation_percent": 0,
                "reasoning": "Value cannot be converted to number",
                "rule": "invalid_value_rule"
            }
        
        # Look up reference range
        ref_range = self._get_reference_range(test_name_lower)
        
        if not ref_range:
            return {
                "status": ParameterStatus.UNKNOWN.value,
                "deviation_percent": 0,
                "reasoning": f"Reference range not found for {test_name}",
                "rule": "unknown_parameter_rule"
            }
        
        # Classify based on range
        min_val = ref_range["min"]
        max_val = ref_range["max"]
        
        if value < min_val:
            deviation = ((min_val - value) / min_val) * 100 if min_val != 0 else 100
            return {
                "status": ParameterStatus.LOW.value,
                "deviation_percent": round(deviation, 2),
                "reference_range": f"{min_val}-{max_val}",
                "reasoning": f"Value {value} is below lower limit {min_val}",
                "rule": "below_lower_limit_rule"
            }
        
        elif value > max_val:
            deviation = ((value - max_val) / max_val) * 100 if max_val != 0 else 100
            return {
                "status": ParameterStatus.HIGH.value,
                "deviation_percent": round(deviation, 2),
                "reference_range": f"{min_val}-{max_val}",
                "reasoning": f"Value {value} is above upper limit {max_val}",
                "rule": "above_upper_limit_rule"
            }
        
        else:
            return {
                "status": ParameterStatus.NORMAL.value,
                "deviation_percent": 0,
                "reference_range": f"{min_val}-{max_val}",
                "reasoning": f"Value {value} is within normal range",
                "rule": "within_normal_range_rule"
            }
    
    def _get_reference_range(self, param_name: str) -> Optional[Dict[str, float]]:
        """Get reference range for a parameter, accounting for gender if applicable"""
        
        param_name = param_name.lower().strip()
        
        # Exact match
        if param_name in self.REFERENCE_RANGES:
            ref = self.REFERENCE_RANGES[param_name]
            return self._extract_range(ref)
        
        # Partial matches
        if "hemoglobin" in param_name or "hb" in param_name:
            ref = self.REFERENCE_RANGES["hemoglobin"]
            return self._extract_range(ref)
        
        if "hematocrit" in param_name or "hct" in param_name:
            ref = self.REFERENCE_RANGES["hematocrit"]
            return self._extract_range(ref)
        
        if "rbc" in param_name or "red blood cell" in param_name:
            ref = self.REFERENCE_RANGES["rbc"]
            return self._extract_range(ref)
        
        if "wbc" in param_name or "white blood cell" in param_name:
            ref = self.REFERENCE_RANGES["wbc"]
            return {"min": ref["min"], "max": ref["max"]}
        
        if "platelet" in param_name or "thrombocyte" in param_name:
            ref = self.REFERENCE_RANGES["platelet"]
            return {"min": ref["min"], "max": ref["max"]}
        
        if "glucose" in param_name:
            ref = self.REFERENCE_RANGES["glucose"]
            return {"min": ref["min"], "max": ref["max"]}
        
        if "cholesterol" in param_name:
            if "total" in param_name:
                ref = self.REFERENCE_RANGES["total_cholesterol"]
                return {"min": ref["min"], "max": ref["max"]}
            if "ldl" in param_name:
                ref = self.REFERENCE_RANGES["ldl"]
                return {"min": ref["min"], "max": ref["max"]}
            if "hdl" in param_name:
                ref = self.REFERENCE_RANGES["hdl"]
                return {"min": ref["min"], "max": ref["max"]}
        
        if "triglyceride" in param_name:
            ref = self.REFERENCE_RANGES["triglycerides"]
            return {"min": ref["min"], "max": ref["max"]}
        
        if "creatinine" in param_name:
            ref = self.REFERENCE_RANGES["creatinine"]
            return self._extract_range(ref)
        
        if "sodium" in param_name:
            ref = self.REFERENCE_RANGES["sodium"]
            return {"min": ref["min"], "max": ref["max"]}
        
        if "potassium" in param_name:
            ref = self.REFERENCE_RANGES["potassium"]
            return {"min": ref["min"], "max": ref["max"]}
        
        return None
    
    def _extract_range(self, ref: Dict) -> Optional[Dict[str, float]]:
        """Extract min/max from reference range dict"""
        if "min" in ref and "max" in ref:
            return {"min": ref["min"], "max": ref["max"]}
        
        if isinstance(ref, dict):
            if self.gender == "male" and "male" in ref:
                min_val, max_val = ref["male"]
                return {"min": min_val, "max": max_val}
            elif self.gender == "female" and "female" in ref:
                min_val, max_val = ref["female"]
                return {"min": min_val, "max": max_val}
            elif "male" in ref:
                min_val, max_val = ref["male"]
                return {"min": min_val, "max": max_val}
        
        return None
    
    # ========== PATTERN DETECTION LOGIC ==========
    
    def detect_anemia_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect anemia pattern based on CBC parameters.
        Rule: Low hemoglobin + Low RBC/Hematocrit
        """
        hb = self._get_param_value(parameters, ["hemoglobin", "hb"])
        rbc = self._get_param_value(parameters, ["rbc", "red blood cell"])
        hct = self._get_param_value(parameters, ["hematocrit", "hct"])
        
        hb_low = hb is not None and hb < 12.0
        rbc_low = rbc is not None and rbc < 4.0
        hct_low = hct is not None and hct < 36.0
        
        if hb_low and (rbc_low or hct_low):
            severity = RiskLevel.HIGH.value if (hb and hb < 10.0) else RiskLevel.MODERATE.value
            return {
                "pattern": "Anemia",
                "severity": severity,
                "parameters": [
                    f"Hemoglobin: {hb}" if hb else None,
                    f"RBC: {rbc}" if rbc else None,
                    f"Hematocrit: {hct}" if hct else None
                ],
                "rule": "anemia_detection_rule",
                "diagnostic_criteria": "Low Hb + (Low RBC or Low Hct)"
            }
        
        return None
    
    def detect_infection_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect infection/inflammation pattern based on WBC and differential.
        Rule: High WBC OR High neutrophils/bands
        """
        wbc = self._get_param_value(parameters, ["wbc", "white blood cell"])
        neutrophil = self._get_param_value(parameters, ["neutrophils", "neutrophil"])
        band = self._get_param_value(parameters, ["bands", "band cells"])
        
        wbc_high = wbc is not None and wbc > 11.0
        neutrophil_high = neutrophil is not None and neutrophil > 70
        band_high = band is not None and band > 5
        
        if wbc_high or neutrophil_high or band_high:
            return {
                "pattern": "Infection/Inflammation",
                "severity": RiskLevel.MODERATE.value,
                "parameters": [
                    f"WBC: {wbc}" if wbc else None,
                    f"Neutrophils: {neutrophil}%" if neutrophil else None,
                    f"Bands: {band}%" if band else None
                ],
                "rule": "infection_detection_rule",
                "diagnostic_criteria": "High WBC or High Neutrophils/Bands"
            }
        
        return None
    
    def detect_bleeding_risk_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect bleeding risk based on hemostasis parameters.
        Rule: Low platelets OR Low fibrinogen OR Prolonged PT/aPTT
        """
        platelet = self._get_param_value(parameters, ["platelet", "platelets"])
        fibrinogen = self._get_param_value(parameters, ["fibrinogen"])
        pt = self._get_param_value(parameters, ["pt", "prothrombin"])
        aptt = self._get_param_value(parameters, ["aptt", "activated partial"])
        
        platelet_low = platelet is not None and platelet < 150
        fibrinogen_low = fibrinogen is not None and fibrinogen < 2.0
        pt_high = pt is not None and pt > 14
        aptt_high = aptt is not None and aptt > 40
        
        if platelet_low or fibrinogen_low or pt_high or aptt_high:
            severity = RiskLevel.HIGH.value if (platelet and platelet < 50) else RiskLevel.MODERATE.value
            return {
                "pattern": "Bleeding Risk",
                "severity": severity,
                "parameters": [
                    f"Platelets: {platelet}" if platelet else None,
                    f"Fibrinogen: {fibrinogen}" if fibrinogen else None,
                    f"PT: {pt}" if pt else None,
                    f"aPTT: {aptt}" if aptt else None
                ],
                "rule": "bleeding_risk_detection_rule",
                "diagnostic_criteria": "Low platelets or Prolonged coagulation times"
            }
        
        return None
    
    def detect_lipid_abnormality_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect lipid abnormality pattern.
        Rule: High cholesterol OR High LDL OR Low HDL OR High triglycerides
        """
        total_chol = self._get_param_value(parameters, ["total cholesterol", "cholesterol"])
        ldl = self._get_param_value(parameters, ["ldl"])
        hdl = self._get_param_value(parameters, ["hdl"])
        triglycerides = self._get_param_value(parameters, ["triglycerides", "triglyceride"])
        
        chol_high = total_chol is not None and total_chol > 200
        ldl_high = ldl is not None and ldl > 130
        hdl_low = hdl is not None and hdl < 40
        trig_high = triglycerides is not None and triglycerides > 150
        
        if chol_high or ldl_high or hdl_low or trig_high:
            # Calculate Framingham risk score indicator
            ratio = None
            if total_chol and hdl and hdl > 0:
                ratio = total_chol / hdl
            
            return {
                "pattern": "Lipid Abnormality",
                "severity": RiskLevel.MODERATE.value,
                "parameters": [
                    f"Total Cholesterol: {total_chol}" if total_chol else None,
                    f"LDL: {ldl}" if ldl else None,
                    f"HDL: {hdl}" if hdl else None,
                    f"Triglycerides: {triglycerides}" if triglycerides else None
                ],
                "cholesterol_hdl_ratio": ratio,
                "rule": "lipid_abnormality_detection_rule",
                "diagnostic_criteria": "High cholesterol/LDL or Low HDL or High triglycerides"
            }
        
        return None
    
    def detect_renal_dysfunction_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect renal dysfunction pattern.
        Rule: High creatinine OR High urea OR Low GFR indicator
        """
        creatinine = self._get_param_value(parameters, ["creatinine"])
        urea = self._get_param_value(parameters, ["urea", "bun"])
        
        creat_high = creatinine is not None and creatinine > 1.3
        urea_high = urea is not None and urea > 20
        
        if creat_high or urea_high:
            severity = RiskLevel.HIGH.value if (creatinine and creatinine > 2.0) else RiskLevel.MODERATE.value
            return {
                "pattern": "Renal Dysfunction",
                "severity": severity,
                "parameters": [
                    f"Creatinine: {creatinine}" if creatinine else None,
                    f"Urea: {urea}" if urea else None
                ],
                "rule": "renal_dysfunction_detection_rule",
                "diagnostic_criteria": "High creatinine or High urea"
            }
        
        return None
    
    def detect_electrolyte_imbalance_pattern(self, parameters: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect electrolyte imbalance pattern.
        Rule: Abnormal sodium/potassium/chloride
        """
        sodium = self._get_param_value(parameters, ["sodium", "na"])
        potassium = self._get_param_value(parameters, ["potassium", "k"])
        chloride = self._get_param_value(parameters, ["chloride", "cl"])
        
        na_abnormal = sodium is not None and (sodium < 135 or sodium > 145)
        k_abnormal = potassium is not None and (potassium < 3.5 or potassium > 5.0)
        cl_abnormal = chloride is not None and (chloride < 96 or chloride > 106)
        
        if na_abnormal or k_abnormal or cl_abnormal:
            severity = RiskLevel.HIGH.value if (
                (sodium and (sodium < 120 or sodium > 160)) or
                (potassium and (potassium < 2.5 or potassium > 6.0))
            ) else RiskLevel.MODERATE.value
            
            return {
                "pattern": "Electrolyte Imbalance",
                "severity": severity,
                "parameters": [
                    f"Sodium: {sodium}" if sodium else None,
                    f"Potassium: {potassium}" if potassium else None,
                    f"Chloride: {chloride}" if chloride else None
                ],
                "rule": "electrolyte_imbalance_detection_rule",
                "diagnostic_criteria": "Abnormal sodium/potassium/chloride"
            }
        
        return None
    
    # ========== RISK SCORE CALCULATIONS ==========
    
    def calculate_anemia_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate anemia risk score (0.0 to 1.0)"""
        hb = self._get_param_value(parameters, ["hemoglobin", "hb"])
        
        if hb is None:
            return 0.0
        
        if hb >= 12.0:
            return 0.0
        elif hb >= 10.0:
            return 0.5
        elif hb >= 7.0:
            return 0.75
        else:
            return 1.0
    
    def calculate_infection_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate infection risk score (0.0 to 1.0)"""
        wbc = self._get_param_value(parameters, ["wbc", "white blood cell"])
        
        if wbc is None:
            return 0.0
        
        if wbc <= 11.0:
            return 0.0
        elif wbc <= 15.0:
            return 0.5
        else:
            return 0.75
    
    def calculate_bleeding_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate bleeding risk score (0.0 to 1.0)"""
        platelet = self._get_param_value(parameters, ["platelet", "platelets"])
        
        if platelet is None:
            return 0.0
        
        if platelet >= 150:
            return 0.0
        elif platelet >= 100:
            return 0.4
        elif platelet >= 50:
            return 0.7
        else:
            return 1.0
    
    def calculate_cardiovascular_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate cardiovascular risk score (0.0 to 1.0)"""
        total_chol = self._get_param_value(parameters, ["total cholesterol", "cholesterol"])
        ldl = self._get_param_value(parameters, ["ldl"])
        hdl = self._get_param_value(parameters, ["hdl"])
        triglycerides = self._get_param_value(parameters, ["triglycerides", "triglyceride"])
        
        score = 0.0
        count = 0
        
        if total_chol is not None:
            if total_chol > 240:
                score += 1.0
            elif total_chol > 200:
                score += 0.5
            count += 1
        
        if ldl is not None:
            if ldl > 160:
                score += 1.0
            elif ldl > 130:
                score += 0.5
            count += 1
        
        if hdl is not None:
            if hdl < 40:
                score += 1.0
            elif hdl < 50:
                score += 0.5
            count += 1
        
        if triglycerides is not None:
            if triglycerides > 400:
                score += 1.0
            elif triglycerides > 150:
                score += 0.5
            count += 1
        
        if count == 0:
            return 0.0
        
        return min(1.0, score / count)
    
    def calculate_renal_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate renal dysfunction risk score (0.0 to 1.0)"""
        creatinine = self._get_param_value(parameters, ["creatinine"])
        
        if creatinine is None:
            return 0.0
        
        if creatinine <= 1.3:
            return 0.0
        elif creatinine <= 2.0:
            return 0.5
        elif creatinine <= 3.0:
            return 0.7
        else:
            return 1.0
    
    def calculate_overall_risk_score(self, parameters: Dict[str, float]) -> float:
        """Calculate overall health risk score (0.0 to 1.0)"""
        scores = [
            self.calculate_anemia_risk_score(parameters),
            self.calculate_infection_risk_score(parameters),
            self.calculate_bleeding_risk_score(parameters),
            self.calculate_cardiovascular_risk_score(parameters),
            self.calculate_renal_risk_score(parameters),
        ]
        
        return sum(scores) / len(scores) if scores else 0.0
    
    # ========== CONTEXT ADJUSTMENTS ==========
    
    def adjust_for_age(self, status: str, test_name: str, age: Optional[int] = None) -> Dict[str, Any]:
        """
        Adjust parameter status based on age.
        Returns adjustment info and modified status if needed.
        """
        age = age or self.age
        
        if age is None:
            return {"adjusted": False, "status": status}
        
        test_lower = test_name.lower()
        
        # Age-specific adjustments
        adjustments = {
            "hemoglobin": {
                "child_0_5": {"range": (0, 5), "note": "Children have lower normal hemoglobin"},
                "child_6_12": {"range": (6, 12), "note": "Pediatric reference range applies"},
                "teen": {"range": (13, 17), "note": "Teenage reference range applies"},
                "adult": {"range": (18, 65), "note": "Adult reference range applies"},
                "senior": {"range": (65, 150), "note": "Elderly may have lower tolerance"}
            },
            "creatinine": {
                "elderly": {"range": (65, 150), "note": "Age-related decrease in GFR"}
            }
        }
        
        if test_lower in adjustments:
            adjustment = adjustments[test_lower]
            
            # Find applicable range
            for age_group, info in adjustment.items():
                if info["range"][0] <= age <= info["range"][1]:
                    return {
                        "adjusted": True,
                        "status": status,
                        "age_group": age_group,
                        "note": info["note"]
                    }
        
        return {"adjusted": False, "status": status}
    
    def adjust_for_gender(self, status: str, test_name: str) -> Dict[str, Any]:
        """
        Adjust parameter status based on gender.
        """
        test_lower = test_name.lower()
        
        gender_specific = [
            "hemoglobin", "hematocrit", "rbc", "creatinine", "iron"
        ]
        
        if any(g in test_lower for g in gender_specific):
            return {
                "adjusted": True,
                "status": status,
                "gender": self.gender,
                "note": f"Gender-specific reference range ({self.gender}) applied"
            }
        
        return {"adjusted": False, "status": status}
    
    # ========== UTILITY METHODS ==========
    
    def _get_param_value(self, parameters: Dict[str, float], 
                         possible_names: List[str]) -> Optional[float]:
        """Get parameter value by checking multiple possible names"""
        for name in possible_names:
            name_lower = name.lower().strip()
            
            # Exact match
            if name_lower in parameters:
                return parameters[name_lower]
            
            # Partial match
            for key, val in parameters.items():
                if name_lower in key.lower():
                    return val
        
        return None
    
    def get_all_detected_patterns(self, parameters: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect all patterns in the given parameters"""
        patterns = []
        
        anemia = self.detect_anemia_pattern(parameters)
        if anemia:
            patterns.append(anemia)
        
        infection = self.detect_infection_pattern(parameters)
        if infection:
            patterns.append(infection)
        
        bleeding = self.detect_bleeding_risk_pattern(parameters)
        if bleeding:
            patterns.append(bleeding)
        
        lipid = self.detect_lipid_abnormality_pattern(parameters)
        if lipid:
            patterns.append(lipid)
        
        renal = self.detect_renal_dysfunction_pattern(parameters)
        if renal:
            patterns.append(renal)
        
        electrolyte = self.detect_electrolyte_imbalance_pattern(parameters)
        if electrolyte:
            patterns.append(electrolyte)
        
        return patterns
    
    def assess_overall_health_status(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """Comprehensive health assessment"""
        
        patterns = self.get_all_detected_patterns(parameters)
        overall_risk = self.calculate_overall_risk_score(parameters)
        
        if overall_risk >= 0.7:
            status = RiskLevel.HIGH.value
        elif overall_risk >= 0.4:
            status = RiskLevel.MODERATE.value
        else:
            status = RiskLevel.LOW.value
        
        return {
            "overall_risk_level": status,
            "risk_score": round(overall_risk, 3),
            "patterns_detected": patterns,
            "total_patterns": len(patterns),
            "requires_attention": len(patterns) > 0 or overall_risk >= 0.4,
            "recommendation": self._get_recommendation(status, patterns)
        }
    
    def _get_recommendation(self, status: str, patterns: List[Dict]) -> str:
        """Get recommendation based on status and patterns"""
        if status == RiskLevel.HIGH.value:
            return "Immediate consultation with healthcare provider recommended"
        elif status == RiskLevel.MODERATE.value:
            return "Follow-up consultation with healthcare provider recommended"
        else:
            return "Continue regular health monitoring"
