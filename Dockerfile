FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY stock_check.py .
COPY load_stores.py .
COPY templates/ templates/
COPY config/ config/

# Create directories for data persistence
RUN mkdir -p /app/data

# Expose port for Flask web application
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create volume mount points
VOLUME ["/app/config", "/app/data"]

# Add curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Run the Flask web application with Gunicorn for production
CMD ["python3", "run.py"]
