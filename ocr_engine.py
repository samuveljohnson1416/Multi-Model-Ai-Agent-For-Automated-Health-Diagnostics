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


def advanced_preprocess_image(image):
    """Multi-stage image enhancement for medical reports"""
    img_array = np.array(image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Multiple preprocessing approaches
    processed_images = []
    
    # Method 1: OTSU thresholding
    _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(thresh1)
    
    # Method 2: Adaptive thresholding
    thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    processed_images.append(thresh2)
    
    # Method 3: Morphological operations
    kernel = np.ones((1,1), np.uint8)
    morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    _, thresh3 = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(thresh3)
    
    # Method 4: Contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    _, thresh4 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(thresh4)
    
    return processed_images


def multi_pass_ocr(image):
    """Perform multiple OCR passes with different configurations"""
    processed_images = advanced_preprocess_image(image)
    
    # Different OCR configurations
    configs = [
        r'--oem 3 --psm 6',  # Uniform text block
        r'--oem 3 --psm 4',  # Single column
        r'--oem 3 --psm 3',  # Fully automatic
        r'--oem 3 --psm 11', # Sparse text
        r'--oem 3 --psm 12', # Sparse text with OSD
    ]
    
    all_text = []
    confidence_scores = []
    
    for processed_img in processed_images:
        pil_img = Image.fromarray(processed_img)
        for config in configs:
            try:
                # Get text with confidence
                data = pytesseract.image_to_data(pil_img, config=config, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(pil_img, config=config)
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                
                all_text.append(text.strip())
                confidence_scores.append(avg_conf)
            except:
                continue
    
    # Return best result
    if confidence_scores:
        best_idx = confidence_scores.index(max(confidence_scores))
        return all_text[best_idx], max(confidence_scores)
    
    return "", 0


def extract_medical_parameters(text):
    """Extract medical parameters with advanced pattern matching"""
    parameters = []
    
    # Common medical parameter patterns with variations
    patterns = {
        'Hemoglobin': [
            r'(?:Hemoglobin|HB|Hb|HEMOGLOBIN|hemoglobin|hb)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'RBC': [
            r'(?:RBC|Red Blood Cell|Red Blood Cells|RBC Count|rbc)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'WBC': [
            r'(?:WBC|White Blood Cell|White Blood Cells|WBC Count|Total WBC|wbc)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'Platelet': [
            r'(?:Platelet|PLT|Platelets|Platelet Count|platelet|plt)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'Glucose': [
            r'(?:Glucose|Blood Sugar|Blood Glucose|Fasting Glucose|glucose)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'Cholesterol': [
            r'(?:Cholesterol|CHOL|Total Cholesterol|cholesterol)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'Creatinine': [
            r'(?:Creatinine|CREAT|Serum Creatinine|creatinine)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
        'BUN': [
            r'(?:Urea|BUN|Blood Urea Nitrogen|urea|bun)\s*[:\-\s]*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)\s*(?:(\d+\.?\d*\s*[-–]\s*\d+\.?\d*))?',
        ],
    }
    
    lines = text.split('\n')
    
    for line in lines:
        for param_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                    ref_range = match.group(3) if len(match.groups()) > 2 and match.group(3) else ""
                    
                    try:
                        float_value = float(value)
                        if 0.01 <= float_value <= 100000:  # Sanity check
                            parameters.append({
                                "name": param_name,
                                "value": value,
                                "unit": unit.strip(),
                                "reference_range": ref_range.strip(),
                                "raw_text": line.strip()
                            })
                            break
                    except ValueError:
                        continue
    
    return parameters


def detect_sections(text):
    """Detect common lab report sections"""
    sections = []
    section_patterns = [
        r'(?i)complete blood count|cbc',
        r'(?i)liver function|lft',
        r'(?i)kidney function|kft|renal',
        r'(?i)lipid profile|lipid',
        r'(?i)thyroid function|tft',
        r'(?i)diabetes|glucose|hba1c',
    ]
    
    for pattern in section_patterns:
        if re.search(pattern, text):
            sections.append(pattern.replace(r'(?i)', '').replace('|', ' or '))
    
    return sections


def find_missing_parameters(extracted_params):
    """Identify common missing parameters"""
    common_params = ['Hemoglobin', 'RBC', 'WBC', 'Platelet', 'Glucose', 'Cholesterol', 'Creatinine', 'BUN']
    extracted_names = [p['name'] for p in extracted_params]
    missing = [param for param in common_params if param not in extracted_names]
    return missing


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
            all_parameters = []
            all_sections = []
            all_text = ""
            total_confidence = 0
            
            for img in pages:
                page_text, confidence = multi_pass_ocr(img)
                all_text += page_text + "\n"
                
                # Extract parameters from each page
                page_params = extract_medical_parameters(page_text)
                all_parameters.extend(page_params)
                
                # Detect sections
                page_sections = detect_sections(page_text)
                all_sections.extend(page_sections)
                
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(pages) if pages else 0
            missing = find_missing_parameters(all_parameters)
            
            # Return structured JSON for PDF
            result = {
                "parameters": all_parameters,
                "detected_sections": list(set(all_sections)),
                "ocr_confidence": f"{avg_confidence:.1f}%",
                "missing_common_parameters": missing,
                "raw_text": all_text
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error: {str(e)}"

    return text.strip()


def extract_text_from_image(uploaded_image):
    try:
        image = Image.open(uploaded_image)
        
        # Multi-pass OCR extraction
        text, confidence = multi_pass_ocr(image)
        
        # Extract medical parameters
        parameters = extract_medical_parameters(text)
        
        # Detect sections
        sections = detect_sections(text)
        
        # Find missing parameters
        missing = find_missing_parameters(parameters)
        
        # Return structured JSON
        result = {
            "parameters": parameters,
            "detected_sections": sections,
            "ocr_confidence": f"{confidence:.1f}%",
            "missing_common_parameters": missing,
            "raw_text": text
        }
        
        return json.dumps(result, indent=2)
        
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
