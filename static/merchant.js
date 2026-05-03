function merchantStoreCredentials(data) {
    if (data.token) {
        localStorage.setItem('merchant_jwt_token', data.token);
    }
    if (data.api_key) {
        localStorage.setItem('merchant_api_key', data.api_key);
    }
    if (data.merchant) {
        localStorage.setItem('merchant_profile', JSON.stringify(data.merchant));
    }
}

function merchantGetProfile() {
    try {
        return JSON.parse(localStorage.getItem('merchant_profile') || '{}');
    } catch (error) {
        return {};
    }
}

function merchantAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const apiKey = localStorage.getItem('merchant_api_key');
    const token = localStorage.getItem('merchant_jwt_token');

    if (apiKey) {
        headers['X-Merchant-Api-Key'] = apiKey;
    } else if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    return headers;
}

function showMerchantMessage(message, type = 'error') {
    const target = document.getElementById('merchantMessage') || document.getElementById('merchantAuthMessage');
    if (!target) return;

    target.className = type === 'success' ? 'merchant-inline-success' : 'merchant-inline-error';
    target.textContent = message;
}

function clearMerchantMessage() {
    const target = document.getElementById('merchantMessage') || document.getElementById('merchantAuthMessage');
    if (!target) return;

    target.className = '';
    target.textContent = '';
}

async function handleMerchantRegister(event) {
    event.preventDefault();
    clearMerchantMessage();

    const formData = new FormData(event.target);
    const payload = {};
    formData.forEach((value, key) => payload[key] = value);

    try {
        const response = await fetch('/api/v1/merchants/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            merchantStoreCredentials(data);
            window.location.href = '/merchant/dashboard';
            return;
        }

        showMerchantMessage(data.message || 'Merchant registration failed');
    } catch (error) {
        showMerchantMessage('Merchant registration failed');
    }
}

async function handleMerchantLogin(event) {
    event.preventDefault();
    clearMerchantMessage();

    const formData = new FormData(event.target);
    const payload = {};
    formData.forEach((value, key) => payload[key] = value);

    try {
        const response = await fetch('/api/v1/merchants/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            merchantStoreCredentials(data);
            window.location.href = '/merchant/dashboard';
            return;
        }

        showMerchantMessage(data.message || 'Merchant login failed');
    } catch (error) {
        showMerchantMessage('Merchant login failed');
    }
}

async function loadMerchantDashboard() {
    const token = localStorage.getItem('merchant_jwt_token');
    const apiKey = localStorage.getItem('merchant_api_key');
    if (!token && !apiKey) {
        window.location.href = '/merchant/login';
        return;
    }

    setMerchantDate();
    hydrateMerchantProfile();
    await refreshMerchantProfile();
    await fetchMerchantPayments();

    const chargeForm = document.getElementById('merchantChargeForm');
    if (chargeForm) {
        setupMerchantChargeFormatting();
        chargeForm.addEventListener('submit', handleMerchantCharge);
    }

    const hash = window.location.hash || '#overview';
    const activeLink = document.querySelector(`.nav-link[href='${hash}']`);
    if (activeLink) {
        setMerchantActiveLink(activeLink);
    }
}

