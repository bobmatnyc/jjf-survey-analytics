# simple_data.db Analysis Report
**Organization Participation Flow Analysis**
**Generated:** 2025-10-11
**Database:** `/Users/masa/Clients/JimJoseph/jjf-survey-analytics/simple_data.db`

---

## Executive Summary

### Key Findings

**Participation Metrics:**
- **24 unique organizations** completed intake forms
- **3 organizations (12.5%)** have CEO responses
- **2 organizations (8.3%)** have Tech Lead responses
- **2 organizations (8.3%)** have Staff responses
- **1 organization (4.2%)** has full completion (Hadar Institute)

**Critical Insight:** There is a significant drop-off between intake and CEO survey completion, with only 12.5% conversion rate.

### Participation Funnel

```
Intake Completed:        24 organizations (100.0%)
  ↓
CEO Survey:               3 organizations ( 12.5%)
  ↓
Tech Lead Survey:         2 organizations (  8.3%)
  ↓
Staff Survey:             2 organizations (  8.3%)
  ↓
Full Completion:          1 organization  (  4.2%)
```

---

## Database Structure

### Table Schema
The database uses a single `tab_data` table with JSON storage:

```sql
CREATE TABLE tab_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tab_name TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tab Types and Row Counts
| Tab Name  | Row Count | Purpose                          |
|-----------|-----------|----------------------------------|
| Intake    | 28        | Initial organization interest    |
| CEO       | 3         | CEO survey responses             |
| Tech      | 2         | Tech Lead survey responses       |
| Staff     | 4         | Staff survey responses           |
| Summary   | 13        | Summary/aggregation data         |
| Questions | 67        | Question definitions             |
| Key       | 6         | Key/legend information           |

---

## Data Linkage Architecture

### Organization Identification

Organizations are identified by **name string matching** across tabs:

| Tab     | Organization Field              | Example Value              |
|---------|---------------------------------|----------------------------|
| Intake  | `"Organization Name:"`          | "Hadar Institute"          |
| CEO     | `"CEO Organization"`            | "Hadar Institute"          |
| Tech    | `"Organization"`                | "Hadar Institute"          |
| Staff   | `"Organization"`                | "Hadar Institute"          |

**Critical:** Organization names must match **exactly** for linking. Minor variations (punctuation, spacing) will break linkage.

### Sample Data Structures

**Intake Tab Fields:**
- `Reference #` - Form submission ID
- `Status` - Submission status (typically "Complete")
- `Name` - Contact person name
- `Email` - Contact email
- `Organization Name:` - **Primary key for linking**
- `When might you be ready to participate?` - Readiness indicator
- `Date` - Submission timestamp
- AI usage level, policy status, etc.

**CEO Tab Fields:**
- `Reference #` - Form submission ID
- `Name` - CEO name
- `CEO Organization` - **Links to Intake organization**
- `CEO Email` - CEO contact
- `Tech Lead First` / `Tech Lead Last` / `Tech Lead Email` - Assigned tech delegate
- `Staff 1 First` / `Staff 1 Last` / `Staff 1 Email` - Assigned staff delegate #1
- ` Staff 2 First` / `Staff 2 Last` / `Staff 2 Email` - Assigned staff delegate #2 (note space in field name)
- `Additional Staff` - Yes/No indicator
- `Date` - Submission timestamp
- Survey question responses (C-PT-1, C-BS-1, etc.)

**Tech Tab Fields:**
- `Reference #` - Form submission ID
- `Name` - Tech lead name
- `Organization` - **Links to CEO organization**
- `Date` - Submission timestamp
- Survey question responses (TL-I-1, TL-OC-1, etc.)

**Staff Tab Fields:**
- `Reference #` - Form submission ID
- `Name` - Staff member name
- `Organization` - **Links to CEO organization**
- `Date` - Submission timestamp
- Survey question responses (S-PT-1, S-BS-1, etc.)

---

## Organizations with Complete Data

### 1. Hadar Institute ✅ FULLY COMPLETE
- **Intake:** Oren Harary (2025-09-17)
- **CEO:** Elie Kaunfer (2025-09-30)
  - Assigned Tech: Oren Harary
  - Assigned Staff: Esther Bedolla, Amishar Frutkoff
