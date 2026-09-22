const baseUrl = process.env.VULNBANK_TEST_URL || 'http://127.0.0.1:15000';
const chromeDebugUrl = process.env.CHROME_DEBUG_URL || 'http://127.0.0.1:19223';
const expiryWaitMs = Number(process.env.XSS_E2E_WAIT_MS || 70000);

const suffix = Date.now().toString();
const receiverUsername = `xss-cleaner-receiver-${suffix}`;
const adminUsername = `xss-cleaner-admin-${suffix}`;
const rejectedUsername = '<img src=x onerror=alert(1)>';
const xssBio = '<img src=x onerror=document.documentElement.dataset.vbBio=1>';
const xssDescription = '<img src=x onerror=document.documentElement.dataset.vbTransaction=1>';
const password = `cleaner-test-${suffix}`;

const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

async function api(path, options = {}) {
    const response = await fetch(baseUrl + path, options);
    const body = await response.json();
    if (!response.ok) {
        throw new Error(`${path} failed (${response.status}): ${JSON.stringify(body)}`);
    }
    return body;
}

async function post(path, body, token) {
    const headers = {'Content-Type': 'application/json'};
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return api(path, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });
}

async function postExpectingRejection(path, body) {
    const response = await fetch(baseUrl + path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    });
    const responseBody = await response.json();
    return {
        rejected: response.status === 400,
        message: responseBody.message,
    };
}

async function connectToChrome() {
    const targets = await (await fetch(`${chromeDebugUrl}/json/list`)).json();
    const pageTarget = targets.find(target => target.type === 'page');
    if (!pageTarget) {
        throw new Error('No Chrome page target found');
    }

    const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
        socket.addEventListener('open', resolve, {once: true});
        socket.addEventListener('error', reject, {once: true});
    });

    let nextId = 1;
    const pending = new Map();
    socket.addEventListener('message', event => {
        const message = JSON.parse(event.data);
        if (!message.id || !pending.has(message.id)) {
            return;
        }
        const {resolve, reject} = pending.get(message.id);
        pending.delete(message.id);
        if (message.error) {
            reject(new Error(JSON.stringify(message.error)));
        } else {
            resolve(message.result);
        }
    });

    function command(method, params = {}) {
        return new Promise((resolve, reject) => {
            const id = nextId++;
            pending.set(id, {resolve, reject});
            socket.send(JSON.stringify({id, method, params}));
        });
    }

    return {socket, command};
}

async function evaluate(command, expression) {
    const response = await command('Runtime.evaluate', {
        expression,
        returnByValue: true,
        awaitPromise: true,
    });
    if (response.exceptionDetails) {
        throw new Error(`Browser evaluation failed: ${JSON.stringify(response.exceptionDetails)}`);
    }
    return response.result.value;
}

async function navigate(command, url, waitMs = 1200) {
    await command('Page.navigate', {url});
    await delay(waitMs);
}

async function readBrowserState(command, token, userId) {
    await navigate(
        command,
        `${baseUrl}/sup3r_s3cr3t_admin?token=${encodeURIComponent(token)}`,
    );
    await evaluate(command, `openUserModal(${userId})`);
    await delay(900);
    const bioExecuted = await evaluate(
        command,
        "document.documentElement.dataset.vbBio === '1'",
    );

    await navigate(
        command,
        `${baseUrl}/dashboard?token=${encodeURIComponent(token)}`,
        1800,
    );
    return {
        bioExecuted,
        transactionExecuted: await evaluate(
            command,
            "document.documentElement.dataset.vbTransaction === '1'",
        ),
    };
}

function requireState(state, expected, label) {
    for (const [key, value] of Object.entries(state)) {
        if (value !== expected) {
            throw new Error(`${label}: expected ${key}=${expected}, received ${value}`);
        }
    }
}

async function main() {
    const usernameValidation = await postExpectingRejection('/register', {
        username: rejectedUsername,
        password,
    });
    if (!usernameValidation.rejected) {
        throw new Error('Special-character username was not rejected');
    }
    console.log(`username_validation=${JSON.stringify(usernameValidation)}`);

    const receiver = await post('/register', {
        username: receiverUsername,
        password,
    });
    const attacker = await post('/register', {
        username: adminUsername,
        password,
        is_admin: true,
    });
    const login = await post('/login', {username: adminUsername, password});
    const token = login.token;
    const userId = attacker.debug_data.user_id;
    const accountNumber = attacker.debug_data.account_number;
    const receiverAccount = receiver.debug_data.account_number;

    await post('/update_bio', {bio: xssBio}, token);
    await post('/transfer', {
        to_account: receiverAccount,
        amount: 1,
        description: xssDescription,
    }, token);

    const {socket, command} = await connectToChrome();
    try {
        await command('Page.enable');
        await command('Runtime.enable');
        await navigate(command, `${baseUrl}/login`, 600);
        await evaluate(
            command,
            `localStorage.setItem('jwt_token', ${JSON.stringify(token)})`,
        );

        const beforeExpiry = await readBrowserState(command, token, userId);
        console.log(`before_expiry=${JSON.stringify(beforeExpiry)}`);
        requireState(beforeExpiry, true, 'Payload execution before expiry');

        await delay(expiryWaitMs);

        const afterExpiry = await readBrowserState(command, token, userId);
        const userAfterExpiry = await api(`/api/v3/user/${userId}`, {
            headers: {Authorization: `Bearer ${token}`},
        });
        const transactionsAfterExpiry = await api(`/transactions/${accountNumber}`);
        const storedValuesNeutralized = {
            usernameUnchanged: userAfterExpiry.user.username === adminUsername,
            bioCleared: userAfterExpiry.user.bio === null,
            descriptionCleared: transactionsAfterExpiry.transactions.some(
                transaction => transaction.description === null,
            ),
        };

        console.log(`after_expiry=${JSON.stringify(afterExpiry)}`);
        console.log(`stored_values=${JSON.stringify(storedValuesNeutralized)}`);
        requireState(afterExpiry, false, 'Payload execution after expiry');
        requireState(storedValuesNeutralized, true, 'Stored-value cleanup');
    } finally {
        socket.close();
    }
}

main().catch(error => {
    console.error(error.stack || error);
    process.exit(1);
});
