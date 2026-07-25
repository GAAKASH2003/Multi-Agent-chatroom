from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
from llm.utils import with_delay
import requests
import jwt
from typing import Optional
from datetime import datetime, timedelta
import dotenv
import os
dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") or ""
ALGORITHM = os.getenv("ALGORITHM") or ""
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or ""


BASE_URL = "http://localhost:8000"  # change to your backend URL
# user_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBYWthc2hAZ21haWwuY29tIiwidXNlcl9pZCI6IjZhMjFiMjkwNWI1ODdlNGZhNDU3NjM0YSIsImV4cCI6MTc4MTg4MzU1Nn0.LA-IrzmPEr8q3Tt1XKitPvNvqlKu1Uo6yXos92-9_-I"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def getCharMappings(grp_id: str,query:str,user_token:str,session_id:str):
    try:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.post(
            url=f"{BASE_URL}/group/charMap/{grp_id}",
            json={"query": query,"session_id":session_id},     # ← body
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching character mappings: {e}")
        return None


# char_map=getCharMappings(grp_id)

# char_list = []
# if char_map:
#     cmap=char_map["charmap"]
#     grp_name=char_map["group_name"]
#     grp_desc=char_map["group_desc"]
#     recent_context=char_map["msg_history"]
#     user_id=char_map["user_id"]



def input_node(state):
    print(f"[input_node] Processing query: {state['user_query']}")
    
    # 1. Fetch character map
    grp_id=state.get("group_id","")
    query=state.get("user_query","")
    email=state.get("user_email","")
    user_id=state.get("user_id","")
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    user_token = create_access_token(
            data={"sub": email, "user_id": user_id}, 
            expires_delta=access_token_expires
    )
    session_id=state.get("session_id","")
    
    char_map=getCharMappings(grp_id,query,user_token,session_id)
    
    if char_map is not None:
        cmap=char_map["charmap"]
        grp_name=char_map["group_name"]
        grp_desc=char_map["group_desc"]
        recent_context=char_map["msg_history"]
        message_vectors=char_map["similar_messages"]
        user_preferences=char_map["user_preferences"]
        session_memory=char_map["session_memory"]
    
    print("[message_vectors]:",message_vectors)
    print("[user_preferences]:",user_preferences)
    print("[recent_context]:",recent_context)
    
    return {
        "characters": cmap,
        "group_name": grp_name,
        "group_description": grp_desc,
        "recent_context": recent_context,
        "message_vectors":message_vectors,
        "user_token":user_token,
        "user_preferences":user_preferences,
        "session_memory":session_memory
    }