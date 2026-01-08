# Multi-Model AI Agent for Automated Health Diagnostics

A comprehensive AI-powered system for analyzing blood reports with advanced OCR capabilities, multi-report processing, and intelligent Q&A assistance.

## 🚀 Features

- **🔍 Advanced OCR**: Extract text from PDFs, images, and scanned documents with 85-90% success rate
- **📊 Multi-Report Processing**: Automatic detection and analysis of multiple reports in single documents
- **🤖 AI Analysis**: Mistral LLM integration with medical safety compliance
- **💬 Intelligent Q&A**: GPT-like chat interface for medical report questions
- **👤 Auto-Demographics**: Automatic age/gender extraction from reports
- **📈 Comparative Analysis**: Trend detection and parameter comparison across reports
- **⚡ Performance Optimized**: Sub-10-second AI responses with caching

## 🎯 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Application**:
   ```bash
   python start_project.py
   ```
   Or use the Windows batch file:
   ```bash
   scripts/start_project.bat
   ```

3. **Access the Interface**:
   - Open your browser to `http://localhost:8501`
   - Upload blood reports (PDF, image, JSON, or CSV)
   - Get AI-powered analysis and interactive chat

## 📁 Project Structure

```
├── src/
│   ├── core/           # Core processing modules (OCR, parsing, validation)
│   │   ├── multi_report_detector.py    # Multi-report boundary detection
│   │   ├── multi_report_manager.py     # Multi-report processing pipeline
│   │   ├── multi_report_qa_assistant.py # Enhanced Q&A for multiple reports
│   │   ├── ocr_engine.py              # Robust OCR with 36 processing combinations
│   │   ├── parser.py                  # Medical parameter extraction
│   │   ├── validator.py               # Data validation and confidence scoring
│   │   ├── interpreter.py             # Results interpretation
│   │   └── qa_assistant.py            # LLM-based Q&A system
│   ├── phase1/         # Basic parameter extraction and demographics
│   ├── phase2/         # Advanced AI analysis with pattern recognition
│   ├── ui/             # Modern Streamlit interface with chat
│   └── utils/          # Utility functions and Ollama management
├── config/             # Reference ranges and configuration
├── data/               # Sample data and file storage
├── docs/               # Comprehensive documentation
├── scripts/            # Utility and startup scripts
└── tests/              # Comprehensive test suite
```

## 🔧 System Requirements

- **Python**: 3.8+
- **Ollama**: For AI analysis (auto-installed)
- **Tesseract OCR**: For image processing
- **Dependencies**: See requirements.txt

## 📚 Documentation

Comprehensive documentation available in `docs/`:

### Core Documentation
- **`PROJECT_DEVELOPMENT_SUMMARY.md`** - Complete development history and problem solutions
- **`PROJECT_STRUCTURE.md`** - Detailed system architecture
- **`OLLAMA_AUTOSTART_README.md`** - AI service setup and management

### Technical Documentation
- **`ROBUST_OCR_ENHANCEMENTS.md`** - OCR capabilities and improvements
- **`SPEED_OPTIMIZATION_SUMMARY.md`** - Performance optimizations
- **`JSON_PROCESSING_FIX.md`** - JSON file processing capabilities
- **`MULTI_REPORT_IMPLEMENTATION_SUMMARY.md`** - Multi-report system details

## 🎯 Key Capabilities

### Multi-Report Processing
- **Automatic Detection**: Identifies multiple reports in single PDFs
- **Data Isolation**: Complete separation between reports to prevent contamination
- **Comparative Analysis**: Trend detection and parameter comparison
- **Session Memory**: Context-aware conversations across multiple reports

### Advanced OCR
- **36 Processing Combinations**: 6 preprocessing × 6 OCR configurations
- **Real-World Image Support**: Handles low-quality scanned documents
- **Medical Content Detection**: Specialized for blood report formats
- **Fallback Mechanisms**: Emergency processing for difficult images

### AI-Powered Analysis
- **Mistral LLM Integration**: Fast, accurate medical reasoning
- **Medical Safety**: Strict compliance with healthcare guidelines
- **Performance Optimized**: 3-8 second response times
- **Contextual Understanding**: Age/gender demographic integration

## 🚀 Getting Started

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd Multi-Model-Ai-Agent-For-Automated-Health-Diagnostics
   pip install -r requirements.txt
   ```

2. **Run Application**:
   ```bash
   python start_project.py
   ```

3. **Upload Reports**: Support for PDF, images, JSON, and CSV files

4. **Interactive Analysis**: Chat with AI about your blood reports

## 📈 Performance Metrics

- **OCR Success Rate**: 85-90% (improved from 60%)
- **AI Response Time**: 3-8 seconds (24% improvement)
- **Multi-Report Support**: Unlimited reports per document
- **System Reliability**: Production-ready with comprehensive error handling

## 🔒 Medical Compliance

- Strict medical disclaimers and safety rules
- No diagnosis or medication recommendations
- Data accuracy with confidence scoring
- HIPAA-conscious design principles

## 📄 License

This project is for educational and research purposes. Please ensure compliance with medical data regulations in your jurisdiction.