from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy_utils import ChoiceType

from app.models.base import Model


@Model.mapped
@dataclass
class Reminder:
    __tablename__ = "reminder"
    __sa_dataclass_metadata_key__ = "sa"

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    REPEAT_TYPES = [
        (DAILY, DAILY),
        (WEEKLY, WEEKLY),
        (MONTHLY, MONTHLY),
        (YEARLY, YEARLY)
    ]

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True, autoincrement=True)})
    remind_at: datetime = field(metadata={"sa": Column(DateTime, nullable=False)})
    repeat: str = field(metadata={"sa": Column(ChoiceType(REPEAT_TYPES, impl=String(7)))})
