# pip install passlib
# pip install bcrypt==3.1.6
# pip install python-multipart
# pip install "python-jose[cryptography]"

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from ..bootstrap import SECRET_KEY, ALGORITHM
from pydantic import BaseModel, EmailStr
from ..models import Users, Roles
from ..database import SessionLocal
from ..utils.logger import log_api_call
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from datetime import timedelta, datetime

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


router = APIRouter(prefix="/auth", tags=["Users"])


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_role(db: db_dependency, username: str):
    row = (
        db.query(Users, Roles)
        .outerjoin(Roles, Users.role_id == Roles.id)
        .filter(Users.username == username)
        .first()
    )
    return row[1].name


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Couldn't validate user.",
            )
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Couldn't validate user."
        )


user_dependency = Annotated[dict, Depends(get_current_user)]


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role_id: int


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    role_id: int | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
@log_api_call
def create_user(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    create_user_request: CreateUserRequest,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    user_role_name = get_user_role(db, user.get("username"))
    if user_role_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed form_data none admin user",
        )

    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role_id=create_user_request.role_id,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
    )

    db.add(create_user_model)
    db.commit()


@router.get("/users_by_role/{role_id}", status_code=status.HTTP_200_OK)
@log_api_call
def read_users_by_role(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    role_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    list_users = (
        db.query(Users)
        .filter(Users.role_id == role_id)
        .order_by(Users.created_at.desc())
        .all()
    )
    return list_users


@router.get("/users_by_username/{username}", status_code=status.HTTP_200_OK)
@log_api_call
def get_user_by_username(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    username: str = Path(min_length=3, max_length=50),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    row_users = db.query(Users).filter(Users.username == username).first()
    return row_users


@router.get("/users_by_email/{email}", status_code=status.HTTP_200_OK)
@log_api_call
def get_user_by_email(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    email: EmailStr = Path(),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    row_users = db.query(Users).filter(Users.email == email).first()
    return row_users


@router.post("/token", response_model=Token)
@log_api_call
def login_for_access_token(
    request: Request,
    db: db_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Couldn't validate user."
        )
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
@router.patch("/update_user/{username}", status_code=status.HTTP_200_OK)
@log_api_call
def update_user(
    request: Request,
    user: user_dependency,
    db: db_dependency,
    updateuser_request: UpdateUserRequest,
    username: str,
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    user_role_name = get_user_role(db, user.get("username"))

    if user_role_name != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed form_data none admin user",
        )

    user_row = db.query(Users).filter(Users.username == username).first()
    if user_row is None:
        raise HTTPException(status_code=404, detail="Not Found!")

   

    if updateuser_request.first_name is not None:
        user_row.first_name = updateuser_request.first_name

    if updateuser_request.last_name is not None:
        user_row.last_name = updateuser_request.last_name

    if updateuser_request.email is not None:
        user_row.email = updateuser_request.email

    if updateuser_request.role_id is not None:
        user_row.role_id = updateuser_request.role_id

    if updateuser_request.password is not None:
        user_row.hashed_password = bcrypt_context.hash(updateuser_request.password)

    db.add(user_row)
    db.commit()
    row = db.query(Users).filter(Users.username == username).first()
    return row
