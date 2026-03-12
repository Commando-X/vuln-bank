import json
import random
import re
import traceback
from datetime import datetime

from flask import jsonify, request

from auth import verify_token
from database import execute_query


def _extract_current_user_unsafe():
    """
    Intentionally weak auth extraction for GraphQL endpoint.
    GraphQL-specific bug: token accepted from multiple sources and auth is optional.
    """
    token = None

    auth_header = request.headers.get('Authorization')
    if auth_header:
        if 'Bearer ' in auth_header:
            parts = auth_header.split(' ')
            if len(parts) > 1:
                token = parts[1]
        else:
            token = auth_header

    if not token:
        token = request.args.get('token')

    if not token:
        body = request.get_json(silent=True) or {}
        token = body.get('token')

    if not token:
        return None

    return verify_token(token)


def _beneficiary_to_dict(row):
    return {
        'id': row[0],
        'user_id': row[1],
        'account_number': row[2],
        'beneficiary_name': row[3],
        'nickname': row[4],
        'transfer_limit': float(row[5]) if row[5] is not None else 0.0,
        'is_verified': bool(row[6]),
        'otp_code': row[7],
        'verified_at': str(row[8]) if row[8] else None,
        'created_at': str(row[9]) if row[9] else None,
    }


def _get_inline_input_object(query, arg_name='input'):
    # Very naive parser for inline GraphQL input objects.
    pattern = re.compile(rf'{arg_name}\s*:\s*\{{(.*?)\}}', re.DOTALL)
    match = pattern.search(query or '')
    if not match:
        return {}

    body = match.group(1)
    pairs = re.findall(r'(\w+)\s*:\s*("[^"]*"|\d+\.\d+|\d+|true|false|null)', body)

    parsed = {}
    for key, raw_value in pairs:
        value = raw_value
        if raw_value.startswith('"') and raw_value.endswith('"'):
            value = raw_value[1:-1]
        elif raw_value in ('true', 'false'):
            value = raw_value == 'true'
        elif raw_value == 'null':
            value = None
        elif '.' in raw_value:
            try:
                value = float(raw_value)
            except ValueError:
                value = raw_value
        else:
            try:
                value = int(raw_value)
            except ValueError:
                value = raw_value

        parsed[key] = value

    return parsed


def _get_inline_int_arg(query, arg_name):
    match = re.search(rf'{arg_name}\s*:\s*(\d+)', query or '')
    if not match:
        return None
    return int(match.group(1))


def _get_inline_string_arg(query, arg_name):
    match = re.search(rf'{arg_name}\s*:\s*"([^"]*)"', query or '')
    if not match:
        return None
    return match.group(1)


def _get_inline_bool_arg(query, arg_name):
    match = re.search(rf'{arg_name}\s*:\s*(true|false)', query or '')
    if not match:
        return None
    return match.group(1) == 'true'


def _name_enquiry(account_number):
    # Vulnerability: SQL injection through account_number interpolation.
    result = execute_query(
        f"SELECT id, username, account_number FROM users WHERE account_number='{account_number}'"
    )
    if result:
        return {
            'account_holder_name': result[0][1],
            'account_number': result[0][2],
            'matched_user_id': result[0][0],
        }
    return {
        'account_holder_name': 'Unknown Account',
        'account_number': account_number,
        'matched_user_id': None,
    }


def _list_beneficiaries(current_user, user_id=None):
    # Vulnerability (IDOR): user_id can be supplied to read another user's beneficiaries.
    target_user_id = user_id
    if target_user_id is None and current_user:
        target_user_id = current_user.get('user_id')

    if target_user_id is None:
        rows = execute_query('SELECT * FROM beneficiaries ORDER BY id DESC')
    else:
        rows = execute_query(
            f'SELECT * FROM beneficiaries WHERE user_id = {target_user_id} ORDER BY id DESC'
        )

    return [_beneficiary_to_dict(row) for row in rows]


def _get_beneficiary_by_id(beneficiary_id):
    # Vulnerability (IDOR): no owner/role check.
    rows = execute_query(f'SELECT * FROM beneficiaries WHERE id = {beneficiary_id}')
    if not rows:
        return None
    return _beneficiary_to_dict(rows[0])


