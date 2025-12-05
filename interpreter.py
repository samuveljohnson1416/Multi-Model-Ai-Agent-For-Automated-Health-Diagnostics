def interpret_results(validated_data):
    """
    Interprets validated blood test results.
    Provides summary and recommendations.
    """
    interpretation = {
        "summary": {},
        "abnormal_parameters": [],
        "recommendations": []
    }
    
    low_count = 0
    high_count = 0
    normal_count = 0
    
    for param_name, param_info in validated_data.items():
        status = param_info.get("status")
        
        if status == "LOW":
            low_count += 1
            interpretation["abnormal_parameters"].append({
                "parameter": param_name,
                "value": param_info.get("value"),
                "status": "LOW",
                "reference": param_info.get("reference_range", "N/A")
            })
        elif status == "HIGH":
            high_count += 1
            interpretation["abnormal_parameters"].append({
                "parameter": param_name,
                "value": param_info.get("value"),
                "status": "HIGH",
                "reference": param_info.get("reference_range", "N/A")
            })
        elif status == "NORMAL":
            normal_count += 1
    
    # Summary
    interpretation["summary"] = {
        "total_parameters": len(validated_data),
        "normal": normal_count,
        "low": low_count,
        "high": high_count
    }
    
    # Recommendations
    if low_count == 0 and high_count == 0:
        interpretation["recommendations"].append("All parameters are within normal range.")
    else:
        interpretation["recommendations"].append(f"Found {low_count + high_count} abnormal parameter(s).")
        interpretation["recommendations"].append("Please consult with a healthcare professional for detailed analysis.")
    
    return interpretation
