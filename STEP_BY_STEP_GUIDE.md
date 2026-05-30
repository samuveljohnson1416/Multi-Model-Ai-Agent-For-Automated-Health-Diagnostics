# 🩺 Multi-Model AI Agent for Health Diagnostics
## Complete Step-by-Step Execution Guide

> This document provides a detailed walkthrough of every step that occurs when processing a blood report through this system.

---

## 📋 Quick Overview

```
USER UPLOADS FILE → OCR EXTRACTION → PARAMETER PARSING → VALIDATION → 
MULTI-MODEL ANALYSIS → LLM INSIGHTS → RISK CALCULATION → CHAT ASSISTANT → DISPLAY RESULTS
```

---

## 🚀 STEP 1: Application Launch

### Entry Points

| File | Purpose | When Used |
|------|---------|-----------|
| `start_project.py` | Local development launcher | Running locally |
| `app.py` | Hugging Face Spaces entry | Cloud deployment |

### What Happens on Startup

```
1. Python environment validation (requires Python 3.8+)
2. Working directory verification
3. System path configuration (adds 'src' to path)
4. LLM provider priority setting (Ollama first, then HuggingFace API)
5. Streamlit server launch on port 8501
6. Ollama service auto-start attempt (if available)
7. UI module import and initialization
```

### Key Code Flow
```python
# start_project.py
def main():
    # Validate environment
    if not Path("src/ui/UI.py").exists():
        sys.exit(1)  # Must run from project root
    
    # Launch Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "src/ui/UI.py", 
        "--server.port", "8501"
    ])
```

---

## 📁 STEP 2: File Upload & Detection

### Location: `src/ui/UI.py` + `src/core/ocr_engine.py`

### Supported File Formats

| Format | Extension | Processing Method |
|--------|-----------|-------------------|
| PDF | `.pdf` | pdfplumber (digital) or OCR (scanned) |
| Image | `.png`, `.jpg`, `.jpeg` | OCR with preprocessing |
| JSON | `.json` | Direct JSON parsing |
| CSV | `.csv` | CSV adapter |
| Text | `.txt` | Direct text processing |

### File Type Detection Logic

```python
def determine_file_type(uploaded_file):
    file_type = uploaded_file.type  # MIME type
    file_name = uploaded_file.name.lower()
    
    if "pdf" in file_type or file_name.endswith('.pdf'):
        return "pdf"
    elif file_type in ["image/png", "image/jpeg"]:
        return "image"
    elif "json" in file_type or file_name.endswith('.json'):
        return "json"
    elif "csv" in file_type or file_name.endswith('.csv'):
        return "csv"
    else:
        return "unsupported"
```

### Processing Routes

```
                    ┌─────────────────────┐
                    │   Uploaded File     │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
       ┌────────┐        ┌────────┐        ┌────────┐
       │  PDF   │        │ Image  │        │ JSON/  │
       │        │        │        │        │  CSV   │
       └───┬────┘        └───┬────┘        └───┬────┘
           │                 │                 │
           ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐      ┌──────────┐
     │pdfplumber│      │ Tesseract│      │ Direct   │
     │  + OCR   │      │   OCR    │      │ Parse    │
     └──────────┘      └──────────┘      └──────────┘
```

---

## 🔍 STEP 3: OCR Processing (Text Extraction)

### Location: `src/core/ocr_engine.py`

### The MedicalOCROrchestrator Class

The system uses a sophisticated OCR orchestrator that tries **6 different preprocessing strategies** to extract text from medical documents.

### Preprocessing Strategies

| # | Strategy | Best For | Technique |
|---|----------|----------|-----------|
| 1 | `standard` | Good quality images | Bilateral filter + Adaptive threshold |
| 2 | `high_contrast` | Faded/low contrast | Histogram equalization + CLAHE |
| 3 | `denoised` | Noisy/grainy images | FastNlMeansDenoising |
| 4 | `sharpened` | Blurry images | Unsharp masking |
| 5 | `morphological` | Text with artifacts | Erosion + Dilation |
| 6 | `adaptive_bilateral` | Mixed quality | Adaptive bilateral filtering |

