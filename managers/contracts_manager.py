"""Работа с договорами клиента в базе данных."""
from datetime import date

from managers.database import Database


class ContractsManager:
    """Сохраняет и читает договоры, чтобы не вводить дату вручную."""

    def __init__(self):
        self.db = Database()

    def save_contract(self, client_id, contract_date, amount=None, number_id=None):
        """Сохранить дату договора клиента.

        Дата обновляется, если договор этого клиента уже есть, поэтому
        повторное создание документа не плодит дубликаты.
        """
        number = self._contract_number(
            number_id if number_id is not None else client_id,
            contract_date
        )
        existing = self.db.fetch_one(
            "SELECT id FROM contracts WHERE client_id = ? AND number = ?",
            (client_id, number),
        )
        if existing:
            self.db.execute(
                "UPDATE contracts SET date = ?, amount = ? WHERE id = ?",
                (contract_date.isoformat(), amount, existing["id"]),
            )
            return existing["id"]

        return self.db.execute(
            "INSERT INTO contracts (client_id, number, date, amount) "
            "VALUES (?, ?, ?, ?)",
            (client_id, number, contract_date.isoformat(), amount),
        )

    def get_last_contract_date(self, client_id):
        """Вернуть дату последнего договора клиента или None."""
        row = self.db.fetch_one(
            "SELECT date FROM contracts WHERE client_id = ? "
            "ORDER BY date DESC, id DESC LIMIT 1",
            (client_id,),
        )
        if not row or not row["date"]:
            return None
        try:
            return date.fromisoformat(str(row["date"])[:10])
        except ValueError:
            return None

    @staticmethod
    def _contract_number(client_id, contract_date):
        return f"{client_id}-{contract_date:%Y%m%d}"
