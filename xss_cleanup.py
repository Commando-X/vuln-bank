import os
import time

import psycopg2

from database import DB_CONFIG


DEFAULT_TTL_MINUTES = 15
DEFAULT_SWEEP_SECONDS = 60


def positive_int_from_env(name, default, minimum=1):
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        print(f"Invalid {name}={raw_value!r}; using {default}")
        return default
    return max(value, minimum)


def cleanup_expired_xss_payloads(connection, ttl_minutes):
    """Neutralize expired stored-XSS values without changing their sinks."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE users
            SET username = CONCAT(
                    'expired-xss-',
                    id,
                    '-',
                    SUBSTRING(MD5(username || account_number || clock_timestamp()::text) FROM 1 FOR 12)
                )
            WHERE username_xss_detected_at <= CURRENT_TIMESTAMP - make_interval(mins => %s)
            """,
            (ttl_minutes,),
        )
        renamed_usernames = cursor.rowcount

        cursor.execute(
            """
            UPDATE users
            SET bio = NULL
            WHERE bio_xss_detected_at <= CURRENT_TIMESTAMP - make_interval(mins => %s)
            """,
            (ttl_minutes,),
        )
        cleared_bios = cursor.rowcount

        cursor.execute(
            """
            UPDATE transactions
            SET description = NULL
            WHERE description_xss_detected_at <= CURRENT_TIMESTAMP - make_interval(mins => %s)
            """,
            (ttl_minutes,),
        )
        cleared_descriptions = cursor.rowcount

    connection.commit()
    return renamed_usernames, cleared_bios, cleared_descriptions


def run_cleanup(ttl_minutes):
    connection = psycopg2.connect(**DB_CONFIG)
    try:
        return cleanup_expired_xss_payloads(connection, ttl_minutes)
    finally:
        connection.close()


def main():
    ttl_minutes = positive_int_from_env(
        'XSS_PAYLOAD_TTL_MINUTES',
        DEFAULT_TTL_MINUTES,
    )
    sweep_seconds = positive_int_from_env(
        'XSS_CLEANUP_INTERVAL_SECONDS',
        DEFAULT_SWEEP_SECONDS,
        minimum=5,
    )

    print(
        f"Stored-XSS cleanup worker started: ttl={ttl_minutes}m, "
        f"interval={sweep_seconds}s"
    )

    while True:
        try:
            renamed, bios, descriptions = run_cleanup(ttl_minutes)
            if renamed or bios or descriptions:
                print(
                    "Expired stored-XSS values neutralized: "
                    f"usernames={renamed}, bios={bios}, "
                    f"transaction_descriptions={descriptions}"
                )
        except Exception as error:
            # Keep retrying if the database or schema is briefly unavailable.
            print(f"Stored-XSS cleanup failed; retrying: {error}")

        time.sleep(sweep_seconds)


if __name__ == '__main__':
    main()
