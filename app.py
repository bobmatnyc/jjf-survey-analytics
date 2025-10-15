#!/usr/bin/env python3
"""
Simple Flask App for JJF Survey Analytics - In-Memory Version
No database required - reads directly from Google Sheets into memory.
"""

from flask import Flask, render_template, jsonify, session, redirect, url_for, request, flash
from functools import wraps
import os
from datetime import datetime
from src.extractors.sheets_reader import SheetsReader
from typing import Dict, List, Any
from src.services.report_generator import ReportGenerator
from src.analytics.ai_analyzer import extract_free_text_responses
from src.utils.version import get_version_string, get_version_info

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'simple-dev-key-change-in-production')

# Authentication Configuration
APP_PASSWORD = os.getenv('APP_PASSWORD', 'survey2025!')
REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'false').lower() == 'true'

# Debug: Log authentication configuration on startup
print(f"[AUTH CONFIG] REQUIRE_AUTH env var: {os.getenv('REQUIRE_AUTH', 'NOT_SET')}")
print(f"[AUTH CONFIG] REQUIRE_AUTH boolean: {REQUIRE_AUTH}")

# Global in-memory data storage
SHEET_DATA: Dict[str, List[Dict[str, Any]]] = {}

# LLM Report Cache
# Cache structure: {
#   'org_reports': {'org_name': {'report': {...}, 'response_count': 3}},
#   'aggregate_report': {'report': {...}, 'total_responses': 22}
# }
REPORT_CACHE: Dict[str, Any] = {
    'org_reports': {},
    'aggregate_report': None
}


def load_sheet_data(verbose: bool = False) -> Dict[str, Any]:
    """Load data from Google Sheets into memory."""
    global SHEET_DATA
    SHEET_DATA = SheetsReader.fetch_all_tabs(verbose=verbose)
    return SHEET_DATA


def get_tab_data(tab_name: str) -> List[Dict[str, Any]]:
    """Get data for a specific tab."""
    return SHEET_DATA.get(tab_name, [])


def get_org_response_count(org_name: str) -> int:
    """
    Count total survey responses for an organization.

    Args:
        org_name: Organization name

    Returns:
        Count of completed surveys (CEO + Tech + Staff)
    """
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    count = 0
    if any(r.get('Organization') == org_name or r.get('CEO Organization') == org_name for r in ceo_data):
        count += 1
    if any(r.get('Organization') == org_name for r in tech_data):
        count += 1
    if any(r.get('Organization') == org_name for r in staff_data):
        count += 1

    return count


def get_total_response_count() -> int:
    """
    Count total survey responses across all organizations.

    Returns:
        Total count of all survey responses
    """
    ceo_count = len([r for r in get_tab_data('CEO') if r.get('Organization') or r.get('CEO Organization')])
    tech_count = len([r for r in get_tab_data('Tech') if r.get('Organization')])
    staff_count = len([r for r in get_tab_data('Staff') if r.get('Organization')])

    return ceo_count + tech_count + staff_count


def is_org_report_cached(org_name: str) -> bool:
    """
    Check if organization report is cached and valid.

    Args:
        org_name: Organization name

    Returns:
        True if cached report exists and response count matches
    """
    if org_name not in REPORT_CACHE['org_reports']:
        return False

    cached = REPORT_CACHE['org_reports'][org_name]
    current_count = get_org_response_count(org_name)

    return cached.get('response_count') == current_count


def is_aggregate_report_cached() -> bool:
    """
    Check if aggregate report is cached and valid.

    Returns:
        True if cached report exists and total response count matches
    """
    if REPORT_CACHE['aggregate_report'] is None:
        return False

    cached = REPORT_CACHE['aggregate_report']
    current_count = get_total_response_count()

    return cached.get('total_responses') == current_count


def cache_org_report(org_name: str, report: Dict[str, Any]) -> None:
    """
    Cache an organization report with current response count.

    Args:
        org_name: Organization name
        report: Generated report data
    """
    REPORT_CACHE['org_reports'][org_name] = {
        'report': report,
        'response_count': get_org_response_count(org_name),
        'cached_at': datetime.now().isoformat()
    }
    print(f"[Cache] Cached report for {org_name} (responses: {get_org_response_count(org_name)})")


def cache_aggregate_report(report: Dict[str, Any]) -> None:
    """
    Cache aggregate report with current total response count.

    Args:
        report: Generated report data
    """
    REPORT_CACHE['aggregate_report'] = {
        'report': report,
        'total_responses': get_total_response_count(),
        'cached_at': datetime.now().isoformat()
    }
    print(f"[Cache] Cached aggregate report (total responses: {get_total_response_count()})")