- **Tech Lead:** Oren Harary (2025-10-08) ✅
- **Staff Responses:**
  - Esther Bedolla Gonzalez (2025-10-06) ✅
  - Amishar Frutkoff (2025-10-10) ✅

**Status:** Complete participation across all stages

---

### 2. Jewish New Teacher Project ⚠️ PARTIAL COMPLETION
- **Intake:** Nina Bruder (2025-09-29)
- **CEO:** Nina Bruder (2025-09-30)
  - Assigned Tech: Jason Randall
  - Assigned Staff: Lauren Katz, Leah Volynsky
- **Tech Lead:** Jason Randall (2025-10-03) ✅
- **Staff Responses:** 0 ❌

**Status:** CEO and Tech complete, awaiting Staff responses

---

### 3. R&R: The Rest of Our Lives ⚠️ PARTIAL COMPLETION
- **Intake:** Rachel Zieleniec (2025-09-15), Sokeng (2025-09-30)
- **CEO:** Josh Feldman (2025-10-03)
  - Assigned Tech: Josh Feldman (CEO self-assigned)
  - Assigned Staff: Rachel Zieleniec, Sokeng Cleary
- **Tech Lead:** Not completed ❌
- **Staff Responses:**
  - Rachel Zieleniec (2025-10-03) ✅
  - Sokeng Cleary (2025-10-10) ✅

**Status:** CEO and Staff complete, awaiting Tech Lead response

---

## Organizations Awaiting CEO Survey (21 orgs)

Organizations that completed intake but have not yet submitted CEO survey:

| Organization                                   | Contact                  | Intake Date | Days Since | Readiness              |
|-----------------------------------------------|--------------------------|-------------|------------|------------------------|
| UpStart                                       | Seth Linden              | 2025-10-07  | 4          | Ready now              |
| Jewish Studio Project                         | Julianne Schwartz        | 2025-10-06  | 5          | Ready now              |
| Atra: Center for Rabbinic Innovation          | Dani Bronstein           | 2025-09-30  | 11         | Don't know             |
| JIMENA                                        | Nathaniel Malka          | 2025-09-30  | 11         | 3-6 months             |
| JIMENA                                        | Sarah Levin              | 2025-09-29  | 12         | Ready now              |
| For the Sake of Argument                      | Abi Dauber Sterne        | 2025-09-28  | 13         | Ready now              |
| Prizmah                                       | Elissa Maier             | 2025-09-26  | 15         | 1-3 months             |
| Moving Traditions                             | Debra Michael            | 2025-09-25  | 16         | Ready now              |
| Repair the World                              | Cindy Greenberg          | 2025-09-25  | 16         | 1-3 months             |
| Safety, Respect, Equity Network               | Shaina Wasserman         | 2025-09-22  | 19         | 1-3 months             |
| Jewtina                                       | Violeta Stolpen          | 2025-09-19  | 22         | 1-3 months             |
| Lauder Impact Initiative                      | Sam Roth                 | 2025-09-19  | 22         | Ready now              |
| Reboot                                        | Shane Hankins            | 2025-09-19  | 22         | Ready now              |
| 70 Faces Media                                | Sara Blancke             | 2025-09-18  | 23         | 1-3 months             |
| Foundation for Jewish Camp                    | Jamie Simon              | 2025-09-18  | 23         | 6-9 months             |
| UpStart                                       | Aaron Katler             | 2025-09-17  | 24         | 1-3 months             |
| Mem Global                                    | David Cygielman          | 2025-09-16  | 25         | 3-6 months             |
| At The Well                                   | Sarah Waxman             | 2025-09-16  | 25         | Ready now              |
| ReCustom                                      | Eileen Levinson          | 2025-09-16  | 25         | Ready now              |
| The Jewish Education Project / RootOne        | Simon Amiel              | 2025-09-16  | 25         | Don't know             |
| Institute for Jewish Spirituality             | Alyse Erman              | 2025-09-16  | 25         | Ready now              |
| SVARA                                         | Ayana Morse              | 2025-09-16  | 25         | Ready now              |
| Jewtina                                       | Analucia Lopezrevoredo   | 2025-09-15  | 26         | 3-6 months             |
| The Shalom Hartman Institute of North America | Rachel Jacoby Rosenfield | 2025-09-15  | 26         | 1-3 months             |

