import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import user, admin, payment
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def handle_ping(request):
    return web.Response(text="Kino bot ishlayapti ✅")


async def start_web_server():
    """Render bepul tarifida 'Web Service' portni tinglashini talab qiladi,
    aks holda deploy muvaffaqiyatsiz tugaydi. Shu mini-server shu muammoni oldini oladi."""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment o'zgaruvchisi topilmadi! Render Environment bo'limiga qo'shing.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(user.router)

    await init_db()
    start_scheduler(bot)
    await start_web_server()

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot polling rejimida ishga tushdi 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
