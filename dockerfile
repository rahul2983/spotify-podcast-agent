FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (faster, smaller)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files
COPY spotify_agent/ ./spotify_agent/
COPY main.py .
COPY setup.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Create cache directory
RUN mkdir -p /home/app/.spotify_podcast_agent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command
CMD ["python", "main.py", "--mode", "api"]