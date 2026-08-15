from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from models import UserType, BookingStatus, PaymentStatus
from db import get_db

# USER SCHEMAS
class UserBase(BaseModel):
    name: str
    email: EmailStr
    service_type: Optional[str] = None
    city: Optional[str] = None
    rating: Optional[int] = None
    usertype: UserType

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    service_type: Optional[str] = None
    city: Optional[str] = None
    rating: Optional[int] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# BOOKING SCHEMAS
class BookingBase(BaseModel):
    customer_id: int
    provider_id: int
    booking_date: datetime
    service_amount: float
    status:BookingStatus


class BookingCreate(BookingBase):
    pass


class BookingUpdateStatus(BaseModel):
    status: BookingStatus


class BookingResponse(BookingBase):
    id: int
    status: BookingStatus

    class Config:
        orm_mode = True

# PAYMENT SCHEMAS
class PaymentBase(BaseModel):
    booking_id: int
    payment_method: str
    paid_amount: float


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    payment_status: PaymentStatus

    class Config:
        orm_mode = True

#RATING schemas

# Base schema (common fields)
class RatingBase(BaseModel):
    provider_id: int
    customer_id: int
    rating: int
    review: str | None = None


# Schema for creating rating
class RatingCreate(RatingBase):
    pass


# Schema for returning rating data
class RatingResponse(RatingBase):
    id: int

    class Config:
        from_attributes = True

class LoginHistory(BaseModel):
    username:str
    password:str

class PhoneRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str

    