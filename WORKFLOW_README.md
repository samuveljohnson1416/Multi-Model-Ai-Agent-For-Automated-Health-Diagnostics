# Blood Report Analysis System - Complete Workflow Documentation

> A comprehensive step-by-step guide explaining how the Multi-Model AI Agent for Health Diagnostics works from start to finish.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Step-by-Step Workflow](#step-by-step-workflow)
   - [Step 1: Application Startup](#step-1-application-startup)
   - [Step 2: File Upload & Type Detection](#step-2-file-upload--type-detection)
   - [Step 3: OCR Processing (Phase 1)](#step-3-ocr-processing-phase-1)
   - [Step 4: Parameter Parsing](#step-4-parameter-parsing)
   - [Step 5: Parameter Validation](#step-5-parameter-validation)
   - [Step 6: Results Interpretation](#step-6-results-interpretation)
   - [Step 7: Multi-Model Analysis](#step-7-multi-model-analysis)
   - [Step 8: Phase 2 - LLM Analysis](#step-8-phase-2---llm-analysis)
   - [Step 9: Advanced Risk Calculation](#step-9-advanced-risk-calculation)
   - [Step 10: AI Chat Assistant](#step-10-ai-chat-assistant)
   - [Step 11: Results Display](#step-11-results-display)
4. [Module Reference](#module-reference)
5. [Data Flow Diagram](#data-flow-diagram)

---

## System Overview

The Blood Report Analysis System is an AI-powered medical report analysis platform that processes blood work reports through multiple stages of intelligent analysis. The system uses a combination of:

- **OCR (Optical Character Recognition)** for extracting text from images/PDFs
- **Rule-based parsing** for identifying medical parameters
- **Multi-model AI analysis** for pattern detection and risk assessment
- **LLM (Large Language Model)** integration for natural language insights
- **Interactive chat interface** for personalized health Q&A

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE (Streamlit)                         │
│                              src/ui/UI.py                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FILE UPLOAD & TYPE DETECTION                         │
│                    PDF / Image / JSON / CSV / Text                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              ┌──────────┐     ┌──────────┐      ┌──────────┐
              │   PDF    │     │  IMAGE   │      │   JSON   │
              │ pdfplumber│    │ Tesseract│      │  Direct  │
              └──────────┘     │ + OpenCV │      │  Parse   │
                    │          └──────────┘      └──────────┘
                    │                │                 │
                    └────────────────┼─────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OCR ENGINE (MedicalOCROrchestrator)                      │
│                         src/core/ocr_engine.py                               │
│  • Multiple preprocessing strategies (6 different approaches)                │
│  • Medical parameter pattern matching                                        │
│  • API fallback (Tesseract → Cloud OCR)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PARAMETER PARSING ENGINE                              │
│                src/core/parser.py + enhanced_blood_parser.py                 │
│  • 20+ blood parameters supported (CBC, differential, chemistry)             │
│  • Regex pattern matching for value extraction                               │
│  • Unit detection and normalization                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PARAMETER VALIDATION                                │
│                         src/core/validator.py                                │
│  • Reference range comparison (config/reference_ranges.json)                 │
│  • Status assignment (LOW / NORMAL / HIGH)                                   │
│  • Dynamic reference ranges based on age/gender                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RESULTS INTERPRETATION                                │
│                        src/core/interpreter.py                               │
│  • Summary generation                                                        │
│  • Abnormal parameter identification                                         │
│  • Basic recommendations                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
┌────────────────────────────────┐    ┌────────────────────────────────────────┐
│    MULTI-MODEL ANALYSIS        │    │         PHASE 2 - LLM ANALYSIS         │
│        (Rule-Based)            │    │   src/phase2/phase2_orchestrator.py    │
│                                │    │                                        │
│  MODEL 1: Parameter Analysis   │    │  • Mistral 7B Instruct via Ollama      │
│  - Severity scoring            │    │  • Hugging Face API fallback           │
│  - Deviation calculation       │    │  • Parameter interpretation            │
│                                │    │  • Pattern recognition                 │
│  MODEL 2: Pattern Recognition  │    │  • Risk assessment synthesis           │
│  - Anemia detection            │    │  • Personalized recommendations        │
│  - Infection analysis          │    │                                        │
│  - Bleeding risk               │    └────────────────────────────────────────┘
│  - Condition correlation       │
│                                │
│  MODEL 3: Risk Computation     │
│  - Anemia risk score           │
│  - Infection risk score        │
│  - Bleeding risk score         │
│  - Overall health score        │
│                                │
│  MODEL 4: Contextual Analysis  │
│  - Age-based adjustments       │
│  - Gender-based adjustments    │
│  - Medical history impact      │
│  - Lifestyle factors           │
└────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADVANCED RISK CALCULATOR                                │
│                 src/core/advanced_risk_calculator.py                         │
│  • Framingham CVD Risk Score (10-year cardiovascular risk)                   │
│  • Lipid Ratio Analysis                                                      │
│  • Metabolic Syndrome Detection                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENHANCED AI AGENT                                     │
│                   src/core/enhanced_ai_agent.py                              │
│  • Intent Inference Engine - understands user questions                      │
│  • Clarifying Question Generator - asks follow-ups when needed               │
│  • Goal-Oriented Workflow Manager - executes complex tasks                   │
│  • Advanced Context Manager - maintains conversation history                 │
│  • Q&A Assistant - answers health-related questions                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESULTS DISPLAY                                    │
│                          src/ui/UI.py                                        │
│  • Parameter table with status indicators                                    │
│  • Risk score visualizations                                                 │
│  • Pattern/condition cards                                                   │
│  • Traceable recommendations                                                 │
│  • Interactive chat interface                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Workflow

### Step 1: Application Startup

**Files Involved:**
- `start_project.py` - Main entry point for local development
- `app.py` - Entry point for Hugging Face Spaces deployment

**What Happens:**

1. **Environment Setup**
   ```python
   # start_project.py
   - Checks if running from project root directory
   - Validates Python version (requires 3.8+)
   - Launches Streamlit server on port 8501
   ```

2. **Path Configuration**
   ```python
   # app.py
   - Adds 'src' directory to Python path
   - Sets LLM provider priority (Ollama first by default)
   - Imports and runs the main UI
   ```

3. **Ollama Auto-Start** (if available)
   ```python
   # utils/ollama_manager.py
   - Attempts to start Ollama service
   - Checks for Mistral model availability
   ```

---

### Step 2: File Upload & Type Detection

**Files Involved:**
- `src/ui/UI.py` - Streamlit file uploader
- `src/core/ocr_engine.py` - `MedicalOCROrchestrator.determine_file_type()`

**What Happens:**

1. **User uploads file** via Streamlit file uploader widget
   - Supported formats: PDF, PNG, JPG, JPEG, JSON, CSV, TXT

2. **File type detection** based on MIME type and extension:
   ```python
   def determine_file_type(uploaded_file):
       # Checks file_type (MIME) and file_name extension
       # Returns: "pdf", "image", "json", "csv", "text", or "unsupported"
   ```

3. **Routing to appropriate processor:**
   | File Type | Processor |
   |-----------|-----------|
   | PDF | `extract_text_from_pdf_direct()` or OCR if scanned |
   | Image | OCR with preprocessing |
   | JSON | Direct JSON parsing |
   | CSV | CSV adapter |
   | Text | Direct text processing |

---

### Step 3: OCR Processing (Phase 1)

**Files Involved:**
- `src/core/ocr_engine.py` - `MedicalOCROrchestrator` class
- `src/phase1/phase1_extractor.py` - `Phase1MedicalImageExtractor` class
- `src/phase1/table_extractor.py` - Table extraction utilities
- `src/phase1/medical_validator.py` - Medical document validation

**What Happens:**

1. **Image Preprocessing** - 6 different strategies are applied:
   ```python
   preprocessing_strategies = [
       'standard',           # Bilateral filter + adaptive threshold
       'high_contrast',      # Histogram equalization + CLAHE
       'denoised',           # Heavy denoising for noisy images
       'sharpened',          # Edge enhancement
       'morphological',      # Morphological operations
       'adaptive_bilateral'  # Adaptive bilateral filtering
   ]
   ```

2. **OCR Execution** with multiple attempts:
   ```python
   # Priority order:
   1. Local Tesseract OCR
   2. Cloud OCR API fallback (if configured)
   
   # For each preprocessing strategy:
   - Apply preprocessing
   - Run OCR
   - Check if extracted text is sufficient (medical parameters found)
   - If sufficient, return text; else try next strategy
   ```

3. **Medical Parameter Validation:**
   ```python
   medical_parameter_patterns = [
       r'(?i)hemoglobin|hb|hgb',
       r'(?i)rbc|red blood cell',
       r'(?i)wbc|white blood cell',
       r'(?i)platelet|plt',
       r'(?i)glucose|blood sugar',
       # ... 20+ more patterns
   ]
   ```

4. **Demographic Extraction** (Phase 1):
   ```python
   # Extract from OCR text:
   - Age (from "Age: XX" or DOB calculation)
   - Gender (from "Sex/Gender: M/F" or titles like Mr/Mrs)
   ```

**Output:** Raw OCR text containing medical report data

---

### Step 4: Parameter Parsing

**Files Involved:**
- `src/core/parser.py` - Main parser entry point
- `src/core/enhanced_blood_parser.py` - `EnhancedBloodParser` class

**What Happens:**

1. **Enhanced Parsing** (tries first):
   ```python
   class EnhancedBloodParser:
       # Comprehensive parameter patterns for:
       
       # Complete Blood Count (CBC)
       - White Blood Cell (WBC)
       - Red Blood Cell (RBC)
       - Hemoglobin
       - Hematocrit
       - MCV, MCH, MCHC, RDW
       - Platelet Count, MPV
       
       # WBC Differential
       - Neutrophil, Lymphocyte, Monocyte
       - Eosinophil, Basophil
       
       # Absolute Counts
       - Neutrophil Absolute, Lymphocyte Absolute, etc.
       
       # Chemistry Panel
       - Glucose, Cholesterol, Creatinine, BUN
       # ... and more
   ```

2. **Regex Pattern Matching:**
   ```python
   # Example pattern for Hemoglobin:
   patterns = [
       r'(?i)hemoglobin\s*\(?\s*hb\s*/?\s*hgb\s*\)?\s*\)?\s*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)',
       r'(?i)hemoglobin.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
       r'(?i)hb\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
       # Multiple patterns for each parameter to handle variations
   ]
   ```

3. **Value & Unit Extraction:**
   ```python
   # For each parameter found:
   parameters[param_name] = {
       "value": float_value,      # Numeric value
       "unit": extracted_unit,    # e.g., "g/dL", "%", "/cumm"
       "raw_text": original_text  # Original matched text
   }
   ```

4. **Fallback Parsing** if enhanced parsing fails:
   - Simpler regex patterns
   - Line-by-line processing
   - Basic pattern matching

**Output:** Dictionary of parsed parameters with values and units

---

### Step 5: Parameter Validation

**Files Involved:**
- `src/core/validator.py` - `validate_parameters()` function
- `src/core/dynamic_reference_ranges.py` - Age/gender-specific ranges
- `config/reference_ranges.json` - Reference range database

**What Happens:**

1. **Load Reference Ranges:**
   ```json
   // config/reference_ranges.json
   {
     "Hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
     "WBC": {"min": 4000, "max": 11000, "unit": "/cumm"},
     "Platelet": {"min": 150000, "max": 400000, "unit": "/cumm"},
     // ... 50+ parameters with reference ranges
   }
   ```

2. **Compare Values Against Reference Ranges:**
   ```python
   def validate_parameters(parsed_data):
       for param_name, param_info in parsed_data.items():
           value = param_info.get("value")
           
           if param_name in reference_ranges:
               ref = reference_ranges[param_name]
               
               if value < ref["min"]:
                   status = "LOW"
               elif value > ref["max"]:
                   status = "HIGH"
               else:
                   status = "NORMAL"
   ```

3. **Dynamic Reference Ranges** (age/gender-specific):
   ```python
   # Adjusts reference ranges based on:
   - Patient age (pediatric, adult, elderly)
   - Patient gender (male vs female ranges)
   - Example: Female Hemoglobin range is 12-16 g/dL
              Male Hemoglobin range is 14-18 g/dL
   ```

4. **Unit Conversion** (if needed):
   ```python
   # src/core/unit_converter.py
   - Converts non-standard units to standard units
   - Example: mg% → mg/dL
   ```

**Output:** Validated parameters with status (LOW/NORMAL/HIGH) and reference ranges

---

### Step 6: Results Interpretation

**Files Involved:**
- `src/core/interpreter.py` - `interpret_results()` function

**What Happens:**

1. **Generate Summary Statistics:**
   ```python
   interpretation = {
       "summary": {
           "total_parameters": len(validated_data),
           "normal": normal_count,
           "low": low_count,
           "high": high_count
       }
   }
   ```

2. **Identify Abnormal Parameters:**
   ```python
   abnormal_parameters = []
   for param_name, param_info in validated_data.items():
       if status in ["LOW", "HIGH"]:
           abnormal_parameters.append({
               "parameter": param_name,
               "value": param_info.get("value"),
               "status": status,
               "reference": param_info.get("reference_range")
           })
   ```

3. **Generate Basic Recommendations:**
   ```python
   if abnormal_count == 0:
       recommendations.append("All parameters are normal.")
   else:
       recommendations.append(f"Found {abnormal_count} abnormal parameter(s).")
       recommendations.append("Consult a doctor for detailed analysis.")
   ```

**Output:** Interpretation dictionary with summary, abnormal parameters, and basic recommendations

---

### Step 7: Multi-Model Analysis

**Files Involved:**
- `src/ui/UI.py` - `perform_multi_model_analysis()` function

**What Happens:**

#### MODEL 1: Rule-Based Parameter Analysis
```python
model1_parameter_analysis = {
    'total_parameters': count,
    'abnormal_parameters': abnormal_count,
    'normal_percentage': percentage,
    'severity_analysis': [
        {
            'parameter': 'Hemoglobin',
            'status': 'LOW',
            'deviation': 15.5,  # % deviation from normal
            'severity': 'Moderate'  # Mild (<10%), Moderate (10-25%), Severe (>25%)
        }
    ]
}
```

#### MODEL 2: Pattern Recognition & Correlation
```python
# Detects clinical patterns by correlating multiple parameters:

# Pattern 1: Anemia Detection
if hemoglobin_low:
    if MCV < 80:
        type = "Microcytic Anemia"  # Iron deficiency/Thalassemia
    elif MCV > 100:
        type = "Macrocytic Anemia"  # B12/Folate deficiency
    else:
        type = "Normocytic Anemia"  # Chronic disease/acute blood loss

# Pattern 2: Infection/Inflammation
if WBC_high:
    if Neutrophils > 70%:
        condition = "Bacterial Infection"
    elif Lymphocytes > 40%:
        condition = "Viral Infection"

# Pattern 3: Bleeding Risk
if Platelet_low:
    if platelet < 50000:
        severity = "Severe Thrombocytopenia"
    elif platelet < 100000:
        severity = "Moderate Thrombocytopenia"

# Pattern 4: Pancytopenia
if Hb_low AND WBC_low AND Platelet_low:
    condition = "Pancytopenia"  # Bone marrow dysfunction
```

#### MODEL 3: Risk Score Computation
```python
# Calculate risk scores (0-100 scale):

# Anemia Risk Score
if hemoglobin < 7:
    anemia_risk = 100
elif hemoglobin < 10:
    anemia_risk = 70
elif hemoglobin < 12:
    anemia_risk = 40
else:
    anemia_risk = 10

# Infection Risk Score (based on WBC)
# Bleeding Risk Score (based on Platelet count)

# Overall Health Score
overall_score = 100 - (anemia_risk * 0.3 + infection_risk * 0.3 + bleeding_risk * 0.4)
```

#### MODEL 4: Contextual Analysis
```python
# src/ui/UI.py - perform_contextual_analysis()

# Adjusts risks based on user context:
1. Age-based adjustments
   - Pediatric: Different reference ranges
   - Middle-aged (40-60): +20% cardiovascular risk
   - Elderly (60+): +40% risk modifier

2. Gender-based adjustments
   - Female: Hemoglobin 12-16 g/dL normal
   - Male: Hemoglobin 14-18 g/dL normal

3. Medical history impact
   - Diabetes: +30% metabolic risk
   - Hypertension: +20% cardiovascular risk
   - Heart Disease: +40% cardiovascular risk

4. Lifestyle factors
   - Smoker: +30% cardiovascular risk
   - Heavy alcohol: +25% liver risk
   - Sedentary: +15% metabolic risk
```

**Output:** Comprehensive analysis with patterns, conditions, risk scores, and traceable recommendations

---

### Step 8: Phase 2 - LLM Analysis

**Files Involved:**
- `src/phase2/phase2_integration_safe.py` - Integration layer
- `src/phase2/phase2_orchestrator.py` - LLM orchestration
- `src/phase2/csv_schema_adapter.py` - CSV schema validation
- `src/phase2/advanced_pattern_analysis.py` - Milestone-2 integration
- `src/utils/llm_provider.py` - Unified LLM provider

**What Happens:**

1. **Check LLM Availability:**
   ```python
   # Checks in order:
   1. Ollama server running? (localhost:11434)
   2. Mistral model available? (mistral:instruct)
   3. Hugging Face API token configured?
   ```

2. **CSV Schema Validation:**
   ```python
   # Validates CSV structure before LLM processing
   required_columns = ['test_name', 'value', 'unit', 'reference_range']
   adaptation_result = adapt_csv_for_phase2(csv_content)
   ```

3. **Model 1 - Parameter Interpretation (LLM):**
   ```python
   # System prompt: Medical Laboratory Specialist persona
   # Task: Classify each parameter as Low/Normal/High/Borderline
   
   prompt = """
   Analyze these laboratory parameters and classify each based on reference range:
   {csv_data}
   Output STRICT JSON format with classifications.
   """
   ```

4. **Model 2 - Pattern Risk Assessment (LLM):**
   ```python
   # Analyzes patterns and correlations
   # Identifies potential health conditions
   # Assesses risk levels
   ```

5. **Synthesis Engine:**
   ```python
   # Combines Model 1 & 2 results
   # Generates overall status and risk level
   # Identifies key concerns
   ```

6. **Recommendation Generator:**
   ```python
   # Generates:
   - Lifestyle recommendations
   - Follow-up guidance
   - Healthcare consultation advice
   ```

**Output:** Phase-2 analysis with LLM-powered insights, patterns, and recommendations

---

### Step 9: Advanced Risk Calculation

**Files Involved:**
- `src/core/advanced_risk_calculator.py` - `AdvancedRiskCalculator` class

**What Happens:**

1. **Framingham CVD Risk Score:**
   ```python
   # Calculates 10-year cardiovascular disease risk
   
   # Point factors:
   - Age points (by age range and gender)
   - Total cholesterol points (by age group)
   - HDL cholesterol points
   - Smoking status points
   - Blood pressure points
   
   # Risk calculation:
   total_points = age_pts + tc_pts + hdl_pts + smoke_pts + bp_pts
   risk_percent = risk_table[total_points]
   
   # Risk categories:
   - Low: < 10%
   - Moderate: 10-20%
   - High: > 20%
   ```

2. **Lipid Ratio Analysis:**
   ```python
   # Calculates:
   - Total Cholesterol / HDL ratio
   - LDL / HDL ratio
   - Triglyceride / HDL ratio
   ```

3. **Metabolic Syndrome Detection:**
   ```python
   # Checks for 3+ of these criteria:
   - Waist circumference > threshold
   - Triglycerides ≥ 150 mg/dL
   - HDL < 40 (men) or < 50 (women) mg/dL
   - Blood pressure ≥ 130/85 mmHg
   - Fasting glucose ≥ 100 mg/dL
   ```

**Output:** Cardiovascular risk percentage, lipid ratios, metabolic syndrome assessment

---

### Step 10: AI Chat Assistant

**Files Involved:**
- `src/core/enhanced_ai_agent.py` - `EnhancedAIAgent` class
- `src/core/intent_inference_engine.py` - Intent detection
- `src/core/clarifying_question_generator.py` - Follow-up questions
- `src/core/goal_oriented_workflow_manager.py` - Workflow execution
- `src/core/advanced_context_manager.py` - Conversation context
- `src/core/qa_assistant.py` - Q&A responses

**What Happens:**

1. **Session Initialization:**
   ```python
   agent = EnhancedAIAgent()
   session_id = agent.start_user_session(user_id, session_type="analysis")
   ```

2. **Message Processing Pipeline:**
   ```python
   def process_user_message(message, additional_context):
       # Step 1: Gather comprehensive context
       context = gather_context(report_data, conversation_history, user_profile)
       
       # Step 2: Infer user intent
       intent = intent_engine.infer_intent(message, context)
       # Intents: analyze_report, explain_parameter, dietary_advice, 
       #          exercise_advice, general_health, compare_reports
       
       # Step 3: Log conversation
       context_manager.add_conversation_message(role='user', content=message)
       
       # Step 4: Determine response strategy
       strategy = determine_strategy(intent, context)
       # Strategies: clarification_needed, workflow_execution,
       #             direct_answer, context_gathering
       
       # Step 5: Execute response strategy
       if strategy == 'clarification_needed':
           response = ask_clarifying_question()
       elif strategy == 'workflow_execution':
           response = execute_workflow()
       elif strategy == 'direct_answer':
           response = generate_answer(message, report_data)
       
       # Step 6: Log assistant response
       context_manager.add_conversation_message(role='assistant', content=response)
       
       return response
   ```

3. **Response Generation Examples:**
   ```python
   # Food/Diet questions:
   "🍎 **General Healthy Eating Guidelines:**
    • Fruits & Vegetables: Aim for 5+ servings daily
    • Whole Grains: Choose brown rice, oats, whole wheat
    ..."
   
   # Parameter-specific questions:
   "Your Hemoglobin is 10.5 g/dL which is LOW.
    This indicates possible anemia.
    Recommended: Iron-rich foods and consult your doctor."
   ```

**Output:** Contextual, personalized responses to user health questions

---

### Step 11: Results Display

**Files Involved:**
- `src/ui/UI.py` - Streamlit interface
- `src/ui/chat_interface.py` - Chat UI components

**What Happens:**

1. **Parameter Table Display:**
   ```python
   # Shows all extracted parameters:
   | Parameter | Value | Unit | Reference Range | Status |
   |-----------|-------|------|-----------------|--------|
   | Hemoglobin| 12.5  | g/dL | 12.0-17.0      | NORMAL |
   | WBC       | 11500 | /cumm| 4000-11000     | HIGH   |
   ```

2. **Risk Score Visualizations:**
   ```python
   # Displays risk gauges/meters for:
   - Anemia Risk
   - Infection Risk
   - Bleeding Risk
   - Overall Health Score
   - Cardiovascular Risk (Framingham)
   ```

3. **Pattern/Condition Cards:**
   ```python
   # Shows detected patterns:
   ⚠️ Bacterial Infection Pattern
   - WBC: 11500 /cumm (HIGH)
   - Neutrophils: 75% (HIGH)
   - Likelihood: High
   ```

4. **Traceable Recommendations:**
   ```python
   # Each recommendation shows:
   📋 Immune Support (Priority: High)
   
   Finding: WBC: 11500/cumm
   Risk: Infection Risk Score: 50/100 - Elevated WBC indicates active infection
   Reasoning: Because WBC count is elevated → active immune response → 
              possible ongoing infection
   
   Actions:
   • Boost immunity with Vitamin C and Zinc
   • Maintain good hygiene
   • Get adequate rest
   ```

5. **Interactive Chat Interface:**
   ```python
   # Streamlit chat interface:
   - User input text box
   - Chat history display
   - AI responses with markdown formatting
   - Quick action buttons
   ```

---

## Module Reference

| Module | Purpose |
|--------|---------|
| `app.py` | HuggingFace Spaces entry point |
| `start_project.py` | Local development entry point |
| `src/ui/UI.py` | Main Streamlit interface (2500+ lines) |
| `src/core/ocr_engine.py` | OCR processing with multiple strategies |
| `src/core/parser.py` | Parameter parsing entry point |
| `src/core/enhanced_blood_parser.py` | Comprehensive parameter extraction |
| `src/core/validator.py` | Reference range validation |
| `src/core/interpreter.py` | Results interpretation |
| `src/core/enhanced_ai_agent.py` | Intelligent chat assistant |
| `src/core/advanced_risk_calculator.py` | Framingham & metabolic risk |
| `src/core/dynamic_reference_ranges.py` | Age/gender-specific ranges |
| `src/core/unit_converter.py` | Unit standardization |
| `src/phase1/phase1_extractor.py` | Image-aware OCR reconstruction |
| `src/phase1/table_extractor.py` | Table extraction from images |
| `src/phase1/medical_validator.py` | Medical document validation |
| `src/phase2/phase2_orchestrator.py` | LLM analysis orchestration |
| `src/phase2/phase2_integration_safe.py` | Safe Phase-2 integration |
| `src/phase2/csv_schema_adapter.py` | CSV schema validation |
| `src/phase2/advanced_pattern_analysis.py` | Milestone-2 pattern analysis |
| `src/utils/llm_provider.py` | Ollama + HuggingFace LLM provider |
| `src/utils/ocr_provider.py` | OCR provider abstraction |
| `src/utils/ollama_manager.py` | Ollama service management |
| `src/utils/csv_converter.py` | JSON to CSV conversion |
| `config/reference_ranges.json` | Medical reference ranges |

---

## Data Flow Diagram

```
┌──────────────┐
│ Blood Report │
│ (PDF/Image)  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐     ┌─────────────────┐
│  OCR Processing  │────▶│  Raw Text       │
│  (6 strategies)  │     │  Extraction     │
└──────────────────┘     └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Parameter       │
                         │ Parsing         │
                         │ (20+ params)    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Validation      │
                         │ (Reference      │
                         │  Ranges)        │
                         └────────┬────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ Multi-Model     │   │ Phase-2 LLM     │   │ Advanced Risk   │
   │ Analysis        │   │ Analysis        │   │ Calculator      │
   │ (4 Models)      │   │ (Mistral 7B)    │   │ (Framingham)    │
   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Enhanced AI     │
                         │ Agent           │
                         │ (Chat Q&A)      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Results Display │
                         │ (Streamlit UI)  │
                         └─────────────────┘
```

---

## Summary

The Blood Report Analysis System processes medical reports through a sophisticated pipeline:

1. **Input** → File upload (PDF/Image/JSON/CSV)
2. **Extraction** → OCR with 6 preprocessing strategies
3. **Parsing** → 20+ medical parameter extraction
4. **Validation** → Reference range comparison with status assignment
5. **Analysis** → 4-model analysis (parameters, patterns, risks, context)
6. **LLM Enhancement** → Mistral 7B for natural language insights
7. **Risk Calculation** → Framingham CVD, lipid ratios, metabolic syndrome
8. **AI Assistant** → Intent-aware Q&A with contextual responses
9. **Output** → Interactive dashboard with traceable recommendations

Each step is designed to be robust with fallbacks, ensuring reliable analysis even with poor quality inputs or unavailable services.

---

*Document generated on: January 18, 2026*
*Project: Multi-Model AI Agent - Health Diagnostics*
