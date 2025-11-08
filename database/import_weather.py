"""
Импорт погодных данных из Meteostat в таблицу Weather.
Загружает данные по всем городам, связанным с отелями,
только за отсутствующие даты в заданном периоде.
"""

from datetime import datetime
from meteostat import Point, Daily, Stations
from sqlalchemy.orm import Session

from shared.db import get_sync_session
from shared.models import City, Weather, Hotel


def fetch_weather_for_city(city: City, start: datetime, end: datetime, existing_set: set) -> list[Weather]:
    """Загружает и возвращает новые погодные записи для конкретного города."""
    lat = float(city.latitude)
    lon = float(city.longitude)
    point = Point(lat, lon)

    # Поиск ближайшей метеостанции с дневными данными
    stations = Stations().nearby(lat, lon).inventory("daily")
    station = stations.fetch(1)

    if station.empty:
        print(f"Нет подходящих станций для {city.name}")
        return []

    station_id = station.index[0]
    station_name = station.iloc[0]["name"]
    print(f"📡 Загружаем для: {city.name} → {station_id} ({station_name})")

    df = Daily(point, start, end).fetch().reset_index()
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
                temp_avg=row.get("tavg"),
                precipitation=row.get("prcp"),
                wind_speed=row.get("wspd"),
                weather_desc="",  # Meteostat не всегда содержит описания
            )
        )

    return new_records


def load_weather_data(start: datetime, end: datetime, db: Session) -> int:
    """Загружает погодные данные для всех городов, связанных с отелями."""
    cities = db.query(City).join(Hotel).distinct().all()
    if not cities:
        print("В базе нет городов, связанных с отелями.")
        return 0

    # Уже существующие (city_id, day)
    existing = (
        db.query(Weather.city_id, Weather.day)
        .filter(Weather.day.between(start.date(), end.date()))
        .all()
    )
    existing_set = {(city_id, day) for city_id, day in existing}

    total_records: list[Weather] = []
    for city in cities:
        total_records.extend(fetch_weather_for_city(city, start, end, existing_set))

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

    with get_sync_session() as db:
        count = load_weather_data(start, end, db)
        print(f"Импорт завершён: добавлено {count} записей.")


if __name__ == "__main__":
    main()
