import os

from sqlalchemy import select
from .database import SessionLocal
from .models import Roles, Users
from passlib.context import CryptContext


# openssl rand -hex 32
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_initial_roles():
    db = SessionLocal()

    try:
        roles = ["admin", "manager", "teacher", "student"]

        for role_name in roles:
            role = db.execute(
                select(Roles).where(Roles.name == role_name)
            ).scalar_one_or_none()

            if role is None:
                db.add(Roles(name=role_name))

        db.commit()

    finally:
        db.close()


def create_admin_user():
    try:
        db = SessionLocal()

        row = db.execute(
            select(Users).where(Users.username == "admin")
        ).scalar_one_or_none()

        if row is not None:
            return

        create_user_model = Users(
            email="admin@gmail.com",
            username="admin",
            first_name="admin_firstname",
            last_name="admin_lastname",
            role_id=1,
            hashed_password=bcrypt_context.hash("admin1234"),
        )

        db.add(create_user_model)
        db.commit()
        db.close()
    except BaseException as e:
        print(
            "--------------------------------------------------------------------------------------------------------"
        )
        print(type(e).__name__)
        print(e)


def verify_admin(password, hashed_password):
    if not bcrypt_context.verify(password, hashed_password):
        return False
    return True
