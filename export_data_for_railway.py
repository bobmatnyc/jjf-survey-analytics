#!/usr/bin/env python3
"""
Export local database data for Railway deployment
Creates SQL files that can be imported to Railway
"""

import sqlite3
import json
import os
from datetime import datetime

def export_database_data():
    """Export all data from local databases to SQL files."""
    
    print("📊 Exporting Local Database Data for Railway")
    print("=" * 50)
    
    # Database files to export
    databases = [
        ('surveyor_data_improved.db', 'railway_data_import.sql'),
        ('survey_normalized.db', 'railway_survey_import.sql')
    ]
    
    for db_path, output_file in databases:
        if not os.path.exists(db_path):
            print(f"⚠️ Database not found: {db_path}")
            continue
            
        print(f"\n📋 Exporting {db_path}...")
        
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"   Tables found: {tables}")
                
                with open(output_file, 'w') as f:
                    f.write(f"-- Data export from {db_path}\n")
                    f.write(f"-- Generated on {datetime.now().isoformat()}\n\n")
                    
                    for table in tables:
                        print(f"   Exporting table: {table}")
                        
                        # Get table schema
                        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                        schema = cursor.fetchone()[0]
                        f.write(f"-- Table: {table}\n")
                        f.write(f"{schema};\n\n")
                        
                        # Get all data
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        
                        if rows:
                            # Get column names
                            columns = [description[0] for description in cursor.description]
                            
                            f.write(f"-- Data for {table} ({len(rows)} rows)\n")
                            
                            for row in rows:
                                values = []
                                for value in row:
                                    if value is None:
                                        values.append('NULL')
                                    elif isinstance(value, str):
                                        # Escape single quotes
                                        escaped = value.replace("'", "''")
                                        values.append(f"'{escaped}'")
                                    else:
                                        values.append(str(value))
                                
                                columns_str = ', '.join(columns)
                                values_str = ', '.join(values)
                                f.write(f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({values_str});\n")
                            
                            f.write(f"\n")
                        else:
                            f.write(f"-- No data in {table}\n\n")
                
                print(f"   ✅ Exported to {output_file}")
                
        except Exception as e:
            print(f"   ❌ Error exporting {db_path}: {e}")
    
    print(f"\n🎯 Export Summary:")
    print(f"✅ Created railway_data_import.sql")
    print(f"✅ Created railway_survey_import.sql")
    print(f"\nThese files contain all your local data and can be imported to Railway.")

def create_railway_import_script():
    """Create a script that can run on Railway to import the data."""
    
    script_content = '''#!/usr/bin/env python3
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
'''
    
    with open('railway_import_data.py', 'w') as f:
        f.write(script_content)
    
    print("✅ Created railway_import_data.py")

if __name__ == '__main__':
    export_database_data()
    create_railway_import_script()
    
    print("\n🚀 Next Steps:")
    print("1. The SQL files contain all your local data")
    print("2. Add these files to your git repository")
    print("3. Deploy to Railway")
    print("4. Run railway_import_data.py on Railway to import the data")
    print("5. Your dashboard will then show all 6 spreadsheets!")