def get_response_rates() -> Dict[str, Any]:
    """
    Calculate response rates using the master organization list.

    Maps organizations from OrgMaster (using 'Organization' field) to
    Intake data (using 'Organization Name:' field) to calculate
    outreach vs response rates.

    Returns:
        Dictionary with response rate metrics and org-level details
    """
    org_master = get_tab_data('OrgMaster')
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Get all organizations from master list
    master_orgs = {row.get('Organization', '').strip()
                   for row in org_master
                   if row.get('Organization', '').strip()}

    # Get organizations that responded to intake
    intake_orgs = {row.get('Organization Name:', '').strip()
                   for row in intake_data
                   if row.get('Organization Name:', '').strip()}

    # Get organizations with CEO responses
    ceo_orgs = {row.get('CEO Organization', '').strip()
                for row in ceo_data
                if row.get('CEO Organization', '').strip()}

    # Get organizations with Tech responses
    tech_orgs = {row.get('Organization', '').strip()
                 for row in tech_data
                 if row.get('Organization', '').strip()}

    # Get organizations with Staff responses
    staff_orgs = {row.get('Organization', '').strip()
                  for row in staff_data
                  if row.get('Organization', '').strip()}

    # Calculate metrics
    total_outreach = len(master_orgs)
    total_responded = len(intake_orgs)
    intake_response_rate = (total_responded / total_outreach * 100) if total_outreach > 0 else 0

    # Survey completion metrics
    ceo_responses = len(ceo_orgs)
    tech_responses = len(tech_orgs)
    staff_responses = len(staff_orgs)

    return {
        'total_outreach': total_outreach,
        'total_responded': total_responded,
        'not_responded': total_outreach - total_responded,
        'intake_response_rate': round(intake_response_rate, 1),
        'ceo_responses': ceo_responses,
        'tech_responses': tech_responses,
        'staff_responses': staff_responses,
        'master_orgs': sorted(master_orgs),
        'responded_orgs': sorted(intake_orgs),
        'not_responded_orgs': sorted(master_orgs - intake_orgs)
    }


def get_participation_overview() -> Dict[str, Any]:
    """Get aggregate participation metrics for dashboard."""
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Extract unique organizations from each tab
    intake_orgs = {row.get('Organization Name:', '').strip()
                   for row in intake_data
                   if row.get('Organization Name:', '').strip()}

    ceo_orgs = {row.get('CEO Organization', '').strip()
                for row in ceo_data
                if row.get('CEO Organization', '').strip()}

    tech_orgs = {row.get('Organization', '').strip()
                 for row in tech_data
                 if row.get('Organization', '').strip()}

    staff_orgs = {row.get('Organization', '').strip()
                  for row in staff_data
                  if row.get('Organization', '').strip()}

    # Calculate metrics
    total_orgs = len(intake_orgs)
    ceo_complete = len(intake_orgs & ceo_orgs)
    tech_complete = len(intake_orgs & tech_orgs)
    staff_complete = len(intake_orgs & staff_orgs)
    fully_complete = len(intake_orgs & ceo_orgs & tech_orgs & staff_orgs)
    not_started = len(intake_orgs - ceo_orgs)

    return {
        'total_organizations': total_orgs,
        'ceo_complete': ceo_complete,
        'tech_complete': tech_complete,
        'staff_complete': staff_complete,
        'fully_complete': fully_complete,
        'not_started': not_started,
        'ceo_percent': round(100.0 * ceo_complete / total_orgs, 1) if total_orgs > 0 else 0,
        'tech_percent': round(100.0 * tech_complete / total_orgs, 1) if total_orgs > 0 else 0,
        'staff_percent': round(100.0 * staff_complete / total_orgs, 1) if total_orgs > 0 else 0,
        'fully_percent': round(100.0 * fully_complete / total_orgs, 1) if total_orgs > 0 else 0
    }


def get_organizations_status() -> List[Dict[str, Any]]:
    """Get per-organization completion status, sorted by most recent activity."""
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Create lookup dictionaries with dates for each survey type
    ceo_orgs_dates = {}
    for row in ceo_data:
        org_name = row.get('CEO Organization', '').strip()
        if org_name:
            ceo_orgs_dates[org_name] = row.get('Date', '')

    tech_orgs_dates = {}
    for row in tech_data:
        org_name = row.get('Organization', '').strip()
        if org_name:
            tech_orgs_dates[org_name] = row.get('Date', '')

    staff_orgs_dates = {}
    for row in staff_data:
        org_name = row.get('Organization', '').strip()
        if org_name:
            staff_orgs_dates[org_name] = row.get('Date', '')

    # Build organization status list with most recent activity
    organizations = []
    for row in intake_data:
        org_name = row.get('Organization Name:', '').strip()
        if not org_name:
            continue

        intake_date = row.get('Date', '')

        has_ceo = org_name in ceo_orgs_dates
        has_tech = org_name in tech_orgs_dates
        has_staff = org_name in staff_orgs_dates

        # Determine overall status
        if has_ceo and has_tech and has_staff:
            overall_status = 'complete'
        elif has_ceo:
            overall_status = 'in_progress'
        else:
            overall_status = 'not_started'

        # Find most recent activity across all surveys
        all_dates = [intake_date]
        if has_ceo:
            all_dates.append(ceo_orgs_dates[org_name])
        if has_tech:
            all_dates.append(tech_orgs_dates[org_name])
        if has_staff:
            all_dates.append(staff_orgs_dates[org_name])

        # Get max date (most recent activity)
        most_recent_activity = max(all_dates) if all_dates else ''

        organizations.append({
            'organization': org_name,
            'intake_date': intake_date[:10] if intake_date else '',
            'ceo_status': 'complete' if has_ceo else 'pending',
            'tech_status': 'complete' if has_tech else 'pending',
            'staff_status': 'complete' if has_staff else 'pending',
            'overall_status': overall_status,
            'last_activity': most_recent_activity
        })

    # Sort by most recent activity descending and limit to 10
    organizations.sort(key=lambda x: x['last_activity'], reverse=True)
    return organizations[:10]


