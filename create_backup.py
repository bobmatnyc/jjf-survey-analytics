#!/usr/bin/env python3
"""
Create a backup of the current Railway database data.
This script downloads the current data and saves it as data_backup.json
"""

import requests
import json
import sys

def create_backup():
    """Download current data from Railway and save as backup."""
    try:
        print("📥 Downloading current data from Railway...")
        
        # Get current data from Railway
        response = requests.get("https://jjf-survey-analytics-production.up.railway.app/backup-data")
        
        if response.status_code == 200:
            backup_data = response.json()
            
            # Save to data_backup.json
            with open('data_backup.json', 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup created successfully!")
            print(f"📊 Backed up:")
            print(f"   - {len(backup_data.get('spreadsheets', []))} spreadsheets")
            print(f"   - {len(backup_data.get('raw_data', []))} data rows")
            print(f"   - {len(backup_data.get('extraction_jobs', []))} extraction jobs")
            print(f"💾 Saved to: data_backup.json")
            
            return True
        else:
            print(f"❌ Failed to get backup data: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

if __name__ == "__main__":
    success = create_backup()
    sys.exit(0 if success else 1)
