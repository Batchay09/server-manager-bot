from datetime import date
from database import Server
from config import EXCHANGE_RATES


def convert_to_rub(amount: float, currency: str) -> float:
    """Конвертирует сумму в рубли."""
    rate = EXCHANGE_RATES.get(currency, 1.0)
    return amount * rate


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
    text += f"📊 <b>Статус оплаты</b>\n"
    text += f"{status_emoji} {status_text}\n"
    text += f"{get_progress_bar(days_left)}\n\n"

    # Основная информация
    text += f"📋 <b>Информация</b>\n"
    text += f"├ 🏢 {server.hosting}\n"
    if server.location:
        text += f"├ 📍 {server.location}\n"
    text += f"├ 💰 {server.price:.0f} {server.currency}/{period_text}\n"
    text += f"└ {server.expiry_date.strftime('%d.%m.%Y')} • {status_text}\n"

    if detailed:
        extras = []
        if server.ip:
            extras.append(f"├ 🌐 <code>{server.ip}</code>")
        if server.url:
            extras.append(f"├ 🔗 {server.url}")
        if server.notes:
            extras.append(f"├ 📝 {server.notes}")
        if server.tags:
            extras.append(f"└ 🏷 {server.tags}")

        if extras:
            text += f"\n🔧 <b>Дополнительно</b>\n"
            # Исправляем последний элемент на └
            if len(extras) > 0:
                extras[-1] = extras[-1].replace("├", "└", 1)
            text += "\n".join(extras)

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

    sort_names = {"date": "по дате", "hosting": "по хостингу", "location": "по локации"}
    sort_name = sort_names.get(sort_by, "по дате")

    text = f"📋 <b>Мои серверы</b> ({total})\n"
    if urgent > 0:
        text += f"⚠️ Требуют внимания: {urgent}\n"
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
        status_text = get_status_text(days_left)
        period_text = get_period_text(server.payment_period)

        # Показываем заголовок группы при сортировке
        if sort_by == "hosting" and current_group != server.hosting:
            current_group = server.hosting
            text += f"\n🏢 <b>{server.hosting}</b>\n"
        elif sort_by == "location":
            loc = server.location or "Без локации"
            if current_group != loc:
                current_group = loc
                text += f"\n📍 <b>{loc}</b>\n"

        # Информация о сервере
        text += f"\n{status_emoji} <b>{server.name}</b>\n"
        # При сортировке по полю — не показываем его (оно в заголовке группы)
        if server.location and sort_by != "location":
            text += f"   {server.location}\n"
        if sort_by != "hosting":
            text += f"   {server.hosting}\n"
        text += f"   💰 {server.price:.0f} {server.currency}/{period_text} • {server.expiry_date.strftime('%d.%m')} ({status_text})\n"

    text += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🔽 Сортировка: {sort_name}"

    return text


def format_expiring_servers(servers: list[Server]) -> str:
    """Форматирует список истекающих серверов."""
    if not servers:
        return (
            "✅ <b>Всё оплачено!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎉 Нет серверов с истекающей\n"
            "оплатой в ближайшие 30 дней"
        )

    text = f"⚡ <b>Требуют внимания</b> ({len(servers)})\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"

    total_by_currency: dict[str, float] = {}

    for server in servers:
        days_left = (server.expiry_date - date.today()).days
        status_emoji = get_status_emoji(days_left)
        status_text = get_status_text(days_left)
        period_text = get_period_text(server.payment_period)

        text += f"\n{status_emoji} <b>{server.name}</b>\n"
        if server.location:
            text += f"   {server.location}\n"
        text += f"   {server.hosting}\n"
        text += f"   {server.expiry_date.strftime('%d.%m.%Y')} — {status_text}\n"
        text += f"   💰 {server.price:.0f} {server.currency}/{period_text}\n"

        total_by_currency[server.currency] = total_by_currency.get(server.currency, 0) + server.price

    # Итого к оплате
    text += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "💵 <b>Итого к оплате:</b>\n"
    total_rub = 0.0
    for currency, amount in sorted(total_by_currency.items()):
        text += f"   {amount:.0f} {currency}\n"
        total_rub += convert_to_rub(amount, currency)
    if len(total_by_currency) > 1 or "RUB" not in total_by_currency:
        text += f"   ≈ <b>{total_rub:.0f} ₽</b>\n"

    return text