def get_latest_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent submission activity across all tabs."""
    activities = []

    # Intake activities
    intake_data = get_tab_data('Intake')
    for row in intake_data:
        org_name = row.get('Organization Name:', '').strip()
        date = row.get('Date', '')
        if org_name and date:
            activities.append({
                'organization': org_name,
                'activity_type': 'Intake',
                'timestamp': date[:16] if len(date) >= 16 else date,
                'activity_description': 'Intake form completed'
            })

    # CEO activities
    ceo_data = get_tab_data('CEO')
    for row in ceo_data:
        org_name = row.get('CEO Organization', '').strip()
        date = row.get('Date', '')
        name = row.get('Name', '')
        if org_name and date:
            activities.append({
                'organization': org_name,
                'activity_type': 'CEO Survey',
                'timestamp': date[:16] if len(date) >= 16 else date,
                'activity_description': f'CEO survey completed by {name}' if name else 'CEO survey completed'
            })

    # Tech activities
    tech_data = get_tab_data('Tech')
    for row in tech_data:
        org_name = row.get('Organization', '').strip()
        date = row.get('Date', '')
        name = row.get('Name', '')
        if org_name and date:
            activities.append({
                'organization': org_name,
                'activity_type': 'Tech Survey',
                'timestamp': date[:16] if len(date) >= 16 else date,
                'activity_description': f'Tech Lead survey completed by {name}' if name else 'Tech Lead survey completed'
            })

    # Staff activities
    staff_data = get_tab_data('Staff')
    for row in staff_data:
        org_name = row.get('Organization', '').strip()
        date = row.get('Date', '')
        name = row.get('Name', '')
        if org_name and date:
            activities.append({
                'organization': org_name,
                'activity_type': 'Staff Survey',
                'timestamp': date[:16] if len(date) >= 16 else date,
                'activity_description': f'Staff survey completed by {name}' if name else 'Staff survey completed'
            })

    # Sort by timestamp descending and limit to specified number
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]


def get_funnel_data() -> Dict[str, Any]:
    """Get participation funnel numbers."""
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Count unique organizations
    intake_count = len({row.get('Organization Name:', '').strip()
                       for row in intake_data
                       if row.get('Organization Name:', '').strip()})

    ceo_count = len({row.get('CEO Organization', '').strip()
                    for row in ceo_data
                    if row.get('CEO Organization', '').strip()})

    tech_count = len({row.get('Organization', '').strip()
                     for row in tech_data
                     if row.get('Organization', '').strip()})

    staff_count = len({row.get('Organization', '').strip()
                      for row in staff_data
                      if row.get('Organization', '').strip()})

    return {
        'intake': intake_count,
        'ceo': ceo_count,
        'tech': tech_count,
        'staff': staff_count,
        'ceo_percent': round(100.0 * ceo_count / intake_count, 1) if intake_count > 0 else 0,
        'tech_percent': round(100.0 * tech_count / intake_count, 1) if intake_count > 0 else 0,
        'staff_percent': round(100.0 * staff_count / intake_count, 1) if intake_count > 0 else 0
    }


def get_stats() -> Dict[str, Any]:
    """Get basic statistics about loaded data including response rates."""
    metadata = SHEET_DATA.get('_metadata', {})

    tabs_stats = []
    for tab_name in SheetsReader.TABS.keys():
        row_count = len(get_tab_data(tab_name))
        tabs_stats.append({
            'tab_name': tab_name,
            'row_count': row_count,
            'last_extract': metadata.get('last_fetch', '')
        })

    # Include response rates from master list
    try:
        response_rates = get_response_rates()
    except Exception as e:
        print(f"Error calculating response rates: {e}")
        response_rates = None

    stats = {
        'tabs': tabs_stats,
        'total_rows': metadata.get('total_rows', 0),
        'last_fetch': metadata.get('last_fetch', ''),
        'spreadsheet_id': metadata.get('spreadsheet_id', '')
    }

    if response_rates:
        stats['response_rates'] = response_rates

    return stats


def format_date(date_str: str) -> str:
    """Format date string to human-readable format."""
    if not date_str:
        return 'N/A'
    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        # Return first 10 characters if format is unknown
        return date_str[:10] if len(date_str) >= 10 else date_str


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate long text with ellipsis."""
    if not text:
        return ''
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'


