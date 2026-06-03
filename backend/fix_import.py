#!/usr/bin/env python3
import re

# Read the new function
with open('/app/backend/import_and_process_new.py', 'r') as f:
    new_func = f.read()

# Read the old data_import.py
with open('/app/backend/data_import.py', 'r') as f:
    content = f.read()

# Find and replace the import_and_process function
pattern = r'def import_and_process\(file_path:.*?\n(?:.*?\n)*?return None, \[str\(e\)\]'
content = re.sub(pattern, new_func.strip(), content, flags=re.DOTALL)

# Write back
with open('/app/backend/data_import.py', 'w') as f:
    f.write(content)

print("✅ import_and_process updated in data_import.py")
