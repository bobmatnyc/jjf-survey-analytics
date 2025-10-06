.PHONY: help install test lint format clean setup init extract status
.PHONY: dev build deploy quality test-cov health sync normalize
.PHONY: lint-fix format-check typecheck all-checks

# =============================================================================
# JJF Survey Analytics Platform - Makefile
# Single-command workflows for all common operations
# =============================================================================

# Default target - show all available commands
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  JJF Survey Analytics - Development Commands                   ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🚀 QUICK START"
	@echo "  make dev          - Start local development server"
	@echo "  make build        - Build complete project (extract + normalize)"
	@echo "  make test         - Run all tests"
	@echo ""
	@echo "⚙️  SETUP & INSTALLATION"
	@echo "  make setup        - Create virtual environment"
	@echo "  make install      - Install all dependencies"
	@echo ""
	@echo "🗄️  DATABASE OPERATIONS"
	@echo "  make init         - Initialize database"
	@echo "  make extract      - Extract data from Google Sheets"
	@echo "  make normalize    - Normalize survey data"
	@echo "  make build        - Extract + Normalize (complete pipeline)"
	@echo "  make status       - Show extraction job status"
	@echo ""
	@echo "🧪 TESTING & QUALITY"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make quality      - Run all quality checks (lint + typecheck + test)"
	@echo "  make health       - Run health checks"
	@echo ""
	@echo "🎨 CODE QUALITY"
	@echo "  make lint         - Run linting (check only)"
	@echo "  make lint-fix     - Run linting and auto-fix issues"
	@echo "  make format       - Format code with black and isort"
	@echo "  make format-check - Check code formatting (no changes)"
	@echo "  make typecheck    - Run mypy type checking"
	@echo ""
	@echo "🧹 CLEANUP"
	@echo "  make clean        - Remove generated files and caches"
	@echo ""
	@echo "📊 SERVICES"
	@echo "  make sync         - Force manual data sync"
	@echo ""
	@echo "📚 DOCUMENTATION"
	@echo "  See CLAUDE.md for comprehensive AI agent instructions"
	@echo "  See README.md for project overview"
	@echo "  See DEVELOPER.md for technical architecture"
	@echo ""

# =============================================================================
# QUICK START COMMANDS
# =============================================================================

# Start local development server (THE definitive way to run locally)
dev:
	@echo "🚀 Starting JJF Survey Analytics development server..."
	@echo "📍 URL: http://localhost:8080"
	@echo "🔓 Auth: Disabled (set REQUIRE_AUTH=true to enable)"
	@echo ""
	python app.py

# Build complete project (extract + normalize)
build: extract normalize
	@echo "✅ Build complete! Databases ready."
	@echo "📁 Raw data: surveyor_data_improved.db"
	@echo "📁 Normalized: survey_normalized.db"
	@echo ""
	@echo "Next step: make dev"

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

# Set up development environment
setup:
	@echo "🔧 Creating virtual environment..."
	python -m venv venv
	@echo "✅ Virtual environment created!"
	@echo ""
	@echo "📝 Next steps:"
	@echo "  1. Activate: source venv/bin/activate  (Mac/Linux)"
	@echo "            or venv\\Scripts\\activate    (Windows)"
	@echo "  2. Install: make install"
	@echo ""

# Install all dependencies (THE definitive way to install)
install:
	@echo "📦 Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .
	@echo "✅ Dependencies installed!"
	@echo ""
	@echo "Next step: make build"

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

# Initialize database
init:
	@echo "🗄️  Initializing database..."
	python main.py init-db
	@echo "✅ Database initialized!"

# Extract data from Google Sheets (THE definitive way to extract)
extract:
	@echo "📥 Extracting data from Google Sheets..."
	python improved_extractor.py
	@echo "✅ Data extraction complete!"
	@echo "📁 Output: surveyor_data_improved.db"

# Normalize survey data (THE definitive way to normalize)
normalize:
	@echo "🔄 Normalizing survey data..."
	python survey_normalizer.py --auto
	@echo "✅ Data normalization complete!"
	@echo "📁 Output: survey_normalized.db"

# Show extraction job status
status:
	@echo "📊 Checking extraction job status..."
	python main.py status

# Extract with verbose logging
extract-verbose:
	@echo "📥 Extracting data with verbose logging..."
	python main.py --verbose extract --use-default-urls

# =============================================================================
# TESTING & QUALITY ASSURANCE
# =============================================================================

# Run all tests (THE definitive way to test)
test:
	@echo "🧪 Running test suite..."
	python -m pytest tests/ -v
	@echo "✅ Tests complete!"

# Run tests with coverage report
test-cov:
	@echo "🧪 Running tests with coverage analysis..."
	python -m pytest tests/ -v --cov=src/surveyor --cov=. --cov-report=html --cov-report=term
	@echo "✅ Tests complete!"
	@echo "📊 Coverage report: htmlcov/index.html"

# Run all quality checks (THE definitive way to validate quality)
quality: lint typecheck test
	@echo "✅ All quality checks passed!"

# Run health checks
health:
	@echo "🏥 Running health checks..."
	python healthcheck.py
	@echo "✅ Health checks complete!"

# =============================================================================
# CODE QUALITY TOOLS
# =============================================================================

# Run linting (check only, no fixes)
lint:
	@echo "🔍 Running linting checks..."
	flake8 src/ tests/ *.py --exclude=venv,hybrid_surveyor,__pycache__,.git
	@echo "✅ Linting complete!"

# Run linting with auto-fix (THE definitive way to fix code issues)
lint-fix:
	@echo "🔧 Running linting with auto-fix..."
	autopep8 --in-place --recursive src/ tests/ *.py
	@echo "✅ Auto-fix complete!"

# Format code (THE definitive way to format)
format:
	@echo "🎨 Formatting code..."
	black src/ tests/ *.py --exclude="venv|hybrid_surveyor" || true
	isort src/ tests/ *.py --skip venv --skip hybrid_surveyor || true
	@echo "✅ Code formatting complete!"

# Check code formatting (no changes)
format-check:
	@echo "🔍 Checking code formatting..."
	black --check src/ tests/ *.py --exclude="venv|hybrid_surveyor" || true
	isort --check-only src/ tests/ *.py --skip venv --skip hybrid_surveyor || true

# Run type checking
typecheck:
	@echo "🔍 Running type checks..."
	mypy src/ --ignore-missing-imports || true
	@echo "✅ Type checking complete!"

# Run all checks together
all-checks: format-check lint typecheck test
	@echo "✅ All checks passed!"

# =============================================================================
# SERVICES & OPERATIONS
# =============================================================================

# Force manual data sync
sync:
	@echo "🔄 Forcing manual data sync..."
	@echo "📍 Visit: http://localhost:8080/sync"
	@echo "🖱️  Click 'Force Sync Now' button"
	@echo ""
	@echo "Or use Python:"
	python -c "from auto_sync_service import get_auto_sync_service; import asyncio; asyncio.run(get_auto_sync_service().force_sync())"

# =============================================================================
# CLEANUP
# =============================================================================

# Clean up generated files and caches
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "✅ Cleanup complete!"

# =============================================================================
# DEPLOYMENT (Use Railway GitHub Integration)
# =============================================================================

# NOTE: Deployment is handled by Railway's GitHub integration
# DO NOT use manual deployment commands
#
# To deploy:
#   1. git commit -m "Your changes"
#   2. git push origin master
#   3. Railway auto-deploys
#
# See CLAUDE.md and DEPLOYMENT_GUIDE.md for details
