import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    UPLOAD_DIR = os.getenv("UPLOAD_DIR")
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

settings = Settings()
