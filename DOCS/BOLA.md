# Broken Object-Level Authorization
BOLA is the absence or dysfunction of identity verification for read/write permissions through an API endpoint. Its presence effectively grants anyone access to the unprotected objects in question.

## Prerequisites
Browser access to functioning web app and two registered user accounts, at least one of which has:
- One transaction of any amount.
- One virtual card of any limit with a balance >= $0.

## Demonstrations
This vulnerability is present in six different functions within app.py. Steps for exploitation and verification of hardening are as follows.

### check_balance_hardened()
#### Exploit
Log in as any user and note their <account_number> (visible directly below their account balance). From here, this may be exploited in one of two ways:
##### As User (Internal)
1. Log out, then log in as any other user.
2. Append /check_balance/<account_number> to the root URL. If the root is localhost:5000, the full URL should read localhost:5000/check_balance/<account_number>
3. Press enter, then observe outcome in browser window.
##### As Interloper (External)
1. Log in as any user and open the browser console/terminal.
2. Issue the following fetch request as a command, replacing `<ACCOUNT_NUMBER>` with the previously noted account number:
    `const attackerToken = localStorage.getItem('jwt_token');
    fetch('/check_balance/' + '<ACCOUNT_NUMBER>', {
    headers: { Authorization: 'Bearer ' + attackerToken }
    }).then(r => r.json()).then(console.log);`

3. Observe outcome.
![alt text](./screenshots/image.png)

#### Mitigate
Return to root URL (Vulnerable Bank homepage) and click Toggle Mitigation button. Repeat either attack (steps above) and observe outcome:
![alt text](./screenshots/image-1.png)

### get_transaction_history()
#### Exploit
#### Mitigate

### toggle_card_freeze()
#### Exploit
#### Mitigate

### get_card_transactions()
#### Exploit
#### Mitigate

### update_card_limit()
#### Exploit
#### Mitigate

### create_bill_payment()
#### Exploit
#### Mitigate