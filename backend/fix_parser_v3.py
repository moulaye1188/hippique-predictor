with open('/app/backend/pdf_parser_v3.py', 'r') as f:
    content = f.read()

content = content.replace('pdf.extract_text_from_page(pdf.pages[0])', 'pdf.pages[0].extract_text()')
content = content.replace('pdf.extract_text_from_page(pdf.pages[2])', 'pdf.pages[2].extract_text()')

with open('/app/backend/pdf_parser_v3.py', 'w') as f:
    f.write(content)

print("✅ Fixed pdfplumber API calls")
