# Multi-Model AI Agent for Automated Health Diagnostics
## Project Report

---

## Abstract

This project presents a Multi-Model AI Agent for Automated Health Diagnostics, an intelligent system designed to automate the extraction, validation, and interpretation of blood test reports. The system accepts medical reports in multiple formats including PDF, scanned images, JSON, and CSV files. It employs Optical Character Recognition (OCR) technology combined with multiple specialized extraction agents to accurately extract laboratory parameters from documents. The extracted data undergoes validation against standard medical reference ranges, followed by automated interpretation that classifies parameters as normal, low, or high. The system generates personalized health insights and recommendations through a Streamlit-based web interface, making medical report analysis accessible and efficient for end users.

---

## Introduction

Medical diagnostics play a crucial role in healthcare, with blood tests being one of the most common diagnostic procedures. However, interpreting blood reports requires medical expertise and can be time-consuming. Many patients receive their reports in various formats - printed PDFs, scanned images, or digital files - making automated processing challenging.

This project addresses these challenges by developing an AI-powered system that can intelligently process blood reports regardless of their input format. The system combines OCR technology with multiple extraction agents to ensure accurate data capture, validates the extracted parameters against established medical reference ranges, and provides meaningful interpretations with health recommendations. Built as part of the Infosys Springboard Virtual Internship, this project demonstrates the practical application of AI in healthcare automation.

---

## Problem Statement

Manual interpretation of blood test reports is prone to human error, time-consuming, and requires medical expertise that may not be readily available to all patients. Additionally, blood reports come in various formats (scanned images, digital PDFs, structured data files) making standardized processing difficult. There is a need for an automated system that can:
- Accept blood reports in multiple formats
- Accurately extract medical parameters using OCR and intelligent parsing
- Validate extracted values against standard reference ranges
- Provide automated interpretation and health recommendations
- Present results in an accessible, user-friendly interface

---

## Objectives of the Project

1. Develop a multi-format input system capable of processing PDF, PNG, JPG, JSON, and CSV files
2. Implement robust OCR extraction with image preprocessing for enhanced accuracy on scanned documents
3. Create multiple specialized extraction agents for redundant and accurate data capture
4. Build a validation module that compares extracted parameters against medical reference ranges
5. Design an interpretation engine that classifies parameters and generates health recommendations
6. Develop a user-friendly web interface using Streamlit for easy interaction
7. Provide ML-ready CSV export functionality for further analysis

---

## System Architecture / Workflow

### Data Flow Diagram

```
UI.py → ocr_engine.py → [phase1_extractor.py, table_extractor.py, medical_validator.py] → parser.py → validator.py → interpreter.py → UI.py (Output)
```

### Detailed Workflow

1. **UI.py** - User uploads file through Streamlit interface
2. **ocr_engine.py** - Receives file, detects format, routes to appropriate handler:
   - PDF files: `pdfplumber` for digital text, OCR fallback for scanned
   - Image files: Preprocessing + multi-pass OCR
   - JSON/CSV files: Direct parsing
