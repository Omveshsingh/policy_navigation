import os
import re
import pandas as pd
import pdfplumber

# List your PDFs with metadata
pdf_files = [
    {"path": r"D:\info\data\india\1 National Health Policy 2017 (English) .pdf", 
     "country": "India", "domain": "Health", "title": "National Health Policy", "year": 2017},
    {"path": r"D:\info\data\india\Operational_Guidelines_For_CPHC.pdf", 
     "country": "India", "domain": "Health", "title": "Operational Guidelines for Comprehensive Primary Health Care", "year": 2018},
    {"path": r"D:\info\data\india\HealthInsuranceforIndia’sMissingMiddle_01-11-2021_digital pub.pdf", 
     "country": "India", "domain": "Health", "title": "Health Insurance for India’s Missing Middle", "year": 2021},
    {"path": r"D:\info\data\india\NEP.pdf", 
     "country": "India", "domain": "Education", "title": "National Education Policy", "year": 2020},
    {"path": r"D:\info\data\UK\UK 2.pdf", 
     "country": "UK", "domain": "Health", "title": "Healthy Lives, Healthy People", "year": 2010},
    {"path": r"D:\info\data\UK\UK 1.pdf", 
     "country": "UK", "domain": "Health", "title": "Health And Care Act", "year": 2022},
    {"path": r"D:\info\data\UK\Finance regualation.pdf", 
     "country": "UK", "domain": "Finance", "title": "Finance Regulation", "year": 2023},
    {"path": r"D:\info\data\UK\Finance regualation2.pdf", 
     "country": "UK", "domain": "Finance", "title": "Finance Regulation", "year": 2022},
    {"path": r"D:\info\data\UK\Legal.pdf", 
     "country": "UK", "domain": "Legal", "title": "Human trafficking laws", "year": 2023},
    {"path": r"D:\info\data\USA\USA 1.pdf", 
     "country": "USA", "domain": "Health", "title": "Introduction to the U.S. Health Care System", "year": 2017},
    {"path": r"D:\info\data\USA\USA 2.pdf", 
     "country": "USA", "domain": "Health", "title": "Healthcare Policy: The Basics", "year": 1999},
    {"path": r"D:\info\data\USA\USA 3.pdf", 
     "country": "USA", "domain": "Health", "title": "Medical Society of Virginia Policy Compendium", "year": 2024},
    {"path": r"D:\info\data\usa\financial1.pdf", 
     "country": "USA", "domain": "Finance", "title": "Public Law", "year": 2010},
    {"path": r"D:\info\data\usa\financial2.pdf", 
     "country": "USA", "domain": "Finance", "title": "Financial Regulations", "year": 2015}
]

# Function to extract and structure text
def extract_sections(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    print(f"⚠️ Skipping page {page_num} in {os.path.basename(pdf_path)}: {e}")
    except Exception as e:
        print(f"❌ Could not open {pdf_path}: {e}")
        return []

    # Split into sections (based on headings in ALL CAPS / Title Case)
    sections = re.split(r"\n(?=[A-Z][A-Za-z\s]{3,50})", text)
    return sections

# Collect all records
records = []
for pdf in pdf_files:
    sections = extract_sections(pdf["path"])
    for sec in sections:
        sec = sec.strip()
        if len(sec) > 20:  # ignore tiny fragments
            heading = sec.split("\n")[0][:80]  # limit heading length
            content = " ".join(sec.split("\n")[1:])
            records.append({
                "Country": pdf["country"],
                "Domain": pdf["domain"],
                "Title": pdf["title"],
                "Year": pdf["year"],
                "Section": heading,
                "Content": content
            })

# Save to CSV
df = pd.DataFrame(records)
output_file = "policies_dataset.csv"
df.to_csv(output_file, index=False, encoding="utf-8")

print(f"✅ Dataset saved as {output_file} with {len(df)} rows")
