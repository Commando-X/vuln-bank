import graphene
from graphql import GraphQLError

from database import execute_query


class TransactionRecordType(graphene.ObjectType):
    id = graphene.Int()
    from_account = graphene.String()
    from_username = graphene.String()
    to_account = graphene.String()
    to_username = graphene.String()
    amount = graphene.Float()
    timestamp = graphene.String()
    transaction_type = graphene.String()
    description = graphene.String()


class TransactionTypeAggregate(graphene.ObjectType):
    transaction_type = graphene.String()
    count = graphene.Int()
    total_amount = graphene.Float()


class TransactionSummaryType(graphene.ObjectType):
    scope = graphene.String()
    account_number = graphene.String()
    total_transactions = graphene.Int()
    total_volume = graphene.Float()
    inflow_total = graphene.Float()
    outflow_total = graphene.Float()
    net_flow = graphene.Float()
    largest_transaction = graphene.Float()
    by_type = graphene.List(TransactionTypeAggregate)
    recent_transactions = graphene.List(TransactionRecordType)


def _load_user_actor(user_id):
    rows = execute_query(
        "SELECT id, username, account_number, is_admin FROM users WHERE id = %s",
        (user_id,)
    )

    if not rows:
        raise GraphQLError('Authenticated user could not be loaded.')

    actor = rows[0]
    return {
        'id': actor[0],
        'username': actor[1],
        'account_number': actor[2],
        'is_admin': bool(actor[3])
    }


def _resolve_scope(actor, requested_account_number):
    if requested_account_number:
        if actor['is_admin'] or requested_account_number == actor['account_number']:
            return requested_account_number, 'account'
        raise GraphQLError('You can only query your own transaction summary.')

    if actor['is_admin']:
        return None, 'global'

    return actor['account_number'], 'account'


def _load_transactions(scoped_account_number):
    query = """
        SELECT
            id,
            from_account,
            to_account,
            amount,
            timestamp,
            transaction_type,
            description
        FROM transactions
    """
    params = None

    if scoped_account_number:
        query += " WHERE from_account = %s OR to_account = %s"
        params = (scoped_account_number, scoped_account_number)

    query += " ORDER BY timestamp DESC"
    return execute_query(query, params)


def _load_account_name_map():
    users = execute_query("SELECT account_number, username FROM users")
    return {
        user[0]: user[1]
        for user in users
    }


def _build_transaction_summary(rows, scoped_account_number, scope, limit):
    safe_limit = min(max(limit or 5, 1), 15)
    account_name_map = _load_account_name_map()
    inflow_total = 0.0
    outflow_total = 0.0
    total_volume = 0.0
    largest_transaction = 0.0
    by_type = {}

    for row in rows:
        amount = float(row[3])
        absolute_amount = abs(amount)
        transaction_type = row[5] or 'unknown'

        total_volume += absolute_amount
        largest_transaction = max(largest_transaction, absolute_amount)

        aggregate = by_type.setdefault(transaction_type, {
            'transaction_type': transaction_type,
            'count': 0,
            'total_amount': 0.0
        })
        aggregate['count'] += 1
        aggregate['total_amount'] += absolute_amount

        if scoped_account_number:
            if row[2] == scoped_account_number:
                inflow_total += absolute_amount
            if row[1] == scoped_account_number:
                outflow_total += absolute_amount
        else:
            inflow_total += absolute_amount
            outflow_total += absolute_amount

    recent_transactions = []
    for row in rows[:safe_limit]:
        timestamp = row[4].isoformat(sep=' ') if hasattr(row[4], 'isoformat') else str(row[4])
        recent_transactions.append({
            'id': row[0],
            'from_account': row[1],
            'from_username': account_name_map.get(row[1]),
            'to_account': row[2],
            'to_username': account_name_map.get(row[2]),
            'amount': float(row[3]),
            'timestamp': timestamp,
            'transaction_type': row[5],
            'description': row[6]
        })

    ordered_breakdown = []
    for aggregate in sorted(by_type.values(), key=lambda item: item['total_amount'], reverse=True):
        ordered_breakdown.append({
            'transaction_type': aggregate['transaction_type'],
            'count': aggregate['count'],
            'total_amount': round(aggregate['total_amount'], 2)
        })

    return {
        'scope': scope,
        'account_number': scoped_account_number or 'ALL_ACCOUNTS',
        'total_transactions': len(rows),
        'total_volume': round(total_volume, 2),
        'inflow_total': round(inflow_total, 2),
        'outflow_total': round(outflow_total, 2),
        'net_flow': round(inflow_total - outflow_total, 2),
        'largest_transaction': round(largest_transaction, 2),
        'by_type': ordered_breakdown,
        'recent_transactions': recent_transactions
    }


class Query(graphene.ObjectType):
    transaction_summary = graphene.Field(
        TransactionSummaryType,
        account_number=graphene.String(),
        limit=graphene.Int(default_value=5)
    )

    def resolve_transaction_summary(self, info, account_number=None, limit=5):
        current_user = (info.context or {}).get('current_user')
        if not current_user:
            raise GraphQLError('Authentication required.')

        actor = _load_user_actor(current_user['user_id'])
        scoped_account_number, scope = _resolve_scope(actor, account_number)
        rows = _load_transactions(scoped_account_number)
        return _build_transaction_summary(rows, scoped_account_number, scope, limit)


transaction_graphql_schema = graphene.Schema(query=Query)
