from fastapi import APIRouter
from starlette import status

from auth_service.api.dependencies import UoWDep
from auth_service.schemas.user import UserShow, UserCreate
from auth_service.use_cases.registration import register_user

from shared.errors import register_errors, ConflictError

router = APIRouter()


@router.post(
    "/register",
    response_model=UserShow,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя в системе",
)
@register_errors(ConflictError)
async def register_user_endpoint(
        data: UserCreate,
        uow: UoWDep,
):
    return await register_user(uow=uow, data=data)
