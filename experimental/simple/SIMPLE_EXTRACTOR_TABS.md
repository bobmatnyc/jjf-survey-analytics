# Simple Extractor Tab Mapping

## Overview
This document details the tab names and purposes for the JJF Technology Assessment spreadsheet extracted by `simple_extractor.py`.

## Spreadsheet Information
- **Spreadsheet ID:** `15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU`
- **Database:** `simple_data.db`
- **Total Tabs:** 7
- **Total Records:** 123 rows

## Tab Mapping

| Tab Name | GID | Row Count | Purpose |
|----------|-----|-----------|---------|
| Summary | 0 | 13 | Overview/summary data |
| Intake | 1366958616 | 28 | Initial participation survey |
| CEO | 1242252865 | 3 | CEO assessment + contacts |
| Tech | 1545410106 | 2 | Tech Lead survey |
| Staff | 377168987 | 4 | Staff survey |
| Questions | 513349220 | 67 | Master question bank |
| Key | 1000323612 | 6 | Organization reference table |

## Tab Details

### Summary (GID: 0)
- **Purpose:** Overview and summary information
- **Records:** 13 rows
- **Type:** Summary data

### Intake (GID: 1366958616)
- **Purpose:** Initial participation survey
- **Records:** 28 responses (largest dataset)
- **Content:** General AI/technology usage questions
- **Note:** Foundation for the assessment process

### CEO (GID: 1242252865)
- **Purpose:** CEO assessment and organizational contacts
- **Records:** 3 responses
- **Question Pattern:** C-* question IDs
  - C-PT-* (Program Technology)
  - C-BS-* (Business Systems)
  - C-D-* (Data)
  - C-I-* (Infrastructure)
  - C-OC-* (Organizational Capacity)
  - C-TC (Technology Challenges)
  - C-TIP (Technology Investment Priorities)
  - C-FC (Free Comments)
- **Additional Data:**
  - CEO contact information
  - Tech Lead contacts
  - Staff member contacts (up to 5)

### Tech (GID: 1545410106)
- **Purpose:** Tech Lead survey
- **Records:** 2 responses
- **Question Pattern:** TL-* question IDs
  - TL-I-1 through TL-I-14 (Infrastructure questions)
  - TL-OC-* (Organizational Capacity)
  - TL-CTC (Current Tech Challenges)
  - TLC-TIP (Tech Investment Priorities)
  - TL-FC (Free Comments)
- **Focus:** Technical infrastructure and capabilities assessment

### Staff (GID: 377168987)
- **Purpose:** Staff technology survey
- **Records:** 4 responses
- **Question Pattern:** S-* question IDs
  - S-PT-* (Program Technology)
  - S-BS-* (Business Systems)
  - S-D-* (Data)
  - S-I-* (Infrastructure)
  - S-OC-* (Organizational Capacity)
  - S-CTC (Current Tech Challenges)
  - S-TIP (Tech Investment Priorities)
  - S-FC (Free Comments)
- **Focus:** Staff perspective on technology usage and operational assessment

### Questions (GID: 513349220)
- **Purpose:** Master question bank
- **Records:** 67 questions
- **Structure:**
  - Question ID (matches C-*, TL-*, S-* patterns)
  - QUESTION (full question text)
  - Answer 1-7 (answer option columns)
- **Use:** Reference for mapping question IDs to full text and available answers

### Key (GID: 1000323612)
- **Purpose:** Organization reference lookup table
- **Records:** 6 entries
- **Structure:**
  - Name (organization identifier)
  - URL (spreadsheet URL)
  - Spreadsheet ID
- **Use:** Maps organization names to their assessment spreadsheets

## Question ID Patterns

### CEO Questions (C-*)
- **C-PT:** Program Technology (how technology is used in program delivery)
- **C-BS:** Business Systems (HR, finance, etc.)
- **C-D:** Data (data management and analytics)
- **C-I:** Infrastructure (technical infrastructure)
- **C-OC:** Organizational Capacity (culture and readiness)
- **C-TC:** Technology Challenges (current obstacles)
- **C-TIP:** Technology Investment Priorities (future focus)
- **C-FC:** Free Comments (open-ended feedback)

### Tech Lead Questions (TL-*)
- **TL-I:** Infrastructure (14 infrastructure-focused questions)
- **TL-OC:** Organizational Capacity (technical culture)
- **TL-CTC:** Current Tech Challenges (specific technical obstacles)
- **TLC-TIP:** Tech Investment Priorities (technical priorities)
- **TL-FC:** Free Comments (technical feedback)

### Staff Questions (S-*)
- **S-PT:** Program Technology (operational perspective)
- **S-BS:** Business Systems (day-to-day tools)
- **S-D:** Data (data usage and quality)
- **S-I:** Infrastructure (infrastructure experience)
- **S-OC:** Organizational Capacity (staff tech culture)
- **S-CTC:** Current Tech Challenges (user-level obstacles)
- **S-TIP:** Tech Investment Priorities (staff needs)
- **S-FC:** Free Comments (staff feedback)

## Migration History

### Old Mapping (Placeholder Names)
```python
TABS = {
    'Summary': 0,
    'Tab_1366958616': 1366958616,
    'Tab_1242252865': 1242252865,
    'Tab_1545410106': 1545410106,
    'Tab_377168987': 377168987,
    'Tab_513349220': 513349220,
    'Tab_1000323612': 1000323612
}
```

### New Mapping (Inferred Names)
```python
TABS = {
    'Summary': '0',
    'Intake': '1366958616',
    'CEO': '1242252865',
    'Tech': '1545410106',
    'Staff': '377168987',
    'Questions': '513349220',
    'Key': '1000323612',
}
```

## Usage

### Extract All Tabs
```bash
python3 simple_extractor.py
```

### Query Specific Tab
```bash
sqlite3 simple_data.db "SELECT * FROM tab_data WHERE tab_name = 'CEO';"
```

### Get Tab Statistics
```bash
sqlite3 simple_data.db "SELECT tab_name, COUNT(*) FROM tab_data GROUP BY tab_name;"
```

### Export Tab to JSON
```python
import sqlite3
import json

conn = sqlite3.connect('simple_data.db')
cursor = conn.cursor()
cursor.execute("SELECT data_json FROM tab_data WHERE tab_name = 'CEO'")
for row in cursor.fetchall():
    print(json.loads(row[0]))
```

## Data Flow

```
Google Sheets
    ↓
simple_extractor.py (Extract with correct tab names)
    ↓
simple_data.db (SQLite with tab_data table)
    ↓
Analysis/Normalization Scripts
```

## Notes

1. **Tab Names:** Inferred from data analysis and question ID patterns
2. **GID Stability:** Google Sheets GIDs are stable identifiers
3. **Data Structure:** All tabs stored in single `tab_data` table with JSON column
4. **Timestamp:** Each row has `extracted_at` timestamp
5. **Idempotent:** Running extractor multiple times replaces data (not append)

## Last Updated
- **Date:** 2025-10-11
- **Version:** 1.0
- **Extraction Status:** ✓ All 7 tabs successfully extracted
