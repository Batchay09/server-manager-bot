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
    get_back_keyboard
)
from utils import (
    format_server_info, format_server_list, format_expiring_servers,
    parse_date, parse_price
)

router = Router()


class AddServerStates(StatesGroup):
    name = State()
    hosting = State()
    expiry_date = State()
    price = State()
    currency = State()
    period = State()
    ip = State()
    url = State()
    notes = State()
    tags = State()


class EditServerStates(StatesGroup):
    waiting_value = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "<b>Добро пожаловать в Server Manager Bot!</b>\n\n"
        "Этот бот поможет вам:\n"
        "- Отслеживать сроки оплаты серверов\n"
        "- Получать напоминания об оплате\n"
        "- Мониторить доступность серверов\n"
        "- Вести статистику расходов\n\n"
        "Используйте меню ниже или команды:\n"
        "/add - добавить сервер\n"
        "/list - список серверов\n"
        "/expiring - истекающие серверы\n"
        "/stats - статистика\n"
        "/settings - настройки\n"
        "/help - справка"
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "<b>Справка по командам:</b>\n\n"
        "/start - главное меню\n"
        "/add - добавить новый сервер\n"
        "/list - список всех серверов\n"
        "/expiring - серверы с истекающей оплатой\n"
        "/stats - статистика расходов\n"
        "/settings - настройки напоминаний\n"
        "/help - эта справка\n\n"
        "<b>Как добавить сервер:</b>\n"
        "1. Введите /add или нажмите кнопку\n"
        "2. Следуйте инструкциям бота\n"
        "3. Обязательные поля: название, хостинг, дата, цена\n\n"
        "<b>Напоминания:</b>\n"
        "Бот автоматически напомнит об оплате за N дней\n"
        "(настраивается в /settings)"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_back_keyboard())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Главное меню:"
    await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    await callback.answer()


# === Добавление сервера ===