def get_organizations_summary() -> List[Dict[str, Any]]:
    """
    Get detailed organization data from master list with intake information.

    Shows ALL organizations from OrgMaster list with their response status.

    Email Resolution:
    - Uses email from Intake sheet if organization has responded
    - Falls back to email from OrgMaster sheet if organization hasn't responded
    - Provides maximum email coverage for all organizations
    """
    org_master = get_tab_data('OrgMaster')
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Create lookup dictionaries for intake data
    intake_lookup = {}
    for row in intake_data:
        org_name = row.get('Organization Name:', '').strip()
        if org_name:
            intake_lookup[org_name] = row

    # Create lookup sets for survey responses
    ceo_orgs = {row.get('CEO Organization', '').strip() for row in ceo_data if row.get('CEO Organization', '').strip()}
    tech_orgs = {row.get('Organization', '').strip() for row in tech_data if row.get('Organization', '').strip()}
    staff_orgs = {row.get('Organization', '').strip() for row in staff_data if row.get('Organization', '').strip()}

    organizations = []

    # Iterate through ALL organizations in master list
    for row in org_master:
        org_name = row.get('Organization', '').strip()
        if not org_name:
            continue

        # Check if this org submitted intake
        intake_record = intake_lookup.get(org_name)
        has_intake = intake_record is not None

        # Check survey completions
        has_ceo = org_name in ceo_orgs
        has_tech = org_name in tech_orgs
        has_staff = org_name in staff_orgs

        # Determine overall status
        if not has_intake:
            status = 'No Response'
        elif has_ceo and has_tech and has_staff:
            status = 'Complete'
        elif has_ceo or has_tech or has_staff:
            status = 'In Progress'
        else:
            status = 'Intake Only'

        # Determine email: use intake email if available, otherwise use OrgMaster email
        email = ''
        if intake_record and intake_record.get('Email', '').strip():
            email = intake_record.get('Email', '').strip()
        else:
            # Use email from OrgMaster for organizations that haven't responded
            email = row.get('Email', '').strip()

        organizations.append({
            'organization': org_name,
            'email': email,
            'submitted_date': format_date(intake_record.get('Date', '')) if intake_record else 'Not Submitted',
            'status': status,
            'has_intake': has_intake,
            'ceo_complete': has_ceo,
            'tech_complete': has_tech,
            'staff_complete': has_staff
        })

    # Sort: Responded first (by date), then not responded (alphabetically)
    organizations.sort(key=lambda x: (
        not x['has_intake'],  # Not responded goes to bottom
        x['submitted_date'] if x['has_intake'] else x['organization']  # Date for responded, name for not
    ))

    return organizations


def get_ceo_summary() -> List[Dict[str, Any]]:
    """Get detailed CEO survey responses."""
    ceo_data = get_tab_data('CEO')

    responses = []
    for row in ceo_data:
        org_name = row.get('CEO Organization', '').strip()
        if not org_name:
            continue

        # Extract key fields from CEO survey
        name = row.get('Name', '')
        email = row.get('Email', '')
        date = format_date(row.get('Date', ''))

        # Get some key responses (adjust field names based on actual data)
        vision = truncate_text(row.get('C-1', '') or row.get('Vision', ''), 150)
        challenges = truncate_text(row.get('C-2', '') or row.get('Challenges', ''), 150)

        responses.append({
            'organization': org_name,
            'name': name,
            'email': email,
            'submitted_date': date,
            'vision': vision,
            'challenges': challenges
        })

    # Sort by date descending
    responses.sort(key=lambda x: x['submitted_date'], reverse=True)
    return responses


def get_tech_summary() -> List[Dict[str, Any]]:
    """Get detailed Tech Lead survey responses."""
    tech_data = get_tab_data('Tech')

    responses = []
    for row in tech_data:
        org_name = row.get('Organization', '').strip()
        if not org_name:
            continue

        name = row.get('Name', '')
        email = row.get('Email', '')
        date = format_date(row.get('Date', ''))

        # Get key infrastructure responses
        infrastructure = truncate_text(row.get('TL-1', '') or row.get('Infrastructure', ''), 150)
        tools = truncate_text(row.get('TL-2', '') or row.get('Tools', ''), 150)

        responses.append({
            'organization': org_name,
            'name': name,
            'email': email,
            'submitted_date': date,
            'infrastructure': infrastructure,
            'tools': tools
        })

    # Sort by date descending
    responses.sort(key=lambda x: x['submitted_date'], reverse=True)
    return responses


