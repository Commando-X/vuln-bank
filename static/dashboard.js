// Global security configuration
let XSS_PROTECTION_ENABLED = false;

// Fetch security configuration
async function loadSecurityConfig() {
    try {
        const response = await fetch('/api/security-config');
        const data = await response.json();
        XSS_PROTECTION_ENABLED = data.xss_protection_enabled;
    } catch (error) {
        console.error('Failed to load security config:', error);
    }
}

// Safe HTML rendering helper
function safeSetContent(element, content, allowHTML = false) {
    if (XSS_PROTECTION_ENABLED || !allowHTML) {
        element.textContent = content;
    } else {
        element.innerHTML = content;
    }
}

function safeCreateHTML(htmlString) {
    if (XSS_PROTECTION_ENABLED) {
        const div = document.createElement('div');
        div.textContent = htmlString;
        return div.innerHTML;
    }
    return htmlString;
}

// Set current date
document.addEventListener('DOMContentLoaded', function() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const today = new Date();
    document.getElementById('current-date').textContent = today.toLocaleDateString('en-US', options);
});

// Vulnerability: Token stored in localStorage
document.addEventListener('DOMContentLoaded', async function() {
    await loadSecurityConfig();
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
    
    // Add virtual cards event listener
    document.getElementById('createCardForm').addEventListener('submit', handleCreateCard);
    
    // Load virtual cards
    fetchVirtualCards();

    // Add bill payment functions
    document.getElementById('payBillForm').addEventListener('submit', handleBillPayment);
    
    // Load initial data
    loadBillCategories();
    loadPaymentHistory();

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

// Transfer money handler
async function handleTransfer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = {};
    formData.forEach((value, key) => jsonData[key] = value);

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
            // Update message and balance
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'green';
            document.getElementById('balance').textContent = data.new_balance;
            
            // Refresh transactions
            fetchTransactions();
            
            // Clear form
            event.target.reset();
        } else {
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Transfer failed');
        document.getElementById('message').style.color = 'red';
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
            safeSetContent(document.getElementById('message'), 'Loan requested successfully, our staff will review and approve!');
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
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Loan request failed');
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
async function fetchTransactions() {
    try {
        const accountNumber = document.getElementById('account-number').textContent;
        const response = await fetch(`/transactions/${accountNumber}`, {
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('jwt_token')
            }
        });

        const data = await response.json();
        const transactionList = document.getElementById('transaction-list');

        if (data.status === 'success') {
            if (data.transactions.length === 0) {
                transactionList.innerHTML = '<p style="text-align: center; padding: 2rem;">No transactions found</p>';
                return;
            }

            if (XSS_PROTECTION_ENABLED) {
                transactionList.innerHTML = '';
                data.transactions.forEach(t => {
                    const isOutgoing = t.from_account === accountNumber;
                    const transactionType = isOutgoing ? 'sent' : 'received';

                    const transactionItem = document.createElement('div');
                    transactionItem.className = `transaction-item ${transactionType}`;

                    const detailsDiv = document.createElement('div');
                    detailsDiv.className = 'transaction-details';

                    const accountDiv = document.createElement('div');
                    accountDiv.className = 'transaction-account';
                    accountDiv.textContent = isOutgoing ? 'To: ' + t.to_account : 'From: ' + t.from_account;
                    detailsDiv.appendChild(accountDiv);

                    const dateDiv = document.createElement('div');
                    dateDiv.className = 'transaction-date';
                    dateDiv.textContent = t.timestamp;
                    detailsDiv.appendChild(dateDiv);

                    if (t.description) {
                        const descDiv = document.createElement('div');
                        descDiv.className = 'transaction-description';
                        descDiv.textContent = t.description;
                        detailsDiv.appendChild(descDiv);
                    }

                    const amountDiv = document.createElement('div');
                    amountDiv.className = `transaction-amount ${transactionType}`;
                    amountDiv.textContent = `${isOutgoing ? '-' : '+'}$${Math.abs(t.amount)}`;

                    transactionItem.appendChild(detailsDiv);
                    transactionItem.appendChild(amountDiv);
                    transactionList.appendChild(transactionItem);
                });
            } else {
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

                transactionList.innerHTML = transactionHtml;
            }
        } else {
            transactionList.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading transactions</p>';
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

    if (XSS_PROTECTION_ENABLED) {
        container.innerHTML = '';
        virtualCards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `virtual-card ${card.is_frozen ? 'frozen' : ''}`;
            cardDiv.id = `card-${card.id}`;

            const cardType = document.createElement('div');
            cardType.className = 'card-type';
            cardType.textContent = card.card_type.toUpperCase();
            cardDiv.appendChild(cardType);

            const cardNumber = document.createElement('div');
            cardNumber.className = 'card-number';
            cardNumber.textContent = formatCardNumber(card.card_number);
            cardDiv.appendChild(cardNumber);

            const cardDetails = document.createElement('div');
            cardDetails.className = 'card-details';

            const expDiv = document.createElement('div');
            expDiv.textContent = `Exp: ${card.expiry_date}`;
            cardDetails.appendChild(expDiv);

            const cvvDiv = document.createElement('div');
            cvvDiv.textContent = `CVV: ${card.cvv}`;
            cardDetails.appendChild(cvvDiv);
            cardDiv.appendChild(cardDetails);

            const limitDiv = document.createElement('div');
            limitDiv.textContent = `Limit: $${card.limit}`;
            cardDiv.appendChild(limitDiv);

            const balanceDiv = document.createElement('div');
            balanceDiv.textContent = `Balance: $${card.balance}`;
            cardDiv.appendChild(balanceDiv);

            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'card-actions';

            const freezeBtn = document.createElement('button');
            freezeBtn.textContent = card.is_frozen ? 'Unfreeze' : 'Freeze';
            freezeBtn.onclick = () => toggleCardFreeze(card.id);
            actionsDiv.appendChild(freezeBtn);

            const detailsBtn = document.createElement('button');
            detailsBtn.textContent = 'Details';
            detailsBtn.onclick = () => showCardDetails(card.id);
            actionsDiv.appendChild(detailsBtn);

            const historyBtn = document.createElement('button');
            historyBtn.textContent = 'History';
            historyBtn.onclick = () => showTransactionHistory(card.id);
            actionsDiv.appendChild(historyBtn);

            const limitBtn = document.createElement('button');
            limitBtn.textContent = 'Update Limit';
            limitBtn.onclick = () => showUpdateLimit(card.id);
            actionsDiv.appendChild(limitBtn);

            cardDiv.appendChild(actionsDiv);
            container.appendChild(cardDiv);
        });
    } else {
        container.innerHTML = virtualCards.map(card => `
            <div class="virtual-card ${card.is_frozen ? 'frozen' : ''}" id="card-${card.id}">
                <div class="card-type">${card.card_type.toUpperCase()}</div>
                <div class="card-number">${formatCardNumber(card.card_number)}</div>
                <div class="card-details">
                    <div>Exp: ${card.expiry_date}</div>
                    <div>CVV: ${card.cvv}</div>
                </div>
                <div>Limit: $${card.limit}</div>
                <div>Balance: $${card.balance}</div>
                <div class="card-actions">
                    <button onclick="toggleCardFreeze(${card.id})">${card.is_frozen ? 'Unfreeze' : 'Freeze'}</button>
                    <button onclick="showCardDetails(${card.id})">Details</button>
                    <button onclick="showTransactionHistory(${card.id})">History</button>
                    <button onclick="showUpdateLimit(${card.id})">Update Limit</button>
                </div>
            </div>
        `).join('');
    }
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
            
            safeSetContent(document.getElementById('message'), 'Virtual card created successfully!');
            document.getElementById('message').style.color = 'green';
        } else {
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Failed to create virtual card');
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
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Failed to freeze/unfreeze card');
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
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Failed to load transaction history');
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
            safeSetContent(document.getElementById('message'), 'Card limit updated successfully');
            document.getElementById('message').style.color = 'green';
        } else {
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Error updating card limit');
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

            if (XSS_PROTECTION_ENABLED) {
                select.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select Category';
                select.appendChild(defaultOption);

                data.categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.name;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = `
                    <option value="">Select Category</option>
                    ${data.categories.map(cat => `
                        <option value="${cat.id}">${cat.name}</option>
                    `).join('')}
                `;
            }
        }
    } catch (error) {
        console.error('Error loading bill categories:', error);
    }
}

