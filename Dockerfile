# Python 3.10 का इस्तेमाल करें (Debian 12 Bookworm पर based)
FROM python:3.10-slim

# Working Directory
WORKDIR /app

# System Dependencies Install करें (Debian 12 के लिए)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Requirements Copy करें
COPY requirements.txt .

# Python Packages Install करें
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# पूरा Code Copy करें
COPY . .

# Port Expose करें (अगर Web Server है तो)
EXPOSE 8000

# Bot Run करें
CMD ["python3", "run.py"]
