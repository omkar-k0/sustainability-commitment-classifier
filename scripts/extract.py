import pdfplumber
import sys
import os

COMPANIES = {
    "siemens": "raw/siemens.pdf",
    "basf": "raw/basf.pdf",
    "sap": "raw/sap.pdf",
    "henkel": "raw/henkel.pdf",
    "bosch": "raw/bosch.pdf",
}

def extract(pdf_path):
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)

for name, path in COMPANIES.items():
    out_path = f"data/{name}.txt"
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            text = f.read()
        print(f"{name}: cached, {len(text)} chars")
        continue
    try:
        text = extract(path)
    except Exception as e:
        print(f"{name}: ERROR {e}")
        continue
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{name}: extracted {len(text)} chars")
