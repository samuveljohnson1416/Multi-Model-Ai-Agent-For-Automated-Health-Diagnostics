"""
Ollama Manager - Automatic startup and management for Ollama service
"""

import subprocess
import time
import requests
import threading
import os
import sys
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaManager:
    """Manages Ollama service startup and health checking"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.startup_timeout = 30  # seconds
        
    def is_ollama_running(self) -> bool:
        """Check if Ollama is already running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_ollama_service(self) -> bool:
        """Start Ollama service if not already running"""
        if self.is_ollama_running():
            logger.info("Ollama is already running")
            self.is_running = True
            return True
        
        logger.info("Starting Ollama service...")
        
        try:
            # Start Ollama serve in background
            if sys.platform.startswith('win'):
                # Windows
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
                )
            else:
                # Linux/Mac
                self.ollama_process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for Ollama to start
            start_time = time.time()
            while time.time() - start_time < self.startup_timeout:
                if self.is_ollama_running():
                    logger.info("Ollama service started successfully")
                    self.is_running = True
                    return True
                time.sleep(1)
            
            logger.error("Ollama failed to start within timeout")
            return False
            
        except FileNotFoundError:
            logger.error("Ollama not found. Please install Ollama first: https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"Failed to start Ollama: {str(e)}")
            return False
    
    def check_mistral_model(self) -> bool:
        """Check if Mistral model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=15)
            if response.status_code == 200:
                models = response.json().get("models", [])
                # Check for any mistral variant
                mistral_models = [model.get("name", "") for model in models if "mistral" in model.get("name", "").lower()]
                if mistral_models:
                    logger.info(f"Found Mistral models: {mistral_models}")
                    return True
                else:
                    logger.warning("No Mistral models found")
                    return False
            else:
                logger.error(f"Failed to get models list: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error checking Mistral model: {e}")
            return False
    
    def pull_mistral_model(self) -> bool:
        """Pull Mistral model if not available"""
        if self.check_mistral_model():
            logger.info("Mistral model already available")
            return True
        
        logger.info("Pulling Mistral model... This may take a few minutes.")
        
        try:
            # Try to pull mistral:instruct model
            if sys.platform.startswith('win'):
                process = subprocess.Popen(
                    ["ollama", "pull", "mistral:instruct"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = subprocess.Popen(
                    ["ollama", "pull", "mistral:instruct"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
                if process.returncode == 0:
                    logger.info("Mistral model pulled successfully")
                    return self.check_mistral_model()
                else:
                    logger.error(f"Failed to pull Mistral model: {stderr.decode()}")
                    return False
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error("Mistral model pull timed out")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling Mistral model: {str(e)}")
            return False
    
    def setup_ollama_complete(self) -> Dict[str, Any]:
        """Complete Ollama setup - start service and ensure model is available"""
        setup_status = {
            "ollama_started": False,
            "mistral_available": False,
            "ready": False,
            "messages": []
        }
        
        # Step 1: Start Ollama service
        if self.start_ollama_service():
            setup_status["ollama_started"] = True
            setup_status["messages"].append("✅ Ollama service started")
        else:
            setup_status["messages"].append("❌ Failed to start Ollama service")
            return setup_status
        
        # Step 2: Check/pull Mistral model
        if self.pull_mistral_model():
            setup_status["mistral_available"] = True
            setup_status["messages"].append("✅ Mistral model ready")
        else:
            setup_status["messages"].append("❌ Mistral model not available")
            return setup_status
        
        # Step 3: Final verification
        if self.is_ollama_running() and self.check_mistral_model():
            setup_status["ready"] = True
            setup_status["messages"].append("🚀 Ollama fully ready for AI analysis")
        
        return setup_status
    
    def stop_ollama_service(self) -> None:
        """Stop Ollama service if we started it"""
        if self.ollama_process:
            try:
                self.ollama_process.terminate()
                self.ollama_process.wait(timeout=10)
                logger.info("Ollama service stopped")
            except Exception as e:
                logger.error(f"Error stopping Ollama: {str(e)}")
            finally:
                self.ollama_process = None
                self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current Ollama status"""
        return {
            "service_running": self.is_ollama_running(),
            "mistral_available": self.check_mistral_model(),
            "process_managed": self.ollama_process is not None,
            "ready_for_ai": self.is_ollama_running() and self.check_mistral_model()
        }


# Global instance for the application
_ollama_manager: Optional[OllamaManager] = None


def get_ollama_manager() -> OllamaManager:
    """Get or create global Ollama manager instance"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager()
    return _ollama_manager


def auto_start_ollama() -> Dict[str, Any]:
    """Auto-start Ollama for the application"""
    manager = get_ollama_manager()
    return manager.setup_ollama_complete()


def cleanup_ollama():
    """Cleanup function to stop Ollama if we started it"""
    global _ollama_manager
    if _ollama_manager:
        _ollama_manager.stop_ollama_service()


# Register cleanup function
import atexit
atexit.register(cleanup_ollama)