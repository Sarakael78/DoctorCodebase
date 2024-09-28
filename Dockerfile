# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Create a non-root user for security
RUN useradd -m appuser

# Set the working directory
WORKDIR /app

# Copy only requirements.txt first to leverage Docker layer caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the Gradio default port
EXPOSE 7860

# Set labels for metadata (optional but recommended)
LABEL Name="DoctorCodebase"
LABEL Description="A Python tool to document and analyze codebases using Gradio."
LABEL Maintainer="dsbworkaholic@gmail.com"
LABEL License="MIT"
LABEL Version="1.0"

# Define environment variables for Gradio (optional)
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Command to run the application
CMD ["python", "main.py"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1



