#!/usr/bin/env python3
"""
Simple Google Sheets Data Extractor
Extracts data from JJF Technology Assessment spreadsheet with 7 tabs:
  - Summary: Overview/summary tab
  - Intake: Initial participation survey (28 responses)
  - CEO: CEO assessment + contacts (3 responses, C-* question IDs)
  - Tech: Tech Lead survey (2 responses, TL-* question IDs)
  - Staff: Staff survey (4 responses, S-* question IDs)
  - Questions: Master question bank (67 questions with IDs and options)
  - Key: Organization reference lookup table (6 entries)
"""

import sqlite3
import csv
import urllib.request
import json
from datetime import datetime
from typing import List, Dict, Any
import os


class SimpleExtractor:
    """Simple data extractor for a single Google Sheet with 7 tabs."""

    # Single spreadsheet ID for JJF Technology Assessment
    SPREADSHEET_ID = "15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU"

    # Tab configuration with GIDs - Inferred names from data analysis
    TABS = {
        "Summary": "0",              # Summary/overview tab
        "Intake": "1366958616",      # Initial participation survey (28 responses)
        "CEO": "1242252865",         # CEO assessment + contacts (3 responses, C-* question IDs)
        "Tech": "1545410106",        # Tech Lead survey (2 responses, TL-* question IDs)
        "Staff": "377168987",        # Staff survey (4 responses, S-* question IDs)
        "Questions": "513349220",    # Question bank with IDs and answer options (67 questions)
        "Key": "1000323612",         # Organization reference lookup table (6 entries)
    }

    def __init__(self, db_path: str = "simple_data.db"):
        self.db_path = db_path
    
    def get_csv_export_url(self, gid: str) -> str:
        """Get CSV export URL for a specific tab."""
        return f"https://docs.google.com/spreadsheets/d/{self.SPREADSHEET_ID}/export?format=csv&gid={gid}"

    def download_tab_data(self, tab_name: str, gid: str) -> List[Dict[str, Any]]:
        """Download data from a specific tab."""
        try:
            csv_url = self.get_csv_export_url(gid)
            print(f"  Downloading from GID {gid}...")

            # Create request with headers
            req = urllib.request.Request(csv_url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=30) as response:
                csv_data = response.read().decode('utf-8')

            # Parse CSV
            if csv_data.strip() and not csv_data.startswith('<!DOCTYPE'):
                import io
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                data = list(csv_reader)
                print(f"  ✓ Downloaded {len(data)} rows from {tab_name}")
                return data
            else:
                print(f"  ✗ Invalid data received for {tab_name}")
                return []

        except Exception as e:
            print(f"  ✗ Error downloading {tab_name}: {e}")
            return []
    
    def create_database(self):
        """Create SQLite database with simple schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Single table for all tab data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tab_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tab_name TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tab_name ON tab_data(tab_name)')

        conn.commit()
        conn.close()
        print(f"✓ Database created: {self.db_path}")

    def clear_tab_data(self, tab_name: str):
        """Clear existing data for a tab."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tab_data WHERE tab_name = ?', (tab_name,))
        conn.commit()
        conn.close()

    def save_tab_data(self, tab_name: str, data: List[Dict[str, Any]]):
        """Save tab data to database."""
        if not data:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clear existing data for this tab
        self.clear_tab_data(tab_name)

        # Insert new data
        for i, row in enumerate(data, 1):
            data_str = json.dumps(row)
            cursor.execute('''
                INSERT INTO tab_data (tab_name, row_index, data_json)
                VALUES (?, ?, ?)
            ''', (tab_name, i, data_str))

        conn.commit()
        conn.close()
        print(f"  ✓ Saved {len(data)} rows to database")

    def extract_all_tabs(self):
        """Extract data from all tabs."""
        print(f"\n{'='*60}")
        print(f"Simple Google Sheets Data Extractor")
        print(f"{'='*60}")
        print(f"Spreadsheet ID: {self.SPREADSHEET_ID}")
        print(f"Tabs: {', '.join(self.TABS.keys())}")
        print(f"{'='*60}\n")

        # Create database
        self.create_database()

        # Extract each tab
        total_rows = 0
        successful_tabs = 0

        for tab_name, gid in self.TABS.items():
            print(f"\n[{tab_name}]")
            data = self.download_tab_data(tab_name, gid)

            if data:
                self.save_tab_data(tab_name, data)
                total_rows += len(data)
                successful_tabs += 1

        print(f"\n{'='*60}")
        print(f"Extraction Complete")
        print(f"{'='*60}")
        print(f"✓ Successfully extracted {successful_tabs}/{len(self.TABS)} tabs")
        print(f"✓ Total rows: {total_rows}")
        print(f"✓ Database: {self.db_path}")
        print(f"{'='*60}\n")

    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        if not os.path.exists(self.db_path):
            return {"error": "Database not found"}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get stats for each tab
        cursor.execute('''
            SELECT tab_name, COUNT(*) as row_count, MAX(extracted_at) as last_extract
            FROM tab_data
            GROUP BY tab_name
            ORDER BY tab_name
        ''')

        tabs_stats = []
        for row in cursor.fetchall():
            tabs_stats.append({
                "tab_name": row[0],
                "row_count": row[1],
                "last_extract": row[2]
            })

        # Get total rows
        cursor.execute('SELECT COUNT(*) FROM tab_data')
        total_rows = cursor.fetchone()[0]

        conn.close()

        return {
            "tabs": tabs_stats,
            "total_rows": total_rows,
            "database": self.db_path
        }


def main():
    """Main function to run extraction."""
    extractor = SimpleExtractor()

    try:
        extractor.extract_all_tabs()

        # Show stats
        stats = extractor.get_stats()
        if "error" not in stats:
            print("\nDatabase Statistics:")
            print(f"Total rows: {stats['total_rows']}")
            for tab in stats['tabs']:
                print(f"  - {tab['tab_name']}: {tab['row_count']} rows")

    except KeyboardInterrupt:
        print("\n\n⚠ Extraction cancelled by user")
    except Exception as e:
        print(f"\n\n✗ Extraction failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
