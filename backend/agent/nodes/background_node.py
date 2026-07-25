import threading
from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
import requests

llm=get_groq_llm()
parser=JsonOutputParser()

BASE_URL="http://localhost:8000"

conv_summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a conversation summarizer for a roleplay group chat.

Summarize this conversation concisely capturing:
- What the user asked
- Which characters responded and what they said
- Key facts, emotions, or story points revealed
- Anything notable about how the user engaged

Keep it under 5 sentences. Write in third person.

Output ONLY valid JSON:
{{
    "summary": "<conversation summary>"
}}
"""),
    ("human", """User asked: {user_query}

Characters responded:
{responses}
""")
])


memory_extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a user memory manager for a roleplay group chat.

Your job is to maintain a running summary of what is known about this user.
The summary should capture:
- Interests and topics they care about
- Likes and dislikes
- Personality traits observed
- Specific facts they've revealed about themselves
- How they prefer to interact with characters

Rules:
- Merge new observations into the existing summary naturally
- Don't repeat information already in the summary
- Keep it concise but informative — 3 to 8 sentences max
- If nothing new is learned, return the existing summary unchanged
- Write in third person ("User likes...", "User is interested in...")
- Only update if this conversation genuinely reveals something new

Output ONLY valid JSON:
{{
    "updated": true | false,
    "summary": "<updated or unchanged summary>"
}}
"""),
    ("human", """Existing summary:
{existing_preferences}

User asked: {user_query}

Characters responded:
{responses}
""")
])


session_memory_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a session memory manager for a roleplay group chat.

Maintain a running summary of this chat session capturing:
- Topics discussed
- Characters the user interacted with
- User's mood and engagement style
- Key facts or story points explored
- Any preferences revealed in this session

Merge new conversation into existing summary naturally.
Keep it under 10 sentences. Write in third person.
Only update if something new and meaningful happened.

Output ONLY valid JSON:
{{
    "updated": true | false,
    "summary": "<updated or unchanged summary>"
}}
"""),
    ("human", """Existing session summary:
{existing_summary}

New exchange:
User asked: {user_query}
{responses}
""")
])

def format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        lines.append(f"[{msg['character_name']}] responded: {msg['response']}")
    return "\n".join(lines)


def run_background_pipeline(
    grp_id: str,
    user_query: str,
    dialogues: list,
    conv_id: str,
    session_id: str,
    user_token: str,
    memory: str,
    dialogue_str: str,
    session_memory: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    responses_str = "\n".join([f"{m['character_name']}: {m['response']}" for m in dialogues])

    # Step 1 — conv summary + embedding
    try:
        chain = conv_summary_prompt | llm | parser
        result = chain.invoke({"user_query": user_query, "responses": responses_str})
        summary = result.get("summary", "")

        if summary and conv_id:
            resp = requests.post(
                f"{BASE_URL}/conv/summary",
                json={"conv_id": conv_id, "summary": summary},
                headers=headers
            )
            resp.raise_for_status()
            print("[background] Step 1 done ✓")
    except Exception as e:
        print(f"[background] Step 1 failed: {e}")

    # Step 2 — update session memory
    try:
        session_chain = session_memory_prompt | llm | parser
        session_result = session_chain.invoke({
            "existing_summary": session_memory or "No session memory yet.",
            "user_query": user_query,
            "responses": dialogue_str
        })

        if session_result.get("updated") and session_result.get("summary") and session_id:
            resp = requests.post(
                f"{BASE_URL}/session/memory",
                json={
                    "session_id": session_id,
                    "memory_summary": session_result["summary"]
                },
                headers=headers
            )
            resp.raise_for_status()
            print("[background] Step 2 done ✓ — session memory updated")
    except Exception as e:
        print(f"[background] Step 2 failed: {e}")

    # Step 3 — user preference memory
    try:
        memory_chain = memory_extraction_prompt | llm | parser
        memory_result = memory_chain.invoke({
            "existing_preferences": memory,
            "user_query": user_query,
            "responses": dialogue_str
        })

        if memory_result.get("updated") and memory_result.get("summary"):
            resp = requests.post(
                f"{BASE_URL}/group/preferences",
                json={"grp_id": grp_id, "preference": memory_result["summary"]},
                headers=headers
            )
            resp.raise_for_status()
            print("[background] Step 3 done ✓")
    except Exception as e:
        print(f"[background] Step 3 failed: {e}")

    print("[background] Pipeline complete ✓")   
        
        
        
        
def background_node(state):
    print("[background_node] Firing background pipeline...")

    # Fire and forget — don't wait
    thread = threading.Thread(
        target=run_background_pipeline,
        kwargs={
            "grp_id": state.get("group_id", ""),
            "user_query": state.get("user_query", ""),
            "dialogues": state.get("dialogues", []),
            "conv_id": state.get("conv_id", ""),
            "user_token": state.get("user_token", ""),
            "dialogue_str": format_history(state.get("dialogues", [])),
            "memory":state.get("user_preferences",""),
            "session_id":state.get("session_id"),
            "session_memory":state.get("session_memory","")
        },
        daemon=True   
    )   
    thread.start()
    print("background ended")

    return {} 