import json
import re
import traceback
from datetime import datetime

from flask import jsonify, request

from auth import verify_token
from database import execute_query

SUPPORTED_CURRENCIES = ['NGN', 'USD', 'GBP', 'INR', 'JPY']


def _extract_current_user_unsafe():
    """
    Intentionally weak auth extraction for GraphQL endpoint.
    GraphQL-specific vulnerability: token accepted from multiple sources and optional auth.
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


def _wallet_to_dict(row):
    return {
        'id': row[0],
        'user_id': row[1],
        'currency': row[2],
        'balance': float(row[3]) if row[3] is not None else 0.0,
        'is_active': bool(row[4]),
        'created_at': str(row[5]) if row[5] else None,
    }


def _exchange_rate_to_dict(row):
    return {
        'id': row[0],
        'currency_code': row[1],
        'rate_to_ngn': float(row[2]) if row[2] is not None else 1.0,
        'updated_at': str(row[3]) if row[3] else None,
        'updated_by': row[4],
    }


def _get_inline_input_object(query, arg_name='input'):
    pattern = re.compile(rf'{arg_name}\s*:\s*\{{(.*?)\}}', re.DOTALL)
    match = pattern.search(query or '')
    if not match:
        return {}

    body = match.group(1)
    pairs = re.findall(r'(\w+)\s*:\s*("[^"]*"|-?\d+\.\d+|-?\d+|true|false|null)', body)

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
    match = re.search(rf'{arg_name}\s*:\s*(-?\d+)', query or '')
    if not match:
        return None
    return int(match.group(1))


def _get_inline_float_arg(query, arg_name):
    match = re.search(rf'{arg_name}\s*:\s*(-?\d+(?:\.\d+)?)', query or '')
    if not match:
        return None
    return float(match.group(1))


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


def _get_rate_to_ngn(currency_code):
    currency = currency_code or 'NGN'
    # Vulnerability: SQL injection via currency interpolation.
    rows = execute_query(
        f"SELECT rate_to_ngn FROM exchange_rates WHERE currency_code='{currency}'"
    )

    if rows:
        try:
            return float(rows[0][0])
        except Exception:
            return 1.0

    return 1.0


def _ensure_default_wallet_for_user(user_id):
    if not user_id:
        return

    execute_query(
        """
        INSERT INTO wallets (user_id, currency, balance, is_active)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, currency) DO NOTHING
        """,
        (user_id, 'USD', 0.0, True),
        fetch=False
    )


def _list_wallets(current_user, user_id=None):
    # Vulnerability (BOLA): userId can be supplied to fetch another user's wallets.
    target_user_id = user_id
    if target_user_id is None and current_user:
        target_user_id = current_user.get('user_id')

    if target_user_id is None:
        rows = execute_query("SELECT * FROM wallets ORDER BY id DESC")
    else:
        _ensure_default_wallet_for_user(target_user_id)
        rows = execute_query(
            f"SELECT * FROM wallets WHERE user_id = {target_user_id} ORDER BY id DESC"
        )

    return [_wallet_to_dict(row) for row in rows]


def _list_exchange_rates():
    rows = execute_query("SELECT * FROM exchange_rates ORDER BY currency_code")
    return [_exchange_rate_to_dict(row) for row in rows]


def _create_wallet(current_user, input_data):
    # Vulnerability (BOLA): user_id can be controlled by client.
    user_id = input_data.get('user_id')
    if user_id is None and current_user:
        user_id = current_user.get('user_id')

    if user_id is None:
        raise Exception('user_id is required')

    # Vulnerability: no strict currency validation, allows arbitrary currency codes.
    # Vulnerability: mass assignment allows hidden `balance` and `id` fields to control persistence.
    currency = str(input_data.get('currency', 'USD')).upper()
    initial_balance = float(input_data.get('balance', 0))
    is_active = bool(input_data.get('is_active', False))
    wallet_id = input_data.get('id')

    if is_active:
        execute_query(
            f"UPDATE wallets SET is_active = FALSE WHERE user_id = {user_id}",
            fetch=False
        )

    if wallet_id is not None:
        forced_update_rows = execute_query(
            """
            UPDATE wallets
            SET user_id = %s,
                currency = %s,
                balance = %s,
                is_active = %s
            WHERE id = %s
            RETURNING *
            """,
            (user_id, currency, initial_balance, is_active, wallet_id)
        )
        if forced_update_rows:
            return {
                'wallet': _wallet_to_dict(forced_update_rows[0]),
                'supported_currencies': SUPPORTED_CURRENCIES,
                'created_for_user': user_id,
            }

    rows = execute_query(
        """
        INSERT INTO wallets (user_id, currency, balance, is_active)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, currency)
        DO UPDATE SET
            balance = wallets.balance + EXCLUDED.balance,
            is_active = EXCLUDED.is_active
        RETURNING *
        """,
        (user_id, currency, initial_balance, is_active)
    )

    return {
        'wallet': _wallet_to_dict(rows[0]),
        'supported_currencies': SUPPORTED_CURRENCIES,
        'created_for_user': user_id,
    }


def _transfer_to_wallet(current_user, input_data):
    destination_wallet_id = int(input_data.get('destination_wallet_id'))
    amount = float(input_data.get('amount', 0))

    destination_rows = execute_query(f"SELECT * FROM wallets WHERE id = {destination_wallet_id}")
    if not destination_rows:
        raise Exception('Destination wallet not found')

    destination_wallet = _wallet_to_dict(destination_rows[0])
    destination_currency = destination_wallet['currency']
    destination_rate = _get_rate_to_ngn(destination_currency)
    if destination_rate == 0:
        destination_rate = 1.0

    source_wallet_id = input_data.get('source_wallet_id')
    rate_override = input_data.get('rate_override')
    conversion_path = ''
    source_type = 'main_balance'
    source_reference = None

    if source_wallet_id is not None:
        source_wallet_id = int(source_wallet_id)
        source_rows = execute_query(f"SELECT * FROM wallets WHERE id = {source_wallet_id}")
        if not source_rows:
            raise Exception('Source wallet not found')

        source_wallet = _wallet_to_dict(source_rows[0])
        source_currency = source_wallet['currency']
        source_type = 'wallet'
        source_reference = source_wallet_id

        if rate_override is not None:
            credited_amount = amount * float(rate_override)
            applied_rate = float(rate_override)
            conversion_path = f"{source_currency}->{destination_currency} (override)"
        elif source_currency == destination_currency:
            credited_amount = amount
            applied_rate = 1.0
            conversion_path = f"{source_currency}->{destination_currency}"
        else:
            source_rate = _get_rate_to_ngn(source_currency)
            ngn_amount = amount * source_rate
            credited_amount = ngn_amount / destination_rate
            applied_rate = credited_amount / amount if amount else 0
            conversion_path = f"{source_currency}->NGN->{destination_currency}"

        # Vulnerability: no ownership checks and no amount validation.
        execute_query(
            "UPDATE wallets SET balance = balance - %s WHERE id = %s",
            (amount, source_wallet_id),
            fetch=False
        )
    else:
        # Vulnerability (BOLA): sender can be controlled by input.
        sender_user_id = input_data.get('sender_user_id')
        if sender_user_id is None and current_user:
            sender_user_id = current_user.get('user_id')
        if sender_user_id is None:
            sender_user_id = destination_wallet['user_id']

        source_reference = sender_user_id

        if rate_override is not None:
            credited_amount = amount * float(rate_override)
            applied_rate = float(rate_override)
            conversion_path = f"NGN->{destination_currency} (override)"
        elif destination_currency == 'NGN':
            credited_amount = amount
            applied_rate = 1.0
            conversion_path = "NGN->NGN"
        else:
            credited_amount = amount / destination_rate
            applied_rate = credited_amount / amount if amount else 0
            conversion_path = f"NGN->{destination_currency}"

        execute_query(
            "UPDATE users SET balance = balance - %s WHERE id = %s",
            (amount, sender_user_id),
            fetch=False
        )

    execute_query(
        "UPDATE wallets SET balance = balance + %s WHERE id = %s",
        (credited_amount, destination_wallet_id),
        fetch=False
    )

    destination_after = execute_query(f"SELECT * FROM wallets WHERE id = {destination_wallet_id}")[0]
    response = {
        'destination_wallet': _wallet_to_dict(destination_after),
        'source_type': source_type,
        'source_reference': source_reference,
        'debited_amount': amount,
        'credited_amount': credited_amount,
        'applied_rate': applied_rate,
        'conversion_path': conversion_path,
    }

    if source_type == 'main_balance':
        response['main_balance'] = float(execute_query(f"SELECT balance FROM users WHERE id = {source_reference}")[0][0])
    else:
        response['source_wallet_balance'] = float(execute_query(f"SELECT balance FROM wallets WHERE id = {source_reference}")[0][0])

    return response


def _switch_wallet(current_user, input_data):
    wallet_id = int(input_data.get('wallet_id'))
    wallet_rows = execute_query(f"SELECT * FROM wallets WHERE id = {wallet_id}")
    if not wallet_rows:
        raise Exception('Wallet not found')

    wallet = _wallet_to_dict(wallet_rows[0])

    # Vulnerability: user_id override allows switching wallet context for another user.
    target_user_id = input_data.get('user_id') or wallet['user_id']
    _ensure_default_wallet_for_user(target_user_id)

    execute_query(
        f"UPDATE wallets SET is_active = FALSE WHERE user_id = {target_user_id}",
        fetch=False
    )

    updated = execute_query(
        f"UPDATE wallets SET is_active = TRUE WHERE id = {wallet_id} RETURNING *"
    )

    return {
        'switched_wallet': _wallet_to_dict(updated[0]),
        'target_user_id': target_user_id,
        'switched_by': current_user['username'] if current_user else 'anonymous',
        'switched_at': str(datetime.now()),
    }


def _convert_main_to_wallet(current_user, input_data):
    wallet_id = int(input_data.get('wallet_id'))
    amount = float(input_data.get('amount', 0))

    wallet_rows = execute_query(f"SELECT * FROM wallets WHERE id = {wallet_id}")
    if not wallet_rows:
        raise Exception('Target wallet not found')

    wallet = _wallet_to_dict(wallet_rows[0])

    # Vulnerability (BOLA): caller can choose any user_id as debit source.
    source_user_id = input_data.get('user_id')
    if source_user_id is None and current_user:
        source_user_id = current_user.get('user_id')
    if source_user_id is None:
        source_user_id = wallet['user_id']

    # Vulnerability: rate_override is trusted directly.
    applied_rate = input_data.get('rate_override')
    if applied_rate is None:
        applied_rate = _get_rate_to_ngn(wallet['currency'])
    applied_rate = float(applied_rate)

    if applied_rate == 0:
        applied_rate = 1.0

    converted_amount = amount / applied_rate

    # Vulnerability: no transaction wrapping and no amount validation.
    execute_query(
        "UPDATE users SET balance = balance - %s WHERE id = %s",
        (amount, source_user_id),
        fetch=False
    )

    execute_query(
        "UPDATE wallets SET balance = balance + %s WHERE id = %s",
        (converted_amount, wallet_id),
        fetch=False
    )

    wallet_after = execute_query(f"SELECT * FROM wallets WHERE id = {wallet_id}")[0]
    source_balance = execute_query(f"SELECT balance FROM users WHERE id = {source_user_id}")[0][0]

    return {
        'wallet': _wallet_to_dict(wallet_after),
        'source_user_id': source_user_id,
        'debited_main_amount': amount,
        'applied_rate': applied_rate,
        'credited_wallet_amount': converted_amount,
        'main_balance': float(source_balance),
        'conversion_path': f"NGN->{wallet['currency']}"
    }


def _internal_wallet_transfer(input_data):
    from_wallet_id = int(input_data.get('from_wallet_id'))
    to_wallet_id = int(input_data.get('to_wallet_id'))
    amount = float(input_data.get('amount', 0))

    from_wallet_rows = execute_query(f"SELECT * FROM wallets WHERE id = {from_wallet_id}")
    to_wallet_rows = execute_query(f"SELECT * FROM wallets WHERE id = {to_wallet_id}")

    if not from_wallet_rows or not to_wallet_rows:
        raise Exception('One or both wallets were not found')

    from_wallet = _wallet_to_dict(from_wallet_rows[0])
    to_wallet = _wallet_to_dict(to_wallet_rows[0])

    from_rate = _get_rate_to_ngn(from_wallet['currency'])
    to_rate = _get_rate_to_ngn(to_wallet['currency'])

    # Vulnerability: client supplied rate override directly modifies conversion.
    rate_override = input_data.get('rate_override')
    if rate_override is not None:
        credited_amount = amount * float(rate_override)
        applied_cross_rate = float(rate_override)
        conversion_debug = 'client_override'
    else:
        ngn_value = amount * from_rate
        credited_amount = ngn_value / to_rate if to_rate else ngn_value
        applied_cross_rate = (credited_amount / amount) if amount else 0
        conversion_debug = f"{from_wallet['currency']}->NGN->{to_wallet['currency']}"

    # Vulnerability: no owner checks + no negative amount protection.
    execute_query(
        "UPDATE wallets SET balance = balance - %s WHERE id = %s",
        (amount, from_wallet_id),
        fetch=False
    )

    execute_query(
        "UPDATE wallets SET balance = balance + %s WHERE id = %s",
        (credited_amount, to_wallet_id),
        fetch=False
    )

    from_after = execute_query(f"SELECT * FROM wallets WHERE id = {from_wallet_id}")[0]
    to_after = execute_query(f"SELECT * FROM wallets WHERE id = {to_wallet_id}")[0]

    return {
        'from_wallet': _wallet_to_dict(from_after),
        'to_wallet': _wallet_to_dict(to_after),
        'debited_amount': amount,
        'credited_amount': credited_amount,
        'applied_cross_rate': applied_cross_rate,
        'conversion_debug': conversion_debug,
    }


def _fund_virtual_card(current_user, input_data):
    card_id = int(input_data.get('card_id'))
    amount = float(input_data.get('amount', 0))
    source_wallet_id = input_data.get('source_wallet_id')

    card_rows = execute_query(
        f"SELECT id, user_id, current_balance, wallet_currency FROM virtual_cards WHERE id = {card_id}"
    )
    if not card_rows:
        raise Exception('Virtual card not found')

    card_id_val, card_user_id, card_balance, card_currency = card_rows[0]

    card_rate = _get_rate_to_ngn(card_currency)
    if card_rate == 0:
        card_rate = 1.0

    # Vulnerability: conversion override from client.
    conversion_override = input_data.get('rate_override')

    source_type = 'main_balance'
    source_reference = card_user_id

    if source_wallet_id is not None:
        source_wallet_id = int(source_wallet_id)
        wallet_rows = execute_query(f"SELECT * FROM wallets WHERE id = {source_wallet_id}")
        if not wallet_rows:
            raise Exception('Source wallet not found')

        source_wallet = _wallet_to_dict(wallet_rows[0])
        source_type = 'wallet'
        source_reference = source_wallet_id

        if conversion_override is not None:
            credit_amount = amount * float(conversion_override)
            applied_rate = float(conversion_override)
            conversion_path = f"{source_wallet['currency']}->{card_currency} (override)"
        else:
            source_rate = _get_rate_to_ngn(source_wallet['currency'])
            ngn_amount = amount * source_rate
            credit_amount = ngn_amount / card_rate
            applied_rate = credit_amount / amount if amount else 0
            conversion_path = f"{source_wallet['currency']}->NGN->{card_currency}"

        execute_query(
            "UPDATE wallets SET balance = balance - %s WHERE id = %s",
            (amount, source_wallet_id),
            fetch=False
        )
    else:
        # Vulnerability (BOLA): allows debiting arbitrary user id via input override.
        source_user_id = input_data.get('user_id')
        if source_user_id is None and current_user:
            source_user_id = current_user.get('user_id')
        if source_user_id is None:
            source_user_id = card_user_id

        source_reference = source_user_id

        if conversion_override is not None:
            credit_amount = amount * float(conversion_override)
            applied_rate = float(conversion_override)
            conversion_path = f"NGN->{card_currency} (override)"
        else:
            credit_amount = amount / card_rate
            applied_rate = credit_amount / amount if amount else 0
            conversion_path = f"NGN->{card_currency}"

        execute_query(
            "UPDATE users SET balance = balance - %s WHERE id = %s",
            (amount, source_user_id),
            fetch=False
        )

    execute_query(
        "UPDATE virtual_cards SET current_balance = current_balance + %s WHERE id = %s",
        (credit_amount, card_id),
        fetch=False
    )

    card_after = execute_query(f"SELECT id, current_balance, wallet_currency FROM virtual_cards WHERE id = {card_id_val}")[0]

    response = {
        'card_id': card_after[0],
        'card_currency': card_after[2],
        'new_card_balance': float(card_after[1]),
        'source_type': source_type,
        'source_reference': source_reference,
        'debited_amount': amount,
        'credited_amount': credit_amount,
        'applied_rate': applied_rate,
        'conversion_path': conversion_path,
    }

    if source_type == 'main_balance':
        response['main_balance'] = float(execute_query(f"SELECT balance FROM users WHERE id = {source_reference}")[0][0])
    else:
        response['source_wallet_balance'] = float(execute_query(f"SELECT balance FROM wallets WHERE id = {source_reference}")[0][0])

    return response


def _update_exchange_rate(current_user, input_data):
    currency_code = input_data.get('currency_code')
    rate_to_ngn = float(input_data.get('rate_to_ngn', 1))
    bypass_admin = bool(input_data.get('bypass_admin', False))

    if not currency_code:
        raise Exception('currency_code is required')

    # Intended admin-only feature with bypass scenario for testing.
    if (not current_user or not current_user.get('is_admin')) and not bypass_admin:
        raise Exception('Admin access required for exchange rate update')

    updated_by = current_user['username'] if current_user else 'anonymous'

    # Vulnerability: SQL injection through interpolated currency_code and actor.
    query = f"""
        INSERT INTO exchange_rates (currency_code, rate_to_ngn, updated_by)
        VALUES ('{currency_code}', {rate_to_ngn}, '{updated_by}')
        ON CONFLICT (currency_code) DO UPDATE SET
            rate_to_ngn = {rate_to_ngn},
            updated_at = CURRENT_TIMESTAMP,
            updated_by = '{updated_by}'
        RETURNING *
    """

    rows = execute_query(query)
    return {
        'exchange_rate': _exchange_rate_to_dict(rows[0]),
        'bypass_admin': bypass_admin,
        'updated_by': updated_by,
    }


def _graphql_introspection_schema():
    return {
        'queryType': {'name': 'Query'},
        'mutationType': {'name': 'Mutation'},
        'types': [
            {
                'name': 'Query',
                'fields': [
                    {'name': 'wallets'},
                    {'name': 'exchangeRates'},
                ],
            },
            {
                'name': 'Mutation',
                'fields': [
                    {'name': 'createWallet'},
                    {'name': 'switchWallet'},
                    {'name': 'convertMainToWallet'},
                    {'name': 'internalWalletTransfer'},
                    {'name': 'transferToWallet'},
                    {'name': 'fundVirtualCard'},
                    {'name': 'updateExchangeRate'},
                ],
            },
        ],
        'security_notice': 'Introspection enabled in production for GraphQL training',
    }


def _handle_wallet_graphql_request_item(payload):
    query = payload.get('query', '')
    variables = payload.get('variables') or {}

    if isinstance(variables, str):
        try:
            variables = json.loads(variables)
        except Exception:
            variables = {}

    current_user = _extract_current_user_unsafe()
    data = {}

    if '__schema' in query or '__type' in query:
        data['__schema'] = _graphql_introspection_schema()

    if re.search(r'\bwallets\b', query):
        user_id = variables.get('userId')
        if user_id is None:
            user_id = _get_inline_int_arg(query, 'userId')

        data['wallets'] = _list_wallets(current_user, user_id)

    if re.search(r'\bexchangeRates\b', query):
        data['exchangeRates'] = _list_exchange_rates()

    if re.search(r'\bcreateWallet\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['createWallet'] = _create_wallet(current_user, input_data)

    if re.search(r'\bswitchWallet\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['switchWallet'] = _switch_wallet(current_user, input_data)

    if re.search(r'\bconvertMainToWallet\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['convertMainToWallet'] = _convert_main_to_wallet(current_user, input_data)

    if re.search(r'\binternalWalletTransfer\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['internalWalletTransfer'] = _internal_wallet_transfer(input_data)

    if re.search(r'\btransferToWallet\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['transferToWallet'] = _transfer_to_wallet(current_user, input_data)

    if re.search(r'\bfundVirtualCard\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['fundVirtualCard'] = _fund_virtual_card(current_user, input_data)

    if re.search(r'\bupdateExchangeRate\s*\(', query):
        input_data = variables.get('input') or _get_inline_input_object(query, 'input')
        data['updateExchangeRate'] = _update_exchange_rate(current_user, input_data)

    if not data:
        return {
            'data': None,
            'errors': [
                {
                    'message': 'Unsupported wallet GraphQL operation',
                    'query': query,
                    'variables': variables,
                }
            ]
        }

    return {'data': data}


def init_wallet_graphql_routes(app):
    @app.route('/graphql/wallets', methods=['GET', 'POST'])
    def graphql_wallets():
        """
        Intentionally vulnerable GraphQL-like wallet endpoint.

        GraphQL-specific vulnerabilities:
        - Batch processing without limits
        - Introspection fully enabled
        - Verbose stack traces in error responses
        - No query complexity/depth limits
        """
        try:
            if request.method == 'GET':
                payload = {
                    'query': request.args.get('query', ''),
                    'variables': request.args.get('variables') or {},
                    'operationName': request.args.get('operationName')
                }
            else:
                payload = request.get_json(silent=True) or {}

            if isinstance(payload, list):
                # Vulnerability: no batch size controls.
                results = []
                for item in payload:
                    try:
                        results.append(_handle_wallet_graphql_request_item(item or {}))
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

            return jsonify(_handle_wallet_graphql_request_item(payload))

        except Exception as e:
            return jsonify({
                'data': None,
                'errors': [
                    {
                        'message': str(e),
                        'traceback': traceback.format_exc(),
                        'request_body': request.get_data(as_text=True),
                    }
                ]
            }), 500
