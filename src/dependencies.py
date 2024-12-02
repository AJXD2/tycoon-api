from fastapi import Depends, HTTPException, status, Request
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


async def verify_session(request: Request, token: str = Depends(oauth2_scheme)) -> bool:
    # Decode and validate token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    if "sub" not in payload or "session_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is missing required claims: 'sub' and 'session_id'",
        )

    # Fetch user based on the 'sub' claim
    user = await models.User.find(
        models.User.username == payload["sub"]
    ).first_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Validate session
    session = next(
        (s for s in user.security.sessions if str(s.id) == payload["session_id"]), None
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Session not found or invalid"
        )

    # Validate client IP
    if not request.client or session.ip != request.client.host:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Session IP mismatch"
        )

    return True


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
