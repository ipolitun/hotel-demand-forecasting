from auth_service.repositories.unit_of_work import IUnitOfWork
from auth_service.schemas.user import UserCredentials
from auth_service.services import UserService
from auth_service.use_cases._helpers import get_hotels_payload
from auth_service.schemas.auth import HotelPrincipal

from shared.errors import AuthorizationError


async def authenticate(
        credentials: UserCredentials,
        uow: IUnitOfWork,
) -> HotelPrincipal:

    async with uow:
        user = await uow.users.get_by_email(str(credentials.email))
        if not user:
            raise AuthorizationError("Invalid credentials")

        UserService(uow.users).verify_credentials(user, credentials.password)

        hotels = await get_hotels_payload(uow, user.id)

        return HotelPrincipal(
            user_id=user.id,
            system_role=user.system_role,
            hotels=hotels,
        )
