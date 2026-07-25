from pydantic import SecretStr
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
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
