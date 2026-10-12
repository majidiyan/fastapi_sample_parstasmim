from functools import wraps
import inspect
from fastapi import Request
from ..database import SessionLocal
from ..models import Logs


def log_api_call(func):
    signature = inspect.signature(func)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        request: Request = kwargs.get("request")

        user = bound.arguments.get("user")

       

        if user and request:
            db = SessionLocal()
            function_name = func.__name__
            prefix = request.url.path
            ip = request.client.host
            method_name = request.method
            device = request.headers.get("user-agent")
            username = user.get("username")
            endpoint = prefix + function_name
            data = {
                "ip": ip,
                "device": device,
                "method_name": method_name,
                "endpoint": endpoint,
                "username": username,
            }
            log = Logs(**data)
            db.add(log)
            db.commit()
            db.close()



        result = func(*args, **kwargs)

        if inspect.isawaitable(result):
            """For async decorators"""
            return await result

        """For normal decorators"""
        return result

    return wrapper
