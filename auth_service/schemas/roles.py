from enum import Enum


class SystemRole(str, Enum):
    ADMIN = "admin"
    SUPPORT = "support"
    USER = "user"


class UserRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"
