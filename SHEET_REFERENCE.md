# Google Sheets Reference

**Spreadsheet ID**: `15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU`

**Spreadsheet Name**: JJF Technology Assessment

---

## Sheet Tabs

### 1. Summary (GID: 0)
**Purpose**: Overview/summary tab
**Rows**: ~13
**Key Columns**: Summary statistics and aggregated data

---

### 2. Intake / Contacts (GID: 1366958616)
**Purpose**: Initial participation survey and contact information
**Rows**: 28 responses
**Key Columns**:
- `Organization Name:` - Organization identifier
- `Email` - Contact email
- `Name` - Contact name
- `Role` - Contact role/title
- `Date` - Submission date
- `Please select which of these best describes how AI is currently being used in your organization:`
- `Do you have an AI policy in place?`
- `Do you have any suggestions or comments for us on the Technology Strategy?`

**Notes**:
- This is the main contacts/intake response sheet
- Organizations submit this form first to express interest
- 28 organizations have submitted intake forms

---

### 3. CEO (GID: 1242252865)
**Purpose**: CEO assessment survey with contact details
**Rows**: 3 responses
**Question ID Prefix**: C-*
**Key Columns**:
- `CEO Organization` - Organization identifier
- `CEO Email` - CEO contact email
- `CEO Name` - CEO name
- `CEO Role` - CEO role/title
- `Tech Lead First`, `Tech Lead Last`, `Tech Lead Email` - Tech lead contact info
- `Staff 1 First`, `Staff 1 Last`, `Staff 1 Email` - Staff contact info
- Additional staff contact fields

**Notes**:
- Only 3 organizations have completed CEO assessments
- Contains contact information for CEO, Tech Lead, and Staff members

---

### 4. Tech (GID: 1545410106)
**Purpose**: Tech Lead survey responses
**Rows**: 2 responses
**Question ID Prefix**: TL-*
**Key Columns**:
- `Organization` - Organization identifier
- Tech lead survey responses

**Notes**:
- Only 2 organizations have completed Tech Lead surveys

---

### 5. Staff (GID: 377168987)
**Purpose**: Staff survey responses
**Rows**: 4 responses
**Question ID Prefix**: S-*
**Key Columns**:
- `Organization` - Organization identifier
- Staff survey responses

**Notes**:
- 4 organizations have completed Staff surveys

---

### 6. Questions (GID: 513349220)
**Purpose**: Question bank with IDs and answer options
**Rows**: 67 questions
**Key Columns**:
- Question IDs
- Question text
- Answer options/choices

**Notes**:
- Master list of all survey questions
- Used for mapping question IDs to text

---

### 7. Key (GID: 1000323612)
**Purpose**: Organization reference lookup table
**Rows**: 6 entries
**Key Columns**:
- Organization reference mappings

**Notes**:
- Cross-reference table for organization names

---

### 8. OrgMaster (GID: 601687640) ⭐ PRIMARY REFERENCE
**Purpose**: Master list of ALL organizations reached out to
**Rows**: 43 organizations
**Key Columns**:
- `Organization` - Organization name (PRIMARY KEY)
- `Email` - Primary contact email
- `Full Name` - Contact full name
- `First Name` - Contact first name
- `Last Name` - Contact last name
- `Job Title` - Contact job title
- `2nd Contact Full Name` - Secondary contact
- `PO` - Primary outreach contact
- `2nd PO` - Secondary outreach contact
- `3rd PO` - Tertiary outreach contact

**Notes**:
- **SINGLE SOURCE OF TRUTH** for all organizations in the assessment
- Contains 43 total organizations contacted
- Used to calculate response rates (28/43 submitted intake = 65.1%)
- Email addresses available for most organizations
- Used as fallback for contact information when organizations haven't responded

---

## Data Relationships

### Organization Tracking Flow
```
OrgMaster (43 orgs)
    ↓
Intake/Contacts (28 responded)
    ↓
    ├─→ CEO Survey (3 completed)
    ├─→ Tech Survey (2 completed)
    └─→ Staff Survey (4 completed)
```

### Organization Name Mapping
- **OrgMaster**: `Organization` field
- **Intake**: `Organization Name:` field (note the colon!)
- **CEO**: `CEO Organization` field
- **Tech**: `Organization` field
- **Staff**: `Organization` field

**Important**: Organization names must match exactly across sheets for proper linking.

---

## Response Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Organizations Contacted | 43 | 100% |
| Intake Responses | 28 | 65.1% |
| No Response | 15 | 34.9% |
| CEO Surveys Complete | 3 | 7.0% |
| Tech Surveys Complete | 2 | 4.7% |
| Staff Surveys Complete | 4 | 9.3% |
| Fully Complete (all surveys) | 1 | 2.3% |

---

## Email Resolution Logic

The application uses a fallback approach for contact emails:

1. **Primary**: Use email from Intake sheet if organization has responded
2. **Fallback**: Use email from OrgMaster sheet if organization hasn't responded
3. **Result**: Maximum email coverage for all organizations

**Implementation**: See `get_organizations_summary()` in `app.py`

---

## Usage in Application

### sheets_reader.py
Defines the tab configuration and handles Google Sheets data fetching:
```python
TABS = {
    "Summary": "0",
    "Intake": "1366958616",      # Contacts/intake responses
    "CEO": "1242252865",         # CEO assessment + contacts
    "Tech": "1545410106",        # Tech Lead survey
    "Staff": "377168987",        # Staff survey
    "Questions": "513349220",    # Question bank
    "Key": "1000323612",         # Organization reference
    "OrgMaster": "601687640",    # Master organization list
}
```

### app.py Functions
- `get_organizations_summary()`: Merges OrgMaster with Intake data, uses email fallback
- `get_response_rates()`: Calculates response rates using OrgMaster as denominator
- `get_stats()`: Dashboard statistics including response rates

---

## Export URLs

Access individual sheets via CSV export:

```
Base URL: https://docs.google.com/spreadsheets/d/15ZaH4wyt4Wz95kiW1kLe6h4bwuqsA-voBwSzGwni2ZU/export?format=csv&gid={GID}

Summary:   &gid=0
Intake:    &gid=1366958616
CEO:       &gid=1242252865
Tech:      &gid=1545410106
Staff:     &gid=377168987
Questions: &gid=513349220
Key:       &gid=1000323612
OrgMaster: &gid=601687640
```

---

*Last Updated: 2025-10-12*