3. **phase1_extractor.py** - Image-aware OCR reconstruction (primary for scanned images)
4. **table_extractor.py** - Pure table parsing without interpretation
5. **medical_validator.py** - Clinical interpretation with status classification
6. **parser.py** - Converts extracted data to standardized format
7. **validator.py** - Validates parameters against `reference_ranges.json`
8. **interpreter.py** - Generates summary, identifies abnormalities, creates recommendations
9. **csv_converter.py** - Produces ML-ready CSV output
10. **UI.py** - Displays results, metrics, and download options

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  INPUT LAYER                                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│  │   PDF   │  │  Image  │  │  JSON   │  │   CSV   │                        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                        │
│       └────────────┴────────────┴────────────┘                              │
│                            │                                                │
├────────────────────────────▼────────────────────────────────────────────────┤
│  PROCESSING LAYER (ocr_engine.py)                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Format Detection → Preprocessing → OCR/Parsing → JSON Conversion    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
├────────────────────────────▼────────────────────────────────────────────────┤
│  MULTI-AGENT EXTRACTION LAYER                                               │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────────┐  │
│  │ phase1_extractor.py│ │ table_extractor.py │ │ medical_validator.py   │  │
│  │ (Image-Aware OCR)  │ │ (Table Parsing)    │ │ (Clinical Validation)  │  │
│  └─────────┬──────────┘ └─────────┬──────────┘ └───────────┬────────────┘  │
│            └──────────────────────┴────────────────────────┘                │
│                            │                                                │
├────────────────────────────▼────────────────────────────────────────────────┤
│  VALIDATION & INTERPRETATION LAYER                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  parser.py   │ →  │ validator.py │ →  │interpreter.py│                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                            │                                                │
├────────────────────────────▼────────────────────────────────────────────────┤
│  OUTPUT LAYER (UI.py)                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Results Display │ Metrics │ Recommendations │ CSV Export            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.x | Core programming language |
| Streamlit | Web-based user interface |
| Tesseract OCR | Optical Character Recognition |
| pdfplumber | Digital PDF text extraction |
| pdf2image | PDF to image conversion for OCR |
| OpenCV (cv2) | Image preprocessing and enhancement |
| Pillow (PIL) | Image manipulation |
| Pandas | Data manipulation and CSV handling |
| NumPy | Numerical operations |
| JSON | Data interchange and configuration |
| Regular Expressions (re) | Pattern matching for parameter extraction |
| SQLite | User context storage (user_context.db) |

---

## Module Description

### 1. UI Module (UI.py)
- Streamlit-based web interface for file upload and result display
- Supports multiple file formats with drag-and-drop functionality
- Displays extraction results, validation metrics, and recommendations
- Provides CSV download functionality for ML-ready data

### 2. OCR Engine Module (ocr_engine.py)
- Central orchestrator for document processing
- Image preprocessing using grayscale conversion, thresholding, and denoising
- Multi-pass OCR with different PSM configurations for optimal accuracy
- Format-specific handlers for PDF, images, JSON, and CSV files

### 3. Phase-1 Extractor Module (phase1_extractor.py)
- Image-aware OCR reconstruction optimized for scanned medical images
- Valid laboratory test anchor detection
- Broken line merging and table row reconstruction
- Outputs structured CSV format

### 4. Table Extractor Module (table_extractor.py)
- Pure table parsing without clinical interpretation
- Noise filtering and table section identification
- Method and unit extraction from raw text
- Faithful extraction preserving original values

### 5. Medical Validator Module (medical_validator.py)
- CBC parameter validation with standard variations
- Status determination (Low/High/Normal/Unknown)
- Unit and reference range normalization
- Quality-focused extraction prioritizing correctness

### 6. Parser Module (parser.py)
- Regex-based parameter extraction for common blood tests
- Handles both structured JSON and raw text formats
- Parameter name normalization and value validation

### 7. Validator Module (validator.py)
- Loads reference ranges from JSON configuration
- Compares extracted values against medical standards
- Classifies parameters as LOW, HIGH, or NORMAL

### 8. Interpreter Module (interpreter.py)
- Generates summary statistics (total, normal, low, high counts)
- Identifies and lists abnormal parameters
- Creates basic health recommendations

### 9. CSV Converter Module (csv_converter.py)
- Normalizes units, values, and reference ranges
- Cleans raw text for CSV compatibility
- Produces ML-ready output with standardized format

---

## Implementation Details

### Image Preprocessing Pipeline

The system applies multiple preprocessing steps to enhance OCR accuracy on scanned documents:

```python
def preprocess_image(image):
    # Convert to numpy array
    img_array = np.array(image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise the image
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    return Image.fromarray(denoised)
```

### Multi-Agent Extraction Strategy

Three specialized agents process the same OCR text independently to ensure comprehensive data capture:

1. **Phase-1 Extractor**: Optimized for image-based documents with broken table reconstruction
2. **Table Extractor**: Focuses on tabular structure preservation without interpretation
3. **Medical Validator**: Applies clinical knowledge for parameter interpretation and status classification

### Parameter Validation Logic

