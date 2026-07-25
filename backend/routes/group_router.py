from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Any
from pydantic import BaseModel, Field
from db.dbConnection import get_collection
from models.Group import Group, GroupCreate, SeedGroupCreate,GroupType
from models.User import User
from routes.auth_router import get_current_user
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import DESCENDING
import dotenv
import os

loaded = dotenv.load_dotenv()

ADMIN_KEY = os.getenv("ADMIN_KEY")


class PreferenceAdd(BaseModel):
    grp_id: str
    preference: str

class PreferenceRemove(BaseModel):
    grp_id: str
    preference: str

class GroupResponse(BaseModel):
    id:str
    name: str
    description: str
    characters: list[str]
    created_by: str
    
    @classmethod
    def model_validate(cls, group_doc: dict) -> "GroupResponse":
        characters = group_doc.get("characters", [])
        normalized_characters = []
        for char in characters:
            normalized_characters.append(str(char) if isinstance(char, ObjectId) else str(char))
                
        return cls(
            id=str(group_doc["_id"]),
            name=group_doc["name"],
            description=group_doc["description"],
            characters=normalized_characters,
            created_by=str(group_doc.get("created_by", ""))
        )
    

class GroupListResponse(BaseModel):
    seed_groups: list[GroupResponse]
    custom_groups: list[GroupResponse]
 

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    character_ids: Optional[list[str]] = None

router = APIRouter(
    prefix="/group",
    tags=["group"],
    responses={404: {"description": "Not found"}},
)


def get_groups_collection():
    """Get groups collection (lazy initialization to ensure DB is connected)"""
    return get_collection("groups")

def get_char_collection():
    """Get groups collection (lazy initialization to ensure DB is connected)"""
    return get_collection("characters")

def get_conv_collection():
     return get_collection("conversations")

def get_msgs_collection():
     return get_collection("messages")

def get_users_collection():
    return get_collection("users")

def get_session_collection():
    return get_collection("chatsession")


