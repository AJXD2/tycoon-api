from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
import pymongo.errors
from src.utils import create_access_token
import src.models as models
import src.dependencies as deps
import pymongo
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> models.Token | models.ResponseError:
    ret_user = await models.User.find({"username": form_data.username}).first_or_none()

    if not ret_user:
        return models.ResponseError(message="Invalid username or password")

    if not ret_user.security.check_pw(form_data.password):
        return models.ResponseError(message="Invalid username or password")

    if not request.client:
        return models.ResponseError(message="Unable to determine client IP.")

    session = models.Session(ip=request.client.host, created_at=datetime.now())
    ret_user.security.sessions.append(session)
    await ret_user.save()

    payload = {"sub": form_data.username, "session_id": str(session.id)}
    access_token = create_access_token(data=payload)

    return models.Token(access_token=access_token, token_type="bearer")


@router.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> models.UserResponse | models.ResponseError:
    new_user = models.User(
        username=form_data.username,
        security=models.UserSecurityData(password=form_data.password),
    )
    try:
        await new_user.insert()
    except pymongo.errors.DuplicateKeyError:
        return models.ResponseError(message="Username already exists")
    except Exception:
        return models.ResponseError(message="Internal server error")
    return models.Response[models.User.RedactedUser](
        message="User created successfully!", data=new_user.redacted()
    )


@router.get("/me")
async def me(
    user: models.User = Depends(deps.get_current_user),
) -> models.UserResponse | models.ResponseError:
    return models.Response(
        message="User fetched successfully!",
        data=user.redacted(),
    )
