"""
Milestone-2: Pattern Recognition & Contextual Analysis Models
Implements Model-2 (Pattern Recognition) and Model-3 (Contextual Analysis)
"""

import pandas as pd
import json
from typing import Dict, List, Any, Optional


class Model2PatternRecognition:
    """
    Model-2: Pattern Recognition & Risk Assessment (Milestone-2 Mandatory)
    
    Operates on Phase-1 outputs to detect patterns across parameter combinations.
    Does NOT re-interpret individual parameters - uses Phase-1 status as authority.
    """
    
    def __init__(self):
        # Define parameter groups for pattern recognition
        self.cbc_parameters = [
            'hemoglobin', 'hematocrit', 'rbc count', 'mcv', 'mch', 'mchc', 'rdw',
            'wbc count', 'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
            'platelet count', 'mpv'
        ]
        
        self.lipid_parameters = [
            'total cholesterol', 'hdl cholesterol', 'ldl cholesterol', 'triglycerides'
        ]
        
        self.liver_parameters = [
            'alt', 'ast', 'alp', 'bilirubin', 'albumin', 'total protein'
        ]
        
        self.kidney_parameters = [
            'creatinine', 'bun', 'urea', 'egfr'
        ]
    
    def analyze_patterns(self, model1_result: Dict) -> Dict[str, Any]:
        """
        Main pattern recognition analysis using Phase-1 outputs
        
        Input: Model-1 results with parameter statuses (Low/Normal/High)
        Output: Detected patterns and risk assessment
        """
        
        # Extract parameter data with Phase-1 statuses
        parameters = self._extract_parameter_data(model1_result)
        
        # Detect patterns across parameter combinations
        detected_patterns = []
        
        # CBC Pattern Recognition
        cbc_patterns = self._analyze_cbc_patterns(parameters)
        detected_patterns.extend(cbc_patterns)
        
        # Lipid Pattern Recognition
        lipid_patterns = self._analyze_lipid_patterns(parameters)
        detected_patterns.extend(lipid_patterns)
        
        # White Blood Cell Distribution Patterns
        wbc_patterns = self._analyze_wbc_distribution_patterns(parameters)
        detected_patterns.extend(wbc_patterns)
        
        # Red Blood Cell Index Patterns
        rbc_patterns = self._analyze_rbc_index_patterns(parameters)
        detected_patterns.extend(rbc_patterns)
        
        # Cross-System Patterns
        cross_system_patterns = self._analyze_cross_system_patterns(parameters)
        detected_patterns.extend(cross_system_patterns)
        
        # Assess overall risk based on detected patterns
        risk_assessment = self._assess_risk_from_patterns(detected_patterns)
        
        return {
            "patterns_detected": [pattern["description"] for pattern in detected_patterns],
            "risk_level": risk_assessment["risk_level"],
            "risk_reasoning": risk_assessment["reasoning"],
            "pattern_details": detected_patterns,
            "total_patterns": len(detected_patterns)
        }
    
    def _extract_parameter_data(self, model1_result: Dict) -> Dict[str, Dict]:
        """Extract parameter data with Phase-1 classifications"""
        parameters = {}
        
        for interpretation in model1_result.get("interpretations", []):
            param_name = interpretation.get("test_name", "").lower()
            parameters[param_name] = {
                "name": interpretation.get("test_name", ""),
                "value": interpretation.get("value", ""),
                "classification": interpretation.get("classification", "Unknown"),
                "reference_range": interpretation.get("reference_range", ""),
                "numeric_value": self._safe_float_conversion(interpretation.get("value", ""))
            }
        
        return parameters
    
    def _safe_float_conversion(self, value: str) -> Optional[float]:
        """Safely convert string value to float"""
        try:
            return float(value) if value and value != "NA" else None
        except (ValueError, TypeError):
            return None
    
    def _analyze_cbc_patterns(self, parameters: Dict) -> List[Dict]:
        """Detect patterns in Complete Blood Count parameters"""
        patterns = []
        
        # Pattern 1: Multiple CBC abnormalities
        cbc_abnormal = []
        for param_name in self.cbc_parameters:
            if param_name in parameters:
                classification = parameters[param_name]["classification"]
                if classification in ["Low", "High"]:
                    cbc_abnormal.append({
                        "name": parameters[param_name]["name"],
                        "status": classification
                    })
        
        if len(cbc_abnormal) >= 3:
            patterns.append({
                "type": "cbc_multiple_abnormalities",
                "description": f"Multiple CBC abnormalities detected across {len(cbc_abnormal)} parameters",
                "parameters_involved": cbc_abnormal,
                "severity": "High" if len(cbc_abnormal) >= 5 else "Moderate"
            })
        
        # Pattern 2: Red cell indices coordination
        rbc_params = ["hemoglobin", "hematocrit", "rbc count"]
        rbc_abnormal = [p for p in rbc_params if p in parameters and 
                       parameters[p]["classification"] in ["Low", "High"]]
        
        if len(rbc_abnormal) >= 2:
            patterns.append({
                "type": "rbc_coordinated_abnormality",
                "description": f"Coordinated red blood cell parameter abnormalities in {len(rbc_abnormal)} indices",
                "parameters_involved": [{"name": parameters[p]["name"], 
                                       "status": parameters[p]["classification"]} for p in rbc_abnormal],
                "severity": "Moderate"
            })
        
        return patterns
    
    def _analyze_wbc_distribution_patterns(self, parameters: Dict) -> List[Dict]:
        """Detect white blood cell distribution imbalances"""
        patterns = []
        
        wbc_differential = ["neutrophils", "lymphocytes", "monocytes", "eosinophils", "basophils"]
        wbc_abnormal = []
        
        for param_name in wbc_differential:
            if param_name in parameters:
                classification = parameters[param_name]["classification"]
                if classification in ["Low", "High"]:
                    wbc_abnormal.append({
                        "name": parameters[param_name]["name"],
                        "status": classification,
                        "value": parameters[param_name]["value"]
                    })
        
        # Pattern: WBC distribution imbalance
        if len(wbc_abnormal) >= 2:
            # Check for opposing patterns (e.g., neutrophils low + lymphocytes high)
            low_count = sum(1 for p in wbc_abnormal if p["status"] == "Low")
            high_count = sum(1 for p in wbc_abnormal if p["status"] == "High")
            
            if low_count > 0 and high_count > 0:
                patterns.append({
                    "type": "wbc_distribution_imbalance",
                    "description": f"White blood cell distribution imbalance with {low_count} low and {high_count} elevated parameters",
                    "parameters_involved": wbc_abnormal,
                    "severity": "Moderate"
                })
            elif len(wbc_abnormal) >= 3:
                patterns.append({
                    "type": "wbc_multiple_abnormalities",
                    "description": f"Multiple white blood cell differential abnormalities across {len(wbc_abnormal)} cell types",
                    "parameters_involved": wbc_abnormal,
                    "severity": "Moderate"
                })
        
        return patterns
    
    def _analyze_lipid_patterns(self, parameters: Dict) -> List[Dict]:
        """Detect lipid profile patterns and ratios"""
        patterns = []
        
        # Pattern 1: Multiple lipid abnormalities
        lipid_abnormal = []
        for param_name in self.lipid_parameters:
            if param_name in parameters:
                classification = parameters[param_name]["classification"]
                if classification in ["Low", "High"]:
                    lipid_abnormal.append({
                        "name": parameters[param_name]["name"],
                        "status": classification
                    })
        
        if len(lipid_abnormal) >= 2:
            patterns.append({
                "type": "lipid_profile_abnormalities",
                "description": f"Multiple lipid profile abnormalities detected in {len(lipid_abnormal)} parameters",
                "parameters_involved": lipid_abnormal,
                "severity": "Moderate"
            })
        
        # Pattern 2: Cholesterol ratio analysis
        total_chol = parameters.get("total cholesterol", {}).get("numeric_value")
        hdl_chol = parameters.get("hdl cholesterol", {}).get("numeric_value")
        
        if total_chol and hdl_chol and hdl_chol > 0:
            ratio = total_chol / hdl_chol
            if ratio > 5.0:
                patterns.append({
                    "type": "cholesterol_ratio_elevation",
                    "description": f"Elevated total cholesterol to HDL ratio ({ratio:.1f}:1)",
                    "parameters_involved": [
                        {"name": "Total Cholesterol", "value": str(total_chol)},
                        {"name": "HDL Cholesterol", "value": str(hdl_chol)}
                    ],
                    "severity": "High" if ratio > 6.0 else "Moderate"
                })
        
        return patterns
    
    def _analyze_rbc_index_patterns(self, parameters: Dict) -> List[Dict]:
        """Detect red blood cell index patterns"""
        patterns = []
        
        rbc_indices = ["mcv", "mch", "mchc", "rdw"]
        rbc_index_abnormal = []
        
        for param_name in rbc_indices:
            if param_name in parameters:
                classification = parameters[param_name]["classification"]
                if classification in ["Low", "High"]:
                    rbc_index_abnormal.append({
                        "name": parameters[param_name]["name"],
                        "status": classification
                    })
        
        if len(rbc_index_abnormal) >= 2:
            patterns.append({
                "type": "rbc_index_abnormalities",
                "description": f"Red blood cell index abnormalities across {len(rbc_index_abnormal)} parameters",
                "parameters_involved": rbc_index_abnormal,
                "severity": "Moderate"
            })
        
        return patterns
    
    def _analyze_cross_system_patterns(self, parameters: Dict) -> List[Dict]:
        """Detect patterns across different organ systems"""
        patterns = []
        
        # Count abnormalities by system
        system_abnormalities = {
            "cbc": 0,
            "lipid": 0,
            "liver": 0,
            "kidney": 0
        }
        
        for param_name, param_data in parameters.items():
            if param_data["classification"] in ["Low", "High"]:
                if param_name in self.cbc_parameters:
                    system_abnormalities["cbc"] += 1
                elif param_name in self.lipid_parameters:
                    system_abnormalities["lipid"] += 1
                elif param_name in self.liver_parameters:
                    system_abnormalities["liver"] += 1
                elif param_name in self.kidney_parameters:
                    system_abnormalities["kidney"] += 1
        
        # Pattern: Multi-system involvement
        affected_systems = [system for system, count in system_abnormalities.items() if count > 0]
        
        if len(affected_systems) >= 3:
            patterns.append({
                "type": "multi_system_abnormalities",
                "description": f"Abnormalities detected across {len(affected_systems)} organ systems",
                "parameters_involved": [{"system": system, "abnormal_count": system_abnormalities[system]} 
                                      for system in affected_systems],
                "severity": "High"
            })
        
        return patterns
    
    def _assess_risk_from_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Assess overall risk level based on detected patterns"""
        
        if not patterns:
            return {
                "risk_level": "Low",
                "reasoning": ["No significant patterns detected across parameter combinations"]
            }
        
        # Count patterns by severity
        high_severity = sum(1 for p in patterns if p.get("severity") == "High")
        moderate_severity = sum(1 for p in patterns if p.get("severity") == "Moderate")
        
        reasoning = []
        
        if high_severity > 0:
            risk_level = "High"
            reasoning.append(f"{high_severity} high-severity pattern(s) detected")
            if moderate_severity > 0:
                reasoning.append(f"Additional {moderate_severity} moderate-severity pattern(s) present")
        elif moderate_severity >= 2:
            risk_level = "High"
            reasoning.append(f"Multiple moderate-severity patterns ({moderate_severity}) indicate elevated risk")
        elif moderate_severity == 1:
            risk_level = "Moderate"
            reasoning.append("Single moderate-severity pattern detected")
        else:
            risk_level = "Low"
            reasoning.append("Patterns detected but of low clinical significance")
        
        # Add pattern-specific reasoning
        pattern_types = [p["type"] for p in patterns]
        if "multi_system_abnormalities" in pattern_types:
            reasoning.append("Multi-system involvement increases overall risk")
        if "wbc_distribution_imbalance" in pattern_types:
            reasoning.append("White blood cell distribution imbalance noted")
        if "cholesterol_ratio_elevation" in pattern_types:
            reasoning.append("Elevated cholesterol ratios contribute to cardiovascular risk")
        
        return {
            "risk_level": risk_level,
            "reasoning": reasoning
        }


class Model3ContextualAnalysis:
    """
    Medical Context Analysis Assistant
    
    Uses ONLY age and gender extracted from blood report text.
    Does NOT ask user for information or assume missing details.
    Refines Model 1 and Model 2 interpretations ONLY when demographics meaningfully affect risk.
    """
    
    def __init__(self):
        # Age-specific risk modifications (evidence-based only)
        self.age_risk_modifiers = {
            "cholesterol": {
                "elderly": "Cardiovascular risk interpretation differs in patients >65 years",
                "young_adult": "Early lipid abnormalities may indicate genetic predisposition"
            },
            "hemoglobin": {
                "elderly": "Lower hemoglobin may be physiologically normal in elderly patients",
                "pediatric": "Pediatric hemoglobin ranges differ significantly from adult values"
            },
            "glucose": {
                "elderly": "Diabetes risk increases significantly with age",
                "middle_age": "Prediabetes screening becomes critical after age 45"
            }
        }
        
        # Gender-specific risk modifications (evidence-based only)
        self.gender_risk_modifiers = {
            "hemoglobin": {
                "female": "Female reference ranges are physiologically lower than male ranges",
                "male": "Male hemoglobin levels are typically higher due to testosterone effects"
            },
            "iron": {
                "female": "Iron deficiency more common in premenopausal females due to menstruation"
            },
            "cholesterol": {
                "female": "Postmenopausal females have increased cardiovascular risk",
                "male": "Males have earlier onset of cardiovascular risk"
            }
        }
    
    def analyze_context_from_csv(self, model1_result: Dict, model2_result: Dict, 
                               csv_content: str) -> Dict[str, Any]:
        """
        Medical context analysis using ONLY demographics that might be in CSV data
        
        Rules:
        - Use ONLY age/gender from CSV data if present
        - Do NOT ask user for information
        - Do NOT assume missing details
        - Say "Context not available" if demographics missing
        - Refine interpretations ONLY when demographics meaningfully affect risk
        - Do NOT diagnose diseases or recommend medications
        - Output JSON only
        """
        
        # Extract demographics from CSV content if present
        demographics = self._extract_demographics_from_csv(csv_content)
        
        # If no demographics found in CSV, return unavailable status
        if not demographics["age"] and not demographics["gender"]:
            return {
                "context_status": "Context not available",
                "reason": "Age and gender not found in CSV data",
                "demographic_info": {
                    "age_extracted": False,
                    "gender_extracted": False,
                    "source": "csv_data_only"
                },
                "risk_refinements": [],
                "context_notes": []
            }
        
        # Analyze context only for available demographics
        risk_refinements = []
        context_notes = []
        
        # Extract abnormal parameters from Model 1
        abnormal_parameters = self._extract_abnormal_parameters(model1_result)
        
        # Extract high-risk patterns from Model 2
        high_risk_patterns = self._extract_high_risk_patterns(model2_result)
        
        # Apply age-based risk refinements (only if age meaningfully affects interpretation)
        if demographics["age"]:
            age_refinements = self._apply_age_risk_refinements(
                abnormal_parameters, high_risk_patterns, demographics["age"]
            )
            risk_refinements.extend(age_refinements)
        
        # Apply gender-based risk refinements (only if gender meaningfully affects interpretation)
        if demographics["gender"]:
            gender_refinements = self._apply_gender_risk_refinements(
                abnormal_parameters, high_risk_patterns, demographics["gender"]
            )
            risk_refinements.extend(gender_refinements)
        
        # Generate context notes only for meaningful refinements
        if risk_refinements:
            context_notes = self._generate_evidence_based_context_notes(risk_refinements)
        
        return {
            "context_status": "Available" if risk_refinements else "Limited impact",
            "demographic_info": {
                "age_extracted": demographics["age"] is not None,
                "gender_extracted": demographics["gender"] is not None,
                "age_value": demographics["age"],
                "gender_value": demographics["gender"],
                "source": "csv_data_only"
            },
            "risk_refinements": risk_refinements,
            "context_notes": context_notes,
            "medical_disclaimer": "Context analysis for informational purposes only. Does not constitute medical diagnosis or treatment recommendations."
        }
    
    def _extract_demographics_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """Extract age and gender from CSV data if present"""
        import pandas as pd
        import io
        
        demographics = {"age": None, "gender": None}
        
        if not csv_content:
            return demographics
        
        try:
            # Parse CSV to look for demographic columns
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Look for age in various column names
            age_columns = ['age', 'Age', 'AGE', 'patient_age', 'Patient_Age']
            for col in age_columns:
                if col in df.columns:
                    age_values = df[col].dropna()
                    if not age_values.empty:
                        try:
                            age_value = int(age_values.iloc[0])
                            if 0 <= age_value <= 120:
                                demographics["age"] = age_value
                                break
                        except (ValueError, TypeError):
                            continue
            
            # Look for gender in various column names
            gender_columns = ['gender', 'Gender', 'GENDER', 'sex', 'Sex', 'SEX', 'patient_gender']
            for col in gender_columns:
                if col in df.columns:
                    gender_values = df[col].dropna()
                    if not gender_values.empty:
                        gender_value = str(gender_values.iloc[0]).upper()
                        if gender_value in ['M', 'MALE', 'MAN']:
                            demographics["gender"] = "Male"
                            break
                        elif gender_value in ['F', 'FEMALE', 'WOMAN']:
                            demographics["gender"] = "Female"
                            break
        
        except Exception:
            # If CSV parsing fails, return empty demographics
            pass
        
        return demographics
    
    def _extract_abnormal_parameters(self, model1_result: Dict) -> List[Dict]:
        """Extract abnormal parameters from Model 1 results"""
        abnormal_params = []
        
        for interpretation in model1_result.get("interpretations", []):
            if interpretation.get("classification") in ["Low", "High", "Borderline"]:
                abnormal_params.append({
                    "parameter": interpretation.get("test_name", "").lower(),
                    "classification": interpretation.get("classification"),
                    "value": interpretation.get("value"),
                    "reference_range": interpretation.get("reference_range")
                })
        
        return abnormal_params
    
    def _extract_high_risk_patterns(self, model2_result: Dict) -> List[str]:
        """Extract high-risk patterns from Model 2 results"""
        patterns = model2_result.get("patterns_detected", [])
        return [pattern for pattern in patterns if "high" in pattern.lower() or "elevated" in pattern.lower()]
    
    def _apply_age_risk_refinements(self, abnormal_parameters: List[Dict], 
                                  high_risk_patterns: List[str], age: int) -> List[Dict]:
        """Apply age-based risk refinements only when clinically meaningful"""
        refinements = []
        
        age_group = self._classify_age_group(age)
        
        for param in abnormal_parameters:
            param_name = param["parameter"]
            classification = param["classification"]
            
            # Only refine if age meaningfully affects risk interpretation
            if param_name in self.age_risk_modifiers:
                if age_group in self.age_risk_modifiers[param_name]:
                    refinements.append({
                        "parameter": param_name,
                        "original_classification": classification,
                        "age_context": self.age_risk_modifiers[param_name][age_group],
                        "refinement_type": "age_based",
                        "clinical_significance": "meaningful"
                    })
        
        return refinements
    
    def _apply_gender_risk_refinements(self, abnormal_parameters: List[Dict], 
                                     high_risk_patterns: List[str], gender: str) -> List[Dict]:
        """Apply gender-based risk refinements only when clinically meaningful"""
        refinements = []
        
        gender_key = gender.lower()
        
        for param in abnormal_parameters:
            param_name = param["parameter"]
            classification = param["classification"]
            
            # Only refine if gender meaningfully affects risk interpretation
            if param_name in self.gender_risk_modifiers:
                if gender_key in self.gender_risk_modifiers[param_name]:
                    refinements.append({
                        "parameter": param_name,
                        "original_classification": classification,
                        "gender_context": self.gender_risk_modifiers[param_name][gender_key],
                        "refinement_type": "gender_based",
                        "clinical_significance": "meaningful"
                    })
        
        return refinements
    
    def _generate_evidence_based_context_notes(self, refinements: List[Dict]) -> List[str]:
        """Generate evidence-based context notes for meaningful refinements only"""
        notes = []
        
        for refinement in refinements:
            if refinement["refinement_type"] == "age_based":
                notes.append(f"{refinement['parameter'].title()}: {refinement['age_context']}")
            elif refinement["refinement_type"] == "gender_based":
                notes.append(f"{refinement['parameter'].title()}: {refinement['gender_context']}")
        
        return notes
    
    def _classify_age_group(self, age: int) -> str:
        """Classify age into clinically relevant groups"""
        if age < 18:
            return "pediatric"
        elif age < 45:
            return "young_adult"
        elif age < 65:
            return "middle_age"
        else:
            return "elderly"


class Milestone2Integration:
    """
    Integration class for Milestone-2 models
    Coordinates Model-2 and Model-3 with existing Phase-1 outputs
    """
    
    def __init__(self):
        self.model2 = Model2PatternRecognition()
        self.model3 = Model3ContextualAnalysis()
    
    def process_milestone2(self, model1_result: Dict, csv_content: str = "", 
                          age: Optional[int] = None, gender: Optional[str] = None) -> Dict[str, Any]:
        """
        Process Milestone-2 analysis pipeline with proper medical context analysis
        
        Pipeline: Phase-1 → Model-2 → Model-3 (from CSV data) → Integration
        """
        
        # Model-2: Pattern Recognition & Risk Assessment
        model2_result = self.model2.analyze_patterns(model1_result)
        
        # Model-3: Medical Context Analysis using ONLY demographics from CSV data
        # This follows the medical context analysis rules:
        # - Use ONLY age/gender from CSV data if present
        # - Do NOT ask user for information
        # - Say "Context not available" if demographics missing from CSV
        model3_result = self.model3.analyze_context_from_csv(model1_result, model2_result, csv_content)
        
        # Integration and synthesis
        integrated_result = self._synthesize_milestone2_results(
            model1_result, model2_result, model3_result
        )
        
        return integrated_result
    
    def _synthesize_milestone2_results(self, model1_result: Dict, model2_result: Dict, 
                                     model3_result: Dict) -> Dict[str, Any]:
        """Synthesize all Milestone-2 results without contradicting Phase-1"""
        
        return {
            "milestone2_analysis": {
                "model1_summary": {
                    "total_parameters": model1_result.get("summary", {}).get("total_parameters", 0),
                    "abnormal_parameters": model1_result.get("summary", {}).get("abnormal_count", 0),
                    "authority": "Phase-1 classifications remain authoritative for individual parameters"
                },
                "model2_patterns": {
                    "patterns_detected": model2_result.get("patterns_detected", []),
                    "risk_level": model2_result.get("risk_level", "Low"),
                    "risk_reasoning": model2_result.get("risk_reasoning", []),
                    "total_patterns": model2_result.get("total_patterns", 0)
                },
                "model3_context": {
                    "context_status": model3_result.get("context_status", "Context not available"),
                    "context_notes": model3_result.get("context_notes", []),
                    "risk_refinements": model3_result.get("risk_refinements", []),
                    "demographic_info": model3_result.get("demographic_info", {}),
                    "medical_disclaimer": model3_result.get("medical_disclaimer", "")
                },
                "integration_notes": [
                    "Model-2 patterns are derived from Phase-1 parameter combinations",
                    "Model-3 context does not override Phase-1 individual parameter classifications",
                    "Risk assessment is based on detected patterns, not individual parameter values"
                ]
            },
            "detailed_results": {
                "model1_result": model1_result,
                "model2_result": model2_result,
                "model3_result": model3_result
            }
        }