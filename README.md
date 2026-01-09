# Blood Report Analysis System

An AI-powered medical report analysis application that extracts, analyzes, and interprets blood test results.

## Features

- **PDF/Image Processing**: Upload blood reports in PDF, PNG, JPG, or JSON format
- **OCR Extraction**: Automatic text extraction from scanned documents
- **Parameter Detection**: Extracts 40+ blood parameters including CBC, chemistry, liver function, thyroid
- **AI Analysis**: Powered by Mistral AI for intelligent health insights
- **Interactive Chat**: Ask questions about your blood report results
- **Status Indicators**: Visual indicators for normal, high, and low values

## Project Structure

```
├── src/
│   ├── core/                    # Core processing modules
│   │   ├── ocr_engine.py        # OCR and document processing
│   │   ├── parser.py            # Blood report parsing
│   │   ├── enhanced_blood_parser.py  # Comprehensive parameter extraction
│   │   ├── validator.py         # Parameter validation
│   │   ├── interpreter.py       # Results interpretation
│   │   ├── enhanced_ai_agent.py # AI agent for chat
│   │   └── multi_report_*.py    # Multi-report handling
│   ├── phase1/                  # Phase 1 extraction modules
│   ├── phase2/                  # Phase 2 AI analysis modules
│   ├── ui/                      # Streamlit UI
│   │   └── UI.py                # Main application interface
│   └── utils/                   # Utility functions
├── config/                      # Configuration files
├── data/                        # Sample data
├── scripts/                     # Setup scripts
├── start_project.py             # Application entry point
└── requirements.txt             # Python dependencies
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Tesseract OCR (for image processing)
5. Install Ollama and pull Mistral model (for AI features):
   ```bash
   ollama pull mistral:instruct
   ```

## Usage

Run the application:
```bash
python start_project.py
```

Or directly with Streamlit:
```bash
streamlit run src/ui/UI.py
```

The application will open at http://localhost:8501

## Supported Parameters

- **CBC**: Hemoglobin, RBC, WBC, Platelets, Hematocrit, MCV, MCH, MCHC, RDW
- **Differential**: Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils
- **Chemistry**: Glucose, Cholesterol, Creatinine, BUN, Uric Acid
- **Liver Function**: SGPT/ALT, SGOT/AST, Bilirubin, Alkaline Phosphatase
- **Thyroid**: TSH, T3, T4
- **Others**: ESR, HbA1c, Vitamins, Electrolytes

## Requirements

- Python 3.10+
- Tesseract OCR
- Ollama (for AI features)
- Poppler (for PDF processing)

## License

MIT License
