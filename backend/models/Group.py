from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from bson import ObjectId
from enum import Enum

class GroupType(str, Enum):
    seed = "seed"      # available to everyone, created by admin
    custom = "custom"  # user created



class Group(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    grp_type: GroupType = Field(default=GroupType.custom)
    name: str = Field(..., description="The name of the group")
    description: str = Field(..., description="A brief description of the group")
    characters: Optional[list[str]] = Field(default=[], description="A list of character IDs belonging to the group")
    created_by: str = Field(..., description="The ID of the user who created the group")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
     
    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        if "characters" in data:
            data["characters"] = [ObjectId(char_id) for char_id in data["characters"]]

        if "created_by" in data:
            data["created_by"] = ObjectId(data["created_by"])
        
        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        if doc.get("characters"):
            doc["characters"] = [str(char_id) for char_id in doc["characters"]]

        if doc.get("created_by"):
            doc["created_by"] = str(doc["created_by"])

        return cls(**doc)

    
class GroupCreate(BaseModel):
    name: str = Field(..., description="The name of the group")
    description: str = Field(..., description="A brief description of the group")
    

  

class SeedGroupCreate(BaseModel):
    name: str
    description: str
    admin_key: str   # simple secret key to protect seed creation