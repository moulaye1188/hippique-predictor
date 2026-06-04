with open('/app/backend/pdf_parser_final.py', 'r') as f:
    content = f.read()

# Fix the format string issue
old = 'race_info[\'race_time\'] = f"{time_match.group(1):02d}:{time_match.group(2)}"'
new = 'race_info[\'race_time\'] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"'
content = content.replace(old, new)

with open('/app/backend/pdf_parser_final.py', 'w') as f:
    f.write(content)

print("✅ Fixed format string bug")
