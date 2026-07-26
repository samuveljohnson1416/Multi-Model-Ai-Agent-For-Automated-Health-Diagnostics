# Health Diagnostics AI Agent

An AI-powered medical report analysis system that provides comprehensive blood work interpretation with intelligent insights and multi-report comparison capabilities.

## Features

- **Advanced OCR Processing** - Extract text from PDF and image files with multiple preprocessing strategies.
- **Comprehensive Blood Analysis** - Parse 20+ blood parameters including CBC, differential counts, and chemistry panels.
- **Intelligent AI Assistant** - Goal-oriented AI that provides personalized health recommendations.
- **Multi-Report Comparison** - Track health trends across multiple reports over time.
- **Real-time Chat Interface** - Interactive Q&A about your blood work results.

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Validation**: Pydantic
- **Database**: Supabase
- **Architecture**: Service Layer with Repository Pattern

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Multi-Model-Ai-Agent-For-Automated-Health-Diagnostics
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

4. Environment Variables:
Copy `.env.example` to `.env` and fill in your Supabase and API credentials.

5. Install Tesseract OCR:
   - **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

## Usage

### Development

You can run the backend and frontend separately:

**Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
```

### Production / Hugging Face Spaces Deployment

You can use the `start.sh` script to run both services simultaneously. This is particularly useful for deployments in single-container environments like Hugging Face Spaces.

```bash
chmod +x start.sh
./start.sh
```

**What `start.sh` does:**
1. Starts the FastAPI backend in the background on port `8000`.
2. Waits a few seconds for the backend to initialize.
3. Starts the Streamlit frontend on port `7860` (the default for HF Spaces) in headless mode.

## Supported File Formats

- **PDF files** - Scanned or digital blood reports
- **Image files** - PNG, JPG, JPEG format medical reports  
- **JSON files** - Structured medical data
- **CSV files** - Tabular blood work data

## Project Structure

```
├── backend/            # FastAPI backend (Routes, Services, Domain, Repository)
├── frontend/           # Streamlit user interface components
├── docs/               # Project Documentation
├── tests/              # Test files
├── start.sh            # Combined startup script for deployment
└── requirements.txt    # Project dependencies
```

## Disclaimer

This tool is for informational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical decisions and interpretations.