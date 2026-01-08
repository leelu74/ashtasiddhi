FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data

# Default command (can be overridden)
CMD ["python", "Anima.py", "--api"]