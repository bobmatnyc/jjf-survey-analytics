# Sheet Name Mapping Analysis

## Executive Summary

Successfully identified actual sheet names from the content in `simple_data.db` by analyzing column headers, question ID patterns, and data structure.

**7 sheets mapped to meaningful names:**
- 5 match user's expected sheets (Intake, CEO, Tech, Staff, Key)
- 2 additional sheets identified (Summary, Questions)

---

## Final Tab Mapping

### GID to Name Mapping

| GID | Tab Name | Actual Name | Rows | Description |
|-----|----------|-------------|------|-------------|
| 0 | Summary | **Summary** | 13 | Dashboard/overview tab |
| 1366958616 | Tab_1366958616 | **Intake** | 28 | Initial participation survey |
| 1242252865 | Tab_1242252865 | **CEO** | 3 | CEO assessment with contact collection |
| 1545410106 | Tab_1545410106 | **Tech** | 2 | Tech Lead survey (TL-* questions) |
| 377168987 | Tab_377168987 | **Staff** | 4 | Staff survey (S-* questions) |
| 513349220 | Tab_513349220 | **Questions** | 67 | Question bank reference |
| 1000323612 | Tab_1000323612 | **Key** | 6 | Organization/reference lookup |

---

## Identification Evidence

### 1. Intake Survey (GID: 1366958616)
**28 responses, 18 columns**

**Key Evidence:**
- Questions about AI usage and policy
- General participation readiness questions
- No specific role-based question IDs
- Broad organizational assessment

**Sample Headers:**
```
Reference #
Status
Name
Email
Role
Organization Name:
When might you be ready to participate?
Please select which of these best describes how AI is currently being used in your organization:
Do you have an AI policy in place?
Do you have any suggestions or comments for us on the Technology Strategy?
```

### 2. CEO Survey (GID: 1242252865)
**3 responses, 65 columns**

**Key Evidence:**
- Contains contact collection fields for CEO, Tech Lead, and Staff
- Uses C-* question IDs (CEO survey questions)
- Collects organizational contact information
- Functions as both intake form and CEO assessment

**Sample Headers:**
```
Reference #
Status
Login Email
Name
CEO Organization
CEO Email
CEO Role
Tech Lead First/Last/Email
Staff 1/2/3/4/5 First/Last/Email
C-PT-1, C-PT-2, C-PT-3  (CEO questions)
C-BS-1, C-BS-2, C-BS-3  (Business systems)
C-D-1, C-D-2  (Data questions)
C-I-1 through C-I-5  (Infrastructure)
C-OC-1 through C-OC-8  (Organizational capacity)
```

### 3. Tech Lead Survey (GID: 1545410106)
**2 responses, 33 columns**

**Key Evidence:**
- Uses TL-* question IDs (Tech Lead questions)
- Infrastructure-focused questions
- Technical system management questions

**Sample Headers:**
```
Reference #
Status
Name
Organization
TL-I-1 through TL-I-14  (Infrastructure questions)
TL-OC-1 through TL-OC-4  (Organizational capacity)
TL-CTC  (Technology challenges)
TLC-TIP  (Investment priorities)
TL-FC  (Final comments)
```

### 4. Staff Survey (GID: 377168987)
**4 responses, 35 columns**

**Key Evidence:**
- Uses S-* question IDs (Staff questions)
- Employee-focused perspective questions
- Business systems access questions

**Sample Headers:**
```
Reference #
Status
Name
Organization
S-PT-1, S-PT-2, S-PT-3  (Performance tracking)
S-BS-1, S-BS-2, S-BS-3, S-BS-4  (Business systems)
S-D-1, S-D-2, S-D-3  (Data questions)
S-I-1 through S-I-7  (Infrastructure)
S-OC-1, S-OC-2  (Organizational capacity)
S-CTC  (Technology challenges)
S-TIP  (Investment priorities)
S-FC  (Final comments)
```

### 5. Questions Bank (GID: 513349220)
**67 questions, 9 columns**

**Key Evidence:**
- Master question reference
- Contains Question ID and text
- Multiple choice answer options
- Used by all surveys

**Structure:**
```
Question ID | QUESTION | Answer 1 | Answer 2 | ... | Answer 7
```

**Question Distribution:**
- C-* (CEO): 25 questions
- S-* (Staff): 22 questions
- TL-* (Tech Lead): 19 questions
- TLC-* (Tech Lead Investment): 1 question

### 6. Key/Reference (GID: 1000323612)
**6 entries, 3 columns**

**Key Evidence:**
- Simple lookup table
- Name and URL structure
- Organization reference data

**Sample Headers:**
```
Name
URL
```

### 7. Summary (GID: 0)
**13 rows, 2 columns**

**Key Evidence:**
- Dashboard/overview sheet
- Contains "OVERALL SUMMARY" text
- Aggregated statistics

---

## Question ID Patterns

### CEO Survey (C-*)
**25 questions total**

