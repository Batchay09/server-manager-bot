from datetime import date
from database import Server


def format_server_info(server: Server, detailed: bool = False) -> str:
    days_left = (server.expiry_date - date.today()).days

    if days_left < 0:
        status = "ПРОСРОЧЕНО"
    elif days_left == 0:
        status = "СЕГОДНЯ"
    elif days_left <= 3:
        status = "СРОЧНО"
    elif days_left <= 7:
        status = "Скоро"
    else:
        status = "ОК"

    period_text = "мес" if server.payment_period == "monthly" else "год"

    text = f"<b>{server.name}</b>\n"
    text += f"Хостинг: {server.hosting}\n"
    text += f"Оплата до: {server.expiry_date.strftime('%d.%m.%Y')} ({days_left} дн.) [{status}]\n"
    text += f"Цена: {server.price:.2f} {server.currency}/{period_text}\n"

    if detailed:
        if server.ip:
            text += f"IP: <code>{server.ip}</code>\n"
        if server.url:
            text += f"URL: {server.url}\n"
        if server.notes:
            text += f"Заметки: {server.notes}\n"
        if server.tags:
            text += f"Теги: {server.tags}\n"
        text += f"Мониторинг: {'Включён' if server.is_monitoring else 'Выключен'}\n"

    return text


def format_server_list(servers: list[Server]) -> str:
    if not servers:
        return "У вас пока нет добавленных серверов."

    text = f"<b>Ваши серверы ({len(servers)}):</b>\n\n"

    for server in servers:
        days_left = (server.expiry_date - date.today()).days

        if days_left < 0:
            emoji = "!"
        elif days_left <= 7:
            emoji = "!"
        else:
            emoji = ""

        text += f"{emoji}<b>{server.name}</b> ({server.hosting})\n"
        text += f"   {server.expiry_date.strftime('%d.%m.%Y')} ({days_left} дн.)\n"

    return text


def format_expiring_servers(servers: list[Server]) -> str:
    if not servers:
        return "Нет серверов с истекающей оплатой в ближайшие 30 дней."

    text = "<b>Серверы с истекающей оплатой:</b>\n\n"

    for server in servers:
        days_left = (server.expiry_date - date.today()).days

        if days_left < 0:
            status = "ПРОСРОЧЕНО"
        elif days_left == 0:
            status = "СЕГОДНЯ"
        elif days_left <= 3:
            status = "СРОЧНО"
        else:
            status = f"{days_left} дн."

        text += f"<b>{server.name}</b> ({server.hosting})\n"
        text += f"   Оплата до: {server.expiry_date.strftime('%d.%m.%Y')} [{status}]\n"
        text += f"   {server.price:.2f} {server.currency}\n\n"

    return text


def format_stats(servers: list[Server]) -> str:
    if not servers:
        return "Нет данных для статистики."

    monthly_by_currency: dict[str, float] = {}
    yearly_by_currency: dict[str, float] = {}
    by_hosting: dict[str, float] = {}

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

        hosting_key = f"{server.hosting} ({currency})"
        by_hosting[hosting_key] = by_hosting.get(hosting_key, 0) + monthly

    text = f"<b>Статистика ({len(servers)} серверов)</b>\n\n"

    text += "<b>Ежемесячные расходы:</b>\n"
    for currency, amount in sorted(monthly_by_currency.items()):
        text += f"  {amount:.2f} {currency}\n"

    text += "\n<b>Годовые расходы:</b>\n"
    for currency, amount in sorted(yearly_by_currency.items()):
        text += f"  {amount:.2f} {currency}\n"

    text += "\n<b>По хостингам (в месяц):</b>\n"
    for hosting, amount in sorted(by_hosting.items(), key=lambda x: -x[1]):
        text += f"  {hosting}: {amount:.2f}\n"

    return text


def format_reminder(servers: list[Server]) -> str:
    if not servers:
        return ""

    text = "Напоминание об оплате серверов:\n\n"

    for server in servers:
        days_left = (server.expiry_date - date.today()).days

        if days_left < 0:
            status = "ПРОСРОЧЕНО!"
        elif days_left == 0:
            status = "СЕГОДНЯ!"
        elif days_left == 1:
            status = "ЗАВТРА!"
        else:
            status = f"через {days_left} дн."

        text += f"<b>{server.name}</b> ({server.hosting})\n"
        text += f"Оплата {status}: {server.expiry_date.strftime('%d.%m.%Y')}\n"
        text += f"Сумма: {server.price:.2f} {server.currency}\n\n"

    return text


def parse_date(date_str: str) -> date | None:
    formats = ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]

    for fmt in formats:
        try:
            return __import__('datetime').datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def parse_price(price_str: str) -> float | None:
    try:
        price_str = price_str.replace(",", ".").replace(" ", "")
        return float(price_str)
    except ValueError:
        return None
