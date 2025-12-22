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
from medical_validator import process_medical_document
from table_extractor import extract_medical_table
from phase1_extractor import extract_phase1_medical_image

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image):
    """Enhance image quality for better OCR"""
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


def reconstruct_broken_tables(text):
    """Reconstruct broken tables and misaligned rows"""
    lines = text.split('\n')
    reconstructed_lines = []
    
    # Buffer for potential table rows
    table_buffer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect potential table row (multiple numeric values or structured data)
        if re.search(r'\d+\.?\d*.*\d+\.?\d*', line) or len(re.findall(r'\s{2,}', line)) > 1:
            table_buffer.append(line)
        else:
            # Process accumulated table buffer
            if table_buffer:
                reconstructed_lines.extend(process_table_buffer(table_buffer))
                table_buffer = []
            reconstructed_lines.append(line)
    
    # Process remaining buffer
    if table_buffer:
        reconstructed_lines.extend(process_table_buffer(table_buffer))
    
    return '\n'.join(reconstructed_lines)


def process_table_buffer(buffer):
    """Process potential table rows to reconstruct broken entries"""
    processed = []
    
    for line in buffer:
        # Split by multiple spaces (table columns)
        parts = re.split(r'\s{2,}', line)
        
        if len(parts) >= 2:
            # Reconstruct as "parameter value unit range"
            param_name = parts[0].strip()
            value = parts[1].strip()
            unit = parts[2].strip() if len(parts) > 2 else ""
            ref_range = parts[3].strip() if len(parts) > 3 else ""
            
            # Reconstruct line
            reconstructed = f"{param_name} {value}"
            if unit:
                reconstructed += f" {unit}"
            if ref_range:
                reconstructed += f" ({ref_range})"
                
            processed.append(reconstructed)
        else:
            processed.append(line)
    
    return processed


def extract_medical_parameters(text):
    """Extract ALL medical parameters with table reconstruction and multi-column support"""
    # Step 1: Reconstruct broken tables
    reconstructed_text = reconstruct_broken_tables(text)
    
    parameters = []
    lines = reconstructed_text.split('\n')
    found_params = set()  # Track to avoid duplicates
    
    # Enhanced extraction patterns for all scenarios
    patterns = [
        # Basic patterns
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s*[:\-]?\s*(\d+\.?\d*)\s*([a-zA-Z/µμ%]*)\s*(?:\(([^)]+)\))?',
        
        # Range patterns
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s+(\d+\.?\d*\s*[-–]\s*\d+\.?\d*)',
        
        # Boolean patterns
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s*[:\-]?\s*(Present|Absent|Positive|Negative|Yes|No|Normal|Abnormal|\+|\-)',
        
        # Symbol patterns
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s*\(([+-])\)',
        
        # Multi-column table patterns
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s{2,}(\d+\.?\d*|\w+)\s*([a-zA-Z/µμ%]*)\s*(\d+\.?\d*\s*[-–]\s*\d+\.?\d*)?',
        
        # Colon separated with optional units
        r'([A-Za-z][A-Za-z\s]{1,30}?)\s*:\s*(\d+\.?\d*|\w+)\s*([a-zA-Z/µμ%]*)',
        
        # Loose matching for low-confidence text
        r'([A-Za-z]{3,})\s+(\d+\.?\d*)',
    ]
    
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
            
        # Try each pattern
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                param_name = match.group(1).strip()
                value = match.group(2).strip()
                
                # Skip generic terms
                if len(param_name) < 2 or param_name.lower() in ['test', 'result', 'value', 'normal', 'range']:
                    continue
                
                # Normalize parameter name
                normalized_name = normalize_parameter_name(param_name)
                
                # Skip duplicates
                if normalized_name in found_params:
                    continue
                
                # Extract additional fields
                unit = ""
                ref_range = ""
                
                if len(match.groups()) > 2 and match.group(3):
                    potential_unit = match.group(3).strip()
                    if re.match(r'\d+\.?\d*\s*[-–]\s*\d+\.?\d*', potential_unit):
                        ref_range = potential_unit
                    else:
                        unit = potential_unit
                
                if len(match.groups()) > 3 and match.group(4):
                    ref_range = match.group(4).strip()
                
                # Handle special values (never change original values)
                original_value = value
                if value.lower() in ['present', 'positive', 'yes', 'true', 'normal', '+']:
                    value = "Present"
                    if not ref_range:
                        ref_range = "Absent"
                elif value.lower() in ['absent', 'negative', 'no', 'false', 'abnormal', '-']:
                    value = "Absent"
                    if not ref_range:
                        ref_range = "Present"
                
                # Validate numeric values (but don't skip low-confidence)
                is_valid = True
                try:
                    if value not in ["Present", "Absent"]:
                        float_val = float(value)
                        # Very permissive range for medical values
                        if not (0.0001 <= float_val <= 10000000):
                            is_valid = False
                except ValueError:
                    # Non-numeric values are acceptable
                    pass
                
                if is_valid:
                    # Calculate confidence
                    confidence = estimate_confidence(line, original_value)
                    
                    parameters.append({
                        "name": normalized_name,
                        "value": value,
                        "unit": unit if unit else "",
                        "reference_range": ref_range if ref_range else "",
                        "raw_text": line,
                        "confidence": f"{confidence:.2f}"
                    })
                    
                    found_params.add(normalized_name)
                    break  # Move to next line
    
    return parameters


