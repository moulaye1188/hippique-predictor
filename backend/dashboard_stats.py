"""
DATABASE QUERIES FOR DASHBOARD STATISTICS
Enhanced with arrival tracking
"""

def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    Including: races, horses, data quality, model learning status
    """
    import sqlite3
    from pathlib import Path
    
    DB_PATH = "/app/data/hippique.db"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Count unique horses
        cursor.execute("SELECT COUNT(DISTINCT id) FROM horses_master")
        total_unique_horses = cursor.fetchone()[0] or 0
        
        # 2. Count total races imported
        cursor.execute("SELECT COUNT(DISTINCT id) FROM races")
        total_races_imported = cursor.fetchone()[0] or 0
        
        # 3. Count races with results (arrivals tracked)
        cursor.execute("""
            SELECT COUNT(DISTINCT race_id) 
            FROM horses 
            WHERE position_result IS NOT NULL
        """)
        races_with_results = cursor.fetchone()[0] or 0
        
        # 4. Calculate data quality score
        if total_races_imported == 0:
            data_quality = "Faible"
            quality_score = 0
        elif races_with_results < 5:
            data_quality = "Faible"
            quality_score = 25
        elif races_with_results < 20:
            data_quality = "Acceptable"
            quality_score = 50
        elif races_with_results < 50:
            data_quality = "Bonne"
            quality_score = 75
        else:
            data_quality = "Excellente"
            quality_score = 100
        
        # 5. Model learning status
        cursor.execute("""
            SELECT MAX(created_at) 
            FROM horses 
            WHERE position_result IS NOT NULL
        """)
        last_result_date = cursor.fetchone()[0]
        
        if races_with_results >= 10:
            model_learning_status = "✅ Apprenant (données historiques)"
        elif races_with_results >= 5:
            model_learning_status = "🟡 Apprentissage en cours (peu de données)"
        else:
            model_learning_status = "❌ Pas encore d'apprentissage"
        
        return {
            'total_unique_horses': total_unique_horses,
            'total_races_imported': total_races_imported,
            'races_with_results': races_with_results,
            'data_quality': data_quality,
            'quality_score': quality_score,
            'model_learning_status': model_learning_status,
            'last_result_date': last_result_date,
            'model_can_learn': races_with_results >= 5
        }
    
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            'total_unique_horses': 0,
            'total_races_imported': 0,
            'races_with_results': 0,
            'data_quality': 'Faible',
            'quality_score': 0,
            'model_learning_status': '❌ Erreur lecture DB',
            'last_result_date': None,
            'model_can_learn': False
        }
    
    finally:
        conn.close()
