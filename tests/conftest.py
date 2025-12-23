import os


def _set_default(var: str, value: str) -> None:
    os.environ.setdefault(var, value)

_set_default("ENV", "test")

# DatabaseConfig (env_prefix="DB_")
_set_default("DB_USER", "postgres")
_set_default("DB_PASSWORD", "postgres")
_set_default("DB_NAME", "test")
_set_default("DB_HOST", "localhost")
_set_default("DB_PORT", "5432")

# JWT
_set_default("JWT_SECRET_KEY", "test-secret")
_set_default("JWT_HASH_ALGORITHM", "HS256")

# Redis
_set_default("REDIS_HOST", "localhost")
_set_default("REDIS_PORT", "6379")