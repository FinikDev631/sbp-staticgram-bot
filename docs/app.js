/**
 * SBP StaticGram Stars Bank • Material Design 3 Web App
 * Real PostgreSQL API, In-App Stars Checkout, Dedicated Settings Modal, Proper Dark/Light Theme & i18n
 */

// --- Dynamic API Base URL ---
const API_BASE = window.location.origin.includes('github.io')
  ? 'https://sbp-staticgram-bot.onrender.com'
  : '';

// --- Internationalization (i18n) Dictionary ---
const I18N = {
  ru: {
    brandName: 'StaticGram Stars',
    brandStatus: 'Онлайн шлюз',
    guestGreeting: 'Гостевой режим',
    guestSubtext: 'Откройте приложение через Telegram бота @sbpbot',
    guestNotice: 'Приложение открыто в режиме просмотра. Для управления балансом откройте СБП через официального бота.',
    userGreeting: 'Привет, {name}!',
    userSubtext: '{label} • Сеть активна',
    networkActive: 'Сеть активна',
    balanceLabel: 'ДОСТУПНЫЙ БАЛАНС',
    balanceSub: 'Мгновенные переводы внутри сети без комиссии',
    inEscrow: 'В резерве',
    activeReserve: 'Активные резервы: {amount} ⭐️',
    viewCheques: 'Смотреть чеки',
    actionTransfer: 'Перевести',
    actionTransferCaption: 'По @username или счёту',
    actionDeposit: 'Пополнить',
    actionDepositCaption: 'Telegram Stars',
    actionWithdraw: 'Вывести',
    actionWithdrawCaption: 'На аккаунт',
    actionCheque: 'Создать чек',
    actionChequeCaption: 'Для отправки в чаты',
    newsTag: '📢 ОФИЦИАЛЬНЫЙ КАНАЛ СБП',
    newsTitle: 'Мгновенные переводы, мультивалютный учёт и чеки',
    newsDesc: 'Новости системы быстрых платежей, обновления шлюза и квитанции нового поколения.',
    newsBtn: 'Подписаться на @sbpnews',
    historyTitle: 'История операций',
    historySub: 'Все транзакции, пополнения и чеки с электронными квитанциями',
    filterAll: 'Все',
    filterTransfer: 'Переводы',
    filterDeposit: 'Пополнения',
    filterCheque: 'Чеки',
    loadingOps: 'Загрузка операций...',
    noOpsCategory: 'В этой категории пока нет операций',
    openBot: 'Открыть бота',
    footerPlatform: 'СБП StaticGram Stars • Платформа мгновенных платежей',
    footerNews: 'Новости',
    footerBot: 'Telegram Бот',

    // Settings
    settingsTitle: '⚙️ Настройки',
    settingsTheme: 'Тема оформления',
    themeLight: 'Светлая',
    themeDark: 'Тёмная',
    themeSystem: 'Системная',
    themeHalloween: 'Хэллоуин 🎃',
    settingsMascotTitle: 'Маскот (Boykisser)',
    mascotToggleName: 'Показывать Бойкиссера',
    mascotToggleSub: 'Интерактивный помощник на главном экране',
    boykisserName: 'Бойкиссер ✨',
    boykisserDefaultSpeech: 'Ты любишь переводить звёзды по СБП, да? :3',
    settingsLang: 'Язык интерфейса',
    settingsAccount: 'Аккаунт СБП',
    settingsUser: 'Пользователь',
    settingsAccountNum: 'Номер счёта',
    settingsStatus: 'Статус шлюза',
    settingsLinks: 'Полезные ссылки',

    // Modals
    modalTransferTitle: '💸 Перевод по СБП',
    modalTransferRecipient: 'Получатель (@username, ID или номер счёта СБП)',
    modalTransferAmount: 'Сумма перевода (⭐️)',
    modalTransferComment: 'Назначение платежа / комментарий (необязательно)',
    modalTransferSubmit: 'Отправить перевод',

    modalDepositTitle: '📥 Пополнение счёта Stars',
    modalDepositDesc: 'Оплата производится мгновенно прямо в приложении через платёжный шлюз Telegram Stars (XTR):',
    modalDepositCustomLabel: 'Произвольная сумма звёзд (⭐️)',
    modalDepositBuy: 'Купить',
    modalDepositPresets: 'Быстрый выбор пакета:',

    modalWithdrawTitle: '📤 Вывод звёзд Stars',
    modalWithdrawDesc: 'Для прямого вывода звёзд используйте команду /withdraw в Telegram-боте либо отправьте перевод на нужный аккаунт СБП.',
    modalWithdrawBtn: 'Перейти к выводу в боте',

    modalChequeTitle: '🧾 Чеки СБП',
    modalChequeTabCreate: '✨ Создать чек',
    modalChequeTabList: '📋 Мои чеки',
    modalChequeTabClaim: '⚡️ Активировать код',
    noActiveCheques: 'У вас пока нет активных чеков',
    btnCancelCheque: 'Аннулировать чек',
    toastChequeCancelled: 'Чек аннулирован, звёзды возвращены на баланс!',
    modalChequeAmount: 'Номинал чека (⭐️)',
    modalChequeType: 'Тип чека',
    modalChequeAny: '🌐 Для всех (активирует первый нажавший в чате)',
    modalChequeUser: '🔒 Именной чек (только для указанного @username)',
    modalChequeRecipient: 'Имя пользователя получателя',
    modalChequeComment: 'Комментарий к чеку',
    modalChequeSubmit: 'Сгенерировать инлайн-чек',
    modalChequeClaimDesc: 'Введите инлайн-код чека (например, @sbpbot ch_123456789abc или ch_123456789abc), чтобы моментально получить звёзды на баланс:',
    modalChequeClaimInputLabel: 'Инлайн-код или ID чека',
    modalChequeClaimBtn: '⚡️ Забрать звёзды на баланс',

    modalChequeResultTitle: '🎉 Чек успешно создан!',
    modalChequeResultDesc: 'Звёзды зарезервированы. Отправьте инлайн-код в любой чат Telegram:',
    modalChequeResultInlineCode: 'Инлайн-код для чата',
    modalChequeResultHint: '💡 Нажмите «Отправить в чат» — откроется диалог выбора чата, и чек отправится интерактивной карточкой с кнопкой!',
    modalChequeResultCopy: '📋 Скопировать код',
    modalChequeResultShare: '⚡️ Отправить в чат',

    modalReceiptTitle: 'Электронный чек',
    modalReceiptCopy: 'Скопировать данные чека',
    receiptTrx: 'Номер квитанции',
    receiptFrom: 'Отправитель',
    receiptTo: 'Получатель',
    receiptDate: 'Дата и время',
    receiptComment: 'Назначение платежа',
    receiptGateway: 'Платёжный шлюз',
    receiptExecuted: 'Исполнен',

    // Notifications & Toasts
    toastCopiedAccount: 'Номер счёта скопирован: {acc}',
    toastOpenBotForAcc: 'Откройте бота в Telegram для получения счёта',
    toastOpenBotForTransfer: 'Для отправки перевода откройте бота @sbpbot',
    toastOpenBotForDeposit: 'Для пополнения баланса откройте бота @sbpbot',
    toastOpenBotForCheque: 'Для работы с чеками откройте бота @sbpbot',
    toastPreparingInvoice: 'Подготовка счёта на {amount} ⭐️...',
    toastDepositSuccess: 'Баланс успешно пополнен на +{amount} ⭐️!',
    toastDepositCancel: 'Оплата отменена',
    toastDepositFail: 'Ошибка при проведении платежа',
    toastSpecifyRecipient: 'Укажите получателя (@username, ID или номер счёта)',
    toastSpecifyAmount: 'Укажите корректную сумму',
    toastInsufficientBalance: 'Недостаточно звёзд. Ваш баланс: {bal} ⭐️',
    toastTransferSending: 'Отправка...',
    toastTransferSubmit: 'Отправить перевод',
    toastTransferSuccess: 'Перевод {amount} ⭐️ успешно отправлен!',
    toastChequeSpecifyNominal: 'Укажите номинал чека',
    toastChequeInsufficient: 'Недостаточно звёзд на балансе для резервирования чека',
    toastChequeSpecifyUser: 'Укажите @username получателя',
    toastChequeCreating: 'Создание...',
    toastChequeSubmit: 'Сгенерировать инлайн-чек',
    toastChequeSpecifyCode: 'Введите инлайн-код чека',
    toastChequeClaiming: 'Активация чека...',
    toastChequeCopied: 'Инлайн-код чека скопирован в буфер обмена!',
    toastReceiptCopied: 'Данные чека скопированы в буфер!',
    confirmTransferPrompt: 'Действительно хотите отправить {amount} ⭐️ получателю {recipient}?'
  },
  en: {
    brandName: 'StaticGram Stars',
    brandStatus: 'Online Gateway',
    guestGreeting: 'Guest Mode',
    guestSubtext: 'Open the app via Telegram bot @sbpbot',
    guestNotice: 'The app is in read-only view. To manage balance and make transfers, open SBP via the official bot.',
    userGreeting: 'Hello, {name}!',
    userSubtext: '{label} • Network Active',
    networkActive: 'Network Active',
    balanceLabel: 'AVAILABLE BALANCE',
    balanceSub: 'Instant network transfers with zero fees',
    inEscrow: 'In Escrow',
    activeReserve: 'Active reserves: {amount} ⭐️',
    viewCheques: 'View Cheques',
    actionTransfer: 'Transfer',
    actionTransferCaption: 'By @username or account',
    actionDeposit: 'Top Up',
    actionDepositCaption: 'Telegram Stars',
    actionWithdraw: 'Withdraw',
    actionWithdrawCaption: 'To account',
    actionCheque: 'Create Cheque',
    actionChequeCaption: 'For sharing in chats',
    newsTag: '📢 OFFICIAL SBP CHANNEL',
    newsTitle: 'Instant transfers, multi-currency accounting & cheques',
    newsDesc: 'Fast payment system updates, gateway releases and next-gen electronic receipts.',
    newsBtn: 'Subscribe to @sbpnews',
    historyTitle: 'Transaction History',
    historySub: 'All transfers, top-ups and cheques with digital receipts',
    filterAll: 'All',
    filterTransfer: 'Transfers',
    filterDeposit: 'Deposits',
    filterCheque: 'Cheques',
    loadingOps: 'Loading transactions...',
    noOpsCategory: 'No transactions in this category yet',
    openBot: 'Open Bot',
    footerPlatform: 'SBP StaticGram Stars • Instant Payment Platform',
    footerNews: 'News',
    footerBot: 'Telegram Bot',

    // Settings
    settingsTitle: '⚙️ Settings',
    settingsTheme: 'Theme Appearance',
    themeLight: 'Light',
    themeDark: 'Dark',
    themeSystem: 'System',
    settingsLang: 'App Language',
    settingsAccount: 'SBP Account',
    settingsUser: 'User',
    settingsAccountNum: 'Account Number',
    settingsStatus: 'Gateway Status',
    settingsLinks: 'Useful Links',

    // Modals
    modalTransferTitle: '💸 Transfer via SBP',
    modalTransferRecipient: 'Recipient (@username, ID or SBP account number)',
    modalTransferAmount: 'Transfer amount (⭐️)',
    modalTransferComment: 'Payment purpose / comment (optional)',
    modalTransferSubmit: 'Send Transfer',

    modalDepositTitle: '📥 Top Up Stars Balance',
    modalDepositDesc: 'Pay instantly inside the Telegram Mini App using the official Telegram Stars (XTR) gateway:',
    modalDepositCustomLabel: 'Custom star amount (⭐️)',
    modalDepositBuy: 'Buy',
    modalDepositPresets: 'Quick package selection:',

    modalWithdrawTitle: '📤 Withdraw Stars',
    modalWithdrawDesc: 'For direct withdrawal of stars, use the /withdraw command in the Telegram bot or send a transfer to your SBP account.',
    modalWithdrawBtn: 'Go to Withdraw in Bot',

    modalChequeTitle: '🧾 SBP Cheques',
    modalChequeTabCreate: '✨ Create Cheque',
    modalChequeTabList: '📋 My Cheques',
    modalChequeTabClaim: '⚡️ Claim by Code',
    noActiveCheques: 'You have no active cheques',
    btnCancelCheque: 'Cancel Cheque',
    toastChequeCancelled: 'Cheque cancelled, stars refunded to balance!',
    modalChequeAmount: 'Cheque nominal (⭐️)',
    modalChequeType: 'Cheque type',
    modalChequeAny: '🌐 For everyone (first user to click in chat claims it)',
    modalChequeUser: '🔒 Named cheque (only for specified @username)',
    modalChequeRecipient: 'Recipient username',
    modalChequeComment: 'Cheque comment',
    modalChequeSubmit: 'Generate Inline Cheque',
    modalChequeClaimDesc: 'Enter cheque inline code (e.g. @sbpbot ch_123456789abc or ch_123456789abc) to claim stars directly to your SBP balance:',
    modalChequeClaimInputLabel: 'Inline Code or Cheque ID',
    modalChequeClaimBtn: '⚡️ Claim Stars to Balance',

    modalChequeResultTitle: '🎉 Cheque Created Successfully!',
    modalChequeResultDesc: 'Stars reserved. Send the inline code to any Telegram chat:',
    modalChequeResultInlineCode: 'Inline Code for Chat',
    modalChequeResultHint: '💡 Click "Send to Chat" to choose a chat and post the interactive cheque card with button!',
    modalChequeResultCopy: '📋 Copy Code',
    modalChequeResultShare: '⚡️ Send to Chat',

    modalReceiptTitle: 'Electronic Receipt',
    modalReceiptCopy: 'Copy Receipt Details',
    receiptTrx: 'Receipt ID',
    receiptFrom: 'Sender',
    receiptTo: 'Recipient',
    receiptDate: 'Date & Time',
    receiptComment: 'Purpose',
    receiptGateway: 'Payment Gateway',
    receiptExecuted: 'Executed',

    // Notifications & Toasts
    toastCopiedAccount: 'Account number copied: {acc}',
    toastOpenBotForAcc: 'Open bot in Telegram to get your account',
    toastOpenBotForTransfer: 'To make transfers, open @sbpbot',
    toastOpenBotForDeposit: 'To top up, open @sbpbot',
    toastOpenBotForCheque: 'To manage cheques, open @sbpbot',
    toastPreparingInvoice: 'Preparing invoice for {amount} ⭐️...',
    toastDepositSuccess: 'Balance topped up by +{amount} ⭐️!',
    toastDepositCancel: 'Payment cancelled',
    toastDepositFail: 'Payment error',
    toastSpecifyRecipient: 'Please specify recipient (@username, ID or account)',
    toastSpecifyAmount: 'Please specify valid amount',
    toastInsufficientBalance: 'Insufficient stars. Your balance: {bal} ⭐️',
    toastTransferSending: 'Sending...',
    toastTransferSubmit: 'Send Transfer',
    toastTransferSuccess: 'Transfer of {amount} ⭐️ sent!',
    toastChequeSpecifyNominal: 'Please enter cheque nominal',
    toastChequeInsufficient: 'Insufficient stars on balance to reserve cheque',
    toastChequeSpecifyUser: 'Please specify recipient @username',
    toastChequeCreating: 'Creating...',
    toastChequeSubmit: 'Generate Inline Cheque',
    toastChequeSpecifyCode: 'Please enter cheque inline code',
    toastChequeClaiming: 'Claiming cheque...',
    toastChequeCopied: 'Cheque inline code copied to clipboard!',
    toastReceiptCopied: 'Receipt details copied to clipboard!',
    confirmTransferPrompt: 'Do you really want to send {amount} ⭐️ to {recipient}?'
  }
};

