from sqlalchemy.orm import Session
from sqlalchemy import func
from models import UserProfile,Booking,Payment,BookingStatus,UserType,PaymentStatus,Rating,LoginHistory
import services.provider_status
from redis_db import redis_client

# USER OPERATIONS

def create_user(db: Session, user):
    db_user = UserProfile(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session):
    return db.query(UserProfile).all()


def get_user(db: Session, user_id: int):
    return db.query(UserProfile).filter(UserProfile.id == user_id).first()


def delete_user(db: Session, user_id: int):
    db_user = db.query(UserProfile).filter(UserProfile.id == user_id).first()

    if not db_user:
        return None

    # Delete related bookings (both customer & provider)
    db.query(Booking).filter(
        (Booking.customer_id == user_id) |
        (Booking.provider_id == user_id)
    ).delete()

    db.commit()

    db.delete(db_user)
    db.commit()

    return db_user

# BOOKING OPERATIONS
def create_booking(db: Session, booking):

    if booking.customer_id == booking.provider_id:
        return {"message": "Customer and Provider cannot be the same user"}

    db_booking = Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    redis_client.hset("provider_status", booking.provider_id, "BUSY")

    return db_booking


def get_bookings(db: Session):
    return db.query(Booking).all()


def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()


def update_booking_status(db: Session, booking_id: int, status):

    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not db_booking:
        return None

    # update booking status in database
    db_booking.status = status
    db.commit()
    db.refresh(db_booking)

    provider_id = db_booking.provider_id

    # 🔹 Update Redis based on booking status
    if status == BookingStatus.REQUESTED:
        redis_client.hset("provider_status", provider_id, "AVAILABLE")

    elif status == BookingStatus.ACCEPTED:
        redis_client.hset("provider_status", provider_id, "BUSY")

    elif status == BookingStatus.COMPLETED:
        redis_client.hset("provider_status", provider_id, "AVAILABLE")

    return db_booking


def cancel_booking(db: Session, booking_id: int):
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not db_booking:
        return {"message": "Booking not found"}

    if db_booking.status == BookingStatus.CANCELLED:
        return {"message": "Booking already cancelled"}

    db_booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(db_booking)

    return {
        "message": "Booking cancelled successfully",
        "booking": db_booking
    }
# PAYMENT OPERATIONS

def create_payment(db: Session, payment):
    db_payment = Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_payment_by_booking(db: Session, booking_id: int):
    return db.query(Payment).filter(
        Payment.booking_id == booking_id
    ).first()

def update_payment_status(db: Session, payment_id: int, status: PaymentStatus):

    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not db_payment:
        return {"message": "Payment not found"}

    db_payment.payment_status = status
    db.commit()
    db.refresh(db_payment)

    return db_payment

#DASHBOARD OPERATIONS

def get_service_type_counts(db: Session):
    results = db.query(func.lower(UserProfile.service_type),func.count(UserProfile.id)
).filter(
    UserProfile.usertype == UserType.serviceprovider
).group_by(
    func.lower(UserProfile.service_type)
).all()
    return {
        service_type: count
        for service_type, count in results
    }


def get_dashboard_data(db: Session):

    customer_count = db.query(UserProfile).filter(
        UserProfile.usertype == UserType.customer
    ).count()

    provider_count = db.query(UserProfile).filter(
        UserProfile.usertype == UserType.serviceprovider
    ).count()

    booking_count = db.query(Booking).count()

    total_revenue = db.query(
        func.sum(Payment.paid_amount)
    ).filter(
        Payment.payment_status == PaymentStatus.SUCCESS
    ).scalar()

    if total_revenue is None:
        total_revenue = 0

    service_type_counts = get_service_type_counts(db)

    return {
        "total_customers": customer_count,
        "total_service_providers": provider_count,
        "total_bookings": booking_count,
        "total_revenue": float(total_revenue),
        "service_type_counts": service_type_counts
    }

