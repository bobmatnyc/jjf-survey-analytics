# Report Implementation Quick Start Guide

**Last Updated:** 2025-10-11
**Estimated Time:** 4-6 hours for basic per-organization report

---

## Overview

This guide provides step-by-step instructions to implement the reporting system for JJF Survey Analytics. Follow these steps to quickly create functional reports.

---

## Prerequisites

- Working JJF Survey Analytics installation
- Python 3.13+ environment
- Flask application running
- Access to survey data via `sheets_reader.py`

---

## Quick Start: Per-Organization Report

### Step 1: Create Report Generator (15 minutes)

Create `/Users/masa/Clients/JimJoseph/jjf-survey-analytics/report_generator.py`:

```python
"""
Report data generator for JJF Survey Analytics.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sheets_reader import get_all_tabs

def get_organization_report_data(org_name: str) -> Dict[str, Any]:
    """
    Generate comprehensive report data for a single organization.

    Args:
        org_name: Organization name

    Returns:
        Dictionary with all report sections
    """
    # Load all data
    tabs = get_all_tabs()
    intake_data = tabs.get('intake', [])
    ceo_data = tabs.get('ceo', [])
    tech_data = tabs.get('tech', [])
    staff_data = tabs.get('staff', [])

    # Find organization records
    org_intake = next((r for r in intake_data if r.get('Organization Name:', '').strip() == org_name), None)
    org_ceo = next((r for r in ceo_data if r.get('CEO Organization', '').strip() == org_name), None)
    org_tech = next((r for r in tech_data if r.get('Organization', '').strip() == org_name), None)
    org_staff = next((r for r in staff_data if r.get('Organization', '').strip() == org_name), None)

    # Calculate completion
    surveys_completed = sum([
        1 if org_intake else 0,
        1 if org_ceo else 0,
        1 if org_tech else 0,
        1 if org_staff else 0
    ])
    completion_pct = int((surveys_completed / 4) * 100)

    # Build contacts list
    contacts = []
    if org_intake:
        contacts.append({
            'name': org_intake.get('Primary Contact Name', 'N/A'),
            'email': org_intake.get('Email', 'N/A'),
            'role': 'Primary Contact',
            'survey_type': 'intake',
            'survey_completed': True,
            'completion_date': org_intake.get('Date', '')
        })

    if org_ceo:
        contacts.append({
            'name': org_ceo.get('CEO Name', 'N/A'),
            'email': org_ceo.get('CEO Email', 'N/A'),
            'role': 'CEO',
            'survey_type': 'ceo',
            'survey_completed': True,
            'completion_date': org_ceo.get('Date', '')
        })

    if org_tech:
        contacts.append({
            'name': org_tech.get('Tech Lead Name', 'N/A'),
            'email': org_tech.get('Tech Lead Email', 'N/A'),
            'role': 'Technology Lead',
            'survey_type': 'tech',
            'survey_completed': True,
            'completion_date': org_tech.get('Date', '')
        })

    if org_staff:
        contacts.append({
            'name': org_staff.get('Staff Name', 'N/A'),
            'email': org_staff.get('Staff Email', 'N/A'),
            'role': 'Staff Member',
            'survey_type': 'staff',
            'survey_completed': True,
            'completion_date': org_staff.get('Date', '')
        })

    # Generate insights
    insights = []
    if completion_pct == 100:
        insights.append("All surveys completed - comprehensive data available")
    elif completion_pct >= 75:
        insights.append("Strong participation across most surveys")
    else:
        insights.append("Additional survey responses would enhance analysis")

    if not org_ceo:
        insights.append("Leadership perspective needed - CEO survey pending")
    if not org_tech:
        insights.append("Technical assessment incomplete - Tech Lead survey pending")
    if not org_staff:
        insights.append("Staff perspective would enhance comprehensive view")

    # Get latest activity date
    dates = []
    for record in [org_intake, org_ceo, org_tech, org_staff]:
        if record and record.get('Date'):
            try:
                dates.append(datetime.strptime(record['Date'][:10], '%Y-%m-%d'))
            except:
                pass

    latest_activity = max(dates) if dates else None

    return {
        'organization_name': org_name,
        'report_date': datetime.now(),
        'completion_percentage': completion_pct,
        'surveys_completed': surveys_completed,
        'total_surveys': 4,
        'total_responses': surveys_completed,
        'participation_rate': completion_pct,
        'latest_activity_date': latest_activity,
        'key_insights': insights,
        'contacts': contacts,
        'intake_data': org_intake or {},
        'ceo_data': org_ceo or {},
        'tech_data': org_tech or {},
        'staff_data': org_staff or {},
        'surveys': [
            {
                'survey_type': 'intake',
                'survey_label': 'Intake Survey',
                'status': 'complete' if org_intake else 'pending',
                'completion_date': org_intake.get('Date', '') if org_intake else None,
                'submitter_name': org_intake.get('Primary Contact Name', '') if org_intake else '',
                'submitter_email': org_intake.get('Email', '') if org_intake else '',
                'icon_color': 'gray'
            },
            {
                'survey_type': 'ceo',
                'survey_label': 'CEO Survey',
                'status': 'complete' if org_ceo else 'pending',
                'completion_date': org_ceo.get('Date', '') if org_ceo else None,
                'submitter_name': org_ceo.get('CEO Name', '') if org_ceo else '',
                'submitter_email': org_ceo.get('CEO Email', '') if org_ceo else '',
                'icon_color': 'blue'
            },
            {
                'survey_type': 'tech_lead',
                'survey_label': 'Tech Lead Survey',
                'status': 'complete' if org_tech else 'pending',
                'completion_date': org_tech.get('Date', '') if org_tech else None,
                'submitter_name': org_tech.get('Tech Lead Name', '') if org_tech else '',
                'submitter_email': org_tech.get('Tech Lead Email', '') if org_tech else '',
                'icon_color': 'purple'
            },
            {
                'survey_type': 'staff',
                'survey_label': 'Staff Survey',
                'status': 'complete' if org_staff else 'pending',
                'completion_date': org_staff.get('Date', '') if org_staff else None,
                'submitter_name': org_staff.get('Staff Name', '') if org_staff else '',
                'submitter_email': org_staff.get('Staff Email', '') if org_staff else '',
                'icon_color': 'green'
            }
        ]
    }
```

