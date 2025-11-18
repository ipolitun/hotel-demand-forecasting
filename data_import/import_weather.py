"""
Импорт погодных данных из Meteostat в таблицу Weather.
Загружает данные по всем городам, связанным с отелями,
только за отсутствующие даты в заданном периоде.
"""

from datetime import datetime
import pandas as pd
from meteostat import Point, Daily, Stations
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.db_models import City, Weather, Hotel


def safe(value):
    """Преобразует pd.NA / NaN → None для корректной вставки в PostgreSQL."""
    if value is None or pd.isna(value):
        return None
    return value


def fetch_weather_for_city(city: City, start: datetime, end: datetime, existing_set: set) -> list[Weather]:
    """Загружает и возвращает новые погодные записи для конкретного города."""
    lat = float(city.latitude)
    lon = float(city.longitude)
    point = Point(lat, lon)

    # Поиск ближайшей метеостанции
    stations = Stations().nearby(lat, lon).inventory("daily")
    station = stations.fetch(1)

    if station.empty:
        print(f"Нет подходящих станций для {city.name}")
        return []

    station_id = station.index[0]
    station_name = station.iloc[0]["name"]
    print(f"📡 Загружаем для: {city.name} → {station_id} ({station_name})")

    df = Daily(point, start, end).fetch()

    if df.empty:
        print(f"Нет данных Meteostat для диапазона по {city.name}")
        return []

    df = df.reset_index()

    new_records = []

    for _, row in df.iterrows():
        day = row["time"].date()
        key = (city.id, day)

        if key in existing_set:
            continue

        new_records.append(
            Weather(
                city_id=city.id,
                day=day,
                temp_avg=safe(row.get("tavg")),
                precipitation=safe(row.get("prcp")),
                wind_speed=safe(row.get("wspd")),
                weather_desc=safe(row.get("weather_desc", "")) or "",
            )
        )

    return new_records


def load_weather_data(start: datetime, end: datetime, db: Session) -> int:
    """Загружает погодные данные для всех городов."""
    cities = (
        db.query(City)
        .join(Hotel, City.id == Hotel.city_id)
        .distinct()
        .all()
    )

    if not cities:
        print("В базе нет городов, связанных с отелями.")
        return 0

    # Существующие записи
    existing = (
        db.query(Weather.city_id, Weather.day)
        .filter(Weather.day.between(start.date(), end.date()))
        .all()
    )
    existing_set = {(city_id, day) for city_id, day in existing}

    total_records: list[Weather] = []

    for city in cities:
        total_records.extend(
            fetch_weather_for_city(city, start, end, existing_set)
        )

    if not total_records:
        print("Новых записей погоды не найдено.")
        return 0

    db.add_all(total_records)
    db.commit()

    print(f"Загружено {len(total_records)} строк погоды.")
    return len(total_records)


def main() -> None:
    """Точка входа: загрузка исторических погодных данных 2015–2017 гг."""
    start = datetime(2015, 7, 1)
    end = datetime(2017, 8, 31)

    with SessionLocal() as session:
        count = load_weather_data(start, end, session)
        print(f"Импорт завершён: добавлено {count} записей.")


if __name__ == "__main__":
    main()
