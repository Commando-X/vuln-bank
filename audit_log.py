"""
Logs / Auditoria module for VulnBank (intentionally vulnerable).

This module owns the security event trail for the application: it records what
happened, who did it, from where, and exposes a console so administrators can read
it back, verify its integrity, export it and purge it.

Every weakness below is deliberate and exists for the Logs/Auditoria module of the
security project:

    AV-01  SQL injection in the console filters (CWE-89)
    AV-02  IDOR: any authenticated user reads any other actor's trail (CWE-639)
    AV-03  Broken function level authorization on edit/delete/purge (CWE-862)
    AV-04  Path traversal / arbitrary local file read in the export (CWE-22)
    AV-05  Stored XSS through audit notes rendered with innerHTML (CWE-79)
    AV-06  Reflected XSS through the console search box (CWE-79)
    AV-07  No Content-Security-Policy anywhere in the app (CWE-693)
    AV-08  Log injection / log forging through unneutralized values (CWE-117)
    AV-09  Audit poisoning: the client authors the whole event (CWE-778)
    AV-10  Anti-forensics: unlogged, administrator-free purge (CWE-778)
    AV-11  Unverifiable integrity: signatures never computed (CWE-354)
    AV-12  CSRF on every mutating audit route (CWE-352)
    AV-13  HTTP parameter tampering, including actor identity override (CWE-807)

The integrity seams (_sanitize_for_log, compute_entry_signature) are present but
unwired so that Phase 3 remediation stays a small, reviewable diff.
"""

import hashlib
import hmac
import json
import os
import re
import sys
from datetime import datetime

from flask import Response, jsonify, render_template, request, send_file

from functools import wraps
from auth import token_required
from database import execute_query