### OCR Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Image Input                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FOR EACH preprocessing_strategy:                                │
│    1. Apply preprocessing (convert to grayscale, enhance, etc.) │
│    2. Run Tesseract OCR                                         │
│    3. Check if text is "sufficient"                             │
│       - Length > 5 characters                                   │
│       - Contains medical parameter patterns                      │
│    4. If sufficient → RETURN text                               │
│    5. If not → try next strategy                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  If all strategies fail → Try Cloud OCR API fallback            │
└─────────────────────────────────────────────────────────────────┘
```

### Medical Parameter Detection Patterns

The system looks for these patterns to validate OCR success:

```python
medical_parameter_patterns = [
    r'(?i)hemoglobin|hb|hgb',
    r'(?i)rbc|red blood cell',
    r'(?i)wbc|white blood cell',
    r'(?i)platelet|plt',
    r'(?i)glucose|blood sugar',
    r'(?i)cholesterol|chol',
    r'(?i)creatinine|creat',
    r'(?i)neutrophil|lymphocyte|eosinophil|monocyte|basophil',
    r'(?i)mcv|mch|mchc|rdw',
    r'(?i)mg/dl|g/dl|/ul|/cumm',  # Unit patterns
]
```

### Phase 1 Extraction (Demographics)

```python
# src/phase1/phase1_extractor.py
# Extracts patient demographics from OCR text

Age Patterns:
- "Age: 45 years"
- "45 yrs old"
- DOB calculation

Gender Patterns:
- "Sex: Male/Female"
- "Gender: M/F"
- Title inference (Mr/Mrs/Ms)
```

---

## 📊 STEP 4: Parameter Parsing

### Location: `src/core/parser.py` + `src/core/enhanced_blood_parser.py`

### Supported Blood Parameters (20+)

#### Complete Blood Count (CBC)
| Parameter | Aliases | Standard Unit |
|-----------|---------|---------------|
| White Blood Cell | WBC, Leucocyte | K/mcL |
| Red Blood Cell | RBC, Erythrocyte | M/mcL |
| Hemoglobin | Hb, Hgb, Haemoglobin | g/dL |
| Hematocrit | HCT, PCV | % |
| MCV | Mean Cell Volume | fL |
| MCH | Mean Cell Hemoglobin | pg |
| MCHC | Mean Cell Hb Conc | g/dL |
| RDW | Red Cell Dist Width | % |
| Platelet Count | PLT, Thrombocyte | K/mcL |
| MPV | Mean Platelet Volume | fL |

#### WBC Differential
| Parameter | Aliases | Standard Unit |
|-----------|---------|---------------|
| Neutrophil | Neut, Polymorphs | % |
| Lymphocyte | Lymph | % |
| Monocyte | Mono | % |
| Eosinophil | Eos | % |
| Basophil | Baso | % |

#### Chemistry Panel
| Parameter | Aliases | Standard Unit |
|-----------|---------|---------------|
| Glucose | Blood Sugar, FBS | mg/dL |
| Cholesterol | CHOL, Total Cholesterol | mg/dL |
| Creatinine | CREAT, Serum Creatinine | mg/dL |
| BUN | Urea, Blood Urea Nitrogen | mg/dL |

### Parsing Algorithm

```python
def parse_blood_report(ocr_text):
    # Step 1: Try enhanced parsing
    enhanced_result = parse_enhanced_blood_report(ocr_text)
    if enhanced_result:
        return enhanced_result
    
    # Step 2: Fallback to basic parsing
    return _parse_blood_report_fallback(ocr_text)

