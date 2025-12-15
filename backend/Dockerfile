FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*



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




# # ---------- builder ----------
# FROM python:3.10-slim AS builder

# ENV DEBIAN_FRONTEND=noninteractive
# WORKDIR /build

# # system deps (build time only)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# # copy BOTH requirements files (this is the key)
# COPY requirements.txt /requirements.txt
# COPY backend/requirements.txt /build/requirements.txt

# # build wheels
# RUN pip install --upgrade pip setuptools wheel \
#     && pip wheel --no-cache-dir -r /build/requirements.txt


# # ---------- runtime ----------
# FROM python:3.10-slim

# ENV DEBIAN_FRONTEND=noninteractive
# WORKDIR /app

# # runtime deps only
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# # install python deps
# COPY --from=builder /build /wheels
# RUN pip install --no-cache-dir /wheels/*.whl

# # copy backend code
# COPY backend /app

# EXPOSE 8000
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
