# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Install system dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    lsb-release \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | tee /etc/apt/trusted.gpg.d/google.asc \
    && echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/google.asc] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and cohorts
RUN mkdir -p uploads cohorts

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
