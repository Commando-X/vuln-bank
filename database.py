import os
import sqlite3
import time

# Vulnerable database configuration
# CWE-259: Use of Hard-coded Password
# CWE-798: Use of Hard-coded Credentials
DB_PATH = os.getenv('DB_PATH', '/app/data/vulnbank.db')

_connection = None

def init_connection_pool(min_connections=1, max_connections=10, max_retries=5, retry_delay=2):
    """
    Initialize the database connection (SQLite)
    Vulnerability: No connection encryption enforced
    """
    global _connection
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    _connection.row_factory = sqlite3.Row  # so fetchall returns dict-like rows
    _connection.execute("PRAGMA journal_mode=WAL")
    _connection.execute("PRAGMA foreign_keys=ON")
    print("Database connection pool created successfully")

def get_connection():
    if _connection:
        return _connection
    raise Exception("Connection pool not initialized")

def return_connection(connection):
    pass  # SQLite uses single connection, no pool

def init_db():
    """
    Initialize database tables
    Multiple vulnerabilities present for learning purposes
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,  -- Vulnerability: Passwords stored in plaintext
                account_number TEXT NOT NULL UNIQUE,
                balance REAL DEFAULT 1000.0,
                is_admin INTEGER DEFAULT 0,
                profile_picture TEXT,
                reset_pin TEXT,  -- Vulnerability: Reset PINs stored in plaintext
                bio TEXT,  -- Vulnerability: Stored XSS - User bio without sanitization
                is_suspended INTEGER DEFAULT 0
            )
        ''')

        # Migration: Add bio column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
        except Exception:
            pass  # Column already exists or error adding it

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_suspended INTEGER DEFAULT 0")
        except Exception:
            pass  # Column already exists or error adding it

        # Create loans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                amount REAL,
                status TEXT DEFAULT 'pending'
            )
        ''')

        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_account TEXT NOT NULL,
                to_account TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_type TEXT NOT NULL,
                description TEXT
            )
        ''')

        # Create virtual cards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS virtual_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                card_number TEXT NOT NULL UNIQUE,  -- Vulnerability: Card numbers stored in plaintext
                cvv TEXT NOT NULL,  -- Vulnerability: CVV stored in plaintext
                expiry_date TEXT NOT NULL,
                card_limit REAL DEFAULT 1000.0,
                current_balance REAL DEFAULT 0.0,
                is_frozen INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                card_type TEXT DEFAULT 'standard',  -- Vulnerability: No validation on card type
                currency TEXT DEFAULT 'USD'
            )
        ''')

        # Create virtual card transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER REFERENCES virtual_cards(id) ON DELETE CASCADE,
                amount REAL NOT NULL,
                merchant_name TEXT,  -- Vulnerability: No input validation
                transaction_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')

        try:
            cursor.execute("ALTER TABLE virtual_cards ADD COLUMN currency TEXT DEFAULT 'USD'")
        except Exception:
            pass

        # Create default admin account if it doesn't exist
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not cursor.fetchone():
            cursor.execute(
                """
                INSERT INTO users (username, password, account_number, balance, is_admin)
                VALUES (?, ?, ?, ?, ?)
                """,
                ('admin', 'admin123', 'ADMIN001', 1000000.0, 1)
            )

        # Create bill categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bill_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Create billers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS billers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER REFERENCES bill_categories(id),
                name TEXT NOT NULL,
                account_number TEXT NOT NULL,  -- Vulnerability: No encryption
                description TEXT,
                minimum_amount REAL DEFAULT 0,
                maximum_amount REAL,  -- Vulnerability: No validation
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Create bill payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bill_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                biller_id INTEGER REFERENCES billers(id),
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,  -- 'balance' or 'virtual_card'
                card_id INTEGER REFERENCES virtual_cards(id),  -- NULL if paid with balance
                reference_number TEXT,  -- Vulnerability: No unique constraint
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                description TEXT
            )
        ''')

        # Insert default bill categories
        cursor.execute("""
            INSERT OR IGNORE INTO bill_categories (name, description)
            VALUES
            ('Utilities', 'Water, Electricity, Gas bills'),
            ('Telecommunications', 'Phone, Internet, Cable TV'),
            ('Insurance', 'Life, Health, Auto insurance'),
            ('Credit Cards', 'Credit card bill payments')
        """)

        # Insert sample billers (use INSERT OR IGNORE with a unique constraint workaround)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 1, 'City Water', 'WATER001', 'City Water Utility', 10
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'WATER001')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 1, 'PowerGen Electric', 'POWER001', 'Electricity Provider', 20
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'POWER001')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 2, 'TeleCom Services', 'TEL001', 'Phone and Internet', 25
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'TEL001')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 2, 'CableTV Plus', 'CABLE001', 'Cable TV Services', 30
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'CABLE001')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 3, 'HealthFirst Insurance', 'INS001', 'Health Insurance', 100
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'INS001')
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO billers (category_id, name, account_number, description, minimum_amount)
            SELECT 4, 'Universal Bank Card', 'CC001', 'Credit Card Payments', 50
            WHERE NOT EXISTS (SELECT 1 FROM billers WHERE account_number = 'CC001')
        """)

        conn.commit()
        print("Database initialized successfully")

    except Exception as e:
        # Vulnerability: Detailed error information exposed
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise e

def execute_query(query, params=None, fetch=True):
    """
    Execute a database query
    Vulnerability: This function still allows for SQL injection if called with string formatting
    """
    conn = get_connection()
    # Convert psycopg2 %s params to SQLite ? params
    query = query.replace('%s', '?')
    try:
        cursor = conn.execute(query, params or ())
        result = None
        if fetch:
            result = cursor.fetchall()
            # Convert Row objects to tuples for compatibility
            result = [tuple(row) for row in result]
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
        return result
    except Exception as e:
        # Vulnerability: Error details might be exposed to users
        conn.rollback()
        raise e

def execute_transaction(queries_and_params):
    """
    Execute multiple queries in a transaction
    Vulnerability: No input validation on queries
    queries_and_params: list of tuples (query, params)
    """
    conn = get_connection()
    try:
        for query, params in queries_and_params:
            query = query.replace('%s', '?')
            conn.execute(query, params or ())
        conn.commit()
    except Exception as e:
        # Vulnerability: Transaction rollback exposed
        conn.rollback()
        raise e
