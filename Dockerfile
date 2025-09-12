FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create uploads and data directories
RUN mkdir -p uploads data

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables
ENV FLASK_APP=app.src:app
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Don't switch to appuser here - entrypoint will handle it
# USER appuser

# Command to run the application
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app.src:app"]