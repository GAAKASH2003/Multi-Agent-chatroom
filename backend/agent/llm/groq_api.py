from pydantic import SecretStr
from langchain_groq import ChatGroq
# from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
# from db.dbConnection import get_collection
import os
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

def get_groq_llm():
        # model="openai/gpt-oss-120b",
        # model="llama-3.3-70b-versatile",
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0.5
    )


def get_qwen_llm():
    return ChatGroq(
        model="qwen3-32b",
        api_key=SecretStr(api_key) if api_key else None,
        temperature=0.5
    )

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)
def embed_document(text: str) -> list[float]:
    """Use when storing message content into DB"""
    prefixed = f"search_document: {text}"
    embedding = model.encode(prefixed, normalize_embeddings=True)
    return embedding.tolist()

def embed_query(text: str) -> list[float]:
    """Use when searching with user query"""
    prefixed = f"search_query: {text}"
    embedding = model.encode(prefixed, normalize_embeddings=True)
    return embedding.tolist()

# def searchSimilarMessages(query: str, limit: int = 5) -> list:
#     msg_collection = get_collection("messages")

#     # Query prefix for searching
#     query_embedding = embed_query(query)

#     results = msg_collection.aggregate([
#         {
#             "$vectorSearch": {
#                 "index": "message_vector_index",
#                 "path": "embedding",
#                 "queryVector": query_embedding,
#                 "numCandidates": 50,
#                 "limit": limit
#             }
#         },
#         {
#             "$project": {
#                 "content": 1,
#                 "sender_id": 1,
#                 "score": {"$meta": "vectorSearchScore"}
#             }
#         }
#     ])

#     return list(results)

# print(len(embed_document("Hello I am going to park?")))


# llm=get_groq_llm()

# messages = [
#     (
#         "system",
#         "You are a helpful assistant that translates English to japanese. Translate the user sentence.",
#     ),
#     ("human", "I hate you."),
# ]
# ai_msg = llm.invoke(messages)
# print(ai_msg.content)


# print(os.getenv("VERCEL_AI_KEY",""))
# embedder = OpenAIEmbeddings(
#     model="text-embedding-3-small",
#     api_key=vercel_api_key,
#     base_url="https://ai-gateway.vercel.sh/v1",
#     dimensions=1536  
# )

# def embed_document(text: str) -> list[float]:
#     # Clean text before embedding
#     text = text.strip()
#     if not text:
#         raise ValueError("Cannot embed empty text")
#     return embedder.embed_documents([text])[0]

# def embed_query(text: str) -> list[float]:
#     text = text.strip()
#     if not text:
#         raise ValueError("Cannot embed empty query")
#     return embedder.embed_query(text)




# vercel_api_key=SecretStr(os.getenv("VERCEL_AI_KEY",""))

# client = OpenAI(
#     api_key=os.getenv("VERCEL_AI_KEY",""),
#     base_url="https://ai-gateway.vercel.sh/v1"
# )

# response = client.embeddings.create(
#     model="text-embedding-3-small",
#     input="test message"
# )
# print(response.data[0].embedding[:5])

# # Test 2 — with provider prefix if above fails
# response = client.embeddings.create(
#     model="openai/text-embedding-3-small",
#     input="test message"
# )
# print(response.data[0].embedding[:5])