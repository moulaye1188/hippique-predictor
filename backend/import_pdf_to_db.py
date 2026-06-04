"""Integration: PDF Parser → Database"""
import sys
sys.path.insert(0, '/app/backend')

from pdf_parser_smart import parse_pdf_smart
from database_schema_v2 import save_race_enriched, save_horse_enriched, save_race_pronostics, save_race_classements
from database import get_or_create_horse_master, add_horse_race


def import_race_from_pdf(pdf_path: str) -> dict:
    """
    Complete workflow: Parse PDF → Save to DB → Update master horses
    """
    print(f"\n{'='*80}")
    print(f"IMPORTING RACE FROM PDF: {pdf_path}")
    print(f"{'='*80}\n")
    
    # Step 1: Parse PDF
    print("Step 1: Parsing PDF...")
    race_info, horses_df, pronostics, classements, best_week = parse_pdf_smart(pdf_path)
    print(f"✓ Parsed: {len(horses_df)} horses, {len(pronostics)} pronostics, {len(classements)} classements\n")
    
    # Step 2: Save race to DB
    print("Step 2: Saving race to database...")
    race_id = save_race_enriched(race_info)
    print(f"✓ Race saved with ID: {race_id}\n")
    
    # Step 3: Save horses
    print("Step 3: Saving horses...")
    horses_saved = 0
    for idx, row in horses_df.iterrows():
        horse_dict = row.to_dict()
        horse_id = save_horse_enriched(race_id, horse_dict)
        horses_saved += 1
    print(f"✓ {horses_saved} horses saved\n")
    
    # Step 4: Save pronostics
    print("Step 4: Saving pronostics...")
    if pronostics:
        save_race_pronostics(race_id, pronostics)
        print(f"✓ {len(pronostics)} pronostic sources saved\n")
    else:
        print("✗ No pronostics found\n")
    
    # Step 5: Save classements
    print("Step 5: Saving classements...")
    if classements:
        save_race_classements(race_id, classements)
        print(f"✓ {len(classements)} classements saved\n")
    else:
        print("✗ No classements found\n")
    
    # Step 6: Update master horses
    print("Step 6: Updating master horse database...")
    horses_updated = 0
    for idx, row in horses_df.iterrows():
        horse_name = row.get('horse_name')
        jockey = row.get('jockey')
        trainer = row.get('trainer')
        
        if not horse_name:
            continue
        
        # Get or create master horse
        horse_master_id = get_or_create_horse_master(horse_name, jockey, trainer)
        
        # Add this race to horse history
        add_horse_race(
            horse_master_id,
            race_info.get('race_date'),
            race_info.get('hippodrome'),
            distance=race_info.get('distance'),
            race_type=race_info.get('race_type'),
            odds=row.get('odds_paris_turf'),
            odds_probability=None,
            age=None,
            weight=row.get('weight'),
            result_position=None,
            imported_from=pdf_path
        )
        horses_updated += 1
    
    print(f"✓ {horses_updated} master horses updated\n")
    
    # Summary
    print(f"{'='*80}")
    print("✅ IMPORT COMPLETE")
    print(f"{'='*80}")
    print(f"Race ID: {race_id}")
    print(f"Horses: {horses_saved}")
    print(f"Pronostics: {len(pronostics)}")
    print(f"Classements: {len(classements)}")
    print(f"Master horses: {horses_updated}\n")
    
    return {
        'race_id': race_id,
        'horses_count': horses_saved,
        'pronostics_count': len(pronostics),
        'classements_count': len(classements),
        'master_horses_count': horses_updated
    }


if __name__ == '__main__':
    result = import_race_from_pdf('/app/backend/test_full.pdf')
    print(f"Result: {result}")
