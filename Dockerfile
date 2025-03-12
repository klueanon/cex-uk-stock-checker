FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY stock_check.py .
COPY config/checker.template.yaml config/checker.template.yaml

# Create volume mount point for config
VOLUME ["/app/config"]

CMD ["python3", "stock_check.py"]
