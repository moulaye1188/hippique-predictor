#!/usr/bin/env python3
"""Update app.py to use new parser"""

with open('/app/backend/app.py', 'r') as f:
    content = f.read()

# Find and replace the parser section
old_section = """        # Parse PDF
        parser = AdvancedPDFParser()
        race_info, horses_df = parser.parse_pdf(temp_path)
        
        # Validate
        is_valid, errors = parser.validate_race_info()
        if not is_valid:
            return jsonify({'error': 'Invalid PDF data', 'details': errors}), 400"""

new_section = """        # Parse PDF - use new pdfplumber parser
        race_info, horses_df = parse_pdf_file(temp_path)
        
        # Validate
        if horses_df is None or horses_df.empty:
            return jsonify({'error': 'Failed to extract horses from PDF'}), 400"""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open('/app/backend/app.py', 'w') as f:
        f.write(content)
    print("✅ app.py updated successfully")
else:
    print("⚠️ Could not find section to replace - manual edit needed")
    print(f"Looking for: {old_section[:100]}...")
