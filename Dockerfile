# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY setup.py setup.py* ./
COPY README.md ./
COPY src/ ./src/
COPY collect_data.py ./
COPY main.py ./
COPY update_risk_scores.py ./
COPY graph_investigation.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p data/raw data/interim data/external \
    models \
    reports/risk_scoring/figures \
    reports/graph_investigation

# Copy automation script
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY run-pipeline.sh /run-pipeline.sh
RUN chmod +x /docker-entrypoint.sh /run-pipeline.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Jakarta

# Expose port (if needed for future API)
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["cron"]
