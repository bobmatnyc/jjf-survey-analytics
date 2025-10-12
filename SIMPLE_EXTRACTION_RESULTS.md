# Simple Extraction Results

**Extraction Date:** 2025-10-11
**Spreadsheet ID:** 15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU
**Database:** simple_data.db

## Summary Statistics

- **Total Tabs Extracted:** 7/7 (100% success)
- **Total Rows:** 123
- **Extraction Method:** Direct CSV export from Google Sheets

## Tab Breakdown

### 1. Summary (GID: 0)
- **Rows:** 13
- **Columns:** 2
- **Content:** Overall summary data
- **Key Columns:** OVERALL SUMMARY

### 2. Tab_1366958616
- **Rows:** 28
- **Columns:** 18
- **Content:** Survey responses with contact information
- **Key Columns:** Reference #, Status, Name, Email, Role, Organization Name, AI usage questions
- **Sample:** Rachel Zieleniec from "R&R: The Rest of Our Lives"

### 3. Tab_1242252865
- **Rows:** 3
- **Columns:** 65
- **Content:** Detailed survey responses (CEO/Organization level)
- **Key Columns:** Reference #, Status, Login Email, Name, CEO Organization

### 4. Tab_1545410106
- **Rows:** 2
- **Columns:** 33
- **Content:** Survey responses with organization data
- **Key Columns:** Reference #, Status, Name, Organization, Date

### 5. Tab_377168987
- **Rows:** 4
- **Columns:** 35
- **Content:** Survey responses with organization data
- **Key Columns:** Reference #, Status, Name, Organization

### 6. Tab_513349220 (LARGEST)
- **Rows:** 67
- **Columns:** 9
- **Content:** Question bank with multiple choice answers
- **Key Columns:** Question ID, QUESTION, Answer 1-7
- **Sample Question:** "Which of the following best describes how technology is utilized in program delivery?"
- **Question IDs:** Format like "C-PT-1"

### 7. Tab_1000323612
- **Rows:** 6
- **Columns:** 3
- **Content:** Reference list (likely URLs or resources)
- **Key Columns:** Name, URL

## Data Patterns Identified

1. **Survey Response Tabs** (1366958616, 1242252865, 1545410106, 377168987)
   - All contain Reference #, Status, Name fields
   - Include timestamps (Date, Start Time, Finish Time, Duration)
   - Capture respondent information (Email, Organization)
   - Vary in question count (18 to 65 columns)

2. **Question Bank** (513349220)
   - Structured question definitions
   - Multiple choice format (up to 7 answer options)
   - Question IDs for reference
   - 67 questions total

3. **Metadata Tabs** (Summary, 1000323612)
   - Summary statistics or overview
   - Reference/resource lists

## Next Steps

1. **Identify Tab Names:** Replace placeholder names with actual sheet names from Google Sheets
2. **Map Relationships:** Link questions in Tab_513349220 to answers in response tabs
3. **Normalize Data:** Create relational structure connecting questions, responses, and respondents
4. **Analyze Patterns:** Identify which surveys use which questions

## Database Access

```bash
# View all tabs
sqlite3 simple_data.db "SELECT tab_name, COUNT(*) FROM tab_data GROUP BY tab_name;"

# Query specific tab
sqlite3 simple_data.db "SELECT data_json FROM tab_data WHERE tab_name = 'Tab_1366958616';"

# Export tab to JSON
sqlite3 simple_data.db "SELECT data_json FROM tab_data WHERE tab_name = 'Tab_513349220';" > questions.jsonl
```

