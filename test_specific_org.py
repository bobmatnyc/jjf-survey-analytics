#!/usr/bin/env python3
"""
Test specific organization's aggregate summary
"""

import sys
from sheets_reader import SheetsReader
from report_generator import ReportGenerator

def main():
    org_name = "Jewish New Teacher Project"

    print(f"Testing aggregate summary for: {org_name}\n")

    # Load data
    print("Loading data...")
    sheet_data = SheetsReader.fetch_all_tabs(verbose=False)
    print(f"✓ Loaded {len(sheet_data)} tabs\n")

    # Generate report
    print("Generating report...")
    report_gen = ReportGenerator(sheet_data, enable_ai=True)
    report = report_gen.generate_organization_report(org_name)

    if not report:
        print(f"✗ No report generated for {org_name}")
        return 1

    maturity = report.get("maturity", {})
    print(f"\n{'='*70}")
    print(f"MATURITY ASSESSMENT - {org_name}")
    print(f"{'='*70}")
    print(f"Overall Score: {maturity.get('overall_score', 0):.1f}/5.0")
    print(f"Maturity Level: {maturity.get('maturity_level', 'Unknown')}")
    print(f"Description: {maturity.get('maturity_description', '')}")

    print(f"\n{'='*70}")
    print("DIMENSION SCORES")
    print(f"{'='*70}")
    variance = maturity.get("variance_analysis", {})
    for dim, analysis in variance.items():
        score = analysis.get("weighted_score", 0)
        ceo = analysis.get("ceo_score", "N/A")
        tech = analysis.get("tech_score", "N/A")
        staff = analysis.get("staff_score", "N/A")
        print(f"{dim:25s} {score:.1f}  (CEO: {ceo}, Tech: {tech}, Staff: {staff})")

    print(f"\n{'='*70}")
    print("AGGREGATE SUMMARY")
    print(f"{'='*70}")
    summary = maturity.get("aggregate_summary")
    if summary:
        print(f"Length: {len(summary)} characters\n")
        print(summary)
        print(f"\n{'='*70}")
    else:
        print("✗ No aggregate summary generated")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
