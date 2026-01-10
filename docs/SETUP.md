# Setup Guide

## Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR**
3. **Ollama** (optional, for AI features)

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Windows:**
- Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
- Add to PATH or update path in `src/core/ocr_engine.py`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Install Ollama (Optional)

1. Download from [ollama.ai](https://ollama.ai)
2. Install Mistral model:
```bash
ollama pull mistral:instruct
```

## Running the Application

```bash
python start_project.py
```

Or directly:
```bash
streamlit run src/ui/UI.py
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in PATH
   - Update path in `src/core/ocr_engine.py` if needed

2. **Port already in use**
   - Change port in start_project.py or kill existing process

3. **Missing dependencies**
   - Run `pip install -r requirements.txt`
   - Ensure you're in the correct virtual environment

### Performance Tips

- Use high-quality scanned images for better OCR results
- Ensure good lighting and contrast in photos
- PDF files generally work better than images