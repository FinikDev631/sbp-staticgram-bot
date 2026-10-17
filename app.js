/**
 * SBP StaticGram Stars Bank • Material Design 3 Web App
 * Interactive dashboard logic & Telegram WebApp bindings
 */

// --- Global Application State ---
const State = {
  balance: 1500,
  escrow: 50,
  isBalanceHidden: false,
  accountNumber: 'СБП-4264-9445',
  currentFilter: 'all',
  activeReceipt: null,
  transactions: [
    {
      id: 'SBP-TRX-20261017-9B41',
      type: 'transfer',
      title: 'Исходящий перевод',
      amount: -1500,
      status: 'Исполнен',
      date: 'Сегодня, 15:53',
      from: 'Ваш счёт',
      to: 'СБП-7721-3091',
      comment: 'Перевод через СБП'
    },
    {
      id: 'SBP-DEP-20261017-A91D',
      type: 'deposit',
      title: 'Пополнение счёта Stars',
      amount: 1500,
      status: 'Исполнен',
      date: 'Сегодня, 15:20',
      from: 'Telegram Stars Gateway',
      to: 'Ваш счёт',
      comment: 'Пополнение баланса без комиссии'
    },
    {
      id: 'SBP-CHK-20261017-CH50',
      type: 'cheque',
      title: 'Создание чека в чат',
      amount: -50,
      status: 'В резерве (Escrow)',
      date: 'Сегодня, 14:10',
      from: 'Ваш счёт',
      to: 'Чек для любого участника',
      comment: 'СБП бонусный чек'
    }
  ]
};

// --- Telegram WebApp SDK Initialization ---
const tg = window.Telegram?.WebApp;

function initTelegram() {
  if (!tg) return;

  try {
    tg.ready();
    tg.expand();

    if (tg.setHeaderColor) tg.setHeaderColor('#F6F2ED');
    if (tg.setBackgroundColor) tg.setBackgroundColor('#F6F2ED');

    const user = tg.initDataUnsafe?.user;
    if (user) {
      const greetingEl = document.getElementById('userGreeting');
      if (greetingEl) {
        greetingEl.textContent = user.first_name ? `Привет, ${user.first_name}!` : 'Личный кабинет';
      }

      if (user.id) {
        const idStr = String(user.id);
        const p1 = idStr.length >= 4 ? idStr.slice(0, 4) : idStr.padStart(4, '0');
        const p2 = idStr.length >= 8 ? idStr.slice(-4) : idStr.padStart(4, '9');
        State.accountNumber = `СБП-${p1}-${p2}`;
        const accEl = document.getElementById('accountNumberDisplay');
        if (accEl) accEl.textContent = State.accountNumber;
      }
    }
  } catch (err) {
    console.debug('Telegram notice:', err);
  }
}

function haptic(type = 'light') {
  try {
    if (tg?.HapticFeedback) {
      if (type === 'success' || type === 'error') {
        tg.HapticFeedback.notificationOccurred(type);
      } else {
        tg.HapticFeedback.impactOccurred(type);
      }
    }
  } catch (e) {}
}

// --- Toast Snackbar Notification ---
let toastTimer = null;
function showToast(message, duration = 3000) {
  const toast = document.getElementById('appToast');
  if (!toast) return;

  toast.textContent = message;
  toast.classList.add('show');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

// --- Balance Display & Toggle ---
function updateBalanceUI() {
  const valEl = document.getElementById('balanceValue');
  if (valEl) {
    valEl.textContent = State.isBalanceHidden ? '••••••' : State.balance.toLocaleString('ru-RU');
  }

  const escrowEl = document.getElementById('escrowTotal');
  if (escrowEl) {
    escrowEl.textContent = `${State.escrow.toLocaleString('ru-RU')} ⭐️`;
  }
}

function initBalanceToggle() {
  const btn = document.getElementById('btnToggleBalance');
  if (!btn) return;

  btn.addEventListener('click', () => {
    haptic('light');
    State.isBalanceHidden = !State.isBalanceHidden;
    updateBalanceUI();

    btn.innerHTML = State.isBalanceHidden
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
  });
}

// --- Account Number Copy ---
function initAccountCopy() {
  const badge = document.getElementById('accountBadge');
  if (!badge) return;

  badge.addEventListener('click', async () => {
    haptic('medium');
    try {
      await navigator.clipboard.writeText(State.accountNumber);
      showToast(`Номер счёта скопирован: ${State.accountNumber}`);
    } catch (e) {
      showToast(`Ваш счёт: ${State.accountNumber}`);
    }
  });
}

// --- Modals Management ---
window.openModal = function(id) {
  haptic('light');
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
};

window.closeModal = function(id) {
  haptic('light');
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
};

function initModals() {
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) backdrop.classList.remove('active');
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(m => m.classList.remove('active'));
    }
  });

  // Action Buttons
  document.getElementById('btnActionTransfer')?.addEventListener('click', () => openModal('modalTransfer'));
  document.getElementById('btnActionDeposit')?.addEventListener('click', () => openModal('modalDeposit'));
  document.getElementById('btnActionWithdraw')?.addEventListener('click', () => {
    haptic('medium');
    openModal('modalTransfer');
    showToast('Укажите реквизиты для вывода звёзд');
  });
  document.getElementById('btnActionCheque')?.addEventListener('click', () => openModal('modalCheque'));

  document.getElementById('btnFilterCheques')?.addEventListener('click', () => {
    filterTransactions('cheque');
    const hist = document.querySelector('.history-card');
    if (hist) hist.scrollIntoView({ behavior: 'smooth' });
  });
}

