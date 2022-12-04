from dataclasses import field
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy_utils import ChoiceType

from app.models.base import model, IdentifiableMixin


@model()
class Reminder(IdentifiableMixin):
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

    remind_at: datetime = field(metadata={"sa": Column(DateTime, nullable=False)})
    repeat: str = field(metadata={"sa": Column(ChoiceType(REPEAT_TYPES, impl=String(7)))})
