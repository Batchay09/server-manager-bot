from datetime import date
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Server


def get_status_emoji(days_left: int) -> str:
    """Возвращает цветной эмодзи статуса."""
    if days_left < 0:
        return "🔴"
    elif days_left <= 3:
        return "🔴"
    elif days_left <= 7:
        return "🟠"
    elif days_left <= 14:
        return "🟡"
    else:
        return "🟢"


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_server"),
        InlineKeyboardButton(text="📋 Серверы", callback_data="list_servers")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Срочные", callback_data="expiring_servers"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
    )
    return builder.as_markup()


def get_server_list_keyboard(servers: list[Server]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Сортируем по дням до оплаты
    sorted_servers = sorted(servers, key=lambda s: (s.expiry_date - date.today()).days)

    for server in sorted_servers:
        days_left = (server.expiry_date - date.today()).days
        status = get_status_emoji(days_left)

        if days_left < 0:
            days_text = "!"
        elif days_left == 0:
            days_text = "сегодня"
        elif days_left == 1:
            days_text = "завтра"
        else:
            days_text = f"{days_left}д"

        builder.row(
            InlineKeyboardButton(
                text=f"{status} {server.name} • {days_text}",
                callback_data=f"server_{server.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_server"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_server_detail_keyboard(server: Server) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Оплачено", callback_data=f"paid_{server.id}"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_{server.id}")
    )

    monitoring_text = "📡 Выкл. мониторинг" if server.is_monitoring else "📡 Вкл. мониторинг"
    builder.row(
        InlineKeyboardButton(text=monitoring_text, callback_data=f"toggle_monitoring_{server.id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{server.id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К списку", callback_data="list_servers")
    )
    return builder.as_markup()


def get_delete_confirm_keyboard(server_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"confirm_delete_{server_id}"),
        InlineKeyboardButton(text="↩️ Отмена", callback_data=f"server_{server_id}")
    )
    return builder.as_markup()


def get_edit_server_keyboard(server_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Название", callback_data=f"edit_name_{server_id}"),
        InlineKeyboardButton(text="🏢 Хостинг", callback_data=f"edit_hosting_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📍 Локация", callback_data=f"edit_location_{server_id}"),
        InlineKeyboardButton(text="🌐 IP", callback_data=f"edit_ip_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔗 URL", callback_data=f"edit_url_{server_id}"),
        InlineKeyboardButton(text="📅 Дата", callback_data=f"edit_expiry_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{server_id}"),
        InlineKeyboardButton(text="📋 Заметки", callback_data=f"edit_notes_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🏷 Теги", callback_data=f"edit_tags_{server_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"server_{server_id}")
    )
    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 RUB", callback_data="currency_RUB"),
        InlineKeyboardButton(text="🇺🇸 USD", callback_data="currency_USD"),
        InlineKeyboardButton(text="🇪🇺 EUR", callback_data="currency_EUR")
    )
    return builder.as_markup()


def get_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Ежемесячно", callback_data="period_monthly"),
        InlineKeyboardButton(text="📆 Ежегодно", callback_data="period_yearly")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_skip_keyboard(field: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"skip_{field}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_settings_keyboard(reminder_days: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"🔔 Сейчас: {reminder_days} дней", callback_data="current_days")
    )
    builder.row(
        InlineKeyboardButton(text="3️⃣", callback_data="set_days_3"),
        InlineKeyboardButton(text="5️⃣", callback_data="set_days_5"),
        InlineKeyboardButton(text="7️⃣", callback_data="set_days_7")
    )
    builder.row(
        InlineKeyboardButton(text="🔟", callback_data="set_days_10"),
        InlineKeyboardButton(text="1️⃣4️⃣", callback_data="set_days_14")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_back_keyboard(callback: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if callback == "main_menu":
        builder.row(
            InlineKeyboardButton(text="🏠 Меню", callback_data=callback)
        )
    else:
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data=callback)
        )
    return builder.as_markup()


