FROM python:3.9-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install PostgreSQL client
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Create necessary directories
RUN mkdir -p static/uploads templates

COPY . .

# Ensure uploads directory exists and has proper permissions
RUN chmod 777 static/uploads

EXPOSE 5000

CMD ["uv", "run", "python", "app.py"]
