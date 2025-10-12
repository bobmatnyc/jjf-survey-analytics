# Report Design Specifications for JJF Survey Analytics

**Document Version:** 1.0.0
**Date:** 2025-10-11
**Purpose:** Define comprehensive reporting structure for per-organization and aggregate survey analytics

---

## Executive Summary

This document provides detailed specifications for implementing two types of comprehensive reports for the JJF Survey Analytics platform:

1. **Per-Organization Reports** - Individual detailed reports for each organization
2. **Aggregate Report** - Summary report across all participating organizations

The design follows the existing platform's design patterns, Tailwind CSS styling, and data architecture.

---

## Table of Contents

1. [Design System & Visual Patterns](#design-system--visual-patterns)
2. [Per-Organization Report Structure](#per-organization-report-structure)
3. [Aggregate Report Structure](#aggregate-report-structure)
4. [Data Requirements](#data-requirements)
5. [Implementation Specifications](#implementation-specifications)
6. [Code Templates](#code-templates)

---

## Design System & Visual Patterns

### Color Palette

```javascript
// Existing Tailwind Config (from simple_base.html)
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'survey-blue': '#1e40af',      // Primary actions, CEO surveys
                'survey-green': '#059669',      // Success, completion, staff surveys
                'survey-purple': '#7c3aed',     // Tech surveys, secondary actions
                'survey-orange': '#ea580c'      // Warnings, highlights
            }
        }
    }
}
```

### Typography Hierarchy

```css
/* Headers */
h1: text-3xl font-bold text-gray-900        /* Main page title */
h2: text-2xl font-bold text-gray-900        /* Section headers */
h3: text-xl font-semibold text-gray-900     /* Subsection headers */
h4: text-lg font-semibold text-gray-900     /* Card titles */

/* Body Text */
p: text-sm text-gray-600                    /* Standard body */
small: text-xs text-gray-500                /* Supporting text */
```

### Layout Patterns

1. **Card Container Pattern**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <!-- Content -->
</div>
```

2. **Metric Card Pattern**
```html
<div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-sm font-medium text-gray-500 mb-1">Metric Label</p>
            <p class="text-3xl font-bold text-gray-900">42</p>
            <p class="text-xs text-gray-500 mt-1">Supporting text</p>
        </div>
        <div class="w-12 h-12 bg-survey-blue bg-opacity-10 rounded-lg flex items-center justify-center">
            <i class="fas fa-icon text-survey-blue text-2xl"></i>
        </div>
    </div>
</div>
```

3. **Data Table Pattern**
```html
<table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-50">
        <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Column Header
            </th>
        </tr>
    </thead>
    <tbody class="bg-white divide-y divide-gray-200">
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm text-gray-900">Data</td>
        </tr>
    </tbody>
</table>
```

4. **Badge Pattern**
```html
<!-- Status Badge -->
<span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
    <i class="fas fa-check-circle mr-2"></i>
    Complete
</span>
```

### Animation & Interaction

```css
/* Fade-in animation for page load */
.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Hover scale effect for cards */
.hover-scale {
    transition: transform 0.2s ease-in-out;
}

.hover-scale:hover {
    transform: scale(1.02);
}
```

---

## Per-Organization Report Structure

### Report Sections (In Order)

#### 1. Report Header & Organization Identity

**Purpose:** Provide clear organization identification and report metadata

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-survey-blue mb-8">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-3xl font-bold text-gray-900 flex items-center mb-2">
                <i class="fas fa-building text-survey-blue mr-3"></i>
                [Organization Name]
            </h1>
            <p class="text-sm text-gray-600">
                <i class="fas fa-calendar-alt mr-2"></i>
                Report Generated: [Date]
            </p>
        </div>
        <div class="text-right">
            <div class="text-3xl font-bold text-survey-blue">[XX]%</div>
            <div class="text-sm text-gray-600">Survey Completion</div>
            <div class="text-xs text-gray-500 mt-1">[X]/4 surveys complete</div>
        </div>
    </div>
</div>
```

**Data Fields:**
- `organization_name` (string)
- `report_date` (datetime)
- `completion_percentage` (integer 0-100)
- `surveys_completed` (integer)
- `total_surveys` (integer, always 4: Intake, CEO, Tech Lead, Staff)

---

#### 2. Executive Summary

**Purpose:** High-level overview of participation and key insights

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-4">
        <i class="fas fa-chart-line text-survey-green mr-2"></i>
        Executive Summary
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <!-- Total Responses -->
        <div class="bg-blue-50 rounded-lg p-4">
            <p class="text-sm font-medium text-blue-800 mb-2">Total Responses</p>
            <p class="text-4xl font-bold text-blue-900">[X]</p>
            <p class="text-xs text-blue-600 mt-1">Across all surveys</p>
        </div>

        <!-- Participation Rate -->
        <div class="bg-green-50 rounded-lg p-4">
            <p class="text-sm font-medium text-green-800 mb-2">Participation Rate</p>
            <p class="text-4xl font-bold text-green-900">[XX]%</p>
            <p class="text-xs text-green-600 mt-1">Expected vs actual</p>
        </div>

        <!-- Last Activity -->
        <div class="bg-purple-50 rounded-lg p-4">
            <p class="text-sm font-medium text-purple-800 mb-2">Latest Activity</p>
            <p class="text-2xl font-bold text-purple-900">[Date]</p>
            <p class="text-xs text-purple-600 mt-1">Most recent submission</p>
        </div>
    </div>

    <!-- Key Insights -->
    <div class="border-t border-gray-200 pt-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">Key Insights</h3>
        <ul class="space-y-2">
            <li class="flex items-start">
                <i class="fas fa-check-circle text-green-600 mr-2 mt-1"></i>
                <span class="text-sm text-gray-700">[Auto-generated insight 1]</span>
            </li>
            <li class="flex items-start">
                <i class="fas fa-check-circle text-green-600 mr-2 mt-1"></i>
                <span class="text-sm text-gray-700">[Auto-generated insight 2]</span>
            </li>
            <li class="flex items-start">
                <i class="fas fa-exclamation-circle text-orange-600 mr-2 mt-1"></i>
                <span class="text-sm text-gray-700">[Auto-generated recommendation]</span>
            </li>
        </ul>
    </div>
</div>
```

**Data Fields:**
- `total_responses` (integer)
- `participation_rate` (integer 0-100)
- `latest_activity_date` (datetime)
- `key_insights[]` (array of strings, auto-generated)

**Insight Generation Logic:**
```python
def generate_insights(org_data):
    insights = []

    # Completion insights
    if org_data['completion_percentage'] == 100:
        insights.append("All surveys completed - comprehensive data available")
    elif org_data['completion_percentage'] >= 75:
        insights.append("Strong participation across most surveys")
    else:
        insights.append("Additional survey responses would enhance analysis")

    # Timing insights
    days_since_intake = (datetime.now() - org_data['intake_date']).days
    if days_since_intake <= 7 and org_data['completion_percentage'] >= 75:
        insights.append("Rapid response time demonstrates strong engagement")

    # Missing surveys
    if not org_data['has_ceo_survey']:
        insights.append("Leadership perspective needed - CEO survey pending")
    if not org_data['has_tech_survey']:
        insights.append("Technical assessment incomplete - Tech Lead survey pending")
    if not org_data['has_staff_survey']:
        insights.append("Staff perspective would enhance comprehensive view")

    return insights
```

---

#### 3. Survey Completion Timeline

**Purpose:** Visualize survey completion sequence and identify gaps

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-4">
        <i class="fas fa-clock text-survey-orange mr-2"></i>
        Survey Completion Timeline
    </h2>

    <div class="space-y-4">
        <!-- Intake Survey -->
        <div class="flex items-center">
            <div class="flex-shrink-0 w-32">
                <span class="text-sm font-medium text-gray-700">Intake</span>
            </div>
            <div class="flex-grow relative">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center z-10">
                        <i class="fas fa-check-circle text-green-600 text-xl"></i>
                    </div>
                    <div class="flex-grow h-1 bg-green-200 ml-2"></div>
                </div>
                <p class="text-xs text-gray-600 mt-1 ml-12">[Date] - [Submitter Name]</p>
            </div>
        </div>

        <!-- CEO Survey -->
        <div class="flex items-center">
            <div class="flex-shrink-0 w-32">
                <span class="text-sm font-medium text-gray-700">CEO Survey</span>
            </div>
            <div class="flex-grow relative">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center z-10">
                        <i class="fas fa-check-circle text-blue-600 text-xl"></i>
                    </div>
                    <div class="flex-grow h-1 bg-blue-200 ml-2"></div>
                </div>
                <p class="text-xs text-gray-600 mt-1 ml-12">[Date] - [CEO Name]</p>
            </div>
        </div>

        <!-- Tech Lead Survey -->
        <div class="flex items-center">
            <div class="flex-shrink-0 w-32">
                <span class="text-sm font-medium text-gray-700">Tech Lead</span>
            </div>
            <div class="flex-grow relative">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center z-10">
                        <i class="fas fa-check-circle text-purple-600 text-xl"></i>
                    </div>
                    <div class="flex-grow h-1 bg-purple-200 ml-2"></div>
                </div>
                <p class="text-xs text-gray-600 mt-1 ml-12">[Date] - [Tech Lead Name]</p>
            </div>
        </div>

        <!-- Staff Survey (Pending State Example) -->
        <div class="flex items-center opacity-50">
            <div class="flex-shrink-0 w-32">
                <span class="text-sm font-medium text-gray-700">Staff Survey</span>
            </div>
            <div class="flex-grow relative">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center z-10">
                        <i class="fas fa-clock text-gray-500 text-xl"></i>
                    </div>
                    <div class="flex-grow h-1 bg-gray-200 ml-2"></div>
                </div>
                <p class="text-xs text-gray-600 mt-1 ml-12">Pending</p>
            </div>
        </div>
    </div>
</div>
```

**Data Fields:**
- `surveys[]` array with:
  - `survey_type` (string: 'intake', 'ceo', 'tech_lead', 'staff')
  - `status` (string: 'complete', 'pending')
  - `completion_date` (datetime, null if pending)
  - `submitter_name` (string)
  - `submitter_email` (string)

---

#### 4. Team Members & Contacts

**Purpose:** Display all team members associated with organization

**Design:**
```html
<div class="bg-white rounded-lg shadow-md overflow-hidden mb-8">
    <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900 flex items-center">
            <i class="fas fa-users text-survey-purple mr-3"></i>
            Team Members
        </h2>
    </div>

    <div class="divide-y divide-gray-200">
        {% for contact in contacts %}
        <div class="p-6 hover:bg-gray-50 transition-colors">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <!-- Avatar -->
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user-tie text-blue-600 text-lg"></i>
                    </div>

                    <!-- Contact Info -->
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900">[Name]</h3>
                        <p class="text-sm text-gray-600">[Role/Title]</p>
                        <p class="text-xs text-gray-500 mt-1">
                            <i class="fas fa-envelope mr-1"></i>[Email]
                        </p>
                    </div>
                </div>

                <!-- Survey Status Badge -->
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    <i class="fas fa-check-circle mr-2"></i>Survey Complete
                </span>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

**Data Fields:**
- `contacts[]` array with:
  - `name` (string)
  - `role` (string)
  - `email` (string)
  - `survey_type` (string)
  - `survey_completed` (boolean)
  - `completion_date` (datetime, optional)

---

#### 5. Intake Information Highlights

**Purpose:** Display key information from intake survey

**Design:**
```html
<div class="bg-white rounded-lg shadow-md overflow-hidden mb-8">
    <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900 flex items-center">
            <i class="fas fa-clipboard-list text-survey-orange mr-3"></i>
            Organization Profile
        </h2>
    </div>

    <div class="p-6 space-y-6">
        <!-- AI Usage -->
        <div class="border-l-4 border-survey-blue pl-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">AI Usage Status</h4>
            <p class="text-sm text-gray-900">[AI usage description]</p>
        </div>

        <!-- AI Policy -->
        <div class="border-l-4 border-survey-purple pl-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">AI Policy</h4>
            <p class="text-sm text-gray-900">[AI policy status]</p>
        </div>

        <!-- Technology Priorities -->
        <div class="border-l-4 border-survey-green pl-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Technology Priorities</h4>
            <p class="text-sm text-gray-900 italic">"[Quoted text from intake]"</p>
        </div>

        <!-- Comments/Suggestions -->
        <div class="border-l-4 border-survey-orange pl-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">Comments & Suggestions</h4>
            <p class="text-sm text-gray-900 italic">"[Quoted comments]"</p>
        </div>
    </div>
</div>
```

**Data Fields:**
- `ai_usage` (string)
- `ai_policy` (string)
- `technology_priorities` (text)
- `comments` (text)
- Additional intake fields based on survey structure

---

#### 6. Survey Responses Summary

**Purpose:** Provide detailed view of all survey responses

**Design:**
```html
<div class="bg-white rounded-lg shadow-md overflow-hidden mb-8">
    <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h2 class="text-2xl font-bold text-gray-900 flex items-center">
            <i class="fas fa-list-alt text-survey-blue mr-3"></i>
            Survey Responses
        </h2>
    </div>

    <!-- CEO Survey Section -->
    <div class="border-b border-gray-200">
        <div class="px-6 py-4 bg-blue-50">
            <h3 class="text-lg font-semibold text-blue-900 flex items-center">
                <i class="fas fa-user-tie text-blue-600 mr-2"></i>
                CEO Survey Responses
            </h3>
        </div>
        <div class="p-6 space-y-4">
            {% for question, answer in ceo_responses %}
            <div class="border-b border-gray-100 pb-4">
                <p class="text-sm font-medium text-gray-700 mb-2">[Question]</p>
                <p class="text-sm text-gray-900 pl-4">[Answer]</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Tech Lead Survey Section -->
    <div class="border-b border-gray-200">
        <div class="px-6 py-4 bg-purple-50">
            <h3 class="text-lg font-semibold text-purple-900 flex items-center">
                <i class="fas fa-laptop-code text-purple-600 mr-2"></i>
                Tech Lead Survey Responses
            </h3>
        </div>
        <div class="p-6 space-y-4">
            {% for question, answer in tech_responses %}
            <div class="border-b border-gray-100 pb-4">
                <p class="text-sm font-medium text-gray-700 mb-2">[Question]</p>
                <p class="text-sm text-gray-900 pl-4">[Answer]</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Staff Survey Section -->
    <div>
        <div class="px-6 py-4 bg-green-50">
            <h3 class="text-lg font-semibold text-green-900 flex items-center">
                <i class="fas fa-users text-green-600 mr-2"></i>
                Staff Survey Responses
            </h3>
        </div>
        <div class="p-6 space-y-4">
            {% for question, answer in staff_responses %}
            <div class="border-b border-gray-100 pb-4">
                <p class="text-sm font-medium text-gray-700 mb-2">[Question]</p>
                <p class="text-sm text-gray-900 pl-4">[Answer]</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

**Data Fields:**
- `ceo_responses[]` (array of question/answer pairs)
- `tech_responses[]` (array of question/answer pairs)
- `staff_responses[]` (array of question/answer pairs)
- Each response includes:
  - `question_text` (string)
  - `answer_text` (string)
  - `question_type` (string: 'text', 'numeric', 'boolean', 'date')

---

#### 7. Export & Actions Footer

**Purpose:** Provide report actions and export functionality

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-sm text-gray-600">Report Generated: [Timestamp]</p>
            <p class="text-xs text-gray-500 mt-1">JJF Survey Analytics Platform</p>
        </div>
        <div class="flex space-x-3">
            <button onclick="window.print()"
                    class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
                <i class="fas fa-print mr-2"></i>Print Report
            </button>
            <button onclick="exportPDF()"
                    class="px-4 py-2 bg-survey-blue text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
                <i class="fas fa-file-pdf mr-2"></i>Export PDF
            </button>
        </div>
    </div>
</div>
```

---

## Aggregate Report Structure

### Report Sections (In Order)

#### 1. Report Header

**Purpose:** Identify report type and date range

**Design:**
```html
<div class="bg-gradient-to-r from-survey-blue to-blue-700 text-white rounded-lg shadow-md p-8 mb-8">
    <h1 class="text-4xl font-bold mb-2">
        <i class="fas fa-chart-bar mr-3"></i>
        Aggregate Survey Analytics Report
    </h1>
    <p class="text-blue-100 text-lg">
        Comprehensive Analysis Across All Participating Organizations
    </p>
    <div class="mt-4 flex items-center space-x-6">
        <div>
            <p class="text-sm text-blue-100">Report Period</p>
            <p class="text-lg font-semibold">[Start Date] - [End Date]</p>
        </div>
        <div>
            <p class="text-sm text-blue-100">Generated</p>
            <p class="text-lg font-semibold">[Report Date]</p>
        </div>
    </div>
</div>
```

---

#### 2. Overview Metrics

**Purpose:** High-level statistics across all organizations

**Design:**
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Total Organizations -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <p class="text-sm font-medium text-gray-500">Organizations</p>
                <p class="text-4xl font-bold text-gray-900">[X]</p>
            </div>
            <i class="fas fa-building text-4xl text-gray-300"></i>
        </div>
        <div class="text-xs text-gray-600">
            <span class="font-semibold text-green-600">[X]</span> fully complete
        </div>
    </div>

    <!-- Total Responses -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <p class="text-sm font-medium text-gray-500">Total Responses</p>
                <p class="text-4xl font-bold text-gray-900">[XXX]</p>
            </div>
            <i class="fas fa-clipboard-check text-4xl text-blue-300"></i>
        </div>
        <div class="text-xs text-gray-600">
            Across all surveys
        </div>
    </div>

    <!-- Average Completion -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <p class="text-sm font-medium text-gray-500">Avg Completion</p>
                <p class="text-4xl font-bold text-gray-900">[XX]%</p>
            </div>
            <i class="fas fa-percentage text-4xl text-green-300"></i>
        </div>
        <div class="text-xs text-gray-600">
            Per organization
        </div>
    </div>

    <!-- Response Rate -->
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <p class="text-sm font-medium text-gray-500">Response Rate</p>
                <p class="text-4xl font-bold text-gray-900">[XX]%</p>
            </div>
            <i class="fas fa-chart-line text-4xl text-purple-300"></i>
        </div>
        <div class="text-xs text-gray-600">
            Expected vs actual
        </div>
    </div>
</div>
```

**Data Fields:**
- `total_organizations` (integer)
- `fully_complete_count` (integer)
- `total_responses` (integer)
- `average_completion_percentage` (float)
- `overall_response_rate` (float)

---

#### 3. Survey Type Breakdown

**Purpose:** Show completion statistics by survey type

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-6">
        <i class="fas fa-chart-pie text-survey-green mr-2"></i>
        Survey Completion by Type
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Intake -->
        <div class="border-l-4 border-gray-500 pl-4">
            <p class="text-sm font-medium text-gray-600 mb-2">Intake Surveys</p>
            <p class="text-3xl font-bold text-gray-900 mb-2">[X]/[Y]</p>
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div class="bg-gray-500 h-2 rounded-full" style="width: [XX]%"></div>
            </div>
            <p class="text-xs text-gray-600">[XX]% complete</p>
        </div>

        <!-- CEO -->
        <div class="border-l-4 border-blue-500 pl-4">
            <p class="text-sm font-medium text-gray-600 mb-2">CEO Surveys</p>
            <p class="text-3xl font-bold text-blue-900 mb-2">[X]/[Y]</p>
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div class="bg-blue-500 h-2 rounded-full" style="width: [XX]%"></div>
            </div>
            <p class="text-xs text-gray-600">[XX]% complete</p>
        </div>

        <!-- Tech Lead -->
        <div class="border-l-4 border-purple-500 pl-4">
            <p class="text-sm font-medium text-gray-600 mb-2">Tech Lead Surveys</p>
            <p class="text-3xl font-bold text-purple-900 mb-2">[X]/[Y]</p>
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div class="bg-purple-500 h-2 rounded-full" style="width: [XX]%"></div>
            </div>
            <p class="text-xs text-gray-600">[XX]% complete</p>
        </div>

        <!-- Staff -->
        <div class="border-l-4 border-green-500 pl-4">
            <p class="text-sm font-medium text-gray-600 mb-2">Staff Surveys</p>
            <p class="text-3xl font-bold text-green-900 mb-2">[X]/[Y]</p>
            <div class="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div class="bg-green-500 h-2 rounded-full" style="width: [XX]%"></div>
            </div>
            <p class="text-xs text-gray-600">[XX]% complete</p>
        </div>
    </div>
</div>
```

**Data Fields:**
- Per survey type:
  - `completed_count` (integer)
  - `expected_count` (integer)
  - `completion_percentage` (float)

---

#### 4. Participation Timeline

**Purpose:** Show response activity over time

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-6">
        <i class="fas fa-calendar-alt text-survey-orange mr-2"></i>
        Participation Timeline
    </h2>

    <!-- Week-by-Week Breakdown -->
    <div class="space-y-3">
        {% for week in timeline_weeks %}
        <div class="flex items-center">
            <div class="w-32 text-sm font-medium text-gray-700">[Week Range]</div>
            <div class="flex-grow">
                <div class="flex items-center">
                    <div class="flex-grow bg-gray-200 rounded-full h-8">
                        <div class="bg-survey-blue h-8 rounded-full flex items-center justify-end pr-3"
                             style="width: [XX]%">
                            <span class="text-xs font-semibold text-white">[X] responses</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Peak Activity Callout -->
    <div class="mt-6 bg-blue-50 border-l-4 border-survey-blue p-4">
        <p class="text-sm font-medium text-blue-900">
            <i class="fas fa-info-circle mr-2"></i>
            Peak activity: [XX] responses during week of [Date]
        </p>
    </div>
</div>
```

**Data Fields:**
- `timeline_weeks[]` array with:
  - `week_start_date` (date)
  - `week_end_date` (date)
  - `response_count` (integer)
  - `percentage_of_total` (float)

---

#### 5. Organization Completion Status Table

**Purpose:** Provide sortable, filterable organization list

**Design:**
```html
<div class="bg-white rounded-lg shadow-md overflow-hidden mb-8">
    <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-gray-900 flex items-center">
                <i class="fas fa-building text-survey-purple mr-3"></i>
                Organization Status
            </h2>
            <div class="flex space-x-2">
                <button onclick="filterComplete()"
                        class="px-3 py-1 text-xs font-medium rounded bg-green-100 text-green-800 hover:bg-green-200">
                    <i class="fas fa-check mr-1"></i>Complete Only
                </button>
                <button onclick="filterIncomplete()"
                        class="px-3 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
                    <i class="fas fa-clock mr-1"></i>In Progress
                </button>
                <button onclick="clearFilters()"
                        class="px-3 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800 hover:bg-gray-200">
                    <i class="fas fa-times mr-1"></i>Clear
                </button>
            </div>
        </div>
    </div>

    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Organization
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Completion
                    </th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <i class="fas fa-clipboard mr-1"></i> Intake
                    </th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <i class="fas fa-user-tie mr-1"></i> CEO
                    </th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <i class="fas fa-laptop-code mr-1"></i> Tech
                    </th>
                    <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <i class="fas fa-users mr-1"></i> Staff
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Activity
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for org in organizations %}
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4">
                        <a href="/report/org/{{ org.name }}"
                           class="text-sm font-semibold text-survey-blue hover:underline">
                            {{ org.name }}
                        </a>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex items-center">
                            <span class="text-sm font-bold text-gray-900 mr-2">{{ org.completion_pct }}%</span>
                            <div class="w-20 bg-gray-200 rounded-full h-2">
                                <div class="h-2 rounded-full
                                    {% if org.completion_pct == 100 %}bg-green-500
                                    {% elif org.completion_pct >= 75 %}bg-blue-500
                                    {% elif org.completion_pct >= 50 %}bg-yellow-500
                                    {% else %}bg-orange-500{% endif %}"
                                     style="width: {{ org.completion_pct }}%"></div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4 text-center">
                        {% if org.has_intake %}
                        <i class="fas fa-check-circle text-green-600 text-lg"></i>
                        {% else %}
                        <i class="fas fa-clock text-gray-400 text-lg"></i>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-center">
                        {% if org.has_ceo %}
                        <i class="fas fa-check-circle text-blue-600 text-lg"></i>
                        {% else %}
                        <i class="fas fa-clock text-gray-400 text-lg"></i>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-center">
                        {% if org.has_tech %}
                        <i class="fas fa-check-circle text-purple-600 text-lg"></i>
                        {% else %}
                        <i class="fas fa-clock text-gray-400 text-lg"></i>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-center">
                        {% if org.has_staff %}
                        <i class="fas fa-check-circle text-green-600 text-lg"></i>
                        {% else %}
                        <i class="fas fa-clock text-gray-400 text-lg"></i>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">
                        {{ org.last_activity_date }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
```

**Data Fields:**
- `organizations[]` array with:
  - `name` (string)
  - `completion_percentage` (integer)
  - `has_intake` (boolean)
  - `has_ceo` (boolean)
  - `has_tech` (boolean)
  - `has_staff` (boolean)
  - `last_activity_date` (date)

---

#### 6. Key Insights & Trends

**Purpose:** Highlight aggregate patterns and insights

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-6">
        <i class="fas fa-lightbulb text-yellow-500 mr-2"></i>
        Key Insights & Trends
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- AI Adoption Insight -->
        <div class="bg-blue-50 border-l-4 border-blue-500 p-4">
            <h3 class="text-lg font-semibold text-blue-900 mb-2">
                <i class="fas fa-robot mr-2"></i>AI Adoption
            </h3>
            <p class="text-sm text-blue-800 mb-2">
                [XX]% of organizations actively using AI tools
            </p>
            <p class="text-xs text-blue-700">
                [Additional insight about AI usage patterns]
            </p>
        </div>

        <!-- Policy Status -->
        <div class="bg-purple-50 border-l-4 border-purple-500 p-4">
            <h3 class="text-lg font-semibold text-purple-900 mb-2">
                <i class="fas fa-file-contract mr-2"></i>Policy Status
            </h3>
            <p class="text-sm text-purple-800 mb-2">
                [XX]% have formal AI policies in place
            </p>
            <p class="text-xs text-purple-700">
                [Additional insight about policy trends]
            </p>
        </div>

        <!-- Technology Maturity -->
        <div class="bg-green-50 border-l-4 border-green-500 p-4">
            <h3 class="text-lg font-semibold text-green-900 mb-2">
                <i class="fas fa-chart-line mr-2"></i>Tech Maturity
            </h3>
            <p class="text-sm text-green-800 mb-2">
                Average maturity score: [X.X]/5.0
            </p>
            <p class="text-xs text-green-700">
                [Additional insight about maturity distribution]
            </p>
        </div>

        <!-- Participation Trends -->
        <div class="bg-orange-50 border-l-4 border-orange-500 p-4">
            <h3 class="text-lg font-semibold text-orange-900 mb-2">
                <i class="fas fa-users mr-2"></i>Participation
            </h3>
            <p class="text-sm text-orange-800 mb-2">
                [XX]% complete within first week
            </p>
            <p class="text-xs text-orange-700">
                [Additional insight about response timing]
            </p>
        </div>
    </div>
</div>
```

**Data Fields:**
- Aggregate statistics:
  - `ai_adoption_percentage` (float)
  - `policy_adoption_percentage` (float)
  - `average_tech_maturity` (float)
  - `quick_completion_percentage` (float)

---

#### 7. Recommendations & Next Steps

**Purpose:** Provide actionable recommendations based on data

**Design:**
```html
<div class="bg-white rounded-lg shadow-md p-6 mb-8">
    <h2 class="text-2xl font-bold text-gray-900 mb-6">
        <i class="fas fa-tasks text-survey-green mr-2"></i>
        Recommendations & Next Steps
    </h2>

    <div class="space-y-4">
        <!-- High Priority -->
        <div class="border-l-4 border-red-500 pl-4 py-2">
            <p class="text-sm font-semibold text-red-900 mb-1">
                <i class="fas fa-exclamation-circle mr-2"></i>High Priority
            </p>
            <p class="text-sm text-gray-700">
                [X] organizations pending staff surveys - target for follow-up
            </p>
        </div>

        <!-- Medium Priority -->
        <div class="border-l-4 border-yellow-500 pl-4 py-2">
            <p class="text-sm font-semibold text-yellow-900 mb-1">
                <i class="fas fa-info-circle mr-2"></i>Medium Priority
            </p>
            <p class="text-sm text-gray-700">
                Consider targeted outreach to [X] organizations with partial completion
            </p>
        </div>

        <!-- Opportunities -->
        <div class="border-l-4 border-green-500 pl-4 py-2">
            <p class="text-sm font-semibold text-green-900 mb-1">
                <i class="fas fa-check-circle mr-2"></i>Opportunities
            </p>
            <p class="text-sm text-gray-700">
                [X] organizations show high AI adoption - potential case studies
            </p>
        </div>
    </div>
</div>
```

---

## Data Requirements

### Database Queries for Per-Organization Report

```python
def get_organization_report_data(org_name: str) -> Dict[str, Any]:
    """
    Fetch all data required for a per-organization report.

    Args:
        org_name: Organization name

    Returns:
        Dictionary containing all report sections
    """

    # Get intake data
    intake_data = get_intake_by_org(org_name)

    # Get CEO survey data
    ceo_data = get_ceo_survey_by_org(org_name)

    # Get tech lead survey data
    tech_data = get_tech_survey_by_org(org_name)

    # Get staff survey data
    staff_data = get_staff_survey_by_org(org_name)

    # Calculate completion metrics
    surveys_completed = sum([
        1 if intake_data else 0,
        1 if ceo_data else 0,
        1 if tech_data else 0,
        1 if staff_data else 0
    ])
    completion_pct = int((surveys_completed / 4) * 100)

    # Build contacts list
    contacts = []
    if intake_data:
        contacts.append({
            'name': intake_data.get('Primary Contact', ''),
            'email': intake_data.get('Email', ''),
            'role': 'Primary Contact',
            'survey_type': 'intake',
            'survey_completed': True,
            'completion_date': intake_data.get('Date', '')
        })

    if ceo_data:
        contacts.append({
            'name': ceo_data.get('CEO Name', ''),
            'email': ceo_data.get('CEO Email', ''),
            'role': 'CEO',
            'survey_type': 'ceo',
            'survey_completed': True,
            'completion_date': ceo_data.get('Date', '')
        })

    if tech_data:
        contacts.append({
            'name': tech_data.get('Tech Lead Name', ''),
            'email': tech_data.get('Tech Lead Email', ''),
            'role': 'Technology Lead',
            'survey_type': 'tech_lead',
            'survey_completed': True,
            'completion_date': tech_data.get('Date', '')
        })

    if staff_data:
        contacts.append({
            'name': staff_data.get('Staff Name', ''),
            'email': staff_data.get('Staff Email', ''),
            'role': 'Staff Member',
            'survey_type': 'staff',
            'survey_completed': True,
            'completion_date': staff_data.get('Date', '')
        })

    # Get latest activity date
    dates = []
    if intake_data and intake_data.get('Date'):
        dates.append(parse_date(intake_data['Date']))
    if ceo_data and ceo_data.get('Date'):
        dates.append(parse_date(ceo_data['Date']))
    if tech_data and tech_data.get('Date'):
        dates.append(parse_date(tech_data['Date']))
    if staff_data and staff_data.get('Date'):
        dates.append(parse_date(staff_data['Date']))

    latest_activity = max(dates) if dates else None

    # Generate insights
    insights = generate_insights({
        'completion_percentage': completion_pct,
        'intake_date': parse_date(intake_data['Date']) if intake_data else None,
        'has_ceo_survey': bool(ceo_data),
        'has_tech_survey': bool(tech_data),
        'has_staff_survey': bool(staff_data)
    })

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
        'intake_data': intake_data,
        'ceo_data': ceo_data,
        'tech_data': tech_data,
        'staff_data': staff_data,
        'surveys': [
            {
                'survey_type': 'intake',
                'status': 'complete' if intake_data else 'pending',
                'completion_date': intake_data.get('Date') if intake_data else None,
                'submitter_name': intake_data.get('Primary Contact', '') if intake_data else '',
                'submitter_email': intake_data.get('Email', '') if intake_data else ''
            },
            {
                'survey_type': 'ceo',
                'status': 'complete' if ceo_data else 'pending',
                'completion_date': ceo_data.get('Date') if ceo_data else None,
                'submitter_name': ceo_data.get('CEO Name', '') if ceo_data else '',
                'submitter_email': ceo_data.get('CEO Email', '') if ceo_data else ''
            },
            {
                'survey_type': 'tech_lead',
                'status': 'complete' if tech_data else 'pending',
                'completion_date': tech_data.get('Date') if tech_data else None,
                'submitter_name': tech_data.get('Tech Lead Name', '') if tech_data else '',
                'submitter_email': tech_data.get('Tech Lead Email', '') if tech_data else ''
            },
            {
                'survey_type': 'staff',
                'status': 'complete' if staff_data else 'pending',
                'completion_date': staff_data.get('Date') if staff_data else None,
                'submitter_name': staff_data.get('Staff Name', '') if staff_data else '',
                'submitter_email': staff_data.get('Staff Email', '') if staff_data else ''
            }
        ]
    }
```

### Database Queries for Aggregate Report

```python
def get_aggregate_report_data() -> Dict[str, Any]:
    """
    Fetch all data required for aggregate report across all organizations.

    Returns:
        Dictionary containing aggregate statistics and organization list
    """

    # Get all organizations from intake data
    intake_data = get_all_intake_data()
    all_orgs = [row.get('Organization Name:', '').strip() for row in intake_data if row.get('Organization Name:', '').strip()]

    ceo_data = get_all_ceo_data()
    tech_data = get_all_tech_data()
    staff_data = get_all_staff_data()

    # Build organization completion map
    ceo_orgs = {row.get('CEO Organization', '').strip() for row in ceo_data if row.get('CEO Organization', '').strip()}
    tech_orgs = {row.get('Organization', '').strip() for row in tech_data if row.get('Organization', '').strip()}
    staff_orgs = {row.get('Organization', '').strip() for row in staff_data if row.get('Organization', '').strip()}

    # Calculate per-organization stats
    organizations = []
    total_responses = 0
    fully_complete_count = 0

    for org_name in all_orgs:
        has_intake = True  # They're in the intake list
        has_ceo = org_name in ceo_orgs
        has_tech = org_name in tech_orgs
        has_staff = org_name in staff_orgs

        surveys_complete = sum([has_intake, has_ceo, has_tech, has_staff])
        completion_pct = int((surveys_complete / 4) * 100)
        total_responses += surveys_complete

        if surveys_complete == 4:
            fully_complete_count += 1

        # Get latest activity date
        org_intake = next((r for r in intake_data if r.get('Organization Name:', '').strip() == org_name), None)
        org_ceo = next((r for r in ceo_data if r.get('CEO Organization', '').strip() == org_name), None)
        org_tech = next((r for r in tech_data if r.get('Organization', '').strip() == org_name), None)
        org_staff = next((r for r in staff_data if r.get('Organization', '').strip() == org_name), None)

        dates = []
        if org_intake and org_intake.get('Date'):
            dates.append(parse_date(org_intake['Date']))
        if org_ceo and org_ceo.get('Date'):
            dates.append(parse_date(org_ceo['Date']))
        if org_tech and org_tech.get('Date'):
            dates.append(parse_date(org_tech['Date']))
        if org_staff and org_staff.get('Date'):
            dates.append(parse_date(org_staff['Date']))

        last_activity = max(dates).strftime('%Y-%m-%d') if dates else 'N/A'

        organizations.append({
            'name': org_name,
            'completion_pct': completion_pct,
            'has_intake': has_intake,
            'has_ceo': has_ceo,
            'has_tech': has_tech,
            'has_staff': has_staff,
            'last_activity_date': last_activity
        })

    # Sort by completion percentage descending
    organizations.sort(key=lambda x: x['completion_pct'], reverse=True)

    # Calculate aggregate metrics
    total_organizations = len(all_orgs)
    average_completion = sum(org['completion_pct'] for org in organizations) / total_organizations if total_organizations > 0 else 0

    # Survey type breakdown
    intake_complete = len(all_orgs)
    ceo_complete = len(ceo_orgs)
    tech_complete = len(tech_orgs)
    staff_complete = len(staff_orgs)

    # Timeline data (group by week)
    all_dates = []
    for row in intake_data + ceo_data + tech_data + staff_data:
        date_str = row.get('Date', '')
        if date_str:
            try:
                all_dates.append(parse_date(date_str))
            except:
                pass

    # Group dates by week
    timeline_weeks = []
    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)

        current = min_date
        while current <= max_date:
            week_end = current + timedelta(days=7)
            count = sum(1 for d in all_dates if current <= d < week_end)

            if count > 0:
                timeline_weeks.append({
                    'week_start_date': current.strftime('%Y-%m-%d'),
                    'week_end_date': week_end.strftime('%Y-%m-%d'),
                    'response_count': count,
                    'percentage_of_total': (count / len(all_dates)) * 100
                })

            current = week_end

    return {
        'report_date': datetime.now(),
        'total_organizations': total_organizations,
        'fully_complete_count': fully_complete_count,
        'total_responses': total_responses,
        'average_completion_percentage': round(average_completion, 1),
        'overall_response_rate': round((total_responses / (total_organizations * 4)) * 100, 1),
        'survey_breakdown': {
            'intake': {
                'completed_count': intake_complete,
                'expected_count': total_organizations,
                'completion_percentage': round((intake_complete / total_organizations) * 100, 1)
            },
            'ceo': {
                'completed_count': ceo_complete,
                'expected_count': total_organizations,
                'completion_percentage': round((ceo_complete / total_organizations) * 100, 1)
            },
            'tech_lead': {
                'completed_count': tech_complete,
                'expected_count': total_organizations,
                'completion_percentage': round((tech_complete / total_organizations) * 100, 1)
            },
            'staff': {
                'completed_count': staff_complete,
                'expected_count': total_organizations,
                'completion_percentage': round((staff_complete / total_organizations) * 100, 1)
            }
        },
        'timeline_weeks': timeline_weeks,
        'organizations': organizations
    }
```

---

## Implementation Specifications

### File Structure

```
/Users/masa/Clients/JimJoseph/jjf-survey-analytics/
├── templates/
│   ├── report_organization.html     # Per-organization report template
│   ├── report_aggregate.html        # Aggregate report template
│   └── report_base.html             # Base template for reports (print-friendly)
│
├── report_generator.py              # Report generation logic
├── report_routes.py                 # Flask routes for reports
└── static/
    └── css/
        └── report_print.css         # Print-specific CSS
```

### Flask Routes

```python
# report_routes.py

from flask import Blueprint, render_template, abort
from report_generator import get_organization_report_data, get_aggregate_report_data

report_bp = Blueprint('reports', __name__, url_prefix='/report')

@report_bp.route('/org/<org_name>')
def organization_report(org_name: str):
    """Generate per-organization report."""
    try:
        data = get_organization_report_data(org_name)
        return render_template('report_organization.html', **data)
    except Exception as e:
        abort(404, description=f"Organization '{org_name}' not found")

@report_bp.route('/aggregate')
def aggregate_report():
    """Generate aggregate report across all organizations."""
    try:
        data = get_aggregate_report_data()
        return render_template('report_aggregate.html', **data)
    except Exception as e:
        abort(500, description="Error generating aggregate report")

@report_bp.route('/org/<org_name>/pdf')
def organization_report_pdf(org_name: str):
    """Generate PDF version of per-organization report."""
    # TODO: Implement PDF generation (using WeasyPrint or similar)
    pass

@report_bp.route('/aggregate/pdf')
def aggregate_report_pdf():
    """Generate PDF version of aggregate report."""
    # TODO: Implement PDF generation
    pass
```

### Print CSS

```css
/* static/css/report_print.css */

@media print {
    /* Hide navigation and interactive elements */
    nav, footer, button, .no-print {
        display: none !important;
    }

    /* Optimize for printing */
    body {
        background: white !important;
        color: black !important;
    }

    /* Ensure proper page breaks */
    .page-break {
        page-break-after: always;
    }

    .avoid-break {
        page-break-inside: avoid;
    }

    /* Adjust card styles for print */
    .shadow-md, .shadow-lg {
        box-shadow: none !important;
        border: 1px solid #e5e7eb !important;
    }

    /* Simplify colors for B&W printing */
    .bg-survey-blue { background-color: #e5e7eb !important; }
    .text-survey-blue { color: #1f2937 !important; }

    /* Ensure charts/graphics print well */
    .chart, .graph {
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
    }
}
```

---

## Code Templates

### Per-Organization Report Template

```html
<!-- templates/report_organization.html -->
{% extends "report_base.html" %}

{% block title %}{{ organization_name }} - Organization Report{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto space-y-8">
    <!-- Report Header -->
    <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-survey-blue avoid-break">
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

    <!-- Export Actions (hide in print) -->
    <div class="no-print flex justify-end space-x-3 mb-4">
        <button onclick="window.print()"
                class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
            <i class="fas fa-print mr-2"></i>Print Report
        </button>
        <a href="/report/org/{{ organization_name }}/pdf"
           class="px-4 py-2 bg-survey-blue text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
            <i class="fas fa-file-pdf mr-2"></i>Export PDF
        </a>
    </div>

    <!-- Executive Summary -->
    <div class="bg-white rounded-lg shadow-md p-6 avoid-break">
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

    <!-- Continue with other sections... -->

</div>
{% endblock %}
```

### Aggregate Report Template

```html
<!-- templates/report_aggregate.html -->
{% extends "report_base.html" %}

{% block title %}Aggregate Survey Analytics Report{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto space-y-8">
    <!-- Report Header -->
    <div class="bg-gradient-to-r from-survey-blue to-blue-700 text-white rounded-lg shadow-md p-8 avoid-break">
        <h1 class="text-4xl font-bold mb-2">
            <i class="fas fa-chart-bar mr-3"></i>
            Aggregate Survey Analytics Report
        </h1>
        <p class="text-blue-100 text-lg mb-4">
            Comprehensive Analysis Across All Participating Organizations
        </p>
        <div class="flex items-center space-x-6">
            <div>
                <p class="text-sm text-blue-100">Generated</p>
                <p class="text-lg font-semibold">{{ report_date.strftime('%B %d, %Y') }}</p>
            </div>
        </div>
    </div>

    <!-- Overview Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 avoid-break">
        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Organizations</p>
                    <p class="text-4xl font-bold text-gray-900">{{ total_organizations }}</p>
                </div>
                <i class="fas fa-building text-4xl text-gray-300"></i>
            </div>
            <div class="text-xs text-gray-600">
                <span class="font-semibold text-green-600">{{ fully_complete_count }}</span> fully complete
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Total Responses</p>
                    <p class="text-4xl font-bold text-gray-900">{{ total_responses }}</p>
                </div>
                <i class="fas fa-clipboard-check text-4xl text-blue-300"></i>
            </div>
            <div class="text-xs text-gray-600">
                Across all surveys
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Avg Completion</p>
                    <p class="text-4xl font-bold text-gray-900">{{ average_completion_percentage }}%</p>
                </div>
                <i class="fas fa-percentage text-4xl text-green-300"></i>
            </div>
            <div class="text-xs text-gray-600">
                Per organization
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <p class="text-sm font-medium text-gray-500">Response Rate</p>
                    <p class="text-4xl font-bold text-gray-900">{{ overall_response_rate }}%</p>
                </div>
                <i class="fas fa-chart-line text-4xl text-purple-300"></i>
            </div>
            <div class="text-xs text-gray-600">
                Expected vs actual
            </div>
        </div>
    </div>

    <!-- Continue with other sections... -->

</div>
{% endblock %}
```

---

## Summary & Next Steps

### Implementation Priority

1. **Phase 1: Per-Organization Reports**
   - Create `report_organization.html` template
   - Implement `get_organization_report_data()` function
   - Add Flask route `/report/org/<org_name>`
   - Test with sample organizations

2. **Phase 2: Aggregate Report**
   - Create `report_aggregate.html` template
   - Implement `get_aggregate_report_data()` function
   - Add Flask route `/report/aggregate`
   - Verify calculations and statistics

3. **Phase 3: PDF Export**
   - Install PDF generation library (WeasyPrint)
   - Create PDF-optimized templates
   - Implement PDF export endpoints
   - Test print/PDF output quality

4. **Phase 4: Integration**
   - Add report links to organization detail pages
   - Add aggregate report link to main dashboard
   - Implement report caching for performance
   - Add report access logging

### Testing Checklist

- [ ] Per-organization report displays all sections correctly
- [ ] Data accuracy verified against source data
- [ ] Aggregate report calculations match manual totals
- [ ] Print CSS renders reports cleanly
- [ ] PDF exports maintain formatting
- [ ] Reports handle missing data gracefully
- [ ] Mobile responsiveness (pre-print view)
- [ ] Performance with full dataset

### Future Enhancements

- Interactive charts using Chart.js or D3.js
- Report scheduling and email delivery
- Comparison reports (org vs aggregate)
- Custom report filtering and date ranges
- Report templates customization
- Data export in multiple formats (CSV, Excel, JSON)

---

**Document End**
