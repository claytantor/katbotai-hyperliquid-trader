# Publishing the Katbot-Trading Skill to Clawhub

This directory contains automated scripts to publish the `katbot-trading` skill to clawhub. Two versions are provided: a Bash script and a Python script, providing flexibility based on your environment.

## Quick Start

### Using Make (Recommended)

```bash
# Publish skill
make publish

# Test publish without making changes
make publish-dry-run

# Publish with verbose output
make publish-verbose
```

### Using Bash Script Directly

```bash
./scripts/publish.sh

# Or with options
./scripts/publish.sh --dry-run
./scripts/publish.sh --verbose
```

### Using Python Script

```bash
python scripts/publish.py

# Or with options
python scripts/publish.py --dry-run
python scripts/publish.py --verbose
```

## Features

Both scripts provide the following functionality:

✅ **Prerequisites Check**
- Verifies clawhub CLI is installed
- Confirms git and Python availability
- Provides helpful install instructions if tools are missing

✅ **Skill Structure Validation**
- Confirms skill directory exists and has proper structure
- Validates SKILL.md with required metadata
- Checks for tools directory and counts Python files
- Extracts and displays skill name

✅ **Git Status Monitoring**
- Detects uncommitted changes
- Identifies untracked files in skill directory
- Encourages clean commits before publishing

✅ **Dry-Run Mode**
- Preview what would be published without making changes
- Shows the exact command that would be executed
- Perfect for CI/CD pipelines and testing

✅ **Verbose Logging**
- Detailed output showing all validation steps
- Useful for debugging and understanding the process

## Command-Line Options

### Common Options

| Option | Usage | Purpose |
|--------|-------|---------|
| `--dry-run` | `./scripts/publish.sh --dry-run` | Preview publish without making changes |
| `--verbose` | `./scripts/publish.sh --verbose` | Show detailed output for all steps |
| `--skill-dir PATH` | `./scripts/publish.sh --skill-dir ./my-skill` | Publish from custom skill directory |
| `--help` | `./scripts/publish.sh --help` | Show help message (bash only) |

## Requirements

Before using these scripts, ensure you have:

1. **Clawhub CLI** installed:
   ```bash
   # Install from https://github.com/clawai/clawhub-cli
   ```

2. **Git** installed (optional but recommended):
   ```bash
   git --version
   ```

3. **Python 3.7+** (for Python script):
   ```bash
   python --version
   ```

## Workflow Examples

### 1. Test Before Publishing

```bash
# Always do a dry-run first to see what would happen
./scripts/publish.sh --dry-run

# Review the output, then publish for real
./scripts/publish.sh
```

### 2. Debug Publishing Issues

```bash
# Use verbose mode to see detailed output
./scripts/publish.sh --verbose

# Or with the Python script
python scripts/publish.py --verbose
```

### 3. CI/CD Integration

```bash
# In your CI/CD pipeline, use dry-run to test
./scripts/publish.sh --dry-run || exit 1

# Then publish
./scripts/publish.sh || exit 1
```

### 4. Publish from Different Directory

```bash
# Publish from a specific skill directory
./scripts/publish.sh --skill-dir ./custom-skill-dir
```

## Environment Setup

### For Clawhub CLI

Ensure you're authenticated with clawhub:

```bash
# Check if clawhub is configured
clawhub auth status

# Login if needed
clawhub login
```

### For Git Integration

The scripts check your git status. For best results:

```bash
# Commit your changes before publishing
git add .
git commit -m "Prepare skill for publishing"

# Then publish
./scripts/publish.sh
```

## Output Examples

### Successful Publish

```
===================================================
Clawhub Publish Script
===================================================

ℹ Checking prerequisites...
✓ clawhub CLI is installed
✓ Python 3.11 is installed
✓ git is installed

ℹ Validating skill structure...
✓ Skill directory exists
✓ SKILL.md found
✓ tools directory exists
✓ SKILL.md has required metadata

ℹ Checking git status...
✓ Working directory is clean

===================================================
Publishing Skill to Clawhub
===================================================

ℹ Publishing skill...
✓ Skill published successfully!

✓ Complete!
```

### Dry-Run Mode

```
===================================================
Clawhub Publish Script
===================================================

...

===================================================
Publishing Skill to Clawhub
===================================================

ℹ Running in DRY-RUN mode (no changes will be made)

Command that would be executed:
  clawhub publish /home/user/project/skills/katbot-trading

ℹ Skill name: katbot-trading
ℹ Skill directory: /home/user/project/skills/katbot-trading

ℹ Run without --dry-run to publish

✓ Complete!
```

## Troubleshooting

### "clawhub CLI not found"

**Solution**: Install clawhub CLI from https://github.com/clawai/clawhub-cli

```bash
# Example installation (check repo for latest instructions)
npm install -g @clawhub/cli
```

### "SKILL.md not found"

**Solution**: Ensure you're in the correct directory or use `--skill-dir` option:

```bash
./scripts/publish.sh --skill-dir ./skills/katbot-trading
```

### "Uncommitted changes detected"

**Solution**: Commit your changes before publishing:

```bash
git add .
git commit -m "Update skill files"
./scripts/publish.sh
```

### Module Not Found Error (Python script)

**Solution**: Ensure Python is correctly installed:

```bash
python --version  # Should be 3.7 or higher
```

## Script Comparison

| Feature | Bash Script | Python Script |
|---------|-------------|---------------|
| Dependencies | bash, standard utils | python 3.7+ |
| Portability | Linux/macOS/Windows (WSL) | Linux/macOS/Windows |
| Performance | Fast | Slightly slower |
| Readability | Shell syntax | Python syntax |
| Extensibility | Required shell knowledge | Python familiarity |
| Debugging | Standard bash tools | Python debugger |

## Integration with GitHub Actions

Add to your `.github/workflows/publish.yml`:

```yaml
name: Publish to Clawhub

on:
  push:
    branches: [ main ]
    paths:
      - 'skills/katbot-trading/**'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install clawhub CLI
        run: npm install -g @clawhub/cli
      
      - name: Publish skill (dry-run)
        run: ./scripts/publish.sh --dry-run
      
      - name: Publish skill
        run: ./scripts/publish.sh
        env:
          CLAWHUB_API_KEY: ${{ secrets.CLAWHUB_API_KEY }}
```

## Maintenance

To keep these scripts updated:

1. Check clawhub CLI documentation for API changes
2. Update SKILL.md when modifying skill metadata
3. Test with `--dry-run` before publishing
4. Review git status before publishing

## Support

For issues with:
- **Clawhub CLI**: Visit https://github.com/clawai/clawhub-cli
- **This skill**: Check the main project README
- **Publishing scripts**: Review the script source code (well-documented)

## License

These publishing scripts are part of the katbotai-hyperliquid-trader project.
