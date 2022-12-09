from dataclasses import field
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String

from app.models.base import model, IdentifiableMixin


@model()
class Reminder(IdentifiableMixin):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    remind_at: datetime = field(metadata={"sa": Column(DateTime, nullable=False)})

    repeat: Optional[str] = field(default=None, metadata={"sa": Column(String(7))})
