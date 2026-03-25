# Stage 1: Build wrapper SDK wheel
FROM python:3.9-slim AS wrapper-deps
RUN pip wheel --no-cache-dir --wheel-dir /wheels swigdojo-target

# Stage 2: Existing vuln-bank build + wrapper
FROM python:3.9-slim

# Install PostgreSQL client (needed for app + BOLA verifier scoring)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install wrapper SDK
COPY --from=wrapper-deps /wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

# Create necessary directories
RUN mkdir -p static/uploads templates

COPY . .

# Ensure uploads directory exists and has proper permissions
RUN chmod 777 static/uploads

# Copy wrapper to /swigdojo/ (runs from there, chdirs to /app)
COPY wrapper.py /swigdojo/wrapper.py

EXPOSE 5000

CMD ["python", "/swigdojo/wrapper.py"]
