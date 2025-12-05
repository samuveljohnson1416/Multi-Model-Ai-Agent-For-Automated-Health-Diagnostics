import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import io


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
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            return f"Error: {str(e)}"

    return text.strip()


def extract_text_from_image(uploaded_image):
    try:
        image = Image.open(uploaded_image)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        return extract_text_from_image(uploaded_file)
    else:
        return f"Unsupported file type: {file_type}"
