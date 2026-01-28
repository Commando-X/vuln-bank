# SQL Injection Vulnerabilities
``
## Prerequisites

## Demonstrations

### login()
Grants attacker full access to a user account.
#### Exploit
1. Go to login page and type in a SQL command as the username.
2. Type in whatever as the password.
3. If the attacker knows a specific username, they can access
that account without their password.
4. If the attacker does not know a username, they are granted
access to a random account.
##### via UI
5. To access a specific user account (say "admin" in this case),
type in `admin' OR '1'='1` into the username field.
6. Type in whatever for the password.

    ![alt text](./screenshots/sql_login_vuln.png)
7. This will bring the attacker to the dashboard of that user.
8. If the username is not known, the attacker can type in
`' OR '1'='1' --` into the username field.
9. Type in whatever for the password.

    ![alt text](./screenshots/sql_login_vuln_random.png)
##### via CLI
10. Open the browser console/terminal.
11. Issue the following fetch request as a command
to gain access to the "admin" account:
`fetch('/login', { method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({username: "admin' OR '1'='1"
})}).then(r => r.json()).then(console.log)`
12. Observe outcome.

    ![alt text](./screenshots/sql_login_vuln_cli.png)
#### Mitigate
Return to root URL (Vulnerable Bank homepage) and click Toggle Mitigation button. Repeat attack (either sequence of steps above) and observe outcome:
13. IU:

![alt text](./screenshots/sql_login_harden.png)
14. CLI:

![alt text](./screenshots/sql_login_harden_cli.png)
### create_admin()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

### forgot_password()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  api_v1_forgot_password()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  api_v2_forgot_password()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  api_v3_forgot_password()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  api_transactions()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  create_virtual_card()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  get_billers_by_category()

#### Exploit

##### via URL

##### via CLI

#### Mitigate

###  get_payment_history()

#### Exploit

##### via URL

##### via CLI

#### Mitigate
