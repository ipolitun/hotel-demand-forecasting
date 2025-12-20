from auth_service.schemas.hotel import HotelCreate
from auth_service.repositories.hotel import IHotelRepository
from auth_service.utils.api_key import generate_api_key

from shared.db_models import Hotel
from shared.errors import NotFoundError


class HotelService:
    def __init__(self, hotel_repo: IHotelRepository):
        self._hotel_repo = hotel_repo

    async def register(self, hotel_data: HotelCreate) -> Hotel:
        api_key = await self._generate_unique_api_key()
        hotel = await self._hotel_repo.create(
            name=hotel_data.name,
            is_city_hotel=hotel_data.is_city_hotel,
            api_key=api_key,
        )
        return hotel

    async def regenerate_api_key(self, hotel_id: int) -> str:
        await self._require_hotel(hotel_id)

        new_key = await self._generate_unique_api_key()
        await self._hotel_repo.update_api_key(hotel_id, new_key)
        return new_key

    async def _generate_unique_api_key(self, max_attempts=5) -> str:
        for _ in range(max_attempts):
            candidate = generate_api_key()
            if not await self._hotel_repo.exists_by_api_key(candidate):
                return candidate
        raise RuntimeError("Failed to generate unique API key after multiple attempts")

    async def _require_hotel(self, hotel_id: int) -> Hotel:
        hotel = await self._hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError("Hotel not found")
        return hotel
