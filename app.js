/**
 * SBP StaticGram Stars Bank тАв Material Design 3 Web App
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
    brandStatus: '╨Ю╨╜╨╗╨░╨╣╨╜ ╤И╨╗╤О╨╖',
    guestGreeting: '╨У╨╛╤Б╤В╨╡╨▓╨╛╨╣ ╤А╨╡╨╢╨╕╨╝',
    guestSubtext: '╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╤З╨╡╤А╨╡╨╖ Telegram ╨▒╨╛╤В╨░ @sbpbot',
    guestNotice: '╨Я╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╡ ╨╛╤В╨║╤А╤Л╤В╨╛ ╨▓ ╤А╨╡╨╢╨╕╨╝╨╡ ╨┐╤А╨╛╤Б╨╝╨╛╤В╤А╨░. ╨Ф╨╗╤П ╤Г╨┐╤А╨░╨▓╨╗╨╡╨╜╨╕╤П ╨▒╨░╨╗╨░╨╜╤Б╨╛╨╝ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨б╨С╨Я ╤З╨╡╤А╨╡╨╖ ╨╛╤Д╨╕╤Ж╨╕╨░╨╗╤М╨╜╨╛╨│╨╛ ╨▒╨╛╤В╨░.',
    userGreeting: '╨Я╤А╨╕╨▓╨╡╤В, {name}!',
    userSubtext: '{label} тАв ╨б╨╡╤В╤М ╨░╨║╤В╨╕╨▓╨╜╨░',
    networkActive: '╨б╨╡╤В╤М ╨░╨║╤В╨╕╨▓╨╜╨░',
    balanceLabel: '╨Ф╨Ю╨б╨в╨г╨Я╨Э╨л╨Щ ╨С╨Р╨Ы╨Р╨Э╨б',
    balanceSub: '╨Ь╨│╨╜╨╛╨▓╨╡╨╜╨╜╤Л╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╤Л ╨▓╨╜╤Г╤В╤А╨╕ ╤Б╨╡╤В╨╕ ╨▒╨╡╨╖ ╨║╨╛╨╝╨╕╤Б╤Б╨╕╨╕',
    inEscrow: '╨Т ╤А╨╡╨╖╨╡╤А╨▓╨╡',
    activeReserve: '╨Р╨║╤В╨╕╨▓╨╜╤Л╨╡ ╤А╨╡╨╖╨╡╤А╨▓╤Л: {amount} тнРя╕П',
    viewCheques: '╨б╨╝╨╛╤В╤А╨╡╤В╤М ╤З╨╡╨║╨╕',
    actionTransfer: '╨Я╨╡╤А╨╡╨▓╨╡╤Б╤В╨╕',
    actionTransferCaption: '╨Я╨╛ @username ╨╕╨╗╨╕ ╤Б╤З╤С╤В╤Г',
    actionDeposit: '╨Я╨╛╨┐╨╛╨╗╨╜╨╕╤В╤М',
    actionDepositCaption: 'Telegram Stars',
    actionWithdraw: '╨Т╤Л╨▓╨╡╤Б╤В╨╕',
    actionWithdrawCaption: '╨Э╨░ ╨░╨║╨║╨░╤Г╨╜╤В',
    actionCheque: '╨б╨╛╨╖╨┤╨░╤В╤М ╤З╨╡╨║',
    actionChequeCaption: '╨Ф╨╗╤П ╨╛╤В╨┐╤А╨░╨▓╨║╨╕ ╨▓ ╤З╨░╤В╤Л',
    newsTag: 'ЁЯУв ╨Ю╨д╨Ш╨ж╨Ш╨Р╨Ы╨м╨Э╨л╨Щ ╨Ъ╨Р╨Э╨Р╨Ы ╨б╨С╨Я',
    newsTitle: '╨Ь╨│╨╜╨╛╨▓╨╡╨╜╨╜╤Л╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╤Л, ╨╝╤Г╨╗╤М╤В╨╕╨▓╨░╨╗╤О╤В╨╜╤Л╨╣ ╤Г╤З╤С╤В ╨╕ ╤З╨╡╨║╨╕',
    newsDesc: '╨Э╨╛╨▓╨╛╤Б╤В╨╕ ╤Б╨╕╤Б╤В╨╡╨╝╤Л ╨▒╤Л╤Б╤В╤А╤Л╤Е ╨┐╨╗╨░╤В╨╡╨╢╨╡╨╣, ╨╛╨▒╨╜╨╛╨▓╨╗╨╡╨╜╨╕╤П ╤И╨╗╤О╨╖╨░ ╨╕ ╨║╨▓╨╕╤В╨░╨╜╤Ж╨╕╨╕ ╨╜╨╛╨▓╨╛╨│╨╛ ╨┐╨╛╨║╨╛╨╗╨╡╨╜╨╕╤П.',
    newsBtn: '╨Я╨╛╨┤╨┐╨╕╤Б╨░╤В╤М╤Б╤П ╨╜╨░ @sbpnews',
    historyTitle: '╨Ш╤Б╤В╨╛╤А╨╕╤П ╨╛╨┐╨╡╤А╨░╤Ж╨╕╨╣',
    historySub: '╨Т╤Б╨╡ ╤В╤А╨░╨╜╨╖╨░╨║╤Ж╨╕╨╕, ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П ╨╕ ╤З╨╡╨║╨╕ ╤Б ╤Н╨╗╨╡╨║╤В╤А╨╛╨╜╨╜╤Л╨╝╨╕ ╨║╨▓╨╕╤В╨░╨╜╤Ж╨╕╤П╨╝╨╕',
    filterAll: '╨Т╤Б╨╡',
    filterTransfer: '╨Я╨╡╤А╨╡╨▓╨╛╨┤╤Л',
    filterDeposit: '╨Я╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П',
    filterCheque: '╨з╨╡╨║╨╕',
    loadingOps: '╨Ч╨░╨│╤А╤Г╨╖╨║╨░ ╨╛╨┐╨╡╤А╨░╤Ж╨╕╨╣...',
    noOpsCategory: '╨Т ╤Н╤В╨╛╨╣ ╨║╨░╤В╨╡╨│╨╛╤А╨╕╨╕ ╨┐╨╛╨║╨░ ╨╜╨╡╤В ╨╛╨┐╨╡╤А╨░╤Ж╨╕╨╣',
    openBot: '╨Ю╤В╨║╤А╤Л╤В╤М ╨▒╨╛╤В╨░',
    footerPlatform: '╨б╨С╨Я StaticGram Stars тАв ╨Я╨╗╨░╤В╤Д╨╛╤А╨╝╨░ ╨╝╨│╨╜╨╛╨▓╨╡╨╜╨╜╤Л╤Е ╨┐╨╗╨░╤В╨╡╨╢╨╡╨╣',
    footerNews: '╨Э╨╛╨▓╨╛╤Б╤В╨╕',
    footerBot: 'Telegram ╨С╨╛╤В',

    // Settings
    settingsTitle: 'тЪЩя╕П ╨Э╨░╤Б╤В╤А╨╛╨╣╨║╨╕',
    settingsTheme: '╨в╨╡╨╝╨░ ╨╛╤Д╨╛╤А╨╝╨╗╨╡╨╜╨╕╤П',
    themeLight: '╨б╨▓╨╡╤В╨╗╨░╤П',
    themeDark: '╨в╤С╨╝╨╜╨░╤П',
    themeSystem: '╨б╨╕╤Б╤В╨╡╨╝╨╜╨░╤П',
    settingsLang: '╨п╨╖╤Л╨║ ╨╕╨╜╤В╨╡╤А╤Д╨╡╨╣╤Б╨░',
    settingsAccount: '╨Р╨║╨║╨░╤Г╨╜╤В ╨б╨С╨Я',
    settingsUser: '╨Я╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤М',
    settingsAccountNum: '╨Э╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░',
    settingsStatus: '╨б╤В╨░╤В╤Г╤Б ╤И╨╗╤О╨╖╨░',
    settingsLinks: '╨Я╨╛╨╗╨╡╨╖╨╜╤Л╨╡ ╤Б╤Б╤Л╨╗╨║╨╕',

    // Modals
    modalTransferTitle: 'ЁЯТ╕ ╨Я╨╡╤А╨╡╨▓╨╛╨┤ ╨┐╨╛ ╨б╨С╨Я',
    modalTransferRecipient: '╨Я╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤М (@username, ID ╨╕╨╗╨╕ ╨╜╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░ ╨б╨С╨Я)',
    modalTransferAmount: '╨б╤Г╨╝╨╝╨░ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░ (тнРя╕П)',
    modalTransferComment: '╨Э╨░╨╖╨╜╨░╤З╨╡╨╜╨╕╨╡ ╨┐╨╗╨░╤В╨╡╨╢╨░ / ╨║╨╛╨╝╨╝╨╡╨╜╤В╨░╤А╨╕╨╣ (╨╜╨╡╨╛╨▒╤П╨╖╨░╤В╨╡╨╗╤М╨╜╨╛)',
    modalTransferSubmit: '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╤М ╨┐╨╡╤А╨╡╨▓╨╛╨┤',

    modalDepositTitle: 'ЁЯУе ╨Я╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╡ ╤Б╤З╤С╤В╨░ Stars',
    modalDepositDesc: '╨Ю╨┐╨╗╨░╤В╨░ ╨┐╤А╨╛╨╕╨╖╨▓╨╛╨┤╨╕╤В╤Б╤П ╨╝╨│╨╜╨╛╨▓╨╡╨╜╨╜╨╛ ╨┐╤А╤П╨╝╨╛ ╨▓ ╨┐╤А╨╕╨╗╨╛╨╢╨╡╨╜╨╕╨╕ ╤З╨╡╤А╨╡╨╖ ╨┐╨╗╨░╤В╤С╨╢╨╜╤Л╨╣ ╤И╨╗╤О╨╖ Telegram Stars (XTR):',
    modalDepositCustomLabel: '╨Я╤А╨╛╨╕╨╖╨▓╨╛╨╗╤М╨╜╨░╤П ╤Б╤Г╨╝╨╝╨░ ╨╖╨▓╤С╨╖╨┤ (тнРя╕П)',
    modalDepositBuy: '╨Ъ╤Г╨┐╨╕╤В╤М',
    modalDepositPresets: '╨С╤Л╤Б╤В╤А╤Л╨╣ ╨▓╤Л╨▒╨╛╤А ╨┐╨░╨║╨╡╤В╨░:',

    modalWithdrawTitle: 'ЁЯУд ╨Т╤Л╨▓╨╛╨┤ ╨╖╨▓╤С╨╖╨┤ Stars',
    modalWithdrawDesc: '╨Ф╨╗╤П ╨┐╤А╤П╨╝╨╛╨│╨╛ ╨▓╤Л╨▓╨╛╨┤╨░ ╨╖╨▓╤С╨╖╨┤ ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣╤В╨╡ ╨║╨╛╨╝╨░╨╜╨┤╤Г /withdraw ╨▓ Telegram-╨▒╨╛╤В╨╡ ╨╗╨╕╨▒╨╛ ╨╛╤В╨┐╤А╨░╨▓╤М╤В╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤ ╨╜╨░ ╨╜╤Г╨╢╨╜╤Л╨╣ ╨░╨║╨║╨░╤Г╨╜╤В ╨б╨С╨Я.',
    modalWithdrawBtn: '╨Я╨╡╤А╨╡╨╣╤В╨╕ ╨║ ╨▓╤Л╨▓╨╛╨┤╤Г ╨▓ ╨▒╨╛╤В╨╡',

    modalChequeTitle: 'ЁЯз╛ ╨б╨╛╨╖╨┤╨░╤В╤М ╤З╨╡╨║ ╨б╨С╨Я',
    modalChequeAmount: '╨Э╨╛╨╝╨╕╨╜╨░╨╗ ╤З╨╡╨║╨░ (тнРя╕П)',
    modalChequeType: '╨в╨╕╨┐ ╤З╨╡╨║╨░',
    modalChequeAny: 'ЁЯМР ╨Ф╨╗╤П ╨▓╤Б╨╡╤Е (╨░╨║╤В╨╕╨▓╨╕╤А╤Г╨╡╤В ╨┐╨╡╤А╨▓╤Л╨╣ ╨╜╨░╨╢╨░╨▓╤И╨╕╨╣ ╨▓ ╤З╨░╤В╨╡)',
    modalChequeUser: 'ЁЯФТ ╨Ш╨╝╨╡╨╜╨╜╨╛╨╣ ╤З╨╡╨║ (╤В╨╛╨╗╤М╨║╨╛ ╨┤╨╗╤П ╤Г╨║╨░╨╖╨░╨╜╨╜╨╛╨│╨╛ @username)',
    modalChequeRecipient: '╨Ш╨╝╤П ╨┐╨╛╨╗╤М╨╖╨╛╨▓╨░╤В╨╡╨╗╤П ╨┐╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤П',
    modalChequeComment: '╨Ъ╨╛╨╝╨╝╨╡╨╜╤В╨░╤А╨╕╨╣ ╨║ ╤З╨╡╨║╤Г',
    modalChequeSubmit: '╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤З╨╡╨║',

    modalChequeResultTitle: 'ЁЯОЙ ╨з╨╡╨║ ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╤Б╨╛╨╖╨┤╨░╨╜!',
    modalChequeResultDesc: '╨Ч╨▓╤С╨╖╨┤╤Л ╨╖╨░╤А╨╡╨╖╨╡╤А╨▓╨╕╤А╨╛╨▓╨░╨╜╤Л ╨▓ Escrow. ╨Ю╤В╨┐╤А╨░╨▓╤М╤В╨╡ ╤Б╤Б╤Л╨╗╨║╤Г ╨╜╨░ ╤З╨╡╨║ ╨▓ ╨╗╤О╨▒╨╛╨╣ ╤З╨░╤В Telegram:',
    modalChequeResultLink: '╨б╤Б╤Л╨╗╨║╨░ ╨╜╨░ ╨░╨║╤В╨╕╨▓╨░╤Ж╨╕╤О ╤З╨╡╨║╨░',
    modalChequeResultCopy: '╨б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╤В╤М ╤Б╤Б╤Л╨╗╨║╤Г',
    modalChequeResultShare: '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╤М ╨▓ ╤З╨░╤В',

    modalReceiptTitle: '╨н╨╗╨╡╨║╤В╤А╨╛╨╜╨╜╤Л╨╣ ╤З╨╡╨║',
    modalReceiptCopy: '╨б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╤В╤М ╨┤╨░╨╜╨╜╤Л╨╡ ╤З╨╡╨║╨░',
    receiptTrx: '╨Э╨╛╨╝╨╡╤А ╨║╨▓╨╕╤В╨░╨╜╤Ж╨╕╨╕',
    receiptFrom: '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╨╡╨╗╤М',
    receiptTo: '╨Я╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤М',
    receiptDate: '╨Ф╨░╤В╨░ ╨╕ ╨▓╤А╨╡╨╝╤П',
    receiptComment: '╨Э╨░╨╖╨╜╨░╤З╨╡╨╜╨╕╨╡ ╨┐╨╗╨░╤В╨╡╨╢╨░',
    receiptGateway: '╨Я╨╗╨░╤В╤С╨╢╨╜╤Л╨╣ ╤И╨╗╤О╨╖',
    receiptExecuted: '╨Ш╤Б╨┐╨╛╨╗╨╜╨╡╨╜',

    // Notifications & Toasts
    toastCopiedAccount: '╨Э╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜: {acc}',
    toastOpenBotForAcc: '╨Ю╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ ╨▓ Telegram ╨┤╨╗╤П ╨┐╨╛╨╗╤Г╤З╨╡╨╜╨╕╤П ╤Б╤З╤С╤В╨░',
    toastOpenBotForTransfer: '╨Ф╨╗╤П ╨╛╤В╨┐╤А╨░╨▓╨║╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot',
    toastOpenBotForDeposit: '╨Ф╨╗╤П ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜╨╕╤П ╨▒╨░╨╗╨░╨╜╤Б╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot',
    toastOpenBotForCheque: '╨Ф╨╗╤П ╤Б╨╛╨╖╨┤╨░╨╜╨╕╤П ╤З╨╡╨║╨░ ╨╛╤В╨║╤А╨╛╨╣╤В╨╡ ╨▒╨╛╤В╨░ @sbpbot',
    toastPreparingInvoice: '╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╤Б╤З╤С╤В╨░ ╨╜╨░ {amount} тнРя╕П...',
    toastDepositSuccess: '╨С╨░╨╗╨░╨╜╤Б ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨┐╨╛╨┐╨╛╨╗╨╜╨╡╨╜ ╨╜╨░ +{amount} тнРя╕П!',
    toastDepositCancel: '╨Ю╨┐╨╗╨░╤В╨░ ╨╛╤В╨╝╨╡╨╜╨╡╨╜╨░',
    toastDepositFail: '╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨┐╤А╨╛╨▓╨╡╨┤╨╡╨╜╨╕╨╕ ╨┐╨╗╨░╤В╨╡╨╢╨░',
    toastSpecifyRecipient: '╨г╨║╨░╨╢╨╕╤В╨╡ ╨┐╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤П (@username, ID ╨╕╨╗╨╕ ╨╜╨╛╨╝╨╡╤А ╤Б╤З╤С╤В╨░)',
    toastSpecifyAmount: '╨г╨║╨░╨╢╨╕╤В╨╡ ╨║╨╛╤А╤А╨╡╨║╤В╨╜╤Г╤О ╤Б╤Г╨╝╨╝╤Г',
    toastInsufficientBalance: '╨Э╨╡╨┤╨╛╤Б╤В╨░╤В╨╛╤З╨╜╨╛ ╨╖╨▓╤С╨╖╨┤. ╨Т╨░╤И ╨▒╨░╨╗╨░╨╜╤Б: {bal} тнРя╕П',
    toastTransferSending: '╨Ю╤В╨┐╤А╨░╨▓╨║╨░...',
    toastTransferSubmit: '╨Ю╤В╨┐╤А╨░╨▓╨╕╤В╤М ╨┐╨╡╤А╨╡╨▓╨╛╨┤',
    toastTransferSuccess: '╨Я╨╡╤А╨╡╨▓╨╛╨┤ {amount} тнРя╕П ╤Г╤Б╨┐╨╡╤И╨╜╨╛ ╨╛╤В╨┐╤А╨░╨▓╨╗╨╡╨╜!',
    toastChequeSpecifyNominal: '╨г╨║╨░╨╢╨╕╤В╨╡ ╨╜╨╛╨╝╨╕╨╜╨░╨╗ ╤З╨╡╨║╨░',
    toastChequeInsufficient: '╨Э╨╡╨┤╨╛╤Б╤В╨░╤В╨╛╤З╨╜╨╛ ╨╖╨▓╤С╨╖╨┤ ╨╜╨░ ╨▒╨░╨╗╨░╨╜╤Б╨╡ ╨┤╨╗╤П ╤А╨╡╨╖╨╡╤А╨▓╨╕╤А╨╛╨▓╨░╨╜╨╕╤П ╤З╨╡╨║╨░',
    toastChequeSpecifyUser: '╨г╨║╨░╨╢╨╕╤В╨╡ @username ╨┐╨╛╨╗╤Г╤З╨░╤В╨╡╨╗╤П',
    toastChequeCreating: '╨б╨╛╨╖╨┤╨░╨╜╨╕╨╡...',
    toastChequeSubmit: '╨б╨│╨╡╨╜╨╡╤А╨╕╤А╨╛╨▓╨░╤В╤М ╤З╨╡╨║',
    toastChequeCopied: '╨б╤Б╤Л╨╗╨║╨░ ╨╜╨░ ╤З╨╡╨║ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜╨░ ╨▓ ╨▒╤Г╤Д╨╡╤А ╨╛╨▒╨╝╨╡╨╜╨░!',
    toastReceiptCopied: '╨Ф╨░╨╜╨╜╤Л╨╡ ╤З╨╡╨║╨░ ╤Б╨║╨╛╨┐╨╕╤А╨╛╨▓╨░╨╜╤Л ╨▓ ╨▒╤Г╤Д╨╡╤А!'
  },
  en: {
    brandName: 'StaticGram Stars',
    brandStatus: 'Online Gateway',
    guestGreeting: 'Guest Mode',
    guestSubtext: 'Open the app via Telegram bot @sbpbot',
    guestNotice: 'The app is in read-only view. To manage balance and make transfers, open SBP via the official bot.',
    userGreeting: 'Hello, {name}!',
    userSubtext: '{label} тАв Network Active',
    networkActive: 'Network Active',
    balanceLabel: 'AVAILABLE BALANCE',
    balanceSub: 'Instant network transfers with zero fees',
    inEscrow: 'In Escrow',
    activeReserve: 'Active reserves: {amount} тнРя╕П',
    viewCheques: 'View Cheques',
    actionTransfer: 'Transfer',
    actionTransferCaption: 'By @username or account',
    actionDeposit: 'Top Up',
    actionDepositCaption: 'Telegram Stars',
    actionWithdraw: 'Withdraw',
    actionWithdrawCaption: 'To account',
    actionCheque: 'Create Cheque',
    actionChequeCaption: 'For sharing in chats',
    newsTag: 'ЁЯУв OFFICIAL SBP CHANNEL',
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
    footerPlatform: 'SBP StaticGram Stars тАв Instant Payment Platform',
    footerNews: 'News',
    footerBot: 'Telegram Bot',

    // Settings
    settingsTitle: 'тЪЩя╕П Settings',
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
    modalTransferTitle: 'ЁЯТ╕ Transfer via SBP',
    modalTransferRecipient: 'Recipient (@username, ID or SBP account number)',
    modalTransferAmount: 'Transfer amount (тнРя╕П)',
    modalTransferComment: 'Payment purpose / comment (optional)',
    modalTransferSubmit: 'Send Transfer',

    modalDepositTitle: 'ЁЯУе Top Up Stars Balance',
    modalDepositDesc: 'Pay instantly inside the Telegram Mini App using the official Telegram Stars (XTR) gateway:',
    modalDepositCustomLabel: 'Custom star amount (тнРя╕П)',
    modalDepositBuy: 'Buy',
    modalDepositPresets: 'Quick package selection:',

    modalWithdrawTitle: 'ЁЯУд Withdraw Stars',
    modalWithdrawDesc: 'For direct withdrawal of stars, use the /withdraw command in the Telegram bot or send a transfer to your SBP account.',
    modalWithdrawBtn: 'Go to Withdraw in Bot',

    modalChequeTitle: 'ЁЯз╛ Create SBP Cheque',
    modalChequeAmount: 'Cheque nominal (тнРя╕П)',
    modalChequeType: 'Cheque type',
    modalChequeAny: 'ЁЯМР For everyone (first user to click in chat claims it)',
    modalChequeUser: 'ЁЯФТ Named cheque (only for specified @username)',
    modalChequeRecipient: 'Recipient username',
    modalChequeComment: 'Cheque comment',
    modalChequeSubmit: 'Generate Cheque',

    modalChequeResultTitle: 'ЁЯОЙ Cheque Created Successfully!',
    modalChequeResultDesc: 'Stars reserved in Escrow. Send the activation link to any Telegram chat:',
    modalChequeResultLink: 'Cheque activation link',
    modalChequeResultCopy: 'Copy Link',
    modalChequeResultShare: 'Share to Chat',

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
    toastOpenBotForCheque: 'To create cheques, open @sbpbot',
    toastPreparingInvoice: 'Preparing invoice for {amount} тнРя╕П...',
    toastDepositSuccess: 'Balance topped up by +{amount} тнРя╕П!',
    toastDepositCancel: 'Payment cancelled',
    toastDepositFail: 'Payment error',
    toastSpecifyRecipient: 'Please specify recipient (@username, ID or account)',
    toastSpecifyAmount: 'Please specify valid amount',
    toastInsufficientBalance: 'Insufficient stars. Your balance: {bal} тнРя╕П',
    toastTransferSending: 'Sending...',
    toastTransferSubmit: 'Send Transfer',
    toastTransferSuccess: 'Transfer of {amount} тнРя╕П sent!',
    toastChequeSpecifyNominal: 'Please enter cheque nominal',
    toastChequeInsufficient: 'Insufficient stars on balance to reserve cheque',
    toastChequeSpecifyUser: 'Please specify recipient @username',
    toastChequeCreating: 'Creating...',
    toastChequeSubmit: 'Generate Cheque',
    toastChequeCopied: 'Cheque link copied to clipboard!',
    toastReceiptCopied: 'Receipt details copied to clipboard!'
  }
};

// --- Application State ---
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
  document.getElementById('themeOptSystem')?.classList.toggle('active', preference === 'system');

  const resolvedTheme = preference === 'system' ? getSystemTheme() : preference;
  document.documentElement.setAttribute('data-theme', resolvedTheme);

  try {
    const bgColor = resolvedTheme === 'dark' ? '#0C0A09' : '#F6F2ED';
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
    if (accountNumEl) accountNumEl.textContent = State.user.account_number || 'тАФ';
  } else {
    if (usernameEl) usernameEl.textContent = '╨У╨╛╤Б╤В╤М (Guest)';
    if (accountNumEl) accountNumEl.textContent = '╨Э╨╡ ╨┐╨╛╨┤╨║╨╗╤О╤З╤С╨╜';
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
    State.firstName = tgUser.first_name || '╨Ъ╨╗╨╕╨╡╨╜╤В';
  } else if (urlParams.get('user_id')) {
    State.userId = parseInt(urlParams.get('user_id'), 10);
    State.username = urlParams.get('username') || null;
    State.firstName = urlParams.get('first_name') || '╨Ъ╨╗╨╕╨╡╨╜╤В';
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
    State.accountNumber = 'тАФ';

    if (greetingEl) greetingEl.textContent = t('guestGreeting');
    if (subtextEl) subtextEl.textContent = t('guestSubtext');
    if (accountEl) accountEl.textContent = 'тАФ';

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
    valEl.textContent = State.isBalanceHidden ? 'тАвтАвтАвтАвтАвтАв' : State.balance.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US');
  }

  const escrowStrip = document.getElementById('escrowStrip');
  const escrowTotal = document.getElementById('escrowTotal');
  if (escrowTotal) {
    escrowTotal.textContent = `${State.escrow.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} тнРя╕П`;
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
        showToast(t('toastChequeCopied'));
      } catch (e) {
        showToast(url);
      }
    }
  });

  document.getElementById('btnShareChequeLink')?.addEventListener('click', () => {
    haptic('light');
    const url = document.getElementById('createdChequeUrl')?.value;
    if (url) {
      const shareText = State.lang === 'ru' ? 'тЪбя╕П ╨Р╨║╤В╨╕╨▓╨╕╤А╤Г╨╣╤В╨╡ ╤З╨╡╨║ ╨б╨С╨Я!' : 'тЪбя╕П Claim SBP Cheque!';
      const shareUrl = `https://staticgram.top/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(shareText)}`;
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(shareUrl);
      } else {
        window.open(shareUrl, '_blank');
      }
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
      // In-app Telegram WebApp Stars Checkout
      if (tg?.openInvoice) {
        tg.openInvoice(data.invoice_link, (status) => {
          if (status === 'paid') {
            haptic('success');
            showToast(t('toastDepositSuccess', { amount }));
            closeModal('modalDeposit');
            // Allow server to process webhook and update balance
            setTimeout(fetchUserData, 800);
            setTimeout(fetchUserData, 2500);
          } else if (status === 'cancelled') {
            showToast(t('toastDepositCancel'));
          } else {
            showToast(t('toastDepositFail'));
          }
        });
      } else {
        // Desktop browser fallback
        window.open(data.invoice_link, '_blank');
        closeModal('modalDeposit');
      }
    } else if (data.bot_url) {
      if (tg?.openTelegramLink) {
        tg.openTelegramLink(data.bot_url);
      } else {
        window.open(data.bot_url, '_blank');
      }
      closeModal('modalDeposit');
    }
  } catch (e) {
    console.error('Deposit invoice error:', e);
    showToast(t('toastDepositFail'));
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
        showToast(data.error || '╨Ю╤И╨╕╨▒╨║╨░ ╨┐╤А╨╕ ╨▓╤Л╨┐╨╛╨╗╨╜╨╡╨╜╨╕╨╕ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░');
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
      showToast('╨Ю╤И╨╕╨▒╨║╨░ ╤Б╨╡╤В╨╕ ╨┐╤А╨╕ ╨╛╤В╨┐╤А╨░╨▓╨║╨╡ ╨┐╨╡╤А╨╡╨▓╨╛╨┤╨░');
    } finally {
      btn.disabled = false;
      btn.textContent = t('modalTransferSubmit');
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
        showToast(data.error || '╨Э╨╡ ╤Г╨┤╨░╨╗╨╛╤Б╤М ╤Б╨╛╨╖╨┤╨░╤В╤М ╤З╨╡╨║');
        btn.disabled = false;
        btn.textContent = t('modalChequeSubmit');
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
      btn.textContent = t('modalChequeSubmit');
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
  const formatted = `${isPos ? '+' : ''}${tx.amount.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} тнРя╕П`;

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
      <span class="value">StaticGram ╨б╨С╨Я тАв Stars Gateway</span>
    </div>
  `;

  openModal('modalReceipt');
};

window.copyReceiptText = async function() {
  haptic('medium');
  if (!State.activeReceipt) return;

  const tx = State.activeReceipt;
  const text = `ЁЯз╛ ${t('modalReceiptTitle')}\nAmount: ${tx.amount > 0 ? '+' : ''}${tx.amount} тнРя╕П\nStatus: ${tx.status}\nID: #${tx.id}\nDate: ${tx.date}\nPurpose: ${tx.comment}`;

  try {
    await navigator.clipboard.writeText(text);
    showToast(t('toastReceiptCopied'));
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
        ${t('loadingOps')}
      </div>
    `;
    return;
  }

  if (State.isGuest) {
    container.innerHTML = `
      <div style="text-align: center; padding: 32px 16px; color: var(--text-secondary); font-size: 13px;">
        <div style="font-size: 32px; margin-bottom: 8px;">ЁЯФР</div>
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

    const formatted = `${tx.amount > 0 ? '+' : ''}${tx.amount.toLocaleString(State.lang === 'ru' ? 'ru-RU' : 'en-US')} тнРя╕П`;

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
  initThemeAndLang();
  initBalanceToggle();
  initAccountCopy();
  initModals();
  initTransferSubmission();
  initChequeSubmission();
  initFilters();
  initTelegram();
});
