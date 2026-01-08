# Ollama Auto-Start Setup

## Overview

Your Blood Report Analysis System now automatically starts Ollama when you launch the project. No more manual `ollama serve` commands!

## Quick Start Options

### Option 1: Windows Batch File (Easiest)
```cmd
start_project.bat
```
Double-click the batch file or run it from command prompt.

### Option 2: Python Launcher
```cmd
python start_project.py
```

### Option 3: Direct Streamlit (with auto-start)
```cmd
streamlit run src/ui/UI.py
```

### Option 4: Main Entry Point
```cmd
python main.py
```

## What Happens Automatically

1. **Ollama Service Start**: Automatically starts `ollama serve` in the background
2. **Model Check**: Verifies Mistral 7B Instruct model is available
3. **Model Download**: Downloads Mistral model if missing (first time only)
4. **Health Check**: Ensures everything is ready for AI analysis
5. **Streamlit Launch**: Opens your web application

## Status Indicators

When you open the Streamlit app, you'll see:

- ✅ **"AI Analysis Ready"** - Ollama & Mistral fully loaded
- ⚠️ **"AI Analysis Limited"** - Ollama setup incomplete (Phase-1 still works)

## Troubleshooting

### If Ollama Fails to Start
1. **Install Ollama**: Download from https://ollama.ai
2. **Check PATH**: Ensure `ollama` command is available
3. **Manual Start**: Run `ollama serve` manually first

### If Model Download Fails
1. **Internet Connection**: Ensure stable internet for model download
2. **Disk Space**: Mistral 7B requires ~4GB free space
3. **Manual Pull**: Run `ollama pull mistral:instruct` manually

### If Port is Busy
The system uses port 11434 for Ollama. If busy:
1. **Check Running Ollama**: `ollama ps`
2. **Kill Process**: Stop other Ollama instances
3. **Change Port**: Modify `ollama_url` in the code if needed

## Technical Details

### Files Added
- `src/utils/ollama_manager.py` - Ollama management utility
- `start_project.py` - Python launcher script
- `start_project.bat` - Windows batch launcher

### Integration Points
- **UI.py**: Auto-starts Ollama on Streamlit launch
- **main.py**: Shows Ollama status on main entry
- **Cleanup**: Automatically stops Ollama on app exit

### Background Process
- Ollama runs as a background process
- Hidden console window on Windows
- Automatic cleanup on application exit
- Graceful handling of existing Ollama instances

## Benefits

1. **Zero Manual Setup**: No more `ollama serve` commands
2. **Seamless Experience**: AI analysis works immediately
3. **Error Handling**: Clear messages if setup fails
4. **Fallback Support**: Phase-1 analysis always available
5. **Resource Management**: Proper cleanup on exit

## Next Steps

Your system is now ready! The Data-Grounded Q&A Gateway we specified will work seamlessly with this auto-start setup.

Simply run `start_project.bat` and your entire medical analysis system will be ready with AI capabilities!