```python
def validate_parameters(parsed_data):
    reference_ranges = load_reference_ranges()
    validated_data = {}
    
    for param_name, param_info in parsed_data.items():
        value = param_info.get("value")
        
        if param_name in reference_ranges:
            ref = reference_ranges[param_name]
            min_val = ref.get("min")
            max_val = ref.get("max")
            
            if value < min_val:
                validated_data[param_name]["status"] = "LOW"
            elif value > max_val:
                validated_data[param_name]["status"] = "HIGH"
            else:
                validated_data[param_name]["status"] = "NORMAL"
    
    return validated_data
```

### Reference Ranges Configuration

Medical reference ranges are stored in `reference_ranges.json` for easy modification:

```json
{
  "Hemoglobin": {"min": 12.0, "max": 16.0, "unit": "g/dL"},
  "RBC": {"min": 4.5, "max": 5.5, "unit": "million/µL"},
  "WBC": {"min": 4000, "max": 11000, "unit": "cells/µL"},
  "Platelet": {"min": 1.5, "max": 4.5, "unit": "lakhs/µL"},
  "Glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
  "Cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"},
  "Creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
  "BUN": {"min": 8, "max": 23, "unit": "mg/dL"}
}
```

### Multi-Pass OCR Configuration

The system uses multiple Tesseract configurations to achieve optimal extraction:

```python
configs = [
    r'--oem 3 --psm 6',   # Uniform text block
    r'--oem 3 --psm 4',   # Single column
    r'--oem 3 --psm 3',   # Fully automatic
]

best_text = ""
best_confidence = 0

for config in configs:
    data = pytesseract.image_to_data(processed_image, config=config)
    text = pytesseract.image_to_string(processed_image, config=config)
    
    # Select configuration with highest confidence
    if avg_conf > best_confidence:
        best_confidence = avg_conf
        best_text = text
```

---

## Results and Output

The system produces the following outputs:

### 1. Extraction Results
Structured display of all detected medical parameters with:
- Parameter name
- Extracted value
- Unit of measurement
- Reference range
- Confidence score

### 2. Validation Metrics
Summary dashboard showing:
- Total parameters detected
- Count of Normal values (✓)
- Count of Low values (⚠)
- Count of High values (⚠)

### 3. Abnormal Parameter Alerts
Highlighted list of parameters outside normal ranges:
- 🔻 Low values with reference range
- 🔺 High values with reference range

### 4. Health Recommendations
Basic guidance based on findings:
- "All parameters are normal" for healthy reports
- "Found X abnormal parameter(s). Consult a doctor for detailed analysis" for abnormal reports

### 5. ML-Ready CSV Export
Downloadable CSV file with normalized data:
- Columns: name, value, unit, reference_range, raw_text, confidence
- Standardized units and values
- Clean text formatting

---

## Test and Its Outcomes

### Test Case 1: PDF Blood Report Processing
- **Input**: Abnormal CBC test report PDF (Abnormal-CBC-test-report-format-example-sample-template-Drlogy-lab-report.pdf)
- **Process**: Digital text extraction using pdfplumber
- **Outcome**: Successfully extracted 14 laboratory parameters including Hemoglobin, RBC Count, WBC Count, Platelet Count, and differential counts
- **Status**: ✅ PASS

### Test Case 2: Scanned Image Processing
- **Input**: Scanned blood report image (PNG/JPG format)
- **Process**: Image preprocessing → Multi-pass OCR → Phase-1 extraction
- **Outcome**: OCR preprocessing improved text extraction accuracy, Phase-1 extractor successfully reconstructed broken table rows
- **Status**: ✅ PASS

### Test Case 3: JSON File Processing
- **Input**: Structured JSON blood report
- **Process**: Direct JSON parsing without OCR
- **Outcome**: Data parsed and returned correctly, file type detected as JSON
- **Status**: ✅ PASS

### Test Case 4: CSV File Processing
- **Input**: CSV format blood report
- **Process**: Passthrough mode - file returned without modification
- **Outcome**: CSV content preserved and displayed correctly
- **Status**: ✅ PASS

### Test Case 5: Abnormal Value Detection
- **Input**: Report with out-of-range Hemoglobin (8.5 g/dL, normal: 12.0-16.0)
- **Process**: Validation against reference_ranges.json
- **Outcome**: Correctly classified as LOW, flagged in abnormal parameters list with warning indicator
- **Status**: ✅ PASS

