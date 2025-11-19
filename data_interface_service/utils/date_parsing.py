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

SUPPORTED_DATE_FORMATS = [
    "%d.%m.%Y",
    "%d.%m.%y",
    "%d-%m-%Y",
    "%d-%m-%y",
    "%d/%m/%Y",
    "%d/%m/%y",
    "%Y-%m-%d",
]


def _try_parse_multiple_formats(series: pd.Series) -> pd.Series:
    """
    Пытается распарсить серию по всем известным форматам.
    Возвращает серию с датами или NaT.
    """
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)

    mask = parsed.isna()
    if not mask.any():
        return parsed

    # Пробуем явные форматы
    for fmt in SUPPORTED_DATE_FORMATS:
        parsed2 = pd.to_datetime(series[mask], format=fmt, errors="coerce")
        parsed.loc[mask] = parsed2
        mask = parsed.isna()
        if not mask.any():
            return parsed

    return parsed


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
    Универсальный парсер дат, поддерживающий разные форматы, RU/EN слова и составные поля.
    """

    # --- Если arrival_date существует — пробуем все форматы ---
    if "arrival_date" in df.columns:
        primary = _try_parse_multiple_formats(df["arrival_date"].astype(str))
    else:
        primary = pd.Series(pd.NaT, index=df.index)

    mask = primary.isna()

    # --- Составная дата — если есть три поля year/month/day ---
    if mask.any():
        required = ["arrival_date_year", "arrival_date_month", "arrival_date_day_of_month"]
        if all(col in df.columns for col in required):

            months = df.loc[mask, "arrival_date_month"].map(_normalize_month)

            composed = (
                df.loc[mask, "arrival_date_year"].astype(str)
                + "-" + months.astype(str)
                + "-" + df.loc[mask, "arrival_date_day_of_month"].astype(str)
            )

            parsed_composed = pd.to_datetime(composed, errors="coerce")
            primary.loc[mask] = parsed_composed

            mask = primary.isna()

    # --- Финальная проверка ---
    if mask.any():
        idx = mask[mask].index.tolist()
        raise CSVProcessingError(
            f"Не удалось распарсить даты. Некорректные строки: {idx[:10]}"
        )

    return primary.dt.date