from auth_service.repositories.unit_of_work import IUnitOfWork
from auth_service.schemas.hotel import HotelCreate, HotelShow
from auth_service.schemas.roles import UserRole
from auth_service.schemas.user import UserCreate, UserShow
from auth_service.services import UserService, HotelService, UserHotelService


async def register_user(
        uow: IUnitOfWork,
        data: UserCreate
) -> UserShow:
    async with uow:
        user_service = UserService(uow.users)

        user = await user_service.register(data)

        await uow.commit()
        return UserShow.model_validate(user)


async def register_hotel_with_owner(
        uow: IUnitOfWork,
        user_id: int,
        hotel_data: HotelCreate
) -> HotelShow:
    async with uow:
        hotel_service = HotelService(uow.hotels)
        users_hotels_service = UserHotelService(uow.users_hotels)

        hotel = await hotel_service.register(hotel_data)

        await users_hotels_service.assign_user_to_hotel(
            user_id=user_id,
            hotel_id=hotel.id,
            role=UserRole.OWNER,
        )

        await uow.commit()
        return HotelShow.model_validate(hotel)