### Step 2: Add Flask Route (5 minutes)

Add to `/Users/masa/Clients/JimJoseph/jjf-survey-analytics/app.py`:

```python
from report_generator import get_organization_report_data

@app.route('/report/org/<org_name>')
def organization_report(org_name: str):
    """Generate per-organization report."""
    try:
        data = get_organization_report_data(org_name)
        return render_template('report_organization.html', **data)
    except Exception as e:
        return render_template('error.html',
                             error=f"Error generating report for '{org_name}': {str(e)}"), 500
```

### Step 3: Create Report Template (30 minutes)

Create `/Users/masa/Clients/JimJoseph/jjf-survey-analytics/templates/report_organization.html`:

```html
{% extends "simple_base.html" %}

{% block title %}{{ organization_name }} - Organization Report{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto space-y-8">
    <!-- Report Header -->
    <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-survey-blue">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-bold text-gray-900 flex items-center mb-2">
                    <i class="fas fa-building text-survey-blue mr-3"></i>
                    {{ organization_name }}
                </h1>
                <p class="text-sm text-gray-600">
                    <i class="fas fa-calendar-alt mr-2"></i>
                    Report Generated: {{ report_date.strftime('%B %d, %Y at %I:%M %p') }}
                </p>
            </div>
            <div class="text-right">
                <div class="text-3xl font-bold text-survey-blue">{{ completion_percentage }}%</div>
                <div class="text-sm text-gray-600">Survey Completion</div>
                <div class="text-xs text-gray-500 mt-1">{{ surveys_completed }}/{{ total_surveys }} surveys complete</div>
            </div>
        </div>
    </div>

    <!-- Export Actions -->
    <div class="no-print flex justify-end space-x-3 mb-4">
        <button onclick="window.print()"
                class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
            <i class="fas fa-print mr-2"></i>Print Report
        </button>
    </div>

    <!-- Executive Summary -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-2xl font-bold text-gray-900 mb-4">
            <i class="fas fa-chart-line text-survey-green mr-2"></i>
            Executive Summary
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div class="bg-blue-50 rounded-lg p-4">
                <p class="text-sm font-medium text-blue-800 mb-2">Total Responses</p>
                <p class="text-4xl font-bold text-blue-900">{{ total_responses }}</p>
                <p class="text-xs text-blue-600 mt-1">Across all surveys</p>
            </div>

            <div class="bg-green-50 rounded-lg p-4">
                <p class="text-sm font-medium text-green-800 mb-2">Participation Rate</p>
                <p class="text-4xl font-bold text-green-900">{{ participation_rate }}%</p>
                <p class="text-xs text-green-600 mt-1">Expected vs actual</p>
            </div>

            <div class="bg-purple-50 rounded-lg p-4">
                <p class="text-sm font-medium text-purple-800 mb-2">Latest Activity</p>
                <p class="text-2xl font-bold text-purple-900">
                    {% if latest_activity_date %}
                        {{ latest_activity_date.strftime('%b %d, %Y') }}
                    {% else %}
                        N/A
                    {% endif %}
                </p>
                <p class="text-xs text-purple-600 mt-1">Most recent submission</p>
            </div>
        </div>

        {% if key_insights %}
        <div class="border-t border-gray-200 pt-4">
            <h3 class="text-lg font-semibold text-gray-900 mb-3">Key Insights</h3>
            <ul class="space-y-2">
                {% for insight in key_insights %}
                <li class="flex items-start">
                    <i class="fas fa-check-circle text-green-600 mr-2 mt-1"></i>
                    <span class="text-sm text-gray-700">{{ insight }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <!-- Survey Completion Timeline -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-2xl font-bold text-gray-900 mb-4">
            <i class="fas fa-clock text-survey-orange mr-2"></i>
            Survey Completion Timeline
        </h2>

        <div class="space-y-4">
            {% for survey in surveys %}
            <div class="flex items-center {% if survey.status == 'pending' %}opacity-50{% endif %}">
                <div class="flex-shrink-0 w-40">
                    <span class="text-sm font-medium text-gray-700">{{ survey.survey_label }}</span>
                </div>
                <div class="flex-grow relative">
                    <div class="flex items-center">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center z-10
                            {% if survey.status == 'complete' %}
                                {% if survey.icon_color == 'blue' %}bg-blue-100{% endif %}
                                {% if survey.icon_color == 'purple' %}bg-purple-100{% endif %}
                                {% if survey.icon_color == 'green' %}bg-green-100{% endif %}
                                {% if survey.icon_color == 'gray' %}bg-gray-200{% endif %}
                            {% else %}
                                bg-gray-200
                            {% endif %}">
                            {% if survey.status == 'complete' %}
                                <i class="fas fa-check-circle text-xl
                                    {% if survey.icon_color == 'blue' %}text-blue-600{% endif %}
                                    {% if survey.icon_color == 'purple' %}text-purple-600{% endif %}
                                    {% if survey.icon_color == 'green' %}text-green-600{% endif %}
                                    {% if survey.icon_color == 'gray' %}text-gray-600{% endif %}"></i>
                            {% else %}
                                <i class="fas fa-clock text-gray-500 text-xl"></i>
                            {% endif %}
                        </div>
                        <div class="flex-grow h-1 ml-2
                            {% if survey.status == 'complete' %}
                                {% if survey.icon_color == 'blue' %}bg-blue-200{% endif %}
                                {% if survey.icon_color == 'purple' %}bg-purple-200{% endif %}
                                {% if survey.icon_color == 'green' %}bg-green-200{% endif %}
                                {% if survey.icon_color == 'gray' %}bg-gray-200{% endif %}
                            {% else %}
                                bg-gray-200
                            {% endif %}"></div>
                    </div>
                    <p class="text-xs text-gray-600 mt-1 ml-12">
                        {% if survey.status == 'complete' %}
                            {{ survey.completion_date[:10] if survey.completion_date else 'Date N/A' }} - {{ survey.submitter_name or 'Name N/A' }}
                        {% else %}
                            Pending
                        {% endif %}
                    </p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Team Members & Contacts -->
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900 flex items-center">
                <i class="fas fa-users text-survey-purple mr-3"></i>
                Team Members
            </h2>
        </div>

        {% if contacts %}
        <div class="divide-y divide-gray-200">
            {% for contact in contacts %}
            <div class="p-6 hover:bg-gray-50 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center
                            {% if contact.survey_type == 'ceo' %}bg-blue-100
                            {% elif contact.survey_type == 'tech' %}bg-purple-100
                            {% elif contact.survey_type == 'staff' %}bg-green-100
                            {% else %}bg-gray-100{% endif %}">
                            {% if contact.survey_type == 'ceo' %}
                            <i class="fas fa-user-tie text-blue-600 text-lg"></i>
                            {% elif contact.survey_type == 'tech' %}
                            <i class="fas fa-laptop-code text-purple-600 text-lg"></i>
                            {% elif contact.survey_type == 'staff' %}
                            <i class="fas fa-user text-green-600 text-lg"></i>
                            {% else %}
                            <i class="fas fa-user text-gray-600 text-lg"></i>
                            {% endif %}
                        </div>

                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">{{ contact.name }}</h3>
                            <p class="text-sm text-gray-600">{{ contact.role }}</p>
                            <p class="text-xs text-gray-500 mt-1">
                                <i class="fas fa-envelope mr-1"></i>{{ contact.email }}
                            </p>
                        </div>
                    </div>

                    {% if contact.survey_completed %}
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                        <i class="fas fa-check-circle mr-2"></i>Survey Complete
                    </span>
                    {% else %}
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                        <i class="fas fa-clock mr-2"></i>Pending
                    </span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="p-6 text-center text-gray-500">
            <p>No contact information available.</p>
        </div>
        {% endif %}
    </div>

    <!-- Intake Information -->
    {% if intake_data %}
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900 flex items-center">
                <i class="fas fa-clipboard-list text-survey-orange mr-3"></i>
                Organization Profile
            </h2>
        </div>
        <div class="p-6 space-y-6">
            {% for key, value in intake_data.items() %}
            {% if value and key not in ['Date', 'Organization Name:', 'Primary Contact Name', 'Email'] %}
            <div class="border-l-4 border-survey-blue pl-4">
                <h4 class="text-sm font-semibold text-gray-700 mb-2">{{ key }}</h4>
                <p class="text-sm text-gray-900">{{ value }}</p>
            </div>
            {% endif %}
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block scripts %}
<style>
@media print {
    .no-print { display: none !important; }
    nav, footer { display: none !important; }
    body { background: white !important; }
}
</style>
{% endblock %}
```

