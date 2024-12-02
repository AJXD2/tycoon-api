from datetime import datetime, timedelta, timezone
import typing
import jwt
from src.settings import settings
import bcrypt
import structlog
import logging
from logging.handlers import RotatingFileHandler


def create_access_token(
    data: dict, expires_delta: typing.Union[timedelta, None] = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> typing.Optional[dict]:
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None


def verify_access_token(token: str):
    payload = decode_access_token(token)
    return payload is not None


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def setup_logging(name: str, dev: bool = False):
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger(name)
    logger.level = logging.INFO
    logger.addHandler(file_handler)

    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
    if dev:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=lambda name: logging.getLogger(name),
    )

    return structlog.get_logger(name)


logger = setup_logging("tycoon-api")
