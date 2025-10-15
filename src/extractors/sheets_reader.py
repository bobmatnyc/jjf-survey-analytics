#!/usr/bin/env python3
"""
Google Sheets Direct Reader
Reads data directly from Google Sheets into memory without database.
"""

import csv
import urllib.request
import io
from typing import List, Dict, Any
from datetime import datetime


class SheetsReader:
    """Direct Google Sheets reader for in-memory storage."""

    # Single spreadsheet ID for JJF Technology Assessment
    SPREADSHEET_ID = "15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU"

    # Tab configuration with GIDs
    TABS = {
        "Summary": "0",              # Summary/overview tab
        "Intake": "1366958616",      # Initial participation survey (28 responses)
        "CEO": "1242252865",         # CEO assessment + contacts (3 responses, C-* question IDs)
        "Tech": "1545410106",        # Tech Lead survey (2 responses, TL-* question IDs)
        "Staff": "377168987",        # Staff survey (4 responses, S-* question IDs)
        "Questions": "513349220",    # Question bank with IDs and answer options (67 questions)
        "Key": "1000323612",         # Organization reference lookup table (6 entries)
        "OrgMaster": "601687640",    # Master list of all organizations reached out to
    }

    @staticmethod
    def get_csv_export_url(gid: str) -> str:
        """Get CSV export URL for a specific tab."""
        return f"https://docs.google.com/spreadsheets/d/{SheetsReader.SPREADSHEET_ID}/export?format=csv&gid={gid}"

    @staticmethod
    def download_tab_data(tab_name: str, gid: str, verbose: bool = False) -> List[Dict[str, Any]]:
        """Download data from a specific tab."""
        try:
            csv_url = SheetsReader.get_csv_export_url(gid)
            if verbose:
                print(f"  Downloading {tab_name} from GID {gid}...")

            # Create request with headers
            req = urllib.request.Request(csv_url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=30) as response:
                csv_data = response.read().decode('utf-8')

            # Parse CSV
            if csv_data.strip() and not csv_data.startswith('<!DOCTYPE'):
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                data = list(csv_reader)
                if verbose:
                    print(f"  ✓ Downloaded {len(data)} rows from {tab_name}")
                return data
            else:
                if verbose:
                    print(f"  ✗ Invalid data received for {tab_name}")
                return []

        except Exception as e:
            if verbose:
                print(f"  ✗ Error downloading {tab_name}: {e}")
            return []

    @classmethod
    def fetch_all_tabs(cls, verbose: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch data from all tabs and return as dictionary.

        Returns:
            {
                'Summary': [rows...],
                'Intake': [rows...],
                'CEO': [rows...],
                ...
                '_metadata': {
                    'last_fetch': timestamp,
                    'total_rows': count,
                    'tabs_count': count
                }
            }
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Google Sheets Direct Reader")
            print(f"{'='*60}")
            print(f"Spreadsheet ID: {cls.SPREADSHEET_ID}")
            print(f"Tabs: {', '.join(cls.TABS.keys())}")
            print(f"{'='*60}\n")

        sheet_data = {}
        total_rows = 0
        successful_tabs = 0

        for tab_name, gid in cls.TABS.items():
            if verbose:
                print(f"[{tab_name}]")

            data = cls.download_tab_data(tab_name, gid, verbose)
            sheet_data[tab_name] = data

            if data:
                total_rows += len(data)
                successful_tabs += 1

        # Add metadata
        sheet_data['_metadata'] = {
            'last_fetch': datetime.now().isoformat(),
            'total_rows': total_rows,
            'tabs_count': successful_tabs,
            'spreadsheet_id': cls.SPREADSHEET_ID
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"Fetch Complete")
            print(f"{'='*60}")
            print(f"✓ Successfully fetched {successful_tabs}/{len(cls.TABS)} tabs")
            print(f"✓ Total rows: {total_rows}")
            print(f"{'='*60}\n")

        return sheet_data


def main():
    """Main function to test reader."""
    data = SheetsReader.fetch_all_tabs(verbose=True)

    print("\nData Summary:")
    for tab_name in SheetsReader.TABS.keys():
        row_count = len(data.get(tab_name, []))
        print(f"  - {tab_name}: {row_count} rows")

    print(f"\nMetadata:")
    metadata = data.get('_metadata', {})
    for key, value in metadata.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
