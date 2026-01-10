#!/usr/bin/env python3
"""
Phase-2 Setup Script for Blood Report Analysis System
Installs and configures Ollama with Mistral 7B Instruct model
"""

import subprocess
import sys
import platform
import requests
import time
import json


def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_ollama():
    """Install Ollama based on operating system"""
    system = platform.system().lower()
    
    print("Installing Ollama...")
    
    if system == "windows":
        print("Please install Ollama manually on Windows:")
        print("1. Download from: https://ollama.ai/download/windows")
        print("2. Run the installer")
        print("3. Restart your terminal")
        return False
    
    elif system == "darwin":  # macOS
        try:
            subprocess.run(['brew', 'install', 'ollama'], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Please install Ollama manually on macOS:")
            print("1. Download from: https://ollama.ai/download/mac")
            print("2. Or use Homebrew: brew install ollama")
            return False
    
    elif system == "linux":
        try:
            # Install using the official script
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                         stdout=subprocess.PIPE, check=True)
            return True
        except subprocess.CalledProcessError:
            print("Please install Ollama manually on Linux:")
            print("curl -fsSL https://ollama.ai/install.sh | sh")
            return False
    
    return False


def start_ollama_service():
    """Start Ollama service"""
    try:
        print("Starting Ollama service...")
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)  # Wait for service to start
        return True
    except Exception as e:
        print(f"Failed to start Ollama service: {e}")
        return False


def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def pull_mistral_model():
    """Pull Mistral 7B Instruct model"""
    try:
        print("Pulling Mistral 7B Instruct model (this may take several minutes)...")
        result = subprocess.run(['ollama', 'pull', 'mistral:7b-instruct'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Mistral 7B Instruct model installed successfully!")
            return True
        else:
            print(f"❌ Failed to pull model: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error pulling model: {e}")
        return False


def verify_model_available():
    """Verify Mistral model is available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if "mistral" in model.get("name", "").lower():
                    print(f"✅ Found model: {model['name']}")
                    return True
        
        print("❌ Mistral model not found in available models")
        return False
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False


def test_phase2_integration():
    """Test Phase-2 integration with sample data"""
    try:
        # Add src to path for imports
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from phase2.phase2_integration_safe import check_phase2_requirements
        
        print("Testing Phase-2 integration...")
        requirements = check_phase2_requirements()
        
        if requirements["status"] == "ready":
            print("✅ Phase-2 integration test passed!")
            return True
        else:
            print(f"❌ Phase-2 integration test failed: {requirements}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False


def install_python_dependencies():
    """Install required Python packages"""
    try:
        print("Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False


def main():
    """Main setup function"""
    print("🩺 Blood Report Analysis System - Phase-2 Setup")
    print("=" * 50)
    
    # Step 1: Install Python dependencies
    if not install_python_dependencies():
        print("❌ Setup failed at Python dependencies")
        return False
    
    # Step 2: Check if Ollama is installed
    if not check_ollama_installed():
        print("Ollama not found. Installing...")
        if not install_ollama():
            print("❌ Please install Ollama manually and run this script again")
            return False
    else:
        print("✅ Ollama is installed")
    
    # Step 3: Start Ollama service
    if not check_ollama_running():
        if not start_ollama_service():
            print("❌ Failed to start Ollama service")
            print("Please run 'ollama serve' manually in another terminal")
            return False
    else:
        print("✅ Ollama service is running")
    
    # Step 4: Pull Mistral model
    if not pull_mistral_model():
        print("❌ Failed to install Mistral model")
        return False
    
    # Step 5: Verify model availability
    if not verify_model_available():
        print("❌ Model verification failed")
        return False
    
    # Step 6: Test integration
    if not test_phase2_integration():
        print("❌ Integration test failed")
        return False
    
    print("\n🎉 Phase-2 setup completed successfully!")
    print("\nNext steps:")
    print("1. Run your Streamlit app: streamlit run UI.py")
    print("2. Upload a blood report")
    print("3. See Phase-2 AI analysis in action")
    print("\nNote: Keep 'ollama serve' running in the background for Phase-2 to work")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)