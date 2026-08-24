import re
from datetime import datetime
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

import database as db


async def check_membership(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Foydalanuvchi kanal/guruh/zayavka guruhga a'zoligini tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest:
        return False
    except Exception:
        return False


async def get_not_subscribed(bot: Bot, user_id: int):
    """Foydalanuvchi hali a'zo bo'lmagan majburiy obunalar ro'yxatini qaytaradi."""
    subs = await db.get_all_force_subs()
    not_subbed = []
    for s in subs:
        ok = await check_membership(bot, s["chat_id"], user_id)
        if not ok:
            not_subbed.append(s)
    return not_subbed


DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})")


def parse_optional_datetime(text: str):
    """'23.08 21:00' formatidagi sanani topadi va shu yilga nisbatan datetime qaytaradi.
    Topilmasa None qaytaradi."""
    m = DATE_RE.search(text)
    if not m:
        return None
    day, month, hour, minute = map(int, m.groups())
    year = datetime.utcnow().year
    try:
        dt = datetime(year, month, day, hour, minute)
    except ValueError:
        return None
    return dt


def extract_link(text: str) -> str:
    """Buyruq matnidan havolani ajratib oladi (sanani olib tashlab)."""
    text = DATE_RE.sub("", text).strip()
    parts = text.split()
    return parts[-1] if parts else ""


async def resolve_chat_from_link(bot: Bot, link: str):
    """Havoladan chat_id va title ni oladi. Bot o'sha kanal/guruhda admin bo'lishi shart."""
    username = link
    if "t.me/" in link:
        username = link.split("t.me/")[-1]
        username = username.split("?")[0]
    if not username.startswith("@") and not username.startswith("+"):
        username = "@" + username
    if username.startswith("+"):
        # bu shaxsiy invite link (join request kerak bo'lishi mumkin) — chat_id ni to'g'ridan oling bo'lmaydi
        return None, None
    try:
        chat = await bot.get_chat(username)
        return chat.id, chat.title
    except Exception:
        return None, None
