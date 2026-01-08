#!/usr/bin/env python3
"""
Test the sample medical JSON file
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, 'src')

from core.ocr_engine import extract_text_from_file

class MockFile:
    """Mock uploaded file for testing"""
    def __init__(self, file_path):
        self.name = os.path.basename(file_path)
        self.type = "application/json"
        with open(file_path, 'rb') as f:
            self.content = f.read()
    
    def read(self):
        return self.content

def test_sample_json():
    """Test the sample medical JSON file"""
    print("🧪 Testing Sample Medical JSON File")
    print("=" * 40)
    
    # Check if sample file exists
    if not os.path.exists('sample_medical_report.json'):
        print("❌ sample_medical_report.json not found")
        return
    
    # Create mock uploaded file
    mock_file = MockFile('sample_medical_report.json')
    
    try:
        # Process through the main entry point
        result = extract_text_from_file(mock_file)
        result_data = json.loads(result)
        
        print("✅ Processing Result:")
        print(f"   Status: {result_data.get('status')}")
        print(f"   Method: {result_data.get('extraction_method')}")
        print(f"   Confidence: {result_data.get('confidence')}")
        
        if result_data.get('status') == 'success':
            raw_text = result_data.get('raw_text', '')
            print(f"   Extracted Text Length: {len(raw_text)} characters")
            print(f"   Has Phase1 CSV: {'phase1_extraction_csv' in result_data}")
            print(f"   Has Processing Agents: {'processing_agents' in result_data}")
            
            print("\n📄 Extracted Text Preview:")
            print("-" * 30)
            print(raw_text[:300] + "..." if len(raw_text) > 300 else raw_text)
            
            # Check Phase1 CSV
            if 'phase1_extraction_csv' in result_data:
                csv_data = result_data['phase1_extraction_csv']
                print(f"\n📊 Phase1 CSV Length: {len(csv_data)} characters")
                if csv_data:
                    lines = csv_data.split('\n')
                    print(f"   CSV Lines: {len(lines)}")
                    if len(lines) > 1:
                        print(f"   Header: {lines[0]}")
                        if len(lines) > 2:
                            print(f"   Sample Row: {lines[1]}")
            
        else:
            print(f"   ❌ Error: {result_data.get('message')}")
            print(f"   Technical Reason: {result_data.get('technical_reason')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test"""
    print("🚀 Sample JSON File Test")
    print("=" * 50)
    print()
    
    test_sample_json()
    
    print("\n🎯 Expected Result:")
    print("✅ JSON file should be processed successfully")
    print("✅ Medical parameters should be extracted")
    print("✅ Full analysis pipeline should be ready")

if __name__ == "__main__":
    main()