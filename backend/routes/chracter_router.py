from pydantic import BaseModel, Field
from db.dbConnection import get_collection
from models.Character import Character, CharacterCreate
from models.User import User
from routes.auth_router import get_current_user
from typing import Optional, Any
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status


class CharacterResponse(BaseModel):
    id:str
    name: str
    description: str
    traits: list[str]
    created_by: str
    type: Optional[str] = "custom"
    @classmethod
    def model_validate(cls, char_doc: dict) -> "CharacterResponse":
        traits = char_doc.get("traits") or []
        normalized_traits = []
        for val in traits:
            normalized_traits.append(str(val) if isinstance(val, ObjectId) else str(val))
                    
        return cls(
            id=str(char_doc["_id"]),
            name=char_doc["name"],
            description=char_doc["description"],
            traits=normalized_traits,
            created_by=str(char_doc.get("created_by", "")),
            type=char_doc.get("type", "custom")
        )


router = APIRouter(
    prefix="/character",
    tags=["character"],
    responses={404: {"description": "Not found"},200: {"description": "Success"}},
)

def get_characters_collection():
    """Get characters collection (lazy initialization to ensure DB is connected)"""
    return get_collection("characters")

def get_groups_collection():
     return get_collection("groups")

@router.get("/", response_model=list[CharacterResponse])
def list_characters(current_user: User = Depends(get_current_user)):
    character_collection = get_characters_collection()
    characters = list(
    character_collection.find({
        "$or": [
            {"created_by": ObjectId(current_user.id)},
            {"type": "seed"}
        ]
        })
    )
    print(characters)
    return [CharacterResponse.model_validate(char_doc) for char_doc in characters]

@router.post("/", response_model=CharacterResponse)
def create_character(
    character: CharacterCreate,
    current_user: User = Depends(get_current_user)
):
    character_collection = get_characters_collection()
    # groups_collection = get_groups_collection()

    # Check for duplicate character in the same group
    # print(character.group)
    existing_character = character_collection.find_one({
        "name": character.name,
        "created_by": ObjectId(current_user.id)
    })

    
    if existing_character:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character name already exists in this group"
        )

    # Create character document
    character.type="custom"  # Ensure type is set to "custom"
    if current_user.id:
        character_doc = Character(
            **character.model_dump(),
            created_by=current_user.id
        ).to_mongo()
        
    print(character_doc)
    # Validate group exists (if provided)
    # if character_doc.get("group"):
    #     group = groups_collection.find_one({
    #         "_id": character_doc.get("group")
    #     })

    #     if not group:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Group not available"
    #         )

    # Insert character
    print(character_doc.get("group"))
    insert_result = character_collection.insert_one(character_doc)
    # update_result=groups_collection.update_one(
    #     {"_id":character_doc.get("group")},
    #     {
    #         "$push": {
    #             "characters": insert_result.inserted_id
    #         }
    #     }
    # )
    # print(update_result.matched_count)
    # print(update_result.modified_count)
    
    # Retrieve inserted character
    created_character = character_collection.find_one({
        "_id": insert_result.inserted_id
    })

    if not created_character:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create character"
        )

    return CharacterResponse(
        id=str(created_character["_id"]),
        name=created_character["name"],
        description=created_character["description"],
        traits=created_character.get("traits", []),
        created_by=str(created_character["created_by"]),
        type=created_character.get("type", "custom")
    )
    

@router.delete("/{char_id}")
def delete_character(char_id: str, current_user: User = Depends(get_current_user)):
    character_collection = get_characters_collection()
    groups_collection = get_groups_collection()

    char_doc = character_collection.find_one({"_id": ObjectId(char_id)})
    if not char_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    if str(char_doc["created_by"]) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this character")
    
    delete_result = character_collection.delete_one({"_id": ObjectId(char_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete character")
    
    # Remove character from group
    
    if char_doc.get("group"):
        for group_id in char_doc.get("group"):
            groups_collection.update_one(
                {"_id": ObjectId(group_id)},
                {"$pull": {"characters": ObjectId(char_id)}}
            )
    
    return {"detail": "Character deleted successfully"}
    
@router.get("/{char_id}", response_model=CharacterResponse)
def get_character(char_id: str):
    character_collection = get_characters_collection()
    char_doc = character_collection.find_one({"_id": ObjectId(char_id)})
    if not char_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    char_doc["_id"] = str(char_doc["_id"])                  
    return CharacterResponse.model_validate(char_doc)