# Enhanced parsing uses multiple regex patterns per parameter:
patterns = [
    r'(?i)hemoglobin\s*\(?\s*hb\s*/?\s*hgb\s*\)?.*?(\d+\.?\d*)',
    r'(?i)hemoglobin.*?(\d+\.?\d*)\s*([a-zA-Z/]+)',
    r'(?i)hb\s*[:/].*?(\d+\.?\d*)',
]
```

### Output Structure

```python
# Parsed parameter dictionary
{
    "Hemoglobin": {
        "value": 12.5,
        "unit": "g/dL",
        "raw_text": "Hemoglobin (Hb): 12.5 g/dL"
    },
    "WBC": {
        "value": 8500,
        "unit": "/cumm",
        "raw_text": "WBC Count: 8500 /cumm"
    },
    # ... more parameters
}
```

---

## ✅ STEP 5: Parameter Validation

### Location: `src/core/validator.py` + `config/reference_ranges.json`

### Reference Range Database

```json
// config/reference_ranges.json (excerpt)
{
  "Hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
  "RBC": {"min": 4.5, "max": 5.5, "unit": "mill/cumm"},
  "WBC": {"min": 4000, "max": 11000, "unit": "/cumm"},
  "Platelet": {"min": 150000, "max": 400000, "unit": "/cumm"},
  "MCV": {"min": 80, "max": 100, "unit": "fL"},
  "MCH": {"min": 27, "max": 32, "unit": "pg"},
  "MCHC": {"min": 32, "max": 36, "unit": "g/dL"},
  "Neutrophils": {"min": 40, "max": 70, "unit": "%"},
  "Lymphocytes": {"min": 20, "max": 40, "unit": "%"},
  "Glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
  "Cholesterol": {"min": 0, "max": 200, "unit": "mg/dL"}
}
```

### Validation Logic

```python
def validate_parameters(parsed_data):
    validated_data = {}
    
    for param_name, param_info in parsed_data.items():
        value = param_info.get("value")
        
        if param_name in reference_ranges:
            ref = reference_ranges[param_name]
            min_val = ref.get("min")
            max_val = ref.get("max")
            
            # Status determination
            if value < min_val:
                status = "LOW"
            elif value > max_val:
                status = "HIGH"
            else:
                status = "NORMAL"
            
            validated_data[param_name] = {
                "value": value,
                "unit": param_info.get("unit"),
                "status": status,
                "reference_range": f"{min_val} - {max_val}"
            }
    
    return validated_data
```

### Dynamic Reference Ranges

The system adjusts reference ranges based on:

```python
# src/core/dynamic_reference_ranges.py

# Age-based adjustments
if age < 18:
    # Pediatric reference ranges
elif age >= 60:
    # Elderly reference ranges

# Gender-based adjustments
if gender == "Female":
    hemoglobin_range = (12.0, 16.0)  # g/dL
elif gender == "Male":
    hemoglobin_range = (14.0, 18.0)  # g/dL
```

### Output Structure

```python
{
    "Hemoglobin": {
        "value": 10.5,
        "unit": "g/dL",
        "status": "LOW",
        "reference_range": "12.0 - 17.0 g/dL"
    },
    "WBC": {
        "value": 8500,
        "unit": "/cumm",
        "status": "NORMAL",
        "reference_range": "4000 - 11000 /cumm"
    }
}
```

---

## 📝 STEP 6: Results Interpretation

### Location: `src/core/interpreter.py`

### Interpretation Process

```python
def interpret_results(validated_data):
    interpretation = {
        "summary": {},
        "abnormal_parameters": [],
        "recommendations": []
    }
    
    # Count parameters by status
    low_count = high_count = normal_count = 0
    
    for param_name, param_info in validated_data.items():
        status = param_info.get("status")
        
        if status == "LOW":
            low_count += 1
            interpretation["abnormal_parameters"].append({
                "parameter": param_name,
                "value": param_info.get("value"),
                "status": "LOW",
                "reference": param_info.get("reference_range")
            })
        elif status == "HIGH":
            high_count += 1
            interpretation["abnormal_parameters"].append(...)
        else:
            normal_count += 1
    
    # Generate summary
    interpretation["summary"] = {
        "total_parameters": len(validated_data),
        "normal": normal_count,
        "low": low_count,
        "high": high_count
    }
    
    # Basic recommendations
    if low_count + high_count == 0:
        interpretation["recommendations"].append("All parameters are normal.")
    else:
        interpretation["recommendations"].append(
            f"Found {low_count + high_count} abnormal parameter(s)."
        )
        interpretation["recommendations"].append(
            "Consult a doctor for detailed analysis."
        )
    
    return interpretation
