#!/bin/bash

# CEX Stock Checker Docker Entrypoint

echo "Starting CEX Stock Checker..."
echo "Working directory: $(pwd)"
echo "Available files: $(ls -la)"

# Ensure config directory exists
mkdir -p /app/config /app/data

# Copy example config if no config exists
if [ ! -f /app/config/checker.yaml ]; then
    echo "Creating default configuration..."
    if [ -f /app/config/checker.yaml.example ]; then
        cp /app/config/checker.yaml.example /app/config/checker.yaml
        echo "Configuration created from example"
    else
        echo "No example config found, will create minimal config via web UI"
    fi
fi

# Check which Python files are available and run the appropriate one
if [ -f run.py ]; then
    echo "Starting with Gunicorn via run.py..."
    exec python3 run.py
elif [ -f app.py ]; then
    echo "Starting with Flask development server via app.py..."
    exec python3 app.py
else
    echo "ERROR: Neither run.py nor app.py found!"
    exit 1
fi