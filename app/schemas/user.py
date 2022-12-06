from pydantic import BaseModel, Field

from app.models import User


class UserSchema(BaseModel):
    id: int = Field(title="Telegram User Id", readonly=True)
    username: str = Field(title="Telegram User Username")
    full_name: str = Field(title="Telegram User Full Name")
    language: User.LANGUAGE_TYPES = Field(title="Telegram User Language")


class UserCreateSchema(BaseModel):
    id: int = Field(title="Telegram User Id")
