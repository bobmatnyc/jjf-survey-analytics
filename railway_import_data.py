#!/usr/bin/env python3
"""
Import data to Railway database
Run this script on Railway to import local data
"""

import sqlite3
import os
import sys

def import_data():
    """Import data from SQL files to Railway databases."""
    
    print("📥 Importing Data to Railway Databases")
    print("=" * 40)
    
    # Import main database
    if os.path.exists('railway_data_import.sql'):
        print("📊 Importing main database data...")
        try:
            with sqlite3.connect('surveyor_data_improved.db') as conn:
                with open('railway_data_import.sql', 'r') as f:
                    sql_content = f.read()
                    # Execute in chunks to avoid issues
                    statements = sql_content.split(';')
                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                conn.execute(statement)
                            except Exception as e:
                                if 'already exists' not in str(e):
                                    print(f"   ⚠️ SQL error: {e}")
                conn.commit()
            print("   ✅ Main database import completed")
        except Exception as e:
            print(f"   ❌ Error importing main database: {e}")
    
    # Import survey database
    if os.path.exists('railway_survey_import.sql'):
        print("📋 Importing survey database data...")
        try:
            with sqlite3.connect('survey_normalized.db') as conn:
                with open('railway_survey_import.sql', 'r') as f:
                    sql_content = f.read()
                    statements = sql_content.split(';')
                    for statement in statements:
                        statement = statement.strip()
                        if statement and not statement.startswith('--'):
                            try:
                                conn.execute(statement)
                            except Exception as e:
                                if 'already exists' not in str(e):
                                    print(f"   ⚠️ SQL error: {e}")
                conn.commit()
            print("   ✅ Survey database import completed")
        except Exception as e:
            print(f"   ❌ Error importing survey database: {e}")
    
    # Verify import
    print("🔍 Verifying import...")
    try:
        with sqlite3.connect('surveyor_data_improved.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM spreadsheets')
            spreadsheet_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM raw_data')
            row_count = cursor.fetchone()[0]
            print(f"   ✅ Spreadsheets: {spreadsheet_count}")
            print(f"   ✅ Data rows: {row_count}")
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
    
    print("🎉 Data import completed!")

if __name__ == '__main__':
    import_data()
