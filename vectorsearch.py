import os
import json
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Create OpenAI client
openai_client = OpenAI(api_key=OPENAI_KEY)

# Connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Function: Get embedding
def get_embedding(text: str) -> list:
    res = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return res.data[0].embedding

# 🔍 Search based on user inputs
def search_real_estate(location: str, price: str, bedrooms: str, top_k=3):
    query = f"{bedrooms} bedroom property in {location} priced around {price}"
    vector = get_embedding(query)

    result = index.query(vector=vector, top_k=top_k, include_metadata=True)

    matches = []
    for match in result["matches"]:
        listing = json.loads(match["metadata"]["full"])
        full_listing = listing
        matches.append({
            "score": match["score"],
            "listing": full_listing
        })

    return matches

# 🔎 Test function
if __name__ == "__main__":
    location = input("Location: ")
    price = input("Price: ")
    bedrooms = input("Bedrooms: ")

    results = search_real_estate(location, price, bedrooms)
    print("\n✨ Top 3 Best Matches:")
    print("DEBUG: results =", results)
    if isinstance(results, dict) and 'matches' in results:
        matches = results['matches']
    else:
        matches = results
    for match in matches:
        if 'listing' in match:
            listing = match['listing']
        elif 'metadata' in match and 'full' in match['metadata']:
            import json
            listing = json.loads(match['metadata']['full'])
        else:
            print("No listing data found in match:", match)
            continue
        title = listing.get("title", "Untitled")
        print(f"Title: {title}")