// --- Application State ---
const State = {
  user: null,
  userId: null,
  username: null,
  firstName: null,
  botUsername: 'sbpbot',
  lastCreatedChequeId: null,
  balance: 0,
  escrow: 0,
  isBalanceHidden: false,
  accountNumber: '—',
  currentFilter: 'all',
  activeReceipt: null,
  transactions: [],
  activeCheques: [],
  isGuest: false,
  isLoading: true,
  lang: 'ru',
  themePreference: 'dark' // 'light' | 'dark' | 'system'
};

const tg = window.Telegram?.WebApp;

// --- i18n Translation Helper ---
function t(key, params = {}) {
  const dict = I18N[State.lang] || I18N.ru;
  let text = dict[key] || I18N.ru[key] || key;
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
  }
  return text;
}

window.selectLanguage = function(newLang) {
  haptic('light');
  State.lang = newLang;
  localStorage.setItem('sbp_lang', newLang);

  // Update active state in settings modal
  document.getElementById('langOptRu')?.classList.toggle('active', newLang === 'ru');
  document.getElementById('langOptEn')?.classList.toggle('active', newLang === 'en');

  // Update all data-i18n elements
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key && I18N[newLang]?.[key]) {
      el.textContent = I18N[newLang][key];
    }
  });

  updateBalanceUI();
  renderTransactions();

  const greetingEl = document.getElementById('userGreeting');
  const subtextEl = document.getElementById('userSubtext');
  if (State.isGuest) {
    if (greetingEl) greetingEl.textContent = t('guestGreeting');
    if (subtextEl) subtextEl.textContent = t('guestSubtext');
  } else if (State.user) {
    if (greetingEl) greetingEl.textContent = t('userGreeting', { name: State.user.first_name || 'Client' });
    if (subtextEl) {
      const label = State.user.username ? `@${State.user.username}` : `ID ${State.user.user_id}`;
      subtextEl.textContent = t('userSubtext', { label });
    }
  }
};

