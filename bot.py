import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database

BOT_TOKEN = "8935442087:AAEkbThT6uMQQqW_LkiK6P0PV5q4QuxlV0o"
ADMIN_ID = 7808709581

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database()

# ===================== TILLAR =====================

TEXTS = {
    'uz': {
        'welcome': "👋 Salom, <b>{name}</b>!\n\n🌐 Tilni tanlang:",
        'choose_lang': "🌐 Tilni tanlang / Выберите язык:",
        'lang_set': "✅ Til o'zbek tiliga o'rnatildi!",
        'enter_pubg': "🎮 Iltimos, <b>PUBG ID</b> ingizni yuboring:",
        'enter_phone': "📱 Iltimos, telefon raqamingizni yuboring:",
        'phone_btn': "📱 Telefon raqamni yuborish",
        'sub_required': "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        'sub_check': "✅ Tekshirish",
        'sub_ok': "✅ Obuna tasdiqlandi!",
        'sub_fail': "❌ Hali barcha kanallarga obuna bo'lmadingiz!",
        'banned': "🚫 Siz botdan bloklangansiz.",
        'registered': "✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!",
        'phone_duplicate': "⚠️ Bu telefon raqam allaqachon ro'yxatdan o'tgan!\n\nHar bir raqam faqat bir marta ishlatilishi mumkin.",
        'ref_link_text': "🔗 <b>Sizning referal linkingiz:</b>\n<code>{link}</code>\n\n👥 Jami taklif qilganlar: <b>{count}</b> ta\n📅 Bu hafta: <b>{weekly}</b> ta\n\n💡 Ushbu linkni do'stlaringizga yuboring!",
        'new_referral': "🎉 <b>{name}</b> sizning referal linkinggiz orqali qo'shildi!\n📊 Jami referallaringiz: <b>{count}</b>",
        'ref_removed': "⚠️ <b>Referal ayirildi!</b>\n\n👤 <b>{name}</b> kanaldan chiqib ketdi.\n📉 Joriy referallaringiz: <b>{count}</b> ta",
        'ref_returned': "🎉 <b>Referal qaytdi!</b>\n\n👤 <b>{name}</b> kanalga qaytdi.\n📈 Joriy referallaringiz: <b>{count}</b> ta",
        'top_title': "📊 <b>TOP 20 — Referal reytingi</b>\n\n",
        'top_weekly_title': "📊 <b>TOP 20 — Bu haftaning reytingi</b>\n\n",
        'no_stats': "📊 Hali statistika yo'q.",
        'profile': "👤 <b>Mening profilım</b>\n\n📛 Ism: <b>{name}</b>\n🔖 Username: @{username}\n🎮 PUBG ID: <b>{pubg_id}</b>\n📱 Telefon: <b>{phone}</b>\n👥 Jami referallar: <b>{count}</b> ta\n📅 Bu hafta: <b>{weekly}</b> ta\n🏆 Reyting: <b>#{rank}</b>",
        'gifts_empty': "🎁 <b>Sovgalar</b>\n\nHozircha sovgalar belgilanmagan. Tez kunda e'lon qilinadi!",
        'daily_reminder': "📊 <b>Kunlik eslatma</b>\n\nSiz hozir <b>#{rank}</b> dasiz!\n🎯 Top 10 ga kirish uchun <b>{need}</b> ta referal yetishmayapti.\n\n🔗 Referal linkingizni do'stlarga yuboring!",
        'main_menu': "🏠 Asosiy menyu:",
        'btn_ref': "🔗 Mening Referal linkım",
        'btn_top': "📊 Statistika (Top 20)",
        'btn_profile': "👤 Mening profilım",
        'btn_gifts': "🎁 Sovgalar",
        'btn_lang': "🌐 Til",
        'btn_admin': "⚙️ Admin Panel",
        'btn_weekly': "📅 Haftalik Top",
        'btn_alltime': "🏆 Umumiy Top",
    },
    'ru': {
        'welcome': "👋 Привет, <b>{name}</b>!\n\n🌐 Выберите язык:",
        'choose_lang': "🌐 Выберите язык / Tilni tanlang:",
        'lang_set': "✅ Язык установлен на русский!",
        'enter_pubg': "🎮 Пожалуйста, введите ваш <b>PUBG ID</b>:",
        'enter_phone': "📱 Пожалуйста, отправьте ваш номер телефона:",
        'phone_btn': "📱 Отправить номер телефона",
        'sub_required': "⚠️ Для использования бота подпишитесь на каналы:",
        'sub_check': "✅ Проверить",
        'sub_ok': "✅ Подписка подтверждена!",
        'sub_fail': "❌ Вы ещё не подписались на все каналы!",
        'banned': "🚫 Вы заблокированы в боте.",
        'registered': "✅ Вы успешно зарегистрированы!",
        'phone_duplicate': "⚠️ Этот номер телефона уже зарегистрирован!\n\nКаждый номер можно использовать только один раз.",
        'ref_link_text': "🔗 <b>Ваша реферальная ссылка:</b>\n<code>{link}</code>\n\n👥 Всего приглашено: <b>{count}</b>\n📅 На этой неделе: <b>{weekly}</b>\n\n💡 Отправьте эту ссылку друзьям!",
        'new_referral': "🎉 <b>{name}</b> присоединился по вашей ссылке!\n📊 Всего рефералов: <b>{count}</b>",
        'ref_removed': "⚠️ <b>Реферал удалён!</b>\n\n👤 <b>{name}</b> покинул канал.\n📉 Текущих рефералов: <b>{count}</b>",
        'ref_returned': "🎉 <b>Реферал вернулся!</b>\n\n👤 <b>{name}</b> снова подписался.\n📈 Текущих рефералов: <b>{count}</b>",
        'top_title': "📊 <b>ТОП 20 — Рейтинг рефералов</b>\n\n",
        'top_weekly_title': "📊 <b>ТОП 20 — Рейтинг этой недели</b>\n\n",
        'no_stats': "📊 Статистики пока нет.",
        'profile': "👤 <b>Мой профиль</b>\n\n📛 Имя: <b>{name}</b>\n🔖 Username: @{username}\n🎮 PUBG ID: <b>{pubg_id}</b>\n📱 Телефон: <b>{phone}</b>\n👥 Всего рефералов: <b>{count}</b>\n📅 На этой неделе: <b>{weekly}</b>\n🏆 Рейтинг: <b>#{rank}</b>",
        'gifts_empty': "🎁 <b>Призы</b>\n\nПризы ещё не объявлены. Скоро будут!",
        'daily_reminder': "📊 <b>Ежедневное напоминание</b>\n\nВы сейчас на <b>#{rank}</b> месте!\n🎯 До Топ 10 не хватает <b>{need}</b> рефералов.\n\n🔗 Отправьте реферальную ссылку друзьям!",
        'main_menu': "🏠 Главное меню:",
        'btn_ref': "🔗 Моя реферальная ссылка",
        'btn_top': "📊 Статистика (Топ 20)",
        'btn_profile': "👤 Мой профиль",
        'btn_gifts': "🎁 Призы",
        'btn_lang': "🌐 Язык",
        'btn_admin': "⚙️ Админ панель",
        'btn_weekly': "📅 Топ недели",
        'btn_alltime': "🏆 Общий Топ",
    }
}

