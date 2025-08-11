FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Remove unnecessary files but keep essentials
RUN rm -rf .git .gitignore __pycache__ debug_*.html stock_history*.json webhook_logs.json || true

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create directories for data persistence
RUN mkdir -p /app/data /app/config

# Expose port for Flask web application
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create volume mount points
VOLUME ["/app/config", "/app/data"]

# Add curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Use entrypoint script for robust startup
CMD ["./entrypoint.sh"]
