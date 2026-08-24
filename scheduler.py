import asyncio
import logging
from aiogram import Bot

import database as db

CHECK_INTERVAL = 30  # soniya


async def _scheduler_loop(bot: Bot):
    while True:
        try:
            await _check_expired_force_subs(bot)
            await _check_expired_premium(bot)
            await _check_expired_payments(bot)
        except Exception as e:
            logging.exception(f"Scheduler xatosi: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


async def _check_expired_force_subs(bot: Bot):
    expired = await db.get_expired_force_subs()
    for s in expired:
        await db.delete_force_sub_by_id(s["id"])
        logging.info(f"Muddati tugagan majburiy obuna o'chirildi: {s['title']}")


async def _check_expired_premium(bot: Bot):
    expired_users = await db.get_expired_premium_users()
    for u in expired_users:
        await db.clear_premium(u["user_id"])
        try:
            await bot.send_message(
                u["user_id"],
                "⏳ Sizning Premium obunangiz muddati tugadi.\n"
                "Yana premium imkoniyatlaridan foydalanish uchun qaytadan sotib olishingiz mumkin 💎"
            )
        except Exception:
            pass


async def _check_expired_payments(bot: Bot):
    expired = await db.get_expired_pending_payments()
    for p in expired:
        await db.update_payment_status(p["id"], "expired")
        try:
            await bot.send_message(
                p["user_id"],
                "⏰ To'lov uchun berilgan 5 daqiqalik vaqt tugadi.\n"
                "To'lov avtomatik bekor qilindi. Qaytadan urinib ko'rishingiz mumkin 🔄"
            )
        except Exception:
            pass


def start_scheduler(bot: Bot):
    asyncio.create_task(_scheduler_loop(bot))
