from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import PREMIUM_PLANS


def force_sub_keyboard(subs, bot_username: str):
    """subs: force_subs jadvalidagi qatorlar ro'yxati"""
    rows = []
    for i, s in enumerate(subs, start=1):
        prefix = {"channel": "📢", "group": "👥", "zayavka": "📝"}.get(s["type"], "🔗")
        rows.append([InlineKeyboardButton(text=f"{prefix} {i} - {s['title'] or 'kanal'}", url=s["link"])])
    rows.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs")])
    rows.append([InlineKeyboardButton(text="💎 Premium panel", callback_data="show_premium_from_gate")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard():
    kb = [
        [KeyboardButton(text="💎 Premium"), KeyboardButton(text="🎁 Referal")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def premium_plans_keyboard():
    rows = []
    for key, (name, days, price) in PREMIUM_PLANS.items():
        rows.append([InlineKeyboardButton(
            text=f"💎 {name} — {price:,} so'm".replace(",", " "),
            callback_data=f"buy_{key}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_wait_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")]
    ])


def admin_check_keyboard(payment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"padm_ok_{payment_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"padm_no_{payment_id}"),
        ]
    ])


def admin_confirm_double_check(payment_id: int, action: str):
    """action: 'ok' yoki 'no' — ikkinchi tasdiqlash bosqichi"""
    yes_cb = f"padm2_{action}_{payment_id}"
    no_cb = f"padm2_back_{payment_id}"
    text_yes = "✅ Ha, tasdiqlayman" if action == "ok" else "✅ Ha, bekor qilaman"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=text_yes, callback_data=yes_cb),
            InlineKeyboardButton(text="◀️ Yo'q, ortga", callback_data=no_cb),
        ]
    ])


def premium_buy_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Premium sotib olish", callback_data="show_premium")]
    ])
