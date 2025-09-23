.PHONY: help install test lint format clean run-tests setup init extract status health

# Default target
help:
	@echo "🔍 Hybrid Surveyor - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Set up development environment"
	@echo "  install        - Install dependencies"
	@echo "  install-dev    - Install with development dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  type-check     - Run type checking"
	@echo "  clean          - Clean up generated files"
	@echo ""
	@echo "Application Commands:"
	@echo "  init           - Initialize database"
	@echo "  extract        - Extract data from default URLs"
	@echo "  status         - Show extraction job status"
	@echo "  health         - Check system health"
	@echo "  config         - Show configuration"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run in Docker container"

# Set up development environment
setup:
	python -m venv venv
	@echo "✅ Virtual environment created"
	@echo "Activate with:"
	@echo "  source venv/bin/activate  # On Linux/Mac"
	@echo "  venv\\Scripts\\activate     # On Windows"
	@echo "Then run: make install-dev"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

# Install with development dependencies
install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev,docs]"
	pre-commit install

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src/hybrid_surveyor --cov-report=html --cov-report=term --cov-report=xml

# Run unit tests only
test-unit:
	pytest tests/unit/ -v -m unit

# Run integration tests only
test-integration:
	pytest tests/integration/ -v -m integration

# Run fast tests (exclude slow ones)
test-fast:
	pytest tests/ -v -m "not slow"

# Run linting
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Type checking
type-check:
	mypy src/hybrid_surveyor

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .tox/

# Initialize database
init:
	hybrid-surveyor init-db

# Extract data from default URLs
extract:
	hybrid-surveyor extract --use-default-urls

# Extract with verbose logging
extract-verbose:
	hybrid-surveyor --verbose extract --use-default-urls

# Show status
status:
	hybrid-surveyor status

# Check health
health:
	hybrid-surveyor health

# Show configuration
config:
	hybrid-surveyor config

# Process unprocessed data
process:
	hybrid-surveyor process

# Build documentation
docs:
	mkdocs build

# Serve documentation locally
docs-serve:
	mkdocs serve

# Docker commands
docker-build:
	docker build -t hybrid-surveyor:latest .

docker-run:
	docker run --rm -it \
		-v $(PWD)/credentials.json:/app/credentials.json \
		-e GOOGLE_CREDENTIALS_FILE=/app/credentials.json \
		hybrid-surveyor:latest

# Development workflow
dev-setup: setup install-dev
	@echo "✅ Development environment ready!"
	@echo "Run 'source venv/bin/activate' to activate the environment"

# CI workflow
ci: lint type-check test-cov
	@echo "✅ CI checks passed!"

# Release workflow
release: clean ci
	python -m build
	@echo "✅ Release build ready in dist/"

# Quick development test
dev-test: format lint test-fast
	@echo "✅ Quick development checks passed!"
