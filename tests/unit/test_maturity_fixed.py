"""
Test the fixed maturity rubric with Jewish New Teacher Project data
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.analytics.maturity_rubric import MaturityRubric
from src.extractors.sheets_reader import SheetsReader

def extract_numeric_responses(record):
    """Extract numeric responses from a survey record."""
    numeric_responses = {}

    for key, value in record.items():
        if key.startswith(('C-', 'TL-', 'S-')) and value:
            try:
                num_value = float(str(value).strip())
                # Only include if it's a valid rating (1-5, excluding 0 and 6)
                if 1 <= num_value <= 5:
                    numeric_responses[key] = num_value
            except (ValueError, TypeError):
                continue

    return numeric_responses


def main():
    print("Loading sheet data...")
    sheet_data = SheetsReader.fetch_all_tabs(verbose=True)

    # Get CEO survey data (using correct tab names)
    ceo_data = sheet_data.get('CEO', [])
    tech_data = sheet_data.get('Tech', [])
    staff_data = sheet_data.get('Staff', [])

    if not ceo_data:
        print("ERROR: No CEO data found")
        return

    # Test with first CEO organization
    ceo_record = ceo_data[0]
    org_name = ceo_record.get('Organization', 'Unknown')

    print(f"\n{'='*60}")
    print(f"Testing Maturity Assessment for: {org_name}")
    print(f"{'='*60}\n")

    # Find matching Tech and Staff records
    tech_record = next((r for r in tech_data if r.get('Organization') == org_name), {})
    staff_record = next((r for r in staff_data if r.get('Organization') == org_name), {})

    # Extract numeric responses
    ceo_responses = extract_numeric_responses(ceo_record)
    tech_responses = extract_numeric_responses(tech_record)
    staff_responses = extract_numeric_responses(staff_record)

    print(f"CEO Responses: {len(ceo_responses)} questions answered")
    print(f"Tech Lead Responses: {len(tech_responses)} questions answered")
    print(f"Staff Responses: {len(staff_responses)} questions answered")

    # Show sample CEO responses to validate 0 values are excluded
    print("\nSample CEO Responses (first 10):")
    for i, (q_id, value) in enumerate(list(ceo_responses.items())[:10]):
        print(f"  {q_id}: {value}")

    # Calculate maturity assessment
    rubric = MaturityRubric()
    org_responses = {
        'CEO': ceo_responses,
        'Tech': tech_responses,
        'Staff': staff_responses
    }

    assessment = rubric.calculate_overall_maturity(org_responses)

    # Display results
    print(f"\n{'='*60}")
    print("MATURITY ASSESSMENT RESULTS")
    print(f"{'='*60}\n")

    print(f"Overall Maturity Score: {assessment['overall_score']:.2f} / 5.0")
    print(f"Maturity Level: {assessment['maturity_level']}")
    print(f"Maturity Percentage: {assessment['maturity_percentage']}%")
    print(f"Description: {assessment['maturity_description']}")

    print(f"\n{'='*60}")
    print("DIMENSION SCORES")
    print(f"{'='*60}\n")

    for dimension, score in assessment['dimension_scores'].items():
        if score is not None:
            print(f"  {dimension}: {score:.2f}")
        else:
            print(f"  {dimension}: No data")

    print(f"\n{'='*60}")
    print("VARIANCE ANALYSIS")
    print(f"{'='*60}\n")

    for dimension, analysis in assessment['variance_analysis'].items():
        print(f"\n{dimension}:")
        print(f"  CEO: {analysis['ceo_score']:.2f}")
        print(f"  Tech Lead: {analysis['tech_score']:.2f}")
        print(f"  Staff: {analysis['staff_score']:.2f}")
        print(f"  Weighted: {analysis['weighted_score']:.2f}")
        print(f"  Variance: {analysis['variance']:.2f} ({analysis['level']} - {analysis['color']})")
        print(f"  Status: {analysis['description']}")

    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}\n")

    for i, rec in enumerate(assessment['recommendations'], 1):
        print(f"{i}. {rec}")

    print(f"\n{'='*60}")
    print("VALIDATION CHECKS")
    print(f"{'='*60}\n")

    # Check if scores are reasonable
    if 1.0 <= assessment['overall_score'] <= 5.0:
        print("✓ Overall score is within valid range (1-5)")
    else:
        print(f"✗ Overall score OUT OF RANGE: {assessment['overall_score']}")

    if 0 <= assessment['maturity_percentage'] <= 100:
        print("✓ Maturity percentage is within valid range (0-100)")
    else:
        print(f"✗ Maturity percentage OUT OF RANGE: {assessment['maturity_percentage']}%")

    # Check if dimensions with missing staff still have reasonable scores
    dimensions_with_data = [d for d, s in assessment['dimension_scores'].items() if s is not None]
    print(f"✓ {len(dimensions_with_data)}/5 dimensions have valid scores")

    print("\nTest complete!")


if __name__ == '__main__':
    main()
