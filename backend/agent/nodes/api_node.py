import requests
import asyncio
from graph.queueManager import manager

BASE_URL="http://localhost:8000"

def clean_content(content: str):
    """Strip [query] and [answer] prefixes from stored content"""
    if "[answer]" in content:
        answer = content.split("[answer]", 1)[1]
        # Remove character name prefix e.g "Nami: ..."
        if ":" in answer:
            answer = answer.split(":", 1)[1]
        return answer.strip()
    if "[query]" in content:
        return content.split("[query]", 1)[1].strip()


def api_node(state):
    conv_id = state.get("conv_id", "")
    loop = state.get("loop", 0)
    char_id = state.get("character", "")
    char_name=state.get("char_name","")
    char_response = char_name+":"+state.get("character_response", "")
    query=state.get("user_query","")
    grp_id=state.get("group_id","")
    userId=state.get("user_id","")
    session_id=state.get("session_id","")
    emit = state["emit"]

    message_content=f"""[query]{query}
[answer]{char_response}
    """
    emit({
        "type": "character_response",
        "data": {
            "character_name": char_name,
            "character_id": char_id,
            "response": clean_content(message_content)
        }
    })

    print(f"[api_node] dialogues: {state.get('dialogues', [])}")
    user_token = state.get("user_token", "")
    headers = {
                "Authorization": f"Bearer {user_token}"
            }

    if not conv_id:
        # No conv yet — create conversation with first message
        print("[api_node] Creating new conversation...")
        
        payload = {
            "query": state.get("user_query", ""),
            "group_id": grp_id,
            "characterResponses": [
                {
                    "cid": char_id,
                    "response": message_content,
                    "grp_id":grp_id,
                    "user_id":userId
                }
            ]
        }

        try:
            response = requests.post(f"{BASE_URL}/conv/createConv", json=payload,headers=headers)
            response.raise_for_status()
            data = response.json()
            
            print(f"[api_node] Conversation created: {data}")
            
            if session_id:
                requests.post(
                    f"{BASE_URL}/session/addConv",
                    json={"session_id": session_id, "conv_id":data["conv_id"]},
                    headers=headers
                )
            
            return {
                "conv_id": data["conv_id"],
                "loop": loop + 1
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[api_node] Error creating conversation: {e}")
            return {"loop": loop + 1}

    else:
        # Conversation exists — just add message
        print(f"[api_node] Adding message to conversation: {conv_id}")
        payload = {
            "conv_id": conv_id,
            "sender_id": char_id,
            "content": message_content,
            "grp_id":grp_id,
            "user_id":userId
        }

        try:
            response = requests.post(f"{BASE_URL}/conv/addMessage", json=payload,headers=headers)
            response.raise_for_status()
            data = response.json()
            print(f"[api_node] Message added: {data}")
        
            return {
                "loop": loop + 1
            }
        except requests.exceptions.RequestException as e:
            print(f"[api_node] Error adding message: {e}")
            return {"loop": loop + 1}
        