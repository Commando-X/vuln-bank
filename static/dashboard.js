// Set current date
document.addEventListener('DOMContentLoaded', function() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const today = new Date();
    document.getElementById('current-date').textContent = today.toLocaleDateString('en-US', options);
});

let beneficiaries = [];
let selectedBeneficiaryId = null;
let wallets = [];
let exchangeRates = [];
let activeWalletId = null;

// Vulnerability: Token stored in localStorage
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('jwt_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    fetchTransactions();

    // Add event listeners
    document.getElementById('transferForm').addEventListener('submit', handleTransfer);
    document.getElementById('loanForm').addEventListener('submit', handleLoanRequest);
    document.getElementById('profileUploadForm').addEventListener('submit', handleProfileUpload);
    const profileUrlBtn = document.getElementById('profileUrlButton');
    if (profileUrlBtn) {
        profileUrlBtn.addEventListener('click', handleProfileUrlImport);
    }

    const beneficiaryForm = document.getElementById('beneficiaryForm');
    if (beneficiaryForm) {
        beneficiaryForm.addEventListener('submit', handleAddBeneficiary);
    }

    const beneficiarySelect = document.getElementById('selected_beneficiary');
    if (beneficiarySelect) {
        beneficiarySelect.addEventListener('change', function(e) {
            handleBeneficiarySelection(e.target.value);
        });
    }

    const beneficiaryOtpForm = document.getElementById('beneficiaryOtpForm');
    if (beneficiaryOtpForm) {
        beneficiaryOtpForm.addEventListener('submit', handleBeneficiaryOtpSubmit);
    }

    const switchWalletBtn = document.getElementById('switchWalletBtn');
    if (switchWalletBtn) {
        switchWalletBtn.addEventListener('click', handleWalletSwitch);
    }

    const convertWalletForm = document.getElementById('convertWalletForm');
    if (convertWalletForm) {
        convertWalletForm.addEventListener('submit', handleMainToWalletConversion);
    }

    const internalTransferForm = document.getElementById('internalTransferForm');
    if (internalTransferForm) {
        internalTransferForm.addEventListener('submit', handleInternalWalletTransfer);
    }

    const createWalletForm = document.getElementById('createWalletForm');
    if (createWalletForm) {
        createWalletForm.addEventListener('submit', handleCreateWallet);
    }

    const walletP2PTransferForm = document.getElementById('walletP2PTransferForm');
    if (walletP2PTransferForm) {
        walletP2PTransferForm.addEventListener('submit', handleTransferToWallet);
    }
    
    // Add virtual cards event listener
    document.getElementById('createCardForm').addEventListener('submit', handleCreateCard);
    
    // Load virtual cards
    fetchVirtualCards();

    // Add bill payment functions
    document.getElementById('payBillForm').addEventListener('submit', handleBillPayment);
    
    // Load initial data
    loadBillCategories();
    loadPaymentHistory();
    loadBeneficiaries();
    loadWalletData();

    // Set active nav link based on URL hash
    const hash = window.location.hash || '#profile';
    const activeLink = document.querySelector(`.nav-link[href='${hash}']`);
    if (activeLink) {
        setActiveLink(activeLink);
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);
});

// Navigation functions
function setActiveLink(element) {
    // Remove active class from all links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to clicked link
    element.classList.add('active');
    
    // For mobile view, close the menu
    if (window.innerWidth <= 768) {
        document.querySelector('.side-panel').classList.remove('active');
    }
}

function toggleSidePanel() {
    document.querySelector('.side-panel').classList.toggle('active');
}

function handleScroll() {
    const sections = document.querySelectorAll('.dashboard-section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let current = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= (sectionTop - 200)) {
            current = '#' + section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === current) {
            link.classList.add('active');
        }
    });
}

function showGlobalMessage(message, color) {
    const messageEl = document.getElementById('message');
    if (!messageEl) return;
    messageEl.innerHTML = message;
    messageEl.style.color = color;
}

async function executeBeneficiaryGraphQL(query, variables = {}) {
    const response = await fetch('/graphql/beneficiaries', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            variables: variables
        })
    });

    return response.json();
}

function getBeneficiaryById(beneficiaryId) {
    return beneficiaries.find(b => Number(b.id) === Number(beneficiaryId));
}

function renderBeneficiaryDropdown() {
    const beneficiarySelect = document.getElementById('selected_beneficiary');
    if (!beneficiarySelect) return;

    const currentValue = selectedBeneficiaryId ? String(selectedBeneficiaryId) : beneficiarySelect.value;

    beneficiarySelect.innerHTML = `
        <option value="">Manual Account Transfer</option>
        ${beneficiaries.map(b => `
            <option value="${b.id}">
                ${(b.nickname || b.beneficiary_name || b.account_number)} - ${b.account_number} ${b.is_verified ? '(Verified)' : '(Pending)'}
            </option>
        `).join('')}
    `;

    if (currentValue && beneficiaries.some(b => String(b.id) === String(currentValue))) {
        beneficiarySelect.value = currentValue;
        handleBeneficiarySelection(currentValue);
        return;
    }

    selectedBeneficiaryId = null;
    handleBeneficiarySelection('');
}

