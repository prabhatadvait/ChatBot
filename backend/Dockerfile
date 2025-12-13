FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ffmpeg \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download Vosk Model (Small, English)
RUN wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip \
    && unzip vosk-model-small-en-us-0.15.zip \
    && mv vosk-model-small-en-us-0.15 model \
    && rm vosk-model-small-en-us-0.15.zip

# Copy requirements
COPY backend/requirements.txt /app/requirements.txt
COPY requirements.txt /requirements.txt

# Install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source code
COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]