# Use Python 3.12 Slim
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Create data directory (even though we use MongoDB, some scripts might expect it)
RUN mkdir -p data

# Expose the default Hugging Face port
EXPOSE 7860

# Start the application
CMD ["python", "main.py"]
