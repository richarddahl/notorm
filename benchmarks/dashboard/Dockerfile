FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the dashboard code
COPY . .

# Make sure data directories exist
RUN mkdir -p data/summaries

# Set the default command
CMD ["python", "app.py"]

# Expose the port
EXPOSE 8050

# Environment variables
ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8050
ENV DASHBOARD_DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${DASHBOARD_PORT}/ || exit 1