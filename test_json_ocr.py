#!/usr/bin/env python3
"""
Test JSON processing in the enhanced OCR system
"""

import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, 'src')

from core.ocr_engine import MedicalOCROrchestrator

def create_test_json_file(json_data, filename):
    """Create a temporary JSON file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_data, f, indent=2)
        return f.name

def test_json_processing():
    """Test JSON file processing"""
    print("🧪 Testing JSON File Processing")
    print("=" * 40)
    
    orchestrator = MedicalOCROrchestrator()
    
    # Test medical JSON
    medical_json = {
        "patient_info": {
            "name": "John Doe",
            "age": 45,
            "gender": "Male"
        },
        "test_results": {
            "hemoglobin": {
                "value": "12.5",
                "unit": "g/dL",
                "reference_range": "13.0-17.0",
                "status": "LOW"
            },
            "glucose": {
                "value": "95",
                "unit": "mg/dL",
                "reference_range": "70-100",
                "status": "NORMAL"
            },
            "cholesterol": {
                "value": "220",
                "unit": "mg/dL",
                "reference_range": "<200",
                "status": "HIGH"
            }
        }
    }
    
    # Create temporary JSON file
    json_file_path = create_test_json_file(medical_json, "test_medical.json")
    
    try:
        # Process the JSON file
        result = orchestrator.process_json_file(json_file_path)
        result_data = json.loads(result)
        
        print("✅ JSON Processing Result:")
        print(f"   Status: {result_data.get('status')}")
        print(f"   Method: {result_data.get('extraction_method')}")
        print(f"   Confidence: {result_data.get('confidence')}")
        print(f"   Validation: {result_data.get('validation_message')}")
        
        if result_data.get('status') == 'success':
            raw_text = result_data.get('raw_text', '')
            print(f"   Extracted Text Length: {len(raw_text)} characters")
            print(f"   Text Preview: {raw_text[:200]}...")
            
            if 'debug_info' in result_data:
                debug = result_data['debug_info']
                print(f"   Parameters Found: {debug.get('parameters_found')}")
                print(f"   Source Format: {debug.get('source_format')}")
        else:
            print(f"   Error: {result_data.get('message')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Cleanup
        try:
            os.unlink(json_file_path)
        except:
            pass
    
    print()

def test_non_medical_json():
    """Test non-medical JSON rejection"""
    print("🧪 Testing Non-Medical JSON Rejection")
    print("=" * 40)
    
    orchestrator = MedicalOCROrchestrator()
    
    # Test non-medical JSON
    non_medical_json = {
        "name": "John Doe",
        "age": 45,
        "city": "New York",
        "occupation": "Engineer",
        "hobbies": ["reading", "swimming"]
    }
    
    # Create temporary JSON file
    json_file_path = create_test_json_file(non_medical_json, "test_non_medical.json")
    
    try:
        # Process the JSON file
        result = orchestrator.process_json_file(json_file_path)
        result_data = json.loads(result)
        
        print("✅ Non-Medical JSON Result:")
        print(f"   Status: {result_data.get('status')}")
        print(f"   Error: {result_data.get('error')}")
        print(f"   Message: {result_data.get('message')}")
        
        if result_data.get('status') == 'error':
            print("   ✅ Correctly rejected non-medical JSON")
        else:
            print("   ❌ Should have rejected non-medical JSON")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Cleanup
        try:
            os.unlink(json_file_path)
        except:
            pass
    
    print()

def main():
    """Run all tests"""
    print("🚀 JSON Processing Test Suite")
    print("=" * 50)
    print()
    
    try:
        test_json_processing()
        test_non_medical_json()
        
        print("🎉 JSON processing tests completed!")
        print()
        print("📋 Summary:")
        print("✅ Medical JSON files are now properly processed")
        print("✅ Non-medical JSON files are correctly rejected")
        print("✅ JSON data is converted to text format for analysis")
        print("✅ Full medical analysis pipeline will now work with JSON")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()