```

---

## 🤖 STEP 7: Multi-Model Analysis

### Location: `src/ui/UI.py` - `perform_multi_model_analysis()`

The system runs **4 analytical models** in parallel:

### MODEL 1: Parameter Analysis (Rule-Based)

```python
# Calculates severity for each abnormal parameter

model1_parameter_analysis = {
    'total_parameters': 15,
    'abnormal_parameters': 3,
    'normal_percentage': 80.0,
    'severity_analysis': [
        {
            'parameter': 'Hemoglobin',
            'status': 'LOW',
            'deviation': 15.5,  # % below minimum
            'severity': 'Moderate'  # Mild <10%, Moderate 10-25%, Severe >25%
        }
    ]
}
```

### MODEL 2: Pattern Recognition

```python
# Detects clinical patterns by correlating multiple parameters

# Pattern 1: ANEMIA DETECTION
if hemoglobin is LOW:
    if MCV < 80 fL:
        → Microcytic Anemia (Iron deficiency / Thalassemia)
    elif MCV > 100 fL:
        → Macrocytic Anemia (B12/Folate deficiency)
    else:
        → Normocytic Anemia (Chronic disease / Blood loss)

# Pattern 2: INFECTION ANALYSIS
if WBC is HIGH:
    if Neutrophils > 70%:
        → Bacterial Infection (High likelihood)
    elif Lymphocytes > 40%:
        → Viral Infection (Moderate likelihood)
elif WBC is LOW:
    → Immunodeficiency Risk

# Pattern 3: BLEEDING RISK
if Platelet < 50,000:
    → Severe Thrombocytopenia (High bleeding risk)
elif Platelet < 100,000:
    → Moderate Thrombocytopenia
elif Platelet < 150,000:
    → Mild Thrombocytopenia

# Pattern 4: PANCYTOPENIA
if Hemoglobin LOW AND WBC LOW AND Platelet LOW:
    → Pancytopenia (Bone marrow dysfunction suspected)
```

### MODEL 3: Risk Score Computation

```python
# Calculates risk scores on 0-100 scale

# ANEMIA RISK SCORE
if hemoglobin < 7:    score = 100  # Critical
elif hemoglobin < 10: score = 70   # Severe
elif hemoglobin < 12: score = 40   # Moderate
else:                 score = 10   # Low

# INFECTION RISK SCORE
if WBC < 2000:        score = 90   # Severe immunosuppression
elif WBC < 4000:      score = 60   # Mild immunosuppression
elif WBC > 15000:     score = 50   # Active infection
elif WBC > 11000:     score = 30   # Mild elevation
else:                 score = 10   # Normal

# BLEEDING RISK SCORE
if platelet < 20000:  score = 100  # Critical
elif platelet < 50000: score = 80  # Severe
elif platelet < 100000: score = 50 # Moderate
elif platelet < 150000: score = 30 # Mild
else:                  score = 10  # Normal

# OVERALL HEALTH SCORE
overall = 100 - (anemia_risk * 0.3 + infection_risk * 0.3 + bleeding_risk * 0.4)
```

### MODEL 4: Contextual Analysis

```python
# Adjusts risks based on patient context

# AGE MODIFIERS
if age < 18:       modifier = 1.0   # Pediatric - different ranges
elif age < 40:     modifier = 1.0   # Young adult - baseline
elif age < 60:     modifier = 1.2   # Middle-aged - +20% risk
else:              modifier = 1.4   # Elderly - +40% risk

# MEDICAL HISTORY MODIFIERS
if "Diabetes" in history:     modifier += 0.3
if "Hypertension" in history: modifier += 0.2
if "Heart Disease" in history: modifier += 0.4

# LIFESTYLE MODIFIERS
if smoker:                    modifier += 0.3
if alcohol == "Heavy":        modifier += 0.25
if exercise == "Sedentary":   modifier += 0.15

