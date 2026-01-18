"""
Automated Test Suite for Blood Report Analysis System
Tests parameter classification, unit conversion, dynamic reference ranges,
lipid ratios, Framingham risk score, and metabolic syndrome detection.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.unit_converter import UnitConverter, convert_to_standard_unit, convert_units
from src.core.dynamic_reference_ranges import DynamicReferenceRanges, validate_parameter_dynamic, get_dynamic_reference
from src.core.advanced_risk_calculator import AdvancedRiskCalculator


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_result(self, name, passed, details=""):
        self.tests.append({
            'name': name,
            'passed': passed,
            'details': details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    @property
    def total_tests(self):
        return self.passed + self.failed
    
    @property
    def accuracy(self):
        if self.total_tests == 0:
            return 0
        return round((self.passed / self.total_tests) * 100, 1)


def test_unit_conversions():
    """Test unit conversion accuracy"""
    results = TestResults()
    converter = UnitConverter()
    
    # Test 1: Glucose mmol/L to mg/dL
    converted, _ = convert_units(5.5, 'mmol/L', 'mg/dL', 'Glucose')
    expected = 99.1  # 5.5 * 18.018
    passed = abs(converted - expected) < 1
    results.add_result("Glucose mmol/L to mg/dL", passed, f"Got {converted}, expected ~{expected}")
    
    # Test 2: Cholesterol mmol/L to mg/dL
    converted, _ = convert_units(5.2, 'mmol/L', 'mg/dL', 'Cholesterol')
    expected = 201.1  # 5.2 * 38.67
    passed = abs(converted - expected) < 5
    results.add_result("Cholesterol mmol/L to mg/dL", passed, f"Got {converted}, expected ~{expected}")
    
    # Test 3: Triglycerides mmol/L to mg/dL
    converted, _ = convert_units(1.7, 'mmol/L', 'mg/dL', 'Triglycerides')
    expected = 150.6  # 1.7 * 88.57
    passed = abs(converted - expected) < 5
    results.add_result("Triglycerides mmol/L to mg/dL", passed, f"Got {converted}, expected ~{expected}")
    
    # Test 4: Hemoglobin g/dL to g/L
    converted, _ = convert_units(14.0, 'g/dL', 'g/L', 'Hemoglobin')
    expected = 140.0
    passed = abs(converted - expected) < 1
    results.add_result("Hemoglobin g/dL to g/L", passed, f"Got {converted}, expected {expected}")
    
    # Test 5: Creatinine mg/dL to umol/L
    converted, _ = convert_units(1.0, 'mg/dL', 'umol/L', 'Creatinine')
    expected = 88.4
    passed = abs(converted - expected) < 1
    results.add_result("Creatinine mg/dL to umol/L", passed, f"Got {converted}, expected {expected}")
    
    return results


def test_dynamic_reference_ranges():
    """Test age/gender adjusted reference ranges"""
    results = TestResults()
    drr = DynamicReferenceRanges()
    
    # Test 1: Hemoglobin for adult male
    ref = drr.get_reference_range('Hemoglobin', age=35, gender='male')
    passed = ref and ref['min'] == 14.0 and ref['max'] == 18.0
    results.add_result("Hemoglobin ref range (male 35)", passed, f"Got {ref}")
    
    # Test 2: Hemoglobin for adult female
    ref = drr.get_reference_range('Hemoglobin', age=35, gender='female')
    passed = ref and ref['min'] == 12.0 and ref['max'] == 16.0
    results.add_result("Hemoglobin ref range (female 35)", passed, f"Got {ref}")
    
    # Test 3: Hemoglobin for elderly male
    ref = drr.get_reference_range('Hemoglobin', age=70, gender='male')
    passed = ref and ref['min'] == 12.5 and ref['max'] == 17.0
    results.add_result("Hemoglobin ref range (male 70)", passed, f"Got {ref}")
    
    # Test 4: Glucose for elderly (relaxed range)
    ref = drr.get_reference_range('Glucose', age=70, gender='male')
    passed = ref and ref['max'] == 110  # Relaxed for elderly
    results.add_result("Glucose ref range (elderly 70)", passed, f"Got {ref}")
    
    # Test 5: Validate parameter - Low hemoglobin for male
    validation = drr.validate_with_dynamic_range('Hemoglobin', 12.0, age=35, gender='male')
    passed = validation['status'] == 'LOW'
    results.add_result("Validate low Hb (male 35)", passed, f"Got {validation['status']}")
    
    # Test 6: Validate parameter - Normal hemoglobin for female
    validation = drr.validate_with_dynamic_range('Hemoglobin', 13.0, age=35, gender='female')
    passed = validation['status'] == 'NORMAL'
    results.add_result("Validate normal Hb (female 35)", passed, f"Got {validation['status']}")
    
    # Test 7: Neutrophils classification
    validation = drr.validate_with_dynamic_range('Neutrophils', 55, age=35, gender='male')
    passed = validation['status'] == 'NORMAL'
    results.add_result("Neutrophils classification", passed, f"Got {validation['status']}")
    
    # Test 8: WBC for child (higher range)
    ref = drr.get_reference_range('WBC', age=8, gender='male')
    passed = ref and ref['max'] == 15000  # Higher for children
    results.add_result("WBC ref range (child 8)", passed, f"Got {ref}")
    
    return results


def test_lipid_ratios():
    """Test lipid panel ratio calculations"""
    results = TestResults()
    calc = AdvancedRiskCalculator()
    
    # Test data
    lipid_data = {
        'total_cholesterol': 220,
        'hdl': 45,
        'ldl': 140,
        'triglycerides': 175
    }
    
    ratios = calc.calculate_lipid_ratios(lipid_data)
    
    # Test 1: TC/HDL ratio
    tc_hdl = ratios.get('tc_hdl_ratio', {}).get('value')
    expected = 220 / 45  # 4.89
    passed = tc_hdl and abs(tc_hdl - expected) < 0.1
    results.add_result("TC/HDL ratio calculation", passed, f"Got {tc_hdl}, expected {expected:.2f}")
    
    # Test 2: LDL/HDL ratio
    ldl_hdl = ratios.get('ldl_hdl_ratio', {}).get('value')
    expected = 140 / 45  # 3.11
    passed = ldl_hdl and abs(ldl_hdl - expected) < 0.1
    results.add_result("LDL/HDL ratio calculation", passed, f"Got {ldl_hdl}, expected {expected:.2f}")
    
    # Test 3: TG/HDL ratio
    tg_hdl = ratios.get('tg_hdl_ratio', {}).get('value')
    expected = 175 / 45  # 3.89
    passed = tg_hdl and abs(tg_hdl - expected) < 0.1
    results.add_result("TG/HDL ratio calculation", passed, f"Got {tg_hdl}, expected {expected:.2f}")
    
    return results


def test_framingham_risk():
    """Test Framingham cardiovascular risk score"""
    results = TestResults()
    calc = AdvancedRiskCalculator()
    
    # Test 1: High risk male (older, smoker, high BP, high cholesterol)
    patient1 = {
        'age': 65,
        'gender': 'male',
        'total_cholesterol': 280,
        'hdl': 35,
        'systolic_bp': 160,
        'bp_treated': False,
        'smoker': True,
        'diabetic': False
    }
    risk1 = calc.calculate_framingham_risk(patient1)
    passed = risk1 and risk1.get('risk_percentage', 0) > 20  # Should be high risk
    results.add_result("Framingham high risk male", passed, f"Got {risk1.get('risk_percentage')}%")
    
    # Test 2: Low risk female (young, non-smoker, normal values)
    patient2 = {
        'age': 40,
        'gender': 'female',
        'total_cholesterol': 180,
        'hdl': 60,
        'systolic_bp': 120,
        'bp_treated': False,
        'smoker': False,
        'diabetic': False
    }
    risk2 = calc.calculate_framingham_risk(patient2)
    passed = risk2 and risk2.get('risk_percentage', 100) < 5  # Should be low risk
    results.add_result("Framingham low risk female", passed, f"Got {risk2.get('risk_percentage')}%")
    
    return results


def test_metabolic_syndrome():
    """Test metabolic syndrome detection"""
    results = TestResults()
    calc = AdvancedRiskCalculator()
    
    # Test 1: Patient WITH metabolic syndrome (3+ criteria)
    patient1 = {
        'waist_circumference': 105,  # >102 for male
        'gender': 'male',
        'triglycerides': 180,  # >150
        'hdl': 35,  # <40 for male
        'systolic_bp': 140,  # >130
        'fasting_glucose': 110  # >100
    }
    result1 = calc.detect_metabolic_syndrome(patient1)
    passed = result1 and result1.get('has_metabolic_syndrome') == True
    results.add_result("Metabolic syndrome detection (positive)", passed, f"Criteria met: {result1.get('criteria_met')}")
    
    # Test 2: Patient WITHOUT metabolic syndrome (<3 criteria)
    patient2 = {
        'waist_circumference': 85,  # Normal
        'gender': 'male',
        'triglycerides': 120,  # Normal
        'hdl': 50,  # Normal
        'systolic_bp': 120,  # Normal
        'fasting_glucose': 90  # Normal
    }
    result2 = calc.detect_metabolic_syndrome(patient2)
    passed = result2 and result2.get('has_metabolic_syndrome') == False
    results.add_result("Metabolic syndrome detection (negative)", passed, f"Criteria met: {result2.get('criteria_met')}")
    
    return results


def test_parameter_classification():
    """Test parameter classification (HIGH/LOW/NORMAL)"""
    results = TestResults()
    drr = DynamicReferenceRanges()
    
    # Test cases: (parameter, value, age, gender, expected_status)
    test_cases = [
        ('Hemoglobin', 15.0, 35, 'male', 'NORMAL'),
        ('Hemoglobin', 10.0, 35, 'male', 'LOW'),
        ('Hemoglobin', 19.0, 35, 'male', 'HIGH'),
        ('Hemoglobin', 13.0, 35, 'female', 'NORMAL'),
        ('Hemoglobin', 11.0, 35, 'female', 'LOW'),
        ('WBC', 7000, 35, 'male', 'NORMAL'),
        ('WBC', 3000, 35, 'male', 'LOW'),
        ('WBC', 15000, 35, 'male', 'HIGH'),
        ('Platelet', 250000, 35, 'male', 'NORMAL'),
        ('Platelet', 100000, 35, 'male', 'LOW'),
        ('Glucose', 85, 35, 'male', 'NORMAL'),
        ('Glucose', 60, 35, 'male', 'LOW'),
        ('Glucose', 130, 35, 'male', 'HIGH'),
        ('Cholesterol', 180, 35, 'male', 'NORMAL'),
        ('Cholesterol', 250, 35, 'male', 'HIGH'),
        ('Neutrophils', 55, 35, 'male', 'NORMAL'),
        ('Neutrophils', 30, 35, 'male', 'LOW'),
        ('Neutrophils', 80, 35, 'male', 'HIGH'),
        ('Lymphocytes', 30, 35, 'male', 'NORMAL'),
        ('Monocytes', 5, 35, 'male', 'NORMAL'),
    ]
    
    for param, value, age, gender, expected in test_cases:
        validation = drr.validate_with_dynamic_range(param, value, age, gender)
        actual = validation.get('status', 'UNKNOWN')
        passed = actual == expected
        results.add_result(
            f"{param} {value} ({gender} {age})",
            passed,
            f"Expected {expected}, got {actual}"
        )
    
    return results


def run_tests():
    """Run all tests and return summary"""
    all_results = TestResults()
    
    print("=" * 60)
    print("BLOOD REPORT ANALYSIS SYSTEM - AUTOMATED TEST SUITE")
    print("=" * 60)
    
    # Run each test category
    test_functions = [
        ("Unit Conversions", test_unit_conversions),
        ("Dynamic Reference Ranges", test_dynamic_reference_ranges),
        ("Lipid Ratios", test_lipid_ratios),
        ("Framingham Risk Score", test_framingham_risk),
        ("Metabolic Syndrome Detection", test_metabolic_syndrome),
        ("Parameter Classification", test_parameter_classification),
    ]
    
    for name, test_func in test_functions:
        print(f"\n📋 Testing: {name}")
        print("-" * 40)
        
        try:
            results = test_func()
            
            for test in results.tests:
                status = "✅ PASS" if test['passed'] else "❌ FAIL"
                print(f"  {status}: {test['name']}")
                if not test['passed'] and test['details']:
                    print(f"         {test['details']}")
            
            all_results.passed += results.passed
            all_results.failed += results.failed
            all_results.tests.extend(results.tests)
            
            print(f"\n  Category: {results.passed}/{results.total_tests} passed ({results.accuracy}%)")
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            all_results.failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {all_results.total_tests}")
    print(f"Passed: {all_results.passed}")
    print(f"Failed: {all_results.failed}")
    print(f"Accuracy: {all_results.accuracy}%")
    print("=" * 60)
    
    return {
        'total_tests': all_results.total_tests,
        'passed': all_results.passed,
        'failed': all_results.failed,
        'accuracy': all_results.accuracy,
        'tests': all_results.tests
    }


if __name__ == "__main__":
    run_tests()
