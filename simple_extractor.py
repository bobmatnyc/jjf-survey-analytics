#!/usr/bin/env python3
"""
Simple Google Sheets Data Extractor

A simplified version that extracts data from the Google Sheets URLs
and creates a SQLite database without complex dependencies.
"""

import sqlite3
import csv
import urllib.request
import urllib.parse
import re
import json
import os
from datetime import datetime
from typing import List, Dict, Any


class SimpleExtractor:
    """Simple data extractor for Google Sheets."""
    
    def __init__(self, db_path: str = "surveyor_data.db"):
        self.db_path = db_path
        self.sheet_urls = [
            "https://docs.google.com/spreadsheets/d/1fAAXXGOiDWc8lMVaRwqvuM2CDNAyNY_Px3usyisGhaw/edit?gid=365352546#gid=365352546",
            "https://docs.google.com/spreadsheets/d/1qEHKDVIO4YTR3TjMt336HdKLIBMV2cebAcvdbGOUdCU/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1-aw7gjjvRMQj89lstVBtKDZ67Cs-dO1SHNsp4scJ4II/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1f3NKqhNR-CJr_e6_eLSTLbSFuYY8Gm0dxpSL0mlybMA/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1mQxcZ9U1UsVmHstgWdbHuT7bqfVXV4ZNCr9pn0TlVWM/edit?usp=sharing",
            "https://docs.google.com/spreadsheets/d/1h9AooI-E70v36EOxuErh4uYBg2TLbsF7X5kXdkrUkoQ/edit?usp=sharing"
        ]
    
    def extract_spreadsheet_id(self, url: str) -> str:
        """Extract spreadsheet ID from Google Sheets URL."""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError(f"Invalid Google Sheets URL: {url}")
        return match.group(1)
    
    def get_csv_export_url(self, spreadsheet_id: str, gid: str = "0") -> str:
        """Get CSV export URL for a Google Sheet."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    
    def extract_gid_from_url(self, url: str) -> str:
        """Extract GID from Google Sheets URL."""
        gid_match = re.search(r'[#&]gid=([0-9]+)', url)
        return gid_match.group(1) if gid_match else "0"
    
    def download_sheet_data(self, url: str) -> List[Dict[str, Any]]:
        """Download data from a Google Sheet as CSV."""
        try:
            spreadsheet_id = self.extract_spreadsheet_id(url)
            gid = self.extract_gid_from_url(url)
            csv_url = self.get_csv_export_url(spreadsheet_id, gid)
            
            print(f"📥 Downloading data from spreadsheet {spreadsheet_id} (gid: {gid})")
            
            # Download CSV data
            with urllib.request.urlopen(csv_url) as response:
                csv_data = response.read().decode('utf-8')
            
            # Parse CSV
            lines = csv_data.strip().split('\n')
            if not lines:
                print(f"⚠️  No data found in spreadsheet {spreadsheet_id}")
                return []
            
            # Use CSV reader to handle quoted fields properly
            import io
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            data = list(csv_reader)
            
            print(f"✅ Downloaded {len(data)} rows from spreadsheet {spreadsheet_id}")
            return data
            
        except Exception as e:
            print(f"❌ Error downloading data from {url}: {e}")
            return []
    
    def create_database(self):
        """Create SQLite database with normalized schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spreadsheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spreadsheet_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_synced TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spreadsheet_id TEXT NOT NULL,
                row_number INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spreadsheet_id) REFERENCES spreadsheets (spreadsheet_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                total_spreadsheets INTEGER DEFAULT 0,
                processed_spreadsheets INTEGER DEFAULT 0,
                total_rows INTEGER DEFAULT 0,
                processed_rows INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_data_spreadsheet ON raw_data(spreadsheet_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spreadsheets_id ON spreadsheets(spreadsheet_id)')
        
        conn.commit()
        conn.close()
        print(f"✅ Database created: {self.db_path}")
    
    def save_spreadsheet_info(self, spreadsheet_id: str, url: str, title: str = None):
        """Save spreadsheet information to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO spreadsheets (spreadsheet_id, url, title, last_synced)
            VALUES (?, ?, ?, ?)
        ''', (spreadsheet_id, url, title or f"Spreadsheet_{spreadsheet_id}", datetime.now()))
        
        conn.commit()
        conn.close()
    
    def save_raw_data(self, spreadsheet_id: str, data: List[Dict[str, Any]]):
        """Save raw data to database."""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data for this spreadsheet
        cursor.execute('DELETE FROM raw_data WHERE spreadsheet_id = ?', (spreadsheet_id,))
        
        # Insert new data
        for i, row in enumerate(data, 1):
            cursor.execute('''
                INSERT INTO raw_data (spreadsheet_id, row_number, data_json)
                VALUES (?, ?, ?)
            ''', (spreadsheet_id, i, json.dumps(row)))
        
        conn.commit()
        conn.close()
        print(f"💾 Saved {len(data)} rows for spreadsheet {spreadsheet_id}")
    
    def create_extraction_job(self, job_name: str) -> int:
        """Create a new extraction job and return its ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO extraction_jobs (job_name, total_spreadsheets)
            VALUES (?, ?)
        ''', (job_name, len(self.sheet_urls)))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def update_extraction_job(self, job_id: int, **kwargs):
        """Update extraction job progress."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        if set_clauses:
            values.append(job_id)
            cursor.execute(f'''
                UPDATE extraction_jobs 
                SET {", ".join(set_clauses)}
                WHERE id = ?
            ''', values)
        
        conn.commit()
        conn.close()
    
    def extract_all_data(self):
        """Extract data from all configured spreadsheets."""
        print("🚀 Starting data extraction...")
        
        # Create database
        self.create_database()
        
        # Create extraction job
        job_name = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_id = self.create_extraction_job(job_name)
        
        total_rows = 0
        processed_spreadsheets = 0
        
        try:
            for i, url in enumerate(self.sheet_urls, 1):
                print(f"\n📊 Processing spreadsheet {i}/{len(self.sheet_urls)}")
                print(f"🔗 URL: {url}")
                
                try:
                    # Extract data
                    data = self.download_sheet_data(url)
                    
                    if data:
                        spreadsheet_id = self.extract_spreadsheet_id(url)
                        
                        # Save spreadsheet info
                        self.save_spreadsheet_info(spreadsheet_id, url)
                        
                        # Save raw data
                        self.save_raw_data(spreadsheet_id, data)
                        
                        total_rows += len(data)
                        processed_spreadsheets += 1
                        
                        # Update job progress
                        self.update_extraction_job(
                            job_id,
                            processed_spreadsheets=processed_spreadsheets,
                            total_rows=total_rows,
                            processed_rows=total_rows
                        )
                    
                except Exception as e:
                    print(f"❌ Error processing spreadsheet {i}: {e}")
                    continue
            
            # Mark job as completed
            self.update_extraction_job(
                job_id,
                status='completed',
                completed_at=datetime.now(),
                processed_spreadsheets=processed_spreadsheets,
                total_rows=total_rows,
                processed_rows=total_rows
            )
            
            print(f"\n✅ Extraction completed successfully!")
            print(f"📈 Job ID: {job_id}")
            print(f"📊 Processed {processed_spreadsheets}/{len(self.sheet_urls)} spreadsheets")
            print(f"📝 Total rows extracted: {total_rows}")
            print(f"💾 Database: {self.db_path}")
            
        except Exception as e:
            # Mark job as failed
            self.update_extraction_job(
                job_id,
                status='failed',
                completed_at=datetime.now(),
                error_message=str(e)
            )
            print(f"❌ Extraction failed: {e}")
            raise
    
    def show_database_info(self):
        """Show information about the database contents."""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 Database Information: {self.db_path}")
        print("=" * 50)
        
        # Show spreadsheets
        cursor.execute('SELECT COUNT(*) FROM spreadsheets')
        spreadsheet_count = cursor.fetchone()[0]
        print(f"📋 Spreadsheets: {spreadsheet_count}")
        
        # Show raw data
        cursor.execute('SELECT COUNT(*) FROM raw_data')
        row_count = cursor.fetchone()[0]
        print(f"📝 Total rows: {row_count}")
        
        # Show extraction jobs
        cursor.execute('SELECT COUNT(*) FROM extraction_jobs')
        job_count = cursor.fetchone()[0]
        print(f"🔄 Extraction jobs: {job_count}")
        
        # Show recent jobs
        cursor.execute('''
            SELECT id, job_name, status, processed_spreadsheets, total_rows, started_at
            FROM extraction_jobs
            ORDER BY started_at DESC
            LIMIT 5
        ''')
        
        jobs = cursor.fetchall()
        if jobs:
            print(f"\n📋 Recent extraction jobs:")
            for job in jobs:
                job_id, name, status, processed, total, started = job
                print(f"  • Job {job_id}: {name} - {status} ({processed} sheets, {total} rows) - {started}")
        
        # Show spreadsheet details
        cursor.execute('''
            SELECT s.spreadsheet_id, s.title, COUNT(r.id) as row_count, s.last_synced
            FROM spreadsheets s
            LEFT JOIN raw_data r ON s.spreadsheet_id = r.spreadsheet_id
            GROUP BY s.spreadsheet_id, s.title, s.last_synced
            ORDER BY s.last_synced DESC
        ''')
        
        spreadsheets = cursor.fetchall()
        if spreadsheets:
            print(f"\n📊 Spreadsheet details:")
            for sheet in spreadsheets:
                sheet_id, title, rows, synced = sheet
                print(f"  • {sheet_id}: {title} ({rows} rows) - Last synced: {synced}")
        
        conn.close()


def main():
    """Main function to run the data extraction."""
    print("🔍 Simple Google Sheets Data Extractor")
    print("=" * 40)
    
    extractor = SimpleExtractor()
    
    try:
        # Extract all data
        extractor.extract_all_data()
        
        # Show database info
        extractor.show_database_info()
        
    except KeyboardInterrupt:
        print("\n⚠️  Extraction cancelled by user")
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