### Step 4: Test (10 minutes)

```bash
# Start your Flask app
python app.py

# Visit in browser
http://localhost:8080/report/org/[Organization Name]

# Example (replace with actual org name from your data):
http://localhost:8080/report/org/Acme%20Corporation
```

---

## Troubleshooting

### "Organization not found" error

**Cause:** Organization name doesn't match exactly

**Solution:**
```python
# Check available organizations
from sheets_reader import get_all_tabs
tabs = get_all_tabs()
intake_data = tabs.get('intake', [])
org_names = [row.get('Organization Name:', '').strip() for row in intake_data if row.get('Organization Name:', '').strip()]
print(org_names)
```

### Template not rendering

**Cause:** Missing `simple_base.html` or incorrect template path

**Solution:**
- Verify `templates/simple_base.html` exists
- Check Flask template folder configuration

### No data showing

**Cause:** `sheets_reader.py` not returning data

**Solution:**
```python
from sheets_reader import get_all_tabs
tabs = get_all_tabs()
print(f"Intake records: {len(tabs.get('intake', []))}")
print(f"CEO records: {len(tabs.get('ceo', []))}")
```

---

## Next Steps

### Add Report Link to Organization Detail Page

In `templates/organization_detail.html`, add:

```html
<div class="bg-white rounded-lg shadow-md p-6">
    <a href="/report/org/{{ org_name }}"
       class="inline-flex items-center px-4 py-2 bg-survey-blue text-white rounded-md hover:bg-blue-700 transition-colors">
        <i class="fas fa-file-alt mr-2"></i>
        Generate Full Report
    </a>
</div>
```

### Add Report Link to Home Dashboard

In `templates/simple_home.html`, add navigation button:

```html
<a href="/report/aggregate"
   class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
    <i class="fas fa-chart-bar mr-2"></i>
    View Aggregate Report
</a>
```

---

## Estimated Timeline

- **Basic Per-Org Report:** 1-2 hours
- **Aggregate Report:** 2-3 hours
- **PDF Export:** 2-3 hours
- **Polish & Testing:** 1-2 hours

**Total:** 6-10 hours for complete implementation

---

## Resources

- **Full Specifications:** See `REPORT_DESIGN_SPECIFICATIONS.md`
- **Analysis Summary:** See `REPORT_ANALYSIS_SUMMARY.md`
- **Existing Code:** Reference `app.py` and `simple_app.py`
- **Design Patterns:** Reference `templates/organization_detail.html`

---

## Support

If you encounter issues:

1. Check error messages in Flask console
2. Verify data structure with `sheets_reader.get_all_tabs()`
3. Review template syntax for Jinja2 errors
4. Test with known good organization name

---

**Happy Reporting!**
