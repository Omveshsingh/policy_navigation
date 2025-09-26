import os
from pdf2image import convert_from_path
import pytesseract
from docx import Document

# Set paths (adjust if different on your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
poppler_path = r"D:\\Release-25.07.0-0\\poppler-25.07.0\\Library\\bin"  # update to your Poppler bin path

def pdf_to_word(pdf_path, output_path=None):
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    
    # Create Word document
    doc = Document()
    
    # Process each page
    for i, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page, lang="eng")
        doc.add_paragraph(text)
        print(f"Processed page {i}/{len(pages)}")
    
    # Save Word file
    if not output_path:
        output_path = os.path.splitext(pdf_path)[0] + ".docx"
    doc.save(output_path)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    # Example usage
    pdf_file = r"D:\info\data\india\NEP.pdf"  # change to your PDF file
    pdf_to_word(pdf_file)
