import logging
import asyncio
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    BufferedInputFile, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openpyxl import Workbook
from database import Database

BOT_TOKEN = "8935442087:AAEkbThT6uMQQqW_LkiK6P0PV5q4QuxlV0o"
ADMIN_ID = 7808709581
WEBAPP_URL = "https://agrkonkurs-konkurs.up.railway.app"  # ⚠️ Bu yerga Web App joylashgan haqiqiy HTTPS manzilni yozing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()


# ===================== STATES =====================

class RegisterStates(StatesGroup):
    waiting_pubg_id = State()
    waiting_phone = State()

class AdminStates(StatesGroup):
    waiting_channel_username = State()
    waiting_channel_name = State()
    waiting_ban_username = State()
    waiting_unban_username = State()
    waiting_msg_user_id = State()
    waiting_msg_text = State()
    waiting_broadcast_text = State()
    waiting_gift_place = State()
    waiting_gift_name = State()
    waiting_gift_top_limit = State()
    waiting_stat_top_limit = State()
    waiting_end_date = State()
    waiting_search_user = State()


# ===================== KEYBOARDS =====================

def main_reply_keyboard(is_admin=False):
    buttons = [
        [KeyboardButton(text="🕹 Konkurs Markazi", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton(text="🔗 Mening Referal linkım"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👤 Mening profilım"), KeyboardButton(text="🎁 Sovgalar")],
        [KeyboardButton(text="📜 Referallarim tarixi")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_reply_keyboard():
    buttons = [
        [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="➖ Kanal o'chirish")],
        [KeyboardButton(text="📋 Kanallar ro'yxati"), KeyboardButton(text="📊 Bot statistikasi")],
        [KeyboardButton(text="👤 Foydalanuvchilar raqamlari"), KeyboardButton(text="📥 Excel yuklab olish")],
        [KeyboardButton(text="🚫 Ban / Unban"), KeyboardButton(text="🔍 Foydalanuvchi qidirish")],
        [KeyboardButton(text="📨 Foydalanuvchiga xabar"), KeyboardButton(text="📢 Hammaga xabar")],
        [KeyboardButton(text="🎁 Sovgalarni boshqarish"), KeyboardButton(text="📈 Statistika top sonini sozlash")],
        [KeyboardButton(text="🏆 G'oliblarni belgilash"), KeyboardButton(text="🏅 G'oliblar ro'yxati")],
        [KeyboardButton(text="🏁 Konkursni tugatish")],
        [KeyboardButton(text="🔙 Asosiy menyu")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )


def subscription_inline_keyboard(not_subscribed: list, check_callback: str = "check_sub"):
    buttons = []
    for username, name in not_subscribed:
        display = name if name else username
        buttons.append([InlineKeyboardButton(
            text=f"📢 {display}",
            url=f"https://t.me/{username.lstrip('@')}"
        )])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=check_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===================== HELPERS =====================

async def check_subscriptions(user_id: int) -> list:
    channels = db.get_channels_with_names()
    not_subscribed = []
    for username, name in channels:
        try:
            member = await bot.get_chat_member(username, user_id)
            if member.status in ["left", "kicked", "banned"]:
                not_subscribed.append((username, name))
        except Exception:
            not_subscribed.append((username, name))
    return not_subscribed


def is_valid_pubg_id(pubg_id: str) -> bool:
    """Kamida 7 xona, 5 yoki 6 bilan boshlanishi kerak"""
    return (
        pubg_id.isdigit()
        and len(pubg_id) >= 7
        and pubg_id[0] in ("5", "6")
    )


async def guard(message: types.Message) -> bool:
    """
    Har tugma bosilganda tekshiradi:
    1. Ban
    2. Ro'yxatdan o'tganmi (PUBG ID bor)
    3. Telefon raqam bor
    4. Kanallarga obuna
    False qaytsa — handler to'xtashi kerak.
    """
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return True

    if db.is_banned(user_id):
        await message.answer("🚫 Siz botdan bloklangansiz.")
        return False

    user = db.get_user(user_id)

    if not user:
        await message.answer(
            "⚠️ Avval ro'yxatdan o'ting!\n\n"
            "🎮 <b>PUBG ID</b> ingizni yuboring:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        return False

    # Telefon raqam yo'qmi?
    if not user[4]:
        not_subscribed = await check_subscriptions(user_id)
        if not_subscribed:
            await message.answer(
                "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling:",
                reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub_then_phone")
            )
        else:
            await message.answer(
                "⚠️ Ro'yxatdan o'tishni tugating!\n\n"
                "📱 Telefon raqamingizni yuboring:",
                reply_markup=phone_keyboard()
            )
        return False

    # Kanal obunasi
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed:
        await message.answer(
            "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling:",
            reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub")
        )
        return False

    return True


# ===================== START =====================

@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or "Nomsiz"
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            ref_id = int(args[1].replace("ref", ""))
            if ref_id != user_id:
                referrer_id = ref_id
        except Exception:
            pass

    if db.is_banned(user_id):
        await message.answer("🚫 Siz botdan bloklangansiz.")
        return

    user = db.get_user(user_id)

    # Yangi foydalanuvchi
    if not user:
        await state.update_data(referrer_id=referrer_id, full_name=full_name, username=username)
        await message.answer(
            f"👋 Salom, <b>{full_name}</b>!\n\n"
            "🎮 <b>PUBG ID</b> ingizni yuboring:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(RegisterStates.waiting_pubg_id)
        return

    # Telefon yo'q — davom ettirish
    if not user[4]:
        await state.update_data(referrer_id=referrer_id)
        not_subscribed = await check_subscriptions(user_id)
        if not_subscribed and user_id != ADMIN_ID:
            await message.answer(
                "⚠️ Endi quyidagi kanallarga obuna bo'ling:",
                reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub_then_phone")
            )
            return
        await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
        await state.set_state(RegisterStates.waiting_phone)
        return

    # Kanal obunasi
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub")
        )
        return

    await message.answer(
        f"👋 Xush kelibsiz, <b>{full_name}</b>!",
        reply_markup=main_reply_keyboard(user_id == ADMIN_ID),
        parse_mode="HTML"
    )


# ===================== REGISTER: PUBG ID =====================

@dp.message(RegisterStates.waiting_pubg_id)
async def pubg_id_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    pubg_id = message.text.strip()

    if not is_valid_pubg_id(pubg_id):
        await message.answer(
            "❌ Noto'g'ri PUBG ID! Qaytadan yuboring:"
        )
        return

    data = await state.get_data()
    referrer_id = data.get("referrer_id")
    full_name = data.get("full_name", message.from_user.full_name)
    username = data.get("username", message.from_user.username or "")

    db.add_user(user_id, full_name, username, pubg_id, referrer_id)
    await state.update_data(referrer_id=referrer_id, pubg_id=pubg_id)

    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(
            "✅ PUBG ID saqlandi!\n\n"
            "⚠️ Endi quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub_then_phone")
        )
        return

    await message.answer("📱 Iltimos, telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
    await state.set_state(RegisterStates.waiting_phone)


# ===================== REGISTER: PHONE =====================

@dp.message(RegisterStates.waiting_phone, F.contact)
async def phone_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    data = await state.get_data()
    referrer_id = data.get("referrer_id")

    # Fake referal himoyasi: bir telefon = bir akkaunt
    existing = db.get_user_by_phone(phone)
    if existing and existing[0] != user_id:
        await message.answer(
            "❌ Bu telefon raqam allaqachon boshqa akkauntda ro'yxatdan o'tgan!\n"
            "Har bir odam faqat bitta akkaunt bilan ishtirok eta oladi.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    db.update_phone(user_id, phone)

    if referrer_id and db.get_user(referrer_id):
        db.add_referral(referrer_id, user_id)
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 <b>{message.from_user.full_name}</b> sizning referal linkinggiz orqali botga qo'shildi!\n"
                f"⏳ Referal 24 soatdan so'ng tasdiqlanadi (faollikni tekshirish uchun).",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Referrer xabar xato: {e}")

    await state.clear()
    await message.answer(
        "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz! Xush kelibsiz! 🎉",
        reply_markup=main_reply_keyboard(user_id == ADMIN_ID)
    )


@dp.message(RegisterStates.waiting_phone)
async def phone_wrong(message: types.Message):
    await message.answer("❗ Iltimos, tugma orqali telefon raqamingizni yuboring:", reply_markup=phone_keyboard())


# ===================== SUBSCRIPTION CHECK =====================

@dp.callback_query(F.data == "check_sub_then_phone")
async def check_sub_then_phone(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    await callback.message.delete()
    await bot.send_message(
        user_id,
        "✅ Obuna tasdiqlandi!\n\n📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(RegisterStates.waiting_phone)


@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    user_id = callback.from_user.id
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    await callback.message.delete()
    await bot.send_message(
        user_id,
        "✅ Obuna tasdiqlandi!",
        reply_markup=main_reply_keyboard(user_id == ADMIN_ID)
    )


# ===================== MAIN MENU =====================

@dp.message(F.text == "🔗 Mening Referal linkım")
async def my_referral(message: types.Message):
    if not await guard(message):
        return
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    count = db.get_referral_count(user_id)
    pending = db.get_pending_referral_count(user_id)
    text = (
        f"🔗 <b>Sizning referal linkingiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"👥 Tasdiqlangan referallar: <b>{count}</b> ta\n"
    )
    if pending > 0:
        text += f"⏳ Kutilayotgan (24 soat ichida): <b>{pending}</b> ta\n"
    text += f"\n💡 Ushbu linkni do'stlaringizga yuboring!"
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📊 Statistika")
async def statistics(message: types.Message):
    if not await guard(message):
        return
    stat_limit = db.get_stat_top_limit()
    top_users = db.get_top_users(stat_limit)
    if not top_users:
        await message.answer("📊 Hali hech kim referal qo'shmagan.")
        return
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    text = f"📊 <b>TOP {stat_limit} — Referal reytingi</b>\n\n"
    for i, (uid, name, uname, pubg_id, ref_count) in enumerate(top_users, 1):
        medal = medals.get(i, f"{i}.")
        un = f"@{uname}" if uname else "—"
        text += (
            f"{medal} <b>{name}</b>\n"
            f"   👤 {un}\n"
            f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
            f"   👥 Referallar: <b>{ref_count}</b>\n\n"
        )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "👤 Mening profilım")
async def my_profile(message: types.Message):
    if not await guard(message):
        return
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        return
    uid, name, uname, pubg_id, phone, ref_id, banned, joined = user
    count = db.get_referral_count(user_id)
    pending = db.get_pending_referral_count(user_id)
    rank = db.get_user_rank(user_id)
    gift_limit = db.get_gift_top_limit()

    text = (
        f"👤 <b>Mening profilım</b>\n\n"
        f"📛 Ism: <b>{name}</b>\n"
        f"🔖 Username: @{uname if uname else 'Yo\'q'}\n"
        f"🎮 PUBG ID: <b>{pubg_id}</b>\n"
        f"📱 Telefon: <b>{phone if phone else 'Yo\'q'}</b>\n"
        f"👥 Referallar: <b>{count}</b> ta"
    )
    if pending > 0:
        text += f" (+{pending} kutilmoqda)"
    text += f"\n🏆 Reyting: <b>#{rank if count > 0 else 'Yo\'q'}</b>\n"

    if count > 0:
        if rank <= gift_limit:
            text += f"\n🎉 Siz hozir sovga zonasidasiz! (Top {gift_limit})"
        else:
            needed = rank - gift_limit
            text += f"\n🎯 Top {gift_limit} ga kirish uchun yana <b>{needed}</b> kishi taklif qiling!"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📜 Referallarim tarixi")
async def referral_history(message: types.Message):
    if not await guard(message):
        return
    user_id = message.from_user.id
    history = db.get_referral_history(user_id, 50)
    if not history:
        await message.answer("📜 Sizda hali referallar tarixi yo'q.")
        return
    text = "📜 <b>Referallarim tarixi</b>\n\n"
    for name, created_at, is_active, confirmed in history:
        date_str = created_at.split("T")[0] if "T" in created_at else created_at[:10]
        if not is_active:
            status = "❌ Chiqib ketgan"
        elif confirmed:
            status = "✅ Tasdiqlangan"
        else:
            status = "⏳ Kutilmoqda"
        text += f"👤 {name} — {date_str} — {status}\n"
    # Telegram xabar uzunligi cheklovi
    if len(text) > 4000:
        text = text[:3950] + "\n\n... (ro'yxat juda uzun)"
    await message.answer(text, parse_mode="HTML")


# ===================== SOVGALAR =====================

@dp.message(F.text == "🎁 Sovgalar")
async def gifts_handler(message: types.Message):
    if not await guard(message):
        return
    gifts = db.get_gifts()
    top_limit = db.get_gift_top_limit()
    end_date = db.get_contest_end_date()

    if not gifts:
        await message.answer(
            "🎁 <b>Sovgalar</b>\n\nHozircha sovgalar belgilanmagan. Tez kunda e'lon qilinadi!",
            parse_mode="HTML"
        )
        return

    text = f"🎁 <b>Sovgalar — Top {top_limit} gacha</b>\n\n"
    for place, gift_name in gifts:
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(place, "🏅")
        text += f"{medal} <b>Top {place}</b> — {gift_name}\n"

    text += f"\n📊 Referal reytingida Top {top_limit} ga kiring va sovgangizni oling!"
    if end_date:
        text += f"\n\n⏰ <b>Konkurs tugash sanasi:</b> {end_date}"

    await message.answer(text, parse_mode="HTML")


# ===================== ADMIN PANEL =====================

@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_reply_keyboard())


@dp.message(F.text == "🔙 Asosiy menyu")
async def back_main(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_reply_keyboard(user_id == ADMIN_ID))


# ---- Bot statistikasi ----
@dp.message(F.text == "📊 Bot statistikasi")
async def bot_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = db.get_total_users()
    total_channels = len(db.get_channels())
    total_referrals = db.get_total_referrals()
    stat_limit = db.get_stat_top_limit()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"📢 Kanallar: <b>{total_channels}</b>\n"
        f"🔗 Faol referallar: <b>{total_referrals}</b>\n"
        f"📈 Statistika top chegarasi: <b>Top {stat_limit}</b>",
        parse_mode="HTML"
    )


# ---- Excel export ----
@dp.message(F.text == "📥 Excel yuklab olish")
async def export_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⏳ Excel fayl tayyorlanmoqda...")

    users = db.get_all_users_with_phones()

    wb = Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"
    ws.append(["№", "Ism", "Username", "PUBG ID", "Telefon", "Referallar soni", "Reyting"])

    for i, (uid, name, uname, pubg_id, phone) in enumerate(users, 1):
        ref_count = db.get_referral_count(uid)
        rank = db.get_user_rank(uid) if ref_count > 0 else "—"
        ws.append([
            i, name, f"@{uname}" if uname else "—", pubg_id,
            phone if phone else "Yo'q", ref_count, rank
        ])

    # Ustun kengligini sozlash
    for col in ws.columns:
        max_len = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    file = BufferedInputFile(buffer.read(), filename="foydalanuvchilar.xlsx")
    await message.answer_document(file, caption=f"📥 Jami {len(users)} ta foydalanuvchi")


# ---- Statistika top sonini sozlash ----
@dp.message(F.text == "📈 Statistika top sonini sozlash")
async def stat_top_setting(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    current = db.get_stat_top_limit()
    await message.answer(
        f"📈 <b>Statistika top sonini sozlash</b>\n\n"
        f"Hozirgi: <b>Top {current}</b>\n\nYangi sonni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_stat_top_limit)


@dp.message(AdminStates.waiting_stat_top_limit)
async def set_stat_top_limit_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        limit = int(message.text.strip())
        if limit < 1:
            raise ValueError
        db.set_stat_top_limit(limit)
        await state.clear()
        await message.answer(f"✅ Statistika endi <b>Top {limit}</b> ni ko'rsatadi!", parse_mode="HTML", reply_markup=admin_reply_keyboard())
    except ValueError:
        await message.answer("❌ Musbat raqam kiriting!")


# ---- Kanallar ro'yxati ----
@dp.message(F.text == "📋 Kanallar ro'yxati")
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = db.get_channels_with_names()
    if not channels:
        await message.answer("📋 Hech qanday kanal qo'shilmagan.")
        return
    text = "📋 <b>Majburiy obuna kanallari:</b>\n\n"
    for i, (uname, name) in enumerate(channels, 1):
        text += f"{i}. {name} — <code>{uname}</code>\n"
    await message.answer(text, parse_mode="HTML")


# ---- Kanal qo'shish ----
@dp.message(F.text == "➕ Kanal qo'shish")
async def add_channel_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "➕ <b>Kanal qo'shish</b>\n\nKanal <b>username</b> ini yuboring:\nMisol: <code>@kanalUsername</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_channel_username)


@dp.message(AdminStates.waiting_channel_username)
async def add_channel_username(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    channel = message.text.strip()
    if not channel.startswith("@"):
        channel = "@" + channel
    try:
        chat = await bot.get_chat(channel)
        await state.update_data(channel_username=channel)
        await message.answer(
            f"✅ Kanal topildi: <b>{chat.title}</b>\n\nKanal <b>nomini</b> kiriting:",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_channel_name)
    except Exception:
        await message.answer("❌ Kanal topilmadi! Bot kanalga <b>Admin</b> bo'lishini tekshiring.", parse_mode="HTML")


@dp.message(AdminStates.waiting_channel_name)
async def add_channel_name(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    channel_username = data.get("channel_username")
    channel_name = message.text.strip()
    db.add_channel(channel_username, channel_name)
    await state.clear()
    await message.answer(
        f"✅ <b>{channel_name}</b> kanali qo'shildi!\nUsername: <code>{channel_username}</code>",
        parse_mode="HTML", reply_markup=admin_reply_keyboard()
    )


# ---- Kanal o'chirish ----
@dp.message(F.text == "➖ Kanal o'chirish")
async def remove_channel_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = db.get_channels_with_names()
    if not channels:
        await message.answer("📋 Kanallar ro'yxati bo'sh.")
        return
    buttons = [[InlineKeyboardButton(text=f"❌ {name} ({uname})", callback_data=f"del_ch:{uname}")]
               for uname, name in channels]
    await message.answer("➖ O'chiriladigan kanalni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("del_ch:"))
async def delete_channel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    channel = callback.data.split(":", 1)[1]
    db.remove_channel(channel)
    await callback.answer(f"✅ {channel} o'chirildi!", show_alert=True)
    await callback.message.delete()


# ---- Foydalanuvchilar raqamlari ----
@dp.message(F.text == "👤 Foydalanuvchilar raqamlari")
async def users_phones(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = db.get_all_users_with_phones()
    if not users:
        await message.answer("👤 Foydalanuvchilar yo'q.")
        return
    text = "👤 <b>Foydalanuvchilar ma'lumotlari:</b>\n\n"
    chunk = ""
    for uid, name, uname, pubg_id, phone in users:
        un = f"@{uname}" if uname else "—"
        ph = phone if phone else "Yo'q"
        entry = (
            f"👤 <b>{name}</b>\n"
            f"   TG: {un}\n"
            f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
            f"   📱 Raqam: <code>{ph}</code>\n\n"
        )
        if len(chunk) + len(entry) > 3500:
            await message.answer(text + chunk, parse_mode="HTML")
            chunk = entry
            text = ""
        else:
            chunk += entry
    if chunk:
        await message.answer((text + chunk).strip(), parse_mode="HTML")


# ---- Ban / Unban ----
@dp.message(F.text == "🚫 Ban / Unban")
async def ban_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    buttons = [
        [InlineKeyboardButton(text="🚫 Ban qilish", callback_data="ban_action")],
        [InlineKeyboardButton(text="✅ Bandan chiqarish", callback_data="unban_action")],
    ]
    await message.answer("🚫 <b>Ban boshqaruvi</b>", parse_mode="HTML",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data == "ban_action")
async def ban_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "🚫 Ban qilinadigan foydalanuvchining <b>username</b> ini yuboring:\nMisol: <code>@username</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_ban_username)


@dp.message(AdminStates.waiting_ban_username)
async def ban_user_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    username = message.text.strip().lstrip("@")
    user = db.get_user_by_username(username)
    if not user:
        await message.answer(f"❌ @{username} topilmadi!")
        await state.clear()
        return
    db.ban_user(user[0])
    await state.clear()
    await message.answer(f"✅ <b>@{username}</b> ban qilindi!", parse_mode="HTML", reply_markup=admin_reply_keyboard())
    try:
        await bot.send_message(user[0], "🚫 Siz botdan bloklangansiz.")
    except Exception:
        pass


@dp.callback_query(F.data == "unban_action")
async def unban_action(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "✅ Bandan chiqariladigan foydalanuvchining <b>username</b> ini yuboring:\nMisol: <code>@username</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_unban_username)


@dp.message(AdminStates.waiting_unban_username)
async def unban_user_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    username = message.text.strip().lstrip("@")
    user = db.get_user_by_username(username)
    if not user:
        await message.answer(f"❌ @{username} topilmadi!")
        await state.clear()
        return
    db.unban_user(user[0])
    await state.clear()
    await message.answer(f"✅ <b>@{username}</b> bandan chiqarildi!", parse_mode="HTML", reply_markup=admin_reply_keyboard())
    try:
        await bot.send_message(user[0], "✅ Baningiz olib tashlandi! Botdan foydalanishingiz mumkin.")
    except Exception:
        pass


# ---- Foydalanuvchi qidirish ----
@dp.message(F.text == "🔍 Foydalanuvchi qidirish")
async def search_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "🔍 <b>Foydalanuvchi qidirish</b>\n\nUsername yoki PUBG ID yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_search_user)


@dp.message(AdminStates.waiting_search_user)
async def search_user_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    query = message.text.strip()
    await state.clear()
    user = None
    if query.startswith("@"):
        user = db.get_user_by_username(query.lstrip("@"))
    else:
        user = db.get_user_by_pubg_id(query)
    if not user:
        await message.answer(f"❌ '{query}' bo'yicha foydalanuvchi topilmadi.", reply_markup=admin_reply_keyboard())
        return
    uid, name, uname, pubg_id, phone, ref_id, banned, joined = user
    ref_count = db.get_referral_count(uid)
    rank = db.get_user_rank(uid)
    ban_status = "🚫 Ban" if banned else "✅ Faol"
    await message.answer(
        f"🔍 <b>Qidiruv natijasi</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"🔖 Username: @{uname if uname else 'Yo\'q'}\n"
        f"🆔 Telegram ID: <code>{uid}</code>\n"
        f"🎮 PUBG ID: <code>{pubg_id}</code>\n"
        f"📱 Telefon: <code>{phone if phone else 'Yo\'q'}</code>\n"
        f"👥 Referallar: <b>{ref_count}</b> ta\n"
        f"🏆 Reyting: <b>#{rank}</b>\n"
        f"📌 Holat: {ban_status}",
        parse_mode="HTML",
        reply_markup=admin_reply_keyboard()
    )


# ---- Foydalanuvchiga xabar ----
@dp.message(F.text == "📨 Foydalanuvchiga xabar")
async def msg_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📨 Foydalanuvchining <b>Telegram ID</b> sini yuboring:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_msg_user_id)


@dp.message(AdminStates.waiting_msg_user_id)
async def msg_user_id_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
        await state.update_data(target_id=target_id)
        await message.answer("✏️ Yubormoqchi bo'lgan xabaringizni yozing:")
        await state.set_state(AdminStates.waiting_msg_text)
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Raqam kiriting:")


@dp.message(AdminStates.waiting_msg_text)
async def msg_user_text(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    target_id = data.get("target_id")
    await state.clear()
    try:
        await bot.send_message(target_id, f"📩 <b>Admin xabari:</b>\n\n{message.text}", parse_mode="HTML")
        await message.answer("✅ Xabar yuborildi!", reply_markup=admin_reply_keyboard())
    except Exception:
        await message.answer(f"❌ {target_id} ga xabar yuborib bo'lmadi.", reply_markup=admin_reply_keyboard())


# ---- Hammaga xabar ----
@dp.message(F.text == "📢 Hammaga xabar")
async def broadcast_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:")
    await state.set_state(AdminStates.waiting_broadcast_text)


@dp.message(AdminStates.waiting_broadcast_text)
async def broadcast_send(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    user_ids = db.get_all_user_ids()
    success, failed = 0, 0
    status_msg = await message.answer(f"📤 Yuborilmoqda... 0/{len(user_ids)}")
    for i, uid in enumerate(user_ids):
        try:
            await bot.send_message(uid, f"📢 <b>Admin xabari:</b>\n\n{message.text}", parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1
        if (i + 1) % 20 == 0:
            try:
                await status_msg.edit_text(f"📤 Yuborilmoqda... {i+1}/{len(user_ids)}")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await status_msg.edit_text(
        f"✅ Xabar yuborish tugadi!\n\n✔️ Muvaffaqiyatli: <b>{success}</b>\n❌ Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ---- Sovgalarni boshqarish ----
@dp.message(F.text == "🎁 Sovgalarni boshqarish")
async def gifts_admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    gifts = db.get_gifts()
    top_limit = db.get_gift_top_limit()
    end_date = db.get_contest_end_date()
    text = (
        f"🎁 <b>Sovgalar boshqaruvi</b>\n\n"
        f"📌 Sovga beriladigan o'rinlar: <b>Top {top_limit}</b>\n"
        f"⏰ Konkurs tugash sanasi: <b>{end_date if end_date else 'Belgilanmagan'}</b>\n\n"
    )
    if gifts:
        text += "🏆 <b>Joriy sovgalar:</b>\n"
        for place, gift_name in gifts:
            text += f"  Top {place} — {gift_name}\n"
    else:
        text += "Hozircha sovgalar yo'q.\n"
    buttons = [
        [InlineKeyboardButton(text="➕ Sovga qo'shish / yangilash", callback_data="add_gift")],
        [InlineKeyboardButton(text="➖ Sovga o'chirish", callback_data="remove_gift")],
        [InlineKeyboardButton(text=f"🔢 Nechta o'ringa sovga (Top {top_limit})", callback_data="set_top_limit")],
        [InlineKeyboardButton(text="📅 Konkurs tugash sanasini belgilash", callback_data="set_end_date")],
    ]
    await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data == "add_gift")
async def add_gift_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("➕ <b>Qaysi o'ringa sovga?</b>\nMisol: <code>1</code>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_gift_place)


@dp.message(AdminStates.waiting_gift_place)
async def add_gift_place(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        place = int(message.text.strip())
        if place < 1:
            raise ValueError
        await state.update_data(gift_place=place)
        await message.answer(f"🎁 Top <b>{place}</b> uchun sovga nomi:", parse_mode="HTML")
        await state.set_state(AdminStates.waiting_gift_name)
    except ValueError:
        await message.answer("❌ Musbat raqam kiriting!")


@dp.message(AdminStates.waiting_gift_name)
async def add_gift_name(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    place = data.get("gift_place")
    db.set_gift(place, message.text.strip())
    await state.clear()
    await message.answer(f"✅ Top {place} uchun sovga saqlandi!", reply_markup=admin_reply_keyboard())


@dp.callback_query(F.data == "remove_gift")
async def remove_gift_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    gifts = db.get_gifts()
    if not gifts:
        await callback.answer("Sovgalar yo'q!", show_alert=True)
        return
    buttons = [[InlineKeyboardButton(text=f"❌ Top {p} — {n}", callback_data=f"del_gift:{p}")] for p, n in gifts]
    await callback.message.edit_text("➖ O'chiriladigan sovgani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("del_gift:"))
async def delete_gift(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    place = int(callback.data.split(":")[1])
    db.remove_gift(place)
    await callback.answer(f"✅ Top {place} sovgasi o'chirildi!", show_alert=True)
    await callback.message.delete()


@dp.callback_query(F.data == "set_top_limit")
async def set_top_limit_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("🔢 <b>Sovga beriladigan o'rinlar sonini kiriting</b>\nMisol: <code>10</code>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_gift_top_limit)


@dp.message(AdminStates.waiting_gift_top_limit)
async def set_top_limit(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        limit = int(message.text.strip())
        if limit < 1:
            raise ValueError
        db.set_gift_top_limit(limit)
        await state.clear()
        await message.answer(f"✅ Sovga beriladigan o'rinlar: <b>Top {limit}</b>", parse_mode="HTML", reply_markup=admin_reply_keyboard())
    except ValueError:
        await message.answer("❌ Musbat raqam kiriting!")


@dp.callback_query(F.data == "set_end_date")
async def set_end_date_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "📅 <b>Konkurs tugash sanasini kiriting:</b>\nMisol: <code>15 Iyul 2025, soat 20:00</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_end_date)


@dp.message(AdminStates.waiting_end_date)
async def set_end_date_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    db.set_contest_end_date(message.text.strip())
    await state.clear()
    await message.answer(f"✅ Konkurs tugash sanasi: <b>{message.text.strip()}</b>", parse_mode="HTML", reply_markup=admin_reply_keyboard())


# ---- G'oliblarni belgilash ----
@dp.message(F.text == "🏆 G'oliblarni belgilash")
async def mark_winners_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = db.mark_winners()
    if count == 0:
        await message.answer("⚠️ Hozircha referal yig'gan odamlar yo'q, g'oliblar belgilanmadi.")
        return
    await message.answer(
        f"✅ <b>{count}</b> ta g'olib belgilandi va saqlandi!\n\n"
        f"'🏅 G'oliblar ro'yxati' tugmasi orqali ko'rishingiz mumkin.",
        parse_mode="HTML"
    )


@dp.message(F.text == "🏅 G'oliblar ro'yxati")
async def winners_list_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    winners = db.get_winners()
    if not winners:
        await message.answer("🏅 Hali g'oliblar belgilanmagan.\n\n'🏆 G'oliblarni belgilash' tugmasini bosing.")
        return
    text = "🏅 <b>G'oliblar ro'yxati</b>\n\n"
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for place, name, uname, pubg_id, ref_count, gift_name in winners:
        medal = medals.get(place, "🏅")
        un = f"@{uname}" if uname else "—"
        text += (
            f"{medal} <b>Top {place} — {name}</b>\n"
            f"   👤 {un}\n"
            f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
            f"   👥 Referallar: {ref_count}\n"
            f"   🎁 Sovrin: {gift_name}\n\n"
        )
    if len(text) > 4000:
        text = text[:3950] + "\n\n... (ro'yxat juda uzun)"
    await message.answer(text, parse_mode="HTML")


# ---- Konkursni tugatish ----
@dp.message(F.text == "🏁 Konkursni tugatish")
async def end_contest_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    buttons = [
        [InlineKeyboardButton(text="✅ Ha, tugatish", callback_data="confirm_end_contest")],
        [InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data="cancel_end_contest")],
    ]
    await message.answer(
        "⚠️ <b>Diqqat!</b>\n\n"
        "Konkursni tugatishni tasdiqlaysizmi?\n\n"
        "💡 Tavsiya: avval '🏆 G'oliblarni belgilash' tugmasini bosing — aks holda g'oliblar tarixi saqlanmaydi!\n\n"
        "🗑 Barcha referallar o'chiriladi\n"
        "🗑 Sovgalar ro'yxati tozalanadi\n"
        "🗑 Tugash sanasi o'chiriladi\n"
        "✅ Foydalanuvchilar saqlanadi\n\n"
        "<b>Bu amalni qaytarib bo'lmaydi!</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(F.data == "confirm_end_contest")
async def do_end_contest(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    user_ids = db.get_all_user_ids()
    db.reset_contest()
    await callback.message.edit_text(
        "✅ <b>Konkurs muvaffaqiyatli tugatildi!</b>\n\n"
        "🗑 Barcha referallar tozalandi\n🗑 Sovgalar o'chirildi\n🔄 Foydalanuvchilar saqlanib qoldi",
        parse_mode="HTML"
    )
    success = 0
    for uid in user_ids:
        try:
            await bot.send_message(
                uid,
                "🏁 <b>Konkurs yakunlandi!</b>\n\nBarcha g'oliblar bilan tez orada bog'lanamiz.\nYangi konkursda ham ishtirok eting! 🎁",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await bot.send_message(ADMIN_ID, f"📢 Konkurs tugashi haqida xabar {success} ta foydalanuvchiga yuborildi.")


@dp.callback_query(F.data == "cancel_end_contest")
async def cancel_end_contest(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("❌ Bekor qilindi.")


# ===================== KUNLIK ESLATMA + TOP 3 E'LONI =====================

async def daily_reminder():
    await asyncio.sleep(86400)
    while True:
        user_ids = db.get_all_user_ids()
        for uid in user_ids:
            try:
                user = db.get_user(uid)
                if not user or not user[4]:
                    continue
                count = db.get_referral_count(uid)
                if count == 0:
                    continue
                rank = db.get_user_rank(uid)
                gift_limit = db.get_gift_top_limit()
                if rank <= gift_limit:
                    msg = (
                        f"📊 <b>Kunlik statistika</b>\n\n"
                        f"🏆 Siz hozir <b>#{rank}</b> dasiz — sovga zonasida! 🎉\n"
                        f"👥 Referallar: <b>{count}</b> ta\n\nShunday davom eting! 💪"
                    )
                else:
                    needed = rank - gift_limit
                    msg = (
                        f"📊 <b>Kunlik statistika</b>\n\n"
                        f"🏆 Siz hozir <b>#{rank}</b> dasiz\n"
                        f"👥 Referallar: <b>{count}</b> ta\n\n"
                        f"🎯 Top {gift_limit} ga kirish uchun yana <b>{needed}</b> ta referal kerak!\n"
                        f"🔗 Referal linkingizni do'stlaringizga yuboring!"
                    )
                await bot.send_message(uid, msg, parse_mode="HTML")
            except Exception:
                pass
            await asyncio.sleep(0.05)

        # Admin uchun kunlik Top 3 xabari
        try:
            top3 = db.get_top_users(3)
            if top3:
                medals = ["🥇", "🥈", "🥉"]
                text = "📈 <b>Bugungi Top 3</b>\n\n"
                for i, (uid, name, uname, pubg_id, ref_count) in enumerate(top3):
                    un = f"@{uname}" if uname else "—"
                    text += f"{medals[i]} {name} ({un}) — {ref_count} referal\n"
                await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Top3 xabar xato: {e}")

        await asyncio.sleep(86400)


# ===================== CHANNEL MEMBER UPDATE =====================

@dp.chat_member()
async def channel_member_update(update: types.ChatMemberUpdated):
    channels = db.get_channels()
    chat_username = f"@{update.chat.username}" if update.chat.username else str(update.chat.id)
    if chat_username not in channels and str(update.chat.id) not in channels:
        return

    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    target_user = update.new_chat_member.user

    if old_status in ["member", "administrator", "creator"] and new_status in ["left", "kicked"]:
        referrer_id = db.get_referrer_of(target_user.id)
        if referrer_id:
            db.deactivate_referral(referrer_id, target_user.id)
            new_count = db.get_referral_count(referrer_id)
            try:
                await bot.send_message(
                    referrer_id,
                    f"⚠️ <b>Referal ayirildi!</b>\n\n"
                    f"👤 <b>{target_user.full_name}</b> kanaldan chiqib ketdi.\n"
                    f"📉 Siz 1 ta referaldan mahrum bo'ldingiz.\n"
                    f"📊 Joriy referallaringiz: <b>{new_count}</b> ta",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Referer xabar xato: {e}")

    elif old_status in ["left", "kicked", "banned"] and new_status in ["member", "administrator", "creator"]:
        referrer_id = db.get_referrer_of(target_user.id)
        if referrer_id:
            db.add_referral(referrer_id, target_user.id)
            new_count = db.get_referral_count(referrer_id)
            try:
                await bot.send_message(
                    referrer_id,
                    f"🎉 <b>Referal qaytdi!</b>\n\n"
                    f"👤 <b>{target_user.full_name}</b> kanalga qaytib obuna bo'ldi.\n"
                    f"📈 Referalingiz qaytarildi.\n"
                    f"📊 Joriy referallaringiz: <b>{new_count}</b> ta",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Referer xabar xato: {e}")


# ===================== MAIN =====================

async def main():
    logger.info("Bot ishga tushdi!")
    asyncio.create_task(daily_reminder())
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    asyncio.run(main())
