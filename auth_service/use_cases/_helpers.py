from auth_service.repositories.unit_of_work import IUnitOfWork
from auth_service.schemas.hotel import HotelAccessPayload


async def get_hotels_payload(uow: IUnitOfWork, user_id: int) -> list[HotelAccessPayload]:
    user_hotels = await uow.users_hotels.get_hotels_by_user(user_id)
    return [
        HotelAccessPayload(
            id=uh.hotel_id,
            user_role=uh.role
        )
        for uh in user_hotels
    ]
