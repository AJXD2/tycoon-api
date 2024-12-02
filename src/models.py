from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from beanie import Document
import beanie
import src.utils as utils
import re
import typing
from datetime import datetime


class UserEconomyData(BaseModel):
    currency: float = 0
    mult: float = 1


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ip: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    last_seen: datetime = Field(default_factory=lambda: datetime.now())


class UserSecurityData(BaseModel):
    password: str
    disabled: bool = False
    sessions: list[Session] = []

    def check_pw(self, password: str) -> bool:
        return utils.verify_password(password, self.password)


class User(Document):
    username: beanie.Indexed(str, unique=True)  # type: ignore
    economy: UserEconomyData = UserEconomyData()
    security: UserSecurityData

    @beanie.before_event(
        beanie.Insert, beanie.Update, beanie.Replace, beanie.Delete, beanie.Save
    )
    def hash_pw(self):
        if bool(re.match(r"^\$2[ayb]\$.{56}$", self.security.password)):
            return
        self.security.password = utils.hash_password(self.security.password)

    def redacted(self):
        if not self.id:
            raise ValueError(f"Something really fucked up happend: {self.username}")

        return self.RedactedUser(
            id=self.id,
            username=self.username,
            economy=self.economy,
        )

    class RedactedUser(BaseModel):
        id: beanie.PydanticObjectId
        username: str
        economy: UserEconomyData

    class Settings:
        name = "users"


# FastAPI models


class Token(BaseModel):
    access_token: str
    token_type: str


ResType = typing.TypeVar("ResType")


class Response[ResType](BaseModel):
    message: str
    data: ResType


class ListResponse[ResType](BaseModel):
    message: str
    data: list[ResType]


# Premade Types
type UserResponse = Response[User.RedactedUser]
