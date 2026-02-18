.PHONY: help install install-dev install-ai uninstall clean validate generate generate-package test test-coverage lint format

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)Resume CLI Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Installation:$(NC)"
	@echo "  make install          Install resume-cli from source"
	@echo "  make install-ai       Install with AI support (Claude/OpenAI)"
	@echo "  make install-dev      Install with development tools (testing, linting)"
	@echo "  make uninstall        Uninstall resume-cli"
	@echo ""
	@echo "$(GREEN)Common Operations:$(NC)"
	@echo "  make validate         Validate resume.yaml schema"
	@echo "  make generate         Generate resume (template-based)"
	@echo "  make generate-package Generate application package (resume + cover letter)"
	@echo "  make ats-check        Check ATS compatibility score"
	@echo "  make variants         List all available resume variants"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make test             Run all tests"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make lint             Lint Python code (flake8)"
	@echo "  make format           Format code (black)"
	@echo "  make build            Build distribution package"
	@echo "  make clean            Remove build artifacts and cache"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make check-deps       Check installed dependencies"
	@echo "  make check-config     Validate configuration files"
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make install && make validate"
	@echo "  make install-ai && make generate-package"
	@echo "  make test && make lint"
	@echo ""

# Installation targets
install:
	@echo "$(BLUE)Installing resume-cli from source...$(NC)"
	pip install -e .
	@echo "$(GREEN)✓ Installation complete$(NC)"
	@echo "  Verify: resume-cli --help"

install-ai:
	@echo "$(BLUE)Installing resume-cli with AI support...$(NC)"
	pip install -e ".[ai]"
	@echo "$(GREEN)✓ AI support installed$(NC)"
	@echo "  Set API keys in .env file:"
	@echo "    ANTHROPIC_API_KEY=sk-..."
	@echo "    OPENAI_API_KEY=sk-..."
	@echo "    GEMINI_API_KEY=..."

install-dev: install
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development tools installed$(NC)"

uninstall:
	@echo "$(BLUE)Uninstalling resume-cli...$(NC)"
	pip uninstall -y resume-cli resumeai 2>/dev/null || true
	@echo "$(GREEN)✓ Uninstalled$(NC)"

# Resume operations
validate:
	@echo "$(BLUE)Validating resume.yaml...$(NC)"
	resume-cli validate
	@echo "$(GREEN)✓ Resume is valid$(NC)"

variants:
	@echo "$(BLUE)Available resume variants:$(NC)"
	resume-cli variants

generate:
	@echo "$(BLUE)Generating resume...$(NC)"
	@echo "$(YELLOW)Usage: resume-cli generate [OPTIONS]$(NC)"
	@echo "  -v, --variant TEXT    Resume variant (default: v1.0.0-base)"
	@echo "  -f, --format CHOICE   Output format: md, tex, pdf (default: md)"
	@echo ""
	@echo "Example:"
	@echo "  resume-cli generate -v v1.1.0-backend -f pdf"
	@echo ""
	@echo "$(YELLOW)Quick start:$(NC)"
	resume-cli generate -v v1.0.0-base -f md --no-save | head -50

generate-package:
	@echo "$(BLUE)Generate application package (resume + cover letter)$(NC)"
	@echo "$(YELLOW)Usage: resume-cli generate-package [OPTIONS]$(NC)"
	@echo "  --job-desc PATH       Path to job description file (required)"
	@echo "  -v, --variant TEXT    Resume variant (default: v1.0.0-base)"
	@echo "  --company TEXT        Company name (optional)"
	@echo "  --non-interactive     Skip interactive questions"
	@echo ""
	@echo "Example:"
	@echo "  resume-cli generate-package --job-desc job-posting.txt --variant v1.1.0-backend"
	@echo ""
	@echo "$(YELLOW)Note: AI customization is automatic when --job-desc is provided$(NC)"

ats-check:
	@echo "$(BLUE)ATS Compatibility Check$(NC)"
	@echo "$(YELLOW)Usage: resume-cli ats-check [OPTIONS]$(NC)"
	@echo "  --job-desc PATH       Path to job description file (required)"
	@echo "  -v, --variant TEXT    Resume variant (default: v1.0.0-base)"
	@echo "  --output PATH         Save report as JSON"
	@echo ""
	@echo "Example:"
	@echo "  resume-cli ats-check --job-desc job.txt -v v1.1.0-backend"

# Testing
test:
	@echo "$(BLUE)Running tests...$(NC)"
	pytest -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=cli --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

# Code quality
lint:
	@echo "$(BLUE)Linting code...$(NC)"
	flake8 cli/ tests/ setup.py --max-line-length=100 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ No linting issues$(NC)"

format:
	@echo "$(BLUE)Formatting code with Black...$(NC)"
	black cli/ tests/ setup.py
	@echo "$(GREEN)✓ Code formatted$(NC)"

# Build
build:
	@echo "$(BLUE)Building distribution package...$(NC)"
	python setup.py sdist bdist_wheel
	@echo "$(GREEN)✓ Build complete - check dist/$(NC)"

# Cleanup
clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info resume_cli.egg-info/
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

# Utilities
check-deps:
	@echo "$(BLUE)Checking installed dependencies...$(NC)"
	pip list | grep -E "(anthropic|openai|google-generativeai|pytest|black|flake8)" || echo "Some packages not installed"
	@echo ""
	@echo "$(YELLOW)Install missing packages:$(NC)"
	@echo "  make install-ai       # For AI support"
	@echo "  make install-dev      # For development"

check-config:
	@echo "$(BLUE)Checking configuration files...$(NC)"
	@echo ""
	@echo "$(YELLOW)resume.yaml:$(NC)"
	@if [ -f resume.yaml ]; then \
		echo "  $(GREEN)✓ Found$(NC)"; \
	else \
		echo "  $(RED)✗ Not found - run: cp resume.example.yaml resume.yaml$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW).env file:$(NC)"
	@if [ -f .env ]; then \
		echo "  $(GREEN)✓ Found$(NC)"; \
	else \
		echo "  $(YELLOW)⚠ Not found - create from .env.template for AI API keys$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)config/default.yaml:$(NC)"
	@if [ -f config/default.yaml ]; then \
		echo "  $(GREEN)✓ Found$(NC)"; \
	else \
		echo "  $(RED)✗ Not found$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)templates/ directory:$(NC)"
	@if [ -d templates ]; then \
		echo "  $(GREEN)✓ Found $(shell ls templates/*.j2 2>/dev/null | wc -l) templates$(NC)"; \
	else \
		echo "  $(RED)✗ Not found$(NC)"; \
	fi

# Quick start
setup: install validate
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Copy example: cp resume.example.yaml resume.yaml"
	@echo "  2. Edit resume.yaml with your information"
	@echo "  3. Generate: resume-cli generate -v v1.0.0-base -f md"
	@echo "  4. For AI: make install-ai && set API keys in .env"
	@echo ""
	@echo "$(YELLOW)More information: resume-cli --help$(NC)"
