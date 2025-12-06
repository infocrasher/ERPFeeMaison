/**
 * Shop Dashboard JavaScript
 * Handles modals, payments, and employee selection
 */

// --- Employee Selection Modal Logic ---

let employeeModal = null;

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap modal
    const modalEl = document.getElementById('employeeSelectionModal');
    if (modalEl) {
        employeeModal = new bootstrap.Modal(modalEl);
    }
});

/**
 * Opens the employee selection modal for a specific order
 * @param {string} orderId - The ID of the order
 * @param {string} statusType - 'ready_at_shop' or 'completed' (not strictly used for URL but good for context)
 */
function openEmployeeModal(orderId, statusType) {
    const form = document.getElementById('employeeSelectionForm');
    const confirmBtn = document.getElementById('confirmEmployeeBtn');

    // Reset form
    form.reset();
    document.querySelectorAll('.employee-checkbox-card').forEach(card => {
        card.classList.remove('selected');
    });
    confirmBtn.disabled = true;

    // Set form action URL
    // Route: /orders/<order_id>/change-status-to-ready
    form.action = `/orders/${orderId}/change-status-to-ready`;

    // Show modal
    if (employeeModal) {
        employeeModal.show();
    }
}

/**
 * Toggles the visual state of an employee card when checkbox changes
 * @param {HTMLInputElement} checkbox - The checkbox element
 */
function toggleEmployeeCard(checkbox) {
    const card = document.getElementById(`card_emp_${checkbox.value}`);
    const confirmBtn = document.getElementById('confirmEmployeeBtn');

    if (checkbox.checked) {
        card.classList.add('selected');
    } else {
        card.classList.remove('selected');
    }

    // Check if at least one employee is selected
    const anySelected = document.querySelector('input[name="employee_ids[]"]:checked');
    confirmBtn.disabled = !anySelected;
}


// --- Payment Modal Logic (Existing) ---

document.addEventListener('DOMContentLoaded', function () {
    const paymentModalEl = document.getElementById('paymentModal');
    if (!paymentModalEl) return;

    const paymentModal = new bootstrap.Modal(paymentModalEl);
    const amountInput = document.getElementById('paymentAmountInput');
    const confirmBtn = document.getElementById('paymentModalConfirm');

    // Display elements
    const totalDisplay = document.getElementById('paymentModalTotal');
    const paidDisplay = document.getElementById('paymentModalPaid');
    const balanceDisplay = document.getElementById('paymentModalBalance');
    const balanceAfterDisplay = document.getElementById('paymentModalBalanceAfter');
    const changeDisplay = document.getElementById('paymentModalChange');

    let currentOrder = null;

    // Open modal triggers
    document.querySelectorAll('.shop-pay-trigger').forEach(btn => {
        btn.addEventListener('click', function () {
            const form = this.closest('.shop-pay-form');
            currentOrder = {
                id: form.dataset.orderId,
                total: parseFloat(form.dataset.total),
                paid: parseFloat(form.dataset.paid),
                balance: parseFloat(form.dataset.balance),
                form: form
            };

            // Update UI
            totalDisplay.textContent = formatMoney(currentOrder.total);
            paidDisplay.textContent = formatMoney(currentOrder.paid);
            balanceDisplay.textContent = formatMoney(currentOrder.balance);

            // Reset input
            amountInput.value = '';
            updateCalculations(0);

            paymentModal.show();

            // Focus input after modal opens
            setTimeout(() => amountInput.focus(), 500);
        });
    });

    // Input changes
    amountInput.addEventListener('input', function () {
        updateCalculations(parseFloat(this.value) || 0);
    });

    // Confirm payment
    confirmBtn.addEventListener('click', function () {
        const amount = parseFloat(amountInput.value);
        if (!amount || amount <= 0) {
            alert('Veuillez entrer un montant valide');
            return;
        }

        // Update hidden input in the original form
        const hiddenInput = currentOrder.form.querySelector('input[name="amount_received"]');
        hiddenInput.value = amount;

        // Submit the form
        currentOrder.form.submit();
        paymentModal.hide();
    });

    function updateCalculations(amountReceived) {
        if (!currentOrder) return;

        const newBalance = currentOrder.balance - amountReceived;

        if (newBalance > 0) {
            balanceAfterDisplay.textContent = formatMoney(newBalance);
            balanceAfterDisplay.className = 'text-danger fw-bold';
            changeDisplay.textContent = '0.00 DA';
        } else {
            balanceAfterDisplay.textContent = '0.00 DA';
            balanceAfterDisplay.className = 'text-success fw-bold';
            changeDisplay.textContent = formatMoney(Math.abs(newBalance));
        }
    }

    function formatMoney(amount) {
        return amount.toFixed(2) + ' DA';
    }
});