function setMerchantDate() {
    const dateElement = document.getElementById('current-date');
    if (!dateElement) return;

    const today = new Date();
    dateElement.textContent = today.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function hydrateMerchantProfile() {
    const merchant = merchantGetProfile();
    const apiKey = localStorage.getItem('merchant_api_key') || merchant.api_key || '-';
    const token = localStorage.getItem('merchant_jwt_token') || '-';

    setText('merchantSidebarName', merchant.name || 'Merchant');
    setText('merchantGreeting', merchant.name ? `${merchant.name} Console` : 'Merchant Console');
    setText('merchantIdValue', merchant.id || '-');
    setText('merchantEmailValue', merchant.email || '-');
    setText('merchantApiKeyValue', apiKey);
    setText('merchantTokenValue', token);
    setText('authMethod', apiKey !== '-' ? 'API Key' : 'JWT');
    setText('integrationApiKeyHeader', `X-Merchant-Api-Key: ${apiKey}`);
    setText('integrationBearerHeader', `Authorization: Bearer ${token}`);
    setText('integrationFetchExample', buildIntegrationFetchExample(apiKey));
}

async function refreshMerchantProfile() {
    try {
        const response = await fetch('/api/v1/merchants/me', {
            headers: merchantAuthHeaders()
        });
        const data = await response.json();

        if (data.status === 'success') {
            localStorage.setItem('merchant_profile', JSON.stringify(data.merchant));
            hydrateMerchantProfile();
            return;
        }

        if (response.status === 401) {
            merchantLogout();
        }
    } catch (error) {
        showMerchantMessage('Could not refresh merchant profile');
    }
}

async function handleMerchantCharge(event) {
    event.preventDefault();
    clearMerchantMessage();

    const formData = new FormData(event.target);
    const payload = {};
    formData.forEach((value, key) => payload[key] = value);
    payload.card_number = normalizeDigits(payload.card_number, 16);
    payload.cvv = normalizeDigits(payload.cvv, 3);
    payload.expiry_date = formatExpiry(payload.expiry_date);

    document.getElementById('chargeCardNumber').value = payload.card_number;
    document.getElementById('chargeCvv').value = payload.cvv;
    document.getElementById('chargeExpiry').value = payload.expiry_date;

    if (payload.card_number.length !== 16) {
        showMerchantMessage('Card number must be 16 digits');
        return;
    }

    if (payload.cvv.length !== 3) {
        showMerchantMessage('CVV must be 3 digits');
        return;
    }

    if (!/^\d{2}\/\d{2}$/.test(payload.expiry_date)) {
        showMerchantMessage('Expiry must be in MM/YY format');
        return;
    }

    try {
        const response = await fetch('/api/v1/payments/charge', {
            method: 'POST',
            headers: merchantAuthHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await response.json();

        if (data.status === 'success') {
            showMerchantMessage(`Payment approved: ${data.payment.authorization_code}`, 'success');
            event.target.reset();
            document.getElementById('chargeCurrency').value = 'USD';
            await fetchMerchantPayments();
            return;
        }

        showMerchantMessage(data.failure_reason || data.message || 'Payment declined');
        await fetchMerchantPayments();
    } catch (error) {
        showMerchantMessage('Payment request failed');
    }
}

function setupMerchantChargeFormatting() {
    const cardNumber = document.getElementById('chargeCardNumber');
    const cvv = document.getElementById('chargeCvv');
    const expiry = document.getElementById('chargeExpiry');

    if (cardNumber) {
        cardNumber.addEventListener('input', () => {
            cardNumber.value = normalizeDigits(cardNumber.value, 16);
        });
        cardNumber.addEventListener('paste', event => {
            event.preventDefault();
            cardNumber.value = normalizeDigits(event.clipboardData.getData('text'), 16);
        });
    }

    if (cvv) {
        cvv.addEventListener('input', () => {
            cvv.value = normalizeDigits(cvv.value, 3);
        });
        cvv.addEventListener('paste', event => {
            event.preventDefault();
            cvv.value = normalizeDigits(event.clipboardData.getData('text'), 3);
        });
    }

    if (expiry) {
        expiry.addEventListener('input', () => {
            expiry.value = formatExpiry(expiry.value);
        });
        expiry.addEventListener('paste', event => {
            event.preventDefault();
            expiry.value = formatExpiry(event.clipboardData.getData('text'));
        });
    }
}

function normalizeDigits(value, maxLength) {
    return String(value || '').replace(/\D/g, '').slice(0, maxLength);
}

function formatExpiry(value) {
    const digits = normalizeDigits(value, 4);
    if (digits.length <= 2) {
        return digits;
    }
    return `${digits.slice(0, 2)}/${digits.slice(2)}`;
}

async function fetchMerchantPayments() {
    const tableBody = document.getElementById('merchantPaymentsBody');
    if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="7" class="empty-table">Loading payments...</td></tr>';
    }

    try {
        const response = await fetch('/api/v1/payments', {
            headers: merchantAuthHeaders()
        });
        const data = await response.json();

        if (data.status !== 'success') {
            if (response.status === 401) {
                merchantLogout();
                return;
            }
            showMerchantMessage(data.message || 'Could not load payments');
            renderMerchantPayments([]);
            return;
        }

        renderMerchantPayments(data.payments || []);
        updateMerchantStats(data.payments || [], data.debug_info);
    } catch (error) {
        showMerchantMessage('Could not load payments');
        renderMerchantPayments([]);
    }
}

function renderMerchantPayments(payments) {
    const tableBody = document.getElementById('merchantPaymentsBody');
    if (!tableBody) return;

    if (!payments.length) {
        tableBody.innerHTML = '<tr><td colspan="7" class="empty-table">No payments yet</td></tr>';
        return;
    }

    tableBody.innerHTML = payments.map(payment => {
        const status = payment.payment_status || payment.status || 'pending';
        return `
            <tr>
                <td class="mono">${escapeHtml(payment.id)}</td>
                <td>${escapeHtml(payment.merchant_name || '-')}</td>
                <td>${escapeHtml(payment.merchant_order_id || '-')}</td>
                <td class="mono">${escapeHtml(payment.card_number || '-')}</td>
                <td class="mono">${formatCurrency(payment.amount, payment.currency)}</td>
                <td><span class="payment-status ${escapeHtml(status)}">${escapeHtml(status)}</span></td>
                <td>${escapeHtml(payment.created_at || '-')}</td>
            </tr>
        `;
    }).join('');
}

function updateMerchantStats(payments, debugInfo) {
    const completed = payments.filter(payment => (payment.payment_status || payment.status) === 'completed');
    const failed = payments.filter(payment => (payment.payment_status || payment.status) === 'failed');
    const completedVolume = completed.reduce((total, payment) => total + Number(payment.amount || 0), 0);

    setText('completedVolume', formatCurrency(completedVolume, 'USD'));
    setText('paymentCount', payments.length);
    setText('failedCount', failed.length);

    if (debugInfo && debugInfo.looked_up_by_merchant && debugInfo.looked_up_by_merchant.auth_method) {
        setText('authMethod', debugInfo.looked_up_by_merchant.auth_method === 'api_key' ? 'API Key' : 'JWT');
    }
}

function merchantLogout() {
    localStorage.removeItem('merchant_jwt_token');
    localStorage.removeItem('merchant_api_key');
    localStorage.removeItem('merchant_profile');
    window.location.href = '/merchant/login';
}

function setMerchantActiveLink(element) {
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    element.classList.add('active');

    if (window.innerWidth <= 768) {
        document.getElementById('merchantSidebar')?.classList.remove('active');
        document.getElementById('sidebarOverlay')?.classList.remove('active');
    }
}

function toggleMerchantSidebar() {
    document.getElementById('merchantSidebar')?.classList.toggle('active');
    document.getElementById('sidebarOverlay')?.classList.toggle('active');
}

function toggleMerchantTheme() {
    const html = document.documentElement;
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('vb-theme', next);
}

function copyMerchantCredential(elementId) {
    const value = document.getElementById(elementId)?.textContent || '';
    if (!value || value === '-') return;

    navigator.clipboard.writeText(value).then(() => {
        showMerchantMessage('Copied', 'success');
    });
}

function buildIntegrationFetchExample(apiKey) {
    const key = apiKey && apiKey !== '-' ? apiKey : '<MERCHANT_API_KEY>';
    return `fetch('/api/v1/payments/charge', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Merchant-Api-Key': '${key}'
  },
  body: JSON.stringify({
    amount: 49.99,
    currency: 'USD',
    card_number: '4111111111111111',
    cvv: '123',
    expiry_date: '12/28',
    merchant_order_id: 'ORDER-1001',
    description: 'Demo ecommerce checkout'
  })
})
  .then(response => response.json())
  .then(payment => console.log(payment));`;
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatCurrency(amount, currency) {
    const numeric = Number(amount || 0);
    return `${currency || 'USD'} ${numeric.toFixed(2)}`;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('merchantRegisterForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleMerchantRegister);
    }

    const loginForm = document.getElementById('merchantLoginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleMerchantLogin);
    }

    if (document.body.classList.contains('merchant-dashboard-page')) {
        loadMerchantDashboard();
    }
});
