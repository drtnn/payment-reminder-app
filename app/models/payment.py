from dataclasses import field

from sqlalchemy import Column, String, ForeignKey, Float, Boolean
from sqlalchemy_utils import CurrencyType, PhoneNumberType

from app.models.base import model, IdentifiableMixin, TimestampableMixin


@model()
class Payment(IdentifiableMixin):
    sum: str = field(metadata={"sa": Column(Float, nullable=False)})
    bank: str = field(metadata={"sa": Column(String(32), nullable=False)})
    phone_number: str = field(metadata={"sa": Column(PhoneNumberType())})
    card_number: str = field(metadata={"sa": Column(String(20))})
    currency: str = field(metadata={"sa": Column(CurrencyType, nullable=False)})


@model()
class InterUserPayment(IdentifiableMixin, TimestampableMixin):
    title: str = field(metadata={"sa": Column(String(255), nullable=False, index=True)})
    from_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    to_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    payment_id: int = field(metadata={"sa": Column(ForeignKey("payment.id", ondelete="CASCADE"))})
    reminder_id: int = field(metadata={"sa": Column(ForeignKey("reminder.id", ondelete="CASCADE"))})
    completed: bool = field(metadata={"sa": Column(Boolean, default=False, nullable=False)})

    # Todo: fix relationships
    # from_user: User = relationship(User, foreign_keys=[from_user_id])
    # to_user: User = relationship(User, foreign_keys=[to_user_id])
    # payment: Payment = relationship(Payment, foreign_keys=[payment_id])
    # reminder: Reminder = relationship(Reminder, foreign_keys=[reminder_id])
