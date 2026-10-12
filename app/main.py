from fastapi import FastAPI
from .bootstrap import create_initial_roles, create_admin_user
from . import models
from .database import engine
from .routers import auth, roles, classroom, assign_class_to_user ,  logs


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
create_initial_roles()
create_admin_user()

app.include_router(logs.router)
app.include_router(roles.router)
app.include_router(auth.router)
app.include_router(classroom.router)
app.include_router(assign_class_to_user.router)
