from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandObject

import database as db
from config import PREMIUM_PLANS, REFERRAL_STAGES, REFERRAL_REWARD_DAYS, REFERRAL_MAX_STAGES, ADMIN_ID
from utils import get_not_subscribed
from keyboards import force_sub_keyboard, main_menu_keyboard, premium_plans_keyboard

router = Router()


WELCOME_TEXT = (
    "🎬 <b>Xush kelibsiz!</b>\n\n"
    "🔎 Kino tomosha qilish uchun menga kerakli <b>kino kodini</b> yuboring.\n"
    "💎 Premium va 🎁 Referal imkoniyatlari pastdagi menyuda mavjud."
)


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    user = message.from_user
    referred_by = None
    if command.args and command.args.startswith("ref_"):
        try:
            ref_id = int(command.args.replace("ref_", ""))
            if ref_id != user.id:
                referred_by = ref_id
        except ValueError:
            pass

    is_new = await db.add_user(user.id, user.username, user.full_name, referred_by)

    not_subbed = await get_not_subscribed(message.bot, user.id)
    if not_subbed:
        await message.answer(
            "❌ <b>Kechirasiz, botimizdan foydalanishdan oldin ushbu kanallarga a'zo bo'lishingiz kerak.</b>",
            reply_markup=force_sub_keyboard(not_subbed, "")
        )
        return

    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())

    # yangi user va referal bo'lsa - hozircha kutib turadi, chunki obuna hali tasdiqlanmagan bo'lishi mumkin edi
    # (bu yerga yetib kelgan bo'lsa obuna allaqachon bor demak, referalni shu yerda hisoblaymiz)
    if is_new and referred_by:
        await _process_referral_reward(message, referred_by)


async def _process_referral_reward(message: Message, referrer_id: int):
    referrer = await db.get_user(referrer_id)
    if not referrer:
        return
    new_count = await db.increment_referral(referrer_id)
    stage = referrer["ref_stage"]
    if stage >= REFERRAL_MAX_STAGES:
        return
    needed = REFERRAL_STAGES[stage]
    if new_count >= needed:
        until = await db.set_premium(referrer_id, "referral", REFERRAL_REWARD_DAYS)
        await db.reset_referral_progress(referrer_id, stage + 1)
        try:
            await message.bot.send_message(
                referrer_id,
                f"🎉 Tabriklaymiz! Siz {needed} ta do'stingizni taklif qildingiz va "
                f"<b>{REFERRAL_REWARD_DAYS} kunlik Premium</b> obunaga ega bo'ldingiz 💎\n"
                f"⏳ Amal qilish muddati: {until.strftime('%d.%m.%Y %H:%M')} gacha"
            )
        except Exception:
            pass


@router.callback_query(F.data == "check_subs")
async def cb_check_subs(callback: CallbackQuery):
    not_subbed = await get_not_subscribed(callback.bot, callback.from_user.id)
    if not_subbed:
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmagansiz!", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(
        "✅ <b>Tabriklaymiz!</b> Endi botdan to'liq foydalanishingiz mumkin.\n\n"
        "🎬 Kino Kodini yuboring 👇",
        reply_markup=main_menu_keyboard()
    )
    user = callback.from_user
    u = await db.get_user(user.id)
    if u and u["referred_by"]:
        await _process_referral_reward(callback.message, u["referred_by"])
    await callback.answer()


@router.callback_query(F.data.in_(["show_premium_from_gate", "show_premium"]))
async def cb_show_premium(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if user and await db.is_user_premium(callback.from_user.id):
        until = datetime.fromisoformat(user["premium_until"])
        plan_name = PREMIUM_PLANS.get(user["premium_type"], (user["premium_type"],))[0]
        await callback.message.answer(
            f"💎 <b>Sizda faol Premium obuna bor!</b>\n\n"
            f"📦 Tarif: {plan_name}\n"
            f"⏳ Tugash sanasi: {until.strftime('%d.%m.%Y %H:%M')}"
        )
    else:
        await callback.message.answer(
            "💎 <b>Premium tariflardan birini tanlang:</b>",
            reply_markup=premium_plans_keyboard()
        )
    await callback.answer()


@router.message(F.text == "💎 Premium")
async def btn_premium(message: Message):
    user = await db.get_user(message.from_user.id)
    if user and await db.is_user_premium(message.from_user.id):
        until = datetime.fromisoformat(user["premium_until"])
        plan_name = PREMIUM_PLANS.get(user["premium_type"], (user["premium_type"],))[0]
        await message.answer(
            f"💎 <b>Sizda faol Premium obuna bor!</b>\n\n"
            f"📦 Tarif: {plan_name}\n"
            f"⏳ Tugash sanasi: {until.strftime('%d.%m.%Y %H:%M')}"
        )
    else:
        await message.answer("💎 <b>Premium tariflardan birini tanlang:</b>", reply_markup=premium_plans_keyboard())


@router.message(F.text == "🎁 Referal")
async def btn_referral(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    me = await message.bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    stage = user["ref_stage"]
    if stage >= REFERRAL_MAX_STAGES:
        await message.answer(
            "🎁 <b>Referal dasturi</b>\n\n"
            "Siz mukofot olish uchun maksimal (3 marta) chegaraga yetdingiz 🏆\n"
            f"🔗 Sizning havolangiz: {link}"
        )
        return
    needed = REFERRAL_STAGES[stage]
    left = max(needed - user["ref_count"], 0)
    await message.answer(
        "🎁 <b>Do'stlaringizni taklif qiling va bepul Premium yutib oling!</b>\n\n"
        f"👥 Hozirgi taklif qilganlar: {user['ref_count']}/{needed}\n"
        f"⏳ Yana {left} ta do'stingiz qo'shilsa — {REFERRAL_REWARD_DAYS} kunlik Premium sizniki 💎\n\n"
        f"🔗 Sizning shaxsiy havolangiz:\n{link}"
    )


# ---------- Kino kodi ----------

@router.message(F.text & ~F.text.startswith("/"))
async def handle_movie_code(message: Message):
    if message.text in ("💎 Premium", "🎁 Referal"):
        return  # bu tugmalar yuqorida ishlanadi

    code = message.text.strip()

    not_premium_user = not await db.is_user_premium(message.from_user.id)
    if not_premium_user:
        not_subbed = await get_not_subscribed(message.bot, message.from_user.id)
        if not_subbed:
            await message.answer(
                "❌ <b>Kechirasiz, botimizdan foydalanishdan oldin ushbu kanallarga a'zo bo'lishingiz kerak.</b>",
                reply_markup=force_sub_keyboard(not_subbed, "")
            )
            return

    movie = await db.get_movie(code)
    if not movie:
        await message.answer("😔 Bunday kodli kino topilmadi. Kodni tekshirib qaytadan yuboring.")
        return

    if movie["is_premium"] and not_premium_user:
        await message.answer(
            "🔒 <b>Kechirasiz, bu kino faqat Premium obunachilar uchun.</b>\n"
            "Kinoni ko'rish uchun Premium sotib oling 💎",
            reply_markup=premium_plans_keyboard()
        )
        return

    await message.answer_video(movie["file_id"], caption=f"🎬 Kino kodi: <code>{code}</code>\nXush ko'rishlar! 🍿")
