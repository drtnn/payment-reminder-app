from dataclasses import field
from typing import Optional

from sqlalchemy import Column, String, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_utils import CurrencyType, PhoneNumberType

from app.models.base import model, IdentifiableMixin, TimestampableMixin
from app.models.reminder import Reminder
from app.models.user import User


@model()
class Payment(IdentifiableMixin):
    sum: str = field(metadata={"sa": Column(Float, nullable=False)})
    bank: str = field(metadata={"sa": Column(String(32), nullable=False)})
    currency: str = field(metadata={"sa": Column(CurrencyType, nullable=False)})

    phone_number: Optional[str] = field(default=None, metadata={"sa": Column(PhoneNumberType())})
    card_number: Optional[str] = field(default=None, metadata={"sa": Column(String(20))})


@model()
class InterUserPayment(IdentifiableMixin, TimestampableMixin):
    title: str = field(metadata={"sa": Column(String(255), nullable=False, index=True)})
    from_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    to_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    payment_id: int = field(metadata={"sa": Column(ForeignKey("payment.id", ondelete="CASCADE"))})
    reminder_id: int = field(metadata={"sa": Column(ForeignKey("reminder.id", ondelete="CASCADE"))})

    completed: bool = field(default=False, metadata={"sa": Column(Boolean, default=False, nullable=False)})

    from_user: User = relationship(User, foreign_keys=[from_user_id.metadata["sa"]])  # type: ignore
    to_user: User = relationship(User, foreign_keys=[to_user_id.metadata["sa"]])  # type: ignore
    payment: Payment = relationship(Payment, foreign_keys=[payment_id.metadata["sa"]])  # type: ignore
    reminder: Reminder = relationship(Reminder, foreign_keys=[reminder_id.metadata["sa"]])  # type: ignore
