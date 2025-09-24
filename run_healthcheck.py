#!/usr/bin/env python3
"""
Convenience script to run health checks with easy command-line interface.

This script provides a simple way to run the comprehensive health check system
without needing to remember the full healthcheck.py command syntax.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add healthcheck directory to path
sys.path.insert(0, str(Path(__file__).parent))

from healthcheck import run_complete_health_check, create_health_check_report, get_version


def main():
    """Main entry point for the health check runner."""
    parser = argparse.ArgumentParser(
        description="JJF Survey Analytics Health Check System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all health checks
  %(prog)s --format json      # Output in JSON format
  %(prog)s --format html      # Output in HTML format
  %(prog)s --quiet            # Only show summary
  %(prog)s --version          # Show version information

Categories checked:
  • API Keys & Authentication
  • External Dependencies  
  • End-to-End Tests
  • Configuration Validation

For detailed documentation, see HEALTHCHECK_README.md
        """
    )
    
    parser.add_argument(
        '--format', 
        choices=['text', 'json', 'html'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only show summary, not detailed results'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file (default: stdout)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Health Check System v{get_version()}'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    args = parser.parse_args()
    
    # Run the health check
    try:
        print("🏥 Running comprehensive health check...", file=sys.stderr)
        results = asyncio.run(run_complete_health_check())
        
        # Create report
        if args.quiet and args.format == 'text':
            # Just show summary
            status_emoji = {'pass': '✅', 'fail': '❌', 'warning': '⚠️'}
            if not args.no_color:
                emoji = status_emoji.get(results['overall_status'], '❓')
            else:
                emoji = results['overall_status'].upper()
            
            report = f"{emoji} {results['summary']['passed']}/{results['summary']['total']} checks passed"
            if results['summary']['failed'] > 0:
                report += f", {results['summary']['failed']} failed"
            if results['summary']['warnings'] > 0:
                report += f", {results['summary']['warnings']} warnings"
        else:
            report = create_health_check_report(results, args.format)
        
        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}", file=sys.stderr)
        else:
            print(report)
        
        # Exit with appropriate code
        exit_code = 0 if results['overall_status'] == 'pass' else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n❌ Health check interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"❌ Health check failed with error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
