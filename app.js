/**
 * SBP StaticGram Stars Bank тАв Material Design 3 Web App
 * Fully Connected Real API & Telegram WebApp bindings (NO fake data)
 */

// --- Dynamic API Base URL ---
const API_BASE = window.location.origin.includes('github.io')
  ? 'https://sbp-staticgram-bot.onrender.com'
  : '';

// --- Global Application State (Zero fake info) ---
const State = {
  user: null,
  userId: null,
  username: null,
  firstName: null,
  balance: 0,
  escrow: 0,
  isBalanceHidden: false,
  accountNumber: 'тАФ',
  currentFilter: 'all',
  activeReceipt: null,
  transactions: [],
  isGuest: false,
  isLoading: true
};

// --- Telegram WebApp SDK Initialization ---
const tg = window.Telegram?.WebApp;

function initTelegram() {
  if (tg) {
    try {
      tg.ready();
      tg.expand();
      if (tg.setHeaderColor) tg.setHeaderColor('#F6F2ED');
      if (tg.setBackgroundColor) tg.setBackgroundColor('#F6F2ED');
    } catch (e) {
      console.debug('Telegram WebApp setup notice:', e);
    }
  }

  // Detect user from Telegram initDataUnsafe or URL parameters
  const tgUser = tg?.initDataUnsafe?.user;
  const urlParams = new URLSearchParams(window.location.search);

  if (tgUser && tgUser.id) {
    State.userId = tgUser.id;
    State.username = tgUser.username || null;
    State.firstName = tgUser.first_name || '╨Ъ╨╗╨╕╨╡╨╜╤В';
  } else if (urlParams.get('user_id')) {
    State.userId = parseInt(urlParams.get('user_id'), 10);
    State.username = urlParams.get('username') || null;
    State.firstName = urlParams.get('first_name') || '╨Ъ╨╗╨╕╨╡╨╜╤В';
  }

  fetchUserData();
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

// --- Fetch Real User Data & Transactions from Database ---
async function fetchUserData() {
  const greetingEl = document.getElementById('userGreeting');
  const subtextEl = document.getElementById('userSubtext');
  const accountEl = document.getElementById('accountNumberDisplay');

  if (!State.userId) {
    // Visitor opened app directly in a web browser outside Telegram
    State.isGuest = true;
    State.isLoading = false;
    State.balance = 0;
    State.escrow = 0;
    State.accountNumber = '╨Э╨╡ ╨░╨▓╤В╨╛╤А╨╕╨╖╨╛╨▓╨░╨╜';

    if (greetingEl) greetingEl.textContent = '╨У╨╛╤Б╤В╨╡╨▓╨╛╨╣ ╤А╨╡╨╢╨╕╨╝';
    if (subtextEl) subtextEl.textContent = '╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╤З╨╡╤А╨╡╨╖ Telegram ╨▒╨╛╤В╨░ @sbpbot';
    if (accountEl) accountEl.textContent = '╨Э╨╡ ╨┐╨╛╨┤╨║╨╗╤О╤З╤С╨╜';

    updateBalanceUI();
    renderTransactions();
    return;
  }

  try {
    const query = new URLSearchParams({
      user_id: String(State.userId),
      username: State.username || '',
      first_name: State.firstName || ''
    });

    const res = await fetch(`${API_BASE}/api/user_data?${query.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.status === 'ok' && data.user) {
      State.user = data.user;
      State.balance = data.user.balance || 0;
      State.escrow = data.user.reserved || 0;
      State.accountNumber = data.user.account_number || 'тАФ';
      State.transactions = data.transactions || [];
      State.isGuest = false;
      State.isLoading = false;

      if (greetingEl) {
        greetingEl.textContent = data.user.first_name ? `╨Я╤А╨╕╨▓╨╡╤В, ${data.user.first_name}!` : '╨Ы╨╕╤З╨╜╤Л╨╣ ╨║╨░╨▒╨╕╨╜╨╡╤В';
      }
      if (subtextEl) {
        subtextEl.textContent = data.user.username ? `@${data.user.username} тАв ╨б╨╡╤В╤М ╨░╨║╤В╨╕╨▓╨╜╨░` : `ID ${data.user.user_id} тАв ╨б╨╡╤В╤М ╨░╨║╤В╨╕╨▓╨╜╨░`;
      }
      if (accountEl) {
        accountEl.textContent = State.accountNumber;
      }

      updateBalanceUI();
      renderTransactions();
    }
  } catch (err) {
    console.error('Failed to fetch real user data:', err);
    State.isLoading = false;
    if (subtextEl) subtextEl.textContent = '╨б╨▓╤П╨╖╤М ╤Б ╨┐╨╗╨░╤В╤С╨╢╨╜╤Л╨╝ ╤И╨╗╤О╨╖╨╛╨╝ ╤Г╤Б╤В╨░╨╜╨░╨▓╨╗╨╕╨▓╨░╨╡╤В╤Б╤П...';
    renderTransactions();
  }
}

// --- Toast Snackbar Notification ---
let toastTimer = null;
function showToast(message, duration = 3500) {
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
    valEl.textContent = State.isBalanceHidden ? 'тАвтАвтАвтАвтАвтАв' : State.balance.toLocaleString('ru-RU');
  }

  const escrowStrip = document.getElementById('escrowStrip');
  const escrowEl = document.getElementById('escrowTotal');
  if (escrowEl) {
    escrowEl.textContent = `${State.escrow.toLocaleString('ru-RU')} тнРя╕П`;
  }
  if (escrowStrip) {
    escrowStrip.style.display = State.escrow > 0 ? 'flex' : 'none';
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
    if (State.isGuest || State.accountNumber === 'тАФ') {
      showToast('╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ ╨▓ Telegram ╨┤╨╗╤П ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╤Б╤З╤С╤В╨░');
      return;
    }
    try {
      await navigator.clipboard.writeText(State.accountNumber);
      showToast(`╨Э╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜: ${State.accountNumber}`);
    } catch (e) {
      showToast(`╨Т╨░╤И ╤Б╤З╤С╤В: ${State.accountNumber}`);
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
  document.getElementById('btnActionTransfer')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast('╨Ф╨╗╤П ╨╛╤В╨┐╤А╨░╨▓╨║╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot');
      return;
    }
    openModal('modalTransfer');
  });

  document.getElementById('btnActionDeposit')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast('╨Ф╨╗╤П ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П ╨▒╨░╨╗╨░╨╜╤Б╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot');
      return;
    }
    openModal('modalDeposit');
  });

  document.getElementById('btnActionWithdraw')?.addEventListener('click', () => {
    openModal('modalWithdraw');
  });

  document.getElementById('btnActionCheque')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast('╨Ф╨╗╤П ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╤З╨╡╨║╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot');
      return;
    }
    openModal('modalCheque');
  });

  document.getElementById('btnFilterCheques')?.addEventListener('click', () => {
    filterTransactions('cheque');
    const hist = document.querySelector('.history-card');
    if (hist) hist.scrollIntoView({ behavior: 'smooth' });
  });

  // Cheque result actions
  document.getElementById('btnCopyChequeLink')?.addEventListener('click', async () => {
    haptic('medium');
    const url = document.getElementById('createdChequeUrl')?.value;
    if (url) {
      try {
        await navigator.clipboard.writeText(url);
        showToast('╨б╤Б╤Л╨╗╨║╨░ ╨╜╨░ ╤З╨╡╨║ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜╨░ ╨▓ ╨▒╤Г╤Д╨╡╤А ╨╛╨▒╨╝╨╡╨╜╨░!');
      } catch (e) {
        showToast('╨б╨║╨╛╨┐╨╕╤А╤Г╨╣╤В╨╡ ╤Б╤Б╤Л╨╗╨║╤Г ╨▓╤А╤Г╤З╨╜╤Г╤О');
      }
    }
  });

  document.getElementById('btnShareChequeLink')?.addEventListener('click', () => {
    haptic('light');
    const url = document.getElementById('createdChequeUrl')?.value;
    if (url) {
      const shareUrl = `https://staticgram.top/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent('тЪбя╕П ╨Р╨║╤В╨╕╨▓╨╕╤А╤Г╨╣╤В╨╡ ╤З╨╡╨║ ╨б╨С╨Я!')}`;
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(shareUrl);
      } else {
        window.open(shareUrl, '_blank');
      }
    }
  });
}

