# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
# build-essential: needed for compiling some Python packages (like xgboost)
# git: needed for DVC to work with git-based remotes
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and setup.py first for better Docker layer caching
# setup.py is needed because requirements.txt includes "-e ." (editable install)
# This way, if only code changes, we don't reinstall dependencies
COPY requirements.txt setup.py ./

# Install Python dependencies
# --no-cache-dir: reduces image size by not storing pip cache
# --upgrade pip: ensures we have the latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project code
# This includes src/ and other necessary files
COPY . .

# Create artifacts directory where models and processed data will be stored
RUN mkdir -p artifacts mlruns

# Set Python path so modules can be imported
# This allows: from src.data import make_dataset
ENV PYTHONPATH=/app

# Default command (can be overridden when running the container)
CMD ["python", "--version"]

