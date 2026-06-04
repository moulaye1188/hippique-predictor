FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"

# Copy application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Ensure data and models directories exist
RUN mkdir -p /app/data /app/models

# Set Python path
ENV PYTHONPATH=/app:${PYTHONPATH}

# Expose port
EXPOSE 5000

# Set working directory to backend
WORKDIR /app/backend

# Run the Flask app via WSGI (with dependency check)
CMD ["python", "wsgi_with_deps.py"]