def get_hosting_choice_keyboard(hostings: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора хостинга из существующих + новый."""
    builder = InlineKeyboardBuilder()
    for hosting in hostings[:8]:  # Максимум 8 кнопок
        builder.row(
            InlineKeyboardButton(text=f"🏢 {hosting}", callback_data=f"select_hosting_{hosting}")
        )
    builder.row(
        InlineKeyboardButton(text="➕ Новый хостинг", callback_data="new_hosting")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_location_choice_keyboard(locations: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора локации из существующих + новая + пропустить."""
    builder = InlineKeyboardBuilder()
    for location in locations[:8]:  # Максимум 8 кнопок
        builder.row(
            InlineKeyboardButton(text=f"📍 {location}", callback_data=f"select_location_{location}")
        )
    builder.row(
        InlineKeyboardButton(text="➕ Новая", callback_data="new_location"),
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_location")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_price_choice_keyboard(prices: list[tuple[float, str]]) -> InlineKeyboardMarkup:
    """Клавиатура выбора цены из существующих + новая."""
    builder = InlineKeyboardBuilder()
    for price, currency in prices[:6]:  # Максимум 6 кнопок
        builder.row(
            InlineKeyboardButton(
                text=f"💰 {price:.2f} {currency}",
                callback_data=f"select_price_{price}_{currency}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Новая цена", callback_data="new_price")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_sort_keyboard(current_sort: str = "date") -> InlineKeyboardMarkup:
    """Клавиатура сортировки списка серверов."""
    builder = InlineKeyboardBuilder()

    date_mark = "✓ " if current_sort == "date" else ""
    hosting_mark = "✓ " if current_sort == "hosting" else ""
    location_mark = "✓ " if current_sort == "location" else ""

    builder.row(
        InlineKeyboardButton(text=f"{date_mark}📅 Дата", callback_data="sort_date"),
        InlineKeyboardButton(text=f"{hosting_mark}🏢 Хостинг", callback_data="sort_hosting"),
        InlineKeyboardButton(text=f"{location_mark}📍 Локация", callback_data="sort_location")
    )
    return builder.as_markup()


def get_server_list_keyboard_with_sort(servers: list[Server], current_sort: str = "date") -> InlineKeyboardMarkup:
    """Клавиатура списка серверов с сортировкой."""
    builder = InlineKeyboardBuilder()

    # Сортируем серверы
    if current_sort == "hosting":
        sorted_servers = sorted(servers, key=lambda s: (s.hosting.lower(), (s.expiry_date - date.today()).days))
    elif current_sort == "location":
        sorted_servers = sorted(servers, key=lambda s: ((s.location or "zzz").lower(), (s.expiry_date - date.today()).days))
    else:  # date
        sorted_servers = sorted(servers, key=lambda s: (s.expiry_date - date.today()).days)

    for server in sorted_servers:
        days_left = (server.expiry_date - date.today()).days
        status = get_status_emoji(days_left)

        if days_left < 0:
            days_text = "!"
        elif days_left == 0:
            days_text = "сегодня"
        elif days_left == 1:
            days_text = "завтра"
        else:
            days_text = f"{days_left}д"

        builder.row(
            InlineKeyboardButton(
                text=f"{status} {server.name} • {days_text}",
                callback_data=f"server_{server.id}"
            )
        )

    # Кнопки сортировки
    date_mark = "✓" if current_sort == "date" else ""
    hosting_mark = "✓" if current_sort == "hosting" else ""
    location_mark = "✓" if current_sort == "location" else ""

    builder.row(
        InlineKeyboardButton(text=f"{date_mark}📅", callback_data="sort_date"),
        InlineKeyboardButton(text=f"{hosting_mark}🏢", callback_data="sort_hosting"),
        InlineKeyboardButton(text=f"{location_mark}📍", callback_data="sort_location")
    )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_server"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    return builder.as_markup()
