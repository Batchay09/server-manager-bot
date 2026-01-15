from datetime import date
from database import Server


def get_status_emoji(days_left: int) -> str:
    """Возвращает цветной эмодзи статуса по дням до оплаты."""
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


def get_status_text(days_left: int) -> str:
    """Возвращает текст статуса."""
    if days_left < 0:
        return "ПРОСРОЧЕНО"
    elif days_left == 0:
        return "СЕГОДНЯ"
    elif days_left == 1:
        return "ЗАВТРА"
    elif days_left <= 3:
        return "СРОЧНО"
    elif days_left <= 7:
        return "Скоро"
    else:
        return f"{days_left} дн."


def get_progress_bar(days_left: int, max_days: int = 30) -> str:
    """Создаёт визуальный прогресс-бар."""
    if days_left < 0:
        return "░░░░░░░░░░ 0%"

    percentage = min(100, max(0, (days_left / max_days) * 100))
    filled = int(percentage / 10)
    empty = 10 - filled

    bar = "▓" * filled + "░" * empty
    return f"{bar} {int(percentage)}%"


def format_server_info(server: Server, detailed: bool = False) -> str:
    """Форматирует карточку сервера в премиум-стиле."""
    days_left = (server.expiry_date - date.today()).days
    status_emoji = get_status_emoji(days_left)
    status_text = get_status_text(days_left)

    period_text = "мес" if server.payment_period == "monthly" else "год"

    # Заголовок
    text = f"┌{'─' * 28}\n"
    text += f"│ 🖥 <b>{server.name}</b>\n"
    text += f"├{'─' * 28}\n"

    # Основная информация
    text += f"│ 🏢 {server.hosting}\n"
    text += f"│ 📅 До {server.expiry_date.strftime('%d.%m.%Y')} ({status_text})\n"
    text += f"│ {get_progress_bar(days_left)} {status_emoji}\n"
    text += f"│ 💰 {server.price:.2f} {server.currency}/{period_text}\n"

    if detailed:
        if server.ip or server.url or server.notes or server.tags:
            text += f"├{'─' * 28}\n"

        if server.ip:
            text += f"│ 🌐 <code>{server.ip}</code>\n"
        if server.url:
            text += f"│ 🔗 {server.url}\n"
        if server.notes:
            text += f"│ 📝 {server.notes}\n"
        if server.tags:
            text += f"│ 🏷 {server.tags}\n"

        monitoring_status = "🟢 Вкл" if server.is_monitoring else "⚫ Выкл"
        text += f"│ 📡 Мониторинг: {monitoring_status}\n"

    text += f"└{'─' * 28}"

    return text


def format_server_list(servers: list[Server]) -> str:
    """Форматирует список серверов."""
    if not servers:
        return "📋 <b>Список серверов пуст</b>\n\n💡 Нажмите «➕ Добавить» чтобы добавить первый сервер"

    text = f"📋 <b>Ваши серверы</b> ({len(servers)})\n\n"

    # Сортируем по дням до оплаты
    sorted_servers = sorted(servers, key=lambda s: (s.expiry_date - date.today()).days)

    for server in sorted_servers:
        days_left = (server.expiry_date - date.today()).days
        status_emoji = get_status_emoji(days_left)
        status_text = get_status_text(days_left)

        text += f"{status_emoji} <b>{server.name}</b>\n"
        text += f"    └ {server.hosting} • {status_text}\n"

    return text


def format_expiring_servers(servers: list[Server]) -> str:
    """Форматирует список истекающих серверов."""
    if not servers:
        return "✅ <b>Всё оплачено!</b>\n\n🎉 Нет серверов с истекающей оплатой в ближайшие 30 дней"

    text = "⚡ <b>Требуют внимания</b>\n\n"

    for server in servers:
        days_left = (server.expiry_date - date.today()).days
        status_emoji = get_status_emoji(days_left)
        status_text = get_status_text(days_left)

        text += f"{status_emoji} <b>{server.name}</b>\n"
        text += f"    📅 {server.expiry_date.strftime('%d.%m.%Y')} — {status_text}\n"
        text += f"    💰 {server.price:.2f} {server.currency}\n\n"

    return text


def format_stats(servers: list[Server]) -> str:
    """Форматирует статистику расходов."""
    if not servers:
        return "📊 <b>Статистика</b>\n\n📭 Нет данных — добавьте серверы"

    monthly_by_currency: dict[str, float] = {}
    yearly_by_currency: dict[str, float] = {}
    by_hosting: dict[str, int] = {}

    for server in servers:
        currency = server.currency

        if server.payment_period == "monthly":
            monthly = server.price
            yearly = server.price * 12
        else:
            monthly = server.price / 12
            yearly = server.price

        monthly_by_currency[currency] = monthly_by_currency.get(currency, 0) + monthly
        yearly_by_currency[currency] = yearly_by_currency.get(currency, 0) + yearly

        by_hosting[server.hosting] = by_hosting.get(server.hosting, 0) + 1

    text = f"📊 <b>Статистика</b>\n"
    text += f"├{'─' * 24}\n"
    text += f"│ 🖥 Всего серверов: <b>{len(servers)}</b>\n"
    text += f"├{'─' * 24}\n"

    text += "│ 💳 <b>Ежемесячно:</b>\n"
    for currency, amount in sorted(monthly_by_currency.items()):
        text += f"│    {amount:.2f} {currency}\n"

    text += f"├{'─' * 24}\n"
    text += "│ 📆 <b>В год:</b>\n"
    for currency, amount in sorted(yearly_by_currency.items()):
        text += f"│    {amount:.2f} {currency}\n"

    text += f"├{'─' * 24}\n"
    text += "│ 🏢 <b>По хостингам:</b>\n"
    for hosting, count in sorted(by_hosting.items(), key=lambda x: -x[1]):
        text += f"│    {hosting}: {count} шт.\n"

    text += f"└{'─' * 24}"

    return text


def format_reminder(servers: list[Server]) -> str:
    """Форматирует напоминание об оплате."""
    if not servers:
        return ""

    text = "🔔 <b>Напоминание об оплате</b>\n\n"

    total_by_currency: dict[str, float] = {}

    for server in servers:
        days_left = (server.expiry_date - date.today()).days
        status_emoji = get_status_emoji(days_left)

        if days_left < 0:
            status = "❗ ПРОСРОЧЕНО"
        elif days_left == 0:
            status = "⚠️ СЕГОДНЯ"
        elif days_left == 1:
            status = "⏰ ЗАВТРА"
        else:
            status = f"📅 через {days_left} дн."

        text += f"{status_emoji} <b>{server.name}</b>\n"
        text += f"    {server.hosting} • {status}\n"
        text += f"    💰 {server.price:.2f} {server.currency}\n\n"

        total_by_currency[server.currency] = total_by_currency.get(server.currency, 0) + server.price

    if len(servers) > 1:
        text += "─" * 24 + "\n"
        text += "💵 <b>Итого к оплате:</b>\n"
        for currency, amount in sorted(total_by_currency.items()):
            text += f"    {amount:.2f} {currency}\n"

    return text


def parse_date(date_str: str) -> date | None:
    """Парсит дату из строки."""
    formats = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]

    for fmt in formats:
        try:
            return __import__('datetime').datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def parse_price(price_str: str) -> float | None:
    """Парсит цену из строки."""
    try:
        price_str = price_str.replace(",", ".").replace(" ", "")
        return float(price_str)
    except ValueError:
        return None
