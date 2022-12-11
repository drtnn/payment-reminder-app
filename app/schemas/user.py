from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.base import IdentifiableSchema


class UserUpdateRequestSchema(BaseModel):
    username: Optional[str] = Field(title="Username", max_length=255)
    full_name: str = Field(title="Full Name", max_length=255)
    language: Literal["ru", "en"] = Field(title="Language", default="ru")


class UserSchema(UserUpdateRequestSchema, IdentifiableSchema):
    pass
