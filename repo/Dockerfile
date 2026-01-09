FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with more robust options
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Try to download spaCy model (optional)
RUN python -c "import spacy; spacy.cli.download('en_core_web_sm')" || echo "spaCy model download failed, will use basic NLP"

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data

# Default command (can be overridden)
CMD ["python", "Anima.py", "--api"]