import os
from dotenv import load_dotenv

load_dotenv()

ROUTER_SERVICE_URL = os.getenv("ROUTER_SERVICE_URL", "http://router:8000")

MAX_DATA_DATE = os.getenv("MAX_DATA_DATE", "2017-05-10")