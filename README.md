# 🩺 Blood Report Analysis System

**Multi-Agent AI System for Automated Medical Report Processing with Phase-2 LLM Analysis**

## 🌟 Features

- **📄 Multi-Format Support**: PDF, PNG, JPG, JPEG, CSV, JSON
- **🤖 Multi-Agent Processing**: Specialized AI agents for different extraction scenarios
- **🔬 Phase-1 Extraction**: Image-aware OCR with completeness guarantee
- **🧠 Phase-2 AI Analysis**: Mistral 7B LLM for intelligent medical interpretation
- **🛡️ Safety Guarantees**: Zero hallucination, local processing, medical disclaimers
- **📊 ML-Ready Output**: Structured CSV for downstream AI models
- **📋 Professional Reports**: Comprehensive medical report generation

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone repository
git clone <repository-url>
cd Blood-Report-Analysis-System

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. **Setup Phase-2 AI (Optional)**
```bash
python setup_phase2.py
```

### 3. **Run Application**
```bash
# Option 1: Full AI experience (recommended)
python start_project.py

# Option 2: Quick UI launch (no AI setup)
python run_app.py

# Option 3: Direct Streamlit command
streamlit run src/ui/UI.py
```

### 4. **Access Web Interface**
Open your browser to: **http://localhost:8501**

## 📁 Project Structure

```
📦 Blood-Report-Analysis-System/
├── 🚀 main.py                    # Main entry point
├── 🚀 start_project.py           # Full launcher with AI setup (recommended)
├── 🚀 run_app.py                 # Quick UI launcher (no AI setup)
├── ⚙️ scripts/                   # Utility scripts
│   ├── setup_phase2.py          # Phase-2 AI setup
│   └── start_project.bat        # Windows launcher
├── 📋 requirements.txt          # Dependencies
├── 📖 README.md                 # This file
├── 📖 PROJECT_STRUCTURE.md      # Detailed structure docs
│
├── 📁 src/                      # Source code
│   ├── 📁 core/                 # Core processing modules
│   ├── 📁 phase1/               # Phase-1 extraction
│   ├── 📁 phase2/               # Phase-2 AI analysis
│   ├── 📁 utils/                # Utilities
│   └── 📁 ui/                   # Web interface
│
├── 📁 config/                   # Configuration files
├── 📁 data/                     # Sample data
├── 📁 docs/                     # Documentation
└── 📁 tests/                    # Test suite
```

## 🔧 System Architecture

### **Phase-1: Multi-Agent Extraction**
- **OCR Engine**: Multi-format document processing
- **Image Extractor**: Scanned image reconstruction
- **Table Extractor**: Pure table data extraction
- **Medical Validator**: Clinical parameter validation

### **Phase-2: AI Analysis (Optional)**
- **Model 1**: Parameter interpretation (Low/Normal/High)
- **Model 2**: Pattern recognition & risk assessment
- **Synthesis Engine**: Result aggregation
- **Recommendation Generator**: Lifestyle guidance

### **Safety Features**
- **Schema Validation**: Never assumes CSV formats
- **Zero Hallucination**: CSV is single source of truth
- **Local Processing**: No data upload (Ollama)
- **Medical Safety**: No diagnosis, mandatory disclaimers

## 📊 Usage Workflow

1. **Upload Report**: PDF, image, or structured data
2. **Phase-1 Processing**: Multi-agent extraction with completeness guarantee
3. **Phase-2 Analysis**: AI interpretation (if available)
4. **View Results**: Professional medical report
5. **Download**: Multiple formats (CSV, JSON, PDF)

## 🛠️ Configuration

### **Tesseract OCR Setup**
```bash
# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Default path: C:\Program Files\Tesseract-OCR\tesseract.exe

# Linux
sudo apt install tesseract-ocr

# macOS
brew install tesseract
```

### **Phase-2 AI Setup**
```bash
# Install Ollama
# Windows: Download from https://ollama.ai/download/windows
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# macOS: brew install ollama

# Pull Mistral model
ollama pull mistral:instruct

# Start Ollama service
ollama serve
```

## 🧪 Testing

### **Run Test Suite**
```bash
python tests/test_phase2.py
```

### **Test Components**
- ✅ Phase-2 requirements validation
- ✅ CSV schema adaptation
- ✅ LLM integration
- ✅ Error handling scenarios

## 📋 Sample Output

### **Phase-1 Extraction**
```csv
test_name,value,unit,reference_range,method,raw_text
Hemoglobin,12.5,g/dL,13.0-17.0,Calculated,Hemoglobin 12.5 g/dL
RBC Count,4.2,million/µL,4.5-5.5,Electrical Impedance,RBC Count 4.2
```

### **Phase-2 AI Analysis**
```
**Phase-2 AI Analysis (Mistral)**
Overall Status: Minor Concerns | Risk Level: Moderate
Tests Analyzed: 8 | Abnormal: 2 | Patterns: 1

Key Findings:
• Hemoglobin: 12.5 g/dL (Low)
• Total Cholesterol: 220 mg/dL (High)

AI Recommendations:
• Iron-rich diet with adequate nutrients
• Regular cardiovascular exercise
```

## 🔒 Privacy & Security

- **Local Processing**: All data stays on your machine
- **No Internet Required**: After setup, works offline
- **HIPAA Considerations**: Suitable for local medical data
- **No Data Logging**: System doesn't store medical information

## 🆘 Troubleshooting

### **Common Issues**

1. **"Tesseract not found"**
   ```bash
   # Check installation
   tesseract --version
   
   # Set path in environment or code
   export TESSERACT_PATH="/usr/bin/tesseract"
   ```

2. **"Phase-2 not available"**
   ```bash
   # Check Ollama status
   curl http://localhost:11434/api/tags
   
   # Start Ollama service
   ollama serve
   ```

3. **"Import errors"**
   ```bash
   # Full AI experience (recommended)
   python start_project.py
   
   # Quick UI launch
   python run_app.py
   
   # Or set PYTHONPATH
   export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
   ```

### **Performance Optimization**

1. **Speed up OCR**
   - Use higher resolution images
   - Ensure good lighting and contrast
   - Pre-process images (rotate, crop)

2. **Improve AI Analysis**
   - Ensure Ollama has sufficient RAM (8GB+)
   - Use SSD storage for better model loading
   - Close other applications during processing

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the project structure guidelines
4. Add tests for new functionality
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Medical Disclaimer

This system is for informational and research purposes only. It does not constitute medical advice, diagnosis, or treatment recommendations. Always consult qualified healthcare professionals for medical decisions.

## 🙏 Acknowledgments

- **Tesseract OCR**: Google's open-source OCR engine
- **Ollama**: Local LLM runtime
- **Mistral AI**: Open-source language model
- **Streamlit**: Web application framework
- **OpenCV**: Computer vision library

---

**Built with ❤️ for healthcare innovation**