// --- Theme Management ---
function getSystemTheme() {
  if (tg?.colorScheme) return tg.colorScheme;
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
  return 'light';
}

window.selectTheme = function(preference) {
  haptic('light');
  State.themePreference = preference;
  localStorage.setItem('sbp_theme', preference);

  document.getElementById('themeOptLight')?.classList.toggle('active', preference === 'light');
  document.getElementById('themeOptDark')?.classList.toggle('active', preference === 'dark');
  document.getElementById('themeOptHalloween')?.classList.toggle('active', preference === 'halloween');
  document.getElementById('themeOptSystem')?.classList.toggle('active', preference === 'system');

  const resolvedTheme = preference === 'system' ? getSystemTheme() : preference;
  document.documentElement.setAttribute('data-theme', resolvedTheme);

  try {
    let bgColor = '#0C0A09';
    if (resolvedTheme === 'light') bgColor = '#F6F2ED';
    else if (resolvedTheme === 'halloween') bgColor = '#0D0805';
    if (tg?.setHeaderColor) tg.setHeaderColor(bgColor);
    if (tg?.setBackgroundColor) tg.setBackgroundColor(bgColor);
  } catch (e) {}
};

function initThemeAndLang() {
  // Theme init
  const savedTheme = localStorage.getItem('sbp_theme') || 'dark'; // Default to sleek dark mode
  selectTheme(savedTheme);

  // Language init
  const savedLang = localStorage.getItem('sbp_lang');
  if (savedLang) {
    selectLanguage(savedLang);
  } else if (tg?.initDataUnsafe?.user?.language_code) {
    const userLang = tg.initDataUnsafe.user.language_code.toLowerCase();
    selectLanguage(userLang.startsWith('ru') ? 'ru' : 'en');
  } else {
    selectLanguage('ru');
  }

  // Settings Gear Button
  document.getElementById('btnOpenSettings')?.addEventListener('click', () => {
    haptic('light');
    updateSettingsModalInfo();
    openModal('modalSettings');
  });
}

