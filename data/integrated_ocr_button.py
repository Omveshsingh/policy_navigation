import streamlit as st
import os
from pdf2image import convert_from_path
import pytesseract
from docx import Document
import json

# ---- CONFIG ----
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"D:\Release-25.07.0-0\poppler-25.07.0\Library\bin"

st.set_page_config(page_title="📂 File Previewer", layout="wide")
st.title("📂 Smart File Upload & Previewer")
st.markdown("Upload a **scanned PDF**, extract text with Tesseract OCR, and download as a Word file.")

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("Upload a scanned PDF", type=["pdf"])

if uploaded_file is not None:
    st.success(f"✅ {uploaded_file.name} uploaded successfully!")

    # Save uploaded file temporarily
    temp_pdf_path = "temp_uploaded.pdf"
    with open(temp_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ---- OCR PROCESS ----
    with st.spinner("Processing PDF with OCR... please wait."):
        pages = convert_from_path(temp_pdf_path, dpi=300, poppler_path=poppler_path)
        extracted_data = {"file_name": uploaded_file.name, "total_pages": len(pages), "pages": []}
        all_text = ""

        for i, page in enumerate(pages, start=1):
            text = pytesseract.image_to_string(page, lang="eng")
            extracted_data["pages"].append({"page": i, "text": text})
            all_text += text + "\n"
            st.write(f"Processed page {i}/{len(pages)}")

        # Output file path (same name but .json)
        output_path = os.path.splitext(uploaded_file.name)[0] + ".json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    st.success(f"✅ OCR completed and saved as: {output_path}")

    # ---- TABS: Preview + Download ----
    tab1, tab2 = st.tabs(["🔍 Preview", "⬇️ Download"])

    with tab1:
        st.subheader("📑 Extracted Preview")
        st.text(all_text[:1000])  # Show first 1000 chars

    with tab2:
        with open(output_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Word File",
                data=f,
                file_name=output_path,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

else:
    st.info("📤 Please upload a scanned PDF to begin.")


