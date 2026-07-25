from __future__ import annotations
from typing import TypedDict, Dict, List, Annotated,Callable
import operator

response_queues = {}
response_loops = {}

class Message(TypedDict):
    character_name: str
    response: str
    

class ConvoState(TypedDict):
    session_id:str
    session_memory: str
    group_id: str
    group_name: str
    group_description: str
    characters: Dict
    user_query: str
    user_token: str
    character: str
    char_name:str
    character_response:str
    loop: int
    status:str
    feedback:str
    dialogues: Annotated[List[Message], operator.add] 
    responded_characters: List[str]
    suggested_characters: List[str]
    recent_context:str
    message_vectors:str
    conv_id:str
    user_id:str
    user_email:str
    user_preferences: str
    error:str
    emit: Callable[[dict], None]