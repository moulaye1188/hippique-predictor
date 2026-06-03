#!/usr/bin/env python3
"""Quick inline test of PDF parser logic"""
import re

def parse_tabular_format_test(text):
    """Simplified parser test"""
    horses = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or 'LES MEILLEURS' in line:
            continue
        
        # Skip headers
        if 'CHEVAUX' in line or 'JOCKEYS' in line:
            continue
        
        # Split on multiple spaces
        parts = re.split(r'\s{2,}', line)
        
        if len(parts) >= 2:
            try:
                num_match = re.match(r'^(\d{1,2})', parts[0])
                if num_match:
                    horse_num = int(num_match.group(1))
                    horse_name = parts[1].strip()
                    
                    # Last part is result position (format: "3-3", "1/1", etc.)
                    last_part = parts[-1].strip() if parts else ""
                    result_match = re.search(r'^(\d+)', last_part)
                    result_pos = int(result_match.group(1)) if result_match else None
                    
                    horse = {
                        'horse_number': horse_num,
                        'horse_name': horse_name,
                        'result_position': result_pos
                    }
                    horses.append(horse)
            except (ValueError, IndexError):
                continue
    
    return horses

# Test with sample data
sample = """
N°  CHEVAUX  JOCKEYS  ENTRAINEURS  PROPRIETAIRES  SEXE  AGE  CORDE  POIDS  PERF.  GAINS  ARRIVEE
01  MUST BAY  A.THOMAS  C.Y.LERNER  J.C.BRUN  M.3  2  6,0  57,0  13.32  39618  3-3
02  REVE BLEU  M.BARZALONA  G.BIETOLINI  ARGE  F.3  8  59,6  57.1  18 560  1-4
03  LE FUTUR  T.PICCONE  HA.PANTALL  PH.LASSEN  M.3  9  58.5  9.1  18 340  4-5
"""

horses = parse_tabular_format_test(sample)
print(f"OK Parsed {len(horses)} horses")
for h in horses:
    print(f"  #{h['horse_number']}: {h['horse_name']} -> Result Position: {h['result_position']}")