def get_staff_summary() -> List[Dict[str, Any]]:
    """Get detailed Staff survey responses."""
    staff_data = get_tab_data('Staff')

    responses = []
    for row in staff_data:
        org_name = row.get('Organization', '').strip()
        if not org_name:
            continue

        name = row.get('Name', '')
        email = row.get('Email', '')
        date = format_date(row.get('Date', ''))

        # Get key usage responses
        usage = truncate_text(row.get('S-1', '') or row.get('Usage', ''), 150)
        satisfaction = truncate_text(row.get('S-2', '') or row.get('Satisfaction', ''), 150)

        responses.append({
            'organization': org_name,
            'name': name,
            'email': email,
            'submitted_date': date,
            'usage': usage,
            'satisfaction': satisfaction
        })

    # Sort by date descending
    responses.sort(key=lambda x: x['submitted_date'], reverse=True)
    return responses


def get_complete_organizations() -> List[Dict[str, Any]]:
    """Get organizations that have completed all surveys."""
    intake_data = get_tab_data('Intake')
    ceo_data = get_tab_data('CEO')
    tech_data = get_tab_data('Tech')
    staff_data = get_tab_data('Staff')

    # Create lookup dictionaries with dates
    ceo_dates = {row.get('CEO Organization', '').strip(): format_date(row.get('Date', ''))
                 for row in ceo_data if row.get('CEO Organization', '').strip()}
    tech_dates = {row.get('Organization', '').strip(): format_date(row.get('Date', ''))
                  for row in tech_data if row.get('Organization', '').strip()}
    staff_dates = {row.get('Organization', '').strip(): format_date(row.get('Date', ''))
                   for row in staff_data if row.get('Organization', '').strip()}

    complete_orgs = []
    for row in intake_data:
        org_name = row.get('Organization Name:', '').strip()
        if not org_name:
            continue

        # Check if all surveys are complete
        if org_name in ceo_dates and org_name in tech_dates and org_name in staff_dates:
            complete_orgs.append({
                'organization': org_name,
                'email': row.get('Email', ''),
                'intake_date': format_date(row.get('Date', '')),
                'ceo_date': ceo_dates[org_name],
                'tech_date': tech_dates[org_name],
                'staff_date': staff_dates[org_name]
            })

    # Sort by intake date descending
    complete_orgs.sort(key=lambda x: x['intake_date'], reverse=True)
    return complete_orgs


# ============================================================================
# Authentication System
# ============================================================================

def require_auth(f):
    """Authentication decorator for protecting routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not REQUIRE_AUTH:
            return f(*args, **kwargs)
        if 'authenticated' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if not REQUIRE_AUTH:
        return redirect(url_for('home'))

    if request.method == 'POST':
        password = request.form.get('password')
        next_url = request.form.get('next') or url_for('home')

        if password == APP_PASSWORD:
            session['authenticated'] = True
            flash('Successfully logged in!', 'success')
            return redirect(next_url)
        else:
            flash('Invalid password. Please try again.', 'error')

    next_url = request.args.get('next', url_for('home'))
    return render_template('login.html', next_url=next_url)


@app.route('/logout')
def logout():
    """Logout."""
    session.pop('authenticated', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============================================================================
# Application Routes
# ============================================================================

@app.route('/')
@require_auth
def home():
    """Home page with organization participation dashboard."""
    data_ready = bool(SHEET_DATA and '_metadata' in SHEET_DATA)
    stats = get_stats() if data_ready else {}

    dashboard_data = {}
    if data_ready:
        dashboard_data = {
            'overview': get_participation_overview(),
            'organizations': get_organizations_status(),
            'activity': get_latest_activity(),
            'funnel': get_funnel_data()
        }

    return render_template('simple/home.html',
                         db_ready=data_ready,
                         stats=stats,
                         dashboard=dashboard_data)


@app.route('/admin')
@require_auth
def admin():
    """Admin page with data management functions."""
    stats = get_stats() if SHEET_DATA and '_metadata' in SHEET_DATA else {
        'tabs': [],
        'total_rows': 0,
        'last_fetch': '',
        'spreadsheet_id': ''
    }

    return render_template('simple/admin.html', stats=stats)


@app.route('/data')
@require_auth
def data_nav():
    """Data navigation page with links to tabs."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/data_nav.html',
                             tabs=[],
                             error="Data not loaded. Please refresh data first.")

    metadata = SHEET_DATA.get('_metadata', {})
    last_fetch = metadata.get('last_fetch', '')

    tabs = []
    for tab_name in SheetsReader.TABS.keys():
        row_count = len(get_tab_data(tab_name))
        tabs.append({
            'name': tab_name,
            'row_count': row_count,
            'last_extract': last_fetch
        })

    return render_template('simple/data_nav.html', tabs=tabs, error=None)