# ADJUSTED RISK
adjusted_risk = base_risk * total_modifier
```

### Traceable Recommendations

Each recommendation includes a **traceability chain**:

```python
{
    'category': 'Anemia Management',
    'priority': 'High',
    'traceability': {
        'finding': 'Hemoglobin: 9.5 g/dL',
        'risk': 'Anemia Risk Score: 70/100 (Severe)',
        'reasoning': 'Because hemoglobin is low → reduced oxygen-carrying '
                    'capacity → fatigue, weakness, organ strain'
    },
    'actions': [
        'Increase iron-rich foods (spinach, red meat, legumes)',
        'Take Vitamin C with iron for better absorption',
        'Consider iron/B12 supplements after consulting doctor'
    ]
}
```

---

## 🧠 STEP 8: Phase 2 - LLM Analysis

### Location: `src/phase2/` directory

### Components

| File | Purpose |
|------|---------|
| `phase2_integration_safe.py` | Integration layer with safety checks |
| `phase2_orchestrator.py` | LLM orchestration |
| `csv_schema_adapter.py` | CSV validation |
| `advanced_pattern_analysis.py` | Milestone-2 integration |

### LLM Provider Priority

```python
# src/utils/llm_provider.py

# Check order:
1. Ollama (localhost:11434) with mistral:instruct
2. Hugging Face Inference API (mistralai/Mistral-7B-Instruct-v0.2)
3. Fallback to rule-based analysis
```

### Phase 2 Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Check LLM Availability                                  │
│  - Ollama running? Mistral model loaded?                        │
│  - HuggingFace API token configured?                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: CSV Schema Validation                                   │
│  - Required columns: test_name, value, unit, reference_range    │
│  - Adapt/transform if needed                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Model 1 - Parameter Interpretation (LLM)               │
│  Persona: Medical Laboratory Specialist                         │
│  Task: Classify each parameter as Low/Normal/High/Borderline    │
│  Output: Strict JSON with classifications                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Model 2 - Pattern Risk Assessment (LLM)                │
│  - Identify correlations between parameters                     │
│  - Detect potential conditions                                  │
│  - Assess risk levels                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Synthesis Engine                                        │
│  - Combine Model 1 & 2 results                                  │
│  - Generate overall status                                      │
│  - Identify key concerns                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Recommendation Generator                                │
│  - Lifestyle recommendations                                    │
│  - Follow-up guidance                                           │
│  - Healthcare consultation advice                               │
└─────────────────────────────────────────────────────────────────┘
```

### LLM Prompt Example

```python
system_prompt = """You are a Medical Laboratory Specialist (MD) with 
15+ years of experience in clinical laboratory medicine.
Your ONLY task is to compare laboratory test values with reference ranges.
You must output STRICT JSON ONLY with no additional text.
Never diagnose diseases.
Use only: Low, Normal, High, Borderline."""

prompt = """Analyze these laboratory parameters:
{csv_data}

Output JSON format:
{
  "interpretations": [...],
  "summary": {"total_tests": N, "abnormal_count": N}
}"""
```

---

## 📈 STEP 9: Advanced Risk Calculation

### Location: `src/core/advanced_risk_calculator.py`

### Framingham CVD Risk Score (10-Year Risk)

```python
# Calculates probability of cardiovascular event in next 10 years

Point Factors:
┌─────────────────┬──────────────────────────────────────────┐
│ Factor          │ Points Assigned                          │
├─────────────────┼──────────────────────────────────────────┤
│ Age             │ -9 to +13 (varies by age range & gender) │
│ Total Cholesterol│ 0 to +11 (based on age and value)       │
│ HDL Cholesterol │ -1 to +2 (higher HDL = fewer points)     │
│ Smoking Status  │ 0 to +9 (if smoker, varies by age)       │
│ Blood Pressure  │ 0 to +3 (based on hypertension status)   │
└─────────────────┴──────────────────────────────────────────┘

Total Points → Risk Percentage:
< 0 points  →  < 1%
0-4 points  →  1%
5-6 points  →  2%
7 points    →  3%
8 points    →  4%
9 points    →  5%
...
17+ points  →  ≥30%

Risk Categories:
- Low:      < 10%
- Moderate: 10-20%
- High:     > 20%
```

### Lipid Ratio Analysis

