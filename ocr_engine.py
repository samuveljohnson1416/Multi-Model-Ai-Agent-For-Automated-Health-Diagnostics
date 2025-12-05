import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import io


def extract_text_from_pdf(uploaded_pdf):
    """
    Extracts text from a PDF file.
    1. Attempts direct text extraction using pdfplumber.
    2. If text is empty (scanned PDF), falls back to OCR.
    """

    text = ""

    try:
        # Streamlit files come as BytesIO, so we save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_pdf.read())
            temp_pdf_path = temp_pdf.name
    except Exception as e:
        return f"Error saving PDF: {str(e)}"

    # First: try extracting digital text
    try:
        with pdfplumber.open(temp_pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass

    # If no text extracted → use OCR fallback
    if len(text.strip()) < 10:
        try:
            pages = convert_from_path(temp_pdf_path)
            text = ""
            for img in pages:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            return f"OCR Error: {str(e)}"

    return text.strip()



def extract_text_from_image(uploaded_image):
    """
    Extracts text from image formats:
    PNG, JPG, JPEG
    """

    try:
        # Streamlit gives a BytesIO object; convert to PIL image
        image = Image.open(uploaded_image)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"OCR Image Error: {str(e)}"


def extract_text_from_file(uploaded_file):
    """
    Main function to extract text from uploaded file.
    Handles both PDF and image formats.
    """
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        return extract_text_from_image(uploaded_file)
    else:
        return f"Unsupported file type: {file_type}"
