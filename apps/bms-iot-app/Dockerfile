# Multi-stage build for ARM-optimized BMS IoT App
FROM balenalib/raspberrypi3-python:3.11-build AS builder

# Install system dependencies for building native libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy packages directory for shared modules
COPY packages/ ./packages/

# Copy app directory to mirror monorepo structure
COPY apps/bms-iot-app/ ./apps/bms-iot-app/

# Set working directory to app location for dependency installation
WORKDIR /app/apps/bms-iot-app

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies with ARM optimization
RUN pip install --no-cache-dir -e .

# Production stage
FROM balenalib/raspberrypi3-python:3.11-run

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory to mirror monorepo structure
WORKDIR /app

# Copy packages directory for shared modules
COPY packages/ ./packages/

# Copy app directory to mirror monorepo structure
COPY apps/bms-iot-app/ ./apps/bms-iot-app/

# Set working directory to app location (same as local development)
WORKDIR /app/apps/bms-iot-app

# Create data directory for persistent storage
RUN mkdir -p /data && chmod 755 /data

# Copy entrypoint script (already copied with app directory)
RUN chmod +x ./docker-entrypoint.sh

# Set environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from src.config.paths import get_config_paths; print('OK')" || exit 1

# Expose any required ports (BACnet uses UDP 47808)
EXPOSE 47808/udp

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["run-main"]
