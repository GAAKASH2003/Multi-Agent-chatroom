from typing import Annotated, Sequence, List, Literal # Typing utilities for type hints and better code readability
from pydantic import BaseModel, Field  # `BaseModel` is the base class used to create data models, `Field` is used to provide additional metadata
from langchain_core.messages import HumanMessage
from langgraph.types import Command # LangGraph types for extending commands and functionalities
from langgraph.graph import StateGraph, START, END, MessagesState # Graph-related utilities for building workflows and state machines
from langgraph.prebuilt import create_react_agent # Prebuilt tools and agents for streamlined development
from pprint import pprint # Utilities for debugging and displaying complex data structures in an organized way
from IPython.display import Image, display
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import os
import dotenv

dotenv.load_dotenv()

app=FastAPI()
# print("GOOGLE_API_KEY",os.getenv("GOOGLE_API_KEY"))
llm=ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"),model="gemini-2.0-flash")
class ConversationState(Dict[str, Any]):
    history: List[str] 
    summary:str 
    user_message:str
    speaker:str
    feedback:str
    status:str
    group_name:str
    group_description:str
    characters:List[Dict]
    character_desc:str
    dialogues:List[Dict]

# StrawhatsGroup = {
#   "group_name": "Strawhat Pirates",
#   "group_description": "A lively pirate crew led by Luffy on adventures."
# }

# characters = [
#     {
#         "name": "Naruto Uzumaki",
#         "description": "The protagonist, a ninja of Konoha with the Nine-Tails fox sealed inside him. Dreams of becoming Hokage.",
#         "traits": ["determined", "loud", "optimistic", "loyal", "never gives up"]
#     },
#     {
#         "name": "Sasuke Uchiha",
#         "description": "Naruto’s rival and best friend, last survivor of the Uchiha clan. Obsessed with avenging his clan.",
#         "traits": ["cold", "brooding", "talented", "vengeful", "independent"]
#     },
#     {
#         "name": "Sakura Haruno",
#         "description": "Member of Team 7, skilled medical ninja, deeply cares about her friends.",
#         "traits": ["intelligent", "compassionate", "stubborn", "emotional"]
#     },
    # {
    #     "name": "Kakashi Hatake",
    #     "description": "Leader of Team 7, known as Copy Ninja. Calm, strategic, and highly skilled.",
    #     "traits": ["laid-back", "wise", "secretive", "loyal"]
    # },
    # {
    #     "name": "Hinata Hyuga",
    #     "description": "Member of the Hyuga clan, gentle but determined, deeply admires Naruto.",
    #     "traits": ["shy", "kind", "determined", "gentle"]
    # },
    # {
    #     "name": "Shikamaru Nara",
    #     "description": "Tactical genius, lazy but reliable when it counts.",
    #     "traits": ["lazy", "brilliant", "strategic", "loyal"]
    # }
# ]

Group = {
  "group_name": "Konoha Shinobi",
  "group_description": "A diverse group of ninjas from Konoha and allies, each with unique skills and personalities from Naruto Anime."
}


orchestrator_prompt = ChatPromptTemplate.from_template(
    """
    You are the orchestrator for the group: {group_name}.
    Group description: {group_desc}
    Characters: {characters}
    Summary of previous conversations:{existing_summary}
    User just asked: {user_message}
    Conversation so far regarding current user query:
    {history}
    consider feedback given by reviewer to select the character:{feedback}
   
    Decide which character should respond next based on:
    - Their role, description, and traits
    - Natural conversation flow

    Output ONLY valid JSON (no extra text).
    the speaker name should exactly match the speaker name given in character description
    Example format: "speaker": "speaker_name"
    """
)

character_prompt =  ChatPromptTemplate.from_template("""
    "system":
     "You are {character_name}, a member of {group_name}.\n"
     "Group description: {group_desc}\n"
     "Your description: {char_desc}\n"
     "Your traits: {char_traits}\n\n"
     "Summary of previous conversations:{existing_summary}"
     "User just asked: {user_message}\n\n"
     "Conversation so far regarding currentvuserquery:\n{history}\n\n"
     
     "Stay in character. Respond naturally to the user.\n\n"
     "Output ONLY valid JSON in this format:\n"
     '"speaker": "{character_name}", "message": "your_reply"'
"""
)

review_prompt = ChatPromptTemplate.from_template("""
You are a reviewer. Your task is to check if the current conversation history properly addresses the user's query.

- Required check: If the user mentions specific characters, make sure EACH of those characters has responded in the conversation history.  
- If any required character is missing, mark as unsatisfied and suggest which characters still need to respond.  
You are the orchestrator for the group: {group_name}.
Group description: {group_desc}
characters: {characters}
Summary of previous conversations:{existing_summary}
user_query: {user_message}
conversation_history of current user query:
{history}


Respond in strict JSON:

  "status": "satisfied" | "unsatisfied",
  "feedback": "Your explanation here. If unsatisfied, mention missing characters."

""")

summariser_prompt = ChatPromptTemplate.from_template("""
           You are a summariser that condenses long multi-character conversations 
           which is of the form character:dialogue 
           into a concise, coherent summary.
           group_name:{group_name}
           group_desc:{group_desc}
           characters_desc:{characters_desc}
           summary for previous queries:
           {history}
           user_query:{user_query}
           dialogues of current query:{new_dialogues}
           
           Your task:
           - Capture the main points of the discussion.
           - Highlight character perspectives only if relevant.
      
           - Output ONLY the summary text of both previous conversation(consider only previous two topics) and current dialogues(give more priority), no extra commentary.
           
           Summary:
""")

