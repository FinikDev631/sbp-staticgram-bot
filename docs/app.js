/**
 * SBP StaticGram Stars Bank • Material Design 3 Mini App
 * Interactive logic, theme controller, Telegram WebApp SDK bindings
 */

// --- Global State ---
const State = {
  balance: 1500,
  escrow: 50,
  isBalanceHidden: false,
  accountNumber: 'СБП-4264-9445',
  theme: 'clay',
  darkMode: false,
  device: 'mobile',
  headingScale: 100,
  bodyScale: 90,
  transactions: [
    {
      id: 'SBP-TRX-20261017-1C5RC',
      type: 'transfer',
      title: 'Перевод @makapob',
      amount: -1500,
      status: 'Исполнен',
      date: 'Сегодня, 15:53',
      from: '@nikov',
      to: '@makapob',
      comment: 'Перевод по СБП (ожидает активации)'
    },
    {
      id: 'SBP-DEP-20261017-A91D',
      type: 'deposit',
      title: 'Пополнение Stars',
      amount: 1500,
      status: 'Исполнен',
      date: 'Сегодня, 15:20',
      from: 'Telegram Stars Gateway',
      to: 'Счёт СБП',
      comment: 'Оплата Stars Invoice без комиссии'
    },
    {
      id: 'SBP-CHK-20261017-CH50',
      type: 'cheque',
      title: 'Создание чека (активен)',
      amount: -50,
      status: 'В резерве (Escrow)',
      date: 'Сегодня, 14:10',
      from: 'Вы',
      to: 'Любой участник чата',
      comment: 'СБП Бонус в чат'
    }
  ]
};

// --- Telegram WebApp SDK Integration ---
const tg = window.Telegram?.WebApp;

function initTelegram() {
  if (!tg) return;

  try {
    tg.ready();
    tg.expand();
    
    // Set theme colors to match earth palette
    if (tg.setHeaderColor) {
      tg.setHeaderColor('#F7F3EE');
    }
    if (tg.setBackgroundColor) {
      tg.setBackgroundColor('#F7F3EE');
    }

    // Extract user profile if available
    const user = tg.initDataUnsafe?.user;
    if (user) {
      const greetingEl = document.getElementById('userGreeting');
      if (greetingEl) {
        greetingEl.textContent = `Привет, ${user.first_name || 'друг'}`;
      }

      // Generate account number derived from user id
      if (user.id) {
        const idStr = String(user.id);
        const p1 = idStr.length >= 4 ? idStr.slice(0, 4) : idStr.padStart(4, '0');
        const p2 = idStr.length >= 8 ? idStr.slice(-4) : idStr.padStart(4, '9');
        State.accountNumber = `СБП-${p1}-${p2}`;
        const accEl = document.getElementById('accountNumberDisplay');
        if (accEl) accEl.textContent = State.accountNumber;
      }

      // Update avatar initials
      const initialsEl = document.getElementById('userAvatarInitials');
      if (initialsEl) {
        const f = user.first_name ? user.first_name[0] : 'S';
        const l = user.last_name ? user.last_name[0] : 'B';
        initialsEl.textContent = `${f}${l}`.toUpperCase();
      }
    }
  } catch (err) {
    console.warn('Telegram WebApp init notice:', err);
  }
}

// Haptic feedback helper
function haptic(type = 'light') {
  try {
    if (tg?.HapticFeedback) {
      if (type === 'success' || type === 'error' || type === 'warning') {
        tg.HapticFeedback.notificationOccurred(type);
      } else {
        tg.HapticFeedback.impactOccurred(type);
      }
    }
  } catch (e) {}
}

// --- Status Bar Clock ---
function startClock() {
  const clockEl = document.getElementById('liveClock');
  if (!clockEl) return;

  function update() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    clockEl.textContent = `${hours}:${minutes}`;
  }

  update();
  setInterval(update, 30000);
}

// --- Dynamic Island Interactions ---
function initDynamicIsland() {
  const island = document.getElementById('dynamicIsland');
  if (!island) return;

  let expanded = false;
  island.addEventListener('click', () => {
    haptic('medium');
    expanded = !expanded;
    if (expanded) {
      island.style.width = '210px';
      island.innerHTML = `
        <div class="island-content">
          <span class="island-star">⚡️</span>
          <span>СБП Шлюз 100% готов</span>
        </div>
      `;
      setTimeout(() => {
        island.style.width = '';
        island.innerHTML = `
          <div class="island-content">
            <span class="island-star">⭐️</span>
            <span class="island-text">СБП Онлайн</span>
          </div>
        `;
        expanded = false;
      }, 3500);
    }
  });
}