function renderBeneficiaryList() {
    const container = document.getElementById('beneficiary-list');
    if (!container) return;

    if (!beneficiaries.length) {
        container.innerHTML = '<p style="text-align: center; padding: 1rem;">No beneficiaries yet. Add one to start transfers.</p>';
        return;
    }

    // Vulnerability: innerHTML with unsanitized beneficiary data.
    container.innerHTML = beneficiaries.map(beneficiary => `
        <div class="beneficiary-item">
            <div class="beneficiary-item-header">
                <div>
                    <div class="beneficiary-name">${beneficiary.nickname || beneficiary.beneficiary_name || 'Unnamed Beneficiary'}</div>
                    <div class="beneficiary-account">${beneficiary.account_number}</div>
                </div>
                <span class="beneficiary-status ${beneficiary.is_verified ? 'verified' : 'pending'}">
                    ${beneficiary.is_verified ? 'Verified' : 'Pending'}
                </span>
            </div>
            <div class="beneficiary-meta">
                Name: ${beneficiary.beneficiary_name || 'N/A'} | Limit: $${beneficiary.transfer_limit}
            </div>
            <div class="beneficiary-actions">
                <button type="button" onclick="useBeneficiaryForTransfer(${beneficiary.id})">Use for Transfer</button>
                <button type="button" onclick="editBeneficiaryNickname(${beneficiary.id})">Edit Nickname</button>
                <button type="button" onclick="editBeneficiaryLimit(${beneficiary.id})">Edit Limit</button>
                <button type="button" onclick="startBeneficiaryVerification(${beneficiary.id})">Verify</button>
                <button type="button" onclick="deleteBeneficiary(${beneficiary.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function loadBeneficiaries() {
    try {
        const response = await executeBeneficiaryGraphQL(`
            query ListBeneficiaries {
                beneficiaries {
                    id
                    user_id
                    account_number
                    beneficiary_name
                    nickname
                    transfer_limit
                    is_verified
                    verified_at
                    created_at
                }
            }
        `);

        beneficiaries = (response.data && response.data.beneficiaries) ? response.data.beneficiaries : [];
        renderBeneficiaryDropdown();
        renderBeneficiaryList();
    } catch (error) {
        const list = document.getElementById('beneficiary-list');
        if (list) {
            list.innerHTML = '<p style="text-align: center; padding: 1rem;">Failed to load beneficiaries.</p>';
        }
    }
}

function handleBeneficiarySelection(beneficiaryId) {
    const toAccountInput = document.getElementById('to_account');
    const transferMeta = document.getElementById('beneficiary-transfer-meta');
    const transferForm = document.getElementById('transferForm');

    if (!toAccountInput || !transferMeta || !transferForm) return;

    if (!beneficiaryId) {
        selectedBeneficiaryId = null;
        toAccountInput.readOnly = false;
        toAccountInput.value = '';
        transferMeta.innerHTML = 'No beneficiary selected.';
        return;
    }

    const selected = getBeneficiaryById(beneficiaryId);
    if (!selected) {
        selectedBeneficiaryId = null;
        toAccountInput.readOnly = false;
        transferMeta.innerHTML = 'Beneficiary not found.';
        return;
    }

    selectedBeneficiaryId = selected.id;
    toAccountInput.value = selected.account_number;
    toAccountInput.readOnly = true;
    transferMeta.innerHTML = `
        Selected: ${selected.nickname || selected.beneficiary_name || selected.account_number} |
        Limit: $${selected.transfer_limit} |
        Status: ${selected.is_verified ? 'Verified' : 'Pending verification'}
    `;
}

function useBeneficiaryForTransfer(beneficiaryId) {
    const beneficiarySelect = document.getElementById('selected_beneficiary');
    if (!beneficiarySelect) return;

    beneficiarySelect.value = beneficiaryId;
    handleBeneficiarySelection(beneficiaryId);
}

async function runBeneficiaryNameEnquiry() {
    const accountNumber = document.getElementById('beneficiary_account_number').value;
    const resultEl = document.getElementById('beneficiary-name-enquiry');

    if (!accountNumber) {
        resultEl.innerHTML = 'Enter an account number first.';
        return;
    }

    try {
        const response = await executeBeneficiaryGraphQL(`
            query NameEnquiry($accountNumber: String) {
                nameEnquiry(accountNumber: $accountNumber) {
                    account_holder_name
                    account_number
                    matched_user_id
                }
            }
        `, { accountNumber: accountNumber });

        const enquiry = response.data && response.data.nameEnquiry;
        if (enquiry) {
            resultEl.innerHTML = `Account Name: <strong>${enquiry.account_holder_name}</strong> (Acct: ${enquiry.account_number})`;
        } else {
            resultEl.innerHTML = 'No name enquiry result returned.';
        }
    } catch (error) {
        resultEl.innerHTML = 'Name enquiry failed.';
    }
}

async function handleAddBeneficiary(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const input = {
        account_number: formData.get('account_number'),
        nickname: formData.get('nickname'),
        transfer_limit: parseFloat(formData.get('transfer_limit') || '5000')
    };

    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation AddBeneficiary($input: BeneficiaryInput) {
                addBeneficiary(input: $input) {
                    id
                    account_number
                    beneficiary_name
                    nickname
                    transfer_limit
                    is_verified
                    generated_otp
                }
            }
        `, { input: input });

        const created = response.data && response.data.addBeneficiary;
        if (created) {
            const enquiryEl = document.getElementById('beneficiary-name-enquiry');
            if (enquiryEl) {
                enquiryEl.innerHTML = 'Beneficiary added successfully. Run verification to activate transfers.';
            }
            showGlobalMessage('Beneficiary added successfully', 'green');
            event.target.reset();
            await loadBeneficiaries();
            return;
        }

        showGlobalMessage('Failed to add beneficiary', 'red');
    } catch (error) {
        showGlobalMessage('Failed to add beneficiary', 'red');
    }
}

async function editBeneficiaryNickname(beneficiaryId) {
    const beneficiary = getBeneficiaryById(beneficiaryId);
    if (!beneficiary) return;

    const newNickname = prompt('Enter new beneficiary nickname', beneficiary.nickname || '');
    if (newNickname === null) return;

    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation UpdateBeneficiary($id: Int, $input: BeneficiaryUpdateInput) {
                updateBeneficiary(id: $id, input: $input) {
                    id
                    nickname
                }
            }
        `, {
            id: Number(beneficiaryId),
            input: { nickname: newNickname }
        });

        if (response.data && response.data.updateBeneficiary) {
            showGlobalMessage('Beneficiary nickname updated', 'green');
            await loadBeneficiaries();
        } else {
            showGlobalMessage('Failed to update nickname', 'red');
        }
    } catch (error) {
        showGlobalMessage('Failed to update nickname', 'red');
    }
}

async function editBeneficiaryLimit(beneficiaryId) {
    const beneficiary = getBeneficiaryById(beneficiaryId);
    if (!beneficiary) return;

    const value = prompt('Enter new transfer limit', beneficiary.transfer_limit);
    if (value === null) return;

    const newLimit = parseFloat(value);
    if (Number.isNaN(newLimit)) {
        showGlobalMessage('Transfer limit must be a number', 'red');
        return;
    }

    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation UpdateBeneficiary($id: Int, $input: BeneficiaryUpdateInput) {
                updateBeneficiary(id: $id, input: $input) {
                    id
                    transfer_limit
                }
            }
        `, {
            id: Number(beneficiaryId),
            input: { transfer_limit: newLimit }
        });

        if (response.data && response.data.updateBeneficiary) {
            showGlobalMessage('Beneficiary transfer limit updated', 'green');
            await loadBeneficiaries();
        } else {
            showGlobalMessage('Failed to update transfer limit', 'red');
        }
    } catch (error) {
        showGlobalMessage('Failed to update transfer limit', 'red');
    }
}

async function deleteBeneficiary(beneficiaryId) {
    if (!confirm('Delete this beneficiary?')) return;

    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation DeleteBeneficiary($id: Int) {
                deleteBeneficiary(id: $id) {
                    success
                    message
                    deleted_beneficiary_id
                }
            }
        `, { id: Number(beneficiaryId) });

        const deleted = response.data && response.data.deleteBeneficiary;
        if (deleted && deleted.success) {
            showGlobalMessage('Beneficiary deleted', 'green');
            await loadBeneficiaries();
            return;
        }

        showGlobalMessage((deleted && deleted.message) || 'Failed to delete beneficiary', 'red');
    } catch (error) {
        showGlobalMessage('Failed to delete beneficiary', 'red');
    }
}

async function startBeneficiaryVerification(beneficiaryId) {
    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation VerifyBeneficiary($id: Int, $autoVerify: Boolean) {
                verifyBeneficiary(id: $id, autoVerify: $autoVerify) {
                    id
                    otp
                    auto_verified
                    beneficiary_name
                    account_number
                    is_verified
                }
            }
        `, {
            id: Number(beneficiaryId),
            autoVerify: false
        });

        const verification = response.data && response.data.verifyBeneficiary;
        if (!verification) {
            showGlobalMessage('Failed to start beneficiary verification', 'red');
            return;
        }

        document.getElementById('otp_beneficiary_id').value = beneficiaryId;
        document.getElementById('beneficiary_otp').value = '';
        document.getElementById('beneficiary-otp-info').innerHTML = `
            OTP sent for ${verification.beneficiary_name} (${verification.account_number}).
        `;
        document.getElementById('beneficiaryOtpModal').style.display = 'flex';
    } catch (error) {
        showGlobalMessage('Failed to start beneficiary verification', 'red');
    }
}

