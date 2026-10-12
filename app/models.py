# pip install alembic
# alembic init alembic
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func


class Roles(Base):
    __tablename__ = "parstasmim_project1_roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class Users(Base):
    __tablename__ = "parstasmim_project1_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("parstasmim_project1_roles.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Classrooms(Base):
    __tablename__ = "parstasmim_project1_classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    capacity = Column(Integer)


class ClassUser(Base):
    __tablename__ = "parstasmim_project1_class_user"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("parstasmim_project1_users.id"), index=True)
    class_id = Column(
        Integer, ForeignKey("parstasmim_project1_classrooms.id"), index=True
    )


class Logs(Base):
    __tablename__ = "parstasmim_project1_logs"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String)
    device = Column(String)
    method_name = Column(String)
    endpoint = Column(String)
    username = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
