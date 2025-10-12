# Sheet Mapping Analysis - Final Results

## Executive Summary

Successfully mapped 7 Google Sheets tabs from GIDs to meaningful names by analyzing:
- Column headers and data structure
- Question ID patterns (C-*, TL-*, S-*)
- Content and response data
- Question bank cross-references

**Key Finding:** All 5 expected sheets (Intake, CEO, Tech, Staff, Key) identified, plus 2 additional sheets (Summary, Questions).

---

## Final TABS Dictionary

```python
TABS = {
    "Intake": 1366958616,      # Initial participation survey (28 responses)
    "CEO": 1242252865,         # CEO assessment + contacts (3 responses)
    "Tech": 1545410106,        # Tech Lead survey (2 responses)
    "Staff": 377168987,        # Staff survey (4 responses)
    "Questions": 513349220,    # Question bank (67 questions)
    "Key": 1000323612,         # Organization reference (6 entries)
}

# Note: Summary sheet (GID 0) can be excluded or processed separately
```

---

## Mapping Evidence Table

| GID | Tab Name | Actual Name | Evidence |
|-----|----------|-------------|----------|
| 0 | Summary | **Summary** | Contains "OVERALL SUMMARY" text, dashboard data |
| 1366958616 | Tab_1366958616 | **Intake** | AI usage questions, participation readiness, 28 responses |
| 1242252865 | Tab_1242252865 | **CEO** | CEO/Tech Lead/Staff contact fields, C-* questions |
| 1545410106 | Tab_1545410106 | **Tech** | TL-* question IDs, infrastructure focus |
| 377168987 | Tab_377168987 | **Staff** | S-* question IDs, employee perspective |
| 513349220 | Tab_513349220 | **Questions** | Question ID/text/answers structure |
| 1000323612 | Tab_1000323612 | **Key** | Name/URL lookup table |

---

## Question ID Patterns

### CEO Survey (C-*) - 25 Questions
- **C-PT** (3): Performance Tracking
- **C-BS** (4): Business Systems  
- **C-D** (2): Data Management
- **C-I** (5): Infrastructure
- **C-OC** (8): Organizational Capacity
- **C-TC, C-TIP, C-FC**: Challenges, Priorities, Comments

### Tech Lead Survey (TL-*) - 19 Questions
- **TL-I** (14): Infrastructure (onboarding, security, updates, policies)
- **TL-OC** (4): Organizational Capacity (strategy, investment, change)
- **TL-CTC, TLC-TIP, TL-FC**: Challenges, Priorities, Comments

### Staff Survey (S-*) - 22 Questions
- **S-PT** (3): Performance Tracking
- **S-BS** (4): Business Systems
- **S-D** (3): Data Management
- **S-I** (7): Infrastructure (access, support, policies)
- **S-OC** (2): Organizational Capacity
- **S-CTC, S-TIP, S-FC**: Challenges, Priorities, Comments

---

## Data Quality Insights

### Response Distribution
```
Intake:    28 responses  ⭐ Highest engagement
CEO:        3 responses  ⚠️  Low follow-through (10.7%)
Tech:       2 responses  ⚠️  Low follow-through (7.1%)
Staff:      4 responses  ⚠️  Low follow-through (14.3%)
```

### Conversion Funnel
```
28 Intake → 3 CEO (10.7%)
         → 2 Tech (7.1%)
         → 4 Staff (14.3%)
```

**Insight:** High initial interest but low completion of detailed assessments.

---

## Sheet Relationships

### Contact Collection (CEO Sheet)
The CEO sheet serves dual purpose:
1. CEO assessment (C-* questions)
2. Contact collection for:
   - CEO (Organization, Email, Role)
   - Tech Lead (First/Last/Email/Role)
   - Staff 1-5 (First/Last/Email/Role)

### Question Reference Flow
```
Questions Bank (67 total)
├── C-* (25) → CEO Sheet responses
├── TL-* (19) → Tech Sheet responses
└── S-* (22) → Staff Sheet responses
```

### Organizational Lookup
```
Key Sheet → Name/URL mapping for organizations
         → Used across all survey sheets
```

---

## Category Analysis

