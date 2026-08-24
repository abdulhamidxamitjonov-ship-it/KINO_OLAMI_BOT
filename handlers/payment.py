from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

import database as db
from config import PREMIUM_PLANS, CARD_NUMBER, CARD_OWNER, ADMIN_ID
from keyboards import payment_wait_keyboard, admin_check_keyboard, admin_confirm_double_check, main_menu_keyboard

router = Router()


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy_plan(callback: CallbackQuery):
    plan_key = callback.data.replace("buy_", "")
    if plan_key not in PREMIUM_PLANS:
        await callback.answer("❌ Noto'g'ri tarif", show_alert=True)
        return

    existing = await db.get_pending_payment(callback.from_user.id)
    if existing:
        await callback.answer("⏳ Sizda tasdiqlanishi kutilayotgan to'lov allaqachon mavjud.", show_alert=True)
        return

    name, days, price = PREMIUM_PLANS[plan_key]
    payment_id = await db.create_payment(callback.from_user.id, plan_key, price)

    price_fmt = f"{price:,}".replace(",", " ")
    text = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Tarif: <b>{name}</b>\n"
        f"💰 To'lov summasi: <b>{price_fmt} so'm</b>\n\n"
        f"💳 Karta raqami:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_OWNER}</b>\n\n"
        f"⚠️ <b>Diqqat:</b> ko'rsatilgan summadan bir tiyin ham kam yoki ko'p tashlamang, "
        f"aks holda to'lov qabul qilinmaydi.\n"
        f"⏱ To'lov uchun vaqtingiz: <b>5 daqiqa</b>.\n\n"
        f"📸 To'lovni amalga oshirgach, chek (screenshot) rasmini shu yerga yuboring.\n"
        f"🚫 Soxta yoki boshqa chekni yubormang — bunday holda to'lov qabul qilinmaydi, chek admin tomonidan qo'lda tekshiriladi."
    )
    await callback.message.answer(text, reply_markup=payment_wait_keyboard())
    await callback.answer()


@router.callback_query(F.data == "cancel_payment")
async def cb_cancel_payment(callback: CallbackQuery):
    payment = await db.get_pending_payment(callback.from_user.id)
    if payment:
        await db.update_payment_status(payment["id"], "cancelled")
    await callback.message.edit_text("❌ To'lov bekor qilindi.")
    await callback.answer()


@router.message(F.photo)
async def handle_payment_screenshot(message: Message):
    payment = await db.get_pending_payment(message.from_user.id)
    if not payment:
        return  # kutilayotgan to'lov yo'q — e'tiborsiz qoldiriladi

    file_id = message.photo[-1].file_id
    await db.set_payment_screenshot(payment["id"], file_id)

    name, days, price = PREMIUM_PLANS[payment["plan_key"]]
    price_fmt = f"{price:,}".replace(",", " ")
    user = message.from_user
    uname = f"@{user.username}" if user.username else "—"

    caption = (
        f"🧾 <b>Yangi to'lov cheki</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name} ({uname})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📦 Tarif: {name}\n"
        f"💰 Summa: {price_fmt} so'm\n"
        f"🔢 To'lov ID: {payment['id']}"
    )
    await message.bot.send_photo(
        ADMIN_ID, file_id, caption=caption,
        reply_markup=admin_check_keyboard(payment["id"])
    )
    await message.answer("✅ Chekingiz qabul qilindi va admin tomonidan tekshirilmoqda. Iltimos, kuting ⏳")


@router.callback_query(F.data.startswith("padm_"))
async def cb_admin_first_check(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Bu tugma faqat admin uchun.", show_alert=True)
        return
    _, action, payment_id = callback.data.split("_")
    text = "✅ Siz to'lovni <b>tasdiqlamoqchisiz</b>." if action == "ok" else "❌ Siz to'lovni <b>bekor qilmoqchisiz</b>."
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n{text}\n❓ Ishonchingiz komilmi?",
        reply_markup=admin_confirm_double_check(int(payment_id), action)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("padm2_back_"))
async def cb_admin_back(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    payment_id = int(callback.data.replace("padm2_back_", ""))
    payment = await db.get_payment(payment_id)
    if not payment:
        await callback.message.edit_caption(caption="⚠️ To'lov topilmadi.")
        await callback.answer()
        return
    name, days, price = PREMIUM_PLANS[payment["plan_key"]]
    price_fmt = f"{price:,}".replace(",", " ")
    caption = (
        f"🧾 <b>Yangi to'lov cheki</b>\n\n"
        f"🆔 Foydalanuvchi ID: <code>{payment['user_id']}</code>\n"
        f"📦 Tarif: {name}\n"
        f"💰 Summa: {price_fmt} so'm\n"
        f"🔢 To'lov ID: {payment['id']}"
    )
    await callback.message.edit_caption(caption=caption, reply_markup=admin_check_keyboard(payment_id))
    await callback.answer("◀️ Ortga qaytdingiz")


@router.callback_query(F.data.startswith("padm2_ok_"))
async def cb_admin_confirm_ok(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    payment_id = int(callback.data.replace("padm2_ok_", ""))
    payment = await db.get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan yoki muddati o'tgan.", show_alert=True)
        return

    name, days, price = PREMIUM_PLANS[payment["plan_key"]]
    until = await db.set_premium(payment["user_id"], payment["plan_key"], days)
    await db.update_payment_status(payment_id, "confirmed")

    await callback.message.edit_caption(
        caption=callback.message.caption.split("\n\n❓")[0] + "\n\n✅ <b>TASDIQLANDI</b>"
    )
    await callback.answer("✅ Premium faollashtirildi")

    try:
        await callback.bot.send_message(
            payment["user_id"],
            f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"💎 Sizga <b>{name}</b> Premium obuna faollashtirildi.\n"
            f"⏳ Amal qilish muddati: {until.strftime('%d.%m.%Y %H:%M')} gacha\n\n"
            f"Xush ko'rishlar! 🍿",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("padm2_no_"))
async def cb_admin_confirm_no(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    payment_id = int(callback.data.replace("padm2_no_", ""))
    payment = await db.get_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await callback.answer("⚠️ Bu to'lov allaqachon ko'rib chiqilgan yoki muddati o'tgan.", show_alert=True)
        return

    await db.update_payment_status(payment_id, "rejected")
    await callback.message.edit_caption(
        caption=callback.message.caption.split("\n\n❓")[0] + "\n\n❌ <b>BEKOR QILINDI</b>"
    )
    await callback.answer("❌ To'lov bekor qilindi")

    try:
        await callback.bot.send_message(
            payment["user_id"],
            "❌ <b>Chekingiz admin tomonidan soxta deb topildi.</b>\n"
            "Iltimos, boshqa to'lov qilib, haqiqiy chek yuboring 🙏",
            reply_markup=main_menu_keyboard()
        )
    except Exception:
        pass
