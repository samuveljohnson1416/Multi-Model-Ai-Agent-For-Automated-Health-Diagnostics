import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import tempfile
import io
import os
import cv2
import numpy as np
import json
import re

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image):
    """Enhance image quality for better OCR"""
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    # Convert back to PIL
    return Image.fromarray(denoised)


def extract_text_from_pdf(uploaded_pdf):
    text = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_pdf.read())
            temp_pdf_path = temp_pdf.name
    except Exception as e:
        return f"Error: {str(e)}"

    try:
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    if len(text.strip()) < 10:
        try:
            pages = convert_from_path(temp_pdf_path)
            text = ""
            for img in pages:
                processed_img = preprocess_image(img)
                custom_config = r'--oem 3 --psm 6'
                text += pytesseract.image_to_string(processed_img, config=custom_config) + "\n"
        except Exception as e:
            return f"Error: {str(e)}"

    # Convert to JSON format with extracted parameters
    return convert_to_json_format(text)


def extract_text_from_image(uploaded_image):
    try:
        image = Image.open(uploaded_image)
        
        # Preprocess image for better OCR
        processed_image = preprocess_image(image)
        
        # Extract text with custom config
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Convert to JSON format with extracted parameters
        return convert_to_json_format(text)
        
    except Exception as e:
        return f"Error: {str(e)}"


def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        return extract_text_from_image(uploaded_file)
    elif file_type == "application/json":
        return uploaded_file.read().decode('utf-8')
    else:
        return f"Unsupported file type: {file_type}"


def normalize_parameter_name(name):
    """Normalize parameter names to standard format"""
    name_map = {
        'hb': 'Hemoglobin',
        'hgb': 'Hemoglobin',
        'hemoglobin': 'Hemoglobin',
        'rbc': 'RBC',
        'red blood cell': 'RBC',
        'red blood cells': 'RBC',
        'wbc': 'WBC',
        'white blood cell': 'WBC',
        'white blood cells': 'WBC',
        'plt': 'Platelet',
        'platelets': 'Platelet',
        'platelet count': 'Platelet',
        'glucose': 'Glucose',
        'blood sugar': 'Glucose',
        'cholesterol': 'Cholesterol',
        'chol': 'Cholesterol',
        'creatinine': 'Creatinine',
        'creat': 'Creatinine',
        'bun': 'BUN',
        'urea': 'BUN',
        'ph': 'pH',
        'PH': 'pH',
    }
    
    normalized = name.lower().strip()
    return name_map.get(normalized, name.strip())


def estimate_confidence(line, value):
    """Estimate confidence based on text clarity"""
    confidence = 0.8  # Base confidence
    
    # Reduce confidence for unclear patterns
    if '?' in line or 'unclear' in line.lower():
        confidence -= 0.3
    if len(line.strip()) < 5:
        confidence -= 0.2
    if not re.search(r'\d', str(value)):
        confidence -= 0.1
    
    return max(0.1, min(1.0, confidence))


def extract_medical_parameters(text):
    """Extract ALL medical parameters using comprehensive pattern matching"""
    parameters = []
    lines = text.split('\n')
    found_params = set()  # Track to avoid duplicates
    
    # Comprehensive extraction patterns
    patterns = [
        # Pattern 1: "<name> <value>"
        r'([A-Za-z][A-Za-z\s]+?)\s+(\d+\.?\d*)\s*$',
        
        # Pattern 2: "<name> : <value>"
        r'([A-Za-z][A-Za-z\s]+?)\s*:\s*(\d+\.?\d*)',
        
        # Pattern 3: "<name> <value> <unit>"
        r'([A-Za-z][A-Za-z\s]+?)\s+(\d+\.?\d*)\s+([a-zA-Z/µμ%]+)',
        
        # Pattern 4: "<name> <value> (<unit>)"
        r'([A-Za-z][A-Za-z\s]+?)\s+(\d+\.?\d*)\s*\(([a-zA-Z/µμ%]+)\)',
        
        # Pattern 5: "<name> Present/Absent"
        r'([A-Za-z][A-Za-z\s]+?)\s+(Present|Absent|Positive|Negative)',
        
        # Pattern 6: "<name> (+)" or "<name> (-)"
        r'([A-Za-z][A-Za-z\s]+?)\s*\(([+-])\)',
        
        # Pattern 7: "<name> <value> <ref_range>"
        r'([A-Za-z][A-Za-z\s]+?)\s+(\d+\.?\d*)\s+(\d+\.?\d*\s*[-–]\s*\d+\.?\d*)',
        
        # Pattern 8: Table-like with multiple spaces
        r'([A-Za-z][A-Za-z\s]+?)\s{2,}(\d+\.?\d*)',
        
        # Pattern 9: Colon separated with units and ranges
        r'([A-Za-z][A-Za-z\s]+?)\s*:\s*(\d+\.?\d*)\s*([a-zA-Z/µμ%]*)\s*(?:\(([^)]+)\))?',
        
        # Pattern 10: Boolean indicators
        r'([A-Za-z][A-Za-z\s]+?)\s*:\s*(Yes|No|True|False|Normal|Abnormal)',
    ]
    
    for line in lines:
        line = line.strip()
        if len(line) < 3:  # Skip very short lines
            continue
            
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                param_name = match.group(1).strip()
                value = match.group(2).strip()
                
                # Skip if parameter name is too short or generic
                if len(param_name) < 2 or param_name.lower() in ['test', 'result', 'value']:
                    continue
                
                # Normalize parameter name
                normalized_name = normalize_parameter_name(param_name)
                
                # Skip duplicates
                if normalized_name in found_params:
                    continue
                
                # Extract unit and reference range
                unit = ""
                ref_range = ""
                
                if len(match.groups()) > 2 and match.group(3):
                    potential_unit = match.group(3).strip()
                    # Check if it's a unit or reference range
                    if re.match(r'\d+\.?\d*\s*[-–]\s*\d+\.?\d*', potential_unit):
                        ref_range = potential_unit
                    else:
                        unit = potential_unit
                
                if len(match.groups()) > 3 and match.group(4):
                    ref_range = match.group(4).strip()
                
                # Handle special values
                if value.lower() in ['present', 'positive', 'yes', 'true', 'normal']:
                    value = "Present"
                    if not ref_range:
                        ref_range = "Absent"
                elif value.lower() in ['absent', 'negative', 'no', 'false', 'abnormal']:
                    value = "Absent"
                    if not ref_range:
                        ref_range = "Present"
                elif value in ['+']:
                    value = "Present"
                    if not ref_range:
                        ref_range = "Absent"
                elif value in ['-']:
                    value = "Absent"
                    if not ref_range:
                        ref_range = "Present"
                
                # Validate numeric values
                try:
                    if value not in ["Present", "Absent"]:
                        float_val = float(value)
                        if not (0.001 <= float_val <= 1000000):  # Reasonable medical range
                            continue
                except ValueError:
                    # Non-numeric values are OK for some parameters
                    pass
                
                # Estimate confidence
                confidence = estimate_confidence(line, value)
                
                parameters.append({
                    "name": normalized_name,
                    "value": value,
                    "unit": unit,
                    "reference_range": ref_range,
                    "raw_text": line,
                    "confidence": f"{confidence:.2f}"
                })
                
                found_params.add(normalized_name)
                break  # Found match for this line, move to next line
    
    return parameters


def convert_to_json_format(text):
    """Convert extracted text to JSON format with medical parameters"""
    parameters = extract_medical_parameters(text)
    
    result = {
        "parameters": parameters
    }
    
    return json.dumps(result, indent=2)