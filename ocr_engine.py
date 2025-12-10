import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import tempfile
import io
import os
import cv2
import numpy as np

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def preprocess_image(image):
    """Enhance image quality for better OCR"""
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh)
    
    # Convert back to PIL
    return Image.fromarray(denoised)


def extract_text_from_pdf(uploaded_pdf):
    text = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_pdf.read())
            temp_pdf_path = temp_pdf.name
    except Exception as e:
        return f"Error: {str(e)}"

    try:
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    if len(text.strip()) < 10:
        try:
            pages = convert_from_path(temp_pdf_path)
            text = ""
            for img in pages:
                processed_img = preprocess_image(img)
                custom_config = r'--oem 3 --psm 6'
                text += pytesseract.image_to_string(processed_img, config=custom_config) + "\n"
        except Exception as e:
            return f"Error: {str(e)}"

    return text.strip()


def extract_text_from_image(uploaded_image):
    try:
        image = Image.open(uploaded_image)
        
        # Preprocess image for better OCR
        processed_image = preprocess_image(image)
        
        # Extract text with custom config
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        return text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        return extract_text_from_image(uploaded_file)
    elif file_type == "application/json":
        return uploaded_file.read().decode('utf-8')
    else:
        return f"Unsupported file type: {file_type}"
