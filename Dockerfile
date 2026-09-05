# Use official Python 3.10.11 image
FROM python:3.10.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY . .

# Expose port (if using web server)
EXPOSE 8000

# Run the application
CMD ["python3", "-m", "Extractor"]
