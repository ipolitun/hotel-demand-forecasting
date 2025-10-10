import os
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")
SCHEDULER_KEY = os.getenv("SCHEDULER_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

if not SCHEDULER_KEY:
    raise RuntimeError("SCHEDULER_KEY is not set in the environment")