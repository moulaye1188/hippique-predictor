"""Integration wrapper for PDF parsing"""

def parse_pdf_file(file_path):
    """
    Wrapper to parse PDF with pdfplumber first, fallback to old parser
    Returns: (race_info dict, horses dataframe)
    """
    try:
        from pdf_parser_v2 import parse_pdf_with_pdfplumber
        import pandas as pd
        
        race_info, df = parse_pdf_with_pdfplumber(file_path)
        if not df.empty:
            return race_info, df
    except Exception as e:
        print(f"PDF parser V2 failed: {e}")
    
    # Fallback
    try:
        from advanced_pdf_parser import AdvancedPDFParser
        parser = AdvancedPDFParser()
        race_info, df = parser.parse_pdf(file_path)
        return race_info, df
    except Exception as e:
        print(f"PDF parser fallback failed: {e}")
        return {}, None