**High Priority (>14 days):** 19 organizations
**Medium Priority (7-14 days):** 2 organizations
**Recent (<7 days):** 2 organizations

---

## Data Quality Issues

### 1. Duplicate Intake Entries (4 organizations)

Multiple people from same organization submitted intake forms:

| Organization               | Contacts                            |
|---------------------------|-------------------------------------|
| JIMENA                    | Sarah Levin, Nathaniel Malka        |
| Jewtina                   | Analucia Lopezrevoredo, Violeta Stolpen |
| R&R: The Rest of Our Lives| Rachel Zieleniec, Sokeng            |
| UpStart                   | Aaron Katler, Seth Linden           |

**Impact:** Duplicate intake entries create ambiguity about primary contact. Dashboard should consolidate or show both.

**Recommendation:** Use most recent intake entry as primary, or display all contacts.

---

### 2. Tech Lead Assignment Mismatches

**R&R: The Rest of Our Lives:**
- CEO assigned: Josh Feldman (CEO)
- Tech form expected from: Josh Feldman
- Tech form submitted: None
- Issue: CEO assigned themselves as tech lead but haven't completed tech form

**Recommendation:** Track "self-assigned" cases separately and follow up accordingly.

---

### 3. Delegate Tracking Issues

**Jewish New Teacher Project:**
- Assigned staff: Lauren Katz, Leah Volynsky
- Staff responses received: 0
- Delegates assigned but not responding

**Recommendation:** Dashboard should show "delegates assigned but no response" status.

---

### 4. Readiness vs. Completion Mismatch

Organizations stating "I'm ready to start now!" (15 orgs) have low completion rate:
- 15 organizations ready now
- Only 2 of those have completed CEO survey
- 13.3% follow-through rate among "ready now" organizations

**Recommendation:** Readiness indicator may not be accurate predictor of completion.

---

## Recommended Dashboard Layout

### Dashboard Section 1: Overview Metrics (Top Cards)

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Total Organizations│  │  CEO Surveys        │  │  Fully Complete     │
│                     │  │                     │  │                     │
│        24           │  │     3 (12.5%)       │  │     1 (4.2%)        │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  Tech Lead Surveys  │  │  Staff Surveys      │  │  Awaiting CEO       │
│                     │  │                     │  │                     │
│     2 (8.3%)        │  │     2 (8.3%)        │  │    21 (87.5%)       │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Dashboard Section 2: Participation Funnel Visualization

```
Intake         ████████████████████████ 24 (100%)
                ↓
CEO Survey     ███ 3 (12.5%)
                ↓
Tech Lead      ██ 2 (8.3%)
                ↓
Staff          ██ 2 (8.3%)
                ↓
Complete       █ 1 (4.2%)
```

### Dashboard Section 3: Organizations by Status

**Table with columns:**
- Organization Name
- Intake Date
- Intake Contact
- Readiness Level
- CEO Status (Complete/Pending)
- Tech Status (Complete/Pending/Assigned)
- Staff Count (0, 1, 2+)
- Overall Status (Complete/In Progress/Not Started)
- Days Since Intake
- Latest Activity

**Sortable and filterable by:**
- Status
- Readiness level
- Days since intake
- Completion stage

### Dashboard Section 4: Organizations Needing Attention

**Priority sections:**

1. **High Priority Follow-up** (Intake >14 days, no CEO survey)
   - Show organization, contact, days waiting
   - Sort by days descending

2. **Delegates Not Responding** (CEO assigned delegates, no response after 7 days)
   - Show organization, assigned delegate name/email, days since assignment

3. **Partial Completions** (CEO done, awaiting delegates)
   - Show organization, which delegates are pending

### Dashboard Section 5: Recent Activity Feed

**Timeline of latest 20 submissions:**
- Timestamp
- Organization
- Activity type (Intake/CEO/Tech/Staff)
- Person name
- Brief description

### Dashboard Section 6: Readiness Analysis

