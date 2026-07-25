from fastapi import APIRouter, HTTPException, status, Depends

from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
import bcrypt
import jwt
from datetime import datetime, timedelta
from db.dbConnection import get_collection
from models.User import User, UserCreate, UserLogin
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from routes.auth_router import get_current_user
from models.ChatSession import ChatSession

def getSessionCollection():
    return get_collection("chatsession")

# routers/session.py
router = APIRouter(prefix="/session", tags=["session"])

class SessionCreate(BaseModel):
    grp_id: str
    title: Optional[str] = None

class SessionMemoryUpdate(BaseModel):
    session_id: str
    memory_summary: str


# Create session
@router.post("/create")
def createSession(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()

    session = ChatSession(
        user_id=str(current_user.id),
        grp_id=payload.grp_id,
        title=payload.title or "New Chat",
    )
    result = session_collection.insert_one(session.to_mongo())

    return {
        "session_id": str(result.inserted_id),
        "grp_id": payload.grp_id,
        "memory_summary": "",
        "conv_ids": [],
        "created_at": session.created_at.isoformat(),
        "title": session.title or "New Chat"
    }


# Get session — includes memory + all conv ids
@router.get("/{session_id}")
def getSession(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()
    session = session_collection.find_one({"_id": ObjectId(session_id)})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return {
        "session_id": str(session["_id"]),
        "grp_id": str(session["grp_id"]),
        "memory_summary": session.get("memory_summary", ""),
        "conv_ids": [str(c) for c in session.get("conv_ids", [])],
        "title": session.get("title", ""),
        "created_at": str(session.get("created_at", "")),
        "updated_at": str(session.get("updated_at", ""))
    }


# List sessions for user in group
@router.get("/list/{grp_id}")
def listSessions(
    grp_id: str,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()
    
    sessions = list(session_collection.find(
        {
            "user_id": ObjectId(current_user.id),
            "grp_id": ObjectId(grp_id)
        },
        sort=[("updated_at", -1)]
    ))

    return {
        "sessions": [
            {
                "session_id": str(s["_id"]),
                "title": s.get("title") or "New Chat",
                "memory_summary": s.get("memory_summary", ""),
                "conv_ids": [str(c) for c in s.get("conv_ids", [])],
                "created_at": str(s.get("created_at", "")),
                "updated_at": str(s.get("updated_at", ""))
            }
            for s in sessions
        ]
    }


# Update memory + add conv_id to session
@router.post("/memory")
def updateSessionMemory(
    payload: SessionMemoryUpdate,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()
    session = session_collection.find_one({"_id": ObjectId(payload.session_id)})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    session_collection.update_one(
        {"_id": ObjectId(payload.session_id)},
        {
            "$set": {
                "memory_summary": payload.memory_summary,
                "updated_at": datetime.now()
            }
        }
    )

    return {
        "session_id": payload.session_id,
        "memory_summary": payload.memory_summary
    }


# Add conv_id to session when conv is created
@router.post("/addConv")
def addConvToSession(
    payload: dict,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()
    session_id = payload.get("session_id")
    conv_id = payload.get("conv_id")

    session = session_collection.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    session_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"conv_ids": ObjectId(conv_id)},
            "$set": {"updated_at": datetime.now()}
        }
    )

    return {"session_id": session_id, "conv_id": conv_id}


# Delete session
@router.delete("/{session_id}")
def deleteSession(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session_collection = getSessionCollection()
    session = session_collection.find_one({"_id": ObjectId(session_id)})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized")

    session_collection.delete_one({"_id": ObjectId(session_id)})
    return {"message": "Session deleted"}