@router.post("/",response_model=GroupResponse)
def create_group(group: GroupCreate, current_user: User = Depends(get_current_user)):
    group_collection = get_groups_collection()
    if group_collection.find_one({"name": group.name}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name already exists")
    # if group.character_ids and len(group.character_ids) > 5:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A group can have at most 5 characters")
    print(group)
    if current_user.id:
     group_doc = Group(**group.model_dump(), created_by=current_user.id).to_mongo()
    result = group_collection.insert_one(group_doc)
    print("inserted_id =", result.inserted_id)
    print("type =", type(result.inserted_id))
    print("group_doc =", group_doc)
    created_group = group_collection.find_one({"_id": result.inserted_id})
    if not created_group:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create group")
    
    response=GroupResponse(
        id=str(created_group["_id"]),
        name=created_group["name"],
        description=created_group["description"],
        characters=created_group["characters"],
        created_by=str(created_group["created_by"])
    )
    return response



class CharPayload(BaseModel):
    group_id: str
    character_id: str

@router.post("/addCharacter")
def add_character_to_group(payload: CharPayload, current_user: User = Depends(get_current_user)):
    group_collection = get_groups_collection()
    character_collection = get_char_collection()

    group_doc = group_collection.find_one({"_id": ObjectId(payload.group_id)})
    
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    print("group_doc",group_doc.get("created_by"),"current_user.id",current_user.id)
    
    if group_doc.get("created_by") != ObjectId(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this group")

    character_doc = character_collection.find_one({"_id": ObjectId(payload.character_id)})
    if not character_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    if payload.character_id in group_doc.get("characters", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character already in the group")

    if len(group_doc.get("characters", [])) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A group can have at most 5 characters")

    update_result = group_collection.update_one(
        {"_id": ObjectId(payload.group_id)},
        {"$push": {"characters": ObjectId(payload.character_id)}})
    
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add character to group")

    character_update_result = character_collection.update_one(
        {"_id": ObjectId(payload.character_id)},
        {"$addToSet": {"group": ObjectId(payload.group_id)}}
    )
    
    if character_update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update character's group information")
    
    return {"detail": "Character added to group successfully"}


@router.post("/removeCharacter")
def remove_character_from_group(
    payload: CharPayload,
    current_user: User = Depends(get_current_user)
):
    group_collection = get_groups_collection()
    character_collection = get_char_collection()

    group_doc = group_collection.find_one({"_id": ObjectId(payload.group_id)})
    if not group_doc:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_doc.get("created_by") != ObjectId(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Check character is actually in group
    existing = [str(c) for c in group_doc.get("characters", [])]
    if payload.character_id not in existing:
        return {"detail": "Character not in group"}  # ← don't raise, just skip

    group_collection.update_one(
        {"_id": ObjectId(payload.group_id)},
        {"$pull": {"characters": ObjectId(payload.character_id)}}
    )

    character_collection.update_one(
        {"_id": ObjectId(payload.character_id)},
        {"$pull": {"groups": ObjectId(payload.group_id)}}
    )

    return {"detail": "Character removed successfully"}


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: str,
    payload: GroupUpdate,
    current_user: User = Depends(get_current_user)
):
    print(payload)
    group_collection = get_groups_collection()
    character_collection = get_char_collection()

    group_doc = group_collection.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(status_code=404, detail="Group not found")

    if group_doc.get("grp_type") == "seed":
        raise HTTPException(status_code=403, detail="Seed groups cannot be edited")

    if group_doc.get("created_by") != ObjectId(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    updates = {}
    if payload.name is not None:
        if payload.name != group_doc["name"]:
            if group_collection.find_one({"name": payload.name}):
                raise HTTPException(status_code=400, detail="Group name already exists")
        updates["name"] = payload.name

    if payload.description is not None:
        updates["description"] = payload.description

    # ── Sync characters ───────────────────────────────────────────
    if payload.character_ids is not None:
        current_ids = {str(c) for c in group_doc.get("characters", [])}
        desired_ids = set(payload.character_ids)

        to_add    = desired_ids - current_ids
        to_remove = current_ids - desired_ids

        # Add new characters to group + back-ref on character
        for char_id in to_add:
            char = character_collection.find_one({"_id": ObjectId(char_id)})
            if not char:
                continue
            character_collection.update_one(
                {"_id": ObjectId(char_id)},
                {"$addToSet": {"group": ObjectId(group_id)}}
            )

        # Remove characters from group + back-ref on character
        for char_id in to_remove:
            character_collection.update_one(
                {"_id": ObjectId(char_id)},
                {"$pull": {"group": ObjectId(group_id)}}
            )

        updates["characters"] = [ObjectId(cid) for cid in desired_ids]

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    group_collection.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": updates}
    )
    updated = group_collection.find_one({"_id": ObjectId(group_id)})
    
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated group")
    
    return GroupResponse(
        id=str(updated["_id"]),
        name=updated["name"],
        description=updated["description"],
        characters=[str(c) for c in updated.get("characters", [])],
        created_by=str(updated["created_by"])
    )

def addCharacterToGroup(group_id: str, character_id: str):
    group_collection = get_groups_collection()
    group_doc = group_collection.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    if character_id in group_doc.get("characters", []):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character already in the group")
    
    update_result = group_collection.update_one(
        {"_id": ObjectId(group_id)},
        {"$push": {"characters": character_id}}
    )
    
    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add character to group")
    
    return {"detail": "Character added to group successfully"}

@router.post("/seed")
def createSeedGroup(
    payload: SeedGroupCreate,
    current_user: User = Depends(get_current_user)
):
    if payload.admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    grp_collection = get_groups_collection()

    group = Group(
        name=payload.name,
        description=payload.description,
        grp_type=GroupType.seed,
        created_by=str(current_user.id)         
    )
    result = grp_collection.insert_one(group.to_mongo())

    return {
        "group_id": str(result.inserted_id),
        "name": group.name,
        "grp_type": group.grp_type,
    }



@router.get("/", response_model=GroupListResponse)
def list_groups(current_user: User = Depends(get_current_user)):
    group_collection = get_groups_collection()

    # Seed groups — visible to everyone
    seed_groups = list(group_collection.find({"grp_type": "seed"}))

    # User's own custom groups only
    custom_groups = list(group_collection.find({
        "grp_type": "custom",
        "created_by": ObjectId(current_user.id)
    }))

    return GroupListResponse(
        seed_groups=[GroupResponse.model_validate(g) for g in seed_groups],
        custom_groups=[GroupResponse.model_validate(g) for g in custom_groups]
    )

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: str):
    group_collection = get_groups_collection()
    group_doc = group_collection.find_one({"_id": ObjectId(group_id)})
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    group_doc["_id"] = str(group_doc["_id"])  
    return GroupResponse.model_validate(group_doc)




@router.get("/groups_by_user", response_model=list[GroupResponse])
def list_groups_by_user( current_user: User = Depends(get_current_user)):
    group_collection = get_groups_collection()
    groups = group_collection.find({"created_by": ObjectId(current_user.id)})
    return [GroupResponse.model_validate(group) for group in groups]


model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1",
    trust_remote_code=True
)
def searchSimilarMessages(
    query: str,
    grp_id: str,
    user_id: str,
    limit: int = 5
) -> list:
    # msg_collection = get_msgs_collection()
    conv_collection=get_conv_collection()
    print("query",query)
    print("grp_id",grp_id)
    print("user_id",user_id)
    latest_conv = conv_collection.find_one(
        {
            "group": ObjectId(grp_id),
            "user_id": ObjectId(user_id)
        },
        sort=[("seq_num", DESCENDING)]
    )
    # print("latest",latest_conv)
    if not latest_conv:
        return []

    max_seq = latest_conv["seq_num"]
    seq_threshold = max_seq - 1   # exclude last 3 convos
    print("seq_threshold",seq_threshold)
    # Skip search if not enough history
    if seq_threshold <= 0:
        return []

    query_vector = model.encode(
        "search_query: " + query,
        normalize_embeddings=True
    ).tolist()

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": limit,
                 "filter": {
                    "group": {"$eq": ObjectId(grp_id)},
                    "user_id": {"$eq": ObjectId(user_id)}
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "query": 1,
                "summary": 1,
                "seq_num": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(conv_collection.aggregate(pipeline))

    print(f"[search] {len(results)} results for: {query}")
    return results


class CharMapRequest(BaseModel):
    query: str
    session_id:Optional[str]=""

def format_vectors(similar: list, cmap: dict) -> str:
    if not similar:
        return "No relevant past messages found."
    lines = []
    for msg in similar:
        lines.append(f"{msg['content']}")
    return "\n".join(lines) if lines else "No relevant past messages found."



def get_user_preferences(user_id: str, grp_id: str) -> str:
    user_collection = get_users_collection()
    user_doc = user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return ""
    prefs = user_doc.get("preferences", {}).get(grp_id, [])
    if not prefs:
        return ""
    return prefs


@router.post("/charMap/{grp_id}")
def getCharMap(grp_id:str,payload:CharMapRequest,current_user: User = Depends(get_current_user)):
    group_collection = get_groups_collection()
    char_collection=get_char_collection()
    conv_collection=get_conv_collection()
    session_collection=get_session_collection()
    group=group_collection.find_one({"_id":ObjectId(grp_id)})
    if group is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group not found")
    
    cmap={}
    
    for char_id in group["characters"]:
        char = char_collection.find_one({"_id": char_id})
        if char:
            cmap[str(char_id)] = {
                "name": char["name"],
                "traits": char["traits"],
                "desc": char["description"]
            }
    
    session=session_collection.find_one({"_id":ObjectId(payload.session_id)})
    print(session)
    if session:
        session_memory=session.get("memory_summary","no memory as of now")
    recent_convs = list(conv_collection.find(
        {
            "group": ObjectId(grp_id),
            "user_id": ObjectId(current_user.id)
        },
        sort=[("seq_num", -1)],
        limit=2
    ))
    
    
    if not recent_convs:
        recent_convs=[]

    
    lines = []
    for conv in recent_convs:
    #     message_ids = conv.get("messages", [])
    #     if not message_ids:
    #         continue
    #     messages = list(msg_collection.find({"_id": {"$in": message_ids}}))
    #     message_lines = []
    #     for msg in messages:
    #         sender_id = str(msg["sender_id"])
    #         sender = cmap.get(sender_id)
    #         content = msg['content']
    #         if sender:
    #             message_lines.append(f"{content}")

    # # Join all messages into one convo block
    # # print(message_lines)
    #     # msg_str=chr(10).join(message_lines)
        print("conv",conv)
        convo_block = "\n".join([
        f"Conversation {conv['seq_num']}:",
        f"User asked: {conv['query']}",
        f"Summary: {conv['summary']}",
        ])
        lines.append(convo_block)
        
    context = "\n\n".join(lines)
    
    similar_messages=searchSimilarMessages(payload.query,grp_id,current_user.id or "",4)
    # msg_vect=format_vectors(similar_messages,cmap)
    user_preferences=get_user_preferences(current_user.id or "",grp_id)
    
    return {"charmap":cmap,"group_name":group["name"],"group_desc":group["description"],"msg_history":context,"user_id":current_user.id,"similar_messages":similar_messages,"user_preferences":user_preferences,"session_memory":session_memory}


# print(searchSimilarMessages("Luffy what is your dream?","6a241cfcb29152fe5570a4e3","6a21b2905b587e4fa457634a",3))

@router.post("/preferences")
def addPreferences(
    payload: PreferenceAdd,
    current_user: User = Depends(get_current_user)
):
    user_collection = get_users_collection()

    # Fetch existing to check duplicates
    user_doc = user_collection.find_one({"_id": ObjectId(current_user.id)})
    existing = user_doc.get("preferences", {}).get(payload.grp_id, []) if user_doc else []

    # Filter out already existing preferences
    new_pref =  payload.preference

    if not new_pref:
        return {
            "message": "No new preferences to add",
            "existing": existing
        }

    user_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {
            "$set": {
                f"preferences.{payload.grp_id}": payload.preference  
            }
        }
    )

    return {
        "message": "Added new preference",
        "added": new_pref,
        "grp_id": payload.grp_id
    }