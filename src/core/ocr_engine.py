import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import tempfile
import io
import os
import cv2
import numpy as np
import json
import re
from phase1.medical_validator import process_medical_document
from phase1.table_extractor import extract_medical_table
from phase1.phase1_extractor import extract_phase1_medical_image

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class MedicalOCROrchestrator:
    """
    Medical OCR Orchestration Agent - Enhanced for robust image processing
    Implements multiple OCR strategies and aggressive preprocessing for challenging images
    """
    
    def __init__(self):
        self.min_text_length = 10  # Further reduced for very short medical texts
        self.min_confidence_threshold = 0.4  # More lenient for real-world images
        self.medical_parameter_patterns = [
            r'(?i)hemoglobin|hb|hgb',
            r'(?i)rbc|red blood cell',
            r'(?i)wbc|white blood cell',
            r'(?i)platelet|plt',
            r'(?i)glucose|blood sugar',
            r'(?i)cholesterol|chol',
            r'(?i)creatinine|creat',
            r'(?i)neutrophil|lymphocyte|eosinophil|monocyte|basophil',
            r'(?i)mcv|mch|mchc|rdw',
            r'(?i)bun|urea',
            r'(?i)alt|ast|sgpt|sgot',
            r'(?i)\bglucose\b|\bchol\b',
            # Additional patterns for common variations
            r'(?i)total\s+count|count',
            r'(?i)level|levels',
            r'(?i)mg/dl|g/dl|/ul|/cumm',
            r'(?i)normal|high|low',
            r'(?i)test|result|value'
        ]
        
        # Enhanced preprocessing strategies
        self.preprocessing_strategies = [
            'standard',
            'high_contrast',
            'denoised',
            'sharpened',
            'morphological',
            'adaptive_bilateral'
        ]
    
    def determine_file_type(self, uploaded_file):
        """
        STEP 1: Determine file type and processing strategy
        """
        file_type = uploaded_file.type
        file_name = uploaded_file.name.lower()
        
        if file_type == "application/pdf":
            return "pdf"
        elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
            return "image"
        elif file_name.endswith('.pdf'):
            return "pdf"
        elif file_name.endswith(('.png', '.jpg', '.jpeg')):
            return "image"
        else:
            return "unsupported"
    
    def extract_text_from_pdf_direct(self, pdf_path):
        """
        Extract text directly from text-based PDF
        """
        try:
            digital_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        digital_text += page_text + "\n"
            
            return digital_text.strip()
        except Exception as e:
            return ""
    
    def is_text_sufficient(self, text):
        """
        Check if extracted text is sufficient (Rule 2)
        """
        if not text or len(text.strip()) < self.min_text_length:
            return False
        
        # Check for presence of medical parameters
        text_lower = text.lower()
        medical_param_found = any(
            re.search(pattern, text_lower) 
            for pattern in self.medical_parameter_patterns
        )
        
        return medical_param_found
    
    def preprocess_image_advanced(self, image, strategy='standard'):
        """
        ROBUST image preprocessing with multiple strategies for challenging images
        """
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply different preprocessing strategies
        if strategy == 'standard':
            return self._preprocess_standard(gray)
        elif strategy == 'high_contrast':
            return self._preprocess_high_contrast(gray)
        elif strategy == 'denoised':
            return self._preprocess_denoised(gray)
        elif strategy == 'sharpened':
            return self._preprocess_sharpened(gray)
        elif strategy == 'morphological':
            return self._preprocess_morphological(gray)
        elif strategy == 'adaptive_bilateral':
            return self._preprocess_adaptive_bilateral(gray)
        else:
            return self._preprocess_standard(gray)
    
    def _preprocess_standard(self, gray):
        """Standard preprocessing"""
        # Bilateral filter for noise reduction
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_high_contrast(self, gray):
        """High contrast preprocessing for faded images"""
        # Histogram equalization
        equalized = cv2.equalizeHist(gray)
        
        # CLAHE for local contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(equalized)
        
        # Aggressive thresholding
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return Image.fromarray(thresh)
    
    def _preprocess_denoised(self, gray):
        """Heavy denoising for noisy images"""
        # Multiple denoising passes
        denoised1 = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        denoised2 = cv2.bilateralFilter(denoised1, 15, 80, 80)
        
        # Gentle thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            denoised2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 15, 8
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_sharpened(self, gray):
        """Sharpening for blurry images"""
        # Unsharp masking
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        
        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_morphological(self, gray):
        """Morphological operations for text cleanup"""
        # Initial thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Remove noise
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Fill gaps
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return Image.fromarray(closing)
    
    def _preprocess_adaptive_bilateral(self, gray):
        """Adaptive bilateral filtering"""
        # Multiple bilateral filter passes with different parameters
        filtered1 = cv2.bilateralFilter(gray, 5, 50, 50)
        filtered2 = cv2.bilateralFilter(filtered1, 9, 75, 75)
        filtered3 = cv2.bilateralFilter(filtered2, 13, 100, 100)
        
        # Adaptive thresholding with larger neighborhood
        adaptive_thresh = cv2.adaptiveThreshold(
            filtered3, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 10
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def perform_ocr_with_validation(self, image):
        """
        ROBUST OCR execution with multiple strategies and preprocessing approaches
        """
        best_result = None
        best_confidence = 0
        all_results = []
        
        # OCR configurations optimized for different scenarios
        ocr_configs = [
            # Medical table configurations
            {
                'config': r'--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,-/():% ',
                'description': 'Medical table optimized'
            },
            # Single column configuration
            {
                'config': r'--oem 3 --psm 4 -l eng',
                'description': 'Single column'
            },
            # Sparse text configuration
            {
                'config': r'--oem 3 --psm 8 -l eng',
                'description': 'Sparse text'
            },
            # Automatic page segmentation
            {
                'config': r'--oem 3 --psm 3 -l eng',
                'description': 'Automatic segmentation'
            },
            # Single text line
            {
                'config': r'--oem 3 --psm 7 -l eng',
                'description': 'Single text line'
            },
            # Raw line without specific structure
            {
                'config': r'--oem 3 --psm 13 -l eng',
                'description': 'Raw line'
            }
        ]
        
        # Try each preprocessing strategy
        for strategy in self.preprocessing_strategies:
            try:
                # Preprocess image with current strategy
                processed_image = self.preprocess_image_advanced(image, strategy)
                
                # Try each OCR configuration
                for ocr_config in ocr_configs:
                    try:
                        # Get OCR data with confidence scores
                        ocr_data = pytesseract.image_to_data(
                            processed_image, 
                            config=ocr_config['config'],
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Extract text
                        text = pytesseract.image_to_string(
                            processed_image, 
                            config=ocr_config['config']
                        )
                        
                        # Calculate average confidence
                        confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        
                        # Store result
                        result = {
                            'text': text.strip(),
                            'confidence': avg_confidence / 100.0,  # Convert to 0-1 scale
                            'config_used': f"{strategy} + {ocr_config['description']}",
                            'strategy': strategy,
                            'ocr_config': ocr_config['description']
                        }
                        
                        all_results.append(result)
                        
                        # Check if this is the best result so far
                        if (len(text.strip()) > 10 and 
                            avg_confidence > best_confidence * 100):
                            best_confidence = avg_confidence
                            best_result = result
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # If no good result found, try to find the best available
        if not best_result and all_results:
            # Sort by text length and confidence
            all_results.sort(key=lambda x: (len(x['text']), x['confidence']), reverse=True)
            best_result = all_results[0]
        
        # Enhanced result with all attempts info
        if best_result:
            best_result['total_attempts'] = len(all_results)
            best_result['all_strategies_tried'] = self.preprocessing_strategies
        
        return best_result
    
    def validate_ocr_output(self, ocr_result):
        """
        ENHANCED validation for OCR output - more lenient for real-world images
        """
        if not ocr_result:
            return False, "OCR failed to produce any result"
        
        text = ocr_result.get('text', '')
        confidence = ocr_result.get('confidence', 0)
        
        # More lenient validation for challenging images
        
        # Check minimum text length (reduced threshold)
        if len(text.strip()) < self.min_text_length:
            return False, f"Text too short: {len(text.strip())} < {self.min_text_length} characters"
        
        # Check for ANY medical-related content (more flexible)
        text_lower = text.lower()
        medical_indicators = []
        
        # Check for medical parameters
        for pattern in self.medical_parameter_patterns:
            if re.search(pattern, text_lower):
                medical_indicators.append("medical_parameter")
                break
        
        # Check for numeric values (medical reports should have measurements)
        numeric_values = re.findall(r'\d+\.?\d*', text)
        if len(numeric_values) >= 1:  # Reduced from 3 to 1
            medical_indicators.append("numeric_values")
        
        # Check for medical units
        medical_units = re.findall(r'(?i)(mg/dl|g/dl|/ul|/cumm|%|percent)', text)
        if medical_units:
            medical_indicators.append("medical_units")
        
        # Check for medical keywords
        medical_keywords = re.findall(r'(?i)(test|result|normal|high|low|range|level|count)', text)
        if medical_keywords:
            medical_indicators.append("medical_keywords")
        
        # Check for table-like structure
        if re.search(r'\d+\.?\d*\s+\d+\.?\d*', text) or len(re.findall(r'\s{2,}', text)) > 2:
            medical_indicators.append("table_structure")
        
        # More flexible validation - need at least 1 indicator
        if not medical_indicators:
            return False, f"No medical content detected. Text preview: '{text[:100]}...'"
        
        # Confidence check (more lenient)
        if confidence < self.min_confidence_threshold:
            # If we have strong medical indicators, be more lenient with confidence
            if len(medical_indicators) >= 2:
                return True, f"Low confidence ({confidence:.2f}) but strong medical indicators: {', '.join(medical_indicators)}"
            else:
                return False, f"OCR confidence too low: {confidence:.2f} < {self.min_confidence_threshold}"
        
        return True, f"Validation passed: {len(medical_indicators)} medical indicators ({', '.join(medical_indicators)}), {len(numeric_values)} numeric values, confidence: {confidence:.2f}"
    
    def process_file(self, uploaded_file):
        """
        Main orchestration method - implements all rules
        """
        # STEP 1: Determine file type
        file_type = self.determine_file_type(uploaded_file)
        
        if file_type == "unsupported":
            return self.create_error_response(
                "Unsupported file type. Please upload PDF, PNG, JPG, or JPEG files."
            )
        
        # Create temporary file
        try:
            if file_type == "pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
        except Exception as e:
            return self.create_error_response(f"File processing error: {str(e)}")
        
        try:
            if file_type == "pdf":
                return self.process_pdf_file(temp_file_path)
            else:
                return self.process_image_file(temp_file_path)
        finally:
            # Cleanup temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
    
    def process_pdf_file(self, pdf_path):
        """
        Process PDF file according to Rules 2-3
        """
        # STEP 2: Try direct text extraction first
        digital_text = self.extract_text_from_pdf_direct(pdf_path)
        
        if self.is_text_sufficient(digital_text):
            # Text-based PDF with sufficient content
            return self.create_success_response(
                digital_text, 
                extraction_method="direct_text",
                confidence=0.95
            )
        
        # STEP 3: Fallback to OCR for scanned PDF
        try:
            # Convert PDF pages to images
            pages = convert_from_path(pdf_path, dpi=300)  # High resolution
            
            combined_ocr_result = {
                'text': '',
                'confidence': 0,
                'config_used': 'multi-page'
            }
            
            total_confidence = 0
            valid_pages = 0
            
            for page_num, page_image in enumerate(pages):
                ocr_result = self.perform_ocr_with_validation(page_image)
                
                if ocr_result:
                    is_valid, validation_msg = self.validate_ocr_output(ocr_result)
                    
                    if is_valid:
                        combined_ocr_result['text'] += f"\n--- Page {page_num + 1} ---\n"
                        combined_ocr_result['text'] += ocr_result['text']
                        total_confidence += ocr_result['confidence']
                        valid_pages += 1
            
            if valid_pages > 0:
                combined_ocr_result['confidence'] = total_confidence / valid_pages
                
                # Final validation of combined result
                is_valid, validation_msg = self.validate_ocr_output(combined_ocr_result)
                
                if is_valid:
                    return self.create_success_response(
                        combined_ocr_result['text'],
                        extraction_method="ocr_scanned_pdf",
                        confidence=combined_ocr_result['confidence'],
                        validation_message=validation_msg
                    )
                else:
                    return self.create_low_confidence_response(validation_msg)
            else:
                return self.create_low_confidence_response("No valid pages found in PDF")
                
        except Exception as e:
            return self.create_error_response(f"PDF OCR processing failed: {str(e)}")
    
    def process_image_file(self, image_path):
        """
        ENHANCED image file processing with multiple fallback strategies
        """
        try:
            # Load image
            image = Image.open(image_path)
            
            # Try to enhance image resolution if it's too small
            width, height = image.size
            if width < 800 or height < 600:
                # Upscale small images
                scale_factor = max(800/width, 600/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Perform OCR with multiple strategies
            ocr_result = self.perform_ocr_with_validation(image)
            
            if not ocr_result:
                return self.create_low_confidence_response("OCR failed to extract any text from image")
            
            # Enhanced validation with detailed feedback
            is_valid, validation_msg = self.validate_ocr_output(ocr_result)
            
            if is_valid:
                return self.create_success_response(
                    ocr_result['text'],
                    extraction_method=f"ocr_image_{ocr_result.get('strategy', 'unknown')}",
                    confidence=ocr_result['confidence'],
                    validation_message=validation_msg,
                    debug_info={
                        'preprocessing_strategy': ocr_result.get('strategy'),
                        'ocr_config': ocr_result.get('ocr_config'),
                        'total_attempts': ocr_result.get('total_attempts', 0),
                        'original_image_size': f"{width}x{height}",
                        'processed_image_size': f"{image.size[0]}x{image.size[1]}" if image.size != (width, height) else "unchanged"
                    }
                )
            else:
                # Try emergency fallback strategies
                emergency_result = self.emergency_ocr_fallback(image)
                if emergency_result:
                    return self.create_success_response(
                        emergency_result['text'],
                        extraction_method="emergency_fallback",
                        confidence=emergency_result['confidence'],
                        validation_message="Emergency fallback extraction succeeded",
                        debug_info={'fallback_method': emergency_result.get('method')}
                    )
                else:
                    return self.create_low_confidence_response(
                        f"{validation_msg}. Tried {ocr_result.get('total_attempts', 0)} different approaches."
                    )
                
        except Exception as e:
            return self.create_error_response(f"Image processing failed: {str(e)}")
    
    def emergency_ocr_fallback(self, image):
        """
        Emergency fallback OCR strategies for very challenging images
        """
        emergency_strategies = [
            'extreme_contrast',
            'edge_enhancement',
            'dilation_erosion',
            'gaussian_blur_sharpen'
        ]
        
        for strategy in emergency_strategies:
            try:
                if strategy == 'extreme_contrast':
                    processed = self._emergency_extreme_contrast(image)
                elif strategy == 'edge_enhancement':
                    processed = self._emergency_edge_enhancement(image)
                elif strategy == 'dilation_erosion':
                    processed = self._emergency_dilation_erosion(image)
                elif strategy == 'gaussian_blur_sharpen':
                    processed = self._emergency_gaussian_blur_sharpen(image)
                else:
                    continue
                
                # Try simple OCR on processed image
                text = pytesseract.image_to_string(processed, config=r'--oem 3 --psm 6 -l eng')
                
                if len(text.strip()) > 10:
                    # Check for any medical-like content
                    if (re.search(r'\d', text) and 
                        (re.search(r'(?i)(test|result|level|count|normal|high|low)', text) or
                         len(re.findall(r'\d+\.?\d*', text)) >= 1)):
                        
                        return {
                            'text': text.strip(),
                            'confidence': 0.3,  # Low but acceptable for emergency
                            'method': strategy
                        }
                        
            except Exception:
                continue
        
        return None
    
    def _emergency_extreme_contrast(self, image):
        """Extreme contrast enhancement"""
        img_array = np.array(image.convert('L'))
        
        # Extreme histogram stretching
        min_val, max_val = np.percentile(img_array, [1, 99])
        stretched = np.clip((img_array - min_val) * 255 / (max_val - min_val), 0, 255).astype(np.uint8)
        
        # Binary threshold
        _, binary = cv2.threshold(stretched, 127, 255, cv2.THRESH_BINARY)
        
        return Image.fromarray(binary)
    
    def _emergency_edge_enhancement(self, image):
        """Edge enhancement for faded text"""
        img_array = np.array(image.convert('L'))
        
        # Sobel edge detection
        sobelx = cv2.Sobel(img_array, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_array, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobelx**2 + sobely**2)
        
        # Normalize and threshold
        edges_norm = ((edges / edges.max()) * 255).astype(np.uint8)
        _, binary = cv2.threshold(edges_norm, 50, 255, cv2.THRESH_BINARY)
        
        return Image.fromarray(binary)
    
    def _emergency_dilation_erosion(self, image):
        """Morphological operations for broken text"""
        img_array = np.array(image.convert('L'))
        
        # Threshold
        _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        return Image.fromarray(eroded)
    
    def _emergency_gaussian_blur_sharpen(self, image):
        """Gaussian blur followed by sharpening"""
        img_array = np.array(image.convert('L'))
        
        # Gaussian blur
        blurred = cv2.GaussianBlur(img_array, (3, 3), 0)
        
        # Unsharp mask
        sharpened = cv2.addWeighted(img_array, 1.5, blurred, -0.5, 0)
        
        # Threshold
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return Image.fromarray(binary)
    
    def create_success_response(self, text, extraction_method, confidence, validation_message="", debug_info=None):
        """
        Create successful extraction response with enhanced debugging
        """
        # Process through Phase-1 extraction
        phase1_csv = extract_phase1_medical_image(text)
        
        # Additional processing through other agents
        try:
            validated_json = process_medical_document(text)
            table_csv = extract_medical_table(text)
        except:
            validated_json = "{}"
            table_csv = ""
        
        response_data = {
            "status": "success",
            "extraction_method": extraction_method,
            "confidence": round(confidence, 3),
            "validation_message": validation_message,
            "patient_info": {"name": "", "place": "", "age": "", "sex": ""},
            "medical_parameters": [],
            "phase1_extraction_csv": phase1_csv,
            "table_extraction_csv": table_csv,
            "validated_json": validated_json,
            "raw_text": text,
            "processing_agents": {
                "orchestrator": "Enhanced Medical OCR Orchestration Agent",
                "phase1_extractor": "Phase-1 Medical Image Extraction Agent",
                "validation_agent": "Medical Document Validation Agent",
                "table_extractor": "Medical Table Extraction Agent"
            }
        }
        
        # Add debug info if provided
        if debug_info:
            response_data["debug_info"] = debug_info
        
        return json.dumps(response_data, indent=2)
    
    def create_low_confidence_response(self, reason):
        """
        Create enhanced low confidence response with debugging info
        """
        return json.dumps({
            "status": "low_confidence",
            "error": "OCR_EXTRACTION_FAILED",
            "message": "Unable to extract medical data from the uploaded image. The image may need better quality or different format.",
            "technical_reason": reason,
            "recommendations": [
                "📱 Try taking a new photo with better lighting",
                "🔍 Ensure the text is clearly visible and in focus",
                "📐 Take the photo straight-on (avoid angles)",
                "💡 Use good lighting - avoid shadows and glare",
                "📄 If possible, upload the original PDF instead of a photo",
                "🖼️ Try cropping to show only the test results table",
                "📏 Ensure the image resolution is high enough to read text clearly"
            ],
            "debug_info": {
                "min_confidence_threshold": self.min_confidence_threshold,
                "min_text_length": self.min_text_length,
                "preprocessing_strategies_available": self.preprocessing_strategies,
                "medical_patterns_checked": len(self.medical_parameter_patterns)
            }
        }, indent=2)
    
    def create_error_response(self, error_message):
        """
        Create error response
        """
        return json.dumps({
            "status": "error",
            "error": "PROCESSING_FAILED",
            "message": error_message,
            "recommendations": [
                "Check file format (PDF, PNG, JPG, JPEG supported)",
                "Ensure file is not corrupted",
                "Try uploading a different version of the document"
            ]
        }, indent=2)


# Global orchestrator instance
_ocr_orchestrator = MedicalOCROrchestrator()


def extract_text_from_file(uploaded_file):
    """
    Main entry point - OCR and Data Ingestion Agent with reliability control
    """
    return _ocr_orchestrator.process_file(uploaded_file)


# Legacy functions maintained for backward compatibility
def preprocess_image(image):
    """Legacy function - maintained for backward compatibility"""
    return _ocr_orchestrator.preprocess_image_advanced(image)


def extract_text_from_pdf(uploaded_pdf):
    """Legacy function - redirects to orchestrator"""
    return _ocr_orchestrator.process_file(uploaded_pdf)


def extract_text_from_image(uploaded_image):
    """Legacy function - redirects to orchestrator"""
    return _ocr_orchestrator.process_file(uploaded_image)