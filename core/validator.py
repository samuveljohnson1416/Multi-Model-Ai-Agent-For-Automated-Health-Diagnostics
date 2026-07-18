import json
import os

# Resolve config path relative to the project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_DIR = os.path.join(_PROJECT_ROOT, 'config')


def load_reference_ranges():
    try:
        config_path = os.path.join(_CONFIG_DIR, 'reference_ranges.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def validate_parameters(parsed_data):
    reference_ranges = load_reference_ranges()
    validated_data = {}
    
    for param_name, param_info in parsed_data.items():
        value = param_info.get("value")
        unit = param_info.get("unit")
        
        validated_data[param_name] = {
            "value": value,
            "unit": unit,
            "status": "UNKNOWN"
        }
        
        if param_name in reference_ranges:
            ref = reference_ranges[param_name]
            min_val = ref.get("min")
            max_val = ref.get("max")
            
            validated_data[param_name]["reference_range"] = f"{min_val} - {max_val} {ref.get('unit')}"
            
            if value < min_val:
                validated_data[param_name]["status"] = "LOW"
            elif value > max_val:
                validated_data[param_name]["status"] = "HIGH"
            else:
                validated_data[param_name]["status"] = "NORMAL"
    
    return validated_data
