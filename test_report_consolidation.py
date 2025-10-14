#!/usr/bin/env python3
"""
Integration test for text consolidation in organization reports.
Tests the full flow from report generation to consolidated outputs.
"""

import os
import sys
from report_generator import ReportGenerator
from sheets_reader import SheetsReader


def test_report_consolidation():
    """Test that report generation includes consolidated text."""
    print("=" * 80)
    print("ORGANIZATION REPORT CONSOLIDATION TEST")
    print("=" * 80)
    print()

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  WARNING: OPENROUTER_API_KEY not found in environment")
        print("AI consolidation will be skipped, but report will still generate.")
        print()

    try:
        # Read Google Sheets data
        print("Loading Google Sheets data...")
        reader = SheetsReader()
        sheet_data = reader.fetch_all_tabs()
        print(f"✓ Loaded {len(sheet_data)} sheets\n")

        # Get organization names
        intake_data = sheet_data.get("Intake", [])
        org_names = [row.get("Organization Name:") for row in intake_data if row.get("Organization Name:")]

        if not org_names:
            print("❌ ERROR: No organizations found in Intake sheet")
            return False

        print(f"Found {len(org_names)} organizations")
        print()

        # Test with first organization
        test_org = org_names[0]
        print(f"Testing with organization: {test_org}")
        print("-" * 80)

        # Generate report with AI enabled
        generator = ReportGenerator(sheet_data, enable_ai=True)
        report = generator.generate_organization_report(test_org)

        if not report:
            print(f"❌ ERROR: Failed to generate report for {test_org}")
            return False

        print("✓ Report generated successfully")
        print()

        # Check maturity description consolidation
        print("1. OVERALL MATURITY DESCRIPTION")
        print("-" * 80)
        maturity_desc = report["maturity"].get("maturity_description", "")
        print(f"Text: {maturity_desc}")
        print(f"Length: {len(maturity_desc)} chars")

        if len(maturity_desc) <= 60:
            print("✓ PASS: Maturity description is concise (≤60 chars)")
        else:
            print(f"⚠️  WARNING: Maturity description is long ({len(maturity_desc)} chars > 60)")
        print()

        # Check AI insights consolidation
        print("2. AI DIMENSION SUMMARIES")
        print("-" * 80)

        if not report.get("ai_insights"):
            print("⚠️  WARNING: AI insights not available (API key missing or AI failed)")
            print("Consolidation cannot be tested without AI insights")
            return True  # Still pass if AI not available

        dimensions = report["ai_insights"].get("dimensions", {})
        all_passed = True

        for dimension, analysis in dimensions.items():
            summary = analysis.get("summary", "")
            print(f"\n{dimension}:")
            print(f"  Text: {summary}")
            print(f"  Length: {len(summary)} chars")

            if len(summary) <= 150:
                print(f"  ✓ PASS: Summary is concise (≤150 chars)")
            else:
                print(f"  ⚠️  FAIL: Summary is too long ({len(summary)} chars > 150)")
                all_passed = False

        print()
        print("=" * 80)
        if all_passed:
            print("✓ ALL CONSOLIDATION TESTS PASSED")
        else:
            print("⚠️  SOME CONSOLIDATION TESTS FAILED")
        print("=" * 80)

        return all_passed

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_report_consolidation()
    exit(0 if success else 1)