function updateSettingsModalInfo() {
  const usernameEl = document.getElementById('settingsUsername');
  const accountNumEl = document.getElementById('settingsAccountNum');

  if (State.user) {
    if (usernameEl) usernameEl.textContent = State.user.username ? `@${State.user.username}` : (State.user.first_name || 'Client');
    if (accountNumEl) accountNumEl.textContent = State.user.account_number || '—';
  } else {
    if (usernameEl) usernameEl.textContent = 'Гость (Guest)';
    if (accountNumEl) accountNumEl.textContent = 'Не подключён';
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

// --- Telegram WebApp SDK Initialization ---
function initTelegram() {
  if (tg) {
    try {
      tg.ready();
      tg.expand();
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
    State.firstName = tgUser.first_name || 'Клиент';
  } else if (urlParams.get('user_id')) {
    State.userId = parseInt(urlParams.get('user_id'), 10);
    State.username = urlParams.get('username') || null;
    State.firstName = urlParams.get('first_name') || 'Клиент';
  }

  fetchUserData();
}

// --- Fetch Real User Data from Database ---
async function fetchUserData() {
  const greetingEl = document.getElementById('userGreeting');
  const subtextEl = document.getElementById('userSubtext');
  const accountEl = document.getElementById('accountNumberDisplay');

  if (!State.userId) {
    State.isGuest = true;
    State.isLoading = false;
    State.balance = 0;
    State.escrow = 0;
    State.accountNumber = '—';

    if (greetingEl) greetingEl.textContent = t('guestGreeting');
    if (subtextEl) subtextEl.textContent = t('guestSubtext');
    if (accountEl) accountEl.textContent = '—';

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
      State.botUsername = data.bot_username || 'sbpbot';
      State.balance = data.user.balance || 0;
      State.escrow = data.user.reserved || 0;
      State.accountNumber = data.user.account_number || '—';
      State.transactions = data.transactions || [];
      State.activeCheques = data.active_cheques || [];
      State.isGuest = false;
      State.isLoading = false;

      if (greetingEl) {
        greetingEl.textContent = t('userGreeting', { name: data.user.first_name || 'Client' });
      }
      if (subtextEl) {
        const label = data.user.username ? `@${data.user.username}` : `ID ${data.user.user_id}`;
        subtextEl.textContent = t('userSubtext', { label });
      }
      if (accountEl) {
        accountEl.textContent = State.accountNumber;
      }

      updateBalanceUI();
      renderTransactions();
      renderActiveCheques();
      updateSettingsModalInfo();
    }
  } catch (err) {
    console.error('Failed to fetch real user data:', err);
    State.isLoading = false;
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
    valEl.textContent = State.isBalanceHidden ? '••••••' : State.balance.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US');
  }

  const escrowStrip = document.getElementById('escrowStrip');
  const escrowTotal = document.getElementById('escrowTotal');
  if (escrowTotal) {
    escrowTotal.textContent = `${State.escrow.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} ⭐️`;
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
    if (State.isGuest || State.accountNumber === '—') {
      showToast(t('toastOpenBotForAcc'));
      return;
    }
    try {
      await navigator.clipboard.writeText(State.accountNumber);
      showToast(t('toastCopiedAccount', { acc: State.accountNumber }));
    } catch (e) {
      showToast(State.accountNumber);
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
      showToast(t('toastOpenBotForTransfer'));
      return;
    }
    openModal('modalTransfer');
  });

  document.getElementById('btnActionDeposit')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast(t('toastOpenBotForDeposit'));
      return;
    }
    openModal('modalDeposit');
  });

  document.getElementById('btnActionWithdraw')?.addEventListener('click', () => {
    openModal('modalWithdraw');
  });

  document.getElementById('btnActionCheque')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast(t('toastOpenBotForCheque'));
      return;
    }
    openModal('modalCheque');
  });

  document.getElementById('btnFilterCheques')?.addEventListener('click', () => {
    if (State.isGuest) {
      showToast(t('toastOpenBotForCheque'));
      return;
    }
    openModal('modalCheque');
    window.switchChequeTab('list');
  });

  // Cheque Tabs switching (Create, My Cheques, Claim)
  window.switchChequeTab = function(tabName) {
    haptic('light');
    const tabCreate = document.getElementById('tabChequeCreate');
    const tabList = document.getElementById('tabChequeList');
    const tabClaim = document.getElementById('tabChequeClaim');
    const sectionCreate = document.getElementById('chequeCreateSection');
    const sectionList = document.getElementById('chequeListSection');
    const sectionClaim = document.getElementById('chequeClaimSection');

    const tabs = [
      { name: 'create', btn: tabCreate, sec: sectionCreate, display: 'block' },
      { name: 'list', btn: tabList, sec: sectionList, display: 'block' },
      { name: 'claim', btn: tabClaim, sec: sectionClaim, display: 'block' }
    ];

    tabs.forEach(t => {
      const isActive = t.name === tabName;
      if (t.btn) {
        t.btn.classList.toggle('active', isActive);
        t.btn.style.background = isActive ? 'var(--surface)' : 'transparent';
        t.btn.style.color = isActive ? 'var(--text-main)' : 'var(--text-secondary)';
        t.btn.style.boxShadow = isActive ? 'var(--shadow-sm)' : 'none';
      }
      if (t.sec) {
        t.sec.style.display = isActive ? t.display : 'none';
      }
    });

    if (tabName === 'list') {
      renderActiveCheques();
    }
  };

  document.getElementById('tabChequeCreate')?.addEventListener('click', () => window.switchChequeTab('create'));
  document.getElementById('tabChequeList')?.addEventListener('click', () => window.switchChequeTab('list'));
  document.getElementById('tabChequeClaim')?.addEventListener('click', () => window.switchChequeTab('claim'));

  // Copy inline code
  window.copyChequeInlineCode = async function() {
    haptic('medium');
    const code = document.getElementById('createdChequeInlineCode')?.value;
    if (code) {
      try {
        await navigator.clipboard.writeText(code);
        showToast(t('toastChequeCopied'));
      } catch (e) {
        showToast(code);
      }
    }
  };

  document.getElementById('btnCopyChequeCode')?.addEventListener('click', window.copyChequeInlineCode);
  document.getElementById('btnQuickCopyCode')?.addEventListener('click', window.copyChequeInlineCode);

  // Send Cheque by Inline Query with multi-level native fallbacks
  window.shareChequeAction = function() {
    const inlineCode = document.getElementById('createdChequeInlineCode')?.value || '';
    const chequeId = State.lastCreatedChequeId || (inlineCode ? inlineCode.split(' ').pop() : '');
    if (typeof window.shareChequeById === 'function') {
      window.shareChequeById(chequeId || inlineCode);
    }
  };

  document.getElementById('btnShareChequeInline')?.addEventListener('click', window.shareChequeAction);

  // Claim Cheque by Code in Mini App
  document.getElementById('btnSubmitClaimCheque')?.addEventListener('click', async () => {
    haptic('medium');
    if (State.isGuest) {
      showToast(t('toastOpenBotForCheque'));
      return;
    }

    const input = document.getElementById('chequeClaimInput');
    const code = input?.value.trim();
    if (!code) {
      showToast(t('toastChequeSpecifyCode'));
      haptic('error');
      return;
    }

    const btn = document.getElementById('btnSubmitClaimCheque');
    btn.disabled = true;
    btn.textContent = t('toastChequeClaiming');

    try {
      const res = await fetch(`${API_BASE}/api/claim_cheque`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: State.userId,
          code: code
        })
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        haptic('error');
        showToast(data.error || 'Ошибка при активации чека');
        btn.disabled = false;
        btn.textContent = t('modalChequeClaimBtn');
        return;
      }

      haptic('success');
      showToast(data.message || `+${data.amount} ⭐️ зачислено на ваш баланс!`);
      closeModal('modalCheque');
      if (input) input.value = '';
      await fetchUserData();
    } catch (e) {
      haptic('error');
      showToast('Ошибка сети при активации чека');
    } finally {
      btn.disabled = false;
      btn.textContent = t('modalChequeClaimBtn');
    }
  });

  // Custom Deposit Form Submit Button
  document.getElementById('btnPayCustomDeposit')?.addEventListener('click', () => {
    const input = document.getElementById('depositCustomInput');
    const amount = parseInt(input?.value, 10);
    if (!amount || amount < 1 || amount > 100000) {
      showToast(t('toastSpecifyAmount'));
      haptic('error');
      return;
    }
    triggerDeposit(amount);
  });
}

