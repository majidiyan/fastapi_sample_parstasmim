from fastapi import APIRouter, Depends, HTTPException, Path, Request

from ..models import ClassUser, Classrooms, Users
from ..database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user
from ..utils.logger import log_api_call

router = APIRouter(prefix="/user_in_class", tags=["Assign User To Class"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class AssignRequest(BaseModel):
    user_id: int = Field(gt=0)
    class_id: int = Field(gt=0)


@router.post("/", status_code=status.HTTP_201_CREATED)
@log_api_call
def register_user_in_class(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    assign_request: AssignRequest,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    classuser_model = ClassUser(**assign_request.dict())

    """Check if user_id exists"""
    user_row = db.query(Users).get(classuser_model.user_id)
    if user_row is None:
        raise HTTPException(status_code=404, detail="User Not Found!")

    """Check if class_id exists"""
    class_row = db.query(Classrooms).get(classuser_model.class_id)
    if class_row is None:
        raise HTTPException(status_code=404, detail="Class Not Found!")

    """ Check if has free postsition in classroom """
    count = (
        db.query(ClassUser)
        .filter(ClassUser.class_id == classuser_model.class_id)
        .count()
    )

    class_row = db.query(Classrooms).get(classuser_model.class_id)
    if class_row.capacity <= count:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Capacity is full."
        )

    """ Check if the user is already in the classroom """
    count = (
        db.query(ClassUser)
        .filter(ClassUser.class_id == classuser_model.class_id)
        .filter(ClassUser.user_id == classuser_model.user_id)
        .count()
    )
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user is already in this classroom.",
        )

    db.add(classuser_model)
    db.commit()


@router.delete("/{user_id}/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_api_call
def remove_user_from_class(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    user_id: int = Path(gt=0),
    class_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    assign_model = (
        db.query(ClassUser)
        .filter(ClassUser.class_id == class_id)
        .filter(ClassUser.user_id == user_id)
        .first()
    )
    if assign_model is None:
        raise HTTPException(status_code=404, detail="Not Found!")

    db.query(ClassUser).filter(ClassUser.class_id == class_id).filter(
        ClassUser.user_id == user_id
    ).delete()
    db.commit()
