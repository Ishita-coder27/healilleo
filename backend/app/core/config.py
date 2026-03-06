from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:str = "postgresql://hellio_user:hellio123@localhost:5432/hellio_db"


settings = Settings()
