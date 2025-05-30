#!/bin/bash

# Install test dependencies if needed
echo "Checking/installing test dependencies..."
uv pip install -e .[dev]

# Run tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ -v --cov=src/coveo_mcp_server --cov-report=term --cov-report=html:coverage_report

# Show coverage report path
echo "Coverage report generated in: $(pwd)/coverage_report"

# Return to the tests directory
cd tests/ 