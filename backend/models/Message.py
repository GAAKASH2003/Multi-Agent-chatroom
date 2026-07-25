from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime

class Message(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    sender_id:str
    grp_id:str
    user_id:str
    content:str
    timestamp:datetime
    embedding: Optional[list[float]] = None 
    
    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        if "grp_id" in data and data["grp_id"]:
            data["grp_id"]= ObjectId(data["grp_id"])
            
        if "user_id" in data and data["user_id"]:
            data["user_id"]= ObjectId(data["user_id"])
            
        if "sender_id" in data and data["sender_id"]:
            data["sender_id"]= ObjectId(data["sender_id"])
            
        if "timeStamp" not in data and data["timeStamp"]:
            data["timeStamp"] = datetime.now()

        return data 


    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        if doc.get("sender_id"):
            doc["sender_id"]=str(doc["sender_id"])
            
        if doc.get("user_id"):
            doc["user_id"]=str(doc["user_id"])
            
        if doc.get("grp_id"):
            doc["grp_id"]=str(doc["grp_id"])
        
        return cls(**doc)
    

class MessageCreate(BaseModel):
    sender_id:str
    grp_id:str
    user_id:str
    content:str
    timeStamp:datetime
    embedding: Optional[list[float]] = None
    
    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        if "sender_id" in data and data["sender_id"]:
            data["sender_id"]=ObjectId(data["sender_id"])\
        
        if "grp_id" in data and data["grp_id"]:
            data["grp_id"]=ObjectId(data["grp_id"])
        
        if "user_id" in data and data["user_id"]:
            data["user_id"]=ObjectId(data["user_id"])    

        return data 


    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        if doc.get("sender_id"):
            doc["sender_id"]=str(doc["sender_id"])
        
        return cls(**doc)


class MessageAdd(BaseModel):
    conv_id: str
    grp_id:str
    user_id:str
    sender_id: str
    content: str
    embedding: Optional[list[float]] = None
    
