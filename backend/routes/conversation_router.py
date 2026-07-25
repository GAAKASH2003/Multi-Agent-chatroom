from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from datetime import datetime
from db.dbConnection import get_collection
from models.Message import MessageCreate
from models.User import User
from routes.auth_router import get_current_user
from models.Conversation import Conversation, ConversationCreate
from models.Message import MessageAdd
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sentence_transformers import SentenceTransformer
from sse_starlette.sse import EventSourceResponse
from agent.graph.builder import app, ConvoState
import asyncio
import json

model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1",
    trust_remote_code=True
)

class ChatRequest(BaseModel):
    query: str
    group_id: str
    session_id:str
    
class ChatResponse(BaseModel):
    query: str
    status: str
    dialogues: list = []
    error: Optional[str] = None
    loop_count: int = 0
    responded_characters: list = []

    
class ConversationResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    query: str
    message: str
    charId:str
    group: str
    user_id: str
    seqNum: int
    timestamp: Optional[datetime] = None

    def to_mongo(self):
        data = self.model_dump(by_alias=True, exclude_none=True)

        if "_id" in data:
            data["_id"] = ObjectId(data["_id"])

        if "group" in data and data["group"]:
            data["group"] = ObjectId(data["group"])

        if "user_id" in data and data["user_id"]:
            data["user_id"] = ObjectId(data["user_id"])
        
        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        if doc.get("group"):
            doc["group"] = str(doc["group"])

        if doc.get("user_id"):
            doc["user_id"] = str(doc["user_id"])
        
        return cls(**doc)



class ConvSummaryUpdate(BaseModel):
    conv_id: str
    summary: str

router = APIRouter(
    prefix="/conv",
    tags=["conversation"],
    responses={404: {"description": "Not found"},200: {"description": "Success"}},
)

def getMessagesCollection():
    return get_collection("messages")

def getConvCollection():
    return get_collection("conversations")

def getGroupsCollection():
    return get_collection("groups")


# @router.post("/chat", response_model=ChatResponse)
# def chat(
#     request: ChatRequest,
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         # Validate group exists and user has access
#         grp_collection = getGroupsCollection()
#         group = grp_collection.find_one({"_id": ObjectId(request.group_id)})
        
#         if not group:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Group not found"
#             )
        
#         # Check if user is member of group (optional - adjust based on your permissions)
#         # if str(current_user.id) not in [str(m) for m in group.get("members", [])]:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_403_FORBIDDEN,
#         #         detail="User is not a member of this group"
#         #     )
        
#         # Initialize state for the graph
        
        
        # state: ConvoState = {
        #     'session_id':"",
        #     "group_id": request.group_id,
        #     "group_name": "",
        #     "group_description": "",
        #     "characters": {},
        #     "user_query": request.query,
        #     "user_token": "",
        #     "character": "",
        #     "char_name": "",
        #     "character_response": "",
        #     "feedback": "",
        #     "loop": 0,
        #     "status": "",
        #     "dialogues": [],
        #     "responded_characters": [],
        #     "suggested_characters": [],
        #     "conv_id": "",
        #     "user_id": str(current_user.id),
        #     "user_email": current_user.email,
        #     "recent_context": "",
        #     "user_preferences": "",
        #     "error": "",
        #     "message_vectors": ""
        # }
        
#         # Compile and invoke the graph
#         result = app.invoke(state)
#         print(result)
#         # Return response
#         return ChatResponse(
#             query=request.query,
#             status=result.get("status", "completed"),
#             dialogues=result.get("dialogues", []),
#             error=result.get("error"),
#             loop_count=result.get("loop", 0),
#             responded_characters=result.get("responded_characters", [])
#         )
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error processing chat: {str(e)}"
#         )



