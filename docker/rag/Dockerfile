FROM python:3.10-slim

# Working directory inside the container
WORKDIR /app

# Install minimal system dependencies needed for package builds if applicable
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the RAG requirements file
COPY ./docker/rag/requirements.txt .

# Upgrade pip and install dependencies (without Playwright)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /app/src/

ENV PYTHONPATH=/app