#!/usr/bin/env python3
"""
Test script for Q&A Assistant speed optimizations
"""

import time
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from core.qa_assistant import BloodReportQAAssistant

def create_mock_analysis_data():
    """Create mock analysis data for testing"""
    return {
        'phase2_full_result': {
            'parameter_interpretation': {
                'interpretations': [
                    {
                        'test_name': 'Hemoglobin',
                        'value': '8.5',
                        'unit': 'g/dL',
                        'reference_range': '12.0-15.5',
                        'classification': 'Low'
                    },
                    {
                        'test_name': 'Total Cholesterol',
                        'value': '250',
                        'unit': 'mg/dL',
                        'reference_range': '<200',
                        'classification': 'High'
                    },
                    {
                        'test_name': 'Blood Sugar',
                        'value': '95',
                        'unit': 'mg/dL',
                        'reference_range': '70-100',
                        'classification': 'Normal'
                    },
                    {
                        'test_name': 'White Blood Cells',
                        'value': '7500',
                        'unit': '/μL',
                        'reference_range': '4000-11000',
                        'classification': 'Normal'
                    }
                ]
            }
        }
    }

def test_speed_optimizations():
    """Test the speed optimizations"""
    print("🚀 Testing Q&A Assistant Speed Optimizations")
    print("=" * 50)
    
    # Create assistant
    assistant = BloodReportQAAssistant()
    
    # Load mock data
    mock_data = create_mock_analysis_data()
    print("📊 Loading analysis data...")
    assistant.load_analysis_data(mock_data)
    
    # Test questions
    test_questions = [
        "What is my hemoglobin level?",
        "Are there any abnormal values in my report?",
        "What foods should I eat based on my results?",
        "What are the health risks from my blood report?",
        "Tell me about my cholesterol levels"
    ]
    
    print(f"🧪 Testing {len(test_questions)} questions...")
    print()
    
    total_time = 0
    successful_responses = 0
    
    for i, question in enumerate(test_questions, 1):
        print(f"Question {i}: {question}")
        
        start_time = time.time()
        
        # Test with progress callback
        def progress_callback(message):
            print(f"  ⚡ {message}")
        
        try:
            if hasattr(assistant, 'answer_question_with_progress'):
                answer = assistant.answer_question_with_progress(question, progress_callback)
            else:
                answer = assistant.answer_question(question)
            
            end_time = time.time()
            response_time = end_time - start_time
            total_time += response_time
            
            print(f"  ⏱️  Response time: {response_time:.2f} seconds")
            print(f"  📝 Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            print()
            
            successful_responses += 1
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()
    
    # Performance summary
    print("📈 Performance Summary")
    print("-" * 30)
    print(f"Total questions: {len(test_questions)}")
    print(f"Successful responses: {successful_responses}")
    print(f"Total time: {total_time:.2f} seconds")
    
    if successful_responses > 0:
        avg_time = total_time / successful_responses
        print(f"Average response time: {avg_time:.2f} seconds")
        
        if avg_time <= 8:
            print("✅ Speed target achieved! (≤8 seconds)")
        else:
            print("⚠️  Speed target not met (>8 seconds)")
    
    # Test caching
    print("\n🔄 Testing Response Caching")
    print("-" * 30)
    
    # Ask the same question again
    test_question = test_questions[0]
    print(f"Repeating: {test_question}")
    
    start_time = time.time()
    answer = assistant.answer_question(test_question)
    end_time = time.time()
    
    cache_time = end_time - start_time
    print(f"Cached response time: {cache_time:.3f} seconds")
    
    if cache_time < 0.1:
        print("✅ Caching working perfectly!")
    else:
        print("⚠️  Caching may not be working optimally")
    
    # Performance stats
    if hasattr(assistant, 'get_performance_stats'):
        print("\n📊 Performance Statistics")
        print("-" * 30)
        stats = assistant.get_performance_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    test_speed_optimizations()