// Quick amount chips for transfer
window.setTransferAmount = function(val) {
  haptic('light');
  const input = document.getElementById('transferAmount');
  if (input) input.value = val;
};

// --- Deposit Trigger (Real Telegram Stars Invoice) ---
window.triggerDeposit = async function(amount) {
  haptic('medium');
  if (State.isGuest) {
    showToast('╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot ╨┤╨╗╤П ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П');
    return;
  }

  showToast(`╨Ч╨░╨┐╤А╨╛╤Б ╤Б╤З╤С╤В╨░ ╨╜╨░ ${amount} тнРя╕П...`);

  try {
    const res = await fetch(`${API_BASE}/api/create_invoice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: State.userId,
        amount: amount
      })
    });

    const data = await res.json();
    closeModal('modalDeposit');

    if (data.invoice_link) {
      if (tg?.openInvoice) {
        tg.openInvoice(data.invoice_link, (status) => {
          if (status === 'paid') {
            haptic('success');
            showToast(`╨С╨░╨╗╨░╨╜╤Б ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜ ╨╜╨░ +${amount} тнРя╕П!`);
            fetchUserData();
          }
        });
      } else {
        window.open(data.invoice_link, '_blank');
      }
    } else if (data.bot_url) {
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(data.bot_url);
      } else {
        window.open(data.bot_url, '_blank');
      }
      showToast('╨б╤З╤С╤В ╨▓╤Л╤Б╤В╨░╨▓╨╗╨╡╨╜! ╨Я╨╡╤А╨╡╨╣╨┤╨╕╤В╨╡ ╨▓ ╨┤╨╕╨░╨╗╨╛╨│ ╤Б ╨▒╨╛╤В╨╛╨╝ ╨┤╨╗╤П ╨╛╨┐╨╗╨░╤В╤Л.');
    }
  } catch (e) {
    console.error('Deposit invoice error:', e);
    showToast('╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╤Д╨╛╤А╨╝╨╕╤А╨╛╨▓╨░╤В╤М ╤Б╤З╤С╤В. ╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ /deposit ╨▓ ╨▒╨╛╤В╨╡.');
  }
};

// --- Submit Transfer (Real PostgreSQL Execution) ---
function initTransferSubmission() {
  const btn = document.getElementById('btnSubmitTransfer');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const recipient = document.getElementById('transferRecipient')?.value.trim();
    const amount = parseInt(document.getElementById('transferAmount')?.value, 10);
    const comment = document.getElementById('transferComment')?.value.trim() || '╨Я╨╡╤А╨╡╨▓╨╛╨┤ ╨┐╨╛ ╨б╨С╨Я';

    if (!recipient) {
      showToast('╨г╨║╨░╨╢╨╕╤В╨╡ ╨┐╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤П (@username, ID ╨╕╨╗╨╕ ╨╜╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░)');
      haptic('error');
      return;
    }

    if (!amount || amount <= 0) {
      showToast('╨г╨║╨░╨╢╨╕╤В╨╡ ╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Г╤О ╤Б╤Г╨╝╨╝╤Г');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast(`╨Э╨╡╨┤╨╛╤Б╤В╨░╤В╨╛╤З╨╜╨╛ ╨╖╨▓╤С╨╖╨┤. ╨Т╨░╤И ╨▒╨░╨╗╨░╨╜╤Б: ${State.balance} тнРя╕П`);
      haptic('error');
      return;
    }

    btn.disabled = true;
    btn.textContent = '╨Ю╤В╨┐╤А╨░╨▓╨║╨░...';

    try {
      const res = await fetch(`${API_BASE}/api/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: State.userId,
          recipient: recipient,
          amount: amount,
          comment: comment
        })
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        haptic('error');
        showToast(data.error || '╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░');
        btn.disabled = false;
        btn.textContent = '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╤М ╨┐╨╡╤А╨╡╨▓╨╛╨┤';
        return;
      }

      haptic('success');
      closeModal('modalTransfer');
      document.getElementById('transferRecipient').value = '';
      document.getElementById('transferAmount').value = '';
      document.getElementById('transferComment').value = '';

      showToast(data.message || `╨Я╨╡╤А╨╡╨▓╨╛╨┤ ${amount} тнРя╕П ╨╛╤В╨┐╤А╨░╨▓╨╗╨╡╨╜!`);
      await fetchUserData();

    } catch (e) {
      haptic('error');
      showToast('╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╡╤В╨╕ ╨┐╤А╨╕ ╨╛╤В╨┐╤А╨░╨▓╨║╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░');
    } finally {
      btn.disabled = false;
      btn.textContent = '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╤М ╨┐╨╡╤А╨╡╨▓╨╛╨┤';
    }
  });
}

