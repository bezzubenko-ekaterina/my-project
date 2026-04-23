import asyncio
import logging
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

import config
from google_sheets import SheetsClient

# Дольше ждём ответ API (медленный интернет / высокий пинг).
_REQUEST = HTTPXRequest(connect_timeout=90.0, read_timeout=60.0, write_timeout=60.0)
_MENU_BUTTON_DEBTS = "Налоги к уплате"
_REMINDER_DAYS = (7, 3, 1)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(_MENU_BUTTON_DEBTS)]],
        resize_keyboard=True,
    )


def _parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_status(value: str) -> str:
    return (value or "").strip().lower()


def _amount_present(value: str) -> bool:
    return (value or "").strip() != ""


def _is_active(value: str) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "да"}


def _looks_like_link_code(value: str) -> bool:
    text = (value or "").strip()
    return bool(re.fullmatch(r"[A-Za-z0-9]{6}", text))


async def _notify_admin(application: Application, message: str) -> None:
    if config.ADMIN_ID <= 0:
        return
    try:
        await application.bot.send_message(chat_id=config.ADMIN_ID, text=message)
    except TelegramError:
        logger.exception("Не удалось отправить сообщение администратору")


async def _get_clients(application: Application) -> list[dict[str, str]]:
    sheets: SheetsClient = application.bot_data["sheets"]
    return await asyncio.to_thread(sheets.get_clients)


async def _get_payments(application: Application) -> list[dict[str, str]]:
    sheets: SheetsClient = application.bot_data["sheets"]
    return await asyncio.to_thread(sheets.get_payments)


async def _get_logs(application: Application) -> list[dict[str, str]]:
    sheets: SheetsClient = application.bot_data["sheets"]
    return await asyncio.to_thread(sheets.get_logs)


async def _append_log(
    application: Application,
    payment_id: str,
    client_id: str,
    notification_type: str,
    status: str,
) -> None:
    sheets: SheetsClient = application.bot_data["sheets"]
    await asyncio.to_thread(
        sheets.append_log,
        payment_id,
        client_id,
        notification_type,
        status,
    )