// Load billers for selected category
async function loadBillers(categoryId) {
    const select = document.getElementById('biller');

    if (!categoryId) {
        select.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Select Biller';
        select.appendChild(option);
        select.disabled = true;
        return;
    }

    try {
        const response = await fetch(`/api/billers/by-category/${categoryId}`);
        const data = await response.json();

        if (data.status === 'success') {
            const billerMap = new Map();
            data.billers.forEach(biller => {
                if (!billerMap.has(biller.name)) {
                    billerMap.set(biller.name, biller);
                }
            });

            const uniqueBillers = Array.from(billerMap.values());
            uniqueBillers.sort((a, b) => a.name.localeCompare(b.name));

            if (XSS_PROTECTION_ENABLED) {
                select.innerHTML = '';
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select Biller';
                select.appendChild(defaultOption);

                uniqueBillers.forEach(biller => {
                    const option = document.createElement('option');
                    option.value = biller.id;
                    option.setAttribute('data-min', biller.minimum_amount);
                    option.setAttribute('data-max', biller.maximum_amount || '');
                    option.textContent = biller.name;
                    select.appendChild(option);
                });
            } else {
                select.innerHTML = `
                    <option value="">Select Biller</option>
                    ${uniqueBillers.map(biller => `
                        <option value="${biller.id}"
                                data-min="${biller.minimum_amount}"
                                data-max="${biller.maximum_amount || ''}"
                        >${biller.name}</option>
                    `).join('')}
                `;
            }
            select.disabled = false;
        } else {
            select.innerHTML = '';
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No billers available';
            select.appendChild(option);
            select.disabled = true;
        }
    } catch (error) {
        console.error('Error loading billers:', error);
        select.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error loading billers';
        select.appendChild(option);
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
            safeSetContent(document.getElementById('message'), 'Bill payment successful!');
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
            safeSetContent(document.getElementById('message'), data.message);
            document.getElementById('message').style.color = 'red';
        }
    } catch (error) {
        safeSetContent(document.getElementById('message'), 'Payment failed');
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
