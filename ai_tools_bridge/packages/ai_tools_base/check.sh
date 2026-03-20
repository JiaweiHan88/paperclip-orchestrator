#!/bin/bash
set -e

echo "Running checks..."

# Run formatting
echo "Running ruff format..."
uv run ruff format src tests --exit-non-zero-on-fix

# Run linting
echo "Running ruff check..."
uv run ruff check src --fix --exit-non-zero-on-fix

# Run tests
echo "Running tests..."
uv run pytest tests

# Run pyright
echo "Running pyright..."
uv run pyright

echo "All checks passed!"