def t(user_id, key, **kwargs):
    lang = db.get_user_language(user_id)
    text = TEXTS.get(lang, TEXTS['uz']).get(key, TEXTS['uz'].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


# ===================== STATES =====================

class RegisterStates(StatesGroup):
    waiting_lang = State()
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
    waiting_end_date = State()
    waiting_search_query = State()


# ===================== KEYBOARDS =====================

def main_reply_keyboard(user_id, is_admin=False):
    lang = db.get_user_language(user_id)
    tx = TEXTS.get(lang, TEXTS['uz'])
    buttons = [
        [KeyboardButton(text=tx['btn_ref']), KeyboardButton(text=tx['btn_top'])],
        [KeyboardButton(text=tx['btn_profile']), KeyboardButton(text=tx['btn_gifts'])],
        [KeyboardButton(text=tx['btn_lang'])],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text=tx['btn_admin'])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_reply_keyboard():
    buttons = [
        [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="➖ Kanal o'chirish")],
        [KeyboardButton(text="📋 Kanallar ro'yxati"), KeyboardButton(text="📊 Bot statistikasi")],
        [KeyboardButton(text="👤 Foydalanuvchilar raqamlari"), KeyboardButton(text="🚫 Ban / Unban")],
        [KeyboardButton(text="📨 Foydalanuvchiga xabar"), KeyboardButton(text="📢 Hammaga xabar")],
        [KeyboardButton(text="🎁 Sovgalarni boshqarish"), KeyboardButton(text="🔍 Foydalanuvchi qidirish")],
        [KeyboardButton(text="🏁 Konkursni tugatish")],
        [KeyboardButton(text="🔙 Asosiy menyu")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def phone_keyboard(user_id):
    lang = db.get_user_language(user_id)
    tx = TEXTS.get(lang, TEXTS['uz'])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tx['phone_btn'], request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )


def lang_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru")],
    ])


