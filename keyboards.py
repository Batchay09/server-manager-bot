from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Server


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Добавить сервер", callback_data="add_server"),
        InlineKeyboardButton(text="Мои серверы", callback_data="list_servers")
    )
    builder.row(
        InlineKeyboardButton(text="Истекающие", callback_data="expiring_servers"),
        InlineKeyboardButton(text="Статистика", callback_data="stats")
    )
    builder.row(
        InlineKeyboardButton(text="Настройки", callback_data="settings")
    )
    return builder.as_markup()


def get_server_list_keyboard(servers: list[Server]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for server in servers:
        days_left = (server.expiry_date - __import__('datetime').date.today()).days
        status = "!" if days_left <= 7 else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{status}{server.name} ({server.hosting}) - {days_left}д",
                callback_data=f"server_{server.id}"
            )
        )
    builder.row(
        InlineKeyboardButton(text="Добавить", callback_data="add_server"),
        InlineKeyboardButton(text="Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_server_detail_keyboard(server: Server) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Оплачено", callback_data=f"paid_{server.id}"),
        InlineKeyboardButton(text="Редактировать", callback_data=f"edit_{server.id}")
    )

    monitoring_text = "Выкл. мониторинг" if server.is_monitoring else "Вкл. мониторинг"
    builder.row(
        InlineKeyboardButton(text=monitoring_text, callback_data=f"toggle_monitoring_{server.id}"),
        InlineKeyboardButton(text="Удалить", callback_data=f"delete_{server.id}")
    )
    builder.row(
        InlineKeyboardButton(text="Назад к списку", callback_data="list_servers")
    )
    return builder.as_markup()


def get_delete_confirm_keyboard(server_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Да, удалить", callback_data=f"confirm_delete_{server_id}"),
        InlineKeyboardButton(text="Отмена", callback_data=f"server_{server_id}")
    )
    return builder.as_markup()


def get_edit_server_keyboard(server_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Название", callback_data=f"edit_name_{server_id}"),
        InlineKeyboardButton(text="Хостинг", callback_data=f"edit_hosting_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="IP", callback_data=f"edit_ip_{server_id}"),
        InlineKeyboardButton(text="URL", callback_data=f"edit_url_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Дата оплаты", callback_data=f"edit_expiry_{server_id}"),
        InlineKeyboardButton(text="Цена", callback_data=f"edit_price_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Заметки", callback_data=f"edit_notes_{server_id}"),
        InlineKeyboardButton(text="Теги", callback_data=f"edit_tags_{server_id}")
    )
    builder.row(
        InlineKeyboardButton(text="Назад", callback_data=f"server_{server_id}")
    )
    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="RUB", callback_data="currency_RUB"),
        InlineKeyboardButton(text="USD", callback_data="currency_USD"),
        InlineKeyboardButton(text="EUR", callback_data="currency_EUR")
    )
    return builder.as_markup()


def get_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Ежемесячно", callback_data="period_monthly"),
        InlineKeyboardButton(text="Ежегодно", callback_data="period_yearly")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_skip_keyboard(field: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить", callback_data=f"skip_{field}"),
        InlineKeyboardButton(text="Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_settings_keyboard(reminder_days: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"За {reminder_days} дней", callback_data="current_days")
    )
    builder.row(
        InlineKeyboardButton(text="3 дня", callback_data="set_days_3"),
        InlineKeyboardButton(text="5 дней", callback_data="set_days_5"),
        InlineKeyboardButton(text="7 дней", callback_data="set_days_7")
    )
    builder.row(
        InlineKeyboardButton(text="10 дней", callback_data="set_days_10"),
        InlineKeyboardButton(text="14 дней", callback_data="set_days_14")
    )
    builder.row(
        InlineKeyboardButton(text="Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_back_keyboard(callback: str = "main_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Назад", callback_data=callback)
    )
    return builder.as_markup()