// Quick amount chips for transfer
window.setTransferAmount = function(val) {
  haptic('light');
  const input = document.getElementById('transferAmount');
  if (input) input.value = val;
};

// --- In-App Deposit Trigger (Telegram Stars Direct Checkout) ---
window.triggerDeposit = async function(amount) {
  haptic('medium');
  if (State.isGuest) {
    showToast(t('toastOpenBotForDeposit'));
    return;
  }

  showToast(t('toastPreparingInvoice', { amount }));

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

    if (data.invoice_link) {
      let invoiceUrl = data.invoice_link;
      if (invoiceUrl && !invoiceUrl.includes('t.me')) {
        const slug = invoiceUrl.split('/').pop().replace('$', '');
        invoiceUrl = `https://t.me/$${slug}`;
      }

      if (tg?.openInvoice) {
        try {
          tg.openInvoice(invoiceUrl, (status) => {
            if (status === 'paid') {
              haptic('success');
              showToast(t('toastDepositSuccess', { amount }));
              closeModal('modalDeposit');
              setTimeout(fetchUserData, 800);
              setTimeout(fetchUserData, 2500);
            } else if (status === 'cancelled') {
              showToast(t('toastDepositCancel'));
            } else {
              // Invoice was sent directly into the user's chat with the bot
              showToast(State.lang === 'en'
                ? `Invoice sent to bot chat! Open @sbpbot to pay.`
                : `Счёт на ${amount} ⭐️ отправлен в чат с ботом! Откройте @sbpbot для оплаты.`);
              closeModal('modalDeposit');
            }
          });
        } catch (invoiceErr) {
          console.warn('openInvoice threw, falling back to chat invoice:', invoiceErr);
          showToast(State.lang === 'en'
            ? `Invoice sent to bot chat! Open @sbpbot to pay.`
            : `Счёт на ${amount} ⭐️ отправлен в чат с ботом! Откройте @sbpbot для оплаты.`);
          closeModal('modalDeposit');
        }
      } else {
        // Desktop browser fallback
        window.open(data.raw_link || data.invoice_link, '_blank');
        closeModal('modalDeposit');
      }
    } else if (data.bot_url) {
      showToast(State.lang === 'en'
        ? `Invoice sent to bot chat! Open @sbpbot to pay.`
        : `Счёт на ${amount} ⭐️ отправлен в чат с ботом! Откройте @sbpbot для оплаты.`);
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(data.bot_url);
      } else {
        window.open(data.bot_url, '_blank');
      }
      closeModal('modalDeposit');
    }
  } catch (e) {
    console.error('Deposit invoice error:', e);
    showToast(State.lang === 'en'
      ? `Invoice sent to bot chat! Open @sbpbot to pay.`
      : `Счёт на ${amount} ⭐️ отправлен в чат с ботом! Откройте @sbpbot для оплаты.`);
    closeModal('modalDeposit');
  }
};

