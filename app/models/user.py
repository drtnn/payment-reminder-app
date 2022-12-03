from dataclasses import dataclass, field

from sqlalchemy import Column, String, Integer
from sqlalchemy_utils.types.choice import ChoiceType

from app.models.base import Model


@Model.mapped
@dataclass
class User:
    __tablename__ = "user"
    __sa_dataclass_metadata_key__ = "sa"

    RUSSIAN = "ru"
    ENGLISH = "en"

    LANGUAGE_TYPES = [
        (RUSSIAN, "Russian"),
        (ENGLISH, "English")
    ]

    id: int = field(metadata={"sa": Column(Integer, primary_key=True)})
    username: str = field(metadata={"sa": Column(String(255), nullable=True, index=True)})
    full_name: str = field(metadata={"sa": Column(String(255), nullable=False)})
    language: str = field(metadata={"sa": Column(ChoiceType(LANGUAGE_TYPES, impl=String(2)), nullable=False)})
