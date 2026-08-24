import os

# Render "Environment" bo'limida shu nomlar bilan o'zgaruvchi qo'shasiz
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7883084346"))

# Kinolar yuklanadigan yopiq kanalning raqamli ID si (masalan: -1001234567890)
# Buni qanday topish README.md da yozilgan
MOVIE_CHANNEL_ID = int(os.getenv("MOVIE_CHANNEL_ID", "0"))

DB_PATH = os.getenv("DB_PATH", "bot.db")

CARD_NUMBER = "9860096601308230"
CARD_OWNER = "Xamitjonov Abdulxamid"

# To'lov uchun kutish vaqti (soniyalarda)
PAYMENT_TIMEOUT = 5 * 60

# Premium tariflar: kalit -> (nomi, kunlar, narxi so'mda)
PREMIUM_PLANS = {
    "7d":  ("7 kunlik",  7,   12000),
    "1m":  ("1 oylik",   30,  25000),
    "3m":  ("3 oylik",   90,  55000),
    "6m":  ("6 oylik",   180, 105000),
    "12m": ("12 oylik",  365, 195000),
}

# Referal bosqichlari: (kerakli do'stlar soni, mukofot kun)
REFERRAL_STAGES = [25, 50, 80]
REFERRAL_REWARD_DAYS = 7
REFERRAL_MAX_STAGES = 3
