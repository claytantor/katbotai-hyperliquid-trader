.PHONY: publish publish-bump publish-bump-build publish-dry-run publish-verbose publish-help

# Publish the skill to clawhub
publish:
	@bash scripts/publish.sh

# Auto-increment minor version and publish
publish-bump:
	@bash scripts/publish.sh --bump

# Auto-increment patch/build number and publish
publish-bump-build:
	@bash scripts/publish.sh --bump-patch

# Perform a dry-run of the publish process
publish-dry-run:
	@bash scripts/publish.sh --dry-run

# Publish with verbose output
publish-verbose:
	@bash scripts/publish.sh --verbose

# Show publish help
publish-help:
	@bash scripts/publish.sh --help

# Alternative Python-based publish target
publish-py:
	@python scripts/publish.py

publish-py-dry-run:
	@python scripts/publish.py --dry-run

publish-py-verbose:
	@python scripts/publish.py --verbose

.PHONY: help
help:
	@echo "Clawhub Publishing Targets:"
	@echo "  make publish          - Publish skill to clawhub"
	@echo "  make publish-bump     - Auto-increment minor version and publish"
	@echo "  make publish-bump-build - Auto-increment patch/build number and publish"
	@echo "  make publish-dry-run  - Test publish without making changes"
	@echo "  make publish-verbose  - Publish with verbose output"
	@echo "  make publish-help     - Show detailed publish help"
	@echo ""
	@echo "Python-based alternatives:"
	@echo "  make publish-py       - Python version of publish"
	@echo ""
	@echo "For CLI usage without make:"
	@echo "  ./scripts/publish.sh [--dry-run] [--verbose]"
	@echo "  python scripts/publish.py [--dry-run] [--verbose]"
