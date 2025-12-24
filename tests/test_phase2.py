#!/usr/bin/env python3
"""
Test script for Phase-2 AI Analysis
Validates all components with sample medical data
"""

import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from phase2.phase2_integration_safe import integrate_phase2_analysis, check_phase2_requirements


def test_sample_csv():
    """Test with sample blood report CSV"""
    sample_csv = """test_name,value,unit,reference_range,method,raw_text
Hemoglobin,12.5,g/dL,13.0-17.0,Calculated,Hemoglobin 12.5 g/dL
RBC Count,4.2,million/µL,4.5-5.5,Electrical Impedance,RBC Count 4.2 million/µL
WBC Count,12500,cells/µL,4000-11000,Flow Cytometry,WBC Count 12500 cells/µL
Platelet Count,180000,cells/µL,150000-450000,Electrical Impedance,Platelet Count 180000 cells/µL
Total Cholesterol,220,mg/dL,150-200,Enzymatic,Total Cholesterol 220 mg/dL
HDL Cholesterol,35,mg/dL,40-60,Enzymatic,HDL Cholesterol 35 mg/dL
LDL Cholesterol,165,mg/dL,100-130,Calculated,LDL Cholesterol 165 mg/dL
Glucose,95,mg/dL,70-100,Enzymatic,Glucose 95 mg/dL"""
    
    return sample_csv


def test_phase2_requirements():
    """Test Phase-2 requirements check"""
    print("🔍 Testing Phase-2 Requirements...")
    
    requirements = check_phase2_requirements()
    print(f"Status: {requirements['status']}")
    print(f"Ollama Available: {requirements['ollama_available']}")
    print(f"Required Model: {requirements['required_model']}")
    
    if requirements['status'] == 'ready':
        print("✅ Phase-2 requirements met")
        return True
    else:
        print("❌ Phase-2 requirements not met")
        print(f"Setup command: {requirements['installation_command']}")
        return False


def test_phase2_integration():
    """Test full Phase-2 integration"""
    print("\n🧪 Testing Phase-2 Integration...")
    
    sample_csv = test_sample_csv()
    
    try:
        result = integrate_phase2_analysis(sample_csv)
        
        print(f"Integration Status: {result['integration_status']}")
        
        # Check Phase-2 summary
        summary = result['phase2_summary']
        if summary['available']:
            print("✅ Phase-2 analysis completed")
            print(f"Overall Status: {summary['overall_status']}")
            print(f"Risk Level: {summary['risk_level']}")
            print(f"AI Confidence: {summary['ai_confidence']}")
            print(f"Tests Analyzed: {summary['metrics']['total_tests']}")
            print(f"Abnormal Count: {summary['metrics']['abnormal_count']}")
            
            # Display findings
            if summary['abnormal_findings']:
                print("\nAbnormal Findings:")
                for finding in summary['abnormal_findings']:
                    print(f"  • {finding['test']}: {finding['value']} ({finding['status']})")
            
            # Display recommendations
            if summary['recommendations']['lifestyle']:
                print("\nAI Recommendations:")
                for rec in summary['recommendations']['lifestyle'][:2]:
                    print(f"  • {rec}")
            
            return True
        else:
            print(f"❌ Phase-2 analysis failed: {summary['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False


def test_model_components():
    """Test individual model components"""
    print("\n🔧 Testing Model Components...")
    
    try:
        from phase2.phase2_orchestrator import Phase2Orchestrator
        
        orchestrator = Phase2Orchestrator()
        sample_csv = test_sample_csv()
        
        # Test CSV parsing
        import pandas as pd
        import io
        df = pd.read_csv(io.StringIO(sample_csv))
        print(f"✅ CSV parsing: {len(df)} rows")
        
        # Test Model 1
        model1_result = orchestrator._model1_parameter_interpretation(df)
        if model1_result and 'interpretations' in model1_result:
            print(f"✅ Model 1: {len(model1_result['interpretations'])} parameters interpreted")
        else:
            print("❌ Model 1 failed")
            return False
        
        # Test Model 2
        model2_result = orchestrator._model2_pattern_risk_assessment(df, model1_result)
        if model2_result and 'risk_assessment' in model2_result:
            print(f"✅ Model 2: Risk level {model2_result['risk_assessment'].get('overall_risk_level', 'Unknown')}")
        else:
            print("❌ Model 2 failed")
            return False
        
        # Test Synthesis
        synthesis_result = orchestrator._synthesis_engine(model1_result, model2_result)
        if synthesis_result and 'overall_status' in synthesis_result:
            print(f"✅ Synthesis: Status {synthesis_result['overall_status']}")
        else:
            print("❌ Synthesis failed")
            return False
        
        # Test Recommendations
        recommendations = orchestrator._recommendation_generator(synthesis_result)
        if recommendations and 'lifestyle_recommendations' in recommendations:
            print(f"✅ Recommendations: {len(recommendations['lifestyle_recommendations'])} suggestions")
        else:
            print("❌ Recommendations failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {str(e)}")
        return False


def test_error_handling():
    """Test error handling with invalid data"""
    print("\n🛡️ Testing Error Handling...")
    
    test_cases = [
        ("Empty CSV", ""),
        ("Invalid CSV", "invalid,csv,data"),
        ("Missing columns", "test,value\nHemoglobin,12.5"),
    ]
    
    for test_name, test_csv in test_cases:
        try:
            result = integrate_phase2_analysis(test_csv)
            if result['phase2_summary'].get('available') == False:
                print(f"✅ {test_name}: Handled gracefully")
            else:
                print(f"❌ {test_name}: Should have failed")
        except Exception as e:
            print(f"✅ {test_name}: Exception handled - {str(e)[:50]}...")
    
    return True


def display_sample_output():
    """Display sample Phase-2 output"""
    print("\n📋 Sample Phase-2 Output:")
    print("=" * 50)
    
    sample_csv = test_sample_csv()
    
    try:
        result = integrate_phase2_analysis(sample_csv)
        
        if result['phase2_summary']['available']:
            print(result['phase2_display_text'])
        else:
            print("Phase-2 not available - showing requirements")
            requirements = check_phase2_requirements()
            print(f"Status: {requirements['status']}")
            print(f"Setup: {requirements['installation_command']}")
            
    except Exception as e:
        print(f"Error generating sample output: {str(e)}")


def main():
    """Run all tests"""
    print("🩺 Phase-2 AI Analysis - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Requirements Check", test_phase2_requirements),
        ("Integration Test", test_phase2_integration),
        ("Component Tests", test_model_components),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase-2 is ready to use.")
        display_sample_output()
    else:
        print("\n⚠️ Some tests failed. Check setup and try again.")
        if not results[0][1]:  # Requirements check failed
            print("\nRun setup script: python setup_phase2.py")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)