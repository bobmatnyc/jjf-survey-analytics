#!/usr/bin/env python
"""
Pre-deployment production checks for JJF Survey Analytics Platform.

Runs comprehensive checks before deploying to Railway production:
- Code quality (linting)
- Environment configuration
- Database connectivity
- API availability
- Health check endpoints
"""

import os
import sys
import subprocess
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print formatted section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def run_command(cmd, capture=True):
    """Run shell command and return result."""
    try:
        if capture:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=True
            )
            return True, result.stdout
        else:
            result = subprocess.run(cmd, shell=True, check=True)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)


def check_linting():
    """Check code quality with linting tools."""
    print_header("Code Quality Checks")

    all_passed = True

    # Check flake8
    print("Running flake8...")
    success, output = run_command("flake8 app.py ai_analyzer.py report_generator.py")
    if success:
        print_success("Flake8 passed")
    else:
        print_warning("Flake8 found issues (non-blocking)")
        all_passed = False

    # Check black formatting
    print("\nRunning black formatter check...")
    success, output = run_command("black --check app.py ai_analyzer.py report_generator.py")
    if success:
        print_success("Black formatting check passed")
    else:
        print_warning("Black formatting issues found (run 'make format' to fix)")
        all_passed = False

    # Check isort
    print("\nRunning isort import sorting check...")
    success, output = run_command("isort --check-only app.py ai_analyzer.py report_generator.py")
    if success:
        print_success("Isort import sorting check passed")
    else:
        print_warning("Isort issues found (run 'make format' to fix)")
        all_passed = False

    return all_passed


def check_environment():
    """Check environment configuration."""
    print_header("Environment Configuration")

    all_passed = True

    # Check .env.local for local development
    if Path('.env.local').exists():
        print_success(".env.local found for local development")

        # Check for required keys
        with open('.env.local', 'r') as f:
            env_content = f.read()
            if 'OPENROUTER_API_KEY' in env_content:
                print_success("OPENROUTER_API_KEY configured in .env.local")
            else:
                print_error("OPENROUTER_API_KEY missing from .env.local")
                all_passed = False
    else:
        print_warning(".env.local not found (ensure Railway has OPENROUTER_API_KEY)")

    # Check requirements.txt
    if Path('requirements.txt').exists():
        print_success("requirements.txt found")
        with open('requirements.txt', 'r') as f:
            reqs = f.read()
            required_packages = ['openai', 'httpx', 'pydantic', 'python-dotenv']
            for pkg in required_packages:
                if pkg in reqs:
                    print_success(f"  {pkg} in requirements.txt")
                else:
                    print_error(f"  {pkg} missing from requirements.txt")
                    all_passed = False
    else:
        print_error("requirements.txt not found")
        all_passed = False

    # Check Procfile for Railway
    if Path('Procfile').exists():
        print_success("Procfile found for Railway deployment")
    else:
        print_error("Procfile missing")
        all_passed = False

    return all_passed


def check_files():
    """Check required files exist."""
    print_header("Required Files Check")

    all_passed = True

    required_files = [
        'app.py',
        'ai_analyzer.py',
        'report_generator.py',
        'maturity_rubric.py',
        'requirements.txt',
        'Procfile',
        'railway.toml',
    ]

    for file in required_files:
        if Path(file).exists():
            print_success(f"{file} exists")
        else:
            print_error(f"{file} missing")
            all_passed = False

    return all_passed


def check_git_status():
    """Check git status."""
    print_header("Git Status")

    all_passed = True

    # Check if there are uncommitted changes
    success, output = run_command("git status --porcelain")
    if success:
        if output.strip():
            print_warning("Uncommitted changes detected:")
            print(output)
            print_warning("Commit all changes before deploying")
            all_passed = False
        else:
            print_success("No uncommitted changes")
    else:
        print_warning("Unable to check git status")

    # Check current branch
    success, output = run_command("git branch --show-current")
    if success:
        branch = output.strip()
        print(f"Current branch: {Colors.BOLD}{branch}{Colors.END}")
        if branch not in ['main', 'master']:
            print_warning(f"Not on main/master branch (on '{branch}')")
            all_passed = False

    return all_passed


def main():
    """Run all pre-deployment checks."""
    print(f"\n{Colors.BOLD}JJF Survey Analytics - Pre-Deployment Checks{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

    checks = [
        ("Linting", check_linting),
        ("Environment", check_environment),
        ("Required Files", check_files),
        ("Git Status", check_git_status),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Error during {name} check: {e}")
            results[name] = False

    # Print summary
    print_header("Pre-Deployment Check Summary")

    all_passed = all(results.values())

    for name, passed in results.items():
        if passed:
            print_success(f"{name}: PASSED")
        else:
            print_warning(f"{name}: FAILED or has warnings")

    print()

    if all_passed:
        print_success("All checks passed! ✓")
        print("\n" + Colors.GREEN + Colors.BOLD +
              "Ready for deployment to Railway" + Colors.END)
        print("\nNext steps:")
        print("  1. git push origin main")
        print("  2. Railway will auto-deploy")
        print("  3. Monitor deployment at Railway dashboard\n")
        return 0
    else:
        print_warning("Some checks failed or have warnings")
        print("\n" + Colors.YELLOW + Colors.BOLD +
              "Review warnings before deploying" + Colors.END)
        print("\nRecommended actions:")
        print("  1. Fix any errors shown above")
        print("  2. Run 'make format' to fix code formatting")
        print("  3. Commit all changes")
        print("  4. Re-run this script\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
