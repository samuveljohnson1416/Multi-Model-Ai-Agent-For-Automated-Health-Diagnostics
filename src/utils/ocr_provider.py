"""
Unified OCR Provider - Supports local Tesseract and multiple cloud OCR APIs
Automatically falls back between providers based on availability and configuration.

Supported Providers:
1. Local Tesseract (default, no API key needed)
2. OCR.space API (500 free requests/day)
3. Google Cloud Vision (1000 free/month)
4. Hugging Face Vision Models (free with token)
"""

import os
import base64
import requests
import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from io import BytesIO
from PIL import Image
import tempfile

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRProviderType(Enum):
    TESSERACT = "tesseract"
    OCR_SPACE = "ocr_space"
    GOOGLE_VISION = "google_vision"
    HUGGINGFACE = "huggingface"
    NONE = "none"


class OCRProvider:
    """
    Unified OCR Provider that supports:
    - Local Tesseract OCR
    - OCR.space API (free tier: 500 requests/day)
    - Google Cloud Vision API (free tier: 1000/month)
    - Hugging Face Vision Models
    """
    
    def __init__(self):
        # Load configuration from environment
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY", "")
        self.google_vision_api_key = os.getenv("GOOGLE_VISION_API_KEY", "")
        self.hf_token = os.getenv("HF_API_TOKEN", "")
        
        # Provider priority (comma-separated list)
        # Default: try tesseract first, then APIs
        self.priority = os.getenv("OCR_PROVIDER_PRIORITY", "tesseract_first")
        self.timeout = int(os.getenv("OCR_TIMEOUT", "30"))
        self.debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # Track availability
        self._tesseract_available: Optional[bool] = None
        self._active_provider: OCRProviderType = OCRProviderType.NONE
    
    def _check_tesseract_available(self) -> bool:
        """Check if Tesseract is installed and accessible"""
        if self._tesseract_available is not None:
            return self._tesseract_available
        
        try:
            import pytesseract
            # Try to get tesseract version
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("✅ Tesseract OCR is available")
            return True
        except Exception as e:
            if self.debug:
                logger.debug(f"Tesseract check failed: {e}")
            self._tesseract_available = False
            return False
    
    def _check_ocr_space_available(self) -> bool:
        """Check if OCR.space API key is configured"""
        return bool(self.ocr_space_api_key)
    
    def _check_google_vision_available(self) -> bool:
        """Check if Google Vision API key is configured"""
        return bool(self.google_vision_api_key)
    
    def _check_hf_available(self) -> bool:
        """Check if Hugging Face token is configured"""
        return bool(self.hf_token)
    
    def get_active_provider(self) -> OCRProviderType:
        """Determine which provider to use based on priority and availability"""
        if self.priority == "tesseract_only":
            return OCRProviderType.TESSERACT if self._check_tesseract_available() else OCRProviderType.NONE
        
        elif self.priority == "api_only":
            # Try APIs in order
            if self._check_ocr_space_available():
                return OCRProviderType.OCR_SPACE
            elif self._check_google_vision_available():
                return OCRProviderType.GOOGLE_VISION
            elif self._check_hf_available():
                return OCRProviderType.HUGGINGFACE
            return OCRProviderType.NONE
        
        elif self.priority == "api_first":
            # Try APIs first, then Tesseract
            if self._check_ocr_space_available():
                return OCRProviderType.OCR_SPACE
            elif self._check_google_vision_available():
                return OCRProviderType.GOOGLE_VISION
            elif self._check_hf_available():
                return OCRProviderType.HUGGINGFACE
            elif self._check_tesseract_available():
                return OCRProviderType.TESSERACT
            return OCRProviderType.NONE
        
        else:  # tesseract_first (default)
            if self._check_tesseract_available():
                return OCRProviderType.TESSERACT
            elif self._check_ocr_space_available():
                return OCRProviderType.OCR_SPACE
            elif self._check_google_vision_available():
                return OCRProviderType.GOOGLE_VISION
            elif self._check_hf_available():
                return OCRProviderType.HUGGINGFACE
            return OCRProviderType.NONE
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def _call_tesseract(self, image: Image.Image, config: str = "") -> Tuple[str, float]:
        """Call local Tesseract OCR"""
        try:
            import pytesseract
            
            if not config:
                config = r'--oem 3 --psm 6 -l eng'
            
            # Get text
            text = pytesseract.image_to_string(image, config=config)
            
            # Get confidence
            data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.5
            
            return text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise
    
    def _call_ocr_space(self, image: Image.Image, language: str = "eng") -> Tuple[str, float]:
        """
        Call OCR.space API
        Free tier: 500 requests/day, max 1MB file size
        Docs: https://ocr.space/OCRAPI
        """
        try:
            # Convert image to base64
            img_base64 = self._image_to_base64(image)
            
            payload = {
                'apikey': self.ocr_space_api_key,
                'base64Image': f'data:image/png;base64,{img_base64}',
                'language': language,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2  # Engine 2 is better for most cases
            }
            
            response = requests.post(
                'https://api.ocr.space/parse/image',
                data=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing', False):
                    error_msg = result.get('ErrorMessage', ['Unknown error'])
                    raise Exception(f"OCR.space error: {error_msg}")
                
                parsed_results = result.get('ParsedResults', [])
                if parsed_results:
                    text = parsed_results[0].get('ParsedText', '')
                    # OCR.space doesn't return confidence, estimate based on exit code
                    exit_code = parsed_results[0].get('FileParseExitCode', 0)
                    confidence = 0.9 if exit_code == 1 else 0.7
                    return text.strip(), confidence
                
                return "", 0.0
            else:
                raise Exception(f"OCR.space API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"OCR.space API failed: {e}")
            raise
    
    def _call_google_vision(self, image: Image.Image) -> Tuple[str, float]:
        """
        Call Google Cloud Vision API
        Free tier: 1000 requests/month
        Docs: https://cloud.google.com/vision/docs/ocr
        """
        try:
            # Convert image to base64
            img_base64 = self._image_to_base64(image)
            
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_vision_api_key}"
            
            payload = {
                "requests": [{
                    "image": {"content": img_base64},
                    "features": [{"type": "TEXT_DETECTION"}]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                responses = result.get('responses', [])
                
                if responses and 'textAnnotations' in responses[0]:
                    # First annotation contains full text
                    text = responses[0]['textAnnotations'][0].get('description', '')
                    # Google Vision doesn't return confidence for text detection
                    confidence = 0.95  # Generally very accurate
                    return text.strip(), confidence
                
                return "", 0.0
            else:
                error = response.json().get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Google Vision API error: {error}")
                
        except Exception as e:
            logger.error(f"Google Vision API failed: {e}")
            raise
    
    def _call_huggingface_ocr(self, image: Image.Image) -> Tuple[str, float]:
        """
        Call Hugging Face OCR model
        Uses microsoft/trocr-base-printed or similar models
        Free with HF token (rate limited)
        """
        try:
            # Convert image to base64
            img_base64 = self._image_to_base64(image)
            
            # Use TrOCR model for printed text
            model_id = os.getenv("HF_OCR_MODEL", "microsoft/trocr-base-printed")
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            # Send image as base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            
            response = requests.post(
                url,
                headers=headers,
                data=img_bytes,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    confidence = 0.8  # Estimate
                    return text.strip(), confidence
                return "", 0.0
            elif response.status_code == 503:
                raise Exception("HF model is loading, please retry")
            else:
                raise Exception(f"HF API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Hugging Face OCR failed: {e}")
            raise
    
    def extract_text(self, image: Image.Image, language: str = "eng") -> Dict[str, Any]:
        """
        Extract text from image using the best available OCR provider.
        Automatically falls back to secondary providers if primary fails.
        
        Returns:
            Dict with keys: text, confidence, provider, success, error
        """
        provider = self.get_active_provider()
        
        if provider == OCRProviderType.NONE:
            return {
                "text": "",
                "confidence": 0.0,
                "provider": "none",
                "success": False,
                "error": "No OCR provider available. Install Tesseract or configure an API key."
            }
        
        # Define provider order for fallback
        providers_to_try = []
        
        if self.priority == "tesseract_first":
            providers_to_try = [
                (OCRProviderType.TESSERACT, self._check_tesseract_available),
                (OCRProviderType.OCR_SPACE, self._check_ocr_space_available),
                (OCRProviderType.GOOGLE_VISION, self._check_google_vision_available),
                (OCRProviderType.HUGGINGFACE, self._check_hf_available),
            ]
        elif self.priority == "api_first":
            providers_to_try = [
                (OCRProviderType.OCR_SPACE, self._check_ocr_space_available),
                (OCRProviderType.GOOGLE_VISION, self._check_google_vision_available),
                (OCRProviderType.HUGGINGFACE, self._check_hf_available),
                (OCRProviderType.TESSERACT, self._check_tesseract_available),
            ]
        else:
            providers_to_try = [(provider, lambda: True)]
        
        last_error = None
        
        for prov, check_func in providers_to_try:
            if not check_func():
                continue
            
            try:
                if prov == OCRProviderType.TESSERACT:
                    text, confidence = self._call_tesseract(image)
                elif prov == OCRProviderType.OCR_SPACE:
                    text, confidence = self._call_ocr_space(image, language)
                elif prov == OCRProviderType.GOOGLE_VISION:
                    text, confidence = self._call_google_vision(image)
                elif prov == OCRProviderType.HUGGINGFACE:
                    text, confidence = self._call_huggingface_ocr(image)
                else:
                    continue
                
                if text:
                    self._active_provider = prov
                    return {
                        "text": text,
                        "confidence": confidence,
                        "provider": prov.value,
                        "success": True,
                        "error": None
                    }
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {prov.value} failed: {e}")
                continue
        
        return {
            "text": "",
            "confidence": 0.0,
            "provider": "none",
            "success": False,
            "error": f"All OCR providers failed. Last error: {last_error}"
        }
    
    def extract_text_from_file(self, file_path: str, language: str = "eng") -> Dict[str, Any]:
        """Extract text from an image file"""
        try:
            image = Image.open(file_path)
            return self.extract_text(image, language)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "provider": "none",
                "success": False,
                "error": f"Failed to open image: {e}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current OCR provider status"""
        return {
            "tesseract_available": self._check_tesseract_available(),
            "ocr_space_available": self._check_ocr_space_available(),
            "ocr_space_key_set": bool(self.ocr_space_api_key),
            "google_vision_available": self._check_google_vision_available(),
            "google_vision_key_set": bool(self.google_vision_api_key),
            "huggingface_available": self._check_hf_available(),
            "hf_token_set": bool(self.hf_token),
            "priority": self.priority,
            "active_provider": self._active_provider.value if self._active_provider else "none",
            "recommended_provider": self.get_active_provider().value
        }
    
    def reset_cache(self):
        """Reset availability cache"""
        self._tesseract_available = None
        self._active_provider = OCRProviderType.NONE


# Global instance
_ocr_provider: Optional[OCRProvider] = None


def get_ocr_provider() -> OCRProvider:
    """Get or create global OCR provider instance"""
    global _ocr_provider
    if _ocr_provider is None:
        _ocr_provider = OCRProvider()
    return _ocr_provider


def extract_text_from_image(image: Image.Image, language: str = "eng") -> Dict[str, Any]:
    """Convenience function for OCR"""
    provider = get_ocr_provider()
    return provider.extract_text(image, language)


def get_ocr_status() -> Dict[str, Any]:
    """Get OCR provider status"""
    provider = get_ocr_provider()
    return provider.get_status()
