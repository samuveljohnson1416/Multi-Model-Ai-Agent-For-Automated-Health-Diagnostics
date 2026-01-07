#!/usr/bin/env python3
"""
Test JSON file processing in the UI
"""

import json

# Test JSON structures that should be recognized as medical data
test_medical_json = {
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
        "value": "180",
        "unit": "mg/dL",
        "reference_range": "<200",
        "status": "NORMAL"
    }
}

# Test simple key-value JSON
test_simple_json = {
    "Hemoglobin": 12.5,
    "Glucose": 95,
    "Cholesterol": 180,
    "RBC Count": 4.2
}

# Test non-medical JSON
test_non_medical_json = {
    "name": "John Doe",
    "age": 45,
    "city": "New York",
    "occupation": "Engineer"
}

def test_medical_detection(json_data, description):
    """Test if JSON data would be detected as medical"""
    print(f"\n🧪 Testing: {description}")
    print(f"Data: {json_data}")
    
    # Check if JSON contains medical parameters
    has_medical = any(key in str(json_data).lower() for key in ['hemoglobin', 'glucose', 'cholesterol', 'rbc', 'wbc', 'platelet'])
    
    print(f"Medical detection: {'✅ YES' if has_medical else '❌ NO'}")
    
    if has_medical:
        # Try to parse it
        parsed_data = {}
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, dict) and 'value' in value:
                    # Standard medical JSON format
                    parsed_data[key] = value
                elif isinstance(value, (int, float, str)):
                    # Simple key-value format
                    parsed_data[key] = {
                        "value": str(value),
                        "unit": "",
                        "reference_range": "",
                        "confidence": "0.95"
                    }
        
        print(f"Parsed parameters: {len(parsed_data)}")
        for param, data in parsed_data.items():
            print(f"  - {param}: {data['value']}")
    
    return has_medical

def main():
    print("🚀 JSON Medical Data Detection Test")
    print("=" * 50)
    
    test_medical_detection(test_medical_json, "Standard medical JSON format")
    test_medical_detection(test_simple_json, "Simple key-value medical JSON")
    test_medical_detection(test_non_medical_json, "Non-medical JSON")
    
    print("\n📋 Summary:")
    print("✅ Standard medical JSON: Should be processed")
    print("✅ Simple medical JSON: Should be processed") 
    print("❌ Non-medical JSON: Should be rejected")

if __name__ == "__main__":
    main()