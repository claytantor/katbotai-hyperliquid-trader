#!/usr/bin/env bash
# Clawhub Publishing Quick Reference
# Print this file for a quick cheat sheet

cat << 'EOF'
┌────────────────────────────────────────────────────────────────┐
│          CLAWHUB PUBLISH - QUICK REFERENCE                     │
└────────────────────────────────────────────────────────────────┘

📋 BASIC USAGE
──────────────────────────────────────────────────────────────────

  Test Before Publishing (DRY-RUN):
    $ make publish-dry-run
    OR: ./scripts/publish.sh --dry-run

  Publish for Real:
    $ make publish
    OR: ./scripts/publish.sh

  Show Help:
    $ make publish-help
    OR: ./scripts/publish.sh --help

🔧 MAKE TARGETS
──────────────────────────────────────────────────────────────────

  make publish           Publish skill to clawhub
  make publish-dry-run   Test publish without changes
  make publish-verbose   Publish with detailed output
  make publish-help      Show detailed help
  make publish-py        Use Python version
  make help              Show all make targets

💻 DIRECT SCRIPT USAGE
──────────────────────────────────────────────────────────────────

  Bash Script:
    ./scripts/publish.sh [OPTIONS]
    ./scripts/publish.sh --dry-run
    ./scripts/publish.sh --verbose
    ./scripts/publish.sh --skill-dir ./my-skill

  Python Script:
    python scripts/publish.py [OPTIONS]
    python scripts/publish.py --dry-run
    python scripts/publish.py --verbose

⚙️ WORKFLOW
──────────────────────────────────────────────────────────────────

  1. Make changes to the skill:
     $ # Edit files in skills/katbot-trading/

  2. Commit to git:
     $ git add .
     $ git commit -m "Update skill features"

  3. Test publish:
     $ make publish-dry-run

  4. Publish:
     $ make publish

✅ VALIDATION CHECKS
──────────────────────────────────────────────────────────────────

  Scripts automatically check:
  ✓ clawhub CLI is installed
  ✓ Python/bash availability
  ✓ Skill directory exists
  ✓ SKILL.md has required metadata
  ✓ Git status (uncommitted changes)
  ✓ Untracked files in skill directory

⚠️  TROUBLESHOOTING
──────────────────────────────────────────────────────────────────

  "clawhub CLI not found"
  → Install from: https://github.com/clawai/clawhub-cli

  "SKILL.md not found"
  → Run from project root or use: --skill-dir ./path

  "Uncommitted changes detected"
  → Run: git add . && git commit -m "message"

📚 DOCUMENTATION
──────────────────────────────────────────────────────────────────

  Quick Start:       PUBLISH_SETUP.md
  Detailed Guide:    scripts/PUBLISH.md
  Skill Config:      skills/katbot-trading/SKILL.md
  Main README:       README.md

🚀 ONE-LINERS
──────────────────────────────────────────────────────────────────

  Test & Publish:
    $ make publish-dry-run && make publish

  Commit & Publish:
    $ git add . && git commit -m "Ready to publish" && make publish

  Verbose Publishing:
    $ make publish-verbose

  With Custom Directory:
    $ ./scripts/publish.sh --skill-dir ./skills/my-skill

📖 MORE HELP
──────────────────────────────────────────────────────────────────

  ./scripts/publish.sh --help
  python scripts/publish.py --help
  cat scripts/PUBLISH.md

EOF