**Bar chart showing:**
- Readiness level
- Number of organizations
- Number/percentage with CEO survey completed

**Example:**
```
Ready now!       ████████████████ 15 orgs (2 CEO done = 13.3%)
1-3 months       ████████ 7 orgs (1 CEO done = 14.3%)
3-6 months       ████ 3 orgs (0 CEO done = 0%)
6-9 months       ██ 1 org (0 CEO done = 0%)
Don't know       ██ 2 orgs (0 CEO done = 0%)
```

---

## SQL Queries for Dashboard

All queries are available in **`dashboard_queries.sql`** with 8 comprehensive queries:

1. **Complete Participation Funnel** - Full organization status across all stages
2. **Dashboard Summary Metrics** - KPIs for overview cards
3. **Completion Rates by Stage** - Conversion funnel with percentages
4. **Recent Activity Feed** - Latest 20 submissions timeline
5. **Organizations Awaiting Follow-up** - Priority list for outreach
6. **Delegate Assignment vs Response** - Track delegate follow-through
7. **Data Quality Issues** - Identify duplicates and anomalies
8. **Readiness Status Summary** - Analyze readiness vs completion

---

## Implementation Recommendations

### Dashboard Technology Stack

**Backend (Python/Flask):**
```python
# Sample query execution
import sqlite3
import json

def get_participation_metrics():
    conn = sqlite3.connect('simple_data.db')
    cursor = conn.cursor()

    query = """
    WITH intake_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.\"Organization Name:\"')) as org_name
        FROM tab_data WHERE tab_name = 'Intake'
    ),
    ceo_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.\"CEO Organization\"')) as org_name
        FROM tab_data WHERE tab_name = 'CEO'
    )
    SELECT
        COUNT(DISTINCT i.org_name) as total_orgs,
        COUNT(DISTINCT c.org_name) as ceo_complete
    FROM intake_list i
    LEFT JOIN ceo_list c ON i.org_name = c.org_name
    """

    return cursor.execute(query).fetchone()
```

**Frontend (HTML/JavaScript):**
- Use existing Flask templates structure
- Tailwind CSS for styling (already in project)
- Chart.js or similar for funnel visualization
- Real-time updates via AJAX polling or WebSockets

### Key Features to Implement

1. **Auto-refresh** - Poll database every 30 seconds for new submissions
2. **Filtering** - Filter by status, readiness, date range
3. **Sorting** - Sort by any column (org name, date, status)
4. **Search** - Full-text search across organization names
5. **Export** - CSV export of filtered data
6. **Alerts** - Visual indicators for high-priority follow-ups

### Data Refresh Strategy

Since `simple_data.db` is extracted from Google Sheets:

1. **Manual refresh**: Run extractor script when needed
2. **Scheduled refresh**: Cron job to re-extract periodically
3. **Dashboard refresh**: Auto-reload metrics every 30-60 seconds
4. **Change detection**: Track `extracted_at` timestamp to show freshness

---

## Sample Implementation Code

### Flask Route for Dashboard Metrics

