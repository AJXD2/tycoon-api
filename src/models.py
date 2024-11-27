from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from beanie import Document
import pymongo


class UserEconomyData(BaseModel):
    currency: float = 0
    mult: float = 1


class UserSecurityData(BaseModel):
    password: str
    two_factor: bool = False


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(min_length=3, max_length=20)
    economy: UserEconomyData = UserEconomyData()
    security: UserSecurityData

    class Settings:
        name = "users"
        indexes = [
            [
                ("username", pymongo.TEXT),
            ]
        ]
