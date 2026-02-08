FROM python:3.11-slim

WORKDIR /app

# Install Docker CLI so the monitor can restart the peer container
RUN apt-get update && \
    apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db_monitor.py .
RUN chmod +x db_monitor.py

CMD ["python", "db_monitor.py"]
