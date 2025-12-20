from auth_service.repositories.user_hotel import IUserHotelRepository
from auth_service.schemas.roles import UserRole

from shared.db_models import UserHotel


class UserHotelService:
    def __init__(self, user_hotel_repo: IUserHotelRepository):
        self._repo = user_hotel_repo

    async def assign_user_to_hotel(
            self,
            user_id: int,
            hotel_id: int,
            role: UserRole
    ) -> UserHotel:
        user_hotel = await self._repo.create(user_id=user_id, hotel_id=hotel_id, role=role)
        return user_hotel

    async def change_user_role(
            self,
            user_id: int,
            hotel_id: int,
            new_role: UserRole
    ) -> UserHotel:
        user_hotel = await self._repo.update_role(user_id, hotel_id, new_role)
        return user_hotel