@router.message(Command("add"))
@router.callback_query(F.data == "add_server")
async def start_add_server(event: Message | CallbackQuery, state: FSMContext):
    await state.set_state(AddServerStates.name)
    text = "Введите <b>название</b> сервера:"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.message(AddServerStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddServerStates.hosting)
    await message.answer(
        "Введите название <b>хостинга</b> (например: Hetzner, DigitalOcean):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddServerStates.hosting)
async def process_hosting(message: Message, state: FSMContext):
    await state.update_data(hosting=message.text.strip())
    await state.set_state(AddServerStates.expiry_date)
    await message.answer(
        "Введите <b>дату окончания оплаты</b> (формат: ДД.ММ.ГГГГ):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddServerStates.expiry_date)
async def process_expiry_date(message: Message, state: FSMContext):
    date_obj = parse_date(message.text.strip())
    if not date_obj:
        await message.answer(
            "Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2024):",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(expiry_date=date_obj)
    await state.set_state(AddServerStates.price)
    await message.answer(
        "Введите <b>стоимость</b> (число):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddServerStates.price)
async def process_price(message: Message, state: FSMContext):
    price = parse_price(message.text.strip())
    if price is None:
        await message.answer(
            "Неверный формат. Введите число (например: 1500 или 29.99):",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(price=price)
    await state.set_state(AddServerStates.currency)
    await message.answer(
        "Выберите <b>валюту</b>:",
        reply_markup=get_currency_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(AddServerStates.currency, F.data.startswith("currency_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    await state.set_state(AddServerStates.period)
    await callback.message.edit_text(
        "Выберите <b>период оплаты</b>:",
        reply_markup=get_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AddServerStates.period, F.data.startswith("period_"))
async def process_period(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split("_")[1]
    await state.update_data(period=period)
    await state.set_state(AddServerStates.ip)
    await callback.message.edit_text(
        "Введите <b>IP адрес</b> сервера (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("ip"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.ip)
async def process_ip(message: Message, state: FSMContext):
    await state.update_data(ip=message.text.strip())
    await state.set_state(AddServerStates.url)
    await message.answer(
        "Введите <b>URL</b> для мониторинга (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("url"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_ip")
async def skip_ip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ip=None)
    await state.set_state(AddServerStates.url)
    await callback.message.edit_text(
        "Введите <b>URL</b> для мониторинга (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("url"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.url)
async def process_url(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip())
    await state.set_state(AddServerStates.notes)
    await message.answer(
        "Введите <b>заметки</b> (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("notes"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_url")
async def skip_url(callback: CallbackQuery, state: FSMContext):
    await state.update_data(url=None)
    await state.set_state(AddServerStates.notes)
    await callback.message.edit_text(
        "Введите <b>заметки</b> (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("notes"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddServerStates.notes)
async def process_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text.strip())
    await state.set_state(AddServerStates.tags)
    await message.answer(
        "Введите <b>теги</b> через запятую (или нажмите Пропустить):",
        reply_markup=get_skip_keyboard("tags"),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "skip_notes")
async def skip_notes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(notes=None)
    await state.set_state(AddServerStates.tags)
    await callback.message.edit_text(
        "Введите <b>теги</b> через запятую (или нажмите Пропустить):",
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
        ip=data.get('ip'),
        url=data.get('url'),
        notes=data.get('notes'),
        tags=data.get('tags')
    )

    await state.clear()

    server = await db.get_server(server_id, user_id)
    text = f"Сервер добавлен!\n\n{format_server_info(server, detailed=True)}"

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )
        await event.answer()
    else:
        await event.answer(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.", reply_markup=get_main_menu())
    await callback.answer()


# === Список серверов ===

@router.message(Command("list"))
async def cmd_list(message: Message):
    servers = await db.get_all_servers(message.from_user.id)
    text = format_server_list(servers)
    await message.answer(text, reply_markup=get_server_list_keyboard(servers), parse_mode="HTML")


@router.callback_query(F.data == "list_servers")
async def cb_list_servers(callback: CallbackQuery):
    servers = await db.get_all_servers(callback.from_user.id)
    text = format_server_list(servers)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_list_keyboard(servers),
        parse_mode="HTML"
    )
    await callback.answer()


# === Детали сервера ===

@router.callback_query(F.data.startswith("server_"))
async def cb_server_detail(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("Сервер не найден", show_alert=True)
        return

    text = format_server_info(server, detailed=True)
    await callback.message.edit_text(
        text,
        reply_markup=get_server_detail_keyboard(server),
        parse_mode="HTML"
    )
    await callback.answer()


# === Оплата ===

@router.callback_query(F.data.startswith("paid_"))
async def cb_mark_paid(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    new_date = await db.mark_paid(server_id, callback.from_user.id)

    if new_date:
        server = await db.get_server(server_id, callback.from_user.id)
        text = f"Оплата отмечена! Новая дата: {new_date.strftime('%d.%m.%Y')}\n\n"
        text += format_server_info(server, detailed=True)
        await callback.message.edit_text(
            text,
            reply_markup=get_server_detail_keyboard(server),
            parse_mode="HTML"
        )
        await callback.answer("Оплата отмечена!")
    else:
        await callback.answer("Ошибка", show_alert=True)


# === Удаление ===

@router.callback_query(F.data.startswith("delete_"))
async def cb_delete_server(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("Сервер не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"Вы уверены, что хотите удалить сервер <b>{server.name}</b>?",
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
            "Сервер удалён.",
            reply_markup=get_back_keyboard("list_servers")
        )
        await callback.answer("Удалено!")
    else:
        await callback.answer("Ошибка удаления", show_alert=True)


# === Редактирование ===

@router.callback_query(F.data.startswith("edit_") & ~F.data.startswith("edit_name_") &
                        ~F.data.startswith("edit_hosting_") & ~F.data.startswith("edit_ip_") &
                        ~F.data.startswith("edit_url_") & ~F.data.startswith("edit_expiry_") &
                        ~F.data.startswith("edit_price_") & ~F.data.startswith("edit_notes_") &
                        ~F.data.startswith("edit_tags_"))
async def cb_edit_server(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[1])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("Сервер не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"Редактирование <b>{server.name}</b>\nВыберите поле:",
        reply_markup=get_edit_server_keyboard(server_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"edit_(name|hosting|ip|url|expiry|price|notes|tags)_\d+"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field = parts[1]
    server_id = int(parts[2])

    field_names = {
        "name": "название",
        "hosting": "хостинг",
        "ip": "IP адрес",
        "url": "URL",
        "expiry": "дату оплаты (ДД.ММ.ГГГГ)",
        "price": "цену",
        "notes": "заметки",
        "tags": "теги"
    }

    await state.set_state(EditServerStates.waiting_value)
    await state.update_data(edit_field=field, edit_server_id=server_id)

    await callback.message.edit_text(
        f"Введите новое значение для поля <b>{field_names[field]}</b>:",
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
            await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ:")
            return
        update_data['expiry_date'] = date_obj
    elif field == "price":
        price = parse_price(value)
        if price is None:
            await message.answer("Неверный формат. Введите число:")
            return
        update_data['price'] = price
    else:
        update_data[field] = value

    success = await db.update_server(server_id, user_id, **update_data)

    if success:
        await state.clear()
        server = await db.get_server(server_id, user_id)
        text = f"Обновлено!\n\n{format_server_info(server, detailed=True)}"
        await message.answer(text, reply_markup=get_server_detail_keyboard(server), parse_mode="HTML")
    else:
        await message.answer("Ошибка обновления", reply_markup=get_cancel_keyboard())


# === Мониторинг ===

@router.callback_query(F.data.startswith("toggle_monitoring_"))
async def cb_toggle_monitoring(callback: CallbackQuery):
    server_id = int(callback.data.split("_")[2])
    server = await db.get_server(server_id, callback.from_user.id)

    if not server:
        await callback.answer("Сервер не найден", show_alert=True)
        return

    if not server.ip and not server.url:
        await callback.answer("Для мониторинга нужен IP или URL", show_alert=True)
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

    status = "включён" if new_value else "выключен"
    await callback.answer(f"Мониторинг {status}")


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
        f"<b>Настройки напоминаний</b>\n\n"
        f"Напоминать за: {settings.reminder_days} дней до окончания оплаты\n\n"
        f"Выберите новое значение:"
    )
    await message.answer(text, reply_markup=get_settings_keyboard(settings.reminder_days), parse_mode="HTML")


@router.callback_query(F.data == "settings")
async def cb_settings(callback: CallbackQuery):
    settings = await db.get_settings(callback.from_user.id)
    text = (
        f"<b>Настройки напоминаний</b>\n\n"
        f"Напоминать за: {settings.reminder_days} дней до окончания оплаты\n\n"
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
        f"<b>Настройки напоминаний</b>\n\n"
        f"Напоминать за: {days} дней до окончания оплаты\n\n"
        f"Выберите новое значение:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(days),
        parse_mode="HTML"
    )
    await callback.answer(f"Установлено: {days} дней")


@router.callback_query(F.data == "current_days")
async def cb_current_days(callback: CallbackQuery):
    await callback.answer()
