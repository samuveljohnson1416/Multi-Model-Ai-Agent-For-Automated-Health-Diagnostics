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
        self.min_text_length = 5  # Further reduced for very short medical texts
        self.min_confidence_threshold = 0.2  # Much more lenient for real-world images
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
            r'(?i)test|result|value',
            # More flexible patterns
            r'\d+\.?\d*',  # Any number
            r'(?i)report|analysis|lab',
            r'(?i)blood|serum|plasma'
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
        
        if file_type == "application/pdf" or file_name.endswith('.pdf'):
            return "pdf"
        elif file_type in ["image/png", "image/jpeg", "image/jpg"] or file_name.endswith(('.png', '.jpg', '.jpeg')):
            return "image"
        elif file_type == "application/json" or file_name.endswith('.json'):
            return "json"
        elif file_type == "text/csv" or file_name.endswith('.csv'):
            return "csv"
        elif file_type in ["text/plain", "text/txt"] or file_name.endswith(('.txt', '.text')):
            return "text"  # Add support for text files
        else:
            # Be more lenient - try to process as image if it might be one
            if any(ext in file_name for ext in ['.png', '.jpg', '.jpeg', '.pdf', '.json', '.csv', '.txt']):
                if '.png' in file_name or '.jpg' in file_name or '.jpeg' in file_name:
                    return "image"
                elif '.pdf' in file_name:
                    return "pdf"
                elif '.json' in file_name:
                    return "json"
                elif '.csv' in file_name:
                    return "csv"
                elif '.txt' in file_name:
                    return "text"
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
        ENHANCED validation for OCR output - much more lenient for real-world images
        """
        if not ocr_result:
            return False, "OCR failed to produce any result"
        
        text = ocr_result.get('text', '')
        confidence = ocr_result.get('confidence', 0)
        
        # Very lenient validation for challenging images
        
        # Check minimum text length (very reduced threshold)
        if len(text.strip()) < self.min_text_length:
            return False, f"Text too short: {len(text.strip())} < {self.min_text_length} characters"
        
        # Check for ANY content that could be medical-related (very flexible)
        text_lower = text.lower()
        medical_indicators = []
        
        # Check for medical parameters
        for pattern in self.medical_parameter_patterns:
            if re.search(pattern, text_lower):
                medical_indicators.append("medical_parameter")
                break
        
        # Check for numeric values (medical reports should have measurements)
        numeric_values = re.findall(r'\d+\.?\d*', text)
        if len(numeric_values) >= 1:
            medical_indicators.append("numeric_values")
        
        # Check for medical units
        medical_units = re.findall(r'(?i)(mg/dl|g/dl|/ul|/cumm|%|percent|ml|l|k/mcl|m/mcl|fl|pg)', text)
        if medical_units:
            medical_indicators.append("medical_units")
        
        # Check for medical keywords
        medical_keywords = re.findall(r'(?i)(test|result|normal|high|low|range|level|count|blood|lab|report)', text)
        if medical_keywords:
            medical_indicators.append("medical_keywords")
        
        # Check for table-like structure
        if re.search(r'\d+\.?\d*\s+\d+\.?\d*', text) or len(re.findall(r'\s{2,}', text)) > 1:
            medical_indicators.append("table_structure")
        
        # Check for any alphabetic content (not just numbers)
        if re.search(r'[a-zA-Z]{2,}', text):
            medical_indicators.append("text_content")
        
        # Very flexible validation - accept if we have ANY indicator OR just text with numbers
        if not medical_indicators and len(numeric_values) == 0:
            # Last chance - if we have any meaningful text at all, accept it
            if len(text.strip()) >= 10 and re.search(r'[a-zA-Z]', text):
                return True, f"Accepting text with basic content. Text preview: '{text[:100]}...'"
            return False, f"No medical or meaningful content detected. Text preview: '{text[:100]}...'"
        
        # Confidence check (very lenient)
        if confidence < self.min_confidence_threshold:
            # If we have any indicators or just some text, be very lenient with confidence
            if len(medical_indicators) >= 1 or len(text.strip()) >= 15:
                return True, f"Low confidence ({confidence:.2f}) but accepting due to content indicators: {', '.join(medical_indicators) if medical_indicators else 'text_length'}"
            else:
                return False, f"OCR confidence too low: {confidence:.2f} < {self.min_confidence_threshold}"
        
        return True, f"Validation passed: {len(medical_indicators)} indicators ({', '.join(medical_indicators)}), {len(numeric_values)} numeric values, confidence: {confidence:.2f}"
    
    def process_file(self, uploaded_file):
        """
        Main orchestration method - implements all rules
        """
        # STEP 1: Determine file type
        file_type = self.determine_file_type(uploaded_file)
        
        if file_type == "unsupported":
            return self.create_error_response(
                "Unsupported file type. Please upload PDF, PNG, JPG, JPEG, JSON, or CSV files."
            )
        
        # Create temporary file
        try:
            if file_type == "pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
            elif file_type in ["json", "csv", "text"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
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
            elif file_type == "json":
                return self.process_json_file(temp_file_path)
            elif file_type == "csv":
                return self.process_csv_file(temp_file_path)
            elif file_type == "text":
                return self.process_text_file(temp_file_path)
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
    
    def process_json_file(self, json_path):
        """
        Process JSON file - extract medical data if present
        """
        try:
            # Read JSON file
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Check if JSON contains medical parameters
            json_str = str(json_data).lower()
            medical_keywords = ['hemoglobin', 'glucose', 'cholesterol', 'rbc', 'wbc', 'platelet', 
                              'hb', 'hgb', 'blood', 'test', 'result', 'count', 'level', 'mcv', 'mch', 'mchc']
            
            has_medical_content = any(keyword in json_str for keyword in medical_keywords)
            
            if not has_medical_content:
                # Be more lenient - if it has any numeric data, try to process it
                if re.search(r'\d+\.?\d*', json_str):
                    has_medical_content = True
            
            if not has_medical_content:
                return self.create_error_response(
                    "JSON file doesn't contain medical data. Please upload a blood report with medical parameters."
                )
            
            # Extract medical parameters from JSON - support multiple formats
            medical_text_lines = []
            
            def extract_medical_params(data, prefix=""):
                """Recursively extract medical parameters and convert to text format"""
                if isinstance(data, dict):
                    for key, value in data.items():
                        current_key = f"{prefix}_{key}" if prefix else key
                        
                        # Skip patient info fields but don't exclude everything
                        if current_key.lower() in ['name', 'id'] and prefix == "":
                            continue
                        
                        if isinstance(value, dict):
                            # Check if this is a parameter with value/unit structure
                            if 'value' in value:
                                unit = value.get('unit', '')
                                ref_range = value.get('reference_range', '')
                                status = value.get('status', '')
                                
                                param_line = f"{current_key}: {value['value']}"
                                if unit:
                                    param_line += f" {unit}"
                                if ref_range:
                                    param_line += f" (Normal: {ref_range})"
                                if status:
                                    param_line += f" [{status}]"
                                
                                medical_text_lines.append(param_line)
                            else:
                                # Recursively check nested objects
                                extract_medical_params(value, current_key)
                        elif isinstance(value, list):
                            # Handle arrays of medical parameters
                            for i, item in enumerate(value):
                                if isinstance(item, dict):
                                    extract_medical_params(item, f"{current_key}_{i}")
                                else:
                                    medical_text_lines.append(f"{current_key}_{i}: {item}")
                        elif isinstance(value, (int, float, str)) and str(value).strip():
                            # Simple key-value format
                            medical_text_lines.append(f"{current_key}: {value}")
                elif isinstance(data, list):
                    # Handle top-level arrays
                    for i, item in enumerate(data):
                        if isinstance(item, dict):
                            extract_medical_params(item, f"item_{i}")
                        else:
                            medical_text_lines.append(f"value_{i}: {item}")
            
            # Extract parameters
            extract_medical_params(json_data)
            
            if not medical_text_lines:
                # Last resort - convert entire JSON to text format
                json_text = json.dumps(json_data, indent=2)
                if len(json_text) > 20:
                    return self.create_success_response(
                        f"Medical Data (from JSON):\n\n{json_text}",
                        extraction_method="json_fallback",
                        confidence=0.6,
                        validation_message="JSON processed as raw text - no structured medical parameters found",
                        debug_info={
                            'source_format': 'JSON',
                            'extraction_method': 'raw_json_text_conversion'
                        }
                    )
                else:
                    return self.create_error_response(
                        "No medical parameters found in JSON. Expected format: {'parameter_name': {'value': '12.5', 'unit': 'g/dL', ...}}"
                    )
            
            # Convert to text format for processing
            medical_text = "\n".join(medical_text_lines)
            
            # Add some context
            full_text = f"Medical Report Data (from JSON):\n\n{medical_text}"
            
            return self.create_success_response(
                full_text,
                extraction_method="json_direct",
                confidence=0.95,
                validation_message=f"Successfully extracted {len(medical_text_lines)} medical parameters from JSON",
                debug_info={
                    'source_format': 'JSON',
                    'parameters_found': len(medical_text_lines),
                    'extraction_method': 'structured_json_parsing'
                }
            )
            
        except json.JSONDecodeError as e:
            return self.create_error_response(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            return self.create_error_response(f"JSON processing failed: {str(e)}")
    
    def process_text_file(self, text_path):
        """
        Process plain text file - treat as direct medical report text
        """
        try:
            # Read text file
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            if not text_content.strip():
                return self.create_error_response("Text file is empty")
            
            # Check if it looks like medical content
            if self.is_text_sufficient(text_content):
                return self.create_success_response(
                    text_content,
                    extraction_method="direct_text_file",
                    confidence=0.95,
                    validation_message="Direct text file processing - medical content detected"
                )
            else:
                # Be more lenient - if it has any content, try to process it
                if len(text_content.strip()) >= 10:
                    return self.create_success_response(
                        text_content,
                        extraction_method="direct_text_file_lenient",
                        confidence=0.7,
                        validation_message="Text file processed with lenient validation"
                    )
                else:
                    return self.create_error_response("Text file content too short or no medical data detected")
            
        except Exception as e:
            return self.create_error_response(f"Text file processing error: {str(e)}")

    def process_csv_file(self, csv_path):
        """
        Process CSV file - return as-is for now
        """
        try:
            # Read CSV content
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            return json.dumps({
                "file_type": "CSV",
                "action": "passthrough",
                "csv_content": csv_content,
                "message": "CSV file returned as-is without OCR or extraction"
            })
            
        except Exception as e:
            return self.create_error_response(f"CSV processing error: {str(e)}")
    
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