@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    req: Request,
    current_user: User = Depends(get_current_user)
):
    grp_collection = getGroupsCollection()
    group = grp_collection.find_one({"_id": ObjectId(request.group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Create a unique queue for this request
    
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit(event: dict):
        asyncio.run_coroutine_threadsafe(
            queue.put(event),
            loop
        )
    print(request.session_id) 
    state: ConvoState = {
            'session_id':request.session_id ,
            "session_memory":"",
            "group_id": request.group_id,
            "group_name": "",
            "group_description": "",
            "characters": {},
            "user_query": request.query,
            "user_token": "",
            "character": "",
            "char_name": "",
            "character_response": "",
            "feedback": "",
            "loop": 0,
            "status": "",
            "dialogues": [],
            "responded_characters": [],
            "suggested_characters": [],
            "conv_id": "",
            "user_id": str(current_user.id),
            "user_email": current_user.email,
            "recent_context": "",
            "user_preferences": "",
            "error": "",
            "message_vectors": "",
            "emit":emit}
        

    async def run_graph():
        try:
            await asyncio.to_thread(app.invoke, state)
        except Exception as e:
            emit({
                "type": "error",
                "data": str(e)
            })
        finally:
            emit({
                "type": "done",
                "data": {
                    "status": "completed"
                }
            })

    async def event_generator():

        asyncio.create_task(run_graph())

        while True:

            item = await queue.get()

            if item["type"] == "done":
                yield {
                    "event": "done",
                    "data": json.dumps(item["data"])
                }
                break

            yield {
                "event": item["type"],
                "data": json.dumps(item["data"])
            }

    return EventSourceResponse(event_generator())



# @router.post("/createConv")
# def createConversation(conv:ConversationCreate,current_user: User = Depends(get_current_user)):
#     msg_collection=getMessagesCollection()
#     # conv_collection=getConvCollection()
#     message_ids=[]
#     for resp in characterResponses:
#         messageTemp=MessageCreate(
#               sender_id=resp["cid"],
#               content=resp["response"],
#               timeStamp=datetime.now()
#             ).to_mongo
#         message_doc=msg_collection.insert_one(messageTemp)
#         message_ids.append(message_doc.inserted_id)
        
      


    
 
def clean_content(content: str) -> str:
    """Strip [query] and [answer] prefixes from stored content"""
    if "[answer]" in content:
        answer = content.split("[answer]", 1)[1]
        # Remove character name prefix e.g "Nami: ..."
        if ":" in answer:
            answer = answer.split(":", 1)[1]
        return answer.strip()
    if "[query]" in content:
        return content.split("[query]", 1)[1].strip()
    return content.strip()

@router.get("/session/{session_id}")
def getSessionConversations(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session_collection = get_collection("chatsession")
    session_doc = session_collection.find_one({"_id": ObjectId(session_id)})
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session_doc.get("user_id")) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    conv_collection = getConvCollection()
    msg_collection = getMessagesCollection()

    conv_ids = session_doc.get("conv_ids", [])
    if not conv_ids:
        return {"turns": []}

    conv_docs = list(conv_collection.find(
        {"_id": {"$in": [ObjectId(cid) for cid in conv_ids]}},
        sort=[("seq_num", 1)]
    ))

    turns = []

    for conv in conv_docs:
        conv_id = str(conv["_id"])
        created_at = conv.get("timestamp") and conv["timestamp"].timestamp() * 1000

        # Fetch responses for this conv
        responses = []
        message_ids = conv.get("messages", [])

        if message_ids:
            message_docs = list(msg_collection.find(
                {"_id": {"$in": [ObjectId(mid) for mid in message_ids]}}
            ))
            message_docs.sort(key=lambda m: m.get("timestamp", datetime.min))

            for msg in message_docs:
                responses.append({
                    "id": str(msg["_id"]),
                    "role": "assistant",
                    "content": clean_content(msg.get("content", "")),
                    "createdAt": msg.get("timeStamp") and msg["timeStamp"].timestamp() * 1000,
                    "characterId": str(msg.get("sender_id", "")),
                    "conv_id": conv_id,
                    "sessionId": session_id,
                })

        # Each turn = one query + its responses
        turns.append({
            "conv_id": conv_id,
            "query": {
                "id": f"{conv_id}_query",
                "role": "user",
                "content": clean_content(conv.get("query", "")),
                "createdAt": created_at,
                "characterId": None,
                "conv_id": conv_id,
                "sessionId": session_id,
            },
            "responses": responses,
            "seq_num": conv.get("seq_num"),
        })

    return {"turns": turns}


@router.post("/createConv")
def createConversation(
    conv: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    msg_collection = getMessagesCollection()
    conv_collection = getConvCollection()

    # 1. Create all messages first
    message_ids = []
    for resp in conv.characterResponses:
        print(resp)
        msg_embedding=message_encode(resp.response)
        message_data = MessageCreate(
            sender_id=resp.cid,
            content=resp.response,
            timeStamp=datetime.now(),
            grp_id=resp.grp_id,
            user_id=current_user.id or "default_id",
            embedding=msg_embedding
        ).to_mongo()

        result = msg_collection.insert_one(message_data)
        message_ids.append(result.inserted_id)  # keep as ObjectId for now

    # 2. Create conversation with message refs
    
    last_conv=conv_collection.find_one(
        {"group":ObjectId(conv.group_id)},
         sort=[("seq_num", -1)] 
    )
    next_seq_num = (last_conv["seq_num"] + 1) if last_conv else 1
    
    conv_data = Conversation(
        query=conv.query,
        messages=[str(mid) for mid in message_ids],
        group=conv.group_id,
        seq_num=next_seq_num,
        user_id=str(current_user.id),
        timestamp=datetime.now()
    ).to_mongo()

    conv_result = conv_collection.insert_one(conv_data)

    return {
        "conv_id": str(conv_result.inserted_id),
        "query": conv.query,
        "message_ids": [str(mid) for mid in message_ids]
    }

@router.post("/addMessage")
def addMessage(
    payload: MessageAdd,
    current_user: User = Depends(get_current_user)
):
    msg_collection = getMessagesCollection()
    conv_collection = getConvCollection()

    # 1. Find conversation
    conv_row = conv_collection.find_one({"_id": ObjectId(payload.conv_id)})
    
    if not conv_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # 2. Compare both as strings to avoid ObjectId vs str mismatch
    if str(conv_row["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # 3. Insert message
    msg_embedding=message_encode(payload.content)
    message_data = MessageCreate(
        sender_id=payload.sender_id,
        content=payload.content,
        timeStamp=datetime.now(),
        grp_id=payload.grp_id,
        user_id=current_user.id or "default_id",
        embedding=msg_embedding
    ).to_mongo()

    result = msg_collection.insert_one(message_data)
    message_id = result.inserted_id

    # 4. Append to conversation
    conv_collection.update_one(
        {"_id": ObjectId(payload.conv_id)},
        {"$push": {"messages": message_id}}
    )

    return {
        "conv_id": payload.conv_id,
        "message_id": str(message_id)
    }
    

        
@router.post("/encode")
def encodemessages():
    conv_collection=getConvCollection()
    cursor = conv_collection.find(
        {"summary": {"$exists": True}},
        {"_id": 1, "summary": 1}
    )

    for doc in cursor:
        embedding = model.encode(doc["summary"]).tolist()

        conv_collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding": embedding}}
    )
        
        
def message_encode(msg: str, is_query: bool = False) -> list[float]:
    # nomic-embed-text-v1 requires prefixes
    prefix = "search_query: " if is_query else "search_document: "
    embedding = model.encode(
        prefix + msg,
        normalize_embeddings=True   # ← required for cosine similarity
    ).tolist()
    return embedding


@router.post("/summary")
def updateConvSummary(
    payload: ConvSummaryUpdate,
    current_user: User = Depends(get_current_user)
):
    conv_collection = getConvCollection()

    conv = conv_collection.find_one({"_id": ObjectId(payload.conv_id)})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if str(conv["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    print(f"[summary] Encoding: {payload.summary[:100]}")
    sum_embedding = message_encode(payload.summary, is_query=False)  # ← document prefix
    print(f"[summary] Dims: {len(sum_embedding)} | First 5: {sum_embedding[:5]}")

    conv_collection.update_one(
        {"_id": ObjectId(payload.conv_id)},
        {"$set": {"summary": payload.summary, "embedding": sum_embedding}}
    )

    return {
        "conv_id": payload.conv_id,
        "summary": payload.summary,
        "embedding_dims": len(sum_embedding)
    }