```python
# Total Cholesterol / HDL Ratio
optimal:    < 3.5
borderline: 3.5 - 5.0
high_risk:  > 5.0

# LDL / HDL Ratio
optimal:    < 2.5
borderline: 2.5 - 3.5
high_risk:  > 3.5

# Triglyceride / HDL Ratio
optimal:    < 2.0
high_risk:  > 4.0
```

### Metabolic Syndrome Detection

```python
# Requires 3 or more criteria:
criteria = {
    "waist_circumference": "> 102 cm (men) or > 88 cm (women)",
    "triglycerides": "≥ 150 mg/dL",
    "hdl_cholesterol": "< 40 mg/dL (men) or < 50 mg/dL (women)",
    "blood_pressure": "≥ 130/85 mmHg",
    "fasting_glucose": "≥ 100 mg/dL"
}

if criteria_met >= 3:
    metabolic_syndrome = True
```

---

## 💬 STEP 10: AI Chat Assistant

### Location: `src/core/enhanced_ai_agent.py`

### Components

| Module | Purpose |
|--------|---------|
| `intent_inference_engine.py` | Understands what user is asking |
| `clarifying_question_generator.py` | Asks follow-up questions |
| `goal_oriented_workflow_manager.py` | Executes complex tasks |
| `advanced_context_manager.py` | Maintains conversation history |
| `qa_assistant.py` | Generates responses |

### Message Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  User Message: "What foods should I eat for my low hemoglobin?"│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Gather Context                                          │
│  - Current report data                                          │
│  - Conversation history                                         │
│  - User profile (age, gender, conditions)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Intent Inference                                        │
│  Detected Intent: "dietary_advice"                              │
│  Confidence: 0.92                                               │
│  Related Parameter: "hemoglobin"                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Determine Response Strategy                             │
│  - Has report? YES                                              │
│  - Confidence high? YES                                         │
│  → Strategy: "direct_answer"                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Generate Response                                       │
│  "Based on your hemoglobin level of 10.5 g/dL (LOW):           │
│   🍎 Iron-rich foods: spinach, red meat, lentils               │
│   🍊 Vitamin C sources for better absorption                    │
│   ⚠️ Consult doctor for supplements if needed"                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Log Conversation                                        │
│  - Store user message with intent                               │
│  - Store assistant response                                     │
│  - Update user preferences                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Intents

| Intent | Example Questions |
|--------|-------------------|
| `analyze_report` | "Analyze my report", "What do my results mean?" |
| `explain_parameter` | "What is hemoglobin?", "Why is WBC important?" |
| `dietary_advice` | "What should I eat?", "Foods for anemia?" |
| `exercise_advice` | "Can I exercise?", "Workout recommendations?" |
| `compare_reports` | "How has my hemoglobin changed?" |
| `general_health` | "How can I improve my health?" |

### Response Examples

```python
# Food/Diet Response
"""🍎 **Foods to Help with Low Hemoglobin:**

**Iron-Rich Foods:**
• Red meat (beef, lamb)
• Spinach and leafy greens
• Legumes (lentils, chickpeas)
• Fortified cereals

**Vitamin C (helps iron absorption):**
• Oranges, lemons
• Bell peppers
• Tomatoes

**Avoid with iron supplements:**
• Tea and coffee (inhibit absorption)
• Calcium-rich foods (take separately)

⚠️ *Your Hemoglobin is 10.5 g/dL. Consult your doctor about supplements.*"""
```

---

## 🖥️ STEP 11: Results Display

### Location: `src/ui/UI.py`

### UI Components

#### 1. Parameter Table

```
┌────────────────┬───────┬────────┬─────────────────┬─────────┐
│ Parameter      │ Value │ Unit   │ Reference Range │ Status  │
├────────────────┼───────┼────────┼─────────────────┼─────────┤
│ Hemoglobin     │ 10.5  │ g/dL   │ 12.0 - 17.0     │ 🔴 LOW  │
│ WBC            │ 11500 │ /cumm  │ 4000 - 11000    │ 🟡 HIGH │
│ RBC            │ 4.8   │ M/mcL  │ 4.5 - 5.5       │ 🟢 NORMAL│
│ Platelet       │ 250000│ /cumm  │ 150000 - 400000 │ 🟢 NORMAL│
└────────────────┴───────┴────────┴─────────────────┴─────────┘
```