@app.route('/data/<tab_name>')
@require_auth
def view_tab(tab_name):
    """Display specific tab data in table format."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/tab_view.html',
                             tab_name=tab_name,
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_tab_data(tab_name)

    if not data:
        return render_template('simple/tab_view.html',
                             tab_name=tab_name,
                             data=[],
                             columns=[],
                             error=f"No data found for tab '{tab_name}'")

    # Add row index to each row
    indexed_data = []
    for i, row in enumerate(data, 1):
        row_copy = row.copy()
        row_copy['_row_index'] = i
        indexed_data.append(row_copy)

    # Collect all unique columns
    columns = ['_row_index']
    for row in indexed_data:
        for key in row.keys():
            if key not in columns and key != '_row_index':
                columns.append(key)

    return render_template('simple/tab_view.html',
                         tab_name=tab_name,
                         data=indexed_data,
                         columns=columns,
                         error=None)


@app.route('/summary/organizations')
@require_auth
def summary_organizations():
    """Summary view of all organizations."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/summary.html',
                             page_title='Organizations',
                             summary_type='organizations',
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_organizations_summary()
    columns = [
        {'key': 'organization', 'label': 'Organization', 'class': 'font-semibold text-gray-900'},
        {'key': 'email', 'label': 'Email', 'class': 'text-gray-600'},
        {'key': 'submitted_date', 'label': 'Intake Date', 'class': 'text-gray-500'},
        {'key': 'status', 'label': 'Status', 'class': 'text-center', 'badge': True}
    ]

    return render_template('simple/summary.html',
                         page_title='Organizations - Intake Submissions',
                         summary_type='organizations',
                         data=data,
                         columns=columns,
                         error=None)


@app.route('/summary/ceo')
@require_auth
def summary_ceo():
    """Summary view of CEO survey responses."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/summary.html',
                             page_title='CEO Surveys',
                             summary_type='ceo',
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_ceo_summary()
    columns = [
        {'key': 'organization', 'label': 'Organization', 'class': 'font-semibold text-gray-900'},
        {'key': 'name', 'label': 'CEO Name', 'class': 'text-gray-700'},
        {'key': 'email', 'label': 'Email', 'class': 'text-gray-600'},
        {'key': 'submitted_date', 'label': 'Submitted', 'class': 'text-gray-500'},
        {'key': 'vision', 'label': 'Vision', 'class': 'text-gray-600 text-sm'},
    ]

    return render_template('simple/summary.html',
                         page_title='CEO Survey Responses',
                         summary_type='ceo',
                         data=data,
                         columns=columns,
                         error=None)


@app.route('/summary/tech')
@require_auth
def summary_tech():
    """Summary view of Tech Lead survey responses."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/summary.html',
                             page_title='Tech Lead Surveys',
                             summary_type='tech',
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_tech_summary()
    columns = [
        {'key': 'organization', 'label': 'Organization', 'class': 'font-semibold text-gray-900'},
        {'key': 'name', 'label': 'Tech Lead Name', 'class': 'text-gray-700'},
        {'key': 'email', 'label': 'Email', 'class': 'text-gray-600'},
        {'key': 'submitted_date', 'label': 'Submitted', 'class': 'text-gray-500'},
        {'key': 'infrastructure', 'label': 'Infrastructure', 'class': 'text-gray-600 text-sm'},
    ]

    return render_template('simple/summary.html',
                         page_title='Tech Lead Survey Responses',
                         summary_type='tech',
                         data=data,
                         columns=columns,
                         error=None)


@app.route('/summary/staff')
@require_auth
def summary_staff():
    """Summary view of Staff survey responses."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/summary.html',
                             page_title='Staff Surveys',
                             summary_type='staff',
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_staff_summary()
    columns = [
        {'key': 'organization', 'label': 'Organization', 'class': 'font-semibold text-gray-900'},
        {'key': 'name', 'label': 'Staff Name', 'class': 'text-gray-700'},
        {'key': 'email', 'label': 'Email', 'class': 'text-gray-600'},
        {'key': 'submitted_date', 'label': 'Submitted', 'class': 'text-gray-500'},
        {'key': 'usage', 'label': 'Usage', 'class': 'text-gray-600 text-sm'},
    ]

    return render_template('simple/summary.html',
                         page_title='Staff Survey Responses',
                         summary_type='staff',
                         data=data,
                         columns=columns,
                         error=None)


@app.route('/summary/complete')
@require_auth
def summary_complete():
    """Summary view of fully complete organizations."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return render_template('simple/summary.html',
                             page_title='Complete Organizations',
                             summary_type='complete',
                             data=[],
                             columns=[],
                             error="Data not loaded. Please refresh data first.")

    data = get_complete_organizations()
    columns = [
        {'key': 'organization', 'label': 'Organization', 'class': 'font-semibold text-gray-900'},
        {'key': 'email', 'label': 'Email', 'class': 'text-gray-600'},
        {'key': 'intake_date', 'label': 'Intake', 'class': 'text-gray-500 text-sm'},
        {'key': 'ceo_date', 'label': 'CEO', 'class': 'text-blue-600 text-sm'},
        {'key': 'tech_date', 'label': 'Tech', 'class': 'text-purple-600 text-sm'},
        {'key': 'staff_date', 'label': 'Staff', 'class': 'text-green-600 text-sm'},
    ]

    return render_template('simple/summary.html',
                         page_title='Fully Complete Organizations',
                         summary_type='complete',
                         data=data,
                         columns=columns,
                         error=None)


