"""
Импорт национальных праздников Португалии в таблицу Holiday.
Загружает только новые записи за указанный период.
"""

import holidays
from datetime import date
from sqlalchemy import and_
from sqlalchemy.orm import Session

from shared.db import get_sync_session
from shared.models import Holiday


def get_pt_holidays(start: date, end: date) -> list[tuple[date, str]]:
    """Возвращает отфильтрованный список праздников Португалии за период."""
    years = list(range(start.year, end.year + 1))
    pt_holidays = holidays.country_holidays("PT", years=years)
    return [(d, name) for d, name in pt_holidays.items() if start <= d <= end]


def load_holidays_to_db(start: date, end: date, db: Session) -> int:
    """Добавляет в базу новые праздники Португалии за указанный период."""
    filtered = get_pt_holidays(start, end)

    # Существующие даты для предотвращения дублирования
    existing_dates = {
        h[0]
        for h in db.query(Holiday.day).filter(
            and_(
                Holiday.day >= start,
                Holiday.day <= end,
                Holiday.region == "Portugal",
            )
        ).all()
    }

    # Отбор только новых записей
    new_records = [
        Holiday(
            day=d,
            holiday_name=name,
            is_national=True,
            region="Portugal",
        )
        for d, name in filtered
        if d not in existing_dates
    ]

    if not new_records:
        print("Нет новых праздников для добавления.")
        return 0

    db.add_all(new_records)
    db.commit()
    return len(new_records)


def main() -> None:
    """Точка входа: импорт праздников Португалии за 2015–2017 годы."""
    start = date(2015, 7, 1)
    end = date(2017, 8, 31)

    with get_sync_session() as db:
        count = load_holidays_to_db(start, end, db)
        print(f"Загружено {count} праздников Португалии.")


if __name__ == "__main__":
    main()