function hideBeneficiaryOtpModal() {
    document.getElementById('beneficiaryOtpModal').style.display = 'none';
}

async function handleBeneficiaryOtpSubmit(event) {
    event.preventDefault();
    const beneficiaryId = Number(document.getElementById('otp_beneficiary_id').value);
    const otp = document.getElementById('beneficiary_otp').value;

    try {
        const response = await executeBeneficiaryGraphQL(`
            mutation VerifyBeneficiaryOtp($id: Int, $otp: String) {
                verifyBeneficiaryOtp(id: $id, otp: $otp) {
                    success
                    message
                    bypass_used
                }
            }
        `, {
            id: beneficiaryId,
            otp: otp
        });

        const verification = response.data && response.data.verifyBeneficiaryOtp;
        if (verification && verification.success) {
            hideBeneficiaryOtpModal();
            showGlobalMessage('Beneficiary verified successfully', 'green');
            await loadBeneficiaries();
            return;
        }

        showGlobalMessage((verification && verification.message) || 'OTP verification failed', 'red');
    } catch (error) {
        showGlobalMessage('OTP verification failed', 'red');
    }
}

async function executeWalletGraphQL(query, variables = {}) {
    const response = await fetch('/graphql/wallets', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            variables: variables
        })
    });

    return response.json();
}

function formatCurrencyLabel(currencyCode) {
    if (currencyCode === 'INR') return 'Rupees (INR)';
    if (currencyCode === 'JPY') return 'Yen (JPY)';
    return currencyCode;
}

function updateWalletMainBalanceDisplay() {
    const mainBalance = document.getElementById('balance');
    const walletMainBalance = document.getElementById('wallet-main-balance');
    if (mainBalance && walletMainBalance) {
        walletMainBalance.textContent = mainBalance.textContent;
    }
}

function renderWalletList() {
    const container = document.getElementById('wallet-list');
    if (!container) return;

    if (!wallets.length) {
        container.innerHTML = '<p style="text-align: center; padding: 1rem;">No wallets found.</p>';
        return;
    }

    // Vulnerability: unsanitized data rendered with innerHTML.
    container.innerHTML = wallets.map(wallet => `
        <div class="wallet-item">
            <div class="wallet-currency">${formatCurrencyLabel(wallet.currency)}</div>
            <div class="wallet-status">Wallet ID: ${wallet.id}</div>
            <div class="wallet-balance">${wallet.balance}</div>
            <div class="wallet-status">${wallet.is_active ? 'Active Account' : 'Inactive'}</div>
        </div>
    `).join('');
}

function renderExchangeRates() {
    const container = document.getElementById('exchange-rate-view');
    if (!container) return;

    if (!exchangeRates.length) {
        container.innerHTML = '<p style="text-align: center; padding: 1rem;">No exchange rates configured.</p>';
        return;
    }

    // Vulnerability: unsanitized data rendered with innerHTML.
    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Currency</th>
                    <th>Rate to NGN</th>
                    <th>Updated</th>
                    <th>Updated By</th>
                </tr>
            </thead>
            <tbody>
                ${exchangeRates.map(rate => `
                    <tr>
                        <td>${formatCurrencyLabel(rate.currency_code)}</td>
                        <td>${rate.rate_to_ngn}</td>
                        <td>${rate.updated_at || '-'}</td>
                        <td>${rate.updated_by || '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function populateWalletSelect(selectId, allowEmpty = false) {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = `
        ${allowEmpty ? '<option value=\"\">Select Wallet</option>' : ''}
        ${wallets.map(wallet => `
            <option value="${wallet.id}">
                ${formatCurrencyLabel(wallet.currency)} - ${wallet.balance}
            </option>
        `).join('')}
    `;
}

function populateWalletSourceSelect() {
    const select = document.getElementById('wallet_transfer_source_wallet_id');
    if (!select) return;

    select.innerHTML = `
        <option value="">Main Balance (NGN)</option>
        ${wallets.map(wallet => `
            <option value="${wallet.id}">
                Wallet ${wallet.id} - ${formatCurrencyLabel(wallet.currency)} (${wallet.balance})
            </option>
        `).join('')}
    `;
}

function renderWalletSelectors() {
    populateWalletSelect('wallet-switch-select');
    populateWalletSelect('convert_wallet_id');
    populateWalletSelect('from_wallet_id');
    populateWalletSelect('to_wallet_id');
    populateWalletSourceSelect();

    const activeWallet = wallets.find(wallet => wallet.is_active);
    activeWalletId = activeWallet ? activeWallet.id : null;

    if (activeWallet) {
        const switchSelect = document.getElementById('wallet-switch-select');
        if (switchSelect) switchSelect.value = String(activeWallet.id);
    }

    const summary = document.getElementById('wallet-active-summary');
    if (summary) {
        if (activeWallet) {
            summary.innerHTML = `Active wallet: <strong>${formatCurrencyLabel(activeWallet.currency)}</strong> (${activeWallet.balance})`;
        } else {
            summary.innerHTML = 'No active wallet selected.';
        }
    }
}

async function loadWalletData() {
    try {
        const [walletResponse, rateResponse] = await Promise.all([
            executeWalletGraphQL(`
                query Wallets {
                    wallets {
                        id
                        user_id
                        currency
                        balance
                        is_active
                        created_at
                    }
                }
            `),
            executeWalletGraphQL(`
                query ExchangeRates {
                    exchangeRates {
                        id
                        currency_code
                        rate_to_ngn
                        updated_at
                        updated_by
                    }
                }
            `)
        ]);

        wallets = (walletResponse.data && walletResponse.data.wallets) ? walletResponse.data.wallets : [];
        exchangeRates = (rateResponse.data && rateResponse.data.exchangeRates) ? rateResponse.data.exchangeRates : [];

        updateWalletMainBalanceDisplay();
        renderWalletSelectors();
        renderWalletList();
        renderExchangeRates();
    } catch (error) {
        const walletList = document.getElementById('wallet-list');
        if (walletList) {
            walletList.innerHTML = '<p style="text-align: center; padding: 1rem;">Failed to load wallets.</p>';
        }
    }
}

async function handleWalletSwitch() {
    const switchSelect = document.getElementById('wallet-switch-select');
    if (!switchSelect || !switchSelect.value) {
        showGlobalMessage('Select a wallet to switch.', 'red');
        return;
    }

    try {
        const response = await executeWalletGraphQL(`
            mutation SwitchWallet($input: WalletSwitchInput) {
                switchWallet(input: $input) {
                    switched_wallet {
                        id
                        currency
                        balance
                        is_active
                    }
                }
            }
        `, {
            input: {
                wallet_id: Number(switchSelect.value)
            }
        });

        const switched = response.data && response.data.switchWallet;
        if (switched) {
            showGlobalMessage('Wallet switched successfully', 'green');
            await loadWalletData();
            return;
        }

        showGlobalMessage('Failed to switch wallet', 'red');
    } catch (error) {
        showGlobalMessage('Failed to switch wallet', 'red');
    }
}

async function handleCreateWallet(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const input = {
        currency: formData.get('currency'),
        is_active: formData.get('is_active') === 'true'
    };

    try {
        const response = await executeWalletGraphQL(`
            mutation CreateWallet($input: WalletCreateInput) {
                createWallet(input: $input) {
                    wallet {
                        id
                        user_id
                        currency
                        balance
                        is_active
                    }
                }
            }
        `, { input: input });

        const created = response.data && response.data.createWallet;
        if (created && created.wallet) {
            showGlobalMessage(`Wallet created: ${created.wallet.currency} (#${created.wallet.id})`, 'green');
            event.target.reset();
            await loadWalletData();
            return;
        }

        showGlobalMessage('Failed to create wallet', 'red');
    } catch (error) {
        showGlobalMessage('Failed to create wallet', 'red');
    }
}

async function handleMainToWalletConversion(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const input = {
        wallet_id: Number(formData.get('wallet_id')),
        amount: parseFloat(formData.get('amount'))
    };

    try {
        const response = await executeWalletGraphQL(`
            mutation ConvertMainToWallet($input: WalletConversionInput) {
                convertMainToWallet(input: $input) {
                    source_user_id
                    debited_main_amount
                    credited_wallet_amount
                    applied_rate
                    main_balance
                    wallet {
                        id
                        currency
                        balance
                    }
                }
            }
        `, { input: input });

        const conversion = response.data && response.data.convertMainToWallet;
        if (conversion) {
            showGlobalMessage(`Converted ${conversion.debited_main_amount} to ${conversion.credited_wallet_amount} ${conversion.wallet.currency}.`, 'green');
            document.getElementById('balance').textContent = conversion.main_balance;
            updateWalletMainBalanceDisplay();
            event.target.reset();
            await loadWalletData();
            return;
        }

        showGlobalMessage('Conversion failed', 'red');
    } catch (error) {
        showGlobalMessage('Conversion failed', 'red');
    }
}

async function handleInternalWalletTransfer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const input = {
        from_wallet_id: Number(formData.get('from_wallet_id')),
        to_wallet_id: Number(formData.get('to_wallet_id')),
        amount: parseFloat(formData.get('amount'))
    };

    try {
        const response = await executeWalletGraphQL(`
            mutation InternalWalletTransfer($input: WalletTransferInput) {
                internalWalletTransfer(input: $input) {
                    debited_amount
                    credited_amount
                    conversion_debug
                    from_wallet {
                        id
                        currency
                        balance
                    }
                    to_wallet {
                        id
                        currency
                        balance
                    }
                }
            }
        `, { input: input });

        const transfer = response.data && response.data.internalWalletTransfer;
        if (transfer) {
            showGlobalMessage(`Internal transfer complete (${transfer.conversion_debug}).`, 'green');
            event.target.reset();
            await loadWalletData();
            return;
        }

        showGlobalMessage('Internal transfer failed', 'red');
    } catch (error) {
        showGlobalMessage('Internal transfer failed', 'red');
    }
}