#### 2. Risk Score Gauges

```
┌────────────────────────────────────────────────────────────────┐
│  RISK ASSESSMENT                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Anemia Risk:     [██████████░░░░░░░░░░] 50/100 (Moderate)    │
│                                                                 │
│  Infection Risk:  [████░░░░░░░░░░░░░░░░] 20/100 (Low)         │
│                                                                 │
│  Bleeding Risk:   [██░░░░░░░░░░░░░░░░░░] 10/100 (Low)         │
│                                                                 │
│  Overall Health:  [████████████████░░░░] 80/100 (Good)        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### 3. Pattern/Condition Cards

```
┌────────────────────────────────────────────────────────────────┐
│ ⚠️ MICROCYTIC ANEMIA PATTERN DETECTED                          │
├────────────────────────────────────────────────────────────────┤
│ Parameters Involved:                                           │
│ • Hemoglobin: 10.5 g/dL (LOW)                                 │
│ • MCV: 72 fL (LOW)                                            │
│ • MCH: 25 pg (LOW)                                            │
│                                                                │
│ Possible Causes:                                               │
│ • Iron deficiency anemia                                       │
│ • Thalassemia trait                                           │
│                                                                │
│ Likelihood: HIGH                                               │
└────────────────────────────────────────────────────────────────┘
```

#### 4. Recommendations Section

```
┌────────────────────────────────────────────────────────────────┐
│ 📋 PERSONALIZED RECOMMENDATIONS                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ 🩸 ANEMIA MANAGEMENT (Priority: High)                          │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Finding: Hemoglobin 10.5 g/dL (LOW)                      │  │
│ │ Risk: Anemia Risk Score: 50/100 (Moderate)               │  │
│ │ Reasoning: Low hemoglobin → reduced oxygen capacity →    │  │
│ │            fatigue and weakness                           │  │
│ └──────────────────────────────────────────────────────────┘  │
│ Actions:                                                       │
│ ✓ Increase iron-rich foods (spinach, red meat, legumes)       │
│ ✓ Take Vitamin C with iron for better absorption              │
│ ✓ Consider iron supplements after consulting doctor           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

#### 5. Chat Interface

```
┌────────────────────────────────────────────────────────────────┐
│ 💬 AI HEALTH ASSISTANT                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ 👤 You: What does my low hemoglobin mean?                      │
│                                                                │
│ 🤖 Assistant: Your hemoglobin level of 10.5 g/dL is below     │
│    the normal range (12-17 g/dL). This indicates anemia,      │
│    which means your blood has reduced capacity to carry       │
│    oxygen. Common symptoms include:                            │
│    • Fatigue and weakness                                     │
│    • Shortness of breath                                      │
│    • Pale skin                                                │
│                                                                │
│    Based on your MCV (72 fL), this appears to be microcytic   │
│    anemia, often caused by iron deficiency.                   │
│                                                                │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Type your question...                              [Send] │  │
│ └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 Complete Module Reference

```
Multi-Model-AI-Agent---Health-Diagnostics/
│
├── app.py                          # HuggingFace Spaces entry
├── start_project.py                # Local development entry
├── requirements.txt                # Python dependencies
├── packages.txt                    # System packages
│
├── config/
│   └── reference_ranges.json       # Medical reference ranges (50+ params)
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                       # Core analysis modules
│   │   ├── ocr_engine.py           # OCR with 6 preprocessing strategies
│   │   ├── parser.py               # Parameter parsing entry
│   │   ├── enhanced_blood_parser.py # Comprehensive parameter extraction
│   │   ├── validator.py            # Reference range validation
│   │   ├── interpreter.py          # Results interpretation
│   │   ├── enhanced_ai_agent.py    # Intelligent chat assistant
│   │   ├── intent_inference_engine.py # User intent detection
│   │   ├── clarifying_question_generator.py # Follow-up questions
│   │   ├── goal_oriented_workflow_manager.py # Task workflows
│   │   ├── advanced_context_manager.py # Conversation history
│   │   ├── qa_assistant.py         # Q&A response generation
│   │   ├── advanced_risk_calculator.py # Framingham CVD risk
│   │   ├── dynamic_reference_ranges.py # Age/gender-specific ranges
│   │   ├── unit_converter.py       # Unit normalization
│   │   └── comprehensive_report_generator.py # Report generation
│   │
│   ├── phase1/                     # Phase 1 - OCR & Extraction
│   │   ├── phase1_extractor.py     # Demographics extraction
│   │   ├── table_extractor.py      # Table extraction from images
│   │   └── medical_validator.py    # Medical document validation
│   │
│   ├── phase2/                     # Phase 2 - LLM Analysis
│   │   ├── phase2_orchestrator.py  # LLM orchestration
│   │   ├── phase2_integration_safe.py # Safe integration layer
│   │   ├── csv_schema_adapter.py   # CSV validation
│   │   └── advanced_pattern_analysis.py # Pattern analysis
│   │
│   ├── ui/                         # User Interface
│   │   ├── UI.py                   # Main Streamlit interface
│   │   └── chat_interface.py       # Chat UI components
│   │
│   └── utils/                      # Utility Functions
│       ├── llm_provider.py         # Ollama + HuggingFace provider
│       ├── ocr_provider.py         # OCR provider abstraction
│       ├── ollama_manager.py       # Ollama service management
│       └── csv_converter.py        # JSON to CSV conversion
│
└── tests/
    ├── __init__.py
    └── test_suite.py               # Unit tests
