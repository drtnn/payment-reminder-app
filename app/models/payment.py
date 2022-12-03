from dataclasses import dataclass, field

from sqlalchemy import Column, String, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy_utils import CurrencyType, PhoneNumberType

from app.models.base import Model
from app.models.reminder import Reminder
from app.models.user import User


@Model.mapped
@dataclass
class Payment:
    __tablename__ = "payment"
    __sa_dataclass_metadata_key__ = "sa"

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True, autoincrement=True)})
    sum: str = field(metadata={"sa": Column(Float, nullable=False)})
    bank: str = field(metadata={"sa": Column(String(32), nullable=False)})
    phone_number: str = field(metadata={"sa": Column(PhoneNumberType())})
    card_number: str = field(metadata={"sa": Column(String(20))})
    currency: str = field(metadata={"sa": Column(CurrencyType, nullable=False)})


@Model.mapped
@dataclass
class InterUserPayment:
    __tablename__ = "inter_user_payment"
    __sa_dataclass_metadata_key__ = "sa"

    id: int = field(init=False, metadata={"sa": Column(Integer, primary_key=True, autoincrement=True)})
    title: str = field(metadata={"sa": Column(String(255), nullable=False, index=True)})
    from_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    to_user_id: int = field(metadata={"sa": Column(ForeignKey("user.id", ondelete="CASCADE"))})
    payment_id: int = field(metadata={"sa": Column(ForeignKey("payment.id", ondelete="CASCADE"))})
    reminder_id: int = field(metadata={"sa": Column(ForeignKey("reminder.id", ondelete="CASCADE"))})

    from_user: User = relationship("User", foreign_keys=[from_user_id])
    to_user: User = relationship("User", foreign_keys=[to_user_id])
    payment: Payment = relationship("Payment", foreign_keys=[payment_id])
    reminder: Reminder = relationship("Reminder", foreign_keys=[reminder_id])
