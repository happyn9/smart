# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    ADMIN_EMAIL: str
    SQLALCHEMY_DATABASE_URL: str
    SENDGRID_API_KEY: str
    FRONTEND_URL: str
    BACKEND_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # permet de ne pas générer d'erreur si des variables sont en plus

settings = Settings()


