from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import pymongo.errors
from src.utils import create_access_token
import src.models as models
import src.dependencies as deps
import pymongo
from datetime import datetime
import structlog

router = APIRouter(prefix="/auth", tags=["auth"])

logger = structlog.get_logger("tycoon-api")


@router.post("/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> models.Token:
    try:
        # Check if user exists
        ret_user = await models.User.find(
            {"username": form_data.username}
        ).first_or_none()
        if not ret_user:
            logger.info(
                "login-attempt-fail", username=form_data.username, reason="not-found"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Verify password
        if not ret_user.security.check_pw(form_data.password):
            logger.info(
                "login-attempt-fail",
                username=form_data.username,
                reason="invalid-password",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Check for client IP
        if not request.client:
            logger.info(
                "login-attempt-fail", username=form_data.username, reason="no-client-ip"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine client IP.",
            )

        # Create a new session
        session = models.Session(ip=request.client.host, created_at=datetime.now())
        if not ret_user.security.sessions:
            ret_user.security.sessions = []
        ret_user.security.sessions.append(session)

        # Save user with session
        await ret_user.save()

        # Generate token
        payload = {"sub": form_data.username, "session_id": str(session.id)}
        access_token = create_access_token(data=payload)
        logger.info("login-success", user=str(ret_user.id))
        return models.Token(access_token=access_token, token_type="bearer")

    except HTTPException as e:
        # Explicitly let FastAPI handle the raised HTTPException
        raise e
    except Exception as e:
        logger.error("Unexpected error during login", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> models.UserResponse:
    try:
        new_user = models.User(
            username=form_data.username,
            security=models.UserSecurityData(password=form_data.password),
        )
        await new_user.insert()

        logger.info("User registered successfully", username=new_user.username)
        return models.Response(
            message="User created successfully!", data=new_user.redacted()
        )
    except pymongo.errors.DuplicateKeyError:
        logger.info("register-fail", username=form_data.username, reason="duplicate")
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User exists with that username"
        )
    except Exception as e:
        logger.error("Unexpected error during registration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unknown error occoured. Please contact @ajxd2",
        )


@router.get("/me")
async def me(
    user: models.User = Depends(deps.get_current_user),
) -> models.UserResponse:
    return models.Response(
        message="User fetched successfully!",
        data=user.redacted(),
    )