def format_stats(servers: list[Server]) -> str:
    """Форматирует статистику расходов."""
    if not servers:
        return "📊 <b>Статистика</b>\n\n📭 Нет данных — добавьте серверы"

    monthly_by_currency: dict[str, float] = {}
    yearly_by_currency: dict[str, float] = {}
    by_hosting: dict[str, int] = {}
    total_monthly_rub = 0.0
    total_yearly_rub = 0.0

    for server in servers:
        currency = server.currency

        if server.payment_period == "monthly":
            monthly = server.price
            yearly = server.price * 12
        elif server.payment_period == "quarterly":
            monthly = server.price / 3
            yearly = server.price * 4
        elif server.payment_period == "halfyear":
            monthly = server.price / 6
            yearly = server.price * 2
        elif server.payment_period == "yearly":
            monthly = server.price / 12
            yearly = server.price
        elif server.payment_period and server.payment_period.startswith("custom_"):
            try:
                months = int(server.payment_period.split("_")[1])
                monthly = server.price / months
                yearly = monthly * 12
            except (IndexError, ValueError):
                monthly = server.price
                yearly = server.price * 12
        else:
            monthly = server.price
            yearly = server.price * 12

        monthly_by_currency[currency] = monthly_by_currency.get(currency, 0) + monthly
        yearly_by_currency[currency] = yearly_by_currency.get(currency, 0) + yearly

        # Конвертируем в рубли для итого
        total_monthly_rub += convert_to_rub(monthly, currency)
        total_yearly_rub += convert_to_rub(yearly, currency)

        by_hosting[server.hosting] = by_hosting.get(server.hosting, 0) + 1

    text = f"📊 <b>Статистика</b>\n"
    text += f"├{'─' * 24}\n"
    text += f"│ 🖥 Всего серверов: <b>{len(servers)}</b>\n"
    text += f"├{'─' * 24}\n"

    text += "│ 💳 <b>Ежемесячно:</b>\n"
    for currency, amount in sorted(monthly_by_currency.items()):
        text += f"│    {amount:.0f} {currency}\n"
    if len(monthly_by_currency) > 1 or "RUB" not in monthly_by_currency:
        text += f"│    ≈ <b>{total_monthly_rub:.0f} ₽</b>\n"

    text += f"├{'─' * 24}\n"
    text += "│ 📆 <b>В год:</b>\n"
    for currency, amount in sorted(yearly_by_currency.items()):
        text += f"│    {amount:.0f} {currency}\n"
    if len(yearly_by_currency) > 1 or "RUB" not in yearly_by_currency:
        text += f"│    ≈ <b>{total_yearly_rub:.0f} ₽</b>\n"

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
            status = f"через {days_left} дн."

        text += f"{status_emoji} <b>{server.name}</b>\n"
        text += f"    {server.hosting} • {status}\n"
        text += f"    💰 {server.price:.2f} {server.currency}\n\n"

        total_by_currency[server.currency] = total_by_currency.get(server.currency, 0) + server.price

    text += "─" * 24 + "\n"
    text += "💵 <b>Итого к оплате:</b>\n"
    total_rub = 0.0
    for currency, amount in sorted(total_by_currency.items()):
        text += f"    {amount:.0f} {currency}\n"
        total_rub += convert_to_rub(amount, currency)
    if len(total_by_currency) > 1 or "RUB" not in total_by_currency:
        text += f"    ≈ <b>{total_rub:.0f} ₽</b>\n"

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
