from enum import Enum


class SystemRole(Enum):
    user = "user"
    admin = "system_admin"
    support = "support"


class UserRole(Enum):
    owner = "owner"
    manager = "manager"
    viewer = "viewer"