@app.route('/api/refresh', methods=['GET', 'POST'])
@require_auth
def api_refresh():
    """Refresh data from Google Sheets and clear report cache."""
    try:
        load_sheet_data(verbose=True)
        stats = get_stats()

        # Clear report cache when data is refreshed
        REPORT_CACHE['org_reports'].clear()
        REPORT_CACHE['aggregate_report'] = None
        print("[Cache] Cleared all cached reports after data refresh")

        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully from Google Sheets',
            'stats': stats,
            'cache_cleared': True
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extract', methods=['GET', 'POST'])
@require_auth
def api_extract():
    """Alias for /api/refresh for backward compatibility."""
    return api_refresh()


@app.route('/api/stats')
@require_auth
def api_stats():
    """Get basic statistics."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return jsonify({
            'error': 'Data not loaded'
        }), 404

    return jsonify(get_stats())


@app.route('/api/response-rates')
@require_auth
def api_response_rates():
    """Get detailed response rate analysis using master organization list."""
    if not SHEET_DATA or '_metadata' not in SHEET_DATA:
        return jsonify({
            'error': 'Data not loaded'
        }), 404

    try:
        response_rates = get_response_rates()
        return jsonify(response_rates)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/cache/status')
@require_auth
def cache_status():
    """Get report cache status for monitoring."""
    org_reports_cached = list(REPORT_CACHE['org_reports'].keys())
    aggregate_cached = REPORT_CACHE['aggregate_report'] is not None

    cache_info = {
        'organization_reports': {
            'count': len(org_reports_cached),
            'organizations': []
        },
        'aggregate_report': {
            'cached': aggregate_cached
        }
    }

    # Add details for each cached org report
    for org_name in org_reports_cached:
        cache_data = REPORT_CACHE['org_reports'][org_name]
        cache_info['organization_reports']['organizations'].append({
            'name': org_name,
            'response_count': cache_data.get('response_count'),
            'cached_at': cache_data.get('cached_at'),
            'current_count': get_org_response_count(org_name),
            'valid': is_org_report_cached(org_name)
        })

    # Add details for aggregate report
    if aggregate_cached:
        agg_data = REPORT_CACHE['aggregate_report']
        cache_info['aggregate_report'].update({
            'total_responses': agg_data.get('total_responses'),
            'cached_at': agg_data.get('cached_at'),
            'current_total': get_total_response_count(),
            'valid': is_aggregate_report_cached()
        })

    return jsonify(cache_info)


@app.route('/api/cache/clear', methods=['POST'])
@require_auth
def clear_cache():
    """Manually clear the report cache."""
    REPORT_CACHE['org_reports'].clear()
    REPORT_CACHE['aggregate_report'] = None
    print("[Cache] Manually cleared all cached reports")

    return jsonify({
        'success': True,
        'message': 'Report cache cleared successfully'
    })


@app.route('/health')
def health_check():
    """Health check endpoint for Railway deployment."""
    try:
        # Check if data is loaded
        data_loaded = bool(SHEET_DATA and '_metadata' in SHEET_DATA)

        # Basic health status
        health_status = {
            'status': 'healthy' if data_loaded else 'degraded',
            'data_loaded': data_loaded,
            'app_version': 'simple-app-with-ai',
            'checks': {
                'sheet_data': 'ok' if data_loaded else 'no_data'
            }
        }

        if data_loaded:
            metadata = SHEET_DATA.get('_metadata', {})
            health_status['last_fetch'] = metadata.get('last_fetch', 'unknown')
            health_status['total_rows'] = metadata.get('total_rows', 0)

        # Return 200 even if degraded - Railway just needs app to respond
        return jsonify(health_status), 200

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/org/<org_name>')
@require_auth
def organization_detail(org_name):
    """
    Display organization detail page with survey status and contacts.

    Shows organization overview, contact information, and survey completion status.
    """
    try:
        if not SHEET_DATA:
            return render_template('error.html',
                                 error="Data not loaded. Please refresh data first."), 503

        # Get intake record for organization
        intake_data = get_tab_data('Intake')
        intake_record = next((r for r in intake_data if r.get('Organization') == org_name), None)

        # Get survey data for completion calculation
        ceo_data = get_tab_data('CEO')
        tech_data = get_tab_data('Tech')
        staff_data = get_tab_data('Staff')

        # Check survey completion status
        ceo_complete = any(r.get('Organization') == org_name for r in ceo_data)
        tech_complete = any(r.get('Organization') == org_name for r in tech_data)
        staff_complete = any(r.get('Organization') == org_name for r in staff_data)

        # Calculate completion metrics
        completed_surveys = sum([ceo_complete, tech_complete, staff_complete])
        total_surveys = 3
        completion_pct = int((completed_surveys / total_surveys) * 100)

        # Build contacts list from intake record
        contacts = []
        if intake_record:
            # CEO contact
            ceo_email = intake_record.get('Email Address')
            if ceo_email:
                contacts.append({
                    'type': 'CEO',
                    'role': 'CEO',
                    'email': ceo_email,
                    'name': intake_record.get('First Name', '') + ' ' + intake_record.get('Last Name', ''),
                    'has_survey': ceo_complete
                })

            # Tech Lead contact
            tech_email = intake_record.get('Tech Lead Email')
            if tech_email:
                contacts.append({
                    'type': 'Tech Lead',
                    'role': 'Technology Lead',
                    'email': tech_email,
                    'name': intake_record.get('Tech Lead Name', 'Tech Lead'),
                    'has_survey': tech_complete
                })

            # Staff contacts (if we have staff email field in intake)
            staff_email = intake_record.get('Staff Email')
            if staff_email:
                contacts.append({
                    'type': 'Staff',
                    'role': 'Staff Member',
                    'email': staff_email,
                    'name': intake_record.get('Staff Name', 'Staff'),
                    'has_survey': staff_complete
                })

        return render_template('reports/organization_detail.html',
                             org_name=org_name,
                             intake_record=intake_record,
                             completion_pct=completion_pct,
                             completed_surveys=completed_surveys,
                             total_surveys=total_surveys,
                             contacts=contacts)

    except Exception as e:
        print(f"Error loading organization detail for {org_name}: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


@app.route('/report/<org_name>')
@require_auth
def organization_report(org_name):
    """
    Generate AI-powered organization report with maturity assessment.

    Uses ReportGenerator to create comprehensive analysis including:
    - Quantitative maturity scores across technology dimensions
    - Qualitative AI analysis of free text responses
    - Score modifiers based on contextual insights

    Implements intelligent caching: Report cached based on response count.
    Cache invalidates automatically when new responses are added.
    """
    try:
        if not SHEET_DATA:
            return render_template('error.html',
                                 error="Data not loaded. Please refresh data first."), 503

        # Check cache first
        if is_org_report_cached(org_name):
            print(f"[Cache HIT] Using cached report for {org_name}")
            report = REPORT_CACHE['org_reports'][org_name]['report']
            return render_template('reports/organization_report.html', report=report, org_name=org_name)

        # Cache miss - generate new report
        print(f"[Cache MISS] Generating new report for {org_name}")

        # Initialize report generator with AI enabled
        generator = ReportGenerator(SHEET_DATA, enable_ai=True)

        # Generate organization report
        report = generator.generate_organization_report(org_name)

        if not report:
            return render_template('error.html',
                                 error=f"No data found for organization: {org_name}"), 404

        # Cache the generated report
        cache_org_report(org_name, report)

        return render_template('reports/organization_report.html', report=report, org_name=org_name)

    except Exception as e:
        print(f"Error generating report for {org_name}: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


@app.route('/report/aggregate')
@require_auth
def aggregate_report():
    """
    Generate aggregate report across all organizations.

    Provides comprehensive maturity assessment aggregated across
    all surveyed organizations with comparative analytics.

    Implements intelligent caching: Report cached based on total response count.
    Cache invalidates automatically when any new response is added.
    """
    try:
        if not SHEET_DATA:
            return render_template('error.html',
                                 error="Data not loaded. Please refresh data first."), 503

        # Check cache first
        if is_aggregate_report_cached():
            print(f"[Cache HIT] Using cached aggregate report")
            report = REPORT_CACHE['aggregate_report']['report']
            return render_template('reports/aggregate_report.html', report=report)

        # Cache miss - generate new report
        print(f"[Cache MISS] Generating new aggregate report")

        # Initialize report generator with AI enabled
        generator = ReportGenerator(SHEET_DATA, enable_ai=True)

        # Generate aggregate report across all organizations
        report = generator.generate_aggregate_report()

        if not report:
            return render_template('error.html',
                                 error="Unable to generate aggregate report"), 500

        # Cache the generated report
        cache_aggregate_report(report)

        return render_template('reports/aggregate_report.html', report=report)

    except Exception as e:
        print(f"Error generating aggregate report: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


# Load data on startup
print("Loading data from Google Sheets on startup...")
try:
    load_sheet_data(verbose=True)
    print(f"✓ Data loaded successfully. Ready to serve requests.")
except Exception as e:
    print(f"✗ Failed to load data on startup: {e}")
    print("  Application will start but data will be empty until refresh.")


if __name__ == '__main__':
    # Display version information
    version_info = get_version_info()
    print("\n" + "=" * 60)
    print(f"JJF Survey Analytics Platform {get_version_string()}")
    if version_info.get('git_branch'):
        print(f"Branch: {version_info['git_branch']}")
    print("=" * 60 + "\n")

    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development' or True
    app.run(host='0.0.0.0', port=port, debug=debug)
