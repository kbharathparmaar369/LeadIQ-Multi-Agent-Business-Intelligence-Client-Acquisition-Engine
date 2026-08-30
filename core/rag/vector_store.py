from sentence_transformers import SentenceTransformer
from core.config import supabase

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# turns a piece of text into 384 dim embedding vector
def embed_text(text: str) -> list[float]:
    vector = embedding_model.encode(text)
    return vector.tolist()

# Alias for compatibility
get_embedding = embed_text

def find_similar_case_studies(query_text: str, top_k: int = 2) -> list[dict]:
    if not supabase:
        print("Warning: Supabase client is not configured.")
        return []

    query_embedding = embed_text(query_text)

    response = supabase.rpc(
        "match_case_studies",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
        },
    ).execute()

    return response.data or []

if __name__ == "__main__":
    results = find_similar_case_studies("slow load time, no mobile optimization, missing SEO tags")
    for r in results:
        print(r)