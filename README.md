# 🤖 Referal Bot — O'rnatish va Ishga Tushirish

## 📋 Talablar
- Python 3.10 yoki undan yuqori
- pip

---

## ⚙️ O'rnatish

### 1. Papkani oching
```bash
cd referral_bot
```

### 2. Kerakli kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

### 3. Botni ishga tushiring
```bash
python bot.py
```

---

## 🚀 Botni sozlash (Admin Panel)

Bot ishga tushgach, Telegram da botga `/start` yozing.

### Kanal qo'shish:
1. ⚙️ Admin Panel → ➕ Kanal qo'shish
2. Kanal username ini yuboring: `@kanalUsername`

> ⚠️ **Muhim:** Botni kanalga **Admin** qiling!
> Kanal → Boshqaruvchilar → Bot qo'shing

---

## 📊 Bot imkoniyatlari

| Xususiyat | Tavsif |
|---|---|
| 🔗 Referal tizim | Har bir foydalanuvchiga shaxsiy referal link |
| 📊 Top 20 | Nik, username, PUBG ID, taklif soni |
| 🎮 PUBG ID | Start bosganida so'raladi |
| 📢 Majburiy obuna | Cheksiz miqdorda kanal qo'shiladi |
| ⚠️ Referal ayirish | Odam kanaldan chiqsa referali ayiriladi + xabar ketadi |
| ⚙️ Admin Panel | Kanallarni boshqarish, statistika |

---

## 📁 Fayl tuzilmasi

```
referral_bot/
├── bot.py          # Asosiy bot fayli
├── database.py     # Ma'lumotlar bazasi
├── requirements.txt
└── data/
    └── bot.db      # SQLite bazasi (avtomatik yaratiladi)
```
