#!/bin/bash

###############################################################################
# Clawhub Publish Script
#
# This script automates publishing the katbot-trading skill to clawhub.
# It validates prerequisites, checks for required files, and runs the publish
# command with appropriate error handling.
#
# Usage:
#   ./scripts/publish.sh [--dry-run] [--verbose] [--skill-dir PATH]
#
###############################################################################

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILL_DIR="${PROJECT_ROOT}/skills/katbot-trading"
DRY_RUN=false
VERBOSE=false
BUMP=false
BUMP_PART="minor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# Functions
###############################################################################

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}  → $1${NC}"
    fi
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --dry-run       Show what would be published without actually publishing
    --verbose       Enable verbose output
    --skill-dir     Custom skill directory path (default: skills/katbot-trading)
    --bump          Auto-increment the minor version in SKILL.md before publishing
    --bump-patch    Auto-increment the patch/build version (X.Y.Z+1) before publishing
    --help          Show this help message

Examples:
    # Publish normally
    ./scripts/publish.sh

    # Auto-increment minor version and publish
    ./scripts/publish.sh --bump

    # Test publish without making changes
    ./scripts/publish.sh --dry-run

    # Verbose output
    ./scripts/publish.sh --verbose
EOF
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if clawhub CLI is installed
    if ! command -v clawhub &> /dev/null; then
        print_error "clawhub CLI not found. Please install clawhub first."
        echo "    Visit: https://github.com/clawai/clawhub-cli"
        exit 1
    fi
    print_success "clawhub CLI is installed"
    log_verbose "$(clawhub --version 2>/dev/null || echo 'version check skipped')"

    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_warning "git not found. Some features may not work properly."
    else
        print_success "git is installed"
    fi
}

validate_skill_structure() {
    print_info "Validating skill structure..."

    # Check if skill directory exists
    if [ ! -d "$SKILL_DIR" ]; then
        print_error "Skill directory not found: $SKILL_DIR"
        exit 1
    fi
    print_success "Skill directory exists"
    log_verbose "$SKILL_DIR"

    # Check if SKILL.md exists
    if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
        print_error "SKILL.md not found in $SKILL_DIR"
        exit 1
    fi
    print_success "SKILL.md found"

    # Check if tools directory exists
    if [ ! -d "$SKILL_DIR/tools" ]; then
        print_warning "tools directory not found in skill directory"
    else
        print_success "tools directory exists"
        local tool_count=$(find "$SKILL_DIR/tools" -type f -name "*.py" | wc -l)
        log_verbose "Found $tool_count Python tool files"
    fi

    # Validate SKILL.md has required metadata
    if ! grep -q "^name:" "$SKILL_DIR/SKILL.md"; then
        print_error "SKILL.md missing required 'name' field"
        exit 1
    fi
    print_success "SKILL.md has required metadata"

    local skill_name=$(grep "^name:" "$SKILL_DIR/SKILL.md" | head -1 | sed 's/.*: //' | xargs)
    log_verbose "Skill name: $skill_name"

    # Check for version
    if ! grep -q "^version:" "$SKILL_DIR/SKILL.md"; then
        print_error "SKILL.md missing required 'version' field"
        exit 1
    fi
    local skill_version=$(grep "^version:" "$SKILL_DIR/SKILL.md" | head -1 | sed 's/.*: //' | xargs)
    log_verbose "Skill version: $skill_version"
}

check_git_status() {
    print_info "Checking git status..."

    # Check if we're in a git repository
    if ! git -C "$PROJECT_ROOT" rev-parse --git-dir > /dev/null 2>&1; then
        print_warning "Not in a git repository"
        return
    fi

    # Check for uncommitted changes
    if ! git -C "$PROJECT_ROOT" diff-index --quiet HEAD --; then
        print_warning "Uncommitted changes detected"
        log_verbose "You may want to commit your changes before publishing"
    else
        print_success "Working directory is clean"
    fi

    # Check for untracked files in skill directory
    local untracked=$(git -C "$PROJECT_ROOT" ls-files --others --exclude-standard "$SKILL_DIR" | wc -l)
    if [ "$untracked" -gt 0 ]; then
        print_warning "$untracked untracked files in skill directory"
    fi
}

bump_version() {
    local part="${1:-minor}"  # major, minor, or patch
    local skill_md="$SKILL_DIR/SKILL.md"
    local current=$(grep "^version:" "$skill_md" | head -1 | sed 's/.*: //' | xargs)
    if [ -z "$current" ]; then
        print_error "Cannot bump: version not found in SKILL.md"
        exit 1
    fi

    local major minor patch
    IFS='.' read -r major minor patch <<< "$current"
    local new_version
    case "$part" in
        major) new_version="$((major + 1)).0.0" ;;
        minor) new_version="${major}.$((minor + 1)).0" ;;
        patch) new_version="${major}.${minor}.$((patch + 1))" ;;
        *)
            print_error "Unknown bump type: $part (use major, minor, or patch)"
            exit 1
            ;;
    esac

    sed -i "s/^version: .*/version: ${new_version}/" "$skill_md"
    print_success "Version bumped: ${current} → ${new_version}"
}

publish_skill() {
    print_header "Publishing Skill to Clawhub"

    local skill_version=$(grep "^version:" "$SKILL_DIR/SKILL.md" | head -1 | sed 's/.*: //' | xargs)
    if [ -z "$skill_version" ]; then
        print_error "Version not found in SKILL.md. Please add 'version: X.Y.Z'"
        return 1
    fi

    local publish_cmd="clawhub publish --version $skill_version"
    
    if [ "$DRY_RUN" = true ]; then
        print_info "Running in DRY-RUN mode (no changes will be made)"
        echo ""
        echo "Command that would be executed:"
        echo "  $publish_cmd \"$SKILL_DIR\""
        echo ""
        print_info "Skill directory: $SKILL_DIR"
        print_info "Skill name: $(grep "^name:" "$SKILL_DIR/SKILL.md" | head -1 | sed 's/.*: //' | xargs)"
        print_info "Skill version: $skill_version"
        echo ""
        print_info "Run without --dry-run to publish"
        return 0
    fi

    print_info "Publishing skill (version: $skill_version)..."
    if $publish_cmd "$SKILL_DIR"; then
        print_success "Skill published successfully!"
        return 0
    else
        print_error "Failed to publish skill"
        return 1
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skill-dir)
                SKILL_DIR="$2"
                shift 2
                ;;
            --bump)
                BUMP=true
                BUMP_PART="minor"
                shift
                ;;
            --bump-patch)
                BUMP=true
                BUMP_PART="patch"
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    print_header "Clawhub Publish Script"
    echo ""

    # Run checks and publish
    check_prerequisites
    echo ""
    
    validate_skill_structure
    echo ""
    
    check_git_status
    echo ""

    if [ "$BUMP" = true ]; then
        bump_version "$BUMP_PART"
        echo ""
    fi

    if ! publish_skill; then
        echo ""
        print_error "Publication failed"
        exit 1
    fi

    echo ""
    print_success "Complete!"
    echo ""
}

# Run main function
main "$@"
