import pandas as pd

from shared.errors import CSVProcessingError


RUS_MONTH_MAP = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}

EN_MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
    'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}

def _normalize_month(x):
    """Преобразует строковое название месяца в номер, с поддержкой RU/EN."""
    if isinstance(x, str):
        x_low = x.lower().strip()

        if x_low in RUS_MONTH_MAP:
            return RUS_MONTH_MAP[x_low]

        if x_low in EN_MONTH_MAP:
            return EN_MONTH_MAP[x_low]

        if x_low.isdigit():
            return int(x_low)

        raise CSVProcessingError(f"Неизвестный месяц: '{x}'")
    return x  # если int


def parse_dates_vectorized(df: pd.DataFrame) -> pd.Series:
    """
    Парсер даты:
    1) пробует arrival_date,
    2) для нераспарсенных строк собирает составную дату,
    3) если все варианты не дают дату — ошибка.
    """
    # 1. arrival_date
    if "arrival_date" in df.columns:
        parsed = pd.to_datetime(df["arrival_date"], errors="coerce")
    else:
        parsed = pd.Series(pd.NaT, index=df.index)

    mask = parsed.isna()

    # 2. составная дата
    if mask.any():
        months = df.loc[mask, "arrival_date_month"].map(_normalize_month)

        composed = (
            df.loc[mask, "arrival_date_year"].astype(str)
            + "-" + months.astype(str)
            + "-" + df.loc[mask, "arrival_date_day_of_month"].astype(str)
        )

        composed_parsed = pd.to_datetime(composed, errors="coerce")
        parsed.loc[mask] = composed_parsed

    # 3. финальная проверка
    if parsed.isna().any():
        bad_rows = parsed[parsed.isna()].index.tolist()
        raise CSVProcessingError(
            f"Не удалось распарсить дату. Проблемные строки: {bad_rows[:5]}..."
        )

    return parsed.dt.date