parser = JsonOutputParser()
strparser=StrOutputParser()
def format_history(history):
    """Convert history into a multiline string."""
    if not history:  # If history is empty
        return "No conversation yet."
        
    if isinstance(history, list):
        # Since we know history is a list of strings, just join them
        return "\n".join(history)
    elif isinstance(history, str):
        # Handle case where input is already a string
        return history
        
    return "No conversation yet."

def update_summary(existing_summary, new_dialogues, context):

    summarise_chain=summariser_prompt|llm|strparser
    input_data = {
        "group_name": context["group_name"],
        "group_desc": context["group_desc"],
        "characters_desc": context["characters_desc"],
        "user_query": context["user_query"],
        "history": existing_summary,
        "new_dialogues":new_dialogues
    }
    return summarise_chain.invoke(input_data)



def orchestrator_node(state):
    chain = orchestrator_prompt | llm | parser
    formatted_history = format_history(state.get("history", []))
    
    # Format the prompt content
    prompt_content = {
        "group_name": state.get("group_name", ""),
        "group_desc": state.get("group_description", ""),
        "characters": state.get("character_desc", ""),
        "history": formatted_history,
        "feedback":state.get("feedback",""),
        "user_message": state["user_message"],
        "existing_summary":state.get("summary",""),
    }
    
    try:
        # Create a proper message structure for Gemini
        # print(prompt_content)
        result = chain.invoke(prompt_content)
        
        # Ensure result is a string containing the speaker name
        if isinstance(result, dict) and "speaker" in result:
            state["speaker"]= result["speaker"]
            return state
        else:
            # Fallback to a default speaker if something goes wrong
            print("failed")
            return 
            
            
    except Exception as e:
        print(f"Error in orchestrator_node: {str(e)}")
        # Fallback to default speaker in case of error
        # state["speaker"]= "Naruto"
        return 


def character_node(state: ConversationState):
    # print(state)
    selected = next((char for char in state["characters"] if char["name"] == state["speaker"]), None)
    if selected is None:
        print(f"Character {state['speaker']} not found. Defaulting to first character.")
        selected = state["characters"][0]
    chain = character_prompt | llm | parser
    formatted_history = format_history(state.get("history", []))
    result = chain.invoke({
        "group_name": state.get("group_name", ""),
        "group_desc": state.get("group_desc", ""),
        "character_name": selected["name"],
        "char_desc": selected["description"],
        "char_traits": selected["traits"],
        "history": formatted_history,
        "user_message": state["user_message"],
        "existing_summary":state.get("summary",""),
    })
    result = {
        "speaker": result["speaker"],
        "message": result["message"]
    }
    new_line = f"{result['speaker']}: {result['message']}"
    state["dialogues"].append({result['speaker']: result["message"]})
    state["history"].append(new_line)
    state["speaker"] = result["speaker"]
    return state


def route_evaluation(state: ConversationState):
    if state['status'] == 'satisfied':
        return 'approved'
    else:
        return 'needs_improvement'


def review_node(state:ConversationState):
    chain=review_prompt|llm|parser
    formatted_history = format_history(state.get("history", []))
    result = chain.invoke({
        "group_name": state.get("group_name", ""),
        "group_desc": state.get("group_desc", ""),
        "characters": state.get("characters", ""),
        "history": formatted_history,
        "user_message": state["user_message"],
        "existing_summary":state.get("summary",""),
    })
    
    return result




graph = StateGraph(ConversationState)
graph.add_node("orchestrator_node", orchestrator_node)
graph.add_node("character_node", character_node)
graph.add_node("review_node", review_node)

graph.add_edge(START, "orchestrator_node")
graph.add_edge("orchestrator_node", "character_node")
graph.add_edge("character_node","review_node")
graph.add_conditional_edges('review_node', route_evaluation, {'approved': END, 'needs_improvement': 'orchestrator_node'})
workflow=graph.compile()

SESSIONS: Dict[str, Dict[str, Any]] = {}
class UserMessage(BaseModel):
    user_query: str
    group_name: str
    group_description: str
    characters:List[Dict]
    summary: str
    
# class ConversationState(Dict[str, Any]):
#     history: List[str] 
#     summary:str 
#     user_message:str
#     speaker:str
#     feedback:str
#     status:str
#     group_name:str
#     group_description:str
#     characters:List[Dict]
#     character_desc:str
#     dialogues:Dict




@app.post("/chat")
def chat(user_msg: UserMessage):
    # print(user_msg)
    character_desc="\n".join([
            f"{c['name']}: {c['description']}, Traits: {', '.join(c['traits'])}"
            for c in user_msg.characters
    ])
    characters=[c for c in user_msg.characters]
    existing_summary = user_msg.summary
    state = {
        "user_message": user_msg.user_query,
        "group_name": user_msg.group_name,
        "group_desc": user_msg.group_description,
        "character_desc": character_desc,
        "characters": characters,
        "summary": existing_summary,
        "history": [],
        "dialogues": [],
    }

    context = {
        "group_name": user_msg.group_name,
        "group_desc": user_msg.group_description,
        "characters_desc": character_desc,
        "user_query": user_msg.user_query,
    }

    final_state = workflow.invoke(state)
    new_dialogues = final_state["history"]
    existing_summary = update_summary(existing_summary, new_dialogues, context)
    return {
        "user_message": user_msg.user_query,
        "conv_summary": existing_summary,
        "dialogues": final_state.get("dialogues", []),
    }
    




# if __name__ == "__main__":
# User_request={
#     "user_query": "Tell me about Naruto and Sasuke's relationship.",
#     "group_name": Group["group_name"],
#     "group_description": Group["group_description"],
#     "characters": characters,
#     "summary": ""
# }
# response = chat(UserMessage(**User_request))
# pprint(response)