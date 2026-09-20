import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    UPLOAD_DIR = os.getenv("UPLOAD_DIR")
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES = os.getenv("JWT_EXPIRE_MINUTES")

settings = Settings()
