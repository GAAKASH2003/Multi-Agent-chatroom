from langgraph.graph import StateGraph, START, END
from graph.initialState import ConvoState
from nodes.orchestrator_node import orchestrator_node
from nodes.character_node import character_node
from nodes.review_node import review_node,route_evaluation
from nodes.input_node import input_node
from nodes.api_node import api_node
from nodes.memory_node import memory_node
from nodes.background_node import background_node

import requests
import time

graph = StateGraph(ConvoState)
graph.add_node("orchestrator_node",orchestrator_node)
graph.add_node("input_node",input_node)
graph.add_node("character_node",character_node)
graph.add_node("review_node",review_node)
graph.add_node("api_node",api_node)
graph.add_node("memory_node",memory_node)
graph.add_node("background_node",background_node)

# graph.add_edge("orchestrator_node","")
graph.add_edge(START,"input_node")
graph.add_edge("input_node","orchestrator_node")
graph.add_edge("orchestrator_node","character_node")
graph.add_edge("character_node","review_node")
graph.add_edge("review_node","api_node")
graph.add_conditional_edges('api_node', route_evaluation, {'approved': 'background_node', 'needs_improvement': 'orchestrator_node'})
graph.add_edge('background_node',END)
app = graph.compile()
# graph.add_edge('memory_node',END)

# graph.add_edge("review_node",END)


BASE_URL = "http://localhost:8000"  # change to your backend URL
user_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBYWthc2hAZ21haWwuY29tIiwidXNlcl9pZCI6IjZhMjFiMjkwNWI1ODdlNGZhNDU3NjM0YSIsImV4cCI6MTc4MjE1MDgzOH0.pP2G6xbmX7HL-mXQqRFwps6nESPRGZOQNGzFmvyBW-w"
grp_id="6a241cfcb29152fe5570a4e3"

        

# if __name__ == "__main__":
#     app = graph.compile()
#     test_state: ConvoState = {
#         "group_id": grp_id,
#         "group_name": "",
#         "group_description": "",
#         "characters": {},
#         "user_query": "Sanji ?",
#         "user_token":"",
#         "character": "",
#         "char_name":"",
#         "character_response":"",
#         "feedback":"",
#         "loop":0,
#         "status":"",
#         "dialogues":[],
#         "responded_characters":[],
#         "suggested_characters":[],
#         "conv_id":"",
#         "user_id":"6a21b2905b587e4fa457634a",
#         "user_email":"Aakash@gmail.com",
#         "recent_context":"",
#         "user_preferences":"",
#         "error":"",
#         "message_vectors":""
#     }
    
    # print(test_state)
    # result = app.invoke(test_state)

    # print("\n=== RESULT ===")
    # print(result)
 
 
 
 
#  {
#   "user_query": "Minna describe the most traumatic experience you have faced?",
#   "user_id": "6a21b2905b587e4fa457634a",
#   "user_email": "Aakash@gmail.com",
#   "group_id": "6a241cfcb29152fe5570a4e3"
# }
 
 
 
 
 
 
 
 
 
 
 
    
#   {
#   "group_id": "6a241cfcb29152fe5570a4e3",
#   "group_name": "One piece",
#   "group_description": "This is a group of pirates inspired from Onepiece Anime",
#   "characters": {
#     "6a270149539495195c8f87bb": {
#       "name": "Nami",
#       "traits": [
#         "intelligent",
#         "resourceful",
#         "greedy",
#         "caring",
#         "brave"
#       ],
#       "desc": "The navigator of the Straw Hat Pirates. An expert cartographer who dreams of drawing a map of the entire world."
#     },
#     "6a27018d539495195c8f87bc": {
#       "name": "Monkey D. Luffy",
#       "traits": [
#         "carefree",
#         "determined",
#         "fearless",
#         "loyal",
#         "optimistic"
#       ],
#       "desc": "Captain of the Straw Hat Pirates who gained rubber powers from the Gum-Gum Fruit. Dreams of becoming the Pirate King."
#     },
#     "6a2701a3539495195c8f87bd": {
#       "name": "Roronoa Zoro",
#       "traits": [
#         "disciplined",
#         "loyal",
#         "serious",
#         "strong-willed",
#         "honorable"
#       ],
#       "desc": "The swordsman of the Straw Hat Pirates who uses the Three-Sword Style. Aims to become the world's greatest swordsman."
#     },
#     "6a2701b7539495195c8f87be": {
#       "name": "Usopp",
#       "traits": [
#         "creative",
#         "cowardly",
#         "loyal",
#         "humorous",
#         "inventive"
#       ],
#       "desc": "The sniper of the Straw Hat Pirates known for his tall tales and creativity. Dreams of becoming a brave warrior of the sea."
#     },
#     "6a2701eb539495195c8f87bf": {
#       "name": "Sanji",
#       "traits": [
#         "chivalrous",
#         "passionate",
#         "kind-hearted",
#         "confident",
#         "loyal"
#       ],
#       "desc": "The cook of the Straw Hat Pirates and a master martial artist. Dreams of finding the All Blue."
#     }
#   },
#   "user_query": "Minna describe the most traumatic experience you have faced?",
#   "user_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBYWthc2hAZ21haWwuY29tIiwidXNlcl9pZCI6IjZhMjFiMjkwNWI1ODdlNGZhNDU3NjM0YSIsImV4cCI6MTc4MTk3NzIyMX0.0qwSL0oUhzt6cCO-s2D_mBdFzU6ew3LoZ-ln88_FdAY",
#   "recent_context": "",
#   "user_id":"6a21b2905b587e4fa457634a"
# }