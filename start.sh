#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-vulnerable_bank}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  sleep 2
done

echo "Starting gunicorn (production WSGI server)..."
# The Flask development server with debug=True exposed the Werkzeug debugger
# on a public bind (CWE-489). gunicorn serves the app without a debugger.
#
# Bind to 0.0.0.0 INSIDE the container so the host-side publish can stay on
# 127.0.0.1 and the reverse proxy can reach it. The two layers bind
# differently and only the host side should be restricted.
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile - \
    "app:app"
