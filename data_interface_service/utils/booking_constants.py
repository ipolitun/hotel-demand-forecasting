CATEGORICAL_COLUMNS = {
    "market_segment": {"default": "Undefined", "dtype": str},
    "distribution_channel": {"default": "Undefined", "dtype": str},
    "booking_ref": {"default": "", "dtype": str},
}

NUMERIC_COLUMNS = {
    # гости
    "adults": {"default": 0, "dtype": int},
    "children": {"default": 0, "dtype": int},
    "babies": {"default": 0, "dtype": int},
    "total_guests": {"default": 0, "dtype": int},

    # ночи
    "stays_in_weekend_nights": {"default": 0, "dtype": int},
    "stays_in_week_nights": {"default": 0, "dtype": int},
    "total_nights": {"default": 0, "dtype": int},

    # метрики
    "lead_time": {"default": 0, "dtype": int},
    "booking_changes": {"default": 0, "dtype": int},
    "adr": {"default": 0.0, "dtype": float},
}

AGGREGATES = {
    "total_guests": ["adults", "children", "babies"],
    "total_nights": ["stays_in_weekend_nights", "stays_in_week_nights"],
}