def subscription_inline_keyboard(not_subscribed: list, check_callback: str = "check_sub"):
    buttons = []
    for username, name in not_subscribed:
        display = name if name else username
        buttons.append([InlineKeyboardButton(text=f"📢 {display}", url=f"https://t.me/{username.lstrip('@')}")])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data=check_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def top_type_keyboard(user_id):
    lang = db.get_user_language(user_id)
    tx = TEXTS.get(lang, TEXTS['uz'])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tx['btn_weekly'], callback_data="top:weekly"),
         InlineKeyboardButton(text=tx['btn_alltime'], callback_data="top:alltime")],
    ])


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


def normalize_phone(phone):
    """Telefon raqamidan faqat raqamlarni olish"""
    return ''.join(filter(str.isdigit, phone))[-9:]


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

    if not user:
        await state.update_data(referrer_id=referrer_id, full_name=full_name, username=username)
        await message.answer(
            f"👋 Salom, <b>{full_name}</b>! / Привет, <b>{full_name}</b>!\n\n"
            "🌐 Tilni tanlang / Выберите язык:",
            parse_mode="HTML",
            reply_markup=lang_inline_keyboard()
        )
        await state.set_state(RegisterStates.waiting_lang)
        return

    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(
            t(user_id, 'sub_required'),
            reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub")
        )
        return

    await message.answer(
        t(user_id, 'main_menu'),
        reply_markup=main_reply_keyboard(user_id, user_id == ADMIN_ID)
    )


# ===================== TIL TANLASH =====================

