FROM mcr.microsoft.com/playwright/python:v1.25.1-focal

WORKDIR /app

# Install additional system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libpq-dev \
    wget \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libwayland-server0 \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip, setuptools, and wheel before installing dependencies
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
