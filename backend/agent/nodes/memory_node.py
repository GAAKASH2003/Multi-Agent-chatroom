from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
from llm.utils import with_delay
import requests

BASE_URL="http://localhost:8000/group"

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
{existing_summary}

User asked: {user_query}

Characters responded:
{responses}
""")
])

llm=get_groq_llm()
parser=JsonOutputParser()


def format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        lines.append(f"[{msg['character_name']}] responded: {msg['response']}")
    return "\n".join(lines)

def memory_node(state):
    dialogues = state.get("dialogues", [])
    if not dialogues:
        return {}

    existing_prefs = state.get("preferences","")

    # Format conversation for extraction
    convo_str = f"User asked: {state['user_query']}\n"
    for msg in dialogues:
        convo_str += f"{msg['character_name']}: {msg['response']}\n"

    chain = memory_extraction_prompt | llm | parser
    result = chain.invoke({
        "existing_preferences": existing_prefs,
        "user_query":state.get("user_query",""),
        "responses":format_history(state.get("dialogues", [])),
        "session_memory":state.get("session_memory","")
    })

    if result.get("updated") and result.get("summary"):
        new_summary = result["summary"]
        print(f"[memory_node] Updating summary: {new_summary}")
        headers = {"Authorization": f"Bearer {state['user_token']}"}
       
        requests.post(
                    f"{BASE_URL}/preferences",
                    json={
                        "grp_id": state["group_id"],
                        "preference":new_summary        
                    },
                    headers=headers
            )
    
    return {}