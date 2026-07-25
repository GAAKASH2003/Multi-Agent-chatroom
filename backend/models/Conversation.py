from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class Conversation(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    query: str
    messages: list[str] = []
    group: str
    seq_num: int
    user_id: str
    summary: Optional[str] =None
    embedding: Optional[list[float]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(populate_by_name=True)

    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data and data["_id"]:
            data["_id"] = ObjectId(data["_id"])

        if "group" in data and data["group"]:
            data["group"] = ObjectId(data["group"])

        if "user_id" in data and data["user_id"]:
            data["user_id"] = ObjectId(data["user_id"])

        # messages are message ObjectIds
        if "messages" in data:
            data["messages"] = [ObjectId(m) for m in data["messages"]]

        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None
        doc = dict(doc)
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        if doc.get("group"):
            doc["group"] = str(doc["group"])
        if doc.get("user_id"):
            doc["user_id"] = str(doc["user_id"])
        if doc.get("messages"):
            doc["messages"] = [str(m) for m in doc["messages"]]
        return cls(**doc)   
    
class CharacterResponse(BaseModel):
    cid: str        
    response: str   
    grp_id:str
    user_id:str
    
class ConversationCreate(BaseModel):
    query: str
    group_id: str
    characterResponses: list[CharacterResponse]

     

