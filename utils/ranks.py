from typing import Optional, Dict, Any, List

RANKS = [
    {
        "level": 1,
        "title": "🥉 Новичок",
        "name": "Новичок",
        "icon": "🥉",
        "threshold": 0,
        "desc": "Базовый уровень участника СБП",
        "perk": "Переводы без комиссии и чеки в чаты"
    },
    {
        "level": 2,
        "title": "🥈 Клиент",
        "name": "Клиент",
        "icon": "🥈",
        "threshold": 50,
        "desc": "Активный пользователь экосистемы",
        "perk": "Серебряный бейдж в чеках и визитке"
    },
    {
        "level": 3,
        "title": "🥇 Резидент",
        "name": "Резидент",
        "icon": "🥇",
        "threshold": 250,
        "desc": "Проверенный частый участник",
        "perk": "Золотой статус доверия"
    },
    {
        "level": 4,
        "title": "💎 Премиум",
        "name": "Премиум",
        "icon": "💎",
        "threshold": 1000,
        "desc": "Премиальный оборот звёзд",
        "perk": "Платиновый бейдж и приоритетная поддержка"
    },
    {
        "level": 5,
        "title": "👑 VIP Магнат",
        "name": "VIP Магнат",
        "icon": "👑",
        "threshold": 5000,
        "desc": "Элитный клиент СБП Банка",
        "perk": "Корона в профиле и эксклюзивный статус"
    },
    {
        "level": 6,
        "title": "🔱 Легенда",
        "name": "Легенда",
        "icon": "🔱",
        "threshold": 25000,
        "desc": "Высшая ступень финансового капитала",
        "perk": "Статус топ-инвестора сервиса"
    }
]


def calculate_rank(turnover: int, custom_rank: Optional[str] = None) -> Dict[str, Any]:
    """Calculates user rank info from turnover, respecting any custom admin rank override."""
    if custom_rank and custom_rank.strip():
        c_title = custom_rank.strip()
        # Extract first emoji as icon if available, else standard crown
        icon = c_title.split()[0] if c_title else "👑"
        return {
            "title": c_title,
            "name": c_title,
            "icon": icon,
            "is_custom": True,
            "level": 99,
            "turnover": int(turnover),
            "desc": "Персональный статус от администрации СБП",
            "perk": "Эксклюзивные индивидуальные привилегии",
            "next_title": None,
            "next_threshold": None,
            "to_next": 0,
            "progress_pct": 100,
            "progress_bar": "██████████"
        }

    turnover = max(0, int(turnover or 0))
    current_tier = RANKS[0]
    next_tier = None
    tier_idx = 0

    for idx, tier in enumerate(RANKS):
        if turnover >= tier["threshold"]:
            current_tier = tier
            tier_idx = idx
        else:
            break

    if tier_idx < len(RANKS) - 1:
        next_tier = RANKS[tier_idx + 1]
        cur_th = current_tier["threshold"]
        nxt_th = next_tier["threshold"]
        span = max(1, nxt_th - cur_th)
        progress = max(0, turnover - cur_th)
        pct = min(99, int((progress / span) * 100))
        to_next = max(0, nxt_th - turnover)
    else:
        next_tier = None
        pct = 100
        to_next = 0

    filled = min(10, max(0, pct // 10))
    empty = 10 - filled
    bar = "█" * filled + "░" * empty

    return {
        "title": current_tier["title"],
        "name": current_tier["name"],
        "icon": current_tier["icon"],
        "is_custom": False,
        "level": current_tier["level"],
        "turnover": turnover,
        "desc": current_tier["desc"],
        "perk": current_tier["perk"],
        "next_title": next_tier["title"] if next_tier else None,
        "next_threshold": next_tier["threshold"] if next_tier else None,
        "to_next": to_next,
        "progress_pct": pct,
        "progress_bar": bar
    }


def format_rank_view_text(user: Dict[str, Any], rank_info: Dict[str, Any]) -> str:
    """Detailed visual card for the user's rank status screen."""
    t_stars = rank_info["turnover"]
    title = rank_info["title"]
    bar = rank_info["progress_bar"]
    pct = rank_info["progress_pct"]

    if rank_info["is_custom"]:
        prog_block = (
            f"✨ <b>Вам присвоен особый статус!</b>\n"
            f"<i>{rank_info['desc']}</i>\n"
        )
    elif rank_info["next_title"]:
        nxt = rank_info["next_title"]
        rem = rank_info["to_next"]
        prog_block = (
            f"📈 <b>Прогресс до {nxt}:</b>\n"
            f"<code>[{bar}]</code> <b>{pct}%</b>\n"
            f"<i>Осталось набрать: <b>{rem:,} ⭐️</b> оборота</i>\n"
        )
    else:
        prog_block = (
            f"🏆 <b>Вы достигли максимального ранга!</b>\n"
            f"<code>[{bar}]</code> <b>100%</b>\n"
        )

    tier_list_lines = []
    for t in RANKS:
        is_cur = (not rank_info["is_custom"]) and (t["level"] == rank_info["level"])
        mark = " 👉 " if is_cur else " • "
        b_tag = "<b>" if is_cur else ""
        b_close = "</b>" if is_cur else ""
        th_str = f"{t['threshold']:,} ⭐️" if t['threshold'] > 0 else "0 ⭐️"
        cur_label = " (Ваш ранг)" if is_cur else ""
        tier_list_lines.append(f"{mark}{t['icon']} {b_tag}{t['name']}{b_close}: от <code>{th_str}</code>{cur_label}")

    tiers_block = "\n".join(tier_list_lines)

    return (
        f"🏆 <b>Система рангов СБП</b>\n\n"
        f"Ваш текущий ранг: <b>{title}</b>\n"
        f"Общий оборот: <b>{t_stars:,} ⭐️</b>\n\n"
        f"{prog_block}\n"
        f"────────────────────────\n"
        f"<b>Ранги и пороги оборота:</b>\n"
        f"{tiers_block}\n\n"
        f"💡 <i>Оборот растёт при любых переводах по СБП, пополнениях и создании чеков!</i>"
    )
