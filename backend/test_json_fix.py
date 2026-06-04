#!/usr/bin/env python3
import json
import numpy as np
import pandas as pd
from pdf_parser_v2 import convert_to_native_types

# Test: créer une dataframe avec int64
df = pd.DataFrame({'horse_number': [np.int64(1), np.int64(2)], 'horse_name': ['TEST', 'TEST2']})

# Essayer de la sérialiser
try:
    row_dict = df.iloc[0].to_dict()
    print(f"Direct json.dumps - Error expected:")
    json.dumps(row_dict)
except TypeError as e:
    print(f"❌ Error: {e}")
    print(f"Type: {type(row_dict['horse_number'])}")

# Utiliser la conversion
row_dict_converted = convert_to_native_types(row_dict)
try:
    json.dumps(row_dict_converted)
    print(f"✅ After conversion - OK!")
except TypeError as e:
    print(f"❌ Still error: {e}")