def convert_to_json_format(text):
    """Convert extracted text through multiple specialized agents"""
    # Phase-1: Image-aware extraction (primary for scanned images)
    phase1_csv = extract_phase1_medical_image(text)
    
    # Medical Document Validation (with interpretation)
    validated_json = process_medical_document(text)
    
    # Pure Table Extraction (no interpretation)
    table_csv = extract_medical_table(text)
    
    try:
        validated_data = json.loads(validated_json)
        
        # Convert validated data to medical parameters
        medical_parameters = []
        for test_name, test_data in validated_data.items():
            medical_parameters.append({
                "name": test_name,
                "value": test_data["value"],
                "unit": test_data["unit"],
                "reference_range": test_data["reference_range"],
                "status": test_data["status"],
                "confidence": "0.95"
            })
        
        # Create comprehensive result with all extraction methods
        structured_result = {
            "patient_info": {"name": "", "place": "", "age": "", "sex": ""},
            "medical_parameters": medical_parameters,
            "phase1_extraction_csv": phase1_csv,
            "table_extraction_csv": table_csv,
            "ignored_fields": [],
            "processing_agents": {
                "phase1_extractor": "Phase-1 Medical Image Extraction Agent",
                "validation_agent": "Medical Document Validation Agent",
                "table_extractor": "Medical Table Extraction Agent"
            },
            "raw_text": text
        }
        
        return json.dumps(structured_result, indent=2)
        
    except json.JSONDecodeError:
        # Fallback: return Phase-1 extraction only
        return json.dumps({
            "patient_info": {"name": "", "place": "", "age": "", "sex": ""},
            "medical_parameters": [],
            "phase1_extraction_csv": phase1_csv,
            "table_extraction_csv": table_csv,
            "ignored_fields": [],
            "processing_agents": {
                "phase1_extractor": "Phase-1 Medical Image Extraction Agent",
                "table_extractor": "Medical Table Extraction Agent"
            },
            "error": "Medical validation failed, using Phase-1 and table extraction",
            "raw_text": text
        })


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
    """OCR and Data Ingestion Agent - Format-specific execution"""
    file_type = uploaded_file.type
    file_name = uploaded_file.name.lower()
    
    # Auto-detect file type and execute appropriate pipeline
    if file_type == "application/pdf":
        return handle_pdf_file(uploaded_file)
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        return handle_image_file(uploaded_file)
    elif file_type == "text/csv" or file_name.endswith('.csv'):
        return handle_csv_file(uploaded_file)
    elif file_type == "application/json" or file_name.endswith('.json'):
        return handle_json_file(uploaded_file)
    else:
        return json.dumps({
            "error": f"Unsupported file type: {file_type}",
            "supported_formats": ["PNG", "JPG", "PDF", "CSV", "JSON"]
        })