async function handleTransferToWallet(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    const input = {
        destination_wallet_id: Number(formData.get('destination_wallet_id')),
        amount: parseFloat(formData.get('amount'))
    };

    const sourceWalletId = formData.get('source_wallet_id');
    if (sourceWalletId) {
        input.source_wallet_id = Number(sourceWalletId);
    }

    try {
        const response = await executeWalletGraphQL(`
            mutation TransferToWallet($input: WalletP2PTransferInput) {
                transferToWallet(input: $input) {
                    destination_wallet {
                        id
                        currency
                        balance
                    }
                    source_type
                    debited_amount
                    credited_amount
                    conversion_path
                    main_balance
                }
            }
        `, { input: input });

        const transfer = response.data && response.data.transferToWallet;
        if (transfer) {
            if (transfer.main_balance !== undefined && transfer.main_balance !== null) {
                document.getElementById('balance').textContent = transfer.main_balance;
                updateWalletMainBalanceDisplay();
            }

            showGlobalMessage(
                `Transferred ${transfer.debited_amount}. Credited ${transfer.credited_amount} ${transfer.destination_wallet.currency} (${transfer.conversion_path}).`,
                'green'
            );
            event.target.reset();
            await loadWalletData();
            return;
        }

        showGlobalMessage('Wallet transfer failed', 'red');
    } catch (error) {
        showGlobalMessage('Wallet transfer failed', 'red');
    }
}

async function fundVirtualCardBalance(cardId) {
    const amountInput = prompt('Amount to fund this virtual card:');
    if (!amountInput) return;

    const amount = parseFloat(amountInput);
    if (Number.isNaN(amount)) {
        showGlobalMessage('Invalid amount', 'red');
        return;
    }

    const useWalletSource = confirm('Use active wallet as source? Click Cancel to use main balance.');

    const input = {
        card_id: Number(cardId),
        amount: amount
    };

    if (useWalletSource && activeWalletId) {
        input.source_wallet_id = Number(activeWalletId);
    }

    try {
        const response = await executeWalletGraphQL(`
            mutation FundVirtualCard($input: WalletCardFundingInput) {
                fundVirtualCard(input: $input) {
                    card_id
                    card_currency
                    new_card_balance
                    source_type
                    debited_amount
                    credited_amount
                    applied_rate
                    main_balance
                }
            }
        `, { input: input });

        const funding = response.data && response.data.fundVirtualCard;
        if (funding) {
            if (funding.main_balance !== undefined && funding.main_balance !== null) {
                document.getElementById('balance').textContent = funding.main_balance;
                updateWalletMainBalanceDisplay();
            }
            showGlobalMessage(`Card funded: +${funding.credited_amount} ${funding.card_currency}`, 'green');
            await Promise.all([loadWalletData(), fetchVirtualCards()]);
            return;
        }

        showGlobalMessage('Card funding failed', 'red');
    } catch (error) {
        showGlobalMessage('Card funding failed', 'red');
    }
}

// Transfer money handler
async function handleTransfer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);
    const beneficiarySelect = document.getElementById('selected_beneficiary');
    const selectedId = beneficiarySelect ? beneficiarySelect.value : '';

    if (selectedId) {
        const beneficiary = getBeneficiaryById(selectedId);

        if (!beneficiary) {
            showGlobalMessage('Selected beneficiary could not be found.', 'red');
            return;
        }

        if (!beneficiary.is_verified) {
            showGlobalMessage('Beneficiary must be verified before transfer.', 'red');
            return;
        }

        const transferAmount = parseFloat(jsonData.amount);
        const beneficiaryLimit = parseFloat(beneficiary.transfer_limit || '0');

        if (!Number.isNaN(transferAmount) && transferAmount > beneficiaryLimit) {
            showGlobalMessage(`Transfer exceeds beneficiary limit of $${beneficiaryLimit}.`, 'red');
            return;
        }

        jsonData.to_account = beneficiary.account_number;
    }

    try {
        const response = await fetch('/transfer', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            showGlobalMessage(data.message, 'green');
            document.getElementById('balance').textContent = data.new_balance;
            updateWalletMainBalanceDisplay();
            
            // Refresh transactions
            fetchTransactions();

            const selectedBeneficiary = selectedId;
            event.target.reset();
            if (selectedBeneficiary && beneficiarySelect) {
                beneficiarySelect.value = selectedBeneficiary;
                handleBeneficiarySelection(selectedBeneficiary);
            } else {
                handleBeneficiarySelection('');
            }
        } else {
            showGlobalMessage(data.message, 'red');
        }
    } catch (error) {
        showGlobalMessage('Transfer failed', 'red');
    }
}