// --- Balance Management ---
function updateBalanceUI() {
  const balanceEl = document.getElementById('balanceValue');
  if (!balanceEl) return;

  if (State.isBalanceHidden) {
    balanceEl.textContent = '••••••';
  } else {
    balanceEl.textContent = State.balance.toLocaleString('ru-RU');
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
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
      : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
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
      showToast(`Счёт: ${State.accountNumber}`);
    }
  });
}

// --- Toast Notifications ---
let toastTimer = null;
function showToast(text, duration = 3000) {
  const toast = document.getElementById('appToast');
  if (!toast) return;

  toast.textContent = text;
  toast.classList.add('show');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

// --- Modal Handlers ---
window.openModal = function(modalId) {
  haptic('light');
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
};

window.closeModal = function(modalId) {
  haptic('light');
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
};

function initModals() {
  // Close modals on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
      }
    });
  });

  // Close modals on Esc key
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
    showToast('Для вывода звезд укажите получателя или бота');
    openModal('modalTransfer');
  });
  document.getElementById('btnActionCheque')?.addEventListener('click', () => openModal('modalCheque'));
  document.getElementById('btnManageEscrow')?.addEventListener('click', () => {
    filterTransactions('cheque');
    showToast('Показаны активные чеки в резерве');
  });
}

// Helper for transfer quick amounts
window.setTransferAmount = function(amount) {
  haptic('light');
  const input = document.getElementById('transferAmount');
  if (input) input.value = amount;
};

// Helper for deposit trigger
window.triggerDeposit = function(amount) {
  haptic('success');
  State.balance += amount;
  
  // Add transaction
  const code = `SBP-DEP-${Date.now().toString(36).toUpperCase()}`;
  State.transactions.unshift({
    id: code,
    type: 'deposit',
    title: 'Пополнение Stars',
    amount: amount,
    status: 'Исполнен',
    date: 'Только что',
    from: 'Telegram Stars',
    to: State.accountNumber,
    comment: 'Мгновенное зачисление через шлюз Stars'
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
      showToast('Укажите @username или номер счёта получателя');
      haptic('error');
      return;
    }

    if (!amount || amount <= 0) {
      showToast('Укажите корректную сумму');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast('Недостаточно звёзд на балансе!');
      haptic('error');
      return;
    }

    haptic('success');
    State.balance -= amount;

    const trxId = `SBP-TRX-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.random().toString(36).slice(2, 7).toUpperCase()}`;

    State.transactions.unshift({
      id: trxId,
      type: 'transfer',
      title: `Перевод ${recipient}`,
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

    // Reset inputs
    document.getElementById('transferRecipient').value = '';
    document.getElementById('transferAmount').value = '';
    document.getElementById('transferComment').value = '';

    showToast(`Перевод ${amount} ⭐️ отправлен получателю ${recipient}!`);
  });
}

// Submit Cheque
function initChequeSubmission() {
  const select = document.getElementById('chequeTarget');
  const userGroup = document.getElementById('chequeTargetUserGroup');
  if (select && userGroup) {
    select.addEventListener('change', () => {
      userGroup.style.display = select.value === 'user' ? 'block' : 'none';
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
      showToast('Укажите сумму чека');
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast('Недостаточно звёзд на балансе для создания чека!');
      haptic('error');
      return;
    }

    haptic('success');
    State.balance -= amount;
    State.escrow += amount;

    const chkId = `SBP-CHK-${Math.random().toString(36).slice(2, 9).toUpperCase()}`;

    State.transactions.unshift({
      id: chkId,
      type: 'cheque',
      title: `Чек (${chkId})`,
      amount: -amount,
      status: 'В резерве (Escrow)',
      date: 'Только что',
      from: 'Вы',
      to: recipient,
      comment: comment
    });

    updateBalanceUI();
    renderTransactions();
    closeModal('modalCheque');

    showToast(`Чек #${chkId} на ${amount} ⭐️ создан и готов к отправке в чат!`);
  });
}

// --- Electronic Receipt Renderer ---
window.openTxReceipt = function(txId) {
  haptic('light');
  const tx = State.transactions.find(t => t.id === txId);
  if (!tx) return;

  const content = document.getElementById('receiptContent');
  if (!content) return;

  const isPositive = tx.amount > 0;
  const amountFormatted = `${isPositive ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} ⭐️`;

  content.innerHTML = `
    <div style="text-align: center; margin-bottom: 8px;">
      <div style="font-size: 26px; font-weight: 800; color: ${isPositive ? 'var(--green)' : 'var(--text-main)'};">
        ${amountFormatted}
      </div>
      <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-top: 2px;">
        ${tx.status}
      </div>
    </div>
    <div class="receipt-row">
      <span class="r-label">Номер операции</span>
      <span class="r-val" style="font-family: monospace;">#${tx.id}</span>
    </div>
    <div class="receipt-row">
      <span class="r-label">Отправитель</span>
      <span class="r-val">${tx.from || 'Счёт СБП'}</span>
    </div>
    <div class="receipt-row">
      <span class="r-label">Получатель</span>
      <span class="r-val">${tx.to || '—'}</span>
    </div>
    <div class="receipt-row">
      <span class="r-label">Дата и время</span>
      <span class="r-val">${tx.date}</span>
    </div>
    <div class="receipt-row">
      <span class="r-label">Назначение платежа</span>
      <span class="r-val">${tx.comment || 'Перевод по СБП'}</span>
    </div>
    <div class="receipt-row">
      <span class="r-label">Шлюз</span>
      <span class="r-val">StaticGram СБП • Stars Gateway</span>
    </div>
  `;

  openModal('modalReceipt');
};

// --- Transactions List & Filtering ---
let currentFilter = 'all';

function filterTransactions(type) {
  currentFilter = type;
  document.querySelectorAll('.filter-pill').forEach(pill => {
    pill.classList.toggle('active', pill.getAttribute('data-filter') === type);
  });
  renderTransactions();
}

function renderTransactions() {
  const container = document.getElementById('transactionList');
  if (!container) return;

  const filtered = currentFilter === 'all'
    ? State.transactions
    : State.transactions.filter(t => t.type === currentFilter);

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 24px; color: var(--text-muted); font-size: 13px;">
        Нет операций в этой категории
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(tx => {
    let iconClass = 'tx-cheque';
    let iconSymbol = '🧾';
    let amountClass = 'neutral';

    if (tx.type === 'transfer') {
      iconClass = 'tx-out';
      iconSymbol = '↗';
      amountClass = 'negative';
    } else if (tx.type === 'deposit') {
      iconClass = 'tx-in';
      iconSymbol = '↙';
      amountClass = 'positive';
    }

    const amountFormatted = `${tx.amount > 0 ? '+' : ''}${tx.amount.toLocaleString('ru-RU')} ⭐️`;

    return `
      <div class="tx-item" data-type="${tx.type}" onclick="openTxReceipt('${tx.id}')">
        <div class="tx-icon ${iconClass}">${iconSymbol}</div>
        <div class="tx-details">
          <div class="tx-title">${tx.title}</div>
          <div class="tx-time">${tx.date} • ${tx.status}</div>
        </div>
        <div class="tx-amount ${amountClass}">${amountFormatted}</div>
      </div>
    `;
  }).join('');
}

function initFilters() {
  document.querySelectorAll('.filter-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      haptic('light');
      const filter = pill.getAttribute('data-filter');
      filterTransactions(filter);
    });
  });

  document.getElementById('btnAllHistory')?.addEventListener('click', () => {
    filterTransactions('all');
  });
}

