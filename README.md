# Blood Report Analysis System

An AI-powered medical report analysis system that provides comprehensive blood work interpretation with intelligent insights and multi-report comparison capabilities.

## Features

- **Advanced OCR Processing** - Extract text from PDF and image files with multiple preprocessing strategies
- **Comprehensive Blood Analysis** - Parse 20+ blood parameters including CBC, differential counts, and chemistry panels
- **Intelligent AI Assistant** - Goal-oriented AI that provides personalized health recommendations
- **Multi-Report Comparison** - Track health trends across multiple reports over time
- **Real-time Chat Interface** - Interactive Q&A about your blood work results

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd blood-report-analysis
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
   - **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

5. Install Ollama (for AI features):
   - Download from [ollama.ai](https://ollama.ai)
   - Install Mistral model: `ollama pull mistral:instruct`

## Usage

1. Start the application:
```bash
python start_project.py
```
Or run directly:
```bash
streamlit run src/ui/UI.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Upload your blood report (PDF, PNG, JPG, or JSON format)

4. View comprehensive analysis and chat with the AI assistant

## Supported File Formats

- **PDF files** - Scanned or digital blood reports
- **Image files** - PNG, JPG, JPEG format medical reports  
- **JSON files** - Structured medical data
- **CSV files** - Tabular blood work data

## Project Structure

```
├── src/
│   ├── core/           # Core analysis modules
│   ├── ui/             # User interface components
│   ├── utils/          # Utility functions
│   ├── phase1/         # Basic extraction modules
│   └── phase2/         # Advanced AI analysis
├── config/             # Configuration files
├── data/               # Sample data and test files
├── docs/               # Documentation
├── scripts/            # Setup and utility scripts
└── tests/              # Test files
```

## Key Components

### Core Modules
- **OCR Engine** - Multi-strategy text extraction from medical documents
- **Blood Parser** - Comprehensive parameter extraction (20+ parameters)
- **AI Agent** - Enhanced intelligence with goal-oriented workflows
- **Multi-Report Manager** - Handle multiple reports with comparison analysis

### Analysis Pipeline
1. **Document Ingestion** - OCR processing with validation
2. **Parameter Extraction** - Parse medical values, units, and reference ranges
3. **Data Validation** - Ensure accuracy and completeness
4. **Medical Interpretation** - Determine normal/abnormal status
5. **AI Analysis** - Personalized insights and recommendations

## Blood Parameters Supported

### Complete Blood Count (CBC)
- White Blood Cell (WBC), Red Blood Cell (RBC), Hemoglobin, Hematocrit
- Mean Cell Volume (MCV), Mean Cell Hemoglobin (MCH), MCHC, RDW
- Platelet Count, Mean Platelet Volume

### Differential Count
- Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils
- Both percentage and absolute counts

### Chemistry Panel
- Glucose, Cholesterol, Creatinine, BUN, Liver enzymes

## AI Features

- **Intent Recognition** - Understands user goals beyond literal questions
- **Clarifying Questions** - Asks intelligent follow-ups for better assistance
- **Context Memory** - Remembers conversation history and preferences
- **Trend Analysis** - Identifies patterns across multiple reports
- **Personalized Recommendations** - Tailored health advice based on results

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical decisions and interpretations.

## Technical Requirements

- Python 3.8+
- Tesseract OCR
- Ollama (optional, for AI features)
- 4GB+ RAM recommended
- Windows/macOS/Linux support