// --- Submit Transfer (Real PostgreSQL Execution) ---
function initTransferSubmission() {
  const btn = document.getElementById('btnSubmitTransfer');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const recipient = document.getElementById('transferRecipient')?.value.trim();
    const amount = parseInt(document.getElementById('transferAmount')?.value, 10);
    const comment = document.getElementById('transferComment')?.value.trim() || 'Перевод по СБП';

    if (!recipient) {
      showToast(t('toastSpecifyRecipient'));
      haptic('error');
      return;
    }

    if (!amount || amount <= 0) {
      showToast(t('toastSpecifyAmount'));
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast(t('toastInsufficientBalance', { bal: State.balance }));
      haptic('error');
      return;
    }

    const confirmText = t('confirmTransferPrompt', { amount, recipient });

    const proceedTransfer = async () => {
      btn.disabled = true;
      btn.textContent = t('toastTransferSending');

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
          showToast(data.error || 'Ошибка при выполнении перевода');
          btn.disabled = false;
          btn.textContent = t('modalTransferSubmit');
          return;
        }

        haptic('success');
        closeModal('modalTransfer');
        document.getElementById('transferRecipient').value = '';
        document.getElementById('transferAmount').value = '';
        document.getElementById('transferComment').value = '';

        showToast(data.message || t('toastTransferSuccess', { amount }));
        await fetchUserData();

      } catch (e) {
        haptic('error');
        showToast('Ошибка сети при отправке перевода');
      } finally {
        btn.disabled = false;
        btn.textContent = t('modalTransferSubmit');
      }
    };

    if (tg?.showConfirm) {
      tg.showConfirm(confirmText, (confirmed) => {
        if (confirmed) {
          proceedTransfer();
        }
      });
    } else {
      if (window.confirm(confirmText)) {
        proceedTransfer();
      }
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
    const comment = document.getElementById('chequeComment')?.value.trim() || 'СБП бонус';

    if (!amount || amount <= 0) {
      showToast(t('toastChequeSpecifyNominal'));
      haptic('error');
      return;
    }

    if (amount > State.balance) {
      showToast(t('toastChequeInsufficient'));
      haptic('error');
      return;
    }

    if (targetType === 'user' && !recipient) {
      showToast(t('toastChequeSpecifyUser'));
      haptic('error');
      return;
    }

    btn.disabled = true;
    btn.textContent = t('toastChequeCreating');

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
        showToast(data.error || 'Не удалось создать чек');
        btn.disabled = false;
        btn.textContent = t('modalChequeSubmit');
        return;
      }

      haptic('success');
      closeModal('modalCheque');
      document.getElementById('chequeAmount').value = '';
      if (document.getElementById('chequeRecipient')) document.getElementById('chequeRecipient').value = '';

      State.lastCreatedChequeId = data.cheque_id;
      const botUser = data.bot_username || State.botUsername || 'sbpbot';
      const inlineCode = data.inline_code || `@${botUser} ${data.cheque_id}`;

      const codeInput = document.getElementById('createdChequeInlineCode');
      if (codeInput) codeInput.value = inlineCode;

      openModal('modalChequeResult');
      await fetchUserData();

    } catch (e) {
      haptic('error');
      showToast('Ошибка сети при создании чека');
    } finally {
      btn.disabled = false;
      btn.textContent = t('modalChequeSubmit');
    }
  });
}

// Global helper for sharing cheques by ID via inline query
window.shareChequeById = function(chequeId) {
  haptic('medium');
  if (!chequeId) {
    const inlineCode = document.getElementById('createdChequeInlineCode')?.value || '';
    chequeId = State.lastCreatedChequeId || inlineCode;
  }
  if (!chequeId) return;

  const botUser = State.botUsername || 'sbpbot';
  const cleanId = (chequeId.match(/ch_[a-zA-Z0-9_-]+/) || [])[0] || chequeId.replace(/^@\w+\s*/, '');
  const textToShare = chequeId.startsWith('@') ? chequeId : `@${botUser} ${cleanId}`;

  // 1. Guaranteed copy to clipboard
  try {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(textToShare);
    }
  } catch (e) {}

  // 2. Enable bot inline mode in WebView params if accessible
  try {
    if (window.Telegram?.WebView?.initParams) {
      window.Telegram.WebView.initParams.tgWebAppBotInline = true;
    }
  } catch (e) {}

  // 3. Try native switchInlineQuery
  let switched = false;
  if (tg?.switchInlineQuery && cleanId) {
    try {
      tg.switchInlineQuery(cleanId, ['users', 'groups', 'channels']);
      switched = true;
    } catch (e) {
      try {
        tg.switchInlineQuery(cleanId);
        switched = true;
      } catch (e2) {}
    }
  }

  // 4. Try native WebView event directly
  if (!switched && cleanId) {
    try {
      if (window.Telegram?.WebView?.postEvent) {
        window.Telegram.WebView.postEvent('web_app_switch_inline_query', false, {
          query: cleanId,
          chat_types: ['users', 'groups', 'channels']
        });
        switched = true;
      }
    } catch (e) {}
  }

  // 5. Open chat selection via t.me share url (t.me is required for isTmeHostname check)
  const tmeShareUrl = `https://t.me/share/url?url=&text=${encodeURIComponent(textToShare)}`;
  try {
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(tmeShareUrl);
    } else if (tg?.openLink) {
      tg.openLink(tmeShareUrl);
    } else {
      window.open(tmeShareUrl, '_blank');
    }
  } catch (e) {
    try {
      if (tg?.openLink) {
        tg.openLink(tmeShareUrl);
      } else {
        window.open(tmeShareUrl, '_blank');
      }
    } catch (err) {}
  }

  showToast(t('toastChequeCopied'));
};

