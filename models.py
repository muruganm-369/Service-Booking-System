from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from db import Base
from enum import Enum


class UserType(str, Enum):
    customer = "customer"
    serviceprovider = "serviceprovider"


class BookingStatus(str, Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Rating(str,Enum):
    FIVE="5"
    FOUR="4"
    THREE="3"


class UserProfile(Base):
    __tablename__ = "userprofiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    service_type = Column(String)
    city = Column(String)
    rating = Column(Integer)
    usertype = Column(SQLAlchemyEnum(UserType), nullable=False)

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("userprofiles.id"))
    provider_id = Column(Integer, ForeignKey("userprofiles.id"))
    booking_date = Column(DateTime)
    service_amount = Column(Float)
    status = Column(
        SQLAlchemyEnum(BookingStatus),
        default=BookingStatus.REQUESTED,
        nullable=False
    )

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    payment_method = Column(String)
    payment_status = Column(
        SQLAlchemyEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    paid_amount = Column(Float)

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)

    provider_id = Column(Integer, ForeignKey("userprofiles.id"))
    customer_id = Column(Integer, ForeignKey("userprofiles.id"))

    rating = Column(Integer)
    review = Column(String)
    comment = Column(String)

class LoginHistory(Base):
    __tablename__ = "logindetails"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)