from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.utils import decode_access_token
import typing
import src.models as models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> typing.Optional[models.User]:
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    ret_user = await models.User.find(
        models.User.username == payload["sub"]
    ).first_or_none()
    if ret_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return ret_user


async def get_active_session(
    token: str = Depends(oauth2_scheme),
) -> typing.Optional[models.Session]:
    token_payload = decode_access_token(token)

    if token_payload is None:
        return None
    ret_user = await models.User.find(
        models.User.username == token_payload["sub"]
    ).first_or_none()
    if ret_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return next(
        (
            i
            for i in ret_user.security.sessions
            if str(i.id) == token_payload["session_id"]
        ),
        None,
    )
