import pdfplumber

with pdfplumber.open("mynotes.pdf") as pdf:
    print("Number of pages:", len(pdf.pages))
    
    full_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ---")
        print(text)
        if text:
            full_text += text

print("=== FULL TEXT LENGTH ===")
print(len(full_text))