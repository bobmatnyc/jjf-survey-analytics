#!/usr/bin/env python3
"""
Update version.py with build metadata
Usage: python scripts/update_version.py [patch|minor|major]
"""

import datetime
import os
import re
import subprocess
import sys


def get_git_info():
    """Get git commit and branch info."""
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        return commit, branch
    except Exception:
        return None, None


def get_current_version(version_file='version.py'):
    """Read current version from version.py."""
    with open(version_file, 'r') as f:
        content = f.read()

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return "1.0.0"


def bump_version(version, bump_type='patch'):
    """Bump version number."""
    major, minor, patch = map(int, version.split('.'))

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def update_version_file(new_version, version_file='version.py'):
    """Update version.py with new version and build info."""
    commit, branch = get_git_info()
    build_date = datetime.datetime.now().isoformat()

    # Read current content
    with open(version_file, 'r') as f:
        content = f.read()

    # Update version
    content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )

    # Update build date
    content = re.sub(
        r'__build_date__\s*=\s*.*',
        f'__build_date__ = "{build_date}"',
        content
    )

    # Update git commit
    if commit:
        content = re.sub(
            r'__git_commit__\s*=\s*.*',
            f'__git_commit__ = "{commit}"',
            content
        )

    # Update git branch
    if branch:
        content = re.sub(
            r'__git_branch__\s*=\s*.*',
            f'__git_branch__ = "{branch}"',
            content
        )

    # Write updated content
    with open(version_file, 'w') as f:
        f.write(content)

    return new_version


def main():
    """Main entry point."""
    version_file = 'version.py'

    # Get bump type from args
    bump_type = sys.argv[1] if len(sys.argv) > 1 else 'patch'

    if bump_type not in ['patch', 'minor', 'major', 'build']:
        print(f"Error: Invalid bump type '{bump_type}'")
        print("Usage: python scripts/update_version.py [patch|minor|major|build]")
        sys.exit(1)

    # Get current version
    current_version = get_current_version(version_file)
    print(f"Current version: {current_version}")

    # Bump version (unless just build)
    if bump_type == 'build':
        new_version = current_version
        print(f"Updating build metadata only...")
    else:
        new_version = bump_version(current_version, bump_type)
        print(f"Bumping {bump_type} version to: {new_version}")

    # Update version file
    update_version_file(new_version, version_file)
    print(f"✅ Version updated successfully!")

    # Show version info
    print()
    subprocess.run([sys.executable, version_file])


if __name__ == '__main__':
    main()
