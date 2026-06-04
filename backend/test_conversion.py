#!/usr/bin/env python3
from pdf_parser_v2 import convert_to_native_types
import numpy as np

# Test
test = {'value': np.int64(42), 'list': [np.int64(1), np.int64(2)]}
result = convert_to_native_types(test)
print(f'Original: {test}')
print(f'Converted: {result}')
print(f'Types OK: {isinstance(result["value"], int)}')
print("✅ Conversion works!")