// --- Electronic Receipt Details ---
window.openReceiptModal = function(txId) {
  haptic('light');
  const tx = State.transactions.find(t => t.id === txId);
  if (!tx) return;

  State.activeReceipt = tx;
  const content = document.getElementById('receiptContent');
  if (!content) return;

  const isPos = tx.amount > 0;
  const formatted = `${isPos ? '+' : ''}${tx.amount.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} ⭐️`;

  const chMatch = (tx.title + ' ' + tx.comment + ' ' + (tx.to || '')).match(/ch_[a-zA-Z0-9]+/);
  let chequeInlineSection = '';
  if (chMatch) {
    const chId = chMatch[0];
    const inlineCode = `@${State.botUsername || 'sbpbot'} ${chId}`;
    chequeInlineSection = `
      <div class="receipt-field" style="border-top: 1px dashed var(--border-subtle); padding-top: 10px; margin-top: 6px;">
        <span class="label">Инлайн-код</span>
        <span class="value" style="font-family: monospace; color: var(--gold); font-weight: 700;">${inlineCode}</span>
      </div>
      <div style="display: flex; gap: 8px; margin-top: 8px;">
        <button type="button" class="btn-submit" onclick="navigator.clipboard.writeText('${inlineCode}'); showToast(t('toastChequeCopied'));" style="flex: 1; padding: 10px; font-size: 12px; background: var(--surface-alt); color: var(--text-main); border: 1px solid var(--border-subtle);">
          📋 Скопировать код
        </button>
        <button type="button" class="btn-submit" onclick="shareChequeById('${chId}')" style="flex: 1; padding: 10px; font-size: 12px; background: #007aff;">
          ⚡️ Отправить в чат
        </button>
      </div>
    `;
  }

  content.innerHTML = `
    <div style="text-align: center; margin-bottom: 6px;">
      <div style="font-size: 28px; font-weight: 800; color: ${isPos ? 'var(--green-positive)' : 'var(--text-main)'};">
        ${formatted}
      </div>
      <div style="font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase;">
        ${tx.status || t('receiptExecuted')}
      </div>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptTrx')}</span>
      <span class="value" style="font-family: monospace;">#${tx.id}</span>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptFrom')}</span>
      <span class="value">${tx.from}</span>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptTo')}</span>
      <span class="value">${tx.to}</span>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptDate')}</span>
      <span class="value">${tx.date}</span>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptComment')}</span>
      <span class="value">${tx.comment}</span>
    </div>
    <div class="receipt-field">
      <span class="label">${t('receiptGateway')}</span>
      <span class="value">StaticGram СБП • Stars Gateway</span>
    </div>
    ${chequeInlineSection}
  `;

  openModal('modalReceipt');
};

window.copyReceiptText = async function() {
  haptic('medium');
  if (!State.activeReceipt) return;

  const tx = State.activeReceipt;
  const text = `🧾 ${t('modalReceiptTitle')}\nAmount: ${tx.amount > 0 ? '+' : ''}${tx.amount} ⭐️\nStatus: ${tx.status}\nID: #${tx.id}\nDate: ${tx.date}\nPurpose: ${tx.comment}`;

  try {
    await navigator.clipboard.writeText(text);
    showToast(t('toastReceiptCopied'));
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

  if (State.isLoading) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-tertiary); font-size: 13px;">
        ${t('loadingOps')}
      </div>
    `;
    return;
  }

  if (State.isGuest) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-secondary); font-size: 13px;">
        <div style="font-size: 32px; margin-bottom: 8px;">🔐</div>
        <b>${t('guestNotice')}</b><br><br>
        <a href="https://staticgram.top/sbpbot" target="_blank" class="btn-submit" style="display: inline-block; padding: 10px 20px; text-decoration: none; max-width: 240px;">
          ${t('openBot')}
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
        ${t('noOpsCategory')}
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(tx => {
    let iconClass = 'tx-cheque';
    let icon = '🧾';
    let amountClass = 'neutral';

    if (tx.type === 'transfer') {
      if (tx.amount < 0) {
        iconClass = 'tx-out';
        icon = '↗';
        amountClass = 'negative';
      } else {
        iconClass = 'tx-in';
        icon = '↙';
        amountClass = 'positive';
      }
    } else if (tx.type === 'deposit') {
      iconClass = 'tx-in';
      icon = '↙';
      amountClass = 'positive';
    } else if (tx.type === 'withdrawal') {
      iconClass = 'tx-out';
      icon = '↗';
      amountClass = 'negative';
    }

    const formatted = `${tx.amount > 0 ? '+' : ''}${tx.amount.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} ⭐️`;

    const chMatch = (tx.title + ' ' + tx.comment + ' ' + (tx.to || '')).match(/ch_[a-zA-Z0-9]+/);
    let inlineBadgeHtml = '';
    if (chMatch) {
      const chId = chMatch[0];
      const botUser = State.botUsername || 'sbpbot';
      const inlineCode = `@${botUser} ${chId}`;
      inlineBadgeHtml = `
        <div class="tx-inline-badge" onclick="event.stopPropagation();">
          <span class="tx-inline-code">${inlineCode}</span>
          <button type="button" class="tx-inline-btn" onclick="event.stopPropagation(); navigator.clipboard.writeText('${inlineCode}'); showToast(t('toastChequeCopied'));" title="Скопировать инлайн-код">📋</button>
          <button type="button" class="tx-inline-btn primary" onclick="event.stopPropagation(); shareChequeById('${chId}');" title="Отправить в чат">⚡️</button>
        </div>
      `;
    }

    return `
      <div class="tx-row" onclick="openReceiptModal('${tx.id}')">
        <div class="tx-left">
          <div class="tx-icon-circle ${iconClass}">${icon}</div>
          <div class="tx-meta">
            <span class="tx-name">${tx.title}</span>
            <span class="tx-sub">${tx.date} • ${tx.comment}</span>
            ${inlineBadgeHtml}
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

// --- Active Cheques Management ---
window.renderActiveCheques = function() {
  const container = document.getElementById('activeChequesContainer');
  if (!container) return;

  const tabListBtn = document.getElementById('tabChequeList');
  const count = State.activeCheques ? State.activeCheques.length : 0;
  if (tabListBtn) {
    tabListBtn.textContent = `${t('modalChequeTabList')} (${count})`;
  }

  if (!State.activeCheques || State.activeCheques.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 28px 12px; color: var(--text-tertiary); font-size: 13px;">
        <div style="font-size: 32px; margin-bottom: 8px;">🧾</div>
        <b>${t('noActiveCheques')}</b><br><br>
        <button type="button" class="btn-submit" onclick="switchChequeTab('create')" style="display: inline-block; padding: 8px 18px; font-size: 13px; max-width: 200px;">
          ${t('modalChequeTabCreate')}
        </button>
      </div>
    `;
    return;
  }

  const botUser = State.botUsername || 'sbpbot';
  container.innerHTML = `
    <div class="active-cheques-list">
      ${State.activeCheques.map(ch => {
        const rec = ch.recipient ? `@${ch.recipient}` : (State.lang === 'ru' ? 'Для всех' : 'For everyone');
        const inlineCode = ch.inline_code || `@${botUser} ${ch.cheque_id}`;
        return `
          <div class="active-cheque-card">
            <div class="active-cheque-header">
              <span class="active-cheque-amount">${Number(ch.amount).toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} ⭐️</span>
              <span class="active-cheque-badge">${ch.recipient ? '🔒 ' + rec : '🎁 ' + rec}</span>
            </div>
            <div class="active-cheque-code-wrap">
              <span class="active-cheque-code">${inlineCode}</span>
            </div>
            <div class="active-cheque-actions">
              <button type="button" class="active-cheque-btn" onclick="navigator.clipboard.writeText('${inlineCode}'); showToast(t('toastChequeCopied'));">
                📋 ${State.lang === 'ru' ? 'Скопировать' : 'Copy'}
              </button>
              <button type="button" class="active-cheque-btn share" onclick="shareChequeById('${ch.cheque_id}')">
                ⚡️ ${State.lang === 'ru' ? 'В чат' : 'Share'}
              </button>
              <button type="button" class="active-cheque-btn cancel" onclick="cancelChequeAction('${ch.cheque_id}')" title="${t('btnCancelCheque')}">
                ❌
              </button>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
};

window.cancelChequeAction = async function(chequeId) {
  haptic('medium');
  if (State.isGuest) return;

  const btn = event?.currentTarget;
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/cancel_cheque`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: State.user.user_id,
        cheque_id: chequeId
      })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      haptic('success');
      showToast(t('toastChequeCancelled'));
      await fetchUserData();
      renderActiveCheques();
    } else {
      haptic('error');
      showToast(data.error || 'Ошибка при аннулировании чека');
    }
  } catch (e) {
    haptic('error');
    showToast('Ошибка сети при отмене чека');
  } finally {
    if (btn) btn.disabled = false;
  }
};

function initFilters() {
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      haptic('light');
      filterTransactions(tab.getAttribute('data-filter'));
    });
  });
}