// Quick amount chips for transfer
window.setTransferAmount = function(val) {
  haptic('light');
  const input = document.getElementById('transferAmount');
  if (input) input.value = val;
};

// Deposit triggers
window.triggerDeposit = function(amount) {
  haptic('success');
  State.balance += amount;

  const depId = `SBP-DEP-${Date.now().toString(36).toUpperCase()}`;
  State.transactions.unshift({
    id: depId,
    type: 'deposit',
    title: 'Пополнение счёта Stars',
    amount: amount,
    status: 'Исполнен',
    date: 'Только что',
    from: 'Telegram Stars',
    to: State.accountNumber,
    comment: 'Зачисление через шлюз Stars'
  });

  updateBalanceUI();
  renderTransactions();
  closeModal('modalDeposit');
  showToast(`Баланс успешно пополнен на +${amount} ⭐️!`);
};

// Submit Transfer
function initTransferSubmission() {
  const btn = document.getElementById('btnSubmitTransfer');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const recipient = document.getElementById('transferRecipient')?.value.trim();
    const amount = parseInt(document.getElementById('transferAmount')?.value, 10);
    const comment = document.getElementById('transferComment')?.value.trim() || 'Перевод по СБП';

    if (!recipient) {
      showToast('Укажите получателя (@username или номер счёта)');
      haptic('error');
      return;
    }

    if (!amount || amount <= 0) {
      showToast('Укажите корректную сумму');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast('Недостаточно звёзд на балансе');
      haptic('error');
      return;
    }

    haptic('success');
    State.balance -= amount;

    const trxId = `SBP-TRX-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;

    State.transactions.unshift({
      id: trxId,
      type: 'transfer',
      title: `Перевод получателю ${recipient}`,
      amount: -amount,
      status: 'Исполнен',
      date: 'Только что',
      from: State.accountNumber,
      to: recipient,
      comment: comment
    });

    updateBalanceUI();
    renderTransactions();
    closeModal('modalTransfer');

    document.getElementById('transferRecipient').value = '';
    document.getElementById('transferAmount').value = '';
    document.getElementById('transferComment').value = '';

    showToast(`Перевод ${amount} ⭐️ успешно отправлен!`);
  });
}

// Submit Cheque
function initChequeSubmission() {
  const targetSelect = document.getElementById('chequeTarget');
  const userGroup = document.getElementById('chequeTargetUserGroup');

  if (targetSelect && userGroup) {
    targetSelect.addEventListener('change', () => {
      userGroup.style.display = targetSelect.value === 'user' ? 'flex' : 'none';
    });
  }

  const btn = document.getElementById('btnSubmitCheque');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const amount = parseInt(document.getElementById('chequeAmount')?.value, 10);
    const targetType = document.getElementById('chequeTarget')?.value;
    const recipient = targetType === 'user' ? document.getElementById('chequeRecipient')?.value.trim() : 'Любой участник';
    const comment = document.getElementById('chequeComment')?.value.trim() || 'СБП бонус';

    if (!amount || amount <= 0) {
      showToast('Укажите номинал чека');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast('Недостаточно звёзд на балансе для резервирования чека');
      haptic('error');
      return;
    }

    haptic('success');
    State.balance -= amount;
    State.escrow += amount;

    const chkCode = `SBP-CHK-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

    State.transactions.unshift({
      id: chkCode,
      type: 'cheque',
      title: `Чек в чат (${chkCode})`,
      amount: -amount,
      status: 'В резерве (Escrow)',
      date: 'Только что',
      from: State.accountNumber,
      to: recipient,
      comment: comment
    });

    updateBalanceUI();
    renderTransactions();
    closeModal('modalCheque');

    showToast(`Чек #${chkCode} на ${amount} ⭐️ создан!`);
  });
}