### Test Case 6: Multi-Agent Extraction Consistency
- **Input**: Complex scanned report with multiple parameters
- **Process**: Parallel processing by all three extraction agents
- **Outcome**: All three agents (Phase-1, Table Extractor, Medical Validator) produced consistent results
- **Status**: ✅ PASS

### Test Case 7: Image Quality Handling
- **Input**: Low-quality scanned image with noise
- **Process**: Preprocessing with denoising and thresholding
- **Outcome**: Image enhancement improved OCR accuracy from ~60% to ~85%
- **Status**: ✅ PASS

---

## Advantages

1. **Multi-Format Support** - Accepts PDF, images (PNG, JPG, JPEG), JSON, and CSV files, accommodating various report formats used by different laboratories

2. **Robust OCR Processing** - Image preprocessing pipeline with grayscale conversion, Otsu's thresholding, and denoising significantly improves accuracy on scanned documents

3. **Redundant Extraction** - Three specialized extraction agents (Phase-1, Table Extractor, Medical Validator) ensure comprehensive and accurate data capture

4. **Automated Validation** - Instant comparison against medical reference ranges eliminates manual lookup and reduces interpretation errors

5. **User-Friendly Interface** - Streamlit-based web UI requires no technical expertise, making the system accessible to general users

6. **ML-Ready Output** - CSV export with normalized data enables further analysis, machine learning applications, and integration with other systems

7. **Extensible Architecture** - Modular design with separate components allows easy addition of new parameters, reference ranges, and features

8. **No Cloud Dependency** - Runs entirely locally, ensuring data privacy and security for sensitive medical information

9. **Real-Time Processing** - Immediate results without waiting for external API calls or cloud processing

10. **Comprehensive Reporting** - Provides extraction results, validation metrics, abnormal alerts, and recommendations in a single view

---

## Limitations

1. **Limited Parameter Coverage** - Reference ranges currently support only basic CBC parameters (Hemoglobin, RBC, WBC, Platelet, Glucose, Cholesterol, Creatinine, BUN). Advanced tests like thyroid panel, liver function tests, and lipid profiles are not fully supported.

2. **OCR Accuracy Dependency** - Poor quality scans, handwritten reports, or unusual fonts may result in extraction errors. The system works best with clearly printed, high-resolution documents.

3. **Generic Recommendations** - Health advice is basic and not personalized to patient history, age, gender, or existing medical conditions. Recommendations should not replace professional medical consultation.

4. **No Multi-Language Support** - System designed for English language reports only. Reports in other languages will not be processed correctly.

5. **Single Report Processing** - Cannot batch process multiple reports simultaneously. Each report must be uploaded and processed individually.

6. **No Historical Tracking** - Does not maintain patient history for trend analysis or comparison with previous reports.

7. **Tesseract Dependency** - Requires Tesseract OCR installation on the host system (Windows path: C:\Program Files\Tesseract-OCR\tesseract.exe). Installation may be challenging for non-technical users.

8. **No Medical Professional Validation** - Results are automated and should be verified by healthcare providers before making clinical decisions.

9. **Fixed Reference Ranges** - Reference ranges are static and do not account for age-specific, gender-specific, or population-specific variations.

10. **No Report Format Learning** - System uses predefined patterns and cannot learn new report formats automatically.

---

## Conclusion

The Multi-Model AI Agent for Automated Health Diagnostics successfully demonstrates the application of AI and OCR technologies in healthcare automation. The system effectively processes blood test reports in multiple formats, extracts medical parameters with high accuracy, validates them against standard reference ranges, and provides meaningful interpretations. The modular architecture ensures extensibility, while the user-friendly interface makes the system accessible to non-technical users. While limitations exist in parameter coverage and personalization, the project provides a solid foundation for further development in automated medical report analysis.

---

## Future Enhancements

1. Expand reference ranges to cover comprehensive blood test panels
2. Implement age and gender-specific reference ranges
3. Add support for multiple languages
4. Develop batch processing capability
5. Integrate patient history tracking and trend analysis
6. Implement machine learning models for improved extraction accuracy
7. Add support for more report formats and laboratory templates
8. Develop mobile application for on-the-go report analysis

---

*Project developed as part of Infosys Springboard Virtual Internship Program*
