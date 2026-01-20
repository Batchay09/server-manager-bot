"""
Хэндлеры для работы с API хостингов.
Синхронизация, импорт серверов.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from keyboards import get_cancel_keyboard, get_back_keyboard
from services.hosting_api import FourVPSClient, get_hosting_client
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


class HostingStates(StatesGroup):
    waiting_api_key = State()


# === Клавиатуры ===

def get_hosting_menu_keyboard(has_api_key: bool = False) -> InlineKeyboardMarkup:
    """Меню интеграции с хостингами."""
    builder = InlineKeyboardBuilder()

    if has_api_key:
        builder.row(
            InlineKeyboardButton(text="🔄 Синхронизация", callback_data="hosting_sync")
        )
        builder.row(
            InlineKeyboardButton(text="📥 Импорт серверов", callback_data="hosting_import")
        )
        builder.row(
            InlineKeyboardButton(text="🔑 Изменить API ключ", callback_data="hosting_set_key"),
            InlineKeyboardButton(text="🗑 Удалить ключ", callback_data="hosting_delete_key")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="🔑 Подключить 4VPS", callback_data="hosting_set_key")
        )

    builder.row(
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_import_keyboard(servers: list, imported_ids: set) -> InlineKeyboardMarkup:
    """Клавиатура выбора серверов для импорта."""
    builder = InlineKeyboardBuilder()

    for server in servers:
        status = "✅" if server.external_id in imported_ids else "⬜"
        text = f"{status} {server.name}"
        if server.ip:
            text += f" ({server.ip})"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"import_toggle_{server.external_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="📥 Импортировать выбранные", callback_data="import_selected")
    )
    builder.row(
        InlineKeyboardButton(text="📥 Импортировать все", callback_data="import_all")
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="hosting_menu")
    )
    return builder.as_markup()


# === Команды ===

@router.message(Command("hosting"))
async def cmd_hosting(message: Message):
    """Меню интеграции с хостингами."""
    api_key = await db.get_api_key(message.from_user.id, "4vps")
    has_key = api_key is not None

    if has_key:
        text = (
            "🔗 <b>Интеграция с хостингами</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ <b>4VPS</b> — подключён\n\n"
            "Выберите действие:"
        )
    else:
        text = (
            "🔗 <b>Интеграция с хостингами</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Подключите API хостинга для:\n"
            "• Автоматического импорта серверов\n"
            "• Синхронизации дат оплаты\n"
            "• Актуальных цен\n\n"
            "🔑 Поддерживается: <b>4VPS</b>"
        )

    await message.answer(text, reply_markup=get_hosting_menu_keyboard(has_key), parse_mode="HTML")


@router.callback_query(F.data == "hosting_menu")
async def cb_hosting_menu(callback: CallbackQuery, state: FSMContext):
    """Меню интеграции с хостингами."""
    await state.clear()
    api_key = await db.get_api_key(callback.from_user.id, "4vps")
    has_key = api_key is not None

    if has_key:
        text = (
            "🔗 <b>Интеграция с хостингами</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ <b>4VPS</b> — подключён\n\n"
            "Выберите действие:"
        )
    else:
        text = (
            "🔗 <b>Интеграция с хостингами</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Подключите API хостинга для:\n"
            "• Автоматического импорта серверов\n"
            "• Синхронизации дат оплаты\n"
            "• Актуальных цен\n\n"
            "🔑 Поддерживается: <b>4VPS</b>"
        )

    await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(has_key), parse_mode="HTML")
    await callback.answer()


# === Настройка API ключа ===

@router.callback_query(F.data == "hosting_set_key")
async def cb_set_api_key(callback: CallbackQuery, state: FSMContext):
    """Запрос API ключа."""
    await state.set_state(HostingStates.waiting_api_key)

    text = (
        "🔑 <b>Подключение 4VPS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Введите ваш API ключ от 4VPS:\n\n"
        "<i>Получить ключ можно в личном кабинете:\n"
        "4vps.su → Настройки → API</i>"
    )

    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(HostingStates.waiting_api_key)
async def process_api_key(message: Message, state: FSMContext):
    """Обработка введённого API ключа."""
    api_key = message.text.strip()

    # Удаляем сообщение с ключом для безопасности
    try:
        await message.delete()
    except Exception:
        pass

    # Проверяем ключ
    status_msg = await message.answer("🔄 Проверяю ключ...", parse_mode="HTML")

    client = FourVPSClient(api_key)
    is_valid = await client.test_connection()

    if is_valid:
        # Сохраняем ключ
        await db.save_api_key(message.from_user.id, "4vps", api_key)
        await state.clear()

        # Получаем количество серверов
        servers = await client.get_servers()
        count = len(servers) if servers else 0

        text = (
            "✅ <b>API ключ сохранён!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🖥 Найдено серверов: <b>{count}</b>\n\n"
            "Теперь вы можете импортировать\n"
            "серверы автоматически."
        )
        await status_msg.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")
    else:
        text = (
            "❌ <b>Неверный API ключ</b>\n\n"
            "Проверьте ключ и попробуйте снова.\n\n"
            "<i>Получить ключ: 4vps.su → Настройки → API</i>"
        )
        await status_msg.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "hosting_delete_key")
async def cb_delete_api_key(callback: CallbackQuery):
    """Удаление API ключа."""
    await db.delete_api_key(callback.from_user.id, "4vps")

    text = (
        "🗑 <b>API ключ удалён</b>\n\n"
        "Интеграция с 4VPS отключена."
    )
    await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(False), parse_mode="HTML")
    await callback.answer("Ключ удалён")


# === Синхронизация ===

@router.callback_query(F.data == "hosting_sync")
async def cb_sync_servers(callback: CallbackQuery):
    """Синхронизация серверов с хостингом."""
    api_key = await db.get_api_key(callback.from_user.id, "4vps")
    if not api_key:
        await callback.answer("❌ API ключ не настроен", show_alert=True)
        return

    await callback.answer("🔄 Синхронизация...")

    client = FourVPSClient(api_key)
    servers = await client.get_servers()

    if servers is None:
        text = "❌ <b>Ошибка подключения</b>\n\nПроверьте API ключ."
        await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")
        return

    if not servers:
        text = "📭 <b>Серверов не найдено</b>\n\nНа вашем аккаунте 4VPS нет серверов."
        await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")
        return

    # Обновляем существующие серверы
    updated = 0
    for server in servers:
        existing = await db.get_server_by_external_id(callback.from_user.id, "4vps", server.external_id)
        if existing:
            await db.update_server(
                existing.id,
                callback.from_user.id,
                expiry_date=server.expiry_date,
                price=server.price,
                ip=server.ip,
                location=server.location
            )
            updated += 1

    text = (
        f"✅ <b>Синхронизация завершена</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔄 Обновлено: <b>{updated}</b> серверов\n"
        f"🖥 Всего на 4VPS: <b>{len(servers)}</b>\n\n"
        f"<i>Обновлены даты, цены и IP адреса</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")


# === Импорт серверов ===

@router.callback_query(F.data == "hosting_import")
async def cb_import_servers(callback: CallbackQuery, state: FSMContext):
    """Показать список серверов для импорта."""
    api_key = await db.get_api_key(callback.from_user.id, "4vps")
    if not api_key:
        await callback.answer("❌ API ключ не настроен", show_alert=True)
        return

    await callback.answer("🔄 Загрузка...")

    client = FourVPSClient(api_key)
    servers = await client.get_servers()

    if servers is None:
        text = "❌ <b>Ошибка подключения</b>\n\nПроверьте API ключ."
        await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")
        return

    if not servers:
        text = "📭 <b>Серверов не найдено</b>\n\nНа вашем аккаунте 4VPS нет серверов."
        await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")
        return

    # Сохраняем серверы в состояние
    await state.update_data(
        hosting_servers=[{
            'external_id': s.external_id,
            'name': s.name,
            'ip': s.ip,
            'price': s.price,
            'currency': s.currency,
            'expiry_date': s.expiry_date.isoformat(),
            'location': s.location
        } for s in servers],
        selected_ids=set()
    )

    # Проверяем какие уже импортированы
    imported_ids = set()
    for server in servers:
        existing = await db.get_server_by_external_id(callback.from_user.id, "4vps", server.external_id)
        if existing:
            imported_ids.add(server.external_id)

    text = (
        f"📥 <b>Импорт серверов</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Найдено серверов: <b>{len(servers)}</b>\n"
        f"Уже импортировано: <b>{len(imported_ids)}</b>\n\n"
        f"✅ — уже в боте"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_import_keyboard(servers, imported_ids),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "import_all")
async def cb_import_all(callback: CallbackQuery, state: FSMContext):
    """Импортировать все серверы."""
    data = await state.get_data()
    servers_data = data.get('hosting_servers', [])

    if not servers_data:
        await callback.answer("❌ Нет серверов для импорта", show_alert=True)
        return

    await callback.answer("📥 Импортирую...")

    imported = 0
    updated = 0

    for s in servers_data:
        from datetime import date
        expiry = date.fromisoformat(s['expiry_date'])

        existing = await db.get_server_by_external_id(callback.from_user.id, "4vps", s['external_id'])
        if existing:
            await db.update_server(
                existing.id,
                callback.from_user.id,
                expiry_date=expiry,
                price=s['price'],
                ip=s['ip'],
                location=s['location']
            )
            updated += 1
        else:
            await db.add_or_update_server_from_hosting(
                user_id=callback.from_user.id,
                provider="4vps",
                external_id=s['external_id'],
                name=s['name'],
                expiry_date=expiry,
                price=s['price'],
                currency=s['currency'],
                ip=s['ip'],
                location=s['location']
            )
            imported += 1

    await state.clear()

    text = (
        f"✅ <b>Импорт завершён!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📥 Импортировано: <b>{imported}</b>\n"
        f"🔄 Обновлено: <b>{updated}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(True), parse_mode="HTML")


@router.callback_query(F.data == "cancel")
async def cb_cancel_hosting(callback: CallbackQuery, state: FSMContext):
    """Отмена действия в контексте хостинга."""
    current_state = await state.get_state()
    if current_state == HostingStates.waiting_api_key:
        await state.clear()
        api_key = await db.get_api_key(callback.from_user.id, "4vps")
        has_key = api_key is not None
        text = "❌ <b>Действие отменено</b>"
        await callback.message.edit_text(text, reply_markup=get_hosting_menu_keyboard(has_key), parse_mode="HTML")
        await callback.answer()
