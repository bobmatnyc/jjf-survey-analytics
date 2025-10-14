#!/usr/bin/env python3
"""
Test script for text consolidation feature.
Tests the consolidate_text method with real examples.
"""

import os
from ai_analyzer import AIAnalyzer

# Test examples from the requirements
EXAMPLES = {
    "overall_description": {
        "original": "Functional systems with integration gaps",
        "target_length": 55,
        "expected_range": (40, 60)
    },
    "program_technology": {
        "original": "The organization exhibits a reactive, decentralized approach to technology adoption, characterized by ad-hoc purchasing and platform selection. There's a clear need for a more strategic, holistic technology governance framework that emphasizes centralized planning, integration, and comprehensive policy development.",
        "target_length": 120,
        "expected_range": (100, 150)
    },
    "business_systems": {
        "original": "Staff responses reveal critical gaps in business system accessibility and functionality, particularly around financial management tools. There is a strong organizational need for more integrated, user-friendly systems that enable real-time decision-making and streamline complex operational workflows.",
        "target_length": 120,
        "expected_range": (100, 150)
    },
    "data_management": {
        "original": "The organization is experiencing significant data management challenges, characterized by data quality degradation and unclear data utilization strategies. While multiple platforms are being used, there are fundamental gaps in data integrity, access, and analytical capabilities that need strategic intervention.",
        "target_length": 120,
        "expected_range": (100, 150)
    },
    "infrastructure": {
        "original": "The organization is experiencing significant infrastructure maturity challenges, characterized by ad-hoc management, lack of standardized processes, and insufficient dedicated resources. However, there's an emerging awareness of the need for strategic infrastructure development to support organizational growth and operational efficiency.",
        "target_length": 120,
        "expected_range": (100, 150)
    },
    "organizational_culture": {
        "original": "The organization demonstrates a mixed technological culture with pockets of innovation and enthusiasm, but suffers from inconsistent technology training, uneven adoption, and limited strategic investment in technological infrastructure. Leadership appears supportive of change, but systematic approaches to technology integration are lacking.",
        "target_length": 120,
        "expected_range": (100, 150)
    }
}


def test_consolidation():
    """Test the consolidation method with real examples."""
    print("=" * 80)
    print("TEXT CONSOLIDATION TEST")
    print("=" * 80)
    print()

    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ ERROR: OPENROUTER_API_KEY not found in environment")
        print("Please set the OPENROUTER_API_KEY in .env.local")
        return False

    try:
        # Initialize AI analyzer
        print("Initializing AIAnalyzer...")
        analyzer = AIAnalyzer()
        print("✓ AIAnalyzer initialized successfully\n")

        all_passed = True

        for test_name, test_data in EXAMPLES.items():
            original = test_data["original"]
            target = test_data["target_length"]
            min_len, max_len = test_data["expected_range"]

            print("-" * 80)
            print(f"TEST: {test_name.replace('_', ' ').title()}")
            print("-" * 80)
            print(f"Original ({len(original)} chars):")
            print(f"  {original}")
            print()

            # Consolidate
            consolidated = analyzer.consolidate_text(original, max_chars=target)

            print(f"Consolidated ({len(consolidated)} chars):")
            print(f"  {consolidated}")
            print()

            # Check if within expected range
            length_ok = min_len <= len(consolidated) <= max_len
            # If original is already short, no reduction is expected
            reduced_or_unchanged = len(consolidated) <= len(original)

            print(f"Results:")
            print(f"  Target: {target} chars")
            print(f"  Actual: {len(consolidated)} chars")
            print(f"  Reduction: {len(original) - len(consolidated)} chars ({(1 - len(consolidated)/len(original))*100:.1f}%)")
            print(f"  Length OK: {'✓' if length_ok else '✗'} (expected {min_len}-{max_len} chars)")
            print(f"  Reduced or Already Short: {'✓' if reduced_or_unchanged else '✗'}")
            print()

            if not (length_ok and reduced_or_unchanged):
                all_passed = False
                print("⚠️  TEST FAILED")
            else:
                print("✓ TEST PASSED")
            print()

        print("=" * 80)
        if all_passed:
            print("✓ ALL TESTS PASSED")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 80)

        return all_passed

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_consolidation()
    exit(0 if success else 1)
