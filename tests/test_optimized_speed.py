#!/usr/bin/env python3
"""
Test optimized Q&A speed and quality
"""

import sys
import os
import time
sys.path.insert(0, 'src')

from core.qa_assistant import BloodReportQAAssistant

def test_optimized_qa():
    """Test optimized speed and quality"""
    
    assistant = BloodReportQAAssistant()
    
    # Rich mock data for quality testing
    mock_data = {
        'phase2_full_result': {
            'parameter_interpretation': {
                'interpretations': [
                    {
                        'test_name': 'Hemoglobin',
                        'value': '10.2',
                        'unit': 'g/dL',
                        'reference_range': '13.0-17.0',
                        'classification': 'Low'
                    },
                    {
                        'test_name': 'Total Cholesterol',
                        'value': '285',
                        'unit': 'mg/dL',
                        'reference_range': '150-200',
                        'classification': 'High'
                    },
                    {
                        'test_name': 'HDL Cholesterol',
                        'value': '32',
                        'unit': 'mg/dL',
                        'reference_range': '40-60',
                        'classification': 'Low'
                    },
                    {
                        'test_name': 'Glucose',
                        'value': '145',
                        'unit': 'mg/dL',
                        'reference_range': '70-100',
                        'classification': 'High'
                    }
                ]
            }
        }
    }
    
    assistant.load_analysis_data(mock_data)
    
    if not assistant._is_ollama_available():
        print("❌ Ollama not available")
        return
    
    print("⚡ Testing OPTIMIZED Speed + Quality Balance")
    print("=" * 60)
    
    # Test questions that require both speed and quality
    test_cases = [
        ("What is my hemoglobin level?", "Direct question"),
        ("Am I at risk for anemia?", "Risk analysis"),
        ("What foods should I eat?", "Lifestyle recommendations"),
        ("Are there concerning patterns?", "Pattern analysis"),
        ("Same question again", "Cache test")  # Should be instant
    ]
    
    # Use the same question twice to test caching
    test_cases[4] = ("What is my hemoglobin level?", "Cache test")
    
    for question, test_type in test_cases:
        print(f"\n🔍 {test_type}: {question}")
        print("-" * 50)
        
        start_time = time.time()
        answer = assistant.answer_question(question)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Color code based on speed
        if response_time < 1:
            speed_indicator = "🚀 INSTANT"
        elif response_time < 5:
            speed_indicator = "⚡ FAST"
        elif response_time < 10:
            speed_indicator = "✅ GOOD"
        else:
            speed_indicator = "🐌 SLOW"
        
        print(f"⏱️  {speed_indicator} ({response_time:.2f}s)")
        print(f"🤖 Quality: {len(answer)} chars, {len(answer.split())} words")
        print(f"📝 Answer: {answer[:150]}...")
        
        # Check for quality indicators
        quality_indicators = []
        if "based on" in answer.lower():
            quality_indicators.append("✅ Grounded")
        if any(word in answer.lower() for word in ["risk", "tendency", "possible"]):
            quality_indicators.append("✅ Risk analysis")
        if "healthcare professional" in answer.lower():
            quality_indicators.append("✅ Safety disclaimer")
        if any(word in answer.lower() for word in ["diet", "food", "lifestyle"]):
            quality_indicators.append("✅ Recommendations")
        
        if quality_indicators:
            print(f"🎯 Quality: {', '.join(quality_indicators)}")

if __name__ == "__main__":
    test_optimized_qa()