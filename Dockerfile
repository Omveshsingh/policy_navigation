# --- policy_navigation: Streamlit OCR + RAG chatbot ---
FROM python:3.11-slim

# System dependencies the app needs:
#   tesseract-ocr  -> required by pytesseract (OCR)
#   poppler-utils  -> required by pdf2image (PDF -> image conversion)
#   libglib2.0-0   -> required by opencv-python-headless at import time
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/bin
# The app's ollama calls need to reach the ollama service (see docker-compose.yml)
ENV OLLAMA_HOST=http://ollama:11434

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "notebook/integrated_ocr_ollama_button.py", "--server.port=8501", "--server.address=0.0.0.0"]