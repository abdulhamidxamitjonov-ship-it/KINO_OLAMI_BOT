import logging
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command

import database as db
from config import ADMIN_ID, MOVIE_CHANNEL_ID
from utils import parse_optional_datetime, extract_link, resolve_chat_from_link

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user and message.from_user.id == ADMIN_ID


# ---------- Kino yuklash: yopiq kanaldagi postlarni tinglash ----------

@router.channel_post(F.chat.id == MOVIE_CHANNEL_ID)
async def handle_movie_channel_post(message: Message):
    """Admin yopiq kanalga kino (video/hujjat) yuborganda, caption dagi kodni film kodi sifatida saqlaydi."""
    code = (message.caption or "").strip().split()[0] if message.caption else None
    if not code:
        return  # kod yozilmagan post e'tiborsiz qoldiriladi

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id

    if not file_id:
        return

    await db.add_movie(code, file_id)
    logging.info(f"Yangi kino saqlandi: kod={code}")


# ---------- /get_id — istalgan kanal/guruhning raqamli ID sini topish ----------

@router.message(Command("get_id"))
async def cmd_get_id(message: Message):
    if not is_admin(message):
        return
    if message.reply_to_message and message.reply_to_message.forward_from_chat:
        chat = message.reply_to_message.forward_from_chat
        await message.answer(f"🆔 Chat ID: <code>{chat.id}</code>\n📌 Nomi: {chat.title}")
        return
    await message.answer(
        "ℹ️ Foydalanish: kerakli kanal/guruhdan istalgan xabarni shu botga forward qiling, "
        "so'ng o'sha forward qilingan xabarga <b>reply</b> qilib /get_id yozing."
    )


# ---------- Majburiy obuna qo'shish ----------

async def _add_force_sub(message: Message, type_: str, cmd_name: str):
    if not is_admin(message):
        return
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer(f"ℹ️ Foydalanish: /{cmd_name} <havola> [chat_id agar yopiq bo'lsa] [23.08 21:00]")
        return

    expire_dt = parse_optional_datetime(text)
    link = extract_link(text)

    # agar oxirgi so'z raqam bo'lsa - bu qo'lda kiritilgan chat_id (yopiq kanal/guruh uchun)
    manual_chat_id = None
    tokens = link.split()
    if len(tokens) >= 2 and tokens[-1].lstrip("-").isdigit():
        manual_chat_id = int(tokens[-1])
        link = tokens[0]

    if manual_chat_id:
        chat_id, title = manual_chat_id, link
    else:
        chat_id, title = await resolve_chat_from_link(message.bot, link)

    if not chat_id:
        await message.answer(
            "❌ Havoladan chat aniqlanmadi. Agar bu yopiq (+ bilan boshlanuvchi) havola bo'lsa, "
            "avval botni o'sha kanal/guruhga admin qilib qo'shing, keyin /get_id orqali ID sini toping va:\n"
            f"/{cmd_name} {link} <ID> shaklida yuboring."
        )
        return

    await db.add_force_sub(type_, chat_id, link, title, expire_dt.isoformat() if expire_dt else None)

    emoji = {"channel": "📢", "group": "👥", "zayavka": "📝"}[type_]
    extra = f"\n⏰ Avtomatik o'chirish vaqti: {expire_dt.strftime('%d.%m.%Y %H:%M')}" if expire_dt else ""
    await message.answer(f"{emoji} <b>{title}</b> majburiy obunaga qo'shildi ✅{extra}")


@router.message(Command("add_channel"))
async def cmd_add_channel(message: Message):
    await _add_force_sub(message, "channel", "add_channel")


@router.message(Command("add_group"))
async def cmd_add_group(message: Message):
    await _add_force_sub(message, "group", "add_group")


@router.message(Command("add_zayafka"))
async def cmd_add_zayafka(message: Message):
    await _add_force_sub(message, "zayavka", "add_zayafka")


# ---------- Majburiy obuna o'chirish ----------

async def _delete_force_sub(message: Message, cmd_name: str):
    if not is_admin(message):
        return
    link = message.text.partition(" ")[2].strip()
    if not link:
        await message.answer(f"ℹ️ Foydalanish: /{cmd_name} <havola>")
        return
    ok = await db.delete_force_sub_by_link(link)
    if ok:
        await message.answer("🗑 Majburiy obuna o'chirildi ✅")
    else:
        await message.answer("❌ Bunday havola topilmadi.")


@router.message(Command("delete_channel"))
async def cmd_delete_channel(message: Message):
    await _delete_force_sub(message, "delete_channel")


@router.message(Command("delete_group"))
async def cmd_delete_group(message: Message):
    await _delete_force_sub(message, "delete_group")


@router.message(Command("delete_zayafka"))
async def cmd_delete_zayafka(message: Message):
    await _delete_force_sub(message, "delete_zayafka")


@router.message(Command("delete_all"))
async def cmd_delete_all(message: Message):
    if not is_admin(message):
        return
    await db.delete_all_force_subs()
    await message.answer("🗑 Barcha majburiy obunalar o'chirildi ✅")


# ---------- Ro'yxatlar ----------

@router.message(Command("list"))
async def cmd_list(message: Message):
    if not is_admin(message):
        return
    subs = await db.get_all_force_subs()
    if not subs:
        await message.answer("📭 Hozircha majburiy obunalar yo'q.")
        return
    emoji = {"channel": "📢", "group": "👥", "zayavka": "📝"}
    lines = ["📋 <b>Majburiy obunalar ro'yxati:</b>\n"]
    for s in subs:
        exp = f" (o'chadi: {s['expire_at'][:16].replace('T', ' ')})" if s["expire_at"] else ""
        lines.append(f"{emoji.get(s['type'], '🔗')} {s['title']} — {s['link']}{exp}")
    await message.answer("\n".join(lines))


@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message):
        return
    users = await db.get_all_users()
    if not users:
        await message.answer("📭 Hozircha foydalanuvchilar yo'q.")
        return
    lines = [f"👥 <b>Jami foydalanuvchilar: {len(users)}</b>\n"]
    for u in users[:200]:  # xabar limitidan chiqib ketmaslik uchun
        uname = f"@{u['username']}" if u["username"] else "—"
        prem = "💎" if u["is_premium"] else ""
        lines.append(f"• {u['user_id']} {uname} {prem}")
    text = "\n".join(lines)
    if len(users) > 200:
        text += f"\n\n... va yana {len(users) - 200} ta foydalanuvchi"
    await message.answer(text)


# ---------- Kinoni premium qilish ----------

@router.message(Command("premium"))
async def cmd_premium_movie(message: Message):
    if not is_admin(message):
        return
    code = message.text.partition(" ")[2].strip()
    if not code:
        await message.answer("ℹ️ Foydalanish: /premium <kino kodi>")
        return
    ok = await db.set_movie_premium(code)
    if ok:
        await message.answer(f"💎 <code>{code}</code> kodli kino endi faqat Premium a'zolar uchun ✅")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")
