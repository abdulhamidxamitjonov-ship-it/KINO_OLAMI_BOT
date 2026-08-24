# 🎬 Kino Bot — Render + GitHub orqali BEPUL deploy qilish qo'llanmasi

Bu qo'llanma kod yozishni bilmasangiz ham, qadamma-qadam bajarishingiz uchun tayyorlangan.

---

## 1-QADAM: GitHub'ga kodni yuklash

1. https://github.com saytida akkaunt oching (agar yo'q bo'lsa).
2. Yangi repository yarating: **New repository** tugmasini bosing.
   - Nomi: `kino-bot` (yoki xohlagan nom)
   - **Private** qilib qo'ying (tavsiya etiladi)
   - "Create repository" bosing.
3. Repository ochilgach, **"uploading an existing file"** havolasini bosing.
4. Ushbu papkadagi **barcha fayllarni** (main.py, config.py, database.py va h.k. hammasini, `handlers` papkasi bilan birga) shu yerga tortib tashlang (drag & drop).
5. Pastda **"Commit changes"** tugmasini bosing.

> ⚠️ `.env` fayl yoki tokenni GitHub'ga hech qachon yuklamang — token Render'ning Environment bo'limida saqlanadi (xavfsizlik uchun).

---

## 2-QADAM: Telegram botini yaratish (agar hali yaratmagan bo'lsangiz)

1. Telegram'da **@BotFather** ga yozing.
2. `/newbot` yuboring, bot nomini va username'ini kiriting.
3. BotFather sizga **BOT_TOKEN** beradi (masalan: `123456:ABC-DEF...`) — buni saqlab qo'ying.

---

## 3-QADAM: Botni kerakli kanal/guruhlarga admin qilib qo'shish

Bot quyidagilarda **albatta ADMIN** bo'lishi kerak (aks holda a'zolikni tekshira olmaydi):
- Kinolar yuklanadigan yopiq kanal
- Har bir majburiy obuna kanal/guruh/zayavka guruh

---

## 4-QADAM: Kino kanalining ID sini topish

Sizning yopiq kanalingiz: `https://t.me/+82OCPwYmJjE3ZGI6`

1. Botni shu kanalga **admin** qilib qo'shing.
2. Kanaldagi istalgan xabarni botga **forward** qiling (shaxsiy chatda).
3. O'sha forward qilingan xabarga **reply** qilib, `/get_id` deb yozing.
4. Bot sizga kanalning raqamli ID sini beradi (masalan: `-1001234567890`) — buni saqlab qo'ying, keyingi qadamda kerak bo'ladi.

---

## 5-QADAM: Render'da bot yaratish

1. https://render.com saytiga kiring, GitHub akkauntingiz bilan ro'yxatdan o'ting.
2. **New +** → **Web Service** ni tanlang.
3. GitHub repositoryingizni (`kino-bot`) tanlang va **Connect** bosing.
4. Quyidagilarni to'ldiring:
   - **Name**: `kino-bot` (xohlagan nom)
   - **Region**: eng yaqinini tanlang
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: **Free** ni tanlang

5. Pastroqda **"Environment Variables"** bo'limini toping va quyidagilarni qo'shing:

| Key | Value |
|---|---|
| `BOT_TOKEN` | BotFather'dan olgan tokeningiz |
| `ADMIN_ID` | `7883084346` |
| `MOVIE_CHANNEL_ID` | 4-qadamda topgan raqamli ID (masalan `-1001234567890`) |

6. **"Create Web Service"** tugmasini bosing.

Render avtomatik ravishda kodni yuklab, botni ishga tushiradi. Bir necha daqiqadan so'ng loglarda:
```
Bot polling rejimida ishga tushdi 🚀
```
degan yozuvni ko'rsangiz — bot ishga tushgan!

---

## 6-QADAM: Bot doim uyg'oq turishi uchun (MUHIM!)

Render'ning bepul tarifida, agar botga 15 daqiqa hech kim murojaat qilmasa, u **"uxlab qoladi"** va keyingi xabarga sekin javob beradi. Buni oldini olish uchun:

1. https://uptimerobot.com saytida bepul akkaunt oching.
2. **"Add New Monitor"** bosing.
3. Monitor turi: **HTTP(s)**
4. URL: Render bergan sizning bot manzilingiz (masalan `https://kino-bot.onrender.com`)
5. Tekshirish oralig'i (Interval): **5 daqiqa**
6. Saqlang.

Endi UptimeRobot har 5 daqiqada botingizga "salom" berib turadi va u doim ishlab turadi. ✅

---

## 7-QADAM: Majburiy obunalarni sozlash

Botga (shaxsiy chatda, admin sifatida) quyidagi buyruqlarni yuboring:

```
/add_channel https://t.me/mychannel
/add_group https://t.me/mygroup
/add_zayafka https://t.me/+xxxxxxxx <chat_id>
```

> Yopiq (`+` bilan boshlanuvchi) kanal/guruh uchun avval botni admin qiling, `/get_id` orqali ID toping, keyin buyruqqa oxiriga qo'shib yuboring.

Vaqt bilan qo'shish:
```
/add_channel https://t.me/mychannel 23.08 21:00
```
— bu kanal 23-avgust soat 21:00 da avtomatik o'chiriladi.

O'chirish:
```
/delete_channel https://t.me/mychannel
/delete_group https://t.me/mygroup
/delete_zayafka https://t.me/+xxxxxxxx
/delete_all
```

Ro'yxatlarni ko'rish:
```
/list      — barcha majburiy obunalar
/users     — barcha bot foydalanuvchilari
```

Kinoni premium qilish:
```
/premium KOD123
```

---

## 8-QADAM: Kino yuklash

Yopiq kanalga video yuboring, **caption (izoh)ning birinchi so'zi kino kodi bo'lsin**:

```
KOD123
Bu yerga istalgan tavsif yozishingiz mumkin
```

Bot avtomatik shu videoni `KOD123` kodi bilan saqlaydi. Mijoz botga `KOD123` deb yozsa — bot shu videoni yuboradi.

---

## Yangilanish kiritish (kodni o'zgartirish kerak bo'lsa)

GitHub'da faylni tahrirlab, "Commit changes" bossangiz, Render **avtomatik** qayta deploy qiladi — hech narsa qilish shart emas.

---

## ⚠️ Eslatma

- SQLite baza fayli (`bot.db`) Render bepul tarifida **doimiy disk emas** — agar siz kodni qayta deploy qilsangiz (GitHub'da o'zgartirish kiritsangiz), baza tozalanishi mumkin (foydalanuvchilar, premium, kinolar ro'yxati). Agar bu muammo bo'lib qolsa, aytib qo'ying — bepul tashqi baza (Neon.tech Postgres)ga o'tkazib beraman, bu holatda ma'lumotlar hech qachon o'chmaydi.
- Bot tokenini hech kimga bermang va GitHub'ga hech qachon to'g'ridan-to'g'ri yozmang.