// --- Electronic Receipt Details ---
window.openReceiptModal = function(txId) {
  haptic('light');
  const tx = State.transactions.find(t => t.id === txId);
  if (!tx) return;

  State.activeReceipt = tx;
  const content = document.getElementById('receiptContent');
  if (!content) return;

  const isPos = tx.amount > 0;
  const formatted = `${isPos ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} ⭐️`;

  content.innerHTML = `
    <div style="text-align: center; margin-bottom: 6px;">
      <div style="font-size: 28px; font-weight: 800; color: ${isPos ? 'var(--green-positive)' : 'var(--text-main)'};">
        ${formatted}
      </div>
      <div style="font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase;">
        ${tx.status}
      </div>
    </div>
    <div class="receipt-field">
      <span class="label">Номер чека</span>
      <span class="value" style="font-family: monospace;">#${tx.id}</span>
    </div>
    <div class="receipt-field">
      <span class="label">Отправитель</span>
      <span class="value">${tx.from}</span>
    </div>
    <div class="receipt-field">
      <span class="label">Получатель</span>
      <span class="value">${tx.to}</span>
    </div>
    <div class="receipt-field">
      <span class="label">Дата и время</span>
      <span class="value">${tx.date}</span>
    </div>
    <div class="receipt-field">
      <span class="label">Назначение платежа</span>
      <span class="value">${tx.comment}</span>
    </div>
    <div class="receipt-field">
      <span class="label">Платёжный шлюз</span>
      <span class="value">StaticGram СБП • Stars Gateway</span>
    </div>
  `;

  openModal('modalReceipt');
};

window.copyReceiptText = async function() {
  haptic('medium');
  if (!State.activeReceipt) return;

  const tx = State.activeReceipt;
  const text = `🧾 Электронный чек СБП\nСумма: ${tx.amount > 0 ? '+' : ''}${tx.amount} ⭐️\nСтатус: ${tx.status}\nНомер: #${tx.id}\nДата: ${tx.date}\nНазначение: ${tx.comment}`;

  try {
    await navigator.clipboard.writeText(text);
    showToast('Данные чека скопированы в буфер!');
  } catch (e) {
    showToast(`Чек #${tx.id}`);
  }
};

// --- History Filters & Rendering ---
function filterTransactions(type) {
  State.currentFilter = type;
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.classList.toggle('active', tab.getAttribute('data-filter') === type);
  });
  renderTransactions();
}

function renderTransactions() {
  const container = document.getElementById('transactionList');
  if (!container) return;

  const filtered = State.currentFilter === 'all'
    ? State.transactions
    : State.transactions.filter(t => t.type === State.currentFilter);

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-tertiary); font-size: 13px;">
        В этой категории пока нет операций
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(tx => {
    let iconClass = 'tx-cheque';
    let icon = '🧾';
    let amountClass = 'neutral';

    if (tx.type === 'transfer') {
      iconClass = 'tx-out';
      icon = '↗';
      amountClass = 'negative';
    } else if (tx.type === 'deposit') {
      iconClass = 'tx-in';
      icon = '↙';
      amountClass = 'positive';
    }

    const formatted = `${tx.amount > 0 ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} ⭐️`;

    return `
      <div class="tx-row" onclick="openReceiptModal('${tx.id}')">
        <div class="tx-left">
          <div class="tx-icon-circle ${iconClass}">${icon}</div>
          <div class="tx-meta">
            <span class="tx-name">${tx.title}</span>
            <span class="tx-sub">${tx.date} • ${tx.comment}</span>
          </div>
        </div>
        <div class="tx-right">
          <span class="tx-amount ${amountClass}">${formatted}</span>
          <span class="tx-status-badge">${tx.status}</span>
        </div>
      </div>
    `;
  }).join('');
}

function initFilters() {
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      haptic('light');
      filterTransactions(tab.getAttribute('data-filter'));
    });
  });
}

// --- App Bootstrap ---
document.addEventListener('DOMContentLoaded', () => {
  initTelegram();
  initBalanceToggle();
  initAccountCopy();
  initModals();
  initTransferSubmission();
  initChequeSubmission();
  initFilters();
  updateBalanceUI();
  renderTransactions();
});
