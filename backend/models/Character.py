from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from bson import ObjectId

class Character(BaseModel): 
    """Pydantic model for Character data validation and serialization"""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., description="The name of the character")
    description: str = Field(..., description="A brief description of the character")
    traits: list[str] = Field(..., description="A list of character traits")
    created_by: str=Field(..., description="user who created the character")
    group:Optional[list[str]]=Field(default=[], description="The group or faction the character belongs to")
    type:str=Field(default="custom", description="The type of the character, default is 'character'")
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        # if "group" in data and data["group"]:
        #     data["group"] = ObjectId(data["group"])

        if "created_by" in data and data["created_by"]:
            data["created_by"]=ObjectId(data["created_by"])
        
        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        # doc["_id"] = str(doc["_id"])
        # if doc.get("group"):
        #     doc["group"] = str(doc["group"])
        if doc.get("group"):
            doc["group"] = [str(g) for g in doc["group"]]
        
        if doc.get("created_by"):
            doc["created_by"]=str(doc["created_by"])
        
        return cls(**doc)


class CharacterCreate(BaseModel):
    """Pydantic model for creating a new character"""
    name: str = Field(..., description="The name of the character")
    description: str = Field(..., description="A brief description of the character")
    traits: list[str] = Field(..., description="A list of character traits")
    type: str = Field(default="custom", description="The type of the character, default is 'character'")
    # group: str = Field(..., description="The group or faction the character belongs to")
   
class CharacterUpdate(BaseModel):
    """Pydantic model for updating an existing character"""
    name: Optional[str] = Field(None, description="The name of the character")
    description: Optional[str] = Field(None, description="A brief description of the character")
    traits: Optional[list[str]] = Field(None, description="A list of character traits")
    created_by:str =Field(..., description="user who created the character")
    
    
class CharacterDelete(BaseModel):
    """Pydantic model for deleting a character"""
    id: str = Field(..., description="The ID of the character to delete")
