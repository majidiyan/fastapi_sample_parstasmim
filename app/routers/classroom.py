from fastapi import APIRouter, Depends, HTTPException, Path, Request

from ..models import Classrooms as ClassModel, ClassUser, Users
from ..database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user
from ..utils.logger import log_api_call

router = APIRouter(tags=["ClassRoom"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class ClassRequest(BaseModel):
    name: str = Field(min_length=3)
    capacity: int = Field(gt=0, lt=30)


class ClassRequestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    capacity: int | None = Field(default=None, gt=0, lt=30)


@router.get("/classroom", status_code=status.HTTP_200_OK)
@log_api_call
def read_all(request: Request, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    return db.query(ClassModel).all()


@router.get("/classroom/{class_id}", status_code=status.HTTP_200_OK)
@log_api_call
def read_class_by_id(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    row = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    return row


@router.get("/classroom_content/{class_id}", status_code=status.HTTP_200_OK)
@log_api_call
def class_content(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    users = (
        db.query(Users)
        .join(ClassUser, Users.id == ClassUser.user_id)
        .filter(ClassUser.class_id == class_id)
        .all()
    )
    return users


@router.get("/classroom/{class_name}", status_code=status.HTTP_200_OK)
@log_api_call
def read_class_by_name(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_name: str = Path(min_length=3),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    list = db.query(ClassModel).filter(ClassModel.name.ilike(f"%{class_name}%")).all()
    return list


@router.post("/classroom", status_code=status.HTTP_201_CREATED)
@log_api_call
def create_class(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_request: ClassRequest,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    class_model = ClassModel(**class_request.dict())
    db.add(class_model)
    db.commit()


@router.patch("/classroom/{class_id}", status_code=status.HTTP_200_OK)
@log_api_call
def update_class(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_request: ClassRequestUpdate,
    class_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if class_model is None:
        raise HTTPException(status_code=404, detail="Not Found!")

    """ In capacity changes, check if the capacity is not occupied """
    try:
        count = db.query(ClassUser).filter(ClassUser.class_id == class_id).count()

        if class_request.capacity is not None:
            if class_request.capacity < count:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cannot reduce the capacity, it is accupied ",
                )
    except BaseException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if class_request.name is not None:
        class_model.name = class_request.name

    if class_request.capacity is not None:
        class_model.capacity = class_request.capacity

    db.add(class_model)
    db.commit()
    row = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    return row


@router.delete("/classroom/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_api_call
def delete_class(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    class_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    class_model = db.query(ClassModel).filter(ClassModel.id == class_id).first()
    if class_model is None:
        raise HTTPException(status_code=404, detail="Not Found!")

    """If class in not empty"""
    count = db.query(ClassUser).filter(ClassUser.class_id == class_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cannot delete the class, it has users in",
        )

    db.query(ClassModel).filter(ClassModel.id == class_id).delete()
    db.commit()
