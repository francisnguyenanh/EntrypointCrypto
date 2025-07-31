# Use official Python 3.9 Linux image (same as Lambda runtime)
FROM python:3.9-slim-bullseye

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python packages to target directory
RUN mkdir -p /opt/python/lib/python3.9/site-packages

# Install CCXT and dependencies for Lambda layer
RUN pip install --no-cache-dir -r requirements.txt -t /opt/python/lib/python3.9/site-packages/

# Create the layer zip file
RUN cd /opt && zip -r /build/ccxt-layer.zip python/

# Set entrypoint to copy the layer to host
CMD ["cp", "/build/ccxt-layer.zip", "/output/"]
