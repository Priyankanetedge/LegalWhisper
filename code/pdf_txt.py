import fitz  

pdf_path = r"C:\Priyanka\judgement\judgement 3.pdf"
txt_path = r"C:\Priyanka\judgement\judgement3\original\judgement 3.txt"

# Open the PDF
doc = fitz.open(pdf_path)

# Extract text from each page
with open(txt_path, "w", encoding="utf-8") as f:
    for page in doc:
        text = page.get_text()
        f.write(text + "\n")

doc.close()

print(f"PDF converted to text and saved as {txt_path}")
