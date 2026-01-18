from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import (
    get_main_menu, get_server_list_keyboard, get_server_detail_keyboard,
    get_delete_confirm_keyboard, get_edit_server_keyboard, get_currency_keyboard,
    get_period_keyboard, get_cancel_keyboard, get_skip_keyboard, get_settings_keyboard,
    get_back_keyboard, get_hosting_choice_keyboard, get_location_choice_keyboard,
    get_price_choice_keyboard, get_server_list_keyboard_with_sort,
    get_payment_confirm_keyboard, get_payment_change_keyboard
)
from utils import (
    format_server_info, format_server_list_sorted, format_expiring_servers,
    parse_date, parse_price, get_period_text
)

router = Router()


class AddServerStates(StatesGroup):
    name = State()
    hosting_choice = State()  # Выбор из существующих хостингов
    hosting_new = State()     # Ввод нового хостинга
    location_choice = State() # Выбор из существующих локаций
    location_new = State()    # Ввод новой локации
    expiry_date = State()
    price_choice = State()    # Выбор из существующих цен
    price_new = State()       # Ввод новой цены
    currency = State()
    period = State()
    period_custom = State()   # Ввод своего периода в месяцах
    ip = State()
    url = State()
    notes = State()
    tags = State()


class EditServerStates(StatesGroup):
    waiting_value = State()


