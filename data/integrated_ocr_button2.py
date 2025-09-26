import streamlit as st
import pandas as pd
import docx
from PyPDF2 import PdfReader
import os
from pdf2image import convert_from_path
import pytesseract
from docx import Document
import tempfile
import json

# Configure Tesseract & Poppler
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
poppler_path = r"D:\\Release-25.07.0-0\\poppler-25.07.0\\Library\\bin"

# App title
st.set_page_config(page_title="📂 File Previewer", layout="wide")
st.title("📂 Smart File Upload & Previewer")
st.markdown("### Upload PDF files and preview + extract text with OCR")

# Sidebar upload
st.sidebar.header("📁 Upload Section")
uploaded_file = st.sidebar.file_uploader(
    "Choose a file", 
    type=["pdf"], 
    accept_multiple_files=False
)

# Chat history
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "file_content" not in st.session_state:
    st.session_state["file_content"] = ""

# OCR function
def pdf_to_word(pdf_path, docx_path, json_path):
    pages = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
    doc = Document()
    extracted_data = []

    for i, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page, lang="eng", config="--psm 6")
        doc.add_paragraph(text)
        extracted_data.append({"page": i, "text": text})
        st.write(f"✅ Processed page {i}/{len(pages)}")

    doc.save(docx_path)
    output_path = os.path.splitext(uploaded_file.name)[0] + ".json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    return extracted_data

# Main app body
if uploaded_file is not None:
    st.success(f"✅ {uploaded_file.name} uploaded successfully!")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        temp_pdf_path = tmp.name

    # Define output paths
    output_docx = temp_pdf_path.replace(".pdf", ".docx")
    output_json = temp_pdf_path.replace(".pdf", ".json")

    # Run OCR
    with st.spinner("🔍 Running OCR on your PDF..."):
        extracted_data = pdf_to_word(temp_pdf_path, output_docx, output_json)

    # Save extracted text in session state for preview/chat
    st.session_state["file_content"] = "\n".join([p["text"] for p in extracted_data])

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Preview", "📊 File Info", "💬 Chat", "⬇️ Download"])

    with tab1:
        st.subheader("📑 File Preview (first 1000 chars)")
        st.text(st.session_state["file_content"][:1000])

    with tab2:
        st.write("**File Name:**", uploaded_file.name)
        st.write("**File Type:** PDF")
        st.write("**File Size:**", f"{uploaded_file.size/1024:.2f} KB")
        st.write("**Pages Extracted:**", len(extracted_data))

    with tab3:
        st.header("💬 Chat about your file")
        user_input = st.text_input("Type your message and press Enter", key="chat_input")
        if user_input:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            if user_input.lower() in st.session_state["file_content"].lower():
                bot_reply = f"Yes, I found something related: \n\n...{user_input}..."
            else:
                bot_reply = "I looked through the file but couldn’t find anything directly related."
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})
            st.markdown(f"**🤖 Bot:** {bot_reply}")

    with tab4:
        st.subheader("⬇️ Download Extracted Files")
        with open(output_docx, "rb") as f:
            st.download_button("Download Word File (.docx)", f, file_name="extracted_text.docx")
        with open(output_json, "rb") as f:
            st.download_button("Download JSON File", f, file_name="extracted_text.json")

else:
    st.info("📤 Please upload a PDF from the sidebar to begin.")
