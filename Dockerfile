# Python 3.9 reached end of life and no longer receives security fixes.
# 3.12 is the current stable release and is what the dependency set below
# is pinned against.
#
# The base image is pinned by digest as well as by tag. A floating tag can
# be repointed upstream at any time, which would change what the build
# actually contains (CWE-494).
FROM python:3.12-slim@sha256:4a68d3169325c47e1bafbb86425220f03fbdff6f079a419e8d39407183288217

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# The version comes from requirements.txt only. Pinning gunicorn here as well
# allowed the two to drift apart, which would silently ship the vulnerable
# release while the audit reported the fixed one.
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p static/uploads templates

# Copy the application. A .dockerignore keeps .env, .git and local
# artifacts out of the image (CWE-538).
COPY . .

# Run as a non-root user (CWE-250).
RUN useradd --create-home --shell /usr/sbin/nologin --uid 10001 appuser \
    && chown -R appuser:appuser /app \
    && chmod 755 /app/static/uploads \
    && chmod +x /app/start.sh

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=5).getcode() == 200 else sys.exit(1)"

CMD ["./start.sh"]