// --- App Bootstrap ---

// --- Boykisser Mascot Logic ---
const BOYKISSER_QUOTES = {
  ru: [
    "Ты любишь переводить звёзды по СБП, да? :3",
    "Ого, какой красивый баланс звёздочек! ✨",
    "Ты целуешь мальчиков или даришь чеки в чатах? UwU",
    "0% комиссии на переводы — это так мило! 🐾",
    "СБП-счёт всего из 5 цифр! Запомнить легче, чем твою улыбку :3",
    "Не забудь подарить чек другу! 🎁",
    "Хэллоуинское настроение! Бууу! 🎃👻",
    "Я тут охраняю твои звёздочки! Муррр 😸"
  ],
  en: [
    "You like transferring Telegram Stars via SBP, don't you? :3",
    "Wow, look at all those shiny stars! ✨",
    "You like kissing boys or creating vouchers? UwU",
    "0% fee on transfers is so cute! 🐾",
    "5-digit account number is so easy to remember :3",
    "Don't forget to send a gift cheque to your friend! 🎁",
    "Spooky Halloween vibes! Booo! 🎃👻",
    "I'm purr-tecting your stars! Purrr 😸"
  ]
};

window.toggleBoykisserSetting = function(forcedVal) {
  haptic('selection');
  const toggle = document.getElementById('toggleBoykisser');
  const isEnabled = typeof forcedVal === 'boolean' ? forcedVal : !(toggle ? toggle.checked : true);
  if (toggle) toggle.checked = isEnabled;
  localStorage.setItem('sbp_boykisser_enabled', isEnabled ? 'true' : 'false');
  applyBoykisserVisibility();
};

window.hideBoykisserQuick = function() {
  haptic('light');
  window.toggleBoykisserSetting(false);
  showToast(State.lang === 'ru' ? 'Бойкиссер скрыт. Включить можно в Настройках ⚙️' : 'Boykisser hidden. Re-enable in Settings ⚙️');
};

function applyBoykisserVisibility() {
  const isEnabled = localStorage.getItem('sbp_boykisser_enabled') !== 'false'; // default true
  const widget = document.getElementById('boykisserWidget');
  const toggle = document.getElementById('toggleBoykisser');
  if (widget) {
    widget.style.display = isEnabled ? 'flex' : 'none';
  }
  if (toggle) {
    toggle.checked = isEnabled;
  }
}

window.onBoykisserTap = function() {
  haptic('medium');
  const bubble = document.getElementById('boykisserBubbleText');
  const img = document.getElementById('boykisserImg');
  const quotes = BOYKISSER_QUOTES[State.lang] || BOYKISSER_QUOTES.ru;
  const quote = quotes[Math.floor(Math.random() * quotes.length)];
  
  if (bubble) {
    bubble.style.transform = 'scale(0.95)';
    setTimeout(() => {
      bubble.textContent = quote;
      bubble.style.transform = 'scale(1)';
    }, 120);
  }
  
  if (img) {
    img.style.transform = 'scale(1.25) rotate(' + (Math.random() > 0.5 ? '12deg' : '-12deg') + ')';
    setTimeout(() => {
      img.style.transform = '';
    }, 300);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initThemeAndLang();
  applyBoykisserVisibility();
  initBalanceToggle();
  initAccountCopy();
  initModals();
  initTransferSubmission();
  initChequeSubmission();
  initFilters();
  initTelegram();
});
