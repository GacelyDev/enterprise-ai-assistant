# Dockerfile
#FROM python:3.10
FROM mcr.microsoft.com/playwright/python:v1.62.0-jammy

WORKDIR /app

# Install system dependencies required to build some libraries
#RUN apt-get update && apt-get install -y \
#    build-essential \
#    ca-certificates \
#    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY ./docker/scraper/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /app/src/

ENV PYTHONPATH=/app