def admin_required(f):
    """
    Fix (M4-R03/M4-R04): every audit route (read and write) requires an admin
    verified against the database on each request, not the token claim.
    """
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        rows = execute_query(
            "SELECT is_admin, is_suspended FROM users WHERE id = %s",
            (current_user.get('user_id'),),
        )
        if not rows or rows[0][1]:
            return jsonify({'error': 'Forbidden'}), 403
        if not rows[0][0]:
            return jsonify({'error': 'Admin privilege required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


AUDIT_SEVERITIES = ['INFO', 'NOTICE', 'WARNING', 'ERROR', 'CRITICAL']

AUDIT_EVENT_TYPES = [
    'ACCOUNT_CREATED',
    'LOGIN_SUCCESS',
    'LOGIN_FAILED',
    'LOGOUT',
    'PROFILE_UPDATED',
    'TRANSFER_INITIATED',
    'LOAN_REQUESTED',
    'LOAN_APPROVED',
    'ACCOUNT_SUSPENDED',
    'ACCOUNT_UNSUSPENDED',
    'ACCOUNT_DELETED',
    'ADMIN_ACCOUNT_CREATED',
    'AUDIT_NOTE_ADDED',
    'AUDIT_LOG_EDITED',
    'AUDIT_LOG_DELETED',
    'AUDIT_LOG_PURGED',
]

AUDIT_TABLE_COLUMNS = (
    'id, event_type, severity, actor_id, actor_username, action, target, '
    'details, ip_address, user_agent, referer, request_id, http_method, '
    'endpoint, result, signature, created_at'
)

AUDIT_COLUMN_KEYS = (
    'id', 'event_type', 'severity', 'actor_id', 'actor_username', 'action',
    'target', 'details', 'ip_address', 'user_agent', 'referer', 'request_id',
    'http_method', 'endpoint', 'result', 'signature', 'created_at',
)

# Fields covered by the entry signature once Phase 3 wires the signing seam.
AUDIT_SIGNATURE_FIELDS = (
    'id', 'event_type', 'severity', 'actor_id', 'actor_username', 'action',
    'target', 'details', 'ip_address', 'user_agent', 'result', 'created_at',
)

# Vulnerability: no key material is configured anywhere, so every signature
# recomputation comes back empty and every entry looks verified.
AUDIT_SIGNING_SECRET = os.getenv('AUDIT_SIGNING_SECRET', '')

# Base directory the export path is resolved against before it is read back.
AUDIT_EXPORT_DIRECTORY = os.path.join('static', 'audit')

# The export endpoint expects its working directory to exist. Without it every
# traversal payload silently misses, because path resolution fails on the first
# missing component instead of on the traversal itself.
try:
    os.makedirs(AUDIT_EXPORT_DIRECTORY, exist_ok=True)
except OSError:
    pass

MODULE_VULNERABILITIES = [
    {
        'id': 'AV-01',
        'title': 'SQL injection in console filters',
        'cwe': 'CWE-89',
        'owasp': 'A03:2021 - Injection',
        'nist': 'DE.CM-1 / ID.RA-1',
        'detail': 'search, event_type, severity, actor, user_id, from, to, limit, offset and order are interpolated into the SQL with f-strings.',
    },
    {
        'id': 'AV-02',
        'title': 'Broken object level authorization (IDOR)',
        'cwe': 'CWE-639',
        'owasp': 'A01:2021 - Broken Access Control',
        'nist': 'PR.AA-5',
        'detail': 'Any authenticated user reads any audit entry by id and any actor trail through ?user_id=.',
    },
    {
        'id': 'AV-03',
        'title': 'Missing function level authorization',
        'cwe': 'CWE-862',
        'owasp': 'A01:2021 - Broken Access Control',
        'nist': 'PR.AA-5 / PR.DS-6',
        'detail': 'Edit, delete and purge routes never check is_admin, so a normal account rewrites or erases the trail.',
    },
    {
        'id': 'AV-04',
        'title': 'Path traversal in the export',
        'cwe': 'CWE-22',
        'owasp': 'A01:2021 - Broken Access Control',
        'nist': 'PR.DS-6 / DE.CM-9',
        'detail': 'The filename parameter is resolved without secure_filename() or a whitelist, so ../ reads any file the process can read.',
    },
    {
        'id': 'AV-05',
        'title': 'Stored XSS through audit notes',
        'cwe': 'CWE-79',
        'owasp': 'A03:2021 - Injection',
        'nist': 'DE.CM-7 / PR.DS-6',
        'detail': 'Note payloads are stored verbatim and painted with innerHTML in the console, stealing the admin JWT from localStorage.',
    },
    {
        'id': 'AV-06',
        'title': 'Reflected XSS in the console search',
        'cwe': 'CWE-79',
        'owasp': 'A03:2021 - Injection',
        'nist': 'DE.CM-7',
        'detail': 'The search term is echoed into the results header with innerHTML before any request happens.',
    },
    {
        'id': 'AV-07',
        'title': 'No Content-Security-Policy',
        'cwe': 'CWE-693',
        'owasp': 'A05:2021 - Security Misconfiguration',
        'nist': 'PR.DS-6 / DE.CM-7',
        'detail': 'No CSP header is emitted anywhere, so AV-05 and AV-06 run without any restriction.',
    },
    {
        'id': 'AV-08',
        'title': 'Log injection and log forging',
        'cwe': 'CWE-117',
        'owasp': 'A09:2021 - Security Logging and Monitoring Failures',
        'nist': 'DE.CM-3 / DE.AE-3',
        'detail': 'render_audit_line() concatenates stored values with no escaping and _sanitize_for_log() is never called, so an attacker-chosen event field containing a newline renders as a second, believable record. Header values are mirrored raw as well: the WSGI layer drops CR/LF from headers, so header poisoning degrades to field forging (a User-Agent of "x severity=CRITICAL result=SUCCESS actor=admin" rewrites the fields of the rendered line), while any caller that supplies a newline-bearing value (the client-authored event_type/severity/target of POST /api/audit/note, or an upstream proxy that forwards a poisoned header) splits one event into two log lines.',
    },
    {
        'id': 'AV-09',
        'title': 'Audit poisoning',
        'cwe': 'CWE-778',
        'owasp': 'A09:2021 - Security Logging and Monitoring Failures',
        'nist': 'DE.CM-3 / DE.AE-2',
        'detail': 'POST /api/audit/note lets the client author event_type, severity, actor_username and details, planting entries that look legitimate.',
    },
    {
        'id': 'AV-10',
        'title': 'Anti-forensic purge',
        'cwe': 'CWE-778',
        'owasp': 'A09:2021 - Security Logging and Monitoring Failures',
        'nist': 'DE.CM-3 / PR.DS-6',
        'detail': 'The purge writes its own event before deleting, so the DELETE erases the only record that the purge happened.',
    },
    {
        'id': 'AV-11',
        'title': 'Unverifiable integrity (false assurance)',
        'cwe': 'CWE-354',
        'owasp': 'A09:2021 - Security Logging and Monitoring Failures',
        'nist': 'DE.AE-1 / DE.CM-1',
        'detail': 'signature is never written and an unsigned entry is reported as verified, so the detector stays green on a manipulated trail.',
    },
    {
        'id': 'AV-12',
        'title': 'Cross-Site Request Forgery',
        'cwe': 'CWE-352',
        'owasp': 'A08:2021 - Software and Data Integrity Failures',
        'nist': 'PR.AA-5 / PR.DS-6',
        'detail': 'Note, edit, delete and purge accept bare cross-site form posts with no CSRF token and no Origin check.',
    },
    {
        'id': 'AV-13',
        'title': 'HTTP parameter tampering',
        'cwe': 'CWE-807',
        'owasp': 'A08:2021 - Software and Data Integrity Failures',
        'nist': 'PR.AA-5 / DE.CM-3',
        'detail': 'limit, offset, order and the actor identity are client-controlled; the JWT is also accepted from the query string via auth.token_required.',
    },
]

DEMO_ATTACKS = [
    "GET /api/audit/logs?search=' OR '1'='1",
    "GET /api/audit/logs?search=' UNION SELECT username, password, balance FROM users--",
    "GET /api/audit/logs?order=created_at, (SELECT password FROM users LIMIT 1)",
    "GET /api/audit/logs?limit=1; DELETE FROM audit_log;--",
    "GET /api/audit/logs/1        (any logged-in user reads the admin trail)",
    "DELETE /api/audit/logs/1    (no admin check, no CSRF token)",
    "POST /admin/audit/purge     {\"all\": true}",
    "GET /api/audit/logs/export?filename=../../../../etc/passwd",
    "GET /api/audit/logs/1/signature   (always reports verified: true)",
    "curl -H 'User-Agent: x severity=CRITICAL result=SUCCESS actor=admin' /login   (field-level log forging)",
    "POST /api/audit/note  {\"event_type\": \"AUDIT_NOTE_ADDED\\n[2026-01-01 00:00:00] TRANSFER_INITIATED severity=INFO result=SUCCESS actor=admin\"}",
    "POST /api/audit/note  {\"actor_username\": \"admin\", \"details\": \"<img src=x onerror=alert(1)>\"}",
]


def get_client_ip():
    """Trust any proxy header the caller sends (Vulnerability: IP spoofing)."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def _sanitize_for_log(value, max_length=1024):
    """
    Fix (M4-R07): normalize untrusted values before they reach the audit trail.
    Coerce to text, strip CR/LF and other control characters (so a single
    attacker-controlled header cannot forge extra log lines), and clamp the
    length.
    """
    if value is None:
        return None
    text = str(value)
    # Remove CR, LF, tab and other C0/C1 control characters.
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    if len(text) > max_length:
        text = text[:max_length]
    return text


def build_log_context():
    """
    Collect the request metadata attached to every audit event.

    Vulnerability: nothing here is sanitized, length-clamped or validated, and
    X-Forwarded-For is believed without question. An attacker therefore controls
    the exact bytes an investigator will later read as platform-captured
    evidence.
    """
    # Fix (M4-R07): sanitize all client-controlled metadata before it is stored
    # or printed, so injected CR/LF cannot forge extra audit records.
    return {
        'ip_address': _sanitize_for_log(get_client_ip(), max_length=64),
        'user_agent': _sanitize_for_log(request.headers.get('User-Agent', 'unknown'), max_length=256),
        'referer': _sanitize_for_log(request.headers.get('Referer'), max_length=256),
        'request_id': _sanitize_for_log(request.headers.get('X-Request-Id'), max_length=128),
        'http_method': _sanitize_for_log(request.method, max_length=16),
        'endpoint': _sanitize_for_log(request.path, max_length=256),
    }


def render_audit_line(entry):
    """
    Format one audit event as a single text record.

    Vulnerability: the values are concatenated without any escaping, so a CR/LF
    inside a header turns one event into several believable lines.
    """
    return ' '.join([
        f"[{entry.get('created_at')}]",
        str(entry.get('event_type') or '-'),
        f"severity={entry.get('severity') or '-'}",
        f"result={entry.get('result') or '-'}",
        f"actor={entry.get('actor_username') or 'anonymous'}",
        f"target={entry.get('target') or '-'}",
        f"ip={entry.get('ip_address') or '-'}",
        f"ua={entry.get('user_agent') or '-'}",
    ])


def record_event(event_type, severity='INFO', action=None, target=None, details=None,
                 result='SUCCESS', actor=None, context=None):
    """
    Persist one audit event and mirror it to stdout.

    Vulnerabilities:
    - CWE-89: the statement is string-formatted, so a quote inside any
      attacker-controlled header reaches the SQL parser. This is reachable
      unauthenticated, because a failed login records an event built from the
      raw request headers.
    - CWE-117: nothing is escaped, so CR/LF in a header is stored and printed
      verbatim and a client can append forged records to the trail and stdout.
    - CWE-354: signature is left NULL, so nothing recorded here is verifiable.
    - Recording never blocks the request it is recording, which also means a
      broken statement leaves the trail silently missing an event.
    """
    if context is None:
        context = build_log_context()

    actor = actor or {}

    entry = {
        # Fix (M4-R07): sanitize every text field so no CR/LF or control bytes
        # reach the database or stdout (prevents log/record forging).
        'event_type': _sanitize_for_log(event_type, 64),
        'severity': _sanitize_for_log(severity, 32),
        'actor_id': actor.get('user_id'),
        'actor_username': _sanitize_for_log(actor.get('username'), 128),
        'action': _sanitize_for_log(action or event_type, 64),
        'target': _sanitize_for_log(target, 256),
        'details': _sanitize_for_log(details, 1024),
        'ip_address': context.get('ip_address'),
        'user_agent': context.get('user_agent'),
        'referer': context.get('referer'),
        'request_id': context.get('request_id'),
        'http_method': context.get('http_method'),
        'endpoint': context.get('endpoint'),
        'result': _sanitize_for_log(result, 32),
        'created_at': datetime.now().isoformat(sep=' ', timespec='seconds'),
    }

    try:
        # Fix (M4-R02): fully parameterized INSERT; no attacker-controlled value
        # is concatenated into the statement.
        execute_query(
            """
            INSERT INTO audit_log
                (event_type, severity, actor_id, actor_username, action, target, details,
                 ip_address, user_agent, referer, request_id, http_method, endpoint,
                 result, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                entry['event_type'], entry['severity'], entry['actor_id'],
                entry['actor_username'], entry['action'], entry['target'],
                entry['details'], entry['ip_address'], entry['user_agent'],
                entry['referer'], entry['request_id'], entry['http_method'],
                entry['endpoint'], entry['result'], entry['created_at'],
            ),
            fetch=False
        )
    except Exception as e:
        # Fix (M4-R02): do not drop records silently; surface the failure loudly
        # (to stderr) so missing audit coverage is visible to operators.
        sys.stderr.write(f"[AUDIT][ERROR] Audit write failed for {event_type}: {e}\n")
        sys.stderr.flush()

    print(render_audit_line(entry))

    return entry


def compute_entry_signature(entry):
    """
    Seam for Phase 3: HMAC-SHA256 over the canonical representation of a row.

    Vulnerability: with no signing key configured the recomputation returns an
    empty string, so there is nothing meaningful to compare a stored signature
    against and every check degrades into a no-op.
    """
    if not AUDIT_SIGNING_SECRET:
        return ''

    canonical = '|'.join(str(entry.get(field) or '') for field in AUDIT_SIGNATURE_FIELDS)
    return hmac.new(
        AUDIT_SIGNING_SECRET.encode('utf-8'),
        canonical.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def verify_entry_signature(entry):
    """
    Decide whether an audit entry is untampered.

    Vulnerability: an entry with no stored signature is reported as verified
    instead of as unsigned. There is no third state, so a row that an attacker
    edited, injected or restored is indistinguishable from a clean one, and the
    detector keeps reporting a healthy trail.
    """
    stored = entry.get('signature') or ''
    recomputed = compute_entry_signature(entry)

    if not stored or not recomputed:
        return {
            'verified': True,
            'checked': False,
            'signed': False,
            'reason': 'No signature material available; entry accepted as-is',
        }

    matched = hmac.compare_digest(stored, recomputed)

    return {
        'verified': matched,
        'checked': True,
        'signed': True,
        'reason': 'Signature matches' if matched else 'Signature mismatch',
    }


def row_to_entry(row):
    """Normalize a database row into a JSON-safe audit entry."""

    entry = {}
    for index, key in enumerate(AUDIT_COLUMN_KEYS):
        value = row[index] if index < len(row) else None
        if value is None or isinstance(value, (int, float)):
            entry[key] = value
        elif hasattr(value, 'isoformat'):
            entry[key] = value.isoformat()
        else:
            entry[key] = str(value)
    return entry


def entries_to_csv(entries):
    """Serialize audit entries as CSV."""

    lines = [','.join(AUDIT_COLUMN_KEYS)]
    for entry in entries:
        cells = []
        for key in AUDIT_COLUMN_KEYS:
            value = entry.get(key)
            value = '' if value is None else str(value)
            if any(marker in value for marker in (',', '"', '\n', '\r')):
                value = '"' + value.replace('"', '""') + '"'
            cells.append(value)
        lines.append(','.join(cells))
    return '\n'.join(lines)


def _bool_from_request(value):
    """Read a loosely typed boolean flag from JSON or form data."""

    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def json_detail(payload):
    """Render an audit detail payload as text."""

    return json.dumps(payload)


def init_audit_routes(app):
    @app.route('/admin/audit')
    @admin_required
    def audit_console(current_user):
        if not current_user.get('is_admin'):
            return 'Access Denied', 403

        return render_template(
            'audit_admin.html',
            event_types=AUDIT_EVENT_TYPES,
            severities=AUDIT_SEVERITIES,
            module_vulnerabilities=MODULE_VULNERABILITIES,
            demo_attacks=DEMO_ATTACKS,
        )

    @app.route('/api/audit/logs', methods=['GET'])
    @admin_required
    def list_audit_logs(current_user):
        """
        Filter and page the audit trail.

        Vulnerability (AV-01, AV-13): every filter is interpolated with f-strings
        and the paging bounds and sort order are interpolated too, so the console
        search doubles as a SQL console. The same route accepts a user_id that
        belongs to somebody else, and it inherits token-in-query-string from
        auth.token_required.
        """
        try:
            search = request.args.get('search', '')
            event_type = request.args.get('event_type', '')
            severity = request.args.get('severity', '')
            actor = request.args.get('actor', '')
            user_id = request.args.get('user_id', '')
            date_from = request.args.get('from', '')
            date_to = request.args.get('to', '')
            limit = request.args.get('limit', 100)
            offset = request.args.get('offset', 0)
            order = request.args.get('order', 'created_at DESC')

            # Fix (M4-R01): every filter value is bound as a parameter.
            conditions = []
            params = []

            if search:
                conditions.append(
                    "(event_type ILIKE %s OR actor_username ILIKE %s OR target ILIKE %s "
                    "OR details ILIKE %s OR user_agent ILIKE %s)"
                )
                like = f"%{search}%"
                params.extend([like, like, like, like, like])
            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type)
            if severity:
                conditions.append("severity = %s")
                params.append(severity)
            if actor:
                conditions.append("actor_username ILIKE %s")
                params.append(f"%{actor}%")
            if user_id:
                try:
                    uid = int(user_id)
                except (ValueError, TypeError):
                    return jsonify({'status': 'error', 'message': 'Invalid user_id'}), 400
                conditions.append("actor_id = %s")
                params.append(uid)
            if date_from:
                conditions.append("created_at >= %s")
                params.append(date_from)
            if date_to:
                conditions.append("created_at <= %s")
                params.append(date_to)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ''

            # Fix (M4-R01/M4-R15): sort order is a whitelist; limit/offset are
            # bounded integers, so paging can no longer inject SQL or exhaust RAM.
            ALLOWED_ORDER = {
                'created_at DESC': 'created_at DESC',
                'created_at ASC': 'created_at ASC',
                'id DESC': 'id DESC',
                'id ASC': 'id ASC',
            }
            order_sql = ALLOWED_ORDER.get(order, 'created_at DESC')
            try:
                limit = min(max(int(limit), 1), 500)
                offset = max(int(offset), 0)
            except (ValueError, TypeError):
                limit, offset = 100, 0

            entries = execute_query(
                f"""
                SELECT {AUDIT_TABLE_COLUMNS}
                FROM audit_log
                {where_clause}
                ORDER BY {order_sql}
                LIMIT %s OFFSET %s
                """,
                tuple(params) + (limit, offset),
            )

            total = execute_query(
                f"SELECT COUNT(*) FROM audit_log{where_clause}",
                tuple(params),
            )[0][0]

            return jsonify({
                'status': 'success',
                'count': len(entries),
                'total': total,
                'limit': limit,
                'offset': offset,
                'order': order,
                'filters': {
                    'search': search,
                    'event_type': event_type,
                    'severity': severity,
                    'actor': actor,
                    'user_id': user_id,
                    'from': date_from,
                    'to': date_to,
                },
                'entries': [row_to_entry(row) for row in entries],
                'debug_info': {
                    'generated_by': current_user['username'],
                    'generated_at': datetime.now().isoformat(),
                    'query_fragments': conditions,
                    'requested_by_ip': get_client_ip(),
                },
            })

        except Exception as e:
            print(f"Audit list error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/api/audit/logs/export', methods=['GET'])
    @admin_required
    def export_audit_logs(current_user):
        """
        Export the trail as CSV or JSON.

        Vulnerability (AV-04): the export format is not whitelisted and the
        filename is joined onto the export directory without secure_filename() or
        normalization, so a traversal returns any file the process can read. The
        export itself is also unmetered and unpaged, so the whole trail leaves the
        box in one request.
        """
        try:
            export_format = request.args.get('format', 'csv')
            filename = request.args.get('filename', f'audit_export.{export_format}')

            entries = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log ORDER BY id ASC LIMIT 5000"
            )
            records = [row_to_entry(row) for row in entries]

            if export_format.lower() == 'json':
                body = jsonify({'status': 'success', 'count': len(records), 'entries': records})
                mimetype = 'application/json'
            else:
                body = entries_to_csv(records)
                mimetype = 'text/csv'

            requested_path = os.path.join(AUDIT_EXPORT_DIRECTORY, filename)

            if os.path.isfile(requested_path):
                return send_file(
                    requested_path,
                    as_attachment=True,
                    download_name=os.path.basename(filename),
                    mimetype=mimetype,
                )

            return Response(
                body if isinstance(body, str) else body.get_data(as_text=True),
                mimetype=mimetype,
                headers={
                    'Content-Disposition': f'attachment; filename={os.path.basename(filename)}'
                },
            )

        except Exception as e:
            print(f"Audit export error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/api/audit/logs/<int:log_id>', methods=['GET'])
    @admin_required
    def get_audit_log(current_user, log_id):
        """
        Fetch a single audit entry.

        Vulnerability (AV-02): the only check is that a token exists. There is no
        ownership or administrator check, so any logged-in customer can read the
        admin trail entry by entry, or walk it with an incrementing id.
        """
        try:
            entries = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log WHERE id = {log_id}"
            )

            if not entries:
                return jsonify({
                    'status': 'error',
                    'message': 'Audit entry not found',
                    'log_id': log_id,
                }), 404

            entry = row_to_entry(entries[0])

            return jsonify({
                'status': 'success',
                'entry': entry,
                'debug_info': {
                    'requested_by': current_user['username'],
                    'requested_by_id': current_user.get('user_id'),
                    'requested_by_is_admin': current_user.get('is_admin'),
                    'requested_at': datetime.now().isoformat(),
                },
            })

        except Exception as e:
            print(f"Audit fetch error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'log_id': log_id,
            }), 500

    @app.route('/api/audit/logs/<int:log_id>/signature', methods=['GET'])
    @admin_required
    def get_audit_log_signature(current_user, log_id):
        """
        Report the integrity verdict for one entry.

        Vulnerability (AV-11): record_event() never writes a signature and no key
        is configured, so verify_entry_signature() takes the unsigned branch and
        answers verified: true. The verdict is indistinguishable from a real one.
        """
        try:
            entries = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log WHERE id = {log_id}"
            )

            if not entries:
                return jsonify({
                    'status': 'error',
                    'message': 'Audit entry not found',
                    'log_id': log_id,
                }), 404

            entry = row_to_entry(entries[0])
            verdict = verify_entry_signature(entry)

            return jsonify({
                'status': 'success',
                'log_id': log_id,
                'integrity': verdict,
                'stored_signature': entry.get('signature'),
                'debug_info': {
                    'signing_key_configured': bool(AUDIT_SIGNING_SECRET),
                    'fields_covered': list(AUDIT_SIGNATURE_FIELDS),
                    'checked_at': datetime.now().isoformat(),
                },
            })

        except Exception as e:
            print(f"Audit signature check error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'log_id': log_id,
            }), 500

    @app.route('/admin/audit/integrity-check', methods=['GET'])
    @admin_required
    def audit_integrity_check(current_user):
        """
        Sweep the whole trail and report tampering.

        Vulnerability (AV-11): the sweep counts unsigned entries and then declares
        them verified anyway, so `tampered` is always 0 and `overall` is always
        'verified'. After a purge the sweep reports a clean trail over an empty
        table, which is precisely the DETECT failure NIST CSF 2.0 DE.AE is meant
        to prevent.
        """
        try:
            scan_limit = request.args.get('limit', 500)

            entries = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log ORDER BY id DESC LIMIT {scan_limit}"
            )

            checked = 0
            unsigned = 0
            tampered = 0

            for row in entries:
                entry = row_to_entry(row)
                verdict = verify_entry_signature(entry)
                checked += 1
                if not verdict['signed']:
                    unsigned += 1
                if verdict['checked'] and not verdict['verified']:
                    tampered += 1

            return jsonify({
                'status': 'success',
                'integrity': {
                    'checked': checked,
                    'verified': checked - tampered,
                    'unsigned': unsigned,
                    'tampered': tampered,
                    'overall': 'verified' if tampered == 0 else 'compromised',
                },
                'message': 'All audit entries verified successfully'
                if tampered == 0
                else f'{tampered} audit entries failed verification',
                'debug_info': {
                    'signing_key_configured': bool(AUDIT_SIGNING_SECRET),
                    'scan_limit': scan_limit,
                    'requested_by': current_user['username'],
                    'checked_at': datetime.now().isoformat(),
                    'note': 'Unsigned entries are counted separately but still reported as verified',
                },
            })

        except Exception as e:
            print(f"Audit integrity check error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/api/audit/stats', methods=['GET'])
    @admin_required
    def audit_stats(current_user):
        """
        Aggregate counters for the console metric cards.

        Vulnerability (AV-01, AV-13): the window, severity and actor filters are
        interpolated, and the unsigned counter it reports is the only honest number
        on the page while the integrity banner right above it claims the trail is
        verified.
        """
        try:
            window = request.args.get('window', 24)
            severity_filter = request.args.get('severity', '')
            actor_filter = request.args.get('actor', '')

            conditions = []
            if severity_filter:
                conditions.append(f"severity = '{severity_filter}'")
            if actor_filter:
                conditions.append(f"actor_username ILIKE '%{actor_filter}%'")
            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ''

            total = execute_query(f"SELECT COUNT(*) FROM audit_log{where_clause}")[0][0]
            by_severity = execute_query(
                f"SELECT severity, COUNT(*) FROM audit_log{where_clause} "
                "GROUP BY severity ORDER BY 2 DESC"
            )
            by_event = execute_query(
                f"SELECT event_type, COUNT(*) FROM audit_log{where_clause} "
                "GROUP BY event_type ORDER BY 2 DESC LIMIT 12"
            )
            top_actors = execute_query(
                f"SELECT actor_username, COUNT(*) FROM audit_log{where_clause} "
                "GROUP BY actor_username ORDER BY 2 DESC LIMIT 10"
            )
            hourly_conditions = list(conditions)
            hourly_conditions.append(
                f"created_at >= CURRENT_TIMESTAMP - make_interval(hours => {window})"
            )
            hourly = execute_query(
                "SELECT date_trunc('hour', created_at), COUNT(*) FROM audit_log "
                f"WHERE {' AND '.join(hourly_conditions)} "
                "GROUP BY 1 ORDER BY 1"
            )
            unsigned_conditions = list(conditions)
            unsigned_conditions.append("(signature IS NULL OR signature = '')")
            unsigned = execute_query(
                f"SELECT COUNT(*) FROM audit_log WHERE {' AND '.join(unsigned_conditions)}"
            )[0][0]

            return jsonify({
                'status': 'success',
                'stats': {
                    'total': total,
                    'window_hours': window,
                    'by_severity': [
                        {'severity': row[0], 'count': row[1]} for row in by_severity
                    ],
                    'by_event_type': [
                        {'event_type': row[0], 'count': row[1]} for row in by_event
                    ],
                    'top_actors': [
                        {'actor_username': row[0], 'count': row[1]} for row in top_actors
                    ],
                    'activity_by_hour': [
                        {
                            'hour': row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                            'count': row[1],
                        }
                        for row in hourly
                    ],
                    'unsigned_entries': unsigned,
                },
                'integrity': {
                    'unsigned_entries': unsigned,
                    'claimed_status': 'verified',
                    'note': 'Entries without a signature are still reported as verified',
                },
            })

        except Exception as e:
            print(f"Audit stats error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/api/audit/tail', methods=['GET'])
    @admin_required
    def audit_tail(current_user):
        """
        Stream the most recent events as plain text lines.

        Vulnerability (AV-02, AV-13): there is no ownership check on the trail and
        `lines` is interpolated, so the endpoint both leaks the whole trail to any
        token and doubles as an injection point. The lines are the forged ones that
        log injection produced, presented as if they were platform output.
        """
        try:
            lines = request.args.get('lines', 50)
            follow = _bool_from_request(request.args.get('follow', '0'))

            entries = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log ORDER BY id DESC LIMIT {lines}"
            )

            rendered = [render_audit_line(row_to_entry(row)) for row in entries]
            rendered.reverse()

            return jsonify({
                'status': 'success',
                'follow': follow,
                'count': len(rendered),
                'lines': rendered,
                'debug_info': {
                    'requested_by': current_user['username'],
                    'requested_lines': lines,
                    'requested_at': datetime.now().isoformat(),
                },
            })

        except Exception as e:
            print(f"Audit tail error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/api/audit/note', methods=['POST'])
    @admin_required
    def add_audit_note(current_user):
        """
        Append a free-text annotation to an event.

        Vulnerability (AV-09, AV-13): the client authors the whole event. The
        attacker supplies event_type, severity, actor_id and actor_username, so
        the trail fills up with entries that the platform itself appears to have
        written on the admin's behalf.

        Vulnerability (AV-05): details is stored exactly as received and later
        painted with innerHTML, turning the console into a stored XSS sink that
        runs in an administrator's session.

        Vulnerability (AV-12): no CSRF token and no Origin check, so a third-party
        page can post notes into an admin's browser.
        """
        try:
            data = request.get_json(silent=True) or {}
            details = data.get('details', '')
            target = data.get('target') or f"log:{data.get('log_id', 'console')}"

            # Fix (M4-R06): the actor is always derived from the authenticated
            # token; the client cannot impersonate another user. The event type
            # and severity are fixed, not client-supplied.
            note_actor = {
                'user_id': current_user.get('user_id'),
                'username': current_user.get('username'),
            }

            entry = record_event(
                'AUDIT_NOTE_ADDED',
                severity='INFO',
                action='note',
                target=target,
                details=details,
                result='SUCCESS',
                actor=note_actor,
            )

            return jsonify({
                'status': 'success',
                'message': 'Note added to the audit trail',
                'entry': entry,
            })

        except Exception as e:
            print(f"Audit note error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500

    @app.route('/admin/audit/logs/<int:log_id>', methods=['POST'])
    @admin_required
    def edit_audit_log(current_user, log_id):
        """
        Amend an existing audit entry in place.

        Vulnerability (AV-03): the route never checks is_admin, so any account can
        rewrite history. Vulnerability (AV-01): the values are interpolated. There
        is no re-verification after the write, and the signature column is left
        exactly as it was, so an edited row keeps whatever verdict it had.
        """
        try:
            data = request.get_json(silent=True) or {}

            existing = execute_query(
                f"SELECT id FROM audit_log WHERE id = {log_id}"
            )

            if not existing:
                return jsonify({
                    'status': 'error',
                    'message': 'Audit entry not found',
                    'log_id': log_id,
                }), 404

            if 'event_type' in data:
                execute_query(
                    f"UPDATE audit_log SET event_type = '{data.get('event_type')}' WHERE id = {log_id}",
                    fetch=False
                )
            if 'severity' in data:
                execute_query(
                    f"UPDATE audit_log SET severity = '{data.get('severity')}' WHERE id = {log_id}",
                    fetch=False
                )
            if 'actor_username' in data:
                execute_query(
                    f"UPDATE audit_log SET actor_username = '{data.get('actor_username')}' WHERE id = {log_id}",
                    fetch=False
                )
            if 'target' in data:
                execute_query(
                    f"UPDATE audit_log SET target = '{data.get('target')}' WHERE id = {log_id}",
                    fetch=False
                )
            if 'result' in data:
                execute_query(
                    f"UPDATE audit_log SET result = '{data.get('result')}' WHERE id = {log_id}",
                    fetch=False
                )
            if 'details' in data:
                execute_query(
                    f"UPDATE audit_log SET details = '{data.get('details')}' WHERE id = {log_id}",
                    fetch=False
                )

            return jsonify({
                'status': 'success',
                'message': 'Audit entry updated',
                'log_id': log_id,
                'debug_info': {
                    'edited_by': current_user['username'],
                    'edited_by_is_admin': current_user.get('is_admin'),
                    'fields': list(data.keys()),
                    'edited_at': datetime.now().isoformat(),
                    'integrity_rechecked': False,
                },
            })

        except Exception as e:
            print(f"Audit edit error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'log_id': log_id,
            }), 500

    @app.route('/api/audit/logs/<int:log_id>', methods=['DELETE'])
    @admin_required
    def delete_audit_log(current_user, log_id):
        """
        Remove one audit entry.

        Vulnerability (AV-03): no administrator check. Vulnerability (AV-12): no
        CSRF token. The delete is not written back to the trail, so the record that
        an entry was removed does not exist either.
        """
        try:
            existing = execute_query(
                f"SELECT {AUDIT_TABLE_COLUMNS} FROM audit_log WHERE id = {log_id}"
            )

            if not existing:
                return jsonify({
                    'status': 'error',
                    'message': 'Audit entry not found',
                    'log_id': log_id,
                }), 404

            entry = row_to_entry(existing[0])

            execute_query(f"DELETE FROM audit_log WHERE id = {log_id}", fetch=False)

            return jsonify({
                'status': 'success',
                'message': 'Audit entry deleted',
                'log_id': log_id,
                'deleted': entry,
                'debug_info': {
                    'deleted_by': current_user['username'],
                    'deleted_by_is_admin': current_user.get('is_admin'),
                    'deleted_at': datetime.now().isoformat(),
                    'deletion_logged': False,
                },
            })

        except Exception as e:
            print(f"Audit delete error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
                'log_id': log_id,
            }), 500

    @app.route('/admin/audit/purge', methods=['POST'])
    @admin_required
    def purge_audit_logs(current_user):
        """
        Bulk-delete audit entries, optionally the entire table.

        Vulnerability (AV-10): the purge writes its own AUDIT_LOG_PURGED event
        before deleting, so the very next statement erases the only record that the
        purge happened. There is no administrator check, no CSRF token and no
        approval step, and nothing is archived first.

        Vulnerability (AV-01): the `before` and `event_type` cutoffs are
        interpolated, so the selective purge is also an injection point.
        """
        try:
            data = request.get_json(silent=True) or {}
            purge_all = _bool_from_request(data.get('all', False))
            before = data.get('before')
            event_type = data.get('event_type')
            severity = data.get('severity')

            conditions = []
            if before:
                conditions.append(f"created_at < '{before}'")
            if event_type:
                conditions.append(f"event_type = '{event_type}'")
            if severity:
                conditions.append(f"severity = '{severity}'")

            # The purge announces itself first, and then removes the announcement.
            record_event(
                'AUDIT_LOG_PURGED',
                severity='WARNING',
                action='purge',
                target=data.get('target') or 'audit_log',
                details=json_detail({
                    'all': purge_all,
                    'before': before,
                    'event_type': event_type,
                    'severity': severity,
                }),
                actor={
                    'user_id': current_user.get('user_id'),
                    'username': current_user.get('username'),
                },
            )

            if purge_all:
                execute_query("DELETE FROM audit_log", fetch=False)
            elif conditions:
                execute_query(
                    f"DELETE FROM audit_log WHERE {' AND '.join(conditions)}",
                    fetch=False
                )

            return jsonify({
                'status': 'success',
                'message': 'Audit trail purged',
                'scope': 'all' if purge_all else 'filtered',
                'filters': {
                    'all': purge_all,
                    'before': before,
                    'event_type': event_type,
                    'severity': severity,
                },
                'debug_info': {
                    'purged_by': current_user['username'],
                    'purged_by_is_admin': current_user.get('is_admin'),
                    'purged_at': datetime.now().isoformat(),
                    'retention_policy': None,
                    'archived_before_delete': False,
                    'self_record_survives': False,
                },
            })

        except Exception as e:
            print(f"Audit purge error: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e),
            }), 500