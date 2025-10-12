#!/usr/bin/env python3
"""View summary of all extracted tabs."""

import sqlite3
import json

def main():
    conn = sqlite3.connect('simple_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tab_name, COUNT(*) as row_count
        FROM tab_data
        GROUP BY tab_name
        ORDER BY tab_name
    """)
    
    print("\n" + "="*80)
    print("TAB EXTRACTION SUMMARY")
    print("="*80)
    
    for tab_name, row_count in cursor.fetchall():
        print(f"\n[{tab_name}] - {row_count} rows")
        
        # Get first row to show column structure
        cursor.execute("""
            SELECT data_json FROM tab_data
            WHERE tab_name = ?
            LIMIT 1
        """, (tab_name,))
        
        row = cursor.fetchone()
        if row:
            data = json.loads(row[0])
            print(f"  Columns ({len(data)}):")
            for col in list(data.keys())[:5]:  # Show first 5 columns
                print(f"    - {col}")
            if len(data) > 5:
                print(f"    ... and {len(data) - 5} more columns")
    
    print("\n" + "="*80)
    conn.close()

if __name__ == "__main__":
    main()
