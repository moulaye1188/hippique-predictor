"""
Migration script to add excluded_horses column to races table
Run this ONCE to add the column
"""
import sqlite3
import json

DB_PATH = "/app/data/hippique.db"

def migrate_add_excluded_horses():
    """Add excluded_horses column to races table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(races)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'excluded_horses' not in columns:
            print("Adding 'excluded_horses' column to races table...")
            cursor.execute('''
                ALTER TABLE races
                ADD COLUMN excluded_horses TEXT DEFAULT '[]'
            ''')
            conn.commit()
            print("✓ Column added successfully!")
        else:
            print("✓ Column already exists!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_excluded_horses()