// --- TWEAKS Panel & Customization Controller ---
function initTweaks() {
  const tweaksPanel = document.getElementById('tweaksPanel');
  const tweaksToggle = document.getElementById('tweaksToggle');
  const btnClose = document.getElementById('btnTweakClose');

  if (tweaksToggle && tweaksPanel) {
    tweaksToggle.addEventListener('change', () => {
      tweaksPanel.style.display = tweaksToggle.checked ? 'flex' : 'none';
    });
  }

  if (btnClose && tweaksToggle && tweaksPanel) {
    btnClose.addEventListener('click', () => {
      tweaksPanel.style.display = 'none';
      tweaksToggle.checked = false;
    });
  }

  // Device Segmented Switcher
  const deviceBtns = document.querySelectorAll('#deviceSegmented .seg-btn');
  deviceBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      haptic('light');
      deviceBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const dev = btn.getAttribute('data-device');
      document.body.classList.remove('device-desktop', 'device-mobile', 'device-tablet');
      document.body.classList.add(`device-${dev}`);
    });
  });

  // Dark Mode Switch
  const darkSwitch = document.getElementById('darkModeSwitch');
  if (darkSwitch) {
    // Check saved preference
    const savedDark = localStorage.getItem('sbp_dark_mode');
    if (savedDark === 'true') {
      darkSwitch.checked = true;
      document.body.classList.add('dark-mode');
    }

    darkSwitch.addEventListener('change', () => {
      haptic('light');
      document.body.classList.toggle('dark-mode', darkSwitch.checked);
      localStorage.setItem('sbp_dark_mode', darkSwitch.checked);
    });
  }

  // Themes Swatches
  const swatches = document.querySelectorAll('#themeSwatches .swatch-btn');
  const savedTheme = localStorage.getItem('sbp_theme') || 'clay';
  setTheme(savedTheme);

  swatches.forEach(btn => {
    btn.addEventListener('click', () => {
      haptic('light');
      const theme = btn.getAttribute('data-theme');
      setTheme(theme);
    });
  });

  function setTheme(theme) {
    const allThemes = ['stone', 'moss', 'mist', 'clay', 'dusk', 'sakura', 'ink'];
    allThemes.forEach(t => document.body.classList.remove(`theme-${t}`));
    document.body.classList.add(`theme-${theme}`);
    localStorage.setItem('sbp_theme', theme);

    swatches.forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-theme') === theme);
    });
  }

  // Typography Sliders
  const sliderH = document.getElementById('sliderHeading');
  const valH = document.getElementById('headingSizeVal');
  if (sliderH && valH) {
    sliderH.addEventListener('input', () => {
      const scale = sliderH.value / 100;
      document.documentElement.style.setProperty('--font-heading-scale', scale);
      valH.textContent = `${sliderH.value}%`;
    });
  }

  const sliderB = document.getElementById('sliderBody');
  const valB = document.getElementById('bodySizeVal');
  if (sliderB && valB) {
    sliderB.addEventListener('input', () => {
      const scale = sliderB.value / 100;
      document.documentElement.style.setProperty('--font-body-scale', scale);
      valB.textContent = `${sliderB.value}%`;
    });
  }

  // Section Toggles
  const toggleEscrow = document.getElementById('toggleEscrowSection');
  const cardEscrow = document.getElementById('escrowCard');
  if (toggleEscrow && cardEscrow) {
    toggleEscrow.addEventListener('change', () => {
      cardEscrow.style.display = toggleEscrow.checked ? 'flex' : 'none';
    });
  }

  const toggleNews = document.getElementById('toggleNewsSection');
  const cardNews = document.getElementById('intentionCard');
  if (toggleNews && cardNews) {
    toggleNews.addEventListener('change', () => {
      cardNews.style.display = toggleNews.checked ? 'flex' : 'none';
    });
  }
}