def _build_client_maps(
    clients: list[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    by_client_id: dict[str, dict[str, str]] = {}
    by_tg_id: dict[str, list[dict[str, str]]] = {}
    for row in clients:
        client_id = (row.get("client_id") or "").strip()
        tg_id = (row.get("telegram_id") or "").strip()
        if client_id:
            by_client_id[client_id] = row
        if tg_id:
            by_tg_id.setdefault(tg_id, []).append(row)
    return by_client_id, by_tg_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    args = context.args or []
    if args:
        await _link_client_by_code(update, context, args[0])
        return

    await update.message.reply_text(
        "Привет! Для привязки отправьте /start ВАШ_КОД_ИЗ_ТАБЛИЦЫ.\n"
        "После привязки используйте кнопку «Налоги к уплате».",
        reply_markup=_menu_keyboard(),
    )


async def _link_client_by_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    link_code: str,
) -> None:
    if not update.message:
        return
    chat_id = str(update.effective_chat.id)
    sheets: SheetsClient = context.application.bot_data["sheets"]
    client_row = await asyncio.to_thread(sheets.find_client_by_link_code, link_code)
    if not client_row:
        await update.message.reply_text(
            "Код привязки не найден. Проверь код у бухгалтера.",
            reply_markup=_menu_keyboard(),
        )
        return
    if not _is_active(client_row.get("active", "")):
        await update.message.reply_text(
            "Клиент в архиве. Обратитесь к бухгалтеру.",
            reply_markup=_menu_keyboard(),
        )
        return
    row_num = int(client_row["__row"])
    await asyncio.to_thread(sheets.set_client_link, row_num, chat_id)
    all_clients = await asyncio.to_thread(sheets.get_clients)
    linked_names = [
        (row.get("name") or "").strip()
        for row in all_clients
        if (row.get("telegram_id") or "").strip() == chat_id and (row.get("name") or "").strip()
    ]
    # Сохраняем порядок и убираем дубли, если строка случайно повторилась.
    unique_names = list(dict.fromkeys(linked_names))
    if unique_names:
        names_block = "\n".join(f"- {name}" for name in unique_names)
        message = (
            "Вы успешно зарегистрировались.\n"
            "Ваши привязанные организации:\n"
            f"{names_block}"
        )
    else:
        client_name = (client_row.get("name") or "").strip() or "клиент"
        message = f"Вы успешно зарегистрировались как {client_name}."
    await update.message.reply_text(
        message,
        reply_markup=_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "/start КОД — привязать аккаунт клиента\n"
        "/help — помощь\n"
        "Кнопка «Налоги к уплате» — текущие задолженности",
        reply_markup=_menu_keyboard(),
    )


async def debts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    tg_id = str(update.effective_chat.id)
    clients = await _get_clients(context.application)
    payments = await _get_payments(context.application)
    by_client_id, by_tg_id = _build_client_maps(clients)

    client_rows = by_tg_id.get(tg_id, [])
    if not client_rows:
        await update.message.reply_text(
            "Ваш Telegram ещё не привязан. Отправьте /start КОД_КЛИЕНТА.",
            reply_markup=_menu_keyboard(),
        )
        return
    client_ids = {
        (row.get("client_id") or "").strip()
        for row in client_rows
        if (row.get("client_id") or "").strip()
    }
    client_payments = [
        row for row in payments if (row.get("client_id") or "").strip() in client_ids
    ]

    pending_with_amount = []
    has_draft_or_unknown = False
    for payment in client_payments:
        status = _normalize_status(payment.get("status", ""))
        amount = payment.get("amount", "")
        if status == "pending" and _amount_present(amount):
            pending_with_amount.append(payment)
        elif status in {"draft", ""} or (status == "pending" and not _amount_present(amount)):
            has_draft_or_unknown = True

    if pending_with_amount:
        lines = ["Ваши налоги к уплате:"]
        for row in pending_with_amount:
            org_name = (
                by_client_id.get((row.get("client_id") or "").strip(), {}).get("name")
                or (row.get("client_id") or "")
            ).strip()
            tax_type = (row.get("tax_type") or "Платёж").strip()
            due_date = (row.get("due_date") or "").strip()
            amount = (row.get("amount") or "").strip()
            lines.append(f"- {org_name}: {tax_type}, {amount} до {due_date}")
        await update.message.reply_text("\n".join(lines), reply_markup=_menu_keyboard())
        return

    if has_draft_or_unknown:
        await update.message.reply_text("Ваш бухгалтер активно считает...", reply_markup=_menu_keyboard())
        return

    await update.message.reply_text("У вас нет задолженностей!", reply_markup=_menu_keyboard())


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text == _MENU_BUTTON_DEBTS:
        await debts_command(update, context)
    elif _looks_like_link_code(text):
        await _link_client_by_code(update, context, text)
    else:
        await update.message.reply_text(
            "Используйте кнопку «Налоги к уплате» или /help.",
            reply_markup=_menu_keyboard(),
        )


async def _send_payment_notification(
    application: Application,
    chat_id: int,
    amount: str,
    due_date_value: str,
) -> None:
    await application.bot.send_message(
        chat_id=chat_id,
        text=f"Добрый день! Оплатите {amount} до {due_date_value}",
    )


async def process_notifications(application: Application) -> None:
    now = datetime.now(ZoneInfo(config.TIMEZONE))
    if now.hour < config.NOTIFICATION_HOUR:
        return

    clients = await _get_clients(application)
    payments = await _get_payments(application)
    logs = await _get_logs(application)
    clients_by_id, _ = _build_client_maps(clients)

    sent_keys = {
        ((row.get("payment_id") or "").strip(), (row.get("notification_type") or "").strip())
        for row in logs
        if _normalize_status(row.get("status", "")) == "sent"
    }
    skipped_unlinked_keys = {
        ((row.get("payment_id") or "").strip(), (row.get("notification_type") or "").strip())
        for row in logs
        if _normalize_status(row.get("status", "")) == "skipped_unlinked"
    }

    for payment in payments:
        payment_id = (payment.get("payment_id") or "").strip()
        client_id = (payment.get("client_id") or "").strip()
        status = _normalize_status(payment.get("status", ""))
        amount = (payment.get("amount") or "").strip()
        due_date_value = (payment.get("due_date") or "").strip()
        due_date = _parse_date(due_date_value)
        amount_confirmed_at = (payment.get("amount_confirmed_at") or "").strip()

        if not payment_id or not client_id or status != "pending" or not _amount_present(amount):
            continue

        notification_types: list[str] = []
        if due_date:
            days_left = (due_date - now.date()).days
            for days_before in _REMINDER_DAYS:
                if days_left == days_before:
                    notification_types.append(f"due_{days_before}")
        if amount_confirmed_at:
            notification_types.append("amount_confirmed")

        if "due_1" in notification_types:
            notification_types = ["due_1"]
        elif "due_3" in notification_types:
            notification_types = ["due_3"]
        elif "due_7" in notification_types:
            notification_types = ["due_7"]
        elif "amount_confirmed" in notification_types:
            notification_types = ["amount_confirmed"]
        else:
            notification_types = []

        for notification_type in notification_types:
            key = (payment_id, notification_type)
            if key in sent_keys:
                continue
            client = clients_by_id.get(client_id)
            if not client or not _is_active(client.get("active", "")):
                continue

            telegram_id = (client.get("telegram_id") or "").strip()
            if not telegram_id:
                if key not in skipped_unlinked_keys:
                    await _append_log(application, payment_id, client_id, notification_type, "skipped_unlinked")
                    skipped_unlinked_keys.add(key)
                continue

            try:
                await _send_payment_notification(application, int(telegram_id), amount, due_date_value)
                await _append_log(application, payment_id, client_id, notification_type, "sent")
                sent_keys.add(key)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Ошибка отправки платежного уведомления")
                await _append_log(application, payment_id, client_id, notification_type, "failed")
                await _notify_admin(
                    application,
                    (
                        "Ошибка отправки уведомления\n"
                        f"payment_id={payment_id}\n"
                        f"client_id={client_id}\n"
                        f"type={notification_type}\n"
                        f"error={exc}"
                    ),
                )


async def scheduler_loop(application: Application) -> None:
    while True:
        try:
            await process_notifications(application)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Ошибка в цикле планировщика")
            if config.ADMIN_ID > 0:
                try:
                    await application.bot.send_message(
                        chat_id=config.ADMIN_ID,
                        text=f"Планировщик упал с ошибкой: {exc}",
                    )
                except TelegramError:
                    logger.exception("Не удалось отправить админ-алерт из планировщика")
        await asyncio.sleep(config.CHECK_INTERVAL_SECONDS)


async def post_init(application: Application) -> None:
    application.create_task(scheduler_loop(application))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Необработанная ошибка в обработчике", exc_info=context.error)
    await _notify_admin(context.application, f"Необработанная ошибка: {context.error}")


def _validate_config() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан. Заполни .env")
    if not config.GOOGLE_SPREADSHEET_ID:
        raise SystemExit("GOOGLE_SPREADSHEET_ID (или GOOGLE_SHEETS_ID) не задан.")


def main() -> None:
    _validate_config()
    sheets = SheetsClient(
        spreadsheet_id=config.GOOGLE_SPREADSHEET_ID,
        service_account_json=config.GOOGLE_SERVICE_ACCOUNT_JSON,
        service_account_json_path=config.GOOGLE_SERVICE_ACCOUNT_JSON_PATH,
    )
    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .request(_REQUEST)
        .post_init(post_init)
        .build()
    )
    app.bot_data["sheets"] = sheets

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_router))
    app.add_error_handler(error_handler)
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        bootstrap_retries=-1,
    )


if __name__ == "__main__":
    main()
