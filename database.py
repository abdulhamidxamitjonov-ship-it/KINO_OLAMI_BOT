import aiosqlite
from datetime import datetime, timedelta
from config import DB_PATH

# ---------- Vaqt yordamchilari ----------

def now_str() -> str:
    return datetime.utcnow().isoformat()

def to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TEXT,
            is_premium INTEGER DEFAULT 0,
            premium_until TEXT,
            premium_type TEXT,
            referred_by INTEGER,
            ref_count INTEGER DEFAULT 0,
            ref_stage INTEGER DEFAULT 0
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT,
            is_premium INTEGER DEFAULT 0,
            added_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS force_subs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            chat_id INTEGER,
            link TEXT,
            title TEXT,
            added_at TEXT,
            expire_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_key TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            screenshot_id TEXT,
            requested_at TEXT,
            decided_at TEXT
        )""")
        await db.commit()


# ---------- USERS ----------

async def add_user(user_id: int, username: str, full_name: str, referred_by: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row:
            return False  # allaqachon bor
        await db.execute(
            "INSERT INTO users (user_id, username, full_name, joined_at, referred_by) VALUES (?,?,?,?,?)",
            (user_id, username, full_name, now_str(), referred_by)
        )
        await db.commit()
        return True  # yangi user


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users")
        return await cur.fetchall()


async def is_user_premium(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user["premium_until"]:
        return False
    return to_dt(user["premium_until"]) > datetime.utcnow()


async def set_premium(user_id: int, plan_key: str, days: int):
    user = await get_user(user_id)
    base = datetime.utcnow()
    if user and user["premium_until"] and to_dt(user["premium_until"]) > base:
        # spetsifikatsiyaga ko'ra ustiga uzaytirilmaydi, shunchaki yangidan belgilanadi
        pass
    until = base + timedelta(days=days)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_premium=1, premium_until=?, premium_type=? WHERE user_id=?",
            (until.isoformat(), plan_key, user_id)
        )
        await db.commit()
    return until


async def clear_premium(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_premium=0, premium_until=NULL, premium_type=NULL WHERE user_id=?",
            (user_id,)
        )
        await db.commit()


async def get_expired_premium_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM users WHERE is_premium=1 AND premium_until IS NOT NULL"
        )
        rows = await cur.fetchall()
        return [r for r in rows if to_dt(r["premium_until"]) <= datetime.utcnow()]


async def increment_referral(referrer_id: int):
    """Referalni +1 qiladi va agar bosqich to'lgan bo'lsa mukofotga tayyor ekanini qaytaradi."""
    user = await get_user(referrer_id)
    if not user:
        return None
    new_count = user["ref_count"] + 1
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET ref_count=? WHERE user_id=?", (new_count, referrer_id))
        await db.commit()
    return new_count


async def reset_referral_progress(user_id: int, new_stage: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET ref_count=0, ref_stage=? WHERE user_id=?",
            (new_stage, user_id)
        )
        await db.commit()


# ---------- MOVIES ----------

async def add_movie(code: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO movies (code, file_id, is_premium, added_at) "
            "VALUES (?, ?, COALESCE((SELECT is_premium FROM movies WHERE code=?), 0), ?)",
            (code, file_id, code, now_str())
        )
        await db.commit()


async def get_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM movies WHERE code=?", (code,))
        return await cur.fetchone()


async def set_movie_premium(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT code FROM movies WHERE code=?", (code,))
        if not await cur.fetchone():
            return False
        await db.execute("UPDATE movies SET is_premium=1 WHERE code=?", (code,))
        await db.commit()
        return True


# ---------- FORCE SUBS ----------

async def add_force_sub(type_: str, chat_id: int, link: str, title: str, expire_at: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO force_subs (type, chat_id, link, title, added_at, expire_at) VALUES (?,?,?,?,?,?)",
            (type_, chat_id, link, title, now_str(), expire_at)
        )
        await db.commit()


async def get_all_force_subs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM force_subs")
        return await cur.fetchall()


async def delete_force_sub_by_link(link: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM force_subs WHERE link=?", (link,))
        row = await cur.fetchone()
        if not row:
            return False
        await db.execute("DELETE FROM force_subs WHERE link=?", (link,))
        await db.commit()
        return True


async def delete_force_sub_by_id(id_: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM force_subs WHERE id=?", (id_,))
        await db.commit()


async def delete_all_force_subs():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM force_subs")
        await db.commit()


async def get_expired_force_subs():
    subs = await get_all_force_subs()
    return [s for s in subs if s["expire_at"] and to_dt(s["expire_at"]) <= datetime.utcnow()]


# ---------- PAYMENTS ----------

async def create_payment(user_id: int, plan_key: str, amount: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO payments (user_id, plan_key, amount, requested_at) VALUES (?,?,?,?)",
            (user_id, plan_key, amount, now_str())
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_payment(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM payments WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        return await cur.fetchone()


async def get_payment(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE id=?", (payment_id,))
        return await cur.fetchone()


async def set_payment_screenshot(payment_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE payments SET screenshot_id=? WHERE id=?", (file_id, payment_id))
        await db.commit()


async def update_payment_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE payments SET status=?, decided_at=? WHERE id=?",
            (status, now_str(), payment_id)
        )
        await db.commit()


async def get_expired_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE status='pending'")
        rows = await cur.fetchall()
        result = []
        for r in rows:
            if to_dt(r["requested_at"]) + timedelta(seconds=300) <= datetime.utcnow():
                result.append(r)
        return result