// --- Topbar Tools ---
function initTopbarTools() {
  // Share Button
  document.getElementById('btnShareApp')?.addEventListener('click', async () => {
    haptic('medium');
    const shareUrl = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'СБП • StaticGram Stars Bank',
          text: 'Мгновенные переводы Telegram Stars через систему СБП!',
          url: shareUrl
        });
      } catch (e) {}
    } else {
      try {
        await navigator.clipboard.writeText(shareUrl);
        showToast('Ссылка на Mini App скопирована в буфер обмена!');
      } catch (e) {
        showToast(shareUrl);
      }
    }
  });

  // Tool buttons toggle
  const toolPay = document.getElementById('toolPay');
  const toolCheques = document.getElementById('toolViewCheques');
  const toolHistory = document.getElementById('toolHistory');

  function setToolActive(btn) {
    [toolPay, toolCheques, toolHistory].forEach(b => b?.classList.remove('active'));
    btn?.classList.add('active');
  }

  toolPay?.addEventListener('click', () => {
    haptic('light');
    setToolActive(toolPay);
    openModal('modalTransfer');
  });

  toolCheques?.addEventListener('click', () => {
    haptic('light');
    setToolActive(toolCheques);
    filterTransactions('cheque');
    showToast('Категория: Чеки');
  });

  toolHistory?.addEventListener('click', () => {
    haptic('light');
    setToolActive(toolHistory);
    filterTransactions('all');
    showToast('Категория: Все операции');
  });

  // Fullscreen button
  document.getElementById('toolFullscreen')?.addEventListener('click', () => {
    haptic('light');
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });

  // Reset Zoom
  document.getElementById('toolResetZoom')?.addEventListener('click', () => {
    haptic('light');
    document.documentElement.style.setProperty('--font-heading-scale', '1');
    document.documentElement.style.setProperty('--font-body-scale', '0.95');
    const sliderH = document.getElementById('sliderHeading');
    const sliderB = document.getElementById('sliderBody');
    const valH = document.getElementById('headingSizeVal');
    const valB = document.getElementById('bodySizeVal');
    if (sliderH) sliderH.value = 100;
    if (sliderB) sliderB.value = 90;
    if (valH) valH.textContent = '100%';
    if (valB) valB.textContent = '90%';
    showToast('Масштаб сброшен до 100%');
  });
}

// --- Initialization on DOM Loaded ---
document.addEventListener('DOMContentLoaded', () => {
  initTelegram();
  startClock();
  initDynamicIsland();
  initBalanceToggle();
  initAccountCopy();
  initModals();
  initTransferSubmission();
  initChequeSubmission();
  initFilters();
  initTweaks();
  initTopbarTools();
  updateBalanceUI();
  renderTransactions();
});
