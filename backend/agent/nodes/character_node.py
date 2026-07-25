from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
from graph.initialState import Message
from llm.utils import with_delay

llm=get_groq_llm()
parser=JsonOutputParser()


# character_prompt =  ChatPromptTemplate.from_template("""
#     "system":
#      "You are {character}.\n"
#      "a member of {group_name}.\n"
#      "Group description: {group_desc}\n"
#      "User query: {user_query}\n\n"
     
#      "Stay in character. Respond naturally to the user query.\n\n"
#      "Output ONLY valid JSON in this format:\n"
#     Example:
#         {{
#             "character_name": "6a241cfcb29152fxxxxxx",
#             "response":character_response
#         }}
# "'
# """
# )


character_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are {character_name}, a member of {group_name}.
═══════════════════════════════════════
IDENTITY
═══════════════════════════════════════
Group: {group_name}
Group Description: {group_desc}

Your Profile:
- Name: {character_name}
- Description: {description}
- Traits: {character_traits}

═══════════════════════════════════════
USER PREFERENCES
═══════════════════════════════════════
{user_pref}

═══════════════════════════════════════
CONTEXT
═══════════════════════════════════════
[What others in the group said about this query]
{history}

[Recent group conversational summary in a session]
{session_memory}

[last two conversation summaries]
{context}

[Past messages relevant to this query]
{message_vectors}

═══════════════════════════════════════
RULES
═══════════════════════════════════════
- Stay completely in character. Never refer to yourself as an AI.
- Speak in your character's natural tone and vocabulary.
- Build on what others said — don't repeat what's already been said.
- Reference other characters by name if relevant.
- Draw from past conversations naturally — don't quote them directly.
- Tailor your response to match user preferences if available.
- Keep responses short, punchy, and conversational.
- Talk directly TO the user, not about them.

═══════════════════════════════════════
OUTPUT
═══════════════════════════════════════
Output ONLY valid JSON:
{{
    "response": "<your in-character response>"
}}
"""),
    ("human", "User: {user_query}")
])


def format_vectors(similar: list, cmap: dict) -> str:
    if not similar:
        return "No relevant past messages found."
    lines = []
    for msg in similar:
        sender_id = str(msg.get("sender_id", ""))
        sender_name = cmap.get(sender_id, {}).get("name", "Unknown")
        lines.append(f"  {sender_name}: {msg['content']}")
    return "\n".join(lines) if lines else "No relevant past messages found."


def format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        lines.append(f"[{msg['character_name']}] responded: {msg['response']}")
    return "\n".join(lines)

@with_delay(seconds=2)
def character_node(state):
    # print(state)
    character_id=state.get("character","")
    # print("characters*********",character_id)
    cmap=state.get("characters")
    details = cmap[character_id]
    chain = character_prompt | llm | parser
    llm_result = chain.invoke({
        "character_name":{details['name']},
        "description": {details['desc']},
        "character_traits":{', '.join(details['traits'])},
        "group_name": state.get("group_name", ""),
        "group_desc": state.get("group_desc", ""),
        "user_query":state.get("user_query",""),
        "history": format_history(state.get("history", [])),
        "context":state.get("recent_context",""),
        "message_vectors":state.get("message_vectors",[]),
        "user_pref":state.get("user_preferences",""),
        "session_memory":state.get("session_memory","")
    })
    # print(f"[character_node] LLM response: {llm_result}")
    
    new_message: Message = {
        "character_name": details["name"],
        "response": llm_result["response"]   # ← use llm_result
    }
    
    # print(f"[character_node] Returning new_message: {new_message}")


    return {
        "character_response": llm_result["response"],
        "dialogues": [new_message]
    }



# {'6a270149539495195c8f87bb': {'name': 'Nami', 'traits': ['intelligent', 'resourceful', 'greedy', 'caring', 'brave'], 'desc': 'The navigator of the Straw Hat Pirates. An expert cartographer who dreams of drawing a map of the entire world.'}, '6a27018d539495195c8f87bc': {'name': 'Monkey D. Luffy', 'traits': ['carefree', 'determined', 'fearless', 'loyal', 'optimistic'], 'desc': 'Captain of the Straw Hat Pirates who gained rubber powers from the Gum-Gum Fruit. Dreams of becoming the Pirate King.'}, '6a2701a3539495195c8f87bd': {'name': 'Roronoa Zoro', 'traits': ['disciplined', 'loyal', 'serious', 'strong-willed', 'honorable'], 'desc': "The swordsman of the Straw Hat Pirates who uses the Three-Sword Style. Aims to become the world's greatest swordsman."}, '6a2701b7539495195c8f87be': {'name': 'Usopp', 'traits': ['creative', 'cowardly', 'loyal', 'humorous', 'inventive'], 'desc': 'The sniper of the Straw Hat Pirates known for his tall tales and creativity. Dreams of becoming a brave warrior of the sea.'}, '6a2701eb539495195c8f87bf': {'name': 'Sanji', 'traits': ['chivalrous', 'passionate', 'kind-hearted', 'confident', 'loyal'], 'desc': 'The cook of the Straw Hat Pirates and a master martial artist. Dreams of finding the All Blue.'}, '6a270202539495195c8f87c0': {'name': 'Tony Tony Chopper', 'traits': ['kind', 'naive', 'compassionate', 'curious', 'innocent'], 'desc': "ate the Human-Human Fruit, becoming the crew's doctor. Wants to cure every disease."}, '6a27021a539495195c8f87c1': {'name': 'Nico Robin', 'traits': ['intelligent', 'calm', 'mysterious', 'observant', 'mature'], 'desc': 'The archaeologist of the Straw Hat Pirates. Seeks to uncover the true history of the world by reading the Poneglyphs.'}, '6a270241539495195c8f87c2': {'name': 'Franky', 'traits': ['eccentric', 'confident', 'inventive', 'energetic', 'loyal'], 'desc': 'The shipwright of the Straw Hat Pirates and a cyborg. Built the Thousand Sunny and dreams of sailing it around the world.'}, '6a27024f539495195c8f87c3': {'name': 'Brook', 'traits': ['cheerful', 'funny', 'optimistic', 'gentlemanly', 'loyal'], 'desc': 'The musician of the Straw Hat Pirates, a living skeleton revived by the Revive-Revive Fruit. Dreams of reuniting with Laboon.'}, '6a27025b539495195c8f87c4': {'name': 'Jinbe', 'traits': ['wise', 'calm', 'honorable', 'protective', 'reliable'], 'desc': 'The helmsman of the Straw Hat Pirates and a powerful fish-man karate master. Former Warlord of the Sea.'}}