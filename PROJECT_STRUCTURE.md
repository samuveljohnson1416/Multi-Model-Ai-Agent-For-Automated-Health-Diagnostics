# Blood Report Analysis System - Project Structure

## 📁 Directory Organization

```
Blood-Report-Analysis-System/
├── 📄 main.py                    # Main entry point
├── 📄 setup_phase2.py           # Phase-2 setup script
├── 📄 PROJECT_STRUCTURE.md      # This file
├── 📄 requirements.txt          # Python dependencies
│
├── 📁 src/                      # Source code
│   ├── 📁 core/                 # Core processing modules
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ocr_engine.py     # Multi-agent OCR processing
│   │   ├── 📄 parser.py         # Parameter extraction
│   │   ├── 📄 validator.py      # Data validation
│   │   └── 📄 interpreter.py    # Result interpretation
│   │
│   ├── 📁 phase1/               # Phase-1 extraction modules
│   │   ├── 📄 __init__.py
│   │   ├── 📄 phase1_extractor.py    # Image-aware extraction
│   │   ├── 📄 medical_validator.py   # Medical validation
│   │   └── 📄 table_extractor.py     # Table extraction
│   │
│   ├── 📁 phase2/               # Phase-2 AI analysis modules
│   │   ├── 📄 __init__.py
│   │   ├── 📄 phase2_orchestrator.py      # LLM orchestration
│   │   ├── 📄 phase2_integration_safe.py  # Safe integration
│   │   └── 📄 csv_schema_adapter.py       # Schema validation
│   │
│   ├── 📁 utils/                # Utility modules
│   │   ├── 📄 __init__.py
│   │   └── 📄 csv_converter.py  # ML-ready CSV conversion
│   │
│   └── 📁 ui/                   # User interface
│       ├── 📄 __init__.py
│       └── 📄 UI.py             # Streamlit web application
│
├── 📁 config/                   # Configuration files
│   └── 📄 reference_ranges.json # Medical reference ranges
│
├── 📁 data/                     # Data files
│   └── 📁 pdf_datas/           # Sample medical reports
│
├── 📁 docs/                     # Documentation
│   ├── 📄 README.md            # Main documentation
│   └── 📄 PHASE2_README.md     # Phase-2 specific docs
│
├── 📁 tests/                    # Test files
│   └── 📄 test_phase2.py       # Phase-2 test suite
│
└── 📁 .venv/                   # Virtual environment (local)
```

## 🏗️ Architecture Overview

### **Core Modules** (`src/core/`)
- **`ocr_engine.py`**: Multi-agent OCR processing with format detection
- **`parser.py`**: Medical parameter extraction and parsing
- **`validator.py`**: Data validation against reference ranges
- **`interpreter.py`**: Result interpretation and classification

### **Phase-1 Extraction** (`src/phase1/`)
- **`phase1_extractor.py`**: Image-aware OCR reconstruction with completeness guarantee
- **`medical_validator.py`**: Medical document validation with clinical safety
- **`table_extractor.py`**: Pure table extraction without interpretation

### **Phase-2 AI Analysis** (`src/phase2/`)
- **`phase2_orchestrator.py`**: Mistral 7B LLM orchestration engine
- **`phase2_integration_safe.py`**: Safety-enhanced integration layer
- **`csv_schema_adapter.py`**: Robust CSV schema validation and adaptation

### **Utilities** (`src/utils/`)
- **`csv_converter.py`**: ML-ready CSV format conversion

### **User Interface** (`src/ui/`)
- **`UI.py`**: Streamlit web application with comprehensive reporting

## 🚀 Usage

### **Start Web Application**
```bash
streamlit run src/ui/UI.py
```

### **Setup Phase-2 AI**
```bash
python setup_phase2.py
```

### **Run Tests**
```bash
python tests/test_phase2.py
```

### **Main Entry Point**
```bash
python main.py
```

## 📦 Module Dependencies

```
UI.py
├── core.ocr_engine
├── core.parser
├── core.validator
├── core.interpreter
├── utils.csv_converter
└── phase2.phase2_integration_safe

ocr_engine.py
├── phase1.medical_validator
├── phase1.table_extractor
└── phase1.phase1_extractor

phase2_integration_safe.py
├── phase2_orchestrator
└── csv_schema_adapter
```

## 🛡️ Safety Features

### **Schema Validation**
- Never assumes CSV column names
- Robust adapter layer for schema differences
- Graceful failure with clear error messages

### **LLM Safety**
- LLM invocation only after successful validation
- No hallucination - CSV is single source of truth
- Local processing with Ollama (no data upload)

### **Medical Safety**
- No diagnosis or medication recommendations
- Mandatory healthcare consultation disclaimers
- Conservative risk assessment approach

## 🔧 Configuration

### **Reference Ranges** (`config/reference_ranges.json`)
Medical parameter reference ranges for validation

### **Environment Variables**
- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)
- `TESSERACT_PATH`: Tesseract OCR executable path

## 📊 Data Flow

```
Input (PDF/Image) 
    ↓
OCR Engine (Multi-Agent)
    ↓
Phase-1 Extraction (Completeness Guarantee)
    ↓
CSV Schema Adapter (Safety Validation)
    ↓
Phase-2 AI Analysis (Mistral 7B)
    ↓
Final Report Generation
    ↓
Output (Web UI + Downloads)
```

## 🧪 Testing

### **Test Coverage**
- Phase-2 requirements validation
- CSV schema adaptation
- LLM integration
- Error handling scenarios

### **Safety Tests**
- Schema validation edge cases
- Numeric formatting safety
- Graceful failure scenarios

## 📝 Development Guidelines

### **Adding New Modules**
1. Place in appropriate `src/` subdirectory
2. Add `__init__.py` imports if needed
3. Update `PROJECT_STRUCTURE.md`
4. Add corresponding tests

### **Import Conventions**
- Use relative imports within packages
- Absolute imports from `src/` root
- Add path modifications for UI modules

### **Safety Requirements**
- Never assume data formats
- Always validate before processing
- Provide clear error messages
- Fail gracefully with fallbacks