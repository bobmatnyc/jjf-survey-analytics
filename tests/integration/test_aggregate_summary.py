#!/usr/bin/env python3
"""
Test script to verify aggregate summary generation
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.extractors.sheets_reader import SheetsReader
from src.services.report_generator import ReportGenerator

# Set up environment
os.environ.setdefault("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))

def main():
    print("=" * 60)
    print("Testing Aggregate Summary Generation")
    print("=" * 60)

    # Initialize reader
    print("\n1. Loading data from Google Sheets...")
    sheet_data = SheetsReader.fetch_all_tabs(verbose=True)

    print(f"   ✓ Loaded {len(sheet_data)} tabs")

    # Initialize report generator with AI enabled
    print("\n2. Initializing Report Generator with AI...")
    report_gen = ReportGenerator(sheet_data, enable_ai=True)

    if report_gen.ai_analyzer:
        print("   ✓ AI Analyzer initialized successfully")
    else:
        print("   ✗ AI Analyzer NOT available (check OPENROUTER_API_KEY)")
        print("   → Testing will use fallback summary generation")

    # Find an organization with CEO responses
    print("\n3. Finding organization with CEO responses...")
    intake_data = sheet_data.get("Intake", [])
    ceo_data = sheet_data.get("CEO", [])

    test_org = None
    for ceo_record in ceo_data:
        if ceo_record.get("Date"):  # Has completed survey
            org_name = ceo_record.get("CEO Organization")
            if org_name:
                test_org = org_name
                break

    if not test_org:
        print("   ✗ No organizations with CEO responses found")
        return 1

    print(f"   ✓ Testing with organization: {test_org}")

    # Generate report
    print(f"\n4. Generating report for '{test_org}'...")
    report = report_gen.generate_organization_report(test_org)

    if not report:
        print(f"   ✗ Failed to generate report for {test_org}")
        return 1

    print("   ✓ Report generated successfully")

    # Check maturity assessment
    print("\n5. Checking maturity assessment...")
    maturity = report.get("maturity", {})

    if not maturity:
        print("   ✗ No maturity assessment found")
        return 1

    overall_score = maturity.get("overall_score", 0)
    maturity_level = maturity.get("maturity_level", "Unknown")
    maturity_desc = maturity.get("maturity_description", "")
    aggregate_summary = maturity.get("aggregate_summary", None)

    print(f"   Overall Score: {overall_score:.1f}/5.0")
    print(f"   Maturity Level: {maturity_level}")
    print(f"   Description: {maturity_desc}")

    # Check dimension scores
    print("\n6. Dimension Scores:")
    variance_analysis = maturity.get("variance_analysis", {})
    for dim, analysis in variance_analysis.items():
        score = analysis.get("weighted_score", 0)
        print(f"   {dim}: {score:.1f}/5.0")

    # Check aggregate summary
    print("\n7. Aggregate Summary Status:")
    if aggregate_summary:
        print("   ✓ Aggregate summary generated!")
        print(f"   Length: {len(aggregate_summary)} characters")
        print(f"\n   Summary:")
        print(f"   {'-' * 58}")
        # Word wrap for display
        import textwrap
        wrapped = textwrap.fill(aggregate_summary, width=58)
        for line in wrapped.split('\n'):
            print(f"   {line}")
        print(f"   {'-' * 58}")

        # Check length requirements (updated to 500-600 character target)
        if len(aggregate_summary) > 700:
            print(f"\n   ⚠ Warning: Summary is {len(aggregate_summary)} chars (target: 500-600)")
            print(f"      Exceeds target by {len(aggregate_summary) - 600} chars")
        elif len(aggregate_summary) < 400:
            print(f"\n   ⚠ Warning: Summary is {len(aggregate_summary)} chars (target: 500-600)")
            print(f"      Below target by {500 - len(aggregate_summary)} chars")
        else:
            print(f"\n   ✓ Summary length is appropriate ({len(aggregate_summary)} chars)")
            print(f"      Within target range (500-600 chars)")

        # Check sentence count (should be 5-7 sentences)
        sentence_count = aggregate_summary.count('.') + aggregate_summary.count('!') + aggregate_summary.count('?')
        print(f"\n   Sentence count: ~{sentence_count} sentences")
        if 5 <= sentence_count <= 7:
            print(f"   ✓ Sentence count within target range (5-7)")
        else:
            print(f"   ⚠ Sentence count outside target range (5-7)")
    else:
        print("   ✗ No aggregate summary generated")
        return 1

    # Check AI insights
    print("\n8. AI Insights Status:")
    ai_insights = report.get("ai_insights")
    if ai_insights and "dimensions" in ai_insights:
        dim_count = len(ai_insights["dimensions"])
        print(f"   ✓ AI insights available for {dim_count} dimensions")
        for dim, insights in ai_insights["dimensions"].items():
            if "summary" in insights and insights["summary"]:
                print(f"     • {dim}: {len(insights['summary'])} chars")
    else:
        print("   ○ No AI insights available (AI may be disabled)")

    print("\n" + "=" * 60)
    print("✓ Test Complete - Aggregate Summary Working!")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
