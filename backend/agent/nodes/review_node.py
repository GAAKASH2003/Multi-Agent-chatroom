from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
from llm.utils import with_delay

llm=get_groq_llm()
parser=JsonOutputParser()

# review_prompt = ChatPromptTemplate.from_template("""
#     You are a reviewer. Your task is to check if the current conversation history properly addresses the user's query.

#     - Required check: If the user mentions specific characters, make sure EACH of those characters has responded in the conversation history. 
#     - if character response satisfies the user query mark as satisfied
#     - if the directed user answers the user query then mark as satisfied 
#     - If any required character is missing, mark as unsatisfied and suggest which characters still need to respond.  

#     You are the orchestrator for the group: {group_name}.
#     Group description: {group_desc}
#     characters: {characters}

#     user_query: {user_query}

#     history:{history}
    
#     Respond in strict JSON:
#     "status": "satisfied" | "unsatisfied",
#     "feedback": "Your explanation here. If unsatisfied, mention missing characters."
# """)

review_prompt = ChatPromptTemplate.from_messages([
    ("system", """
        You are a conversation reviewer for a roleplay group.
        Group: {group_name}
        Group Description: {group_desc}
        
        character_response for this particular query
        {character_name}:{character_response}
        Available Characters:
        {characters}

        Already Responded Characters:
        {responded_characters}
        
        Use characters responses and recent conversations in the grp as context to give review       
        Character responses for the same query:
        {history}
        
        [last two conversation summaries]
        {context}
        
        [Recent group conversational summary in a session as a whole]
        {session_memory}

        Your job is to evaluate the conversation and decide if the user query has been fully addressed.

        Rules:
        - If the user directly addresses multiple characters, ALL of them must respond before satisfied.
        - If the query is general, ONE well-suited response is enough.
        - If the query is about a shared experience, consider if multiple characters should naturally weigh in.
        - Once all required characters have responded, mark as satisfied.
        - If unsatisfied, suggest which characters STILL NEED to respond (exclude already responded ones).
        - select charcters based on conversation history if needed 
        - responded characters should not respond again
        Output ONLY valid JSON:
        {{
            "status": "satisfied" | "unsatisfied",
            "feedback": "Brief explanation. If unsatisfied, mention which characters should still respond and why.",
            "suggested_characters": []  // names of characters who should still respond seperated by commas, empty if satisfied
        }}
"""),
    ("human", """User Query: {user_query}
""")
])

def format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        lines.append(f"[{msg['character_name']}] responded: {msg['response']}")
    return "\n".join(lines)

@with_delay(seconds=2)
def review_node(state):
    chain=review_prompt|llm|parser
    dialogues = state.get("dialogues", [])
    responded_names = list({msg["character_name"] for msg in dialogues})
    print(f"[review_node] dialogues: {state.get('dialogues', [])}")
    result = chain.invoke({
        "group_name": state.get("group_name", ""),
        "group_desc": state.get("group_desc", ""),
        "characters": state.get("characters", ""),
        "character_name":state.get("char_name", ""),
        "user_query": state.get("user_query",""),
        "character": state.get("character",""),
        "character_response":state.get("character_response",""),
        "history": format_history(state.get("dialogues", [])),
        "responded_characters": ", ".join(responded_names) if responded_names else "None yet",
        "context":state.get("recent_context",""),
        "session_memory":state.get("session_memory","")
    })
    print(f"Review → status: {result.get('status')} | feedback: {result.get('feedback')} | suggested: {result.get('suggested_characters')}")
    return {
        "status": result.get("status", "unsatisfied"),
        "feedback": result.get("feedback", ""),
        "suggested_characters": result.get("suggested_characters", []),
        "responded_characters": responded_names
    }

def route_evaluation(state):
    if state['status'] == 'satisfied' or state['loop']>=5:
        return 'approved'
    else:
        return 'needs_improvement'
      
      