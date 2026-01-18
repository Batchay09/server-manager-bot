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
        return f"ПРОСРОЧЕНО ({abs(days_left)} дн.)"
    elif days_left == 0:
        return "СЕГОДНЯ"
    elif days_left == 1:
        return "ЗАВТРА"
    elif days_left <= 3:
        return f"СРОЧНО ({days_left} дн.)"
    elif days_left <= 7:
        return f"Скоро ({days_left} дн.)"
    else:
        return f"{days_left} дн."


def get_period_text(period: str) -> str:
    """Возвращает текст периода оплаты."""
    if period == "monthly":
        return "мес"
    elif period == "quarterly":
        return "3 мес"
    elif period == "halfyear":
        return "6 мес"
    elif period == "yearly":
        return "год"
    elif period and period.startswith("custom_"):
        try:
            months = int(period.split("_")[1])
            return f"{months} мес"
        except (IndexError, ValueError):
            return "мес"
    else:
        return "мес"


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
    """Форматирует карточку сервера."""
    days_left = (server.expiry_date - date.today()).days
    status_emoji = get_status_emoji(days_left)
    status_text = get_status_text(days_left)
    period_text = get_period_text(server.payment_period)

    # Заголовок
    text = f"🖥 <b>{server.name}</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Статус оплаты
    text += f"{status_emoji} <b>{status_text}</b>\n"
    text += f"{get_progress_bar(days_left)}\n"
    text += f"📅 {server.expiry_date.strftime('%d.%m.%Y')}\n\n"

    # Основная информация
    text += f"🏢 {server.hosting}"
    if server.location:
        text += f" • {server.location}"
    text += f"\n💰 {server.price:.0f} {server.currency}/{period_text}\n"

    if detailed:
        extras = []
        if server.ip:
            extras.append(f"🌐 <code>{server.ip}</code>")
        if server.url:
            extras.append(f"🔗 {server.url}")
        if server.notes:
            extras.append(f"📝 {server.notes}")
        if server.tags:
            extras.append(f"🏷 {server.tags}")

        if extras:
            text += "\n" + "\n".join(extras)

    return text


def format_server_list(servers: list[Server]) -> str:
    """Форматирует список серверов."""
    return format_server_list_sorted(servers, "date")


def format_server_list_sorted(servers: list[Server], sort_by: str = "date") -> str:
    """Форматирует список серверов с сортировкой."""
    if not servers:
        return (
            "📋 <b>Нет серверов</b>\n\n"
            "Нажмите <b>➕ Добавить</b> чтобы\n"
            "добавить первый сервер"
        )

    # Считаем статистику
    total = len(servers)
    urgent = sum(1 for s in servers if (s.expiry_date - date.today()).days <= 7)

    sort_icons = {"date": "📅", "hosting": "🏢", "location": "📍"}
    sort_icon = sort_icons.get(sort_by, "📅")

    text = f"📋 <b>Серверы</b> ({total})"
    if urgent > 0:
        text += f" • ⚠️ {urgent}"
    text += f"\n{sort_icon} Сортировка\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"

    # Сортируем по выбранному критерию
    if sort_by == "hosting":
        sorted_servers = sorted(servers, key=lambda s: (s.hosting.lower(), (s.expiry_date - date.today()).days))
    elif sort_by == "location":
        sorted_servers = sorted(servers, key=lambda s: ((s.location or "zzz").lower(), (s.expiry_date - date.today()).days))
    else:  # date
        sorted_servers = sorted(servers, key=lambda s: (s.expiry_date - date.today()).days)

    current_group = None
    for server in sorted_servers:
        days_left = (server.expiry_date - date.today()).days
        status_emoji = get_status_emoji(days_left)

        # Показываем заголовок группы
        if sort_by == "hosting" and current_group != server.hosting:
            current_group = server.hosting
            text += f"\n<b>{server.hosting}</b>\n"
        elif sort_by == "location":
            loc = server.location or "—"
            if current_group != loc:
                current_group = loc
                text += f"\n<b>{loc}</b>\n"

    text += "\n👆 Выберите сервер"

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
