#!/usr/bin/env python3
"""
Direct Import to Railway PostgreSQL

This script extracts data from Google Sheets and imports directly to PostgreSQL.
Designed to run on Railway where DATABASE_URL is available.

Usage:
  # On Railway via curl
  curl https://your-app.railway.app/api/import-google-sheets-to-postgres

  # Or deploy this and trigger via Railway shell
  railway shell
  python import_to_railway_postgres.py
"""

import os
import sys

def main():
    """Run extraction and import to PostgreSQL."""

    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set. This script must run on Railway.")
        print("   Set up Railway deployment first.")
        sys.exit(1)

    print("🚀 Google Sheets → PostgreSQL Import")
    print("=" * 50)

    # Step 1: Extract data from Google Sheets
    print("\n📥 Step 1: Extracting data from Google Sheets...")
    try:
        from improved_extractor import ImprovedExtractor
        extractor = ImprovedExtractor()

        # Run extraction to SQLite first
        print("   Running extraction...")
        os.system('python improved_extractor.py')
        print("   ✅ Extraction complete")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

    # Step 2: Normalize to SQLite
    print("\n🔄 Step 2: Normalizing data...")
    try:
        print("   Running normalization...")
        os.system('python survey_normalizer.py --auto')
        print("   ✅ Normalization complete")
    except Exception as e:
        print(f"   ❌ Normalization failed: {e}")
        import traceback
        traceback.print_exc()

    # Step 3: Import SQLite data to PostgreSQL
    print("\n🐘 Step 3: Importing to PostgreSQL...")
    try:
        os.system('python migrate_sqlite_to_postgres.py')
        print("   ✅ Import to PostgreSQL complete")
    except Exception as e:
        print(f"   ❌ PostgreSQL import failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n🎉 Import process completed!")
    print("   Check your Railway dashboard to verify the data")

if __name__ == '__main__':
    main()