Categories:
- **C-PT-***: Performance Tracking (3 questions)
- **C-BS-***: Business Systems (4 questions)
- **C-D-***: Data Management (2 questions)
- **C-I-***: Infrastructure (5 questions)
- **C-OC-***: Organizational Capacity (8 questions)
- **C-TC**: Technology Challenges
- **C-TIP**: Investment Priorities
- **C-FC**: Final Comments

**Sample Questions:**
```
C-BS-1: Which of the following best describes your systems for fundraising and grants management
C-BS-2: Which of the following best describes how you are able to use and access financial data
C-BS-3: Which of the following best describes your current HR system
C-D-1: Which of the following best describes your tools for collecting and using data for program
```

### Tech Lead Survey (TL-*)
**19 questions total**

Categories:
- **TL-I-***: Infrastructure (14 questions)
- **TL-OC-***: Organizational Capacity (4 questions)
- **TL-CTC**: Technology Challenges
- **TLC-TIP**: Investment Priorities (Tech Lead specific)
- **TL-FC**: Final Comments

**Sample Questions:**
```
TL-I-1: Which of the following best describes your process for on-boarding and off-boarding staff
TL-I-10: Which of the following best describes how software and system updates are managed
TL-I-11: Which of the following best describes what training for key technology systems look like
TL-I-12: Which of the following best describes how hardware and software support is handled
```

### Staff Survey (S-*)
**22 questions total**

Categories:
- **S-PT-***: Performance Tracking (3 questions)
- **S-BS-***: Business Systems (4 questions)
- **S-D-***: Data Management (3 questions)
- **S-I-***: Infrastructure (7 questions)
- **S-OC-***: Organizational Capacity (2 questions)
- **S-CTC**: Technology Challenges
- **S-TIP**: Investment Priorities
- **S-FC**: Final Comments

**Sample Questions:**
```
S-BS-1: Which of the following best describes your ability to access financial data relevant to you
S-BS-2: Which of the following best describes your organization's HR systems and processes
S-BS-3: Which of the following best describes your organization's fundraising systems
```

---

## Recommended Implementation

### Updated TABS Dictionary

```python
# Use in simple_extractor.py
TABS = {
    "Intake": 1366958616,
    "CEO": 1242252865,
    "Tech": 1545410106,
    "Staff": 377168987,
    "Questions": 513349220,
    "Key": 1000323612,
}
```

### Sheet Processing Order

1. **Key** - Load organization reference data first
2. **Questions** - Load question bank for reference
3. **Intake** - Process initial participation surveys
4. **CEO** - Process CEO assessments (includes contact collection)
5. **Tech** - Process Tech Lead surveys
6. **Staff** - Process Staff surveys
7. **Summary** - Generate or skip (may be auto-generated)

---

## Data Relationships

### Contact Flow (CEO Sheet)
```
CEO Sheet → Collects contacts for:
├── CEO (Organization, Email, Role)
├── Tech Lead (First, Last, Email, Role)
└── Staff 1-5 (First, Last, Email, Role)
```

### Survey Response Flow
```
Intake Survey → Initial interest
    ↓
CEO Survey → Organizational assessment + Contact collection
    ↓
Tech Lead Survey → Technical infrastructure assessment
    ↓
Staff Survey → Employee perspective assessment
```

### Question Reference
```
Questions Bank (67 questions)
├── C-* questions → Used in CEO Survey
├── TL-* questions → Used in Tech Lead Survey
└── S-* questions → Used in Staff Survey
```

---

## Data Quality Observations

### Response Counts
- **High**: Intake (28 responses) - Good initial engagement
- **Low**: CEO (3), Tech (2), Staff (4) - Limited follow-through
- **Reference**: Questions (67), Key (6) - Complete

### Data Completeness
- Intake survey has highest completion rate
- CEO survey collects extensive contact information
- Tech and Staff surveys have role-specific questions
- Question bank is comprehensive (67 questions across 3 surveys)

### Sheet Structure
- All survey sheets follow consistent metadata pattern:
  - Reference #, Status, Name, Email/Organization, Date, Time, Duration
- Question columns use standardized ID format
- Business metadata (Browser, Device, Referrer) captured

---

## Next Steps

1. **Update simple_extractor.py** with new TABS dictionary
2. **Test extraction** with meaningful sheet names
3. **Update normalization** to handle 7 sheets (not 6)
4. **Consider Summary sheet** - determine if it should be extracted or ignored
5. **Document question ID patterns** for future reference

---

## Analysis Methodology

1. **Schema Analysis**: Examined `tab_data` table structure
2. **Content Inspection**: Reviewed first 5 rows of each tab
3. **Header Analysis**: Identified column patterns and question IDs
4. **Question Mapping**: Matched question IDs to question bank
5. **Pattern Recognition**: Identified C-*, TL-*, S-* prefixes
6. **Cross-Reference**: Validated mappings across all sheets

**Tools Used:**
- SQLite queries on `simple_data.db`
- JSON data inspection
- Pattern matching on question IDs
- Column header analysis

---

*Analysis Date: 2025-10-11*
*Database: simple_data.db*
*Total Sheets Analyzed: 7*