@dp.callback_query(F.data.startswith("setlang:"))
async def set_language(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = callback.data.split(":")[1]

    current_state = await state.get_state()

    # Ro'yxatdan o'tish jarayonida til tanlash
    if current_state == RegisterStates.waiting_lang:
        await state.update_data(language=lang)
        db.update_language(user_id, lang)  # vaqtinchalik saqlash (user yo'q bo'lsa ignore)
        tx = TEXTS.get(lang, TEXTS['uz'])
        await callback.message.edit_text(
            tx['enter_pubg'],
            parse_mode="HTML"
        )
        await state.set_state(RegisterStates.waiting_pubg_id)
        return

    # Mavjud foydalanuvchi til o'zgartirishi
    db.update_language(user_id, lang)
    tx = TEXTS.get(lang, TEXTS['uz'])
    await callback.message.edit_text(tx['lang_set'])
    await bot.send_message(
        user_id,
        tx['main_menu'],
        reply_markup=main_reply_keyboard(user_id, user_id == ADMIN_ID)
    )


@dp.message(F.text.in_(["🌐 Til", "🌐 Язык"]))
async def change_language(message: types.Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        return
    await message.answer(
        t(user_id, 'choose_lang'),
        reply_markup=lang_inline_keyboard()
    )


# ===================== REGISTER: PUBG ID =====================

@dp.message(RegisterStates.waiting_pubg_id)
async def pubg_id_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    pubg_id = message.text.strip()
    data = await state.get_data()
    referrer_id = data.get("referrer_id")
    full_name = data.get("full_name", message.from_user.full_name)
    username = data.get("username", message.from_user.username or "")
    language = data.get("language", "uz")

    db.add_user(user_id, full_name, username, pubg_id, referrer_id, language)
    await state.update_data(referrer_id=referrer_id, pubg_id=pubg_id)

    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await state.update_data(step="need_phone_after_sub")
        await message.answer(
            "✅ PUBG ID saqlandi!\n\n" + t(user_id, 'sub_required'),
            reply_markup=subscription_inline_keyboard(not_subscribed, "check_sub_then_phone")
        )
        return

    await message.answer(
        t(user_id, 'enter_phone'),
        reply_markup=phone_keyboard(user_id)
    )
    await state.set_state(RegisterStates.waiting_phone)


# ===================== REGISTER: PHONE =====================

@dp.message(RegisterStates.waiting_phone, F.contact)
async def phone_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    data = await state.get_data()
    referrer_id = data.get("referrer_id")

    # Fake referal himoyasi: bir telefon = bir akkaunt
    normalized = normalize_phone(phone)
    existing = db.get_user_by_phone(phone)
    if not existing:
        # Normallashtirish bilan ham tekshir
        all_users = db.get_all_users_with_phones()
        for uid, *_, ph in all_users:
            if ph and normalize_phone(ph) == normalized and uid != user_id:
                existing = (uid,)
                break

    if existing and existing[0] != user_id:
        await message.answer(
            t(user_id, 'phone_duplicate'),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return

    db.update_phone(user_id, phone)

    # Referal qo'shish — faqat ro'yxat tugagandan keyin
    if referrer_id and db.get_user(referrer_id):
        db.add_referral(referrer_id, user_id)
        try:
            full_name = message.from_user.full_name
            await bot.send_message(
                referrer_id,
                t(referrer_id, 'new_referral',
                  name=full_name,
                  count=db.get_referral_count(referrer_id)),
                parse_mode="HTML"
            )
            # Referral GIF yuborish
            await bot.send_animation(
                referrer_id,
                animation="https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif"
            )
        except Exception as e:
            logger.error(f"Referrer xabar xato: {e}")

    await state.clear()
    await message.answer(
        t(user_id, 'registered'),
        reply_markup=main_reply_keyboard(user_id, user_id == ADMIN_ID)
    )


@dp.message(RegisterStates.waiting_phone)
async def phone_wrong(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        "❗ Iltimos, tugma orqali telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard(user_id)
    )


# ===================== SUBSCRIPTION CHECK =====================

@dp.callback_query(F.data == "check_sub_then_phone")
async def check_sub_then_phone(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed:
        await callback.answer(t(user_id, 'sub_fail'), show_alert=True)
        return
    await callback.message.delete()
    await bot.send_message(
        user_id,
        "✅ Obuna tasdiqlandi!\n\n" + t(user_id, 'enter_phone'),
        reply_markup=phone_keyboard(user_id)
    )
    await state.set_state(RegisterStates.waiting_phone)


@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    user_id = callback.from_user.id
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed:
        await callback.answer(t(user_id, 'sub_fail'), show_alert=True)
        return
    await callback.message.delete()
    await bot.send_message(
        user_id,
        t(user_id, 'sub_ok'),
        reply_markup=main_reply_keyboard(user_id, user_id == ADMIN_ID)
    )


# ===================== MAIN MENU =====================

@dp.message(F.text.in_(["🔗 Mening Referal linkım", "🔗 Моя реферальная ссылка"]))
async def my_referral(message: types.Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        return
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(t(user_id, 'sub_required'),
                             reply_markup=subscription_inline_keyboard(not_subscribed))
        return
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"
    count = db.get_referral_count(user_id)
    weekly = db.get_user_ref_count_weekly(user_id)
    await message.answer(
        t(user_id, 'ref_link_text', link=ref_link, count=count, weekly=weekly),
        parse_mode="HTML"
    )


@dp.message(F.text.in_(["📊 Statistika (Top 20)", "📊 Статистика (Топ 20)"]))
async def statistics(message: types.Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        return
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(t(user_id, 'sub_required'),
                             reply_markup=subscription_inline_keyboard(not_subscribed))
        return
    await message.answer(
        "📊 Qaysi reytingni ko'rmoqchisiz?",
        reply_markup=top_type_keyboard(user_id)
    )


@dp.callback_query(F.data.startswith("top:"))
async def show_top(callback: CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split(":")[1]
    weekly = (mode == "weekly")

    top_users = db.get_top_users(20, weekly=weekly)
    if not top_users:
        await callback.answer(t(user_id, 'no_stats'), show_alert=True)
        return

    title_key = 'top_weekly_title' if weekly else 'top_title'
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    text = t(user_id, title_key)
    for i, (uid, name, uname, pubg_id, ref_count) in enumerate(top_users, 1):
        medal = medals.get(i, f"{i}.")
        un = f"@{uname}" if uname else "—"
        text += (
            f"{medal} <b>{name}</b>\n"
            f"   👤 {un}\n"
            f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
            f"   👥 Referallar: <b>{ref_count}</b>\n\n"
        )
    await callback.message.edit_text(text, parse_mode="HTML")


@dp.message(F.text.in_(["👤 Mening profilım", "👤 Мой профиль"]))
async def my_profile(message: types.Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        return
    user = db.get_user(user_id)
    if not user:
        await message.answer("Profil topilmadi!")
        return
    uid, name, uname, pubg_id, phone, ref_id, banned, language, joined = user
    count = db.get_referral_count(user_id)
    weekly = db.get_user_ref_count_weekly(user_id)
    rank = db.get_user_rank(user_id)
    await message.answer(
        t(user_id, 'profile',
          name=name,
          username=uname if uname else "Yo'q",
          pubg_id=pubg_id,
          phone=phone if phone else "Yo'q",
          count=count,
          weekly=weekly,
          rank=rank),
        parse_mode="HTML"
    )


# ===================== SOVGALAR =====================

@dp.message(F.text.in_(["🎁 Sovgalar", "🎁 Призы"]))
async def gifts_handler(message: types.Message):
    user_id = message.from_user.id
    if db.is_banned(user_id):
        return
    not_subscribed = await check_subscriptions(user_id)
    if not_subscribed and user_id != ADMIN_ID:
        await message.answer(t(user_id, 'sub_required'),
                             reply_markup=subscription_inline_keyboard(not_subscribed))
        return

    gifts = db.get_gifts()
    top_limit = db.get_gift_top_limit()
    end_date = db.get_contest_end_date()

    if not gifts:
        await message.answer(t(user_id, 'gifts_empty'), parse_mode="HTML")
        return

    text = f"🎁 <b>Sovgalar — Top {top_limit} gacha</b>\n\n"
    for place, gift_name, given in gifts:
        if place == 1: medal = "🥇"
        elif place == 2: medal = "🥈"
        elif place == 3: medal = "🥉"
        else: medal = "🏅"
        given_mark = " ✅ <i>Berildi</i>" if given else ""
        text += f"{medal} <b>Top {place}</b> — {gift_name}{given_mark}\n"

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
    await message.answer(
        t(user_id, 'main_menu'),
        reply_markup=main_reply_keyboard(user_id, user_id == ADMIN_ID)
    )


# ---- Bot statistikasi ----
@dp.message(F.text == "📊 Bot statistikasi")
async def bot_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = db.get_total_users()
    total_channels = len(db.get_channels())
    total_referrals = db.get_total_referrals()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"📢 Kanallar: <b>{total_channels}</b>\n"
        f"🔗 Faol referallar: <b>{total_referrals}</b>",
        parse_mode="HTML"
    )


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
        await state.update_data(channel_username=channel, channel_auto_name=chat.title)
        await message.answer(
            f"✅ Kanal topildi: <b>{chat.title}</b>\n\nEndi kanal <b>nomini</b> kiriting:",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.waiting_channel_name)
    except Exception:
        await message.answer("❌ Kanal topilmadi! Bot kanalga Admin bo'lishini tekshiring.", parse_mode="HTML")


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
        parse_mode="HTML",
        reply_markup=admin_reply_keyboard()
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
    await message.answer("➖ O'chiriladigan kanalni tanlang:",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


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
        entry = (f"👤 <b>{name}</b>\n   TG: {un}\n"
                 f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
                 f"   📱 Raqam: <code>{ph}</code>\n\n")
        if len(chunk) + len(entry) > 3500:
            await message.answer(text + chunk, parse_mode="HTML")
            chunk = entry
            text = ""
        else:
            chunk += entry
    if chunk:
        await message.answer((text + chunk).strip(), parse_mode="HTML")


# ---- Foydalanuvchi qidirish ----
@dp.message(F.text == "🔍 Foydalanuvchi qidirish")
async def search_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "🔍 <b>Foydalanuvchi qidirish</b>\n\n"
        "Username yoki PUBG ID ni yuboring:\n"
        "Misol: <code>@username</code> yoki <code>5123456789</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_search_query)


@dp.message(AdminStates.waiting_search_query)
async def search_user_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    query = message.text.strip()
    results = db.search_users(query)
    await state.clear()

    if not results:
        await message.answer(
            f"❌ <b>'{query}'</b> bo'yicha hech narsa topilmadi.",
            parse_mode="HTML",
            reply_markup=admin_reply_keyboard()
        )
        return

    text = f"🔍 <b>Natijalar ({len(results)} ta):</b>\n\n"
    for uid, name, uname, pubg_id, phone in results:
        ref_count = db.get_referral_count(uid)
        rank = db.get_user_rank(uid)
        un = f"@{uname}" if uname else "—"
        ph = phone if phone else "Yo'q"
        text += (
            f"👤 <b>{name}</b>\n"
            f"   🆔 ID: <code>{uid}</code>\n"
            f"   TG: {un}\n"
            f"   🎮 PUBG ID: <code>{pubg_id}</code>\n"
            f"   📱 Tel: <code>{ph}</code>\n"
            f"   👥 Referallar: <b>{ref_count}</b> | 🏆 #{rank}\n\n"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_reply_keyboard())


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
        await bot.send_message(user[0], "✅ Sizning baningiz olib tashlandi!")
    except Exception:
        pass


# ---- Foydalanuvchiga xabar ----
@dp.message(F.text == "📨 Foydalanuvchiga xabar")
async def msg_user_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📨 Xabar yuboriladigan foydalanuvchining <b>Telegram ID</b> sini yuboring:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_msg_user_id)


@dp.message(AdminStates.waiting_msg_user_id)
async def msg_user_id(message: types.Message, state: FSMContext):
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
        await message.answer(f"✅ Xabar {target_id} ga yuborildi!", reply_markup=admin_reply_keyboard())
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


# ===================== SOVGALAR (ADMIN) =====================

@dp.message(F.text == "🎁 Sovgalarni boshqarish")
async def gifts_admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    gifts = db.get_gifts()
    top_limit = db.get_gift_top_limit()
    end_date = db.get_contest_end_date()

    text = f"🎁 <b>Sovgalar boshqaruvi</b>\n\n"
    text += f"📌 Sovga beriladigan o'rinlar: <b>Top {top_limit}</b>\n"
    text += f"⏰ Tugash sanasi: <b>{end_date if end_date else 'Belgilanmagan'}</b>\n\n"

    if gifts:
        text += "🏆 <b>Joriy sovgalar:</b>\n"
        for place, gift_name, given in gifts:
            mark = " ✅" if given else ""
            text += f"  Top {place} — {gift_name}{mark}\n"
    else:
        text += "Hozircha sovgalar yo'q.\n"

    buttons = [
        [InlineKeyboardButton(text="➕ Sovga qo'shish / yangilash", callback_data="add_gift")],
        [InlineKeyboardButton(text="➖ Sovga o'chirish", callback_data="remove_gift")],
        [InlineKeyboardButton(text="✅ Sovrin berildi belgisi", callback_data="mark_gift_given")],
        [InlineKeyboardButton(text="🔢 Nechta o'ringa sovga (hozir: Top {})".format(top_limit), callback_data="set_top_limit")],
        [InlineKeyboardButton(text="📅 Konkurs tugash sanasini belgilash", callback_data="set_end_date")],
    ]
    await message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data == "add_gift")
async def add_gift_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text(
        "➕ <b>Sovga qo'shish</b>\n\nQaysi o'ringa sovga qo'shasiz?\nMisol: <code>1</code>",
        parse_mode="HTML"
    )
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
        await message.answer(f"✅ Top <b>{place}</b> uchun sovga nomi nima?\nMisol: <code>iPhone 16 Pro</code>",
                             parse_mode="HTML")
        await state.set_state(AdminStates.waiting_gift_name)
    except ValueError:
        await message.answer("❌ Musbat raqam kiriting!")


@dp.message(AdminStates.waiting_gift_name)
async def add_gift_name(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    place = data.get("gift_place")
    gift_name = message.text.strip()
    db.set_gift(place, gift_name)
    await state.clear()
    await message.answer(
        f"✅ <b>Top {place}</b> uchun sovga saqlandi:\n🎁 {gift_name}",
        parse_mode="HTML",
        reply_markup=admin_reply_keyboard()
    )


@dp.callback_query(F.data == "mark_gift_given")
async def mark_gift_given_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    gifts = db.get_gifts()
    if not gifts:
        await callback.answer("Sovgalar yo'q!", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton(
            text=f"{'✅' if given else '🎁'} Top {place} — {name}",
            callback_data=f"give_gift:{place}"
        )]
        for place, name, given in gifts
    ]
    await callback.message.edit_text(
        "✅ Sovrin berilgan o'rinni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(F.data.startswith("give_gift:"))
async def do_mark_gift_given(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    place = int(callback.data.split(":")[1])
    db.mark_gift_given(place)
    await callback.answer(f"✅ Top {place} sovgasi berildi deb belgilandi!", show_alert=True)
    await callback.message.delete()


@dp.callback_query(F.data == "remove_gift")
async def remove_gift_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    gifts = db.get_gifts()
    if not gifts:
        await callback.answer("Sovgalar yo'q!", show_alert=True)
        return
    buttons = [
        [InlineKeyboardButton(text=f"❌ Top {place} — {name}", callback_data=f"del_gift:{place}")]
        for place, name, given in gifts
    ]
    await callback.message.edit_text("➖ O'chiriladigan sovgani tanlang:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


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
    await callback.message.edit_text(
        "🔢 <b>Sovga beriladigan o'rinlar sonini kiriting</b>\nMisol: <code>10</code>",
        parse_mode="HTML"
    )
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
        await message.answer(f"✅ Sovga beriladigan o'rinlar: <b>Top {limit}</b>", parse_mode="HTML",
                             reply_markup=admin_reply_keyboard())
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
    date_text = message.text.strip()
    db.set_contest_end_date(date_text)
    await state.clear()
    await message.answer(f"✅ Konkurs tugash sanasi: <b>{date_text}</b>", parse_mode="HTML",
                         reply_markup=admin_reply_keyboard())


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
        "⚠️ <b>Diqqat!</b>\n\nKonkursni tugatishni tasdiqlaysizmi?\n\n"
        "🗑 Barcha referallar o'chiriladi\n🗑 Sovgalar tozalanadi\n"
        "✅ Foydalanuvchilar saqlanadi\n\n<b>Bu amalni qaytarib bo'lmaydi!</b>",
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
        "✅ <b>Konkurs muvaffaqiyatli tugatildi!</b>\n\n🗑 Barcha referallar tozalandi\n🔄 Foydalanuvchilar saqlanib qoldi",
        parse_mode="HTML"
    )
    success = 0
    for uid in user_ids:
        try:
            lang = db.get_user_language(uid)
            if lang == 'ru':
                msg = "🏁 <b>Конкурс завершён!</b>\n\nСкоро свяжемся с победителями. Участвуйте в следующем! 🎁"
            else:
                msg = "🏁 <b>Konkurs yakunlandi!</b>\n\nBarcha g'oliblar bilan tez orada bog'lanamiz. Yangi konkursda ham ishtirok eting! 🎁"
            await bot.send_message(uid, msg, parse_mode="HTML")
            success += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await bot.send_message(ADMIN_ID, f"📢 Konkurs tugashi haqida {success} ta foydalanuvchiga xabar yuborildi.")


@dp.callback_query(F.data == "cancel_end_contest")
async def cancel_end_contest(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.edit_text("❌ Bekor qilindi.")


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
                    t(referrer_id, 'ref_removed', name=target_user.full_name, count=new_count),
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
                    t(referrer_id, 'ref_returned', name=target_user.full_name, count=new_count),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Referer xabar xato: {e}")


# ===================== KUNLIK ESLATMA =====================

async def daily_reminder_task():
    """Har kuni soat 10:00 da eslatma yuborish"""
    while True:
        now = asyncio.get_event_loop().time()
        from datetime import datetime, timedelta
        dt = datetime.now()
        # Keyingi soat 10:00 gacha kutish
        next_run = dt.replace(hour=10, minute=0, second=0, microsecond=0)
        if dt >= next_run:
            next_run += timedelta(days=1)
        wait_seconds = (next_run - dt).total_seconds()
        await asyncio.sleep(wait_seconds)

        user_ids = db.get_all_user_ids()
        top_users = db.get_top_users(10)
        top_10_ids = {uid for uid, *_ in top_users}

        for uid in user_ids:
            if uid == ADMIN_ID:
                continue
            rank = db.get_user_rank(uid)
            if rank <= 10:
                continue  # Top 10 da bor, eslatma shart emas
            ref_count = db.get_referral_count(uid)
            # Top 10 ga kirish uchun nechta referal kerak
            if top_users and len(top_users) >= 10:
                top10_count = top_users[9][4]  # 10-o'rindagi ref soni
                need = max(0, top10_count - ref_count + 1)
            else:
                need = max(1, 10 - ref_count)

            try:
                await bot.send_message(
                    uid,
                    t(uid, 'daily_reminder', rank=rank, need=need),
                    parse_mode="HTML"
                )
            except Exception:
                pass
            await asyncio.sleep(0.05)


# ===================== MAIN =====================

async def main():
    logger.info("Bot v5 ishga tushdi!")
    asyncio.create_task(daily_reminder_task())
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    asyncio.run(main())
