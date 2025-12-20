from auth_service.repositories.user import IUserRepository
from auth_service.schemas.user import UserCreate, PasswordUpdate
from auth_service.utils.password import hash_password, verify_password

from shared.db_models import User
from shared.errors import AuthorizationError, ConflictError, NotFoundError


class UserService:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def register(self, user_data: UserCreate) -> User:
        if await self._user_repo.exists_by_email(str(user_data.email)):
            raise ConflictError("User already exists")

        hashed_pwd = hash_password(user_data.password)

        user = await self._user_repo.create(
            name=user_data.name,
            surname=user_data.surname,
            email=str(user_data.email),
            hashed_password=hashed_pwd
        )
        return user

    async def change_password(
            self,
            user_id: int,
            pwd_data: PasswordUpdate
    ) -> User:
        user = await self._require_user(user_id)
        self.verify_credentials(user, pwd_data.current_password)

        if verify_password(
                plain_password=pwd_data.new_password,
                hashed_password=user.hashed_password,
        ):
            raise ConflictError("New password must differ from the current password")

        new_hashed_pwd = hash_password(pwd_data.new_password)

        updated_user = await self._user_repo.update_password(user_id, new_hashed_pwd)
        return updated_user

    async def deactivate_self(self, user_id: int) -> User:
        user = await self._require_user(user_id)

        if not user.is_active:
            raise ConflictError("User is already deactivated")

        deactivated_user = await self._user_repo.deactivate(user_id)
        return deactivated_user

    @staticmethod
    def verify_credentials(user: User, plain_password: str) -> None:
        if not user.is_active or not verify_password(
                plain_password=plain_password,
                hashed_password=user.hashed_password
        ):
            raise AuthorizationError("Invalid credentials")

    async def _require_user(self, user_id: int) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user
