from fastapi import APIRouter
from starlette import status

from auth_service.api.dependencies import UoWDep, AuthPrincipalDep
from auth_service.schemas.hotel import HotelShow, HotelCreate
from auth_service.use_cases.registration import register_hotel_with_owner

from shared.errors import register_errors, AuthorizationError

router = APIRouter()


@router.post(
    "/register",
    response_model=HotelShow,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация отеля в системе",
)
@register_errors(AuthorizationError)
async def register_hotel_endpoint(
        data: HotelCreate,
        principal: AuthPrincipalDep,
        uow: UoWDep,
):
    return await register_hotel_with_owner(
        uow=uow,
        user_id=principal.user_id,
        hotel_data=data
    )