```

---

## 🔄 Complete Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─────────┐                                                                │
│  │ Upload  │                                                                │
│  │  File   │                                                                │
│  └────┬────┘                                                                │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ File Type   │───▶│    OCR      │───▶│   Parser    │───▶│  Validator  │  │
│  │ Detection   │    │ Extraction  │    │ (20+ params)│    │ (Ref Ranges)│  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                                   │         │
│       ┌──────────────────────────────────────────────────────────┘         │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     ANALYSIS LAYER                                   │   │
│  ├───────────────┬───────────────┬───────────────┬────────────────────┤   │
│  │   Model 1     │   Model 2     │   Model 3     │     Model 4        │   │
│  │  Parameter    │   Pattern     │    Risk       │    Contextual      │   │
│  │  Analysis     │  Recognition  │  Computation  │    Analysis        │   │
│  └───────┬───────┴───────┬───────┴───────┬───────┴────────┬───────────┘   │
│          │               │               │                │               │
│          └───────────────┴───────────────┴────────────────┘               │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       LLM ANALYSIS (Phase 2)                         │   │
│  │            Mistral 7B via Ollama or HuggingFace API                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ADVANCED RISK CALCULATOR                          │   │
│  │           Framingham CVD | Lipid Ratios | Metabolic Syndrome        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       RESULTS DISPLAY                                │   │
│  │    Parameter Table | Risk Gauges | Pattern Cards | Recommendations  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     AI CHAT ASSISTANT                                │   │
│  │              Interactive Q&A with Context Awareness                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Summary

The Multi-Model AI Agent for Health Diagnostics processes blood reports through **11 distinct steps**:

| Step | Name | Key Action |
|------|------|------------|
| 1 | Application Launch | Initialize Streamlit, configure paths |
| 2 | File Upload | Detect file type, route to processor |
| 3 | OCR Processing | Extract text using 6 strategies |
| 4 | Parameter Parsing | Identify 20+ blood parameters |
| 5 | Validation | Compare against reference ranges |
| 6 | Interpretation | Generate summary & basic recommendations |
| 7 | Multi-Model Analysis | Run 4 analytical models |
| 8 | LLM Analysis | Get AI-powered insights via Mistral |
| 9 | Risk Calculation | Compute Framingham CVD & metabolic risks |
| 10 | AI Chat | Enable interactive Q&A |
| 11 | Display Results | Show comprehensive dashboard |

Each step is designed with **fallbacks** and **error handling** to ensure reliable analysis even with poor quality inputs or unavailable services.

---

*Generated: January 18, 2026*  
*Project: Multi-Model AI Agent - Health Diagnostics*  
*Version: 2.0*