def handle_pdf_file(uploaded_file):
    """Handle PDF files - digital text first, OCR fallback"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_file.read())
            temp_pdf_path = temp_pdf.name
    except Exception as e:
        return json.dumps({"error": f"PDF processing error: {str(e)}"})

    # Step 1: Extract digital text
    digital_text = ""
    try:
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    digital_text += page_text + "\n"
    except:
        pass

    # Step 2: OCR fallback if insufficient digital text
    ocr_text = ""
    if len(digital_text.strip()) < 20:  # Insufficient digital text
        try:
            pages = convert_from_path(temp_pdf_path)
            for img in pages:
                processed_img = preprocess_image(img)
                custom_config = r'--oem 3 --psm 6'
                ocr_text += pytesseract.image_to_string(processed_img, config=custom_config) + "\n"
        except Exception as e:
            return json.dumps({"error": f"OCR processing error: {str(e)}"})

    # Step 3: Merge results without duplication
    combined_text = digital_text if digital_text.strip() else ocr_text
    
    # Step 4: Extract parameters
    return convert_to_json_format(combined_text)


def handle_image_file(uploaded_file):
    """Handle image files - high-accuracy OCR with layout detection"""
    try:
        image = Image.open(uploaded_file)
        
        # Enhanced preprocessing for layout detection
        processed_image = preprocess_image(image)
        
        # Multi-pass OCR for maximum accuracy
        configs = [
            r'--oem 3 --psm 6',   # Uniform text block
            r'--oem 3 --psm 4',   # Single column
            r'--oem 3 --psm 3',   # Fully automatic
        ]
        
        best_text = ""
        best_confidence = 0
        
        for config in configs:
            try:
                # Get text with confidence data
                data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
                text = pytesseract.image_to_string(processed_image, config=config)
                
                # Calculate confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_conf = sum(confidences) / len(confidences) if confidences else 0
                
                if avg_conf > best_confidence:
                    best_confidence = avg_conf
                    best_text = text
            except:
                continue
        
        # Extract parameters from best OCR result
        return convert_to_json_format(best_text)
        
    except Exception as e:
        return json.dumps({"error": f"Image processing error: {str(e)}"})


def handle_csv_file(uploaded_file):
    """Handle CSV files - return as-is without OCR or extraction"""
    try:
        # Read CSV content exactly as uploaded
        csv_content = uploaded_file.read().decode('utf-8')
        
        # Return CSV metadata in JSON format for consistency
        return json.dumps({
            "file_type": "CSV",
            "action": "passthrough",
            "csv_content": csv_content,
            "message": "CSV file returned as-is without OCR or extraction"
        })
        
    except Exception as e:
        return json.dumps({"error": f"CSV processing error: {str(e)}"})


def handle_json_file(uploaded_file):
    """Handle JSON files - parse directly without OCR"""
    try:
        json_content = uploaded_file.read().decode('utf-8')
        
        # Validate JSON format
        parsed_json = json.loads(json_content)
        
        # Return parsed JSON
        return json.dumps({
            "file_type": "JSON",
            "action": "parsed",
            "data": parsed_json,
            "message": "JSON file parsed directly without OCR"
        })
        
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON format: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"JSON processing error: {str(e)}"})


def extract_patient_info(text):
    """Extract patient information from OCR text"""
    patient_info = {
        "name": "",
        "place": "",
        "age": "",
        "sex": ""
    }
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
            
        # Extract patient name
        name_patterns = [
            r'(?i)(?:patient\s*name|name)\s*[:\-]?\s*([A-Za-z\s]+)',
            r'(?i)(?:mr\.|mrs\.|ms\.|dr\.)\s*([A-Za-z\s]+)',
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s|$)',  # Title case names
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, line)
            if match and not patient_info["name"]:
                name = match.group(1).strip()
                if len(name) > 2 and not re.search(r'\d', name):
                    patient_info["name"] = name
                    break
        
        # Extract location/place
        place_patterns = [
            r'(?i)(?:address|location|place|city)\s*[:\-]?\s*([A-Za-z\s,]+)',
            r'(?i)([A-Za-z\s]+(?:hospital|clinic|center|medical))',
        ]
        
        for pattern in place_patterns:
            match = re.search(pattern, line)
            if match and not patient_info["place"]:
                place = match.group(1).strip()
                if len(place) > 2:
                    patient_info["place"] = place
                    break
        
        # Extract age
        age_patterns = [
            r'(?i)age\s*[:\-]?\s*(\d+)',
            r'(?i)(\d+)\s*(?:years?|yrs?|y\.o\.)',
            r'(?i)(?:age|aged)\s*(\d+)',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, line)
            if match and not patient_info["age"]:
                age = match.group(1)
                if 0 <= int(age) <= 150:
                    patient_info["age"] = age
                    break
        
        # Extract sex/gender
        sex_patterns = [
            r'(?i)(?:sex|gender)\s*[:\-]?\s*(male|female|m|f)',
            r'(?i)\b(male|female)\b',
            r'(?i)\b(m|f)\b(?:\s|$)',
        ]
        
        for pattern in sex_patterns:
            match = re.search(pattern, line)
            if match and not patient_info["sex"]:
                sex = match.group(1).upper()
                if sex in ['M', 'MALE']:
                    patient_info["sex"] = "Male"
                elif sex in ['F', 'FEMALE']:
                    patient_info["sex"] = "Female"
                break
    
    return patient_info


def identify_ignored_fields(text, patient_info, medical_params):
    """Identify fields that should be ignored"""
    ignored_fields = []
    lines = text.split('\n')
    
    # Get already extracted content
    extracted_content = set()
    
    # Add patient info content
    for key, value in patient_info.items():
        if value:
            extracted_content.add(value.lower())
    
    # Add medical parameter content
    for param in medical_params:
        extracted_content.add(param["name"].lower())
        if param["value"]:
            extracted_content.add(str(param["value"]).lower())
    
    # Patterns for content to ignore
    ignore_patterns = [
        r'(?i)(?:date|time|report|page|lab|laboratory)',
        r'(?i)(?:collected|received|printed|generated)',
        r'(?i)(?:instrument|analyzer|method|technique)',
        r'(?i)(?:doctor|physician|pathologist|technician)',
        r'(?i)(?:sample|specimen|blood|serum|plasma)',
        r'(?i)(?:reference|normal|range|values)',
        r'(?i)(?:department|section|unit)',
        r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Dates
        r'\d{1,2}:\d{2}(?::\d{2})?',  # Times
        r'(?:page|pg)\s*\d+',  # Page numbers
        r'^[A-Z\s]+$',  # All caps headings
    ]
    
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
            
        # Check if line contains already extracted content
        line_lower = line.lower()
        is_extracted = any(content in line_lower for content in extracted_content)
        
        if not is_extracted:
            # Check if matches ignore patterns
            for pattern in ignore_patterns:
                if re.search(pattern, line):
                    ignored_fields.append(line)
                    break
            else:
                # Check if it's a heading or noise
                if (len(line) < 50 and 
                    (line.isupper() or 
                     not re.search(r'\d', line) or
                     len(line.split()) < 3)):
                    ignored_fields.append(line)
    
    return ignored_fields


def normalize_medical_parameter_name(name):
    """Normalize medical parameter names"""
    name_map = {
        'eosi': 'Eosinophils',
        'eosinophil': 'Eosinophils',
        'neutro': 'Neutrophils',
        'neutrophil': 'Neutrophils',
        'lympho': 'Lymphocytes',
        'lymphocyte': 'Lymphocytes',
        'mono': 'Monocytes',
        'monocyte': 'Monocytes',
        'baso': 'Basophils',
        'basophil': 'Basophils',
        'hb': 'Hemoglobin',
        'hgb': 'Hemoglobin',
        'hemoglobin': 'Hemoglobin',
        'rbc': 'RBC Count',
        'red blood cell': 'RBC Count',
        'wbc': 'WBC Count',
        'white blood cell': 'WBC Count',
        'plt': 'Platelet Count',
        'platelets': 'Platelet Count',
        'glucose': 'Glucose',
        'blood sugar': 'Glucose',
        'cholesterol': 'Total Cholesterol',
        'chol': 'Total Cholesterol',
        'creatinine': 'Creatinine',
        'creat': 'Creatinine',
        'bun': 'BUN',
        'urea': 'BUN',
        'sgpt': 'ALT (SGPT)',
        'alt': 'ALT (SGPT)',
        'sgot': 'AST (SGOT)',
        'ast': 'AST (SGOT)',
    }
    
    normalized = name.lower().strip()
    return name_map.get(normalized, name.strip())


def structure_medical_document(ocr_json):
    """Medical document structuring agent - separate into 3 sections"""
    try:
        # Parse OCR JSON
        ocr_data = json.loads(ocr_json)
        
        # Get raw text and parameters
        raw_text = ocr_data.get("raw_text", "")
        if not raw_text and "parameters" in ocr_data:
            # Reconstruct text from parameters if needed
            raw_text = "\n".join([param.get("raw_text", "") for param in ocr_data["parameters"]])
        
        # Extract patient information
        patient_info = extract_patient_info(raw_text)
        
        # Process medical parameters
        medical_parameters = []
        if "parameters" in ocr_data:
            for param in ocr_data["parameters"]:
                param_name = param.get("name", "")
                param_value = param.get("value", "")
                
                # Skip if this looks like patient info
                if any(keyword in param_name.lower() for keyword in ['name', 'age', 'sex', 'patient', 'address']):
                    continue
                
                # Only include if it's a medical parameter
                if (param_value and 
                    (re.search(r'\d', str(param_value)) or 
                     str(param_value).lower() in ['present', 'absent', 'positive', 'negative'])):
                    
                    medical_parameters.append({
                        "name": normalize_medical_parameter_name(param_name),
                        "value": param.get("value", ""),
                        "unit": param.get("unit", ""),
                        "reference_range": param.get("reference_range", ""),
                        "confidence": param.get("confidence", "")
                    })
        
        # Identify ignored fields
        ignored_fields = identify_ignored_fields(raw_text, patient_info, medical_parameters)
        
        # Structure the output
        structured_output = {
            "patient_info": patient_info,
            "medical_parameters": medical_parameters,
            "ignored_fields": ignored_fields
        }
        
        return json.dumps(structured_output, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Document structuring error: {str(e)}",
            "patient_info": {"name": "", "place": "", "age": "", "sex": ""},
            "medical_parameters": [],
            "ignored_fields": []
        })