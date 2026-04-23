import json
import uuid
from datetime import datetime
from typing import Any

import gspread


CLIENTS_SHEET = "Clients"
PAYMENTS_SHEET = "Payments"
LOG_SHEET = "NotificationLog"


class SheetsClient:
    def __init__(self, spreadsheet_id: str, service_account_json: str, service_account_json_path: str = "") -> None:
        creds = self._load_credentials(service_account_json, service_account_json_path)
        client = gspread.service_account_from_dict(creds)
        self.spreadsheet = client.open_by_key(spreadsheet_id)
        self.clients_ws = self.spreadsheet.worksheet(CLIENTS_SHEET)
        self.payments_ws = self.spreadsheet.worksheet(PAYMENTS_SHEET)
        self.log_ws = self.spreadsheet.worksheet(LOG_SHEET)

    @staticmethod
    def _load_credentials(service_account_json: str, service_account_json_path: str) -> dict[str, Any]:
        if service_account_json.strip():
            try:
                return json.loads(service_account_json)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "GOOGLE_SERVICE_ACCOUNT_JSON должен содержать валидный JSON."
                ) from exc
        if service_account_json_path.strip():
            with open(service_account_json_path, "r", encoding="utf-8") as file:
                return json.load(file)
        raise ValueError(
            "Не найдены креды Google. Укажи GOOGLE_SERVICE_ACCOUNT_JSON или GOOGLE_SERVICE_ACCOUNT_JSON_PATH."
        )

    @staticmethod
    def _rows_as_dicts(values: list[list[str]]) -> list[dict[str, str]]:
        if not values:
            return []
        headers = values[0]
        rows: list[dict[str, str]] = []
        for row_idx, row_values in enumerate(values[1:], start=2):
            row: dict[str, str] = {"__row": str(row_idx)}
            for col_idx, header in enumerate(headers):
                row[header] = row_values[col_idx] if col_idx < len(row_values) else ""
            rows.append(row)
        return rows

    def get_clients(self) -> list[dict[str, str]]:
        return self._rows_as_dicts(self.clients_ws.get_all_values())

    def get_payments(self) -> list[dict[str, str]]:
        return self._rows_as_dicts(self.payments_ws.get_all_values())

    def get_logs(self) -> list[dict[str, str]]:
        return self._rows_as_dicts(self.log_ws.get_all_values())

    def find_client_by_link_code(self, link_code: str) -> dict[str, str] | None:
        normalized_code = link_code.strip().upper()
        for row in self.get_clients():
            if row.get("link_code", "").strip().upper() == normalized_code:
                return row
        return None

    def find_client_by_telegram_id(self, telegram_id: str) -> dict[str, str] | None:
        normalized_tg = telegram_id.strip()
        for row in self.get_clients():
            if row.get("telegram_id", "").strip() == normalized_tg:
                return row
        return None

    def set_client_link(self, row_num: int, telegram_id: str) -> None:
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.clients_ws.update(f"G{row_num}:H{row_num}", [[telegram_id, now]], value_input_option="USER_ENTERED")

    def append_log(
        self,
        payment_id: str,
        client_id: str,
        notification_type: str,
        status: str,
    ) -> None:
        log_id = f"L{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        sent_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.log_ws.append_row(
            [log_id, payment_id, client_id, notification_type, sent_at, status],
            value_input_option="USER_ENTERED",
        )