def get_service_revenue(db: Session):

    results = db.query(
        UserProfile.service_type,
        func.sum(Payment.paid_amount)
    ).join(
        Booking, Payment.booking_id == Booking.id
    ).join(
        UserProfile, Booking.provider_id == UserProfile.id
    ).filter(
        Payment.payment_status == PaymentStatus.SUCCESS,
        UserProfile.service_type != None
    ).group_by(
        UserProfile.service_type
    ).all()

    return {
        service_type: float(revenue)
        for service_type, revenue in results
    }
#create rating
def create_rating(db: Session, rating):

    existing_rating = db.query(Rating).filter(
        Rating.customer_id == rating.customer_id
    ).first()

    if existing_rating:
        return {"message": "Rating already submitted for this booking"}

    db_rating = Rating(**rating.dict())

    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)

    return db_rating

def topservices(db: Session):
    result = (
        db.query(
            func.lower(UserProfile.service_type),
            func.count(Booking.id)
        )
        .join(Booking, Booking.provider_id == UserProfile.id)
        .filter(UserProfile.service_type != None)
        .group_by(func.lower(UserProfile.service_type))
        .all()
    )
    return {
        service_type: count
        for service_type, count in result
    }

def get_available_providers(db: Session):

    providers = db.query(
        UserProfile.id,
        UserProfile.name,
        UserProfile.service_type
    ).filter(
        UserProfile.usertype == UserType.serviceprovider
    ).all()

    available_providers = []

    for provider_id, name, service_type in providers:

        status = redis_client.hget("provider_status", provider_id)

        if status is None:
            status = "AVAILABLE"

        if status == "AVAILABLE":

            available_providers.append({
                "provider_id": provider_id,
                "name": name,
                "service_type": service_type,
                "status": status
            })

    return available_providers

from redis_db import redis_client
from models import UserProfile, UserType
from sqlalchemy.orm import Session

def get_busy_providers(db: Session):

    providers = db.query(
        UserProfile.id,
        UserProfile.name,
        UserProfile.service_type
    ).filter(
        UserProfile.usertype == UserType.serviceprovider
    ).all()

    busy_providers = []

    for provider_id, name, service_type in providers:

        status = redis_client.hget("provider_status", provider_id)

        if status == "BUSY":

            busy_providers.append({
                "provider_id": provider_id,
                "name": name,
                "service_type": service_type,
                "status": status
            })

    return busy_providers

def complete_booking(db: Session, booking_id: int):

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        return {"message": "Booking not found"}

    booking.status = BookingStatus.COMPLETED
    db.commit()

    redis_client.hset("provider_status", booking.provider_id, "AVAILABLE")

    return {"message": "Service completed"}

def get_available_providers_by_service(db: Session, service_type: str):

    providers = db.query(
        UserProfile.id,
        UserProfile.name,
        UserProfile.service_type
    ).filter(
        UserProfile.usertype == UserType.serviceprovider,
        UserProfile.service_type == service_type
    ).all()

    available_providers = []

    for provider_id, name, service in providers:

        status = redis_client.hget("provider_status", provider_id)

        if status is None or status == "AVAILABLE":

            available_providers.append({
                "provider_id": provider_id,
                "name": name,
                "service_type": service,
                "status": "AVAILABLE"
            })

    return available_providers

def get_ratings(db: Session):
    ratings = db.query(
        UserProfile.name,
        UserProfile.service_type,
        Rating.rating,
        Rating.review
    ).join(
        UserProfile, Rating.provider_id == UserProfile.id
    ).all()

    return [
        {
            "provider_name": r[0],
            "service_type": r[1],
            "rating": r[2],
            "review":r[3]
        }
        for r in ratings
    ]

def login_info(db: Session, user):
    login_record = LoginHistory(
        username=user.username,
        password=user.password
    )

    db.add(login_record)
    db.commit()
    db.refresh(login_record)

    return login_record