def _add_beneficiary(current_user, input_data):
    # Vulnerability: user_id can be client-controlled (BOLA / privilege escalation).
    user_id = input_data.get('user_id')
    if user_id is None and current_user:
        user_id = current_user.get('user_id')

    if user_id is None:
        raise Exception('user_id is required when no token is provided')

    account_number = input_data.get('account_number')
    if not account_number:
        raise Exception('account_number is required')

    enquiry = _name_enquiry(account_number)

    # Feature: nickname + transfer limit per beneficiary.
    nickname = input_data.get('nickname')
    transfer_limit = float(input_data.get('transfer_limit', 5000.0))

    # Vulnerability: bypass verification by allowing is_verified from input.
    is_verified = bool(input_data.get('is_verified', False))

    otp_code = str(random.randint(100000, 999999))
    beneficiary_name = input_data.get('beneficiary_name') or enquiry['account_holder_name']
    verified_at = datetime.now() if is_verified else None

    created = execute_query(
        """
        INSERT INTO beneficiaries
        (user_id, account_number, beneficiary_name, nickname, transfer_limit, is_verified, otp_code, verified_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            user_id,
            account_number,
            beneficiary_name,
            nickname,
            transfer_limit,
            is_verified,
            otp_code,
            verified_at,
        ),
    )

    beneficiary = _beneficiary_to_dict(created[0])

    # Vulnerability: OTP is returned in API response.
    beneficiary['generated_otp'] = otp_code
    beneficiary['name_enquiry'] = enquiry
    return beneficiary


def _update_beneficiary(beneficiary_id, input_data):
    if not input_data:
        raise Exception('input is required')

    # Vulnerability: Mass assignment - dynamic updates with no field whitelist.
    updates = []
    values = []
    for key, value in input_data.items():
        updates.append(f"{key} = %s")
        values.append(value)

    query = f"""
        UPDATE beneficiaries
        SET {', '.join(updates)}
        WHERE id = {beneficiary_id}
        RETURNING *
    """

    rows = execute_query(query, tuple(values))
    if not rows:
        raise Exception('beneficiary not found')

    return _beneficiary_to_dict(rows[0])


def _delete_beneficiary(beneficiary_id):
    # Vulnerability: No authentication/authorization check.
    rows = execute_query(
        f'DELETE FROM beneficiaries WHERE id = {beneficiary_id} RETURNING id, user_id, account_number'
    )

    if not rows:
        return {
            'success': False,
            'message': 'Beneficiary not found',
            'deleted_beneficiary_id': beneficiary_id,
        }

    return {
        'success': True,
        'message': 'Beneficiary deleted',
        'deleted_beneficiary_id': rows[0][0],
        'deleted_user_id': rows[0][1],
        'deleted_account_number': rows[0][2],
    }


def _verify_beneficiary(beneficiary_id, auto_verify=False):
    # Vulnerability (IDOR): no ownership check on beneficiary_id.
    rows = execute_query(f'SELECT * FROM beneficiaries WHERE id = {beneficiary_id}')
    if not rows:
        raise Exception('beneficiary not found')

    beneficiary = _beneficiary_to_dict(rows[0])
    enquiry = _name_enquiry(beneficiary['account_number'])

    otp_code = str(random.randint(100000, 999999))

    if auto_verify:
        # Vulnerability: explicit bypass flag.
        updated = execute_query(
            """
            UPDATE beneficiaries
            SET is_verified = TRUE, otp_code = %s, verified_at = %s, beneficiary_name = %s
            WHERE id = %s
            RETURNING *
            """,
            (otp_code, datetime.now(), enquiry['account_holder_name'], beneficiary_id),
        )
    else:
        updated = execute_query(
            """
            UPDATE beneficiaries
            SET otp_code = %s, beneficiary_name = %s
            WHERE id = %s
            RETURNING *
            """,
            (otp_code, enquiry['account_holder_name'], beneficiary_id),
        )

    result = _beneficiary_to_dict(updated[0])
    result['name_enquiry'] = enquiry
    # Vulnerability: OTP disclosure.
    result['otp'] = otp_code
    result['auto_verified'] = auto_verify
    return result


def _verify_beneficiary_otp(beneficiary_id, otp):
    rows = execute_query(f'SELECT * FROM beneficiaries WHERE id = {beneficiary_id}')
    if not rows:
        raise Exception('beneficiary not found')

    beneficiary = _beneficiary_to_dict(rows[0])
    stored_otp = beneficiary.get('otp_code')

    # Vulnerability: hardcoded OTP bypass.
    bypass_used = otp == '000000'
    is_valid = bypass_used or (otp == stored_otp)

    if is_valid:
        updated = execute_query(
            """
            UPDATE beneficiaries
            SET is_verified = TRUE, verified_at = %s
            WHERE id = %s
            RETURNING *
            """,
            (datetime.now(), beneficiary_id),
        )

        verified_beneficiary = _beneficiary_to_dict(updated[0])
        return {
            'success': True,
            'message': 'Beneficiary OTP verification successful',
            'bypass_used': bypass_used,
            'beneficiary': verified_beneficiary,
        }

    # Vulnerability: excessive debug exposure.
    return {
        'success': False,
        'message': 'Invalid OTP',
        'expected_otp': stored_otp,
        'provided_otp': otp,
        'beneficiary': beneficiary,
    }


def _graphql_introspection_schema():
    # Intentionally exposed introspection response.
    return {
        'queryType': {
            'name': 'Query'
        },
        'mutationType': {
            'name': 'Mutation'
        },
        'types': [
            {
                'name': 'Query',
                'fields': [
                    {'name': 'beneficiaries'},
                    {'name': 'beneficiary'},
                    {'name': 'nameEnquiry'},
                ],
            },
            {
                'name': 'Mutation',
                'fields': [
                    {'name': 'addBeneficiary'},
                    {'name': 'updateBeneficiary'},
                    {'name': 'deleteBeneficiary'},
                    {'name': 'verifyBeneficiary'},
                    {'name': 'verifyBeneficiaryOtp'},
                ],
            },
        ],
        'security_notice': 'Introspection is enabled in production for demo purposes',
    }


def _handle_graphql_request_item(payload):
    query = payload.get('query', '')
    variables = payload.get('variables') or {}

    if isinstance(variables, str):
        try:
            variables = json.loads(variables)
        except Exception:
            variables = {}

    current_user = _extract_current_user_unsafe()

    data = {}

    # GraphQL-specific bug: unrestricted introspection enabled.
    if '__schema' in query or '__type' in query:
        data['__schema'] = _graphql_introspection_schema()

    # Queries
    if re.search(r'\bbeneficiaries\b', query):
        user_id = variables.get('userId')
        if user_id is None:
            user_id = _get_inline_int_arg(query, 'userId')

        data['beneficiaries'] = _list_beneficiaries(current_user, user_id)

    if re.search(r'\bbeneficiary\s*\(', query):
        beneficiary_id = variables.get('beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = variables.get('id')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'id')

        data['beneficiary'] = _get_beneficiary_by_id(beneficiary_id)

    if re.search(r'\bnameEnquiry\s*\(', query):
        account_number = variables.get('accountNumber')
        if account_number is None:
            account_number = _get_inline_string_arg(query, 'accountNumber')

        data['nameEnquiry'] = _name_enquiry(account_number)

    # Mutations
    if re.search(r'\baddBeneficiary\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['addBeneficiary'] = _add_beneficiary(current_user, input_data)

    if re.search(r'\bupdateBeneficiary\s*\(', query):
        beneficiary_id = variables.get('beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = variables.get('id')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'id')

        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['updateBeneficiary'] = _update_beneficiary(beneficiary_id, input_data)

    if re.search(r'\bdeleteBeneficiary\s*\(', query):
        beneficiary_id = variables.get('beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = variables.get('id')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'id')

        data['deleteBeneficiary'] = _delete_beneficiary(beneficiary_id)

    if re.search(r'\bverifyBeneficiaryOtp\s*\(', query):
        beneficiary_id = variables.get('beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = variables.get('id')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'id')

        otp = variables.get('otp')
        if otp is None:
            otp = _get_inline_string_arg(query, 'otp')

        data['verifyBeneficiaryOtp'] = _verify_beneficiary_otp(beneficiary_id, otp)

    if re.search(r'\bverifyBeneficiary\s*\(', query):
        beneficiary_id = variables.get('beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = variables.get('id')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'beneficiaryId')
        if beneficiary_id is None:
            beneficiary_id = _get_inline_int_arg(query, 'id')

        auto_verify = variables.get('autoVerify')
        if auto_verify is None:
            auto_verify = _get_inline_bool_arg(query, 'autoVerify')
        if auto_verify is None:
            auto_verify = False

        data['verifyBeneficiary'] = _verify_beneficiary(beneficiary_id, auto_verify)

    if not data:
        return {
            'data': None,
            'errors': [
                {
                    'message': 'Unsupported GraphQL operation',
                    'query': query,
                    'variables': variables,
                }
            ],
        }

    return {'data': data}


def init_beneficiary_graphql_routes(app):
    @app.route('/graphql/beneficiaries', methods=['GET', 'POST'])
    def graphql_beneficiaries():
        """
        Intentionally vulnerable GraphQL-like endpoint for beneficiary management.

        GraphQL-specific vulnerabilities:
        - No query depth or complexity limits
        - Introspection enabled in all environments
        - Verbose error messages with traces
        - Batch operations without safeguards
        """
        try:
            if request.method == 'GET':
                payload = {
                    'query': request.args.get('query', ''),
                    'variables': request.args.get('variables') or {},
                    'operationName': request.args.get('operationName'),
                }
            else:
                payload = request.get_json(silent=True) or {}

            # GraphQL-specific bug: accepts arbitrary batch size with no limits.
            if isinstance(payload, list):
                results = []
                for item in payload:
                    try:
                        results.append(_handle_graphql_request_item(item or {}))
                    except Exception as item_error:
                        results.append({
                            'data': None,
                            'errors': [
                                {
                                    'message': str(item_error),
                                    'traceback': traceback.format_exc(),
                                    'failed_payload': item,
                                }
                            ],
                        })
                return jsonify(results)

            result = _handle_graphql_request_item(payload)
            return jsonify(result)

        except Exception as e:
            return jsonify({
                'data': None,
                'errors': [
                    {
                        'message': str(e),
                        'traceback': traceback.format_exc(),
                        'request_body': request.get_data(as_text=True),
                    }
                ],
            }), 500
