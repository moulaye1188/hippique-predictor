#!/usr/bin/env python3
"""
ADD MISSING ARRIVAL PARSING & MODEL RETRAINING

This system was missing:
1. Parsing of race results/arrivals from PDFs
2. Updating race results in database
3. Retraining model with actual outcomes for learning
"""

# NEW FUNCTION: Parse race results/arrivals

def _parse_race_arrivals(text: str) -> Dict:
    """Extract race arrival (results) from PDF text"""
    arrivals = {}
    
    # Pattern: "Arrivée : 7 - 11 - 2 - 15"
    # Or: "ARRIVÉE :\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)"
    
    # Try different patterns
    patterns = [
        r'ARRIVÉE\s*:\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)',  # French
        r'ARRIVAL\s*:\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)',  # English
        r'Arrivée\s*:\s*(\d+)\s*–\s*(\d+)\s*–\s*(\d+)\s*–\s*(\d+)',  # Different dash
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            arrivals['1st'] = int(match.group(1))
            arrivals['2nd'] = int(match.group(2))
            arrivals['3rd'] = int(match.group(3))
            arrivals['4th'] = int(match.group(4))
            arrivals['quartet'] = [int(match.group(1)), int(match.group(2)), 
                                  int(match.group(3)), int(match.group(4))]
            return arrivals
    
    # Try single-line pattern
    single_match = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', text)
    if single_match:
        arrivals['1st'] = int(single_match.group(1))
        arrivals['2nd'] = int(single_match.group(2))
        arrivals['3rd'] = int(single_match.group(3))
        arrivals['4th'] = int(single_match.group(4))
        arrivals['quartet'] = [int(single_match.group(1)), int(single_match.group(2)),
                              int(single_match.group(3)), int(single_match.group(4))]
    
    return arrivals


# NEW FUNCTION: Update race with actual results

def save_race_results(race_id: int, arrivals: Dict, horses_df: pd.DataFrame):
    """Update race database with actual arrival results"""
    if not arrivals or 'quartet' not in arrivals:
        print("⚠️  No arrival data found")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    quartet = arrivals['quartet']
    
    try:
        # Update each horse with their actual position
        for position, horse_number in enumerate(quartet, 1):
            # Find horse in this race
            cursor.execute(
                'UPDATE horses SET position_result = ? WHERE race_id = ? AND horse_number = ?',
                (position, race_id, horse_number)
            )
        
        conn.commit()
        print(f"✅ Race {race_id} results saved: {quartet}")
        return True
    except Exception as e:
        print(f"❌ Error saving race results: {e}")
        return False
    finally:
        conn.close()


# NEW WORKFLOW: When loading PDF from NEXT DAY

def process_pdf_with_previous_results(file_path: str, previous_race_id: int = None):
    """
    When processing a PDF, check if it contains results from PREVIOUS race
    
    Typical workflow:
    1. Monday PDF: Race for Monday -> save predictions
    2. Tuesday PDF: Contains Monday results + Tuesday predictions
    3. Parse Monday results -> Update DB -> Retrain model -> Make Tuesday predictions
    """
    
    # Parse current PDF
    race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(file_path)
    
    # Extract ANY arrival results present
    full_text = ""
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages[:5]:  # Check first 5 pages
                full_text += page.extract_text() + "\n"
    except:
        pass
    
    # Parse arrivals
    arrivals = _parse_race_arrivals(full_text)
    
    # If we found results for a race
    if arrivals and previous_race_id:
        print(f"✅ Found race results in PDF: {arrivals['quartet']}")
        
        # 1. Save results to DB
        save_race_results(previous_race_id, arrivals, horses_df)
        
        # 2. RETRAIN MODEL with new data
        print("🔄 Retraining model with new race data...")
        model = UpgradedHippiqueModel()
        model.load()
        model.train()  # Retrains with all historical data INCLUDING new result
        model.save()
        print("✅ Model retrained!")
    
    return race_info, horses_df, pronostics, classements, best_week


# MODIFIED app.py route

def load_race_from_pdf_v2_with_results():
    """Updated route that captures results"""
    
    # ... existing code ...
    
    # NEW: Check if PDF contains previous race results
    full_text = extract_full_pdf_text(temp_path)
    previous_arrivals = _parse_race_arrivals(full_text)
    
    if previous_arrivals:
        # You know which race this is from (date parsing)
        print(f"📊 Race results found: {previous_arrivals['quartet']}")
        # Update previous race with results
        # save_race_results(previous_race_id, previous_arrivals, ...)
        # Retrain model
    
    # ... rest of code ...


print("""
WHAT WAS MISSING:
================

1. ❌ No arrival parsing from PDFs
   ✅ NEW: _parse_race_arrivals() function

2. ❌ No database update for race results
   ✅ NEW: save_race_results() function

3. ❌ No automatic model retraining after new results
   ✅ NEW: process_pdf_with_previous_results() workflow

4. ❌ Model never learns from actual outcomes
   ✅ FIXED: With retraining workflow

HOW IT SHOULD WORK:
===================

Day 1 (Monday):
  - Parse Monday's race PDF
  - Make predictions
  - Save to database

Day 2 (Tuesday):
  - Parse Tuesday PDF
  - EXTRACT Monday's results (should be in Tuesday's PDF)
  - UPDATE Monday's race in DB with actual results
  - RETRAIN model with historical data + new actual results
  - Make Tuesday predictions (with improved model!)

THIS IS CRUCIAL FOR MODEL IMPROVEMENT:
=======================================

Without capturing actual results:
  - Model never learns if predictions were right/wrong
  - Cannot improve over time
  - Gets stuck with initial training data

With capturing actual results:
  - Model learns from each race outcome
  - Gets better week by week
  - Can identify patterns that work

IMPLEMENTATION PRIORITY:
========================

1. HIGH: Add _parse_race_arrivals() to pdf_parser_smart.py
2. HIGH: Add save_race_results() to database.py
3. HIGH: Modify app.py to call these functions
4. MEDIUM: Add automatic model retraining schedule
5. MEDIUM: Track model improvement metrics week-by-week
""")