// Loan request handler
async function handleLoanRequest(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

    try {
        const response = await fetch('/request_loan', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            document.getElementById('message').innerHTML = 'Loan requested successfully, our staff will review and approve!';
            document.getElementById('message').style.color = 'green';
            
            // Check if loans section exists, if not create it
            let loansSection = document.querySelector('.loans-section');
            if (!loansSection) {
                // Create new loans section
                loansSection = document.createElement('div');
                loansSection.className = 'loans-section';
                loansSection.style.marginTop = '2rem';
                loansSection.innerHTML = `
                    <h3 style="margin-bottom: 1rem;">Your Loan Applications</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Amount</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                `;
                // Add it to the loans section
                document.getElementById('loans').appendChild(loansSection);
            }
            
            // Add new loan to the table
            const loansTableBody = loansSection.querySelector('tbody');
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>$${jsonData.amount}</td>
                <td><span class="status-pending">pending</span></td>
            `;
            loansTableBody.appendChild(newRow);
            
            // Clear form
            event.target.reset();
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Loan request failed';
        document.getElementById('message').style.color = 'red';
    }
}

// Profile picture upload handler
async function handleProfileUpload(event) {
    event.preventDefault();
    const formData = new FormData(event.target);

    try {
        const response = await fetch('/upload_profile_picture', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            },
            body: formData
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Vulnerability: No sanitization of file_path
            const img = document.getElementById('profile-picture');
            img.src = '/' + data.file_path + '?v=' + new Date().getTime(); // Prevent caching
            document.getElementById('upload-message').innerText = 'Upload successful!';
            document.getElementById('upload-message').style.color = 'green';
            event.target.reset();
        } else {
            document.getElementById('upload-message').innerText = data.message;
            document.getElementById('upload-message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('upload-message').innerText = 'Upload failed';
        document.getElementById('upload-message').style.color = 'red';
    }
}

// Import profile picture from URL (Intentionally Vulnerable to SSRF)
async function handleProfileUrlImport() {
    const imageUrl = prompt('Enter image URL to import as your profile picture:');
    if (!imageUrl) return;

    try {
        const response = await fetch('/upload_profile_picture_url', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image_url: imageUrl })
        });

        const data = await response.json();
        if (data.status === 'success') {
            const img = document.getElementById('profile-picture');
            img.src = '/' + data.file_path + '?v=' + new Date().getTime();
            document.getElementById('upload-message').innerText = 'Imported from URL successfully!';
            document.getElementById('upload-message').style.color = 'green';
        } else {
            document.getElementById('upload-message').innerText = data.message || 'Import failed';
            document.getElementById('upload-message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('upload-message').innerText = 'Import failed';
        document.getElementById('upload-message').style.color = 'red';
    }
}


// Fetch transactions
// Vulnerability: No rate limiting on transaction fetches
async function fetchTransactions() {
    try {
        const accountNumber = document.getElementById('account-number').textContent;
        const response = await fetch(`/transactions/${accountNumber}`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            if (data.transactions.length === 0) {
                document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">No transactions found</p>';
                return;
            }
            
            // Vulnerability: innerHTML used with unsanitized data
            const transactionHtml = data.transactions.map(t => {
                const isOutgoing = t.from_account === accountNumber;
                const transactionType = isOutgoing ? 'sent' : 'received';
                
                return `
                    <div class="transaction-item ${transactionType}">
                        <div class="transaction-details">
                            <div class="transaction-account">
                                ${isOutgoing ? 'To: ' + t.to_account : 'From: ' + t.from_account}
                            </div>
                            <div class="transaction-date">${t.timestamp}</div>
                            ${t.description ? `<div class="transaction-description">${t.description}</div>` : ''}
                        </div>
                        <div class="transaction-amount ${transactionType}">
                            ${isOutgoing ? '-' : '+'}$${Math.abs(t.amount)}
                        </div>
                    </div>
                `;
            }).join('');
            
            document.getElementById('transaction-list').innerHTML = transactionHtml;
        } else {
            document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading transactions</p>';
        }
    } catch (error) {
        document.getElementById('transaction-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading transactions</p>';
    }
}

// Virtual Cards Management
let virtualCards = [];

async function fetchVirtualCards() {
    try {
        const response = await fetch('/api/virtual-cards', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            virtualCards = data.cards;
            renderVirtualCards();
        } else {
            document.getElementById('virtual-cards-list').innerHTML = '<p style="text-align: center;">No virtual cards found</p>';
        }
    } catch (error) {
        document.getElementById('virtual-cards-list').innerHTML = '<p style="text-align: center;">Error loading virtual cards</p>';
    }
}

function renderVirtualCards() {
    const container = document.getElementById('virtual-cards-list');
    if (virtualCards.length === 0) {
        container.innerHTML = '<p style="text-align: center;">No virtual cards found. Create one to get started.</p>';
        return;
    }
    
    // Vulnerability: XSS possible in card rendering
    container.innerHTML = virtualCards.map(card => `
        <div class="virtual-card ${card.is_frozen ? 'frozen' : ''}" id="card-${card.id}">
            <div class="card-type">${card.card_type.toUpperCase()} • ${card.currency || 'NGN'}</div>
            <div class="card-number">${formatCardNumber(card.card_number)}</div>
            <div class="card-details">
                <div>Exp: ${card.expiry_date}</div>
                <div>CVV: ${card.cvv}</div>
            </div>
            <div>Limit: $${card.limit}</div>
            <div>Balance: ${card.balance} ${card.currency || 'NGN'}</div>
            <div class="card-actions">
                <button onclick="toggleCardFreeze(${card.id})">${card.is_frozen ? 'Unfreeze' : 'Freeze'}</button>
                <button onclick="showCardDetails(${card.id})">Details</button>
                <button onclick="showTransactionHistory(${card.id})">History</button>
                <button onclick="showUpdateLimit(${card.id})">Update Limit</button>
                <button onclick="fundVirtualCardBalance(${card.id})">Fund</button>
            </div>
        </div>
    `).join('');
}

function formatCardNumber(number) {
    return number.match(/.{1,4}/g).join(' ');
}

function showCreateCardModal() {
    document.getElementById('createCardModal').style.display = 'flex';
}

function hideCreateCardModal() {
    document.getElementById('createCardModal').style.display = 'none';
    document.getElementById('createCardForm').reset();
}

function showCardDetails(cardId) {
    const card = virtualCards.find(c => c.id === cardId);
    if (!card) return;

    const modal = document.getElementById('cardDetailsModal');
    const content = document.getElementById('cardDetailsContent');
    
    content.innerHTML = `
        <div class="form-group">
            <label>Card Number</label>
            <p>${formatCardNumber(card.card_number)}</p>
        </div>
        <div class="form-group">
            <label>CVV</label>
            <p>${card.cvv}</p>
        </div>
        <div class="form-group">
            <label>Expiry Date</label>
            <p>${card.expiry_date}</p>
        </div>
        <div class="form-group">
            <label>Card Type</label>
            <p>${card.card_type}</p>
        </div>
        <div class="form-group">
            <label>Currency</label>
            <p>${card.currency || 'NGN'}</p>
        </div>
        <div class="form-group">
            <label>Current Limit</label>
            <p>$${card.limit}</p>
        </div>
        <div class="form-group">
            <label>Current Balance</label>
            <p>$${card.balance}</p>
        </div>
        <div class="form-group">
            <label>Status</label>
            <p>${card.is_frozen ? 'Frozen' : 'Active'}</p>
        </div>
        <div class="form-group">
            <label>Created</label>
            <p>${new Date(card.created_at).toLocaleDateString()}</p>
        </div>
    `;
    
    modal.style.display = 'flex';
}

function hideCardDetailsModal() {
    document.getElementById('cardDetailsModal').style.display = 'none';
}

async function handleCreateCard(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

    try {
        const response = await fetch('/api/virtual-cards/create', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            hideCreateCardModal();
            await fetchVirtualCards();
            
            document.getElementById('message').innerHTML = 'Virtual card created successfully!';
            document.getElementById('message').style.color = 'green';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to create virtual card';
        document.getElementById('message').style.color = 'red';
    }
}

async function toggleCardFreeze(cardId) {
    try {
        const response = await fetch(`/api/virtual-cards/${cardId}/toggle-freeze`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            await fetchVirtualCards();
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to freeze/unfreeze card';
        document.getElementById('message').style.color = 'red';
    }
}

async function showTransactionHistory(cardId) {
    try {
        const response = await fetch(`/api/virtual-cards/${cardId}/transactions`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const modal = document.getElementById('cardDetailsModal');
            const content = document.getElementById('cardDetailsContent');
            
            if (data.transactions.length === 0) {
                content.innerHTML = '<p style="text-align: center; padding: 1rem;">No transactions found for this card</p>';
                modal.style.display = 'flex';
                return;
            }
            
            content.innerHTML = `
                <h4>Transaction History</h4>
                <div class="transaction-list">
                    ${data.transactions.map(t => `
                        <div class="transaction-item">
                            <div class="transaction-details">
                                <div class="transaction-account">${t.merchant}</div>
                                <div class="transaction-date">${new Date(t.timestamp).toLocaleString()}</div>
                            </div>
                            <div class="transaction-amount">${t.amount}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            modal.style.display = 'flex';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Failed to load transaction history';
        document.getElementById('message').style.color = 'red';
    }
}

async function showUpdateLimit(cardId) {
    const card = virtualCards.find(c => c.id === cardId);
    if (!card) return;

    const modal = document.getElementById('cardDetailsModal');
    const content = document.getElementById('cardDetailsContent');
    
    // Vulnerability: Exposing form that allows updating any field
    content.innerHTML = `
        <h4>Update Card Limit</h4>
        <form id="updateCardForm" onsubmit="return handleCardUpdate(event, ${cardId})">
            <div class="form-group">
                <label for="card_limit_update">Card Limit</label>
                <input type="number" id="card_limit_update" name="card_limit" value="${card.limit}" step="0.01" required>
            </div>
            <div class="modal-footer">
                <button type="submit">Update Limit</button>
                <button type="button" onclick="hideCardDetailsModal()">Cancel</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'flex';
}

// Add handleCardUpdate function
async function handleCardUpdate(event, cardId) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    // Only send card_limit from UI
    const jsonData = {
        card_limit: parseFloat(formData.get('card_limit'))
    };

    try {
        // Vulnerability: Sending all form data including sensitive fields
        const response = await fetch(`/api/virtual-cards/${cardId}/update-limit`, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            await fetchVirtualCards();
            hideCardDetailsModal();
            document.getElementById('message').innerHTML = 'Card limit updated successfully';
            document.getElementById('message').style.color = 'green';
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Error updating card limit';
        document.getElementById('message').style.color = 'red';
    }
    
    return false; // Prevent form submission
}

// Bill Payments Functions
function showPayBillModal() {
    document.getElementById('payBillModal').style.display = 'flex';
}

function hidePayBillModal() {
    document.getElementById('payBillModal').style.display = 'none';
    document.getElementById('payBillForm').reset();
    document.getElementById('biller').disabled = true;
    document.getElementById('cardSelection').style.display = 'none';
}

// Load bill categories
async function loadBillCategories() {
    try {
        const response = await fetch('/api/bill-categories');
        const data = await response.json();
        
        if (data.status === 'success') {
            const select = document.getElementById('billCategory');
            // Vulnerability: XSS possible in category name and description
            select.innerHTML = `
                <option value="">Select Category</option>
                ${data.categories.map(cat => `
                    <option value="${cat.id}">${cat.name}</option>
                `).join('')}
            `;
        }
    } catch (error) {
        console.error('Error loading bill categories:', error);
    }
}

// Load billers for selected category
async function loadBillers(categoryId) {
    if (!categoryId) {
        const select = document.getElementById('biller');
        select.innerHTML = '<option value="">Select Biller</option>';
        select.disabled = true;
        return;
    }
    
    try {
        const response = await fetch(`/api/billers/by-category/${categoryId}`);
        const data = await response.json();
        
        const select = document.getElementById('biller');
        if (data.status === 'success') {
            // Create a Map to store unique billers by name
            const billerMap = new Map();
            
            // Only keep the first occurrence of each biller name
            data.billers.forEach(biller => {
                if (!billerMap.has(biller.name)) {
                    billerMap.set(biller.name, biller);
                }
            });

            // Convert Map values back to array
            const uniqueBillers = Array.from(billerMap.values());

            // Sort billers by name for consistency
            uniqueBillers.sort((a, b) => a.name.localeCompare(b.name));

            select.innerHTML = `
                <option value="">Select Biller</option>
                ${uniqueBillers.map(biller => `
                    <option value="${biller.id}" 
                            data-min="${biller.minimum_amount}"
                            data-max="${biller.maximum_amount || ''}"
                    >${biller.name}</option>
                `).join('')}
            `;
            select.disabled = false;
        } else {
            select.innerHTML = '<option value="">No billers available</option>';
            select.disabled = true;
        }
    } catch (error) {
        console.error('Error loading billers:', error);
        const select = document.getElementById('biller');
        select.innerHTML = '<option value="">Error loading billers</option>';
        select.disabled = true;
    }
}

// Toggle card selection based on payment method
function toggleCardSelection(method) {
    const cardSelection = document.getElementById('cardSelection');
    if (method === 'virtual_card') {
        cardSelection.style.display = 'block';
        loadVirtualCardsForPayment();  // Load the cards
    } else {
        cardSelection.style.display = 'none';
    }
}

// Function to load virtual cards for payment selection
async function loadVirtualCardsForPayment() {
    try {
        const response = await fetch('/api/virtual-cards', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const select = document.querySelector('select[name="card_id"]');
            // Only show non-frozen cards with available balance
            select.innerHTML = `
                <option value="">Select Card</option>
                ${data.cards.filter(card => !card.is_frozen).map(card => `
                    <option value="${card.id}">
                        Card ending in ${card.card_number.slice(-4)} 
                        (Balance: $${card.balance})
                    </option>
                `).join('')}
            `;
        }
    } catch (error) {
        console.error('Error loading virtual cards:', error);
    }
}

// Handle bill payment submission
async function handleBillPayment(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {
        biller_id: parseInt(formData.get('biller_id')),
        amount: parseFloat(formData.get('amount')),
        payment_method: formData.get('payment_method'),
        description: formData.get('description') || 'Bill Payment'
    };
    
    if (jsonData.payment_method === 'virtual_card') {
        jsonData.card_id = parseInt(formData.get('card_id'));
    }

    try {
        const response = await fetch('/api/bill-payments/create', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            hidePayBillModal();
            document.getElementById('message').innerHTML = 'Bill payment successful!';
            document.getElementById('message').style.color = 'green';
            await loadPaymentHistory();
            
            // Refresh balances if necessary
            if (jsonData.payment_method === 'virtual_card') {
                await fetchVirtualCards();
            } else {
                // Update account balance
                const balanceElement = document.getElementById('balance');
                const currentBalance = parseFloat(balanceElement.textContent);
                balanceElement.textContent = (currentBalance - jsonData.amount).toFixed(2);
            }
        } else {
            document.getElementById('message').innerHTML = data.message;
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        document.getElementById('message').innerHTML = 'Payment failed';
        document.getElementById('message').style.color = 'red';
    }
}

// Load payment history
async function loadPaymentHistory() {
    try {
        const response = await fetch('/api/bill-payments/history', {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        if (data.status === 'success') {
            const container = document.getElementById('bill-payments-list');
            if (data.payments.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 2rem;">No bill payments found</p>';
                return;
            }

            // Vulnerability: XSS possible in payment details
            container.innerHTML = data.payments.map(payment => `
                <div class="payment-item">
                    <div class="payment-header">
                        <div class="payment-amount">$${payment.amount}</div>
                        <div class="payment-status">${payment.status}</div>
                    </div>
                    <div class="payment-details">
                        <div>Biller: ${payment.biller_name}</div>
                        <div>Category: ${payment.category_name}</div>
                        <div>Payment Method: ${payment.payment_method}
                            ${payment.card_number ? ` (Card ending in ${payment.card_number.slice(-4)})` : ''}
                        </div>
                        <div>Reference: ${payment.reference}</div>
                        <div>Date: ${new Date(payment.created_at).toLocaleString()}</div>
                        ${payment.description ? `<div>Description: ${payment.description}</div>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            document.getElementById('bill-payments-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading payment history</p>';
        }
    } catch (error) {
        document.getElementById('bill-payments-list').innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading payment history</p>';
    }
}

// Vulnerability: No server-side token invalidation
function logout() {
    localStorage.removeItem('jwt_token');
    window.location.href = '/login';
}


// ===== CUSTOMER SUPPORT CHAT FUNCTIONALITY =====

let chatOpen = false;
let chatHistory = [];

// Initialize chat widget
document.addEventListener('DOMContentLoaded', function() {
    // Set initial time for welcome message
    document.getElementById('initialTime').textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    // Add enter key listener for chat input
    document.getElementById('chatMessageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
});

function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    const chatBadge = document.getElementById('chatBadge');
    const chatWidget = document.getElementById('chatWidget');
    
    if (chatOpen) {
        // Close chat
        chatWindow.classList.add('closing');
        chatWidget.classList.remove('chat-open');
        setTimeout(() => {
            chatWindow.style.display = 'none';
            chatWindow.classList.remove('closing');
        }, 300);
        chatOpen = false;
    } else {
        // Open chat
        chatWindow.style.display = 'flex';
        chatWindow.classList.add('opening');
        chatWidget.classList.add('chat-open');
        setTimeout(() => {
            chatWindow.classList.remove('opening');
        }, 300);
        chatOpen = true;
        
        // Hide notification badge
        chatBadge.style.display = 'none';
        
        // Focus input
        setTimeout(() => {
            document.getElementById('chatMessageInput').focus();
        }, 300);
    }
}

function sendChatMessage() {
    const input = document.getElementById('chatMessageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Check for special commands
    if (message.toLowerCase() === '/status' || message.toLowerCase() === '/rate-limit') {
        // Add user message to chat
        addMessageToChat(message, true);
        
        // Clear input
        input.value = '';
        
        // Show typing indicator briefly
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.style.display = 'flex';
        
        setTimeout(() => {
            typingIndicator.style.display = 'none';
            checkRateLimitStatus();
        }, 500);
        
        return;
    }
    
    if (message.toLowerCase() === '/help' || message.toLowerCase() === '/commands') {
        // Add user message to chat
        addMessageToChat(message, true);
        
        // Clear input
        input.value = '';
        
        const helpMessage = `🤖 **Available Commands:**\n\n` +
            `• **/help** - Show this help message\n` +
            `• **/status** or **/rate-limit** - Check your current rate limit status\n` +
            `• **Switch modes** - Use the radio buttons above to switch between Anonymous and Authenticated modes\n\n` +
            `**Rate Limits:**\n` +
            `• Anonymous: 5 requests per 3 hours\n` +
            `• Authenticated: 10 requests per 3 hours\n\n` +
            `Just type your question to chat with the AI assistant!`;
        
        setTimeout(() => {
            addMessageToChat(helpMessage, false);
        }, 300);
        
        return;
    }
    
    // Add user message to chat
    addMessageToChat(message, true);
    
    // Clear input
    input.value = '';
    
    // Disable send button and show typing indicator
    const sendBtn = document.getElementById('sendChatBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    
    sendBtn.disabled = true;
    typingIndicator.style.display = 'flex';
    
    // Send message to AI
    sendToAI(message);
}

function addMessageToChat(message, isUser = false, timestamp = null) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageTime = timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            ${isUser ? 
                `<svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>` :
                `<svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7H14A7,7 0 0,1 21,14H22A1,1 0 0,1 23,15V18A1,1 0 0,1 22,19H21V20A2,2 0 0,1 19,22H5A2,2 0 0,1 3,20V19H2A1,1 0 0,1 1,18V15A1,1 0 0,1 2,14H3A7,7 0 0,1 10,7H11V5.73C10.4,5.39 10,4.74 10,4A2,2 0 0,1 12,2M7.5,13A2.5,2.5 0 0,0 5,15.5A2.5,2.5 0 0,0 7.5,18A2.5,2.5 0 0,0 10,15.5A2.5,2.5 0 0,0 7.5,13M16.5,13A2.5,2.5 0 0,0 14,15.5A2.5,2.5 0 0,0 16.5,18A2.5,2.5 0 0,0 19,15.5A2.5,2.5 0 0,0 16.5,13Z"/>
                </svg>`
            }
        </div>
        <div class="message-content">
            <div class="message-text">${escapeHtml(message)}</div>
            <div class="message-time">${messageTime}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendToAI(message) {
    try {
        // Get selected chat mode
        const selectedMode = document.querySelector('input[name="chatMode"]:checked').value;
        const token = localStorage.getItem('jwt_token');
        
        // Determine endpoint and headers based on mode
        let endpoint, headers;
        
        if (selectedMode === 'authenticated') {
            endpoint = '/api/ai/chat';
            headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            };
        } else {
            endpoint = '/api/ai/chat/anonymous';
            headers = {
                'Content-Type': 'application/json'
            };
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        document.getElementById('typingIndicator').style.display = 'none';
        
        // Re-enable send button
        document.getElementById('sendChatBtn').disabled = false;
        
        if (response.status === 429) {
            // Handle rate limiting specifically
            const rateLimitInfo = data.rate_limit_info || {};
            const limitType = rateLimitInfo.limit_type || 'unknown';
            const currentCount = rateLimitInfo.current_count || 'unknown';
            const limit = rateLimitInfo.limit || 'unknown';
            const windowHours = rateLimitInfo.window_hours || 3;
            
            let rateLimitMessage = `🚫 **Rate Limit Exceeded**\n\n`;
            
            if (limitType === 'unauthenticated_ip') {
                rateLimitMessage += `You've reached the limit for anonymous users: **${currentCount}/${limit} requests** in the last ${windowHours} hours.\n\n`;
                rateLimitMessage += `💡 **Tip**: Log in to get higher limits (10 requests per 3 hours)`;
            } else if (limitType === 'authenticated_user') {
                rateLimitMessage += `You've reached your user limit: **${currentCount}/${limit} requests** in the last ${windowHours} hours.\n\n`;
                rateLimitMessage += `Please wait before sending more messages.`;
            } else if (limitType === 'authenticated_ip') {
                rateLimitMessage += `Your IP address has reached the limit: **${currentCount}/${limit} requests** in the last ${windowHours} hours.\n\n`;
                rateLimitMessage += `Please wait before sending more messages.`;
            } else {
                rateLimitMessage += `${data.message || 'Too many requests. Please try again later.'}\n\n`;
                rateLimitMessage += `You can check your rate limit status in the chat options.`;
            }
            
            setTimeout(() => {
                addMessageToChat(rateLimitMessage, false);
            }, 500);
            
        } else if (data.status === 'success') {
            const aiResponse = data.ai_response.response || 'Sorry, I couldn\'t process your request.';
            
            // Add mode indicator to response for debugging
            let responseWithMode = aiResponse;
            if (selectedMode === 'anonymous') {
                responseWithMode += '\n\n🔓 (Anonymous Mode - No user context)';
            } else {
                responseWithMode += '\n\n🔐 (Authenticated Mode - User context included)';
            }
            
            // Add AI response with slight delay for realism
            setTimeout(() => {
                addMessageToChat(responseWithMode, false);
            }, 500);
            
        } else {
            // Handle other API errors (400, 401, 500, etc.)
            let errorMsg = 'Sorry, I\'m experiencing technical difficulties. Please try again later.';
            
            if (response.status === 401) {
                errorMsg = '🔐 **Authentication Error**\n\nYour session has expired. Please log in again or switch to Anonymous mode.';
            } else if (response.status === 400) {
                errorMsg = '❌ **Invalid Request**\n\n' + (data.message || 'Please check your message and try again.');
            } else if (response.status === 500) {
                errorMsg = '🔧 **Server Error**\n\nThere\'s a temporary issue with the AI service. Please try again in a few moments.';
            } else if (data.message) {
                // Use the specific error message from the server
                errorMsg = '⚠️ **Error**\n\n' + data.message;
            }
            
            setTimeout(() => {
                addMessageToChat(errorMsg, false);
            }, 500);
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        
        // Hide typing indicator
        document.getElementById('typingIndicator').style.display = 'none';
        
        // Re-enable send button
        document.getElementById('sendChatBtn').disabled = false;
        
        // Show error message with mode awareness
        const selectedMode = document.querySelector('input[name="chatMode"]:checked').value;
        let errorMsg = 'I\'m currently unable to connect. Please check your internet connection and try again.';
        
        if (selectedMode === 'authenticated' && error.message && error.message.includes('token')) {
            errorMsg = 'Authentication failed. Please try logging in again or switch to Anonymous mode.';
        }
        
        setTimeout(() => {
            addMessageToChat(errorMsg, false);
        }, 500);
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Function to check current rate limit status
async function checkRateLimitStatus() {
    try {
        const token = localStorage.getItem('jwt_token');
        const headers = {};
        
        // Include auth header if available for more detailed status
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('/api/ai/rate-limit-status', {
            headers: headers
        });
        
        if (response.ok) {
            const data = await response.json();
            const unauth = data.rate_limits.unauthenticated;
            const auth = data.rate_limits.authenticated;
            
            let statusMessage = `📊 **Current Rate Limit Status**\n\n`;
            statusMessage += `**Anonymous Mode:**\n`;
            statusMessage += `${unauth.requests_made}/${unauth.limit} requests used (${unauth.remaining || 0} remaining)\n\n`;
            
            if (data.authenticated_user) {
                statusMessage += `**Authenticated Mode (${data.authenticated_user.username}):**\n`;
                statusMessage += `User: ${auth.user_requests_made}/${auth.limit} requests used (${auth.user_remaining || 0} remaining)\n`;
                statusMessage += `IP: ${auth.ip_requests_made}/${auth.limit} requests used (${auth.ip_remaining || 0} remaining)\n\n`;
            } else {
                statusMessage += `**Authenticated Mode:**\n`;
                statusMessage += `Log in to see your authenticated rate limits\n\n`;
            }
            
            statusMessage += `Rate limits reset every ${unauth.window_hours} hours.`;
            
            addMessageToChat(statusMessage, false);
        } else {
            addMessageToChat('❌ Unable to check rate limit status. Please try again later.', false);
        }
    } catch (error) {
        console.error('Error checking rate limit status:', error);
        addMessageToChat('❌ Error checking rate limit status. Please try again later.', false);
    }
}

// Show notification badge when chat is closed (simulate new messages)
function showChatNotification() {
    if (!chatOpen) {
        const chatBadge = document.getElementById('chatBadge');
        chatBadge.style.display = 'flex';
    }
}

// Optional: Add some sample interactions for demo
function addWelcomeMessage() {
    if (chatHistory.length === 0) {
        const welcomeMsg = `Hi! I'm your AI banking assistant. How can I help you today?\n\n` +
            `💡 **Quick Tips:**\n` +
            `• Type **/help** for available commands\n` +
            `• Type **/status** to check your rate limits\n` +
            `• Switch between Anonymous (5 requests/3hrs) and Authenticated (10 requests/3hrs) modes above\n\n` +
            `Ask me about your account, transactions, or any banking questions!`;
        
        chatHistory.push({
            message: welcomeMsg,
            isUser: false,
            timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
        });
    }
}
