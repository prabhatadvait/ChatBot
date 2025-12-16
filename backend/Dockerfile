# Stage 1: Builder
FROM python:3.10-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements in a structure that satisfies relative imports (-r ../requirements.txt)
COPY requirements.txt /requirements.txt
COPY backend/requirements.txt /build/requirements.txt

# Install dependencies to a specific prefix
RUN pip install --prefix=/install --no-cache-dir -r /build/requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# Install ONLY runtime dependencies
# ffmpeg is required for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Copy backend source code
COPY backend /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]