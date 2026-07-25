from langchain_core.prompts import ChatPromptTemplate
from llm.groq_api import get_groq_llm 
from langchain_core.output_parsers import JsonOutputParser
from llm.utils import with_delay


llm=get_groq_llm()
parser=JsonOutputParser()



orchestrator_prompt = ChatPromptTemplate.from_template("""
        You are the orchestrator for the group: {group_name}.
        Group description:
        {group_desc}
        Your job is to select the SINGLE most suitable character to respond to the user's query.
        Follow these rules STRICTLY in order:
        1. DIRECT ADDRESS RULE (highest priority):
        - If the user directly addresses a character by name select THAT character immediately. No exceptions.
        2. Consider feedback and previous conversation for selecting suitable character if there is no feedback or history follow other rules
        3. RELEVANCE RULE:
        - Analyze the user query carefully.
        - Match the query against each character's:
            * Name and aliases
            * Traits (personality, skills)
            * Description (role, backstory, experiences, abilities)
            * Relevance to the group context: {group_desc}
        - Select the character whose background/traits/experiences make them the BEST fit to answer.

        4. REASONING (internal, not output):
        - Ask yourself: "Which character would most naturally and authentically answer this question?"
        - Consider: who was involved, who has expertise, whose personality fits, whose story connects.
        - choose character if any character refers in the previous recent message 
        
        Available characters:
        {characters}

        User query:
        {user_query}

        Feedback from review node consider it for selecting characters: 
        {feedback}

        Use characters responses and recent conversations in the grp as context to decide characters        
        Character responses for the same query:
        {history}
        
        [Recent group conversational summary in a session]
        {session_memory}
        
        [last two conversation summaries]
        {context}
        
        Exclude this characters while selecting because these characters already responded to query if empty consider no one responded 
        {responded}
          
        The reviewer has suggested these characters should still respond if empty consider all charcters:
        {suggested_characters}
        Output format:
        {{
            "character_id": "<id of selected character>",
            "name": "<character_name>"
        }}
""")


def format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history:
        lines.append(f"[{msg['character_name']}] responded: {msg['response']}")
    return "\n".join(lines)

@with_delay(seconds=2)
def orchestrator_node(state):
    chain = orchestrator_prompt | llm | parser
    cmap=state["characters"]
    responded = state.get("responded_characters", [])
    suggested = state.get("suggested_characters", []) 
    # print(char_map)
    # cmap=char_map["charmap"]
    if cmap:
        char_list=[]
        for char_id, details in cmap.items():
            char_str = f"""
                Character ID: {char_id}
                Name: {details['name']}
                Traits: {', '.join(details['traits'])}
                Description: {details['desc']}
            """
            char_list.append(char_str.strip())

    prompt_content = {
        "group_name": state["group_name"],
        "group_desc": state["group_description"],
        "characters": "\n\n".join(char_list),
        "user_query": state["user_query"],
        "feedback": state.get("feedback",""),
        "history":  format_history(state.get("dialogues", [])),
        "context":state.get("recent_context",""),
        "responded":responded,
        "suggested_characters": suggested,
        "session_memory":state.get("session_memory","")
    }
    formatted_prompt = orchestrator_prompt.format_messages(**prompt_content)
    print(formatted_prompt[0].content)
    try:
        result = chain.invoke(prompt_content)
        print("LLM Output:", result)

        if isinstance(result, dict) and "character_id" in result:
            character_details=cmap[ result["character_id"]]
            print(f"selected character:{character_details}")
            return {
                "character": result["character_id"],
                "char_name": result["name"]
            }

        raise ValueError("character_id missing from response")

    except Exception as e:
        print(f"Error in orchestrator_node: {e}")

        return {
            "character": ""
        }