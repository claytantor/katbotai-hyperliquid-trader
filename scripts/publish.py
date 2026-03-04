#!/usr/bin/env python3

"""
Clawhub Publish Script

This script automates publishing the katbot-trading skill to clawhub.
It validates prerequisites, checks for required files, and runs the publish
command with appropriate error handling.

Usage:
    python scripts/publish.py [--dry-run] [--verbose] [--skill-dir PATH]

"""

import argparse
import sys
import subprocess
import os
import json
from pathlib import Path
from typing import Optional
import re


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'='*51}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*51}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print an error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def log_verbose(text: str, verbose: bool) -> None:
    """Print verbose output if enabled"""
    if verbose:
        print(f"{Colors.BLUE}  → {text}{Colors.RESET}")


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    return subprocess.run(['which', cmd], capture_output=True).returncode == 0


def check_prerequisites(verbose: bool) -> bool:
    """Check if all required tools are installed"""
    print_info("Checking prerequisites...")

    # Check clawhub CLI
    if not check_command_exists('clawhub'):
        print_error("clawhub CLI not found. Please install clawhub first.")
        print("    Visit: https://github.com/clawai/clawhub-cli")
        return False
    print_success("clawhub CLI is installed")

    # Check Python version
    py_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}"
        f".{sys.version_info.micro}"
    )
    print_success(f"Python {py_version} is installed")
    log_verbose(f"Python executable: {sys.executable}", verbose)

    # Check git
    if not check_command_exists('git'):
        print_warning("git not found. Some features may not work properly.")
    else:
        print_success("git is installed")

    return True


def extract_skill_name(skill_md_path: Path) -> Optional[str]:
    """Extract skill name from SKILL.md"""
    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()
            match = re.search(r'^name:\s*(.+?)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None


def extract_skill_version(skill_md_path: Path) -> Optional[str]:
    """Extract skill version from SKILL.md"""
    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()
            match = re.search(r'^version:\s*(.+?)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None


def validate_skill_structure(skill_dir: Path, verbose: bool) -> bool:
    """Validate the skill directory structure"""
    print_info("Validating skill structure...")

    # Check skill directory exists
    if not skill_dir.exists():
        print_error(f"Skill directory not found: {skill_dir}")
        return False
    print_success("Skill directory exists")
    log_verbose(str(skill_dir), verbose)

    # Check SKILL.md exists
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print_error(f"SKILL.md not found in {skill_dir}")
        return False
    print_success("SKILL.md found")

    # Check tools directory
    tools_dir = skill_dir / "tools"
    if not tools_dir.exists():
        print_warning("tools directory not found in skill directory")
    else:
        print_success("tools directory exists")
        py_files = list(tools_dir.glob("*.py"))
        log_verbose(f"Found {len(py_files)} Python tool files", verbose)

    # Validate SKILL.md has required metadata
    with open(skill_md) as f:
        content = f.read()
        if 'name:' not in content:
            print_error("SKILL.md missing required 'name' field")
            return False
        if 'version:' not in content:
            print_error("SKILL.md missing required 'version' field")
            return False

    print_success("SKILL.md has required metadata")

    skill_name = extract_skill_name(skill_md)
    if skill_name:
        log_verbose(f"Skill name: {skill_name}", verbose)
    
    skill_version = extract_skill_version(skill_md)
    if skill_version:
        log_verbose(f"Skill version: {skill_version}", verbose)

    return True


def check_git_status(project_root: Path, skill_dir: Path, verbose: bool) -> None:
    """Check git status of the project"""
    print_info("Checking git status...")

    # Check if in git repo
    result = subprocess.run(
        ['git', '-C', str(project_root), 'rev-parse', '--git-dir'],
        capture_output=True
    )
    if result.returncode != 0:
        print_warning("Not in a git repository")
        return

    # Check for uncommitted changes
    result = subprocess.run(
        ['git', '-C', str(project_root), 'diff-index', '--quiet', 'HEAD', '--'],
        capture_output=True
    )
    if result.returncode != 0:
        print_warning("Uncommitted changes detected")
        log_verbose("You may want to commit your changes before publishing", verbose)
    else:
        print_success("Working directory is clean")

    # Check for untracked files in skill directory
    result = subprocess.run(
        ['git', '-C', str(project_root), 'ls-files', '--others',
         '--exclude-standard', str(skill_dir)],
        capture_output=True,
        text=True
    )
    untracked_count = len([l for l in result.stdout.split('\n') if l.strip()])
    if untracked_count > 0:
        print_warning(f"{untracked_count} untracked files in skill directory")


def publish_skill(
    skill_dir: Path,
    dry_run: bool,
    verbose: bool
) -> bool:
    """Publish the skill to clawhub"""
    print_header("Publishing Skill to Clawhub")

    skill_version = extract_skill_version(skill_dir / "SKILL.md")
    if not skill_version:
        print_error("Version not found in SKILL.md. Please add 'version: X.Y.Z'")
        return False

    cmd = ['clawhub', 'publish', '--version', skill_version]

    if dry_run:
        print_info("Running in DRY-RUN mode (no changes will be made)")
        print()
        print("Command that would be executed:")
        print(f"  {' '.join(cmd)} {skill_dir}")
        print()
        skill_name = extract_skill_name(skill_dir / "SKILL.md")
        if skill_name:
            print_info(f"Skill name: {skill_name}")
        print_info(f"Skill version: {skill_version}")
        print_info(f"Skill directory: {skill_dir}")
        print()
        print_info("Run without --dry-run to publish")
        return True

    print_info(f"Publishing skill (version: {skill_version})...")
    cmd.append(str(skill_dir))

    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print_success("Skill published successfully!")
            return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to publish skill (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print_error("clawhub command not found")
        return False

    return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Publish the katbot-trading skill to clawhub'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be published without actually publishing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--skill-dir',
        type=Path,
        help='Custom skill directory path (default: skills/katbot-trading)'
    )

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    skill_dir = args.skill_dir or (project_root / 'skills' / 'katbot-trading')

    # Run checks
    print_header("Clawhub Publish Script")

    if not check_prerequisites(args.verbose):
        sys.exit(1)
    print()

    if not validate_skill_structure(skill_dir, args.verbose):
        sys.exit(1)
    print()

    check_git_status(project_root, skill_dir, args.verbose)
    print()

    if not publish_skill(skill_dir, args.dry_run, args.verbose):
        print()
        print_error("Publication failed")
        sys.exit(1)

    print()
    print_success("Complete!")
    print()


if __name__ == '__main__':
    main()
