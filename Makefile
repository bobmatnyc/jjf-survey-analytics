.PHONY: help install test lint format clean run-tests setup init extract status

# Default target
help:
	@echo "Available commands:"
	@echo "  setup     - Set up the development environment"
	@echo "  install   - Install dependencies"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linting"
	@echo "  format    - Format code"
	@echo "  clean     - Clean up generated files"
	@echo "  init      - Initialize database"
	@echo "  extract   - Extract data from default URLs"
	@echo "  status    - Show extraction job status"

# Set up development environment
setup:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # On Linux/Mac"
	@echo "  venv\\Scripts\\activate     # On Windows"
	@echo "Then run: make install"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

# Run tests
test:
	python -m pytest tests/ -v

# Run tests with coverage
test-cov:
	python -m pytest tests/ -v --cov=src/surveyor --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

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

# Initialize database
init:
	python main.py init-db

# Extract data from default URLs
extract:
	python main.py extract --use-default-urls

# Show status
status:
	python main.py status

# Run with verbose logging
extract-verbose:
	python main.py --verbose extract --use-default-urls
