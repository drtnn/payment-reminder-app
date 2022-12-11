from typing import Optional, Literal

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: int = Field(title="Telegram User Id", readonly=True)
    username: Optional[str] = Field(title="Telegram User Username", max_length=255)
    full_name: str = Field(title="Telegram User Full Name", max_length=255)
    language: Literal["ru", "en"] = Field(title="Telegram User Language", default="ru")


class UserCreateRequestSchema(UserSchema):
    id: int = Field(title="Telegram User Id")
