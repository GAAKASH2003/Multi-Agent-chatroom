# models/session.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional,List
from bson import ObjectId
from datetime import datetime


class ChatSession(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    grp_id: str
    title: Optional[str] = None
    memory_summary: Optional[str] = None
    conv_ids: List[str] = Field(default_factory=list)  # ← track convs in session
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(populate_by_name=True)

    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"]:
            data["_id"] = ObjectId(data["_id"])
        if "user_id" in data:
            data["user_id"] = ObjectId(data["user_id"])
        if "grp_id" in data:
            data["grp_id"] = ObjectId(data["grp_id"])
        if "conv_ids" in data:
            data["conv_ids"] = [ObjectId(c) for c in data["conv_ids"]]
        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None
        doc = dict(doc)
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        if doc.get("user_id"):
            doc["user_id"] = str(doc["user_id"])
        if doc.get("grp_id"):
            doc["grp_id"] = str(doc["grp_id"])
        if doc.get("conv_ids"):
            doc["conv_ids"] = [str(c) for c in doc["conv_ids"]]
        return cls(**doc)