class PaymentStates(StatesGroup):
    waiting_price = State()
    waiting_currency = State()
    waiting_date = State()
    waiting_period_custom = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    # Получаем статистику для приветствия
    servers = await db.get_all_servers(message.from_user.id)
    servers_count = len(servers)

    if servers_count > 0:
        from datetime import date
        expiring = sum(1 for s in servers if (s.expiry_date - date.today()).days <= 7)
        expiring_text = f"\n⚠️ Требуют внимания: <b>{expiring}</b>" if expiring > 0 else ""
        stats_text = f"📊 Серверов: <b>{servers_count}</b>{expiring_text}"
    else:
        stats_text = "👋 Добавьте первый сервер"

    text = (
        f"🖥 <b>Server Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{stats_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Справка</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Команды:</b>\n"
        "├ /start — главное меню\n"
        "├ /add — добавить сервер\n"
        "├ /list — список серверов\n"
        "├ /expiring — срочные к оплате\n"
        "├ /stats — статистика\n"
        "├ /settings — настройки\n"
        "└ /help — эта справка\n\n"
        "<b>Как добавить сервер:</b>\n"
        "1️⃣ Нажмите «➕ Добавить»\n"
        "2️⃣ Введите данные пошагово\n"
        "3️⃣ Обязательно: название, хостинг, дата, цена\n\n"
        "<b>Напоминания:</b>\n"
        "🔔 Бот напомнит за N дней до оплаты\n"
        "⚙️ Настройте в разделе «Настройки»"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_keyboard())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    # Получаем статистику
    servers = await db.get_all_servers(callback.from_user.id)
    servers_count = len(servers)

    if servers_count > 0:
        from datetime import date
        expiring = sum(1 for s in servers if (s.expiry_date - date.today()).days <= 7)
        expiring_text = f"\n⚠️ Требуют внимания: <b>{expiring}</b>" if expiring > 0 else ""
        stats_text = f"📊 Серверов: <b>{servers_count}</b>{expiring_text}"
    else:
        stats_text = "👋 Добавьте первый сервер"

    text = (
        f"🖥 <b>Server Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{stats_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback.answer()


# === Добавление сервера ===

@router.message(Command("add"))
@router.callback_query(F.data == "add_server")
async def start_add_server(event: Message | CallbackQuery, state: FSMContext):
    await state.set_state(AddServerStates.name)
    text = "📝 Введите <b>название</b> сервера:"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.message(AddServerStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    user_id = message.from_user.id

    # Получаем существующие хостинги
    hostings = await db.get_unique_hostings(user_id)

    if hostings:
        await state.set_state(AddServerStates.hosting_choice)
        await message.answer(
            "🏢 Выберите <b>хостинг</b> или добавьте новый:",
            reply_markup=get_hosting_choice_keyboard(hostings),
            parse_mode="HTML"
        )
    else:
        await state.set_state(AddServerStates.hosting_new)
        await message.answer(
            "🏢 Введите название <b>хостинга</b>:\n"
            "<i>Например: Hetzner, DigitalOcean, Timeweb</i>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(AddServerStates.hosting_choice, F.data.startswith("select_hosting_"))
async def process_hosting_select(callback: CallbackQuery, state: FSMContext):
    hosting = callback.data.replace("select_hosting_", "")
    await state.update_data(hosting=hosting)
    await ask_location(callback, state)
    await callback.answer()


@router.callback_query(AddServerStates.hosting_choice, F.data == "new_hosting")
async def process_hosting_new_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddServerStates.hosting_new)
    await callback.message.edit_text(
        "🏢 Введите название <b>хостинга</b>:\n"
        "<i>Например: Hetzner, DigitalOcean, Timeweb</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.hosting_new)
async def process_hosting_input(message: Message, state: FSMContext):
    await state.update_data(hosting=message.text.strip())
    await ask_location(message, state)


async def ask_location(event: Message | CallbackQuery, state: FSMContext):
    """Запрашивает локацию."""
    user_id = event.from_user.id
    locations = await db.get_unique_locations(user_id)

    text = "📍 Выберите <b>локацию</b> сервера:"

    if locations:
        await state.set_state(AddServerStates.location_choice)
        keyboard = get_location_choice_keyboard(locations)
    else:
        # Если нет локаций, показываем только кнопки "Новая" и "Пропустить"
        await state.set_state(AddServerStates.location_choice)
        keyboard = get_location_choice_keyboard([])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(AddServerStates.location_choice, F.data.startswith("select_location_"))
async def process_location_select(callback: CallbackQuery, state: FSMContext):
    location = callback.data.replace("select_location_", "")
    await state.update_data(location=location)
    await ask_expiry_date(callback, state)
    await callback.answer()


@router.callback_query(AddServerStates.location_choice, F.data == "new_location")
async def process_location_new_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddServerStates.location_new)
    await callback.message.edit_text(
        "📍 Введите <b>локацию</b> сервера:\n"
        "<i>Например: Frankfurt, Amsterdam, Moscow</i>",
        reply_markup=get_skip_keyboard("location"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddServerStates.location_choice, F.data == "skip_location")
async def process_location_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(location=None)
    await ask_expiry_date(callback, state)
    await callback.answer()


@router.message(AddServerStates.location_new)
async def process_location_input(message: Message, state: FSMContext):
    await state.update_data(location=message.text.strip())
    await ask_expiry_date(message, state)


@router.callback_query(AddServerStates.location_new, F.data == "skip_location")
async def process_location_new_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(location=None)
    await ask_expiry_date(callback, state)
    await callback.answer()


async def ask_expiry_date(event: Message | CallbackQuery, state: FSMContext):
    """Запрашивает дату оплаты."""
    await state.set_state(AddServerStates.expiry_date)
    text = (
        "📅 Введите <b>дату окончания оплаты</b>:\n"
        "<i>Формат: ДД.ММ.ГГГГ (например: 25.12.2026)</i>"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.message(AddServerStates.expiry_date)
async def process_expiry_date(message: Message, state: FSMContext):
    date_obj = parse_date(message.text.strip())
    if not date_obj:
        await message.answer(
            "❌ Неверный формат даты\n\n"
            "Используйте: <b>ДД.ММ.ГГГГ</b>\n"
            "<i>Например: 25.12.2026</i>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(expiry_date=date_obj)
    await ask_price(message, state)


async def ask_price(event: Message | CallbackQuery, state: FSMContext):
    """Запрашивает цену."""
    user_id = event.from_user.id
    prices = await db.get_unique_prices(user_id)

    if prices:
        await state.set_state(AddServerStates.price_choice)
        text = "💰 Выберите <b>стоимость</b> или введите новую:"
        keyboard = get_price_choice_keyboard(prices)
    else:
        await state.set_state(AddServerStates.price_new)
        text = "💰 Введите <b>стоимость</b>:\n<i>Например: 1500 или 29.99</i>"
        keyboard = get_cancel_keyboard()

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(AddServerStates.price_choice, F.data.startswith("select_price_"))
async def process_price_select(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.replace("select_price_", "").rsplit("_", 1)
    price = float(parts[0])
    currency = parts[1]
    await state.update_data(price=price, currency=currency)
    await state.set_state(AddServerStates.period)
    await callback.message.edit_text(
        "📆 Выберите <b>период оплаты</b>:",
        reply_markup=get_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddServerStates.price_choice, F.data == "new_price")
async def process_price_new_choice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddServerStates.price_new)
    await callback.message.edit_text(
        "💰 Введите <b>стоимость</b>:\n"
        "<i>Например: 1500 или 29.99</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.price_new)
async def process_price_input(message: Message, state: FSMContext):
    price = parse_price(message.text.strip())
    if price is None:
        await message.answer(
            "❌ Неверный формат\n\n"
            "Введите число: <b>1500</b> или <b>29.99</b>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(price=price)
    await state.set_state(AddServerStates.currency)
    await message.answer(
        "💵 Выберите <b>валюту</b>:",
        reply_markup=get_currency_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(AddServerStates.currency, F.data.startswith("currency_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    await state.set_state(AddServerStates.period)
    await callback.message.edit_text(
        "📆 Выберите <b>период оплаты</b>:",
        reply_markup=get_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddServerStates.period, F.data.startswith("period_"))
async def process_period(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split("_")[1]

    if period == "custom":
        await state.set_state(AddServerStates.period_custom)
        await callback.message.edit_text(
            "📆 Введите <b>период оплаты</b> в месяцах:\n"
            "<i>Например: 2, 4, 9</i>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await state.update_data(period=period)
    await state.set_state(AddServerStates.ip)
    await callback.message.edit_text(
        "🌐 Введите <b>IP адрес</b> сервера:\n"
        "<i>Или нажмите «Пропустить»</i>",
        reply_markup=get_skip_keyboard("ip"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.period_custom)
async def process_period_custom(message: Message, state: FSMContext):
    try:
        months = int(message.text.strip())
        if months < 1 or months > 120:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите число от 1 до 120",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(period=f"custom_{months}")
    await state.set_state(AddServerStates.ip)
    await message.answer(
        "🌐 Введите <b>IP адрес</b> сервера:\n"
        "<i>Или нажмите «Пропустить»</i>",
        reply_markup=get_skip_keyboard("ip"),
        parse_mode="HTML"
    )


@router.message(AddServerStates.ip)
async def process_ip(message: Message, state: FSMContext):
    await state.update_data(ip=message.text.strip())
    await state.set_state(AddServerStates.url)
    await message.answer(
        "🔗 Введите <b>URL</b> для мониторинга:\n"
        "<i>Например: https://example.com</i>",
        reply_markup=get_skip_keyboard("url"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_ip")
async def skip_ip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ip=None)
    await state.set_state(AddServerStates.url)
    await callback.message.edit_text(
        "🔗 Введите <b>URL</b> для мониторинга:\n"
        "<i>Например: https://example.com</i>",
        reply_markup=get_skip_keyboard("url"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.url)
async def process_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await state.set_state(AddServerStates.notes)
    await message.answer(
        "📋 Введите <b>заметки</b>:\n"
        "<i>Любая полезная информация</i>",
        reply_markup=get_skip_keyboard("notes"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_url")
async def skip_url(callback: CallbackQuery, state: FSMContext):
    await state.update_data(url=None)
    await state.set_state(AddServerStates.notes)
    await callback.message.edit_text(
        "📋 Введите <b>заметки</b>:\n"
        "<i>Любая полезная информация</i>",
        reply_markup=get_skip_keyboard("notes"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.notes)
async def process_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text.strip())
    await state.set_state(AddServerStates.tags)
    await message.answer(
        "🏷 Введите <b>теги</b> через запятую:\n"
        "<i>Например: production, api, важный</i>",
        reply_markup=get_skip_keyboard("tags"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_notes")
async def skip_notes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(notes=None)
    await state.set_state(AddServerStates.tags)
    await callback.message.edit_text(
        "🏷 Введите <b>теги</b> через запятую:\n"
        "<i>Например: production, api, важный</i>",
        reply_markup=get_skip_keyboard("tags"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.tags)
async def process_tags(message: Message, state: FSMContext):
    await state.update_data(tags=message.text.strip())
    await finish_add_server(message, state)


@router.callback_query(F.data == "skip_tags")
async def skip_tags(callback: CallbackQuery, state: FSMContext):
    await state.update_data(tags=None)
    await finish_add_server(callback, state)


async def finish_add_server(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = event.from_user.id

    server_id = await db.add_server(
        user_id=user_id,
        name=data['name'],
        hosting=data['hosting'],
        expiry_date=data['expiry_date'],
        price=data['price'],
        currency=data['currency'],
        payment_period=data['period'],
        location=data.get('location'),
        ip=data.get('ip'),
        url=data.get('url'),
        notes=data.get('notes'),
        tags=data.get('tags')
    )

    await state.clear()

    server = await db.get_server(server_id, user_id)
    text = f"✅ <b>Сервер добавлен!</b>\n\n{format_server_info(server, detailed=True)}"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )
        await event.answer("Готово!")
    else:
        await event.answer(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Действие отменено</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# === Список серверов ===

@router.message(Command("list"))
async def cmd_list(message: Message, state: FSMContext):
    servers = await db.get_all_servers(message.from_user.id)
    data = await state.get_data()
    current_sort = data.get('sort', 'date')
    text = format_server_list_sorted(servers, current_sort)
    await message.answer(text, reply_markup=get_server_list_keyboard_with_sort(servers, current_sort), parse_mode="HTML")


@router.callback_query(F.data == "list_servers")
async def cb_list_servers(callback: CallbackQuery, state: FSMContext):
    servers = await db.get_all_servers(callback.from_user.id)
    data = await state.get_data()
    current_sort = data.get('sort', 'date')
    text = format_server_list_sorted(servers, current_sort)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_list_keyboard_with_sort(servers, current_sort),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sort_"))
async def cb_sort_servers(callback: CallbackQuery, state: FSMContext):
    sort_type = callback.data.replace("sort_", "")
    await state.update_data(sort=sort_type)

    servers = await db.get_all_servers(callback.from_user.id)
    text = format_server_list_sorted(servers, sort_type)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_list_keyboard_with_sort(servers, sort_type),
        parse_mode="HTML"
    )
    await callback.answer(f"Сортировка: {sort_type}")


# === Детали сервера ===

@router.callback_query(F.data.startswith("server_"))
async def cb_server_detail(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    text = format_server_info(server, detailed=True)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )
    await callback.answer()


# === Оплата ===

@router.callback_query(F.data.regexp(r"^paid_\d+$"))
async def cb_mark_paid(callback: CallbackQuery):
    """Показывает диалог подтверждения оплаты."""
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    period_text = get_period_text(server.payment_period)
    text = (
        f"💳 <b>Подтверждение оплаты</b>\n\n"
        f"🖥 {server.name}\n"
        f"💰 {server.price:.2f} {server.currency}/{period_text}\n\n"
        f"Условия остались прежними?"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_confirm_keyboard(server_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_same_"))
async def cb_pay_same(callback: CallbackQuery):
    """Оплата с теми же условиями."""
    server_id = int(callback.data.split("_")[2])
    new_date = await db.mark_paid(server_id, callback.from_user.id)

    if new_date:
        server = await db.get_server(server_id, callback.from_user.id)
        text = f"✅ <b>Оплата отмечена!</b>\n\n"
        text += f"📅 Следующая оплата: <b>{new_date.strftime('%d.%m.%Y')}</b>\n\n"
        text += format_server_info(server, detailed=True)
        await callback.message.edit_text(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )
        await callback.answer("✅ Оплата отмечена!")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("pay_changed_"))
async def cb_pay_changed(callback: CallbackQuery):
    """Показывает меню изменения условий оплаты."""
    server_id = int(callback.data.split("_")[2])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    text = (
        f"✏️ <b>Что изменилось?</b>\n\n"
        f"🖥 {server.name}\n\n"
        f"Выберите что обновить:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_change_keyboard(server_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_edit_price_"))
async def cb_pay_edit_price(callback: CallbackQuery, state: FSMContext):
    """Запрос новой цены при оплате."""
    server_id = int(callback.data.split("_")[3])
    await state.set_state(PaymentStates.waiting_price)
    await state.update_data(pay_server_id=server_id)

    await callback.message.edit_text(
        "💰 Введите <b>новую стоимость</b>:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentStates.waiting_price)
async def process_pay_price(message: Message, state: FSMContext):
    """Обработка новой цены."""
    price = parse_price(message.text.strip())
    if price is None:
        await message.answer(
            "❌ Неверный формат\n\nВведите число: <b>1500</b> или <b>29.99</b>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(pay_new_price=price)
    await state.set_state(PaymentStates.waiting_currency)
    await message.answer(
        "💵 Выберите <b>валюту</b>:",
        reply_markup=get_currency_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(PaymentStates.waiting_currency, F.data.startswith("currency_"))
async def process_pay_currency(callback: CallbackQuery, state: FSMContext):
    """Обработка валюты и завершение оплаты с новой ценой."""
    currency = callback.data.split("_")[1]
    data = await state.get_data()
    server_id = data['pay_server_id']
    new_price = data['pay_new_price']

    # Обновляем цену и отмечаем оплату
    await db.update_server(server_id, callback.from_user.id, price=new_price, currency=currency)
    new_date = await db.mark_paid(server_id, callback.from_user.id)

    await state.clear()

    server = await db.get_server(server_id, callback.from_user.id)
    text = f"✅ <b>Оплата отмечена!</b>\n\n"
    text += f"💰 Новая цена: <b>{new_price:.2f} {currency}</b>\n"
    text += f"📅 Следующая оплата: <b>{new_date.strftime('%d.%m.%Y')}</b>\n\n"
    text += format_server_info(server, detailed=True)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )
    await callback.answer("✅ Оплата отмечена!")


@router.callback_query(F.data.startswith("pay_edit_period_"))
async def cb_pay_edit_period(callback: CallbackQuery, state: FSMContext):
    """Выбор нового периода оплаты."""
    server_id = int(callback.data.split("_")[3])
    await state.update_data(pay_server_id=server_id)

    await callback.message.edit_text(
        "📆 Выберите <b>новый период оплаты</b>:",
        reply_markup=get_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("period_") & ~StateFilter(AddServerStates.period))
async def process_pay_period(callback: CallbackQuery, state: FSMContext):
    """Обработка периода и завершение оплаты."""
    data = await state.get_data()
    server_id = data.get('pay_server_id')

    if not server_id:
        await callback.answer()
        return

    period = callback.data.split("_")[1]

    # Если выбран кастомный период — запрашиваем количество месяцев
    if period == "custom":
        await state.set_state(PaymentStates.waiting_period_custom)
        await callback.message.edit_text(
            "📆 Введите <b>период оплаты</b> в месяцах:\n"
            "<i>Например: 2, 4, 9</i>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Обновляем период и отмечаем оплату
    await db.update_server(server_id, callback.from_user.id, payment_period=period)
    new_date = await db.mark_paid(server_id, callback.from_user.id)

    await state.clear()

    server = await db.get_server(server_id, callback.from_user.id)
    period_text_full = get_period_text(period)
    text = f"✅ <b>Оплата отмечена!</b>\n\n"
    text += f"📆 Новый период: <b>{period_text_full}</b>\n"
    text += f"📅 Следующая оплата: <b>{new_date.strftime('%d.%m.%Y')}</b>\n\n"
    text += format_server_info(server, detailed=True)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )
    await callback.answer("✅ Оплата отмечена!")


@router.message(PaymentStates.waiting_period_custom)
async def process_pay_period_custom(message: Message, state: FSMContext):
    """Обработка кастомного периода при оплате."""
    try:
        months = int(message.text.strip())
        if months < 1 or months > 120:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Введите число от 1 до 120",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    server_id = data['pay_server_id']
    period = f"custom_{months}"

    # Обновляем период и отмечаем оплату
    await db.update_server(server_id, message.from_user.id, payment_period=period)
    new_date = await db.mark_paid(server_id, message.from_user.id)

    await state.clear()

    server = await db.get_server(server_id, message.from_user.id)
    text = f"✅ <b>Оплата отмечена!</b>\n\n"
    text += f"📆 Новый период: <b>{months} мес</b>\n"
    text += f"📅 Следующая оплата: <b>{new_date.strftime('%d.%m.%Y')}</b>\n\n"
    text += format_server_info(server, detailed=True)
    await message.answer(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_edit_date_"))
async def cb_pay_edit_date(callback: CallbackQuery, state: FSMContext):
    """Запрос новой даты оплаты."""
    server_id = int(callback.data.split("_")[3])
    await state.set_state(PaymentStates.waiting_date)
    await state.update_data(pay_server_id=server_id)

    await callback.message.edit_text(
        "📅 Введите <b>дату следующей оплаты</b>:\n"
        "<i>Формат: ДД.ММ.ГГГГ</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentStates.waiting_date)
async def process_pay_date(message: Message, state: FSMContext):
    """Обработка новой даты оплаты."""
    date_obj = parse_date(message.text.strip())
    if not date_obj:
        await message.answer(
            "❌ Неверный формат даты\n\nИспользуйте: <b>ДД.ММ.ГГГГ</b>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    server_id = data['pay_server_id']

    # Обновляем дату напрямую
    await db.update_server(server_id, message.from_user.id, expiry_date=date_obj)

    await state.clear()

    server = await db.get_server(server_id, message.from_user.id)
    text = f"✅ <b>Оплата отмечена!</b>\n\n"
    text += f"📅 Следующая оплата: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n\n"
    text += format_server_info(server, detailed=True)
    await message.answer(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )


# === Удаление ===

@router.callback_query(F.data.startswith("delete_"))
async def cb_delete_server(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"🗑 <b>Удалить сервер?</b>\n\n"
        f"Вы уверены, что хотите удалить\n"
        f"<b>{server.name}</b>?",
        reply_markup=get_delete_confirm_keyboard(server_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def cb_confirm_delete(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[2])
    success = await db.delete_server(server_id, callback.from_user.id)

    if success:
        await callback.message.edit_text(
            "🗑 <b>Сервер удалён</b>",
            reply_markup=get_back_keyboard("list_servers"),
            parse_mode="HTML"
        )
        await callback.answer("Удалено!")
    else:
        await callback.answer("❌ Ошибка удаления", show_alert=True)


# === Редактирование ===

@router.callback_query(F.data.regexp(r"^edit_\d+$"))
async def cb_edit_server(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"✏️ <b>Редактирование</b>\n\n"
        f"Сервер: <b>{server.name}</b>\n\n"
        f"Выберите поле:",
        reply_markup=get_edit_server_keyboard(server_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"edit_(name|hosting|location|ip|url|expiry|price|notes|tags)_\d+"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field = parts[1]
    server_id = int(parts[2])

    field_names = {
        "name": ("📝", "название"),
        "hosting": ("🏢", "хостинг"),
        "location": ("📍", "локацию"),
        "ip": ("🌐", "IP адрес"),
        "url": ("🔗", "URL"),
        "expiry": ("📅", "дату оплаты (ДД.ММ.ГГГГ)"),
        "price": ("💰", "цену"),
        "notes": ("📋", "заметки"),
        "tags": ("🏷", "теги")
    }

    emoji, name = field_names[field]
    await state.set_state(EditServerStates.waiting_value)
    await state.update_data(edit_field=field, edit_server_id=server_id)

    await callback.message.edit_text(
        f"{emoji} Введите новое значение для поля\n<b>{name}</b>:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditServerStates.waiting_value)
async def process_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data['edit_field']
    server_id = data['edit_server_id']
    user_id = message.from_user.id
    value = message.text.strip()

    # Валидация и преобразование
    update_data = {}

    if field == "expiry":
        date_obj = parse_date(value)
        if not date_obj:
            await message.answer(
                "❌ Неверный формат даты\n\n"
                "Используйте: <b>ДД.ММ.ГГГГ</b>",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
            return
        update_data['expiry_date'] = date_obj
    elif field == "price":
        price = parse_price(value)
        if price is None:
            await message.answer(
                "❌ Неверный формат\n\n"
                "Введите число",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
            return
        update_data['price'] = price
    else:
        update_data[field] = value

    success = await db.update_server(server_id, user_id, **update_data)

    if success:
        await state.clear()
        server = await db.get_server(server_id, user_id)
        text = f"✅ <b>Обновлено!</b>\n\n{format_server_info(server, detailed=True)}"
        await message.answer(text, reply_markup=get_server_detail_keyboard(server), parse_mode="HTML")
    else:
        await message.answer(
            "❌ Ошибка обновления",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )


# === Мониторинг ===

@router.callback_query(F.data.startswith("toggle_monitoring_"))
async def cb_toggle_monitoring(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[2])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("❌ Сервер не найден", show_alert=True)
        return

    if not server.ip and not server.url:
        await callback.answer("⚠️ Для мониторинга нужен IP или URL", show_alert=True)
        return

    new_value = not server.is_monitoring
    await db.update_server(server_id, callback.from_user.id, is_monitoring=new_value)

    server = await db.get_server(server_id, callback.from_user.id)
    text = format_server_info(server, detailed=True)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )

    status = "🟢 включён" if new_value else "⚫ выключен"
    await callback.answer(f"📡 Мониторинг {status}")


# === Истекающие серверы ===

@router.message(Command("expiring"))
async def cmd_expiring(message: Message):
    servers = await db.get_expiring_servers(message.from_user.id, days=30)
    text = format_expiring_servers(servers)
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "expiring_servers")
async def cb_expiring_servers(callback: CallbackQuery):
    servers = await db.get_expiring_servers(callback.from_user.id, days=30)
    text = format_expiring_servers(servers)
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


# === Настройки ===

@router.message(Command("settings"))
async def cmd_settings(message: Message):
    settings = await db.get_settings(message.from_user.id)
    text = (
        f"⚙️ <b>Настройки</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔔 Напоминать за <b>{settings.reminder_days}</b> дней\n"
        f"до окончания оплаты\n\n"
        f"Выберите новое значение:"
    )
    await message.answer(text, reply_markup=get_settings_keyboard(settings.reminder_days), parse_mode="HTML")


@router.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    settings = await db.get_settings(callback.from_user.id)
    text = (
        f"⚙️ <b>Настройки</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔔 Напоминать за <b>{settings.reminder_days}</b> дней\n"
        f"до окончания оплаты\n\n"
        f"Выберите новое значение:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(settings.reminder_days),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_days_"))
async def cb_set_reminder_days(callback: CallbackQuery):
    days = int(callback.data.split("_")[2])
    await db.update_settings(callback.from_user.id, reminder_days=days)

    text = (
        f"⚙️ <b>Настройки</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔔 Напоминать за <b>{days}</b> дней\n"
        f"до окончания оплаты\n\n"
        f"Выберите новое значение:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(days),
        parse_mode="HTML"
    )
    await callback.answer(f"✅ Установлено: {days} дней")


@router.callback_query(F.data == "current_days")
async def cb_current_days(callback: CallbackQuery):
    await callback.answer()
