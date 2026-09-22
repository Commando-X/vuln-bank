EXPOSED_ENV_FILES = {
    '.env': '''APP_ENV=production
FLASK_DEBUG=true
SECRET_KEY=8f6d3e9027474fd8b516ac09e319e2ef
JWT_SECRET=00af85a8f47d41f7bfb9ce45ad1130aa
DB_HOST=vulnbank-db.internal
DB_PORT=5432
DB_NAME=vulnerable_bank
DB_USER=vulnbank_prod
DB_PASSWORD=VbProd_2026_DbAccess!
DATABASE_URL=postgresql://vulnbank_prod:VbProd_2026_DbAccess!@vulnbank-db.internal:5432/vulnerable_bank
REDIS_URL=redis://:VbRedis_2026!@vulnbank-cache.internal:6379/0
DEEPSEEK_API_KEY=ds_live_7f3b9d82c1264ea0a8c77f90
SMTP_HOST=mail.vulnbank.internal
SMTP_PORT=587
SMTP_USER=alerts@vulnbank.org
SMTP_PASSWORD=MailRelay_2026!
''',
    '.env.bak': '''APP_ENV=production
FLASK_DEBUG=true
SECRET_KEY=5c78f362be4b4ad8bc395325aa46fe71
JWT_SECRET=9b66150da3e54310923fde26a558ec87
DB_HOST=10.20.30.40
DB_PORT=5432
DB_NAME=vulnerable_bank
DB_USER=vulnbank_admin
DB_PASSWORD=VulnBankAdmin_2025!
DATABASE_URL=postgresql://vulnbank_admin:VulnBankAdmin_2025!@10.20.30.40:5432/vulnerable_bank
ADMIN_USERNAME=ops_admin
ADMIN_PASSWORD=VbOperations_2025!
SMTP_HOST=10.20.30.25
SMTP_PORT=587
SMTP_USER=banking-alerts@vulnbank.org
SMTP_PASSWORD=LegacyMail_2025!
''',
}
