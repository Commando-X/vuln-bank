# GraphQL Queries

This folder contains example GraphQL operations for the transaction analytics endpoint.

- Endpoint: `POST /graphql`
- Auth: `Authorization: Bearer <jwt>`
- Introspection: disabled

Standard users can query their own account summary. Admins can query global metrics or target a specific account with `accountNumber`.