```python
from flask import Flask, jsonify, render_template
import sqlite3
import json

app = Flask(__name__)

@app.route('/api/dashboard/metrics')
def dashboard_metrics():
    conn = sqlite3.connect('simple_data.db')
    cursor = conn.cursor()

    # Execute Query 2 from dashboard_queries.sql
    query = """
    WITH intake_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.\"Organization Name:\"')) as org_name
        FROM tab_data WHERE tab_name = 'Intake'
          AND json_extract(data_json, '$.\"Organization Name:\"') IS NOT NULL
    ),
    ceo_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.\"CEO Organization\"')) as org_name
        FROM tab_data WHERE tab_name = 'CEO'
    ),
    tech_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.Organization')) as org_name
        FROM tab_data WHERE tab_name = 'Tech'
    ),
    staff_list AS (
        SELECT DISTINCT TRIM(json_extract(data_json, '$.Organization')) as org_name
        FROM tab_data WHERE tab_name = 'Staff'
    )
    SELECT
        (SELECT COUNT(DISTINCT org_name) FROM intake_list) as total_organizations,
        (SELECT COUNT(DISTINCT i.org_name) FROM intake_list i
         INNER JOIN ceo_list c ON i.org_name = c.org_name) as ceo_complete,
        (SELECT COUNT(DISTINCT i.org_name) FROM intake_list i
         INNER JOIN tech_list t ON i.org_name = t.org_name) as tech_complete,
        (SELECT COUNT(DISTINCT i.org_name) FROM intake_list i
         INNER JOIN staff_list s ON i.org_name = s.org_name) as staff_complete,
        (SELECT COUNT(DISTINCT i.org_name) FROM intake_list i
         INNER JOIN ceo_list c ON i.org_name = c.org_name
         INNER JOIN tech_list t ON i.org_name = t.org_name
         INNER JOIN staff_list s ON i.org_name = s.org_name) as fully_complete,
        (SELECT COUNT(DISTINCT i.org_name) FROM intake_list i
         LEFT JOIN ceo_list c ON i.org_name = c.org_name
         WHERE c.org_name IS NULL) as not_started
    """

    result = cursor.execute(query).fetchone()
    conn.close()

    return jsonify({
        'total_organizations': result[0],
        'ceo_complete': result[1],
        'tech_complete': result[2],
        'staff_complete': result[3],
        'fully_complete': result[4],
        'not_started': result[5]
    })

@app.route('/dashboard')
def dashboard():
    return render_template('participation_dashboard.html')
```

### HTML Template Structure

```html
<!-- templates/participation_dashboard.html -->
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Organization Participation Dashboard</h1>

    <!-- Overview Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-gray-500 text-sm">Total Organizations</div>
            <div class="text-3xl font-bold" id="total-orgs">-</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <div class="text-gray-500 text-sm">CEO Surveys</div>
            <div class="text-3xl font-bold" id="ceo-complete">-</div>
            <div class="text-sm text-gray-400" id="ceo-pct">-</div>
        </div>
        <!-- More metric cards... -->
    </div>

    <!-- Funnel Visualization -->
    <div class="bg-white rounded-lg shadow p-6 mb-8">
        <h2 class="text-xl font-bold mb-4">Participation Funnel</h2>
        <canvas id="funnelChart"></canvas>
    </div>

    <!-- Organizations Table -->
    <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-bold mb-4">Organizations by Status</h2>
        <table id="orgs-table" class="w-full">
            <!-- Table content -->
        </table>
    </div>
</div>

<script>
// Auto-refresh metrics every 30 seconds
setInterval(refreshMetrics, 30000);

function refreshMetrics() {
    fetch('/api/dashboard/metrics')
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-orgs').textContent = data.total_organizations;
            document.getElementById('ceo-complete').textContent = data.ceo_complete;
            // Update other metrics...
        });
}

// Initial load
refreshMetrics();
</script>
{% endblock %}
```

---

## Next Steps

### Immediate Actions

1. **Create dashboard route** in `app.py`
2. **Add template** `templates/participation_dashboard.html`
3. **Implement API endpoints** for metrics using queries from `dashboard_queries.sql`
4. **Test queries** against `simple_data.db`
5. **Add navigation** link to existing dashboard

### Enhancement Opportunities

1. **Email notifications** for high-priority follow-ups
2. **Export functionality** for filtered organization lists
3. **Historical tracking** - Track changes over time
4. **Delegate email automation** - Send reminders to assigned delegates
5. **Integration with existing analytics** - Link to survey_normalized.db data

### Data Maintenance

1. **Regular extraction** - Schedule `simple_extractor.py` to run periodically
2. **Data validation** - Implement checks for organization name consistency
3. **Duplicate resolution** - Establish process for handling duplicate intakes
4. **Archive old data** - Keep historical snapshots for trend analysis

---

## Conclusion

The `simple_data.db` database provides a clear participation flow from Intake → CEO → Tech Lead → Staff surveys, with organization name as the linking key. The current 12.5% conversion rate from intake to CEO survey represents a significant opportunity for improved follow-up and engagement.

The recommended dashboard will provide:
- Real-time visibility into participation status
- Clear identification of organizations needing follow-up
- Tracking of delegate assignments and responses
- Data quality monitoring
- Activity timeline for recent submissions

All necessary SQL queries are provided in `dashboard_queries.sql` for immediate implementation.
