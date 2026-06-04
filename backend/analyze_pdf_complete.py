#!/usr/bin/env python3
"""Complete PDF analysis - understand the full structure"""
import pdfplumber
import re

with pdfplumber.open('/app/backend/test_full.pdf') as pdf:
    print(f"{'='*80}")
    print(f"COMPLETE PDF ANALYSIS")
    print(f"{'='*80}\n")
    
    print(f"Total pages: {len(pdf.pages)}\n")
    
    # Analyze each page
    for page_idx in range(len(pdf.pages)):
        page = pdf.pages[page_idx]
        text = page.extract_text()
        
        print(f"\n{'='*80}")
        print(f"PAGE {page_idx} ANALYSIS")
        print(f"{'='*80}")
        print(f"Text length: {len(text)} characters\n")
        
        # Save full text to file for manual inspection
        with open(f'/app/backend/page_{page_idx}_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Saved full text to page_{page_idx}_text.txt\n")
        
        # Identify sections
        print("SECTIONS DETECTED:")
        
        # Race header
        if "QUARTE" in text or "DIMANCHE" in text or "PARISLONGCHAMP" in text:
            print("  ✅ Race header section")
        
        # Horse descriptions
        if re.search(r'\d+\s*-\s*[A-Z\s]+\s*:', text):
            print("  ✅ Horse descriptions (1-MUST BAY, 2-REVE BLEU, etc.)")
        
        # Results table
        if "RESULTATS" in text.upper() or "ARRIVÉE" in text.upper():
            print("  ✅ Results section")
        
        # Rankings/scores
        if re.search(r'(FORME|CLASSE|PROGR[EÉ]S|R[EÉ]GULARIT[EÉ])', text, re.IGNORECASE):
            print("  ✅ Rankings section (FORME, CLASSE, etc.)")
        
        # Pronostics
        if re.search(r'(TURF-FR|L\'ALSACE|VOIX DU NORD|TURFOMANIA|EQUIDIA|LE PARISIEN)', text, re.IGNORECASE):
            print("  ✅ Pronostics section (external sources)")
        
        # Odds tables
        if re.search(r'PARIS\s*TURF|TI[EÉ]RC[EÉ].*MAGAZINE', text, re.IGNORECASE):
            print("  ✅ Odds tables (Paris Turf, Tiercé Magazine)")
        
        # Best trainers/jockeys
        if re.search(r'MEILLEUR.*SEMAINE|ENTRAINEURS|JOCKEYS', text, re.IGNORECASE):
            print("  ✅ Best of week section")
        
        # Table count
        tables = page.extract_tables()
        if tables:
            print(f"  ✅ Structured tables: {len(tables)} found")
            for t_idx, table in enumerate(tables):
                if table:
                    print(f"     Table {t_idx}: {len(table)} rows × {len(table[0]) if table[0] else 0} cols")

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print("Check page_0_text.txt and page_1_text.txt for full content")
print(f"{'='*80}\n")
