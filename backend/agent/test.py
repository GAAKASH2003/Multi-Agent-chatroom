from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1",
    trust_remote_code=True
)

contents = [
    "Nami:My dream is to draw a map of the entire world! I want to be the greatest navigator and cartographer, and have a treasure that'll let me live a life of luxury!",
    "Monkey D. Luffy:My dream is to become the Pirate King! I want to sail the seas, find One Piece, and be the greatest pirate of all time!",
    "Nami:Ugh, don't remind me... It was when Arlong and his crew took over my hometown, Cocoyasi Village. They enslaved my friends and family, and I was forced to draw maps for them.",
    "Sanji:Ah, Nami-san's heart bears the scars of Arlong's tyranny.",
    "Sanji:My dream is to become a brave warrior of the sea, just like my idol, Ryugu!",
    "Usopp:My dream is to become a brave warrior of the sea!",
    "Nami:My favorite crew member has to be Sanji.",
    "Sanji:My favorite crew member has to be Nami-san.",
    "Roronoa Zoro:My dream is to become the world's greatest swordsman."
]

query = "what is nami's dream?"

# Nomic recommends task prefixes
query_emb = model.encode(
    f"search_query: {query}",
    convert_to_numpy=True
)

doc_embs = model.encode(
    [f"search_document: {doc}" for doc in contents],
    convert_to_numpy=True
)

scores = cosine_similarity(
    query_emb.reshape(1, -1),
    doc_embs
)[0]

for content, score in sorted(
    zip(contents, scores),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{score:.4f} -> {content[:100]}")