### Shared Question Categories
All three surveys (CEO, Tech, Staff) assess:
- **Performance Tracking (PT)**: Technology in program delivery, AI usage
- **Business Systems (BS)**: Fundraising, finance, HR systems
- **Data Management (D)**: Data collection and analytics
- **Infrastructure (I)**: Security, policies, support, hardware
- **Organizational Capacity (OC)**: Strategy, investment, change management

### Role-Specific Focus

**CEO Questions:**
- Strategic/organizational perspective
- Leadership and planning
- Risk management and compliance
- More questions on organizational capacity (8 vs 4/2)

**Tech Lead Questions:**
- Technical implementation details
- Infrastructure management (14 questions)
- Policies and procedures
- System administration

**Staff Questions:**
- User experience perspective
- Day-to-day operational needs
- Access and support satisfaction
- More questions on data tools and infrastructure

---

## Sample Questions by Role

### CEO Strategic Questions
```
C-OC-2: Which of the following best describes how technology is discussed 
        by your organization's leadership team?

C-OC-4: Which of the following best describes how you use technology strategy 
        in organizational planning?

C-I-2:  Which of the following best describes your current cybersecurity 
        policies and protections?
```

### Tech Lead Implementation Questions
```
TL-I-1:  Which of the following best describes your process for on-boarding 
         and off-boarding staff with technology?

TL-I-10: Which of the following best describes how software and system updates 
         are managed across your organization?

TL-OC-1: Which of the following best describes your technology strategy?
```

### Staff Experience Questions
```
S-I-1:   Which of the following best describes your experience with technology 
         access on day one at your organization?

S-I-5:   Which of the following best describes your experience with technology 
         support?

S-BS-1:  Which of the following best describes your ability to access financial 
         data relevant to your work responsibilities?
```

---

## Implementation Notes

### Processing Order
1. **Key** - Load first for organizational reference
2. **Questions** - Load for question text mapping
3. **Intake** - Process initial surveys
4. **CEO** - Extract contacts and CEO assessments
5. **Tech** - Process Tech Lead surveys
6. **Staff** - Process Staff surveys
7. **Summary** - Skip or process separately (dashboard data)

### Database Schema Considerations
- Intake sheet has different structure (no question IDs)
- CEO sheet needs contact extraction logic
- Tech/Staff sheets use question ID references
- Questions sheet is reference table, not responses

### Normalization Strategy
```python
# Pseudo-code for processing
if sheet == "Intake":
    # Handle as standalone survey (no question IDs)
    process_intake_responses()
elif sheet in ["CEO", "Tech", "Staff"]:
    # Map question IDs to question text from Questions sheet
    responses = extract_responses_with_question_mapping()
elif sheet == "Questions":
    # Load as reference table
    load_question_bank()
elif sheet == "Key":
    # Load as lookup table
    load_organization_key()
```

---

## Next Steps

1. ✅ **Update simple_extractor.py**
   - Replace TABS dictionary with new mappings
   - Update any tab name references

2. ⏳ **Test Extraction**
   - Run extractor with new names
   - Verify all 6 tabs extracted correctly
   - Check data integrity

3. ⏳ **Update Normalization**
   - Handle Intake sheet separately (no question IDs)
   - Implement contact extraction from CEO sheet
   - Map question IDs to question text

4. ⏳ **Consider Summary Sheet**
   - Decide if it should be extracted
   - May be auto-generated from other data
   - Could be excluded from extraction

5. ⏳ **Documentation**
   - Update README with new sheet names
   - Document question categories
   - Add data flow diagrams

---

## Analysis Methodology

**Tools Used:**
- SQLite queries on `simple_data.db`
- JSON data inspection
- Pattern matching on question IDs
- Cross-reference validation

**Key Steps:**
1. Examined database schema and structure
2. Analyzed column headers for each tab
3. Identified question ID patterns (C-*, TL-*, S-*)
4. Cross-referenced with Questions bank
5. Validated mappings across all sheets
6. Documented evidence for each mapping

**Files Generated:**
- `SHEET_MAPPING_ANALYSIS.md` - Detailed analysis
- `MAPPING_RESULTS.md` - This summary
- Console output with visual summary

---

*Analysis Date: 2025-10-11*  
*Database: simple_data.db*  
*Total Sheets Analyzed: 7*  
*Total Questions Cataloged: 67*