// --- Submit Cheque (Real PostgreSQL Execution) ---
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

  btn.addEventListener('click', async () => {
    const amount = parseInt(document.getElementById('chequeAmount')?.value, 10);
    const targetType = document.getElementById('chequeTarget')?.value;
    const recipient = targetType === 'user' ? document.getElementById('chequeRecipient')?.value.trim() : null;
    const comment = document.getElementById('chequeComment')?.value.trim() || '╨б╨С╨Я ╨▒╨╛╨╜╤Г╤Б';

    if (!amount || amount <= 0) {
      showToast('╨г╨║╨░╨╢╨╕╤В╨╡ ╨╜╨╛╨╝╨╕╨╜╨░╨╗ ╤З╨╡╨║╨░');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast('╨Э╨╡╨┤╨╛╤Б╤В╨░╤В╨╛╤З╨╜╨╛ ╨╖╨▓╤С╨╖╨┤ ╨╜╨░ ╨▒╨░╨╗╨░╨╜╤Б╨╡ ╨┤╨╗╤П ╤А╨╡╨╖╨╡╤А╨▓╨╕╤А╨╛╨▓╨░╨╜╨╕╤П ╤З╨╡╨║╨░');
      haptic('error');
      return;
    }

    if (targetType === 'user' && !recipient) {
      showToast('╨г╨║╨░╨╢╨╕╤В╨╡ @username ╨┐╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤П');
      haptic('error');
      return;
    }

    btn.disabled = true;
    btn.textContent = '╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡...';

    try {
      const res = await fetch(`${API_BASE}/api/create_cheque`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: State.userId,
          amount: amount,
          recipient: recipient,
          comment: comment
        })
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        haptic('error');
        showToast(data.error || '╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╤З╨╡╨║');
        btn.disabled = false;
        btn.textContent = '╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤З╨╡╨║';
        return;
      }

      haptic('success');
      closeModal('modalCheque');
      document.getElementById('chequeAmount').value = '';
      if (document.getElementById('chequeRecipient')) document.getElementById('chequeRecipient').value = '';

      const urlInput = document.getElementById('createdChequeUrl');
      if (urlInput) urlInput.value = data.cheque_url;

      openModal('modalChequeResult');
      await fetchUserData();

    } catch (e) {
      haptic('error');
      showToast('╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╡╤В╨╕ ╨┐╤А╨╕ ╤Б╨╛╨╖╨┤╨░╨╜╨╕╨╕ ╤З╨╡╨║╨░');
    } finally {
      btn.disabled = false;
      btn.textContent = '╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤З╨╡╨║';
    }
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
  const formatted = `${isPos ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} тнРя╕П`;

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
      <span class="label">╨Э╨╛╨╝╨╡╤А ╨║╨▓╨╕╤В╨░╨╜╤Ж╨╕╨╕</span>
      <span class="value" style="font-family: monospace;">#${tx.id}</span>
    </div>
    <div class="receipt-field">
      <span class="label">╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╨╡╨╗╤М</span>
      <span class="value">${tx.from}</span>
    </div>
    <div class="receipt-field">
      <span class="label">╨Я╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤М</span>
      <span class="value">${tx.to}</span>
    </div>
    <div class="receipt-field">
      <span class="label">╨Ф╨░╤В╨░ ╨╕ ╨▓╤А╨╡╨╝╤П</span>
      <span class="value">${tx.date}</span>
    </div>
    <div class="receipt-field">
      <span class="label">╨Э╨░╨╖╨╜╨░╤З╨╡╨╜╨╕╨╡ ╨┐╨╗╨░╤В╨╡╨╢╨░</span>
      <span class="value">${tx.comment}</span>
    </div>
    <div class="receipt-field">
      <span class="label">╨Я╨╗╨░╤В╤С╨╢╨╜╤Л╨╣ ╤И╨╗╤О╨╖</span>
      <span class="value">StaticGram ╨б╨С╨Я тАв Stars Gateway</span>
    </div>
  `;

  openModal('modalReceipt');
};

window.copyReceiptText = async function() {
  haptic('medium');
  if (!State.activeReceipt) return;

  const tx = State.activeReceipt;
  const text = `ЁЯз╛ ╨н╨╗╨╡╨║╤В╤А╨╛╨╜╨╜╤Л╨╣ ╤З╨╡╨║ ╨б╨С╨Я\n╨б╤Г╨╝╨╝╨░: ${tx.amount > 0 ? '+' : ''}${tx.amount} тнРя╕П\n╨б╤В╨░╤В╤Г╤Б: ${tx.status}\n╨Э╨╛╨╝╨╡╤А: #${tx.id}\n╨Ф╨░╤В╨░: ${tx.date}\n╨Э╨░╨╖╨╜╨░╤З╨╡╨╜╨╕╨╡: ${tx.comment}`;

  try {
    await navigator.clipboard.writeText(text);
    showToast('╨Ф╨░╨╜╨╜╤Л╨╡ ╤З╨╡╨║╨░ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜╤Л ╨▓ ╨▒╤Г╤Д╨╡╤А!');
  } catch (e) {
    showToast(`╨з╨╡╨║ #${tx.id}`);
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

  if (State.isLoading) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-tertiary); font-size: 13px;">
        ╨Ч╨░╨│╤А╤Г╨╖╨║╨░ ╨╛╨┐╨╡╤А╨░╤Ж╨╕╨╣...
      </div>
    `;
    return;
  }

  if (State.isGuest) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-secondary); font-size: 13px;">
        <div style="font-size: 32px; margin-bottom: 8px;">ЁЯФР</div>
        <b>╨Я╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╨╛╤В╨║╤А╤Л╤В╨╛ ╨▓ ╤А╨╡╨╢╨╕╨╝╨╡ ╨┐╤А╨╛╤Б╨╝╨╛╤В╤А╨░</b><br>
        ╨Ф╨╗╤П ╤Г╨┐╤А╨░╨▓╨╗╨╡╨╜╨╕╤П ╨▒╨░╨╗╨░╨╜╤Б╨╛╨╝ ╨╕ ╨╛╤В╨┐╤А╨░╨▓╨║╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨╛╨▓ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨б╨С╨Я ╤З╨╡╤А╨╡╨╖ ╨╛╤Д╨╕╤Ж╨╕╨░╨╗╤М╨╜╨╛╨│╨╛ ╨▒╨╛╤В╨░ ╨▓ Telegram.<br><br>
        <a href="https://staticgram.top/sbpbot" target="_blank" class="btn-submit" style="display: inline-block; padding: 10px 20px; text-decoration: none; max-width: 240px;">
          ╨Ю╤В╨║╤А╤Л╤В╤М ╨▓ Telegram
        </a>
      </div>
    `;
    return;
  }

  const filtered = State.currentFilter === 'all'
    ? State.transactions
    : State.transactions.filter(t => t.type === State.currentFilter);

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-tertiary); font-size: 13px;">
        ╨Т ╤Н╤В╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╨┐╨╛╨║╨░ ╨╜╨╡╤В ╨╛╨┐╨╡╤А╨░╤Ж╨╕╨╣
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(tx => {
    let iconClass = 'tx-cheque';
    let icon = 'ЁЯз╛';
    let amountClass = 'neutral';

    if (tx.type === 'transfer') {
      if (tx.amount < 0) {
        iconClass = 'tx-out';
        icon = 'тЖЧ';
        amountClass = 'negative';
      } else {
        iconClass = 'tx-in';
        icon = 'тЖЩ';
        amountClass = 'positive';
      }
    } else if (tx.type === 'deposit') {
      iconClass = 'tx-in';
      icon = 'тЖЩ';
      amountClass = 'positive';
    } else if (tx.type === 'withdrawal') {
      iconClass = 'tx-out';
      icon = 'тЖЧ';
      amountClass = 'negative';
    }

    const formatted = `${tx.amount > 0 ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} тнРя╕П`;

    return `
      <div class="tx-row" onclick="openReceiptModal('${tx.id}')">
        <div class="tx-left">
          <div class="tx-icon-circle ${iconClass}">${icon}</div>
          <div class="tx-meta">
            <span class="tx-name">${tx.title}</span>
            <span class="tx-sub">${tx.date} тАв ${tx.comment}</span>
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
  initBalanceToggle();
  initAccountCopy();
  initModals();
  initTransferSubmission();
  initChequeSubmission();
  initFilters();
  initTelegram();
});
