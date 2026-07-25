from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional,List,Dict
from bson import ObjectId


class UserCreate(BaseModel):
    """Request body for user registration"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    """Request body for user login"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class User(BaseModel):
    """Model used internally for MongoDB"""

    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    password: str
    # token:Optional[str]
    preferences: Optional[Dict[str, str]] = Field(default_factory=dict)  # grp_id → [preferences]

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return cls(**doc)



