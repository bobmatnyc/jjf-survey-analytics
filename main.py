#!/usr/bin/env python3
"""
Main entry point for the Surveyor application.

This script provides a convenient way to run the CLI without
having to use the full module path.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from surveyor.cli.main import cli

if __name__ == "__main__":
    cli()
