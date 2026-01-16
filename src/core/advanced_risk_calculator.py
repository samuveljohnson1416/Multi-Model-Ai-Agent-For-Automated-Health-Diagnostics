"""
Advanced Risk Calculator Module
Implements Framingham CVD Risk, Lipid Ratios, and Metabolic Syndrome Detection
"""

from typing import Dict, Optional, List
import math


class AdvancedRiskCalculator:
    """
    Calculates advanced cardiovascular and metabolic risk scores.
    """
    
    def __init__(self):
        # Framingham point tables for men
        self.male_age_points = {
            (20, 34): -9, (35, 39): -4, (40, 44): 0, (45, 49): 3,
            (50, 54): 6, (55, 59): 8, (60, 64): 10, (65, 69): 11,
            (70, 74): 12, (75, 79): 13
        }
        
        # Framingham point tables for women
        self.female_age_points = {
            (20, 34): -7, (35, 39): -3, (40, 44): 0, (45, 49): 3,
            (50, 54): 6, (55, 59): 8, (60, 64): 10, (65, 69): 12,
            (70, 74): 14, (75, 79): 16
        }
        
        # Total cholesterol points by age group (male)
        self.male_tc_points = {
            (20, 39): {(0, 159): 0, (160, 199): 4, (200, 239): 7, (240, 279): 9, (280, 999): 11},
            (40, 49): {(0, 159): 0, (160, 199): 3, (200, 239): 5, (240, 279): 6, (280, 999): 8},
            (50, 59): {(0, 159): 0, (160, 199): 2, (200, 239): 3, (240, 279): 4, (280, 999): 5},
            (60, 69): {(0, 159): 0, (160, 199): 1, (200, 239): 1, (240, 279): 2, (280, 999): 3},
            (70, 79): {(0, 159): 0, (160, 199): 0, (200, 239): 0, (240, 279): 1, (280, 999): 1}
        }
        
        # Total cholesterol points by age group (female)
        self.female_tc_points = {
            (20, 39): {(0, 159): 0, (160, 199): 4, (200, 239): 8, (240, 279): 11, (280, 999): 13},
            (40, 49): {(0, 159): 0, (160, 199): 3, (200, 239): 6, (240, 279): 8, (280, 999): 10},
            (50, 59): {(0, 159): 0, (160, 199): 2, (200, 239): 4, (240, 279): 5, (280, 999): 7},
            (60, 69): {(0, 159): 0, (160, 199): 1, (200, 239): 2, (240, 279): 3, (280, 999): 4},
            (70, 79): {(0, 159): 0, (160, 199): 1, (200, 239): 1, (240, 279): 2, (280, 999): 2}
        }

        # HDL points (same for both genders)
        self.hdl_points = {
            (60, 999): -1, (50, 59): 0, (40, 49): 1, (0, 39): 2
        }
        
        # Smoking points by age (male)
        self.male_smoking_points = {
            (20, 39): 8, (40, 49): 5, (50, 59): 3, (60, 69): 1, (70, 79): 1
        }
        
        # Smoking points by age (female)
        self.female_smoking_points = {
            (20, 39): 9, (40, 49): 7, (50, 59): 4, (60, 69): 2, (70, 79): 1
        }
        
        # Risk percentage by total points (male)
        self.male_risk_percent = {
            0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 4,
            9: 5, 10: 6, 11: 8, 12: 10, 13: 12, 14: 16, 15: 20, 16: 25, 17: 30
        }
        
        # Risk percentage by total points (female)
        self.female_risk_percent = {
            9: 1, 10: 1, 11: 1, 12: 1, 13: 2, 14: 2, 15: 3, 16: 4,
            17: 5, 18: 6, 19: 8, 20: 11, 21: 14, 22: 17, 23: 22, 24: 27, 25: 30
        }

    def _get_age_range_points(self, age: int, points_table: dict) -> int:
        """Get points for age from a range-based table"""
        for (min_age, max_age), points in points_table.items():
            if min_age <= age <= max_age:
                return points
        return 0

    def _get_tc_points(self, age: int, tc: float, gender: str) -> int:
        """Get total cholesterol points based on age and gender"""
        table = self.male_tc_points if gender.lower() == 'male' else self.female_tc_points
        
        # Find age group
        age_group = None
        for age_range in table.keys():
            if age_range[0] <= age <= age_range[1]:
                age_group = age_range
                break
        
        if not age_group:
            age_group = (70, 79) if age >= 70 else (20, 39)
        
        # Find TC range
        for tc_range, points in table[age_group].items():
            if tc_range[0] <= tc <= tc_range[1]:
                return points
        return 0

    def _get_hdl_points(self, hdl: float) -> int:
        """Get HDL points"""
        for (min_hdl, max_hdl), points in self.hdl_points.items():
            if min_hdl <= hdl <= max_hdl:
                return points
        return 0

    def _get_smoking_points(self, age: int, gender: str) -> int:
        """Get smoking points based on age and gender"""
        table = self.male_smoking_points if gender.lower() == 'male' else self.female_smoking_points
        for (min_age, max_age), points in table.items():
            if min_age <= age <= max_age:
                return points
        return 1

    def calculate_framingham_risk(self, parameters: Dict, context: Dict) -> Dict:
        """
        Calculate 10-year cardiovascular disease risk using Framingham Risk Score.
        """
        age = context.get('age', 50)
        gender = context.get('gender', 'Male')
        is_smoker = context.get('lifestyle', {}).get('smoker', False)
        has_hypertension = 'Hypertension' in context.get('medical_history', [])
        is_treated_bp = context.get('treated_bp', False)
        
        # Get cholesterol values
        tc = parameters.get('Cholesterol', {}).get('value', 200)
        hdl = parameters.get('HDL', {}).get('value', 50)
        
        # Calculate points
        total_points = 0
        point_breakdown = {}
        
        # Age points
        age_table = self.male_age_points if gender.lower() == 'male' else self.female_age_points
        age_pts = self._get_age_range_points(age, age_table)
        point_breakdown['age'] = age_pts
        total_points += age_pts
        
        # Total cholesterol points
        tc_pts = self._get_tc_points(age, tc, gender)
        point_breakdown['total_cholesterol'] = tc_pts
        total_points += tc_pts
        
        # HDL points
        hdl_pts = self._get_hdl_points(hdl)
        point_breakdown['hdl'] = hdl_pts
        total_points += hdl_pts
        
        # Smoking points
        if is_smoker:
            smoke_pts = self._get_smoking_points(age, gender)
            point_breakdown['smoking'] = smoke_pts
            total_points += smoke_pts
        else:
            point_breakdown['smoking'] = 0
        
        # Blood pressure points (simplified)
        if has_hypertension:
            bp_pts = 2 if is_treated_bp else 1
            point_breakdown['blood_pressure'] = bp_pts
            total_points += bp_pts
        else:
            point_breakdown['blood_pressure'] = 0
        
        # Get risk percentage
        risk_table = self.male_risk_percent if gender.lower() == 'male' else self.female_risk_percent
        
        if total_points < min(risk_table.keys()):
            risk_percent = 1
        elif total_points > max(risk_table.keys()):
            risk_percent = 30
        else:
            risk_percent = risk_table.get(total_points, 10)
        
        # Determine risk category
        if risk_percent < 10:
            risk_category = 'Low'
        elif risk_percent < 20:
            risk_category = 'Moderate'
        else:
            risk_category = 'High'
        
        return {
            'total_points': total_points,
            'point_breakdown': point_breakdown,
            'risk_percent': risk_percent,
            'risk_category': risk_category,
            'interpretation': f"{risk_percent}% chance of cardiovascular event in next 10 years",
            'factors_considered': {
                'age': age,
                'gender': gender,
                'total_cholesterol': tc,
                'hdl': hdl,
                'smoker': is_smoker,
                'hypertension': has_hypertension
            }
        }

    def calculate_lipid_ratios(self, parameters: Dict) -> Dict:
        """
        Calculate lipid panel ratios for cardiovascular risk assessment.
        """
        tc = parameters.get('Cholesterol', {}).get('value')
        hdl = parameters.get('HDL', {}).get('value')
        ldl = parameters.get('LDL', {}).get('value')
        tg = parameters.get('Triglycerides', {}).get('value')
        
        ratios = {}
        
        # TC/HDL Ratio (Castelli Risk Index I)
        if tc and hdl and hdl > 0:
            tc_hdl = round(tc / hdl, 1)
            ratios['tc_hdl_ratio'] = {
                'value': tc_hdl,
                'name': 'TC/HDL Ratio',
                'optimal': '< 4.5 (men), < 4.0 (women)',
                'risk': 'Low' if tc_hdl < 4.5 else 'Moderate' if tc_hdl < 5.5 else 'High',
                'interpretation': 'Lower is better. High ratio indicates increased CVD risk.'
            }
        
        # LDL/HDL Ratio (Castelli Risk Index II)
        if ldl and hdl and hdl > 0:
            ldl_hdl = round(ldl / hdl, 1)
            ratios['ldl_hdl_ratio'] = {
                'value': ldl_hdl,
                'name': 'LDL/HDL Ratio',
                'optimal': '< 3.0 (men), < 2.5 (women)',
                'risk': 'Low' if ldl_hdl < 3.0 else 'Moderate' if ldl_hdl < 4.0 else 'High',
                'interpretation': 'Lower is better. Indicates balance between bad and good cholesterol.'
            }
        
        # TG/HDL Ratio (Insulin Resistance Marker)
        if tg and hdl and hdl > 0:
            tg_hdl = round(tg / hdl, 1)
            ratios['tg_hdl_ratio'] = {
                'value': tg_hdl,
                'name': 'TG/HDL Ratio',
                'optimal': '< 2.0',
                'risk': 'Low' if tg_hdl < 2.0 else 'Moderate' if tg_hdl < 4.0 else 'High',
                'interpretation': 'Marker for insulin resistance and small dense LDL particles.'
            }
        
        # Non-HDL Cholesterol
        if tc and hdl:
            non_hdl = round(tc - hdl, 1)
            ratios['non_hdl'] = {
                'value': non_hdl,
                'name': 'Non-HDL Cholesterol',
                'optimal': '< 130 mg/dL',
                'risk': 'Low' if non_hdl < 130 else 'Moderate' if non_hdl < 160 else 'High',
                'interpretation': 'Includes all atherogenic particles. Target < 130 mg/dL.'
            }
        
        # Atherogenic Index of Plasma (AIP)
        if tg and hdl and hdl > 0 and tg > 0:
            aip = round(math.log10(tg / hdl), 2)
            ratios['aip'] = {
                'value': aip,
                'name': 'Atherogenic Index of Plasma',
                'optimal': '< 0.11',
                'risk': 'Low' if aip < 0.11 else 'Moderate' if aip < 0.21 else 'High',
                'interpretation': 'Predicts cardiovascular risk. Lower values indicate lower risk.'
            }
        
        # Overall lipid risk assessment
        risk_scores = [r.get('risk', 'Low') for r in ratios.values()]
        high_count = risk_scores.count('High')
        mod_count = risk_scores.count('Moderate')
        
        if high_count >= 2:
            overall = 'High'
        elif high_count >= 1 or mod_count >= 2:
            overall = 'Moderate'
        else:
            overall = 'Low'
        
        return {
            'ratios': ratios,
            'overall_lipid_risk': overall,
            'recommendations': self._get_lipid_recommendations(ratios, overall)
        }

    def _get_lipid_recommendations(self, ratios: Dict, overall_risk: str) -> List[str]:
        """Generate recommendations based on lipid ratios"""
        recommendations = []
        
        if overall_risk == 'High':
            recommendations.append("Consult a cardiologist for comprehensive cardiovascular assessment")
            recommendations.append("Consider lipid-lowering therapy if not already prescribed")
        
        if ratios.get('tc_hdl_ratio', {}).get('risk') in ['Moderate', 'High']:
            recommendations.append("Focus on increasing HDL through exercise and healthy fats")
        
        if ratios.get('tg_hdl_ratio', {}).get('risk') in ['Moderate', 'High']:
            recommendations.append("Reduce refined carbohydrates and sugars to improve TG/HDL ratio")
            recommendations.append("Consider screening for insulin resistance or metabolic syndrome")
        
        if ratios.get('non_hdl', {}).get('risk') in ['Moderate', 'High']:
            recommendations.append("Reduce saturated fat intake and increase fiber consumption")
        
        if not recommendations:
            recommendations.append("Maintain current healthy lifestyle")
            recommendations.append("Continue regular lipid monitoring annually")
        
        return recommendations

    def detect_metabolic_syndrome(self, parameters: Dict, context: Dict) -> Dict:
        """
        Detect Metabolic Syndrome using NCEP ATP III criteria.
        Requires 3 or more of 5 criteria to be met.
        """
        criteria_met = 0
        criteria_details = []
        
        gender = context.get('gender', 'Male').lower()
        medical_history = context.get('medical_history', [])
        
        # Criterion 1: Elevated Waist Circumference (using BMI as proxy if waist not available)
        waist = context.get('waist_circumference')
        if waist:
            if (gender == 'male' and waist >= 102) or (gender == 'female' and waist >= 88):
                criteria_met += 1
                criteria_details.append({
                    'criterion': 'Abdominal Obesity',
                    'met': True,
                    'value': f"{waist} cm",
                    'threshold': '≥102 cm (men), ≥88 cm (women)'
                })
            else:
                criteria_details.append({
                    'criterion': 'Abdominal Obesity',
                    'met': False,
                    'value': f"{waist} cm",
                    'threshold': '≥102 cm (men), ≥88 cm (women)'
                })
        
        # Criterion 2: Elevated Triglycerides
        tg = parameters.get('Triglycerides', {}).get('value')
        if tg:
            if tg >= 150:
                criteria_met += 1
                criteria_details.append({
                    'criterion': 'Elevated Triglycerides',
                    'met': True,
                    'value': f"{tg} mg/dL",
                    'threshold': '≥150 mg/dL'
                })
            else:
                criteria_details.append({
                    'criterion': 'Elevated Triglycerides',
                    'met': False,
                    'value': f"{tg} mg/dL",
                    'threshold': '≥150 mg/dL'
                })
        
        # Criterion 3: Reduced HDL
        hdl = parameters.get('HDL', {}).get('value')
        if hdl:
            hdl_threshold = 40 if gender == 'male' else 50
            if hdl < hdl_threshold:
                criteria_met += 1
                criteria_details.append({
                    'criterion': 'Low HDL Cholesterol',
                    'met': True,
                    'value': f"{hdl} mg/dL",
                    'threshold': f'<{hdl_threshold} mg/dL'
                })
            else:
                criteria_details.append({
                    'criterion': 'Low HDL Cholesterol',
                    'met': False,
                    'value': f"{hdl} mg/dL",
                    'threshold': f'<{hdl_threshold} mg/dL'
                })
        
        # Criterion 4: Elevated Blood Pressure (using history)
        if 'Hypertension' in medical_history or 'High Blood Pressure' in medical_history:
            criteria_met += 1
            criteria_details.append({
                'criterion': 'Elevated Blood Pressure',
                'met': True,
                'value': 'History of Hypertension',
                'threshold': '≥130/85 mmHg or on treatment'
            })
        else:
            criteria_details.append({
                'criterion': 'Elevated Blood Pressure',
                'met': False,
                'value': 'No hypertension history',
                'threshold': '≥130/85 mmHg or on treatment'
            })
        
        # Criterion 5: Elevated Fasting Glucose
        glucose = parameters.get('Glucose', {}).get('value')
        has_diabetes = 'Diabetes' in medical_history or 'Type 2 Diabetes' in medical_history
        
        if glucose and glucose >= 100:
            criteria_met += 1
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': True,
                'value': f"{glucose} mg/dL",
                'threshold': '≥100 mg/dL or on treatment'
            })
        elif has_diabetes:
            criteria_met += 1
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': True,
                'value': 'Diabetes diagnosis',
                'threshold': '≥100 mg/dL or on treatment'
            })
        else:
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': False,
                'value': f"{glucose} mg/dL" if glucose else 'Not available',
                'threshold': '≥100 mg/dL or on treatment'
            })
        
        has_syndrome = criteria_met >= 3
        
        return {
            'has_metabolic_syndrome': has_syndrome,
            'criteria_met': criteria_met,
            'criteria_required': 3,
            'criteria_details': criteria_details,
            'risk_level': 'High' if has_syndrome else 'Low',
            'recommendations': self._get_metabolic_recommendations(has_syndrome, criteria_details)
        }

    def _get_metabolic_recommendations(self, has_syndrome: bool, criteria: List[Dict]) -> List[str]:
        """Generate recommendations for metabolic syndrome"""
        recommendations = []
        
        if has_syndrome:
            recommendations.append("⚠️ Metabolic Syndrome detected - consult healthcare provider")
            recommendations.append("Lifestyle modifications are first-line treatment")
            recommendations.append("Target 7-10% weight loss if overweight")
            recommendations.append("150+ minutes of moderate exercise per week")
            recommendations.append("Follow Mediterranean or DASH diet pattern")
        
        for criterion in criteria:
            if criterion['met']:
                if 'Triglycerides' in criterion['criterion']:
                    recommendations.append("Reduce refined carbs and alcohol to lower triglycerides")
                elif 'HDL' in criterion['criterion']:
                    recommendations.append("Increase aerobic exercise to raise HDL")
                elif 'Glucose' in criterion['criterion']:
                    recommendations.append("Monitor blood sugar regularly; consider diabetes screening")
        
        if not has_syndrome:
            recommendations.append("✅ No metabolic syndrome detected")
            recommendations.append("Continue healthy lifestyle to maintain metabolic health")
        
        return recommendations


def calculate_all_advanced_risks(parameters: Dict, context: Dict) -> Dict:
    """
    Calculate all advanced risk scores.
    Convenience function that runs all calculations.
    """
    calculator = AdvancedRiskCalculator()
    
    return {
        'framingham_risk': calculator.calculate_framingham_risk(parameters, context),
        'lipid_ratios': calculator.calculate_lipid_ratios(parameters),
        'metabolic_syndrome': calculator.detect_metabolic_syndrome(parameters, context)
    }
