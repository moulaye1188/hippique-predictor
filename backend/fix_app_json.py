#!/usr/bin/env python3
with open('/app/backend/app.py', 'r') as f:
    content = f.read()

# Add the import if not present
if 'from pdf_parser_v2 import convert_to_native_types' not in content:
    # Find the line after other imports
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_idx = i + 1
    lines.insert(insert_idx, 'from pdf_parser_v2 import convert_to_native_types')
    content = '\n'.join(lines)

# Convert race_info and predictions_list to native types before JSON
# Find the load_race_from_pdf return statement and add conversion
old_section = """        return jsonify({
            'success': True,
            'race_id': race_id,
            'race_info': race_info,
            'horses_imported': saved_horses_count,
            'new_horses': new_horses_count,
            'predictions': predictions_list[:10],"""

new_section = """        return jsonify({
            'success': True,
            'race_id': race_id,
            'race_info': convert_to_native_types(race_info),
            'horses_imported': int(saved_horses_count),
            'new_horses': int(new_horses_count),
            'predictions': convert_to_native_types(predictions_list[:10]),"""

content = content.replace(old_section, new_section)

with open('/app/backend/app.py', 'w') as f:
    f.write(content)

print("✅ app.py fixed with type conversions")
