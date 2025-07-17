import os
import json
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Load keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Create OpenAI client
openai_client = OpenAI(api_key=OPENAI_KEY)

# Connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  # or your cloud provider
            region=PINECONE_ENV  # e.g., "us-west-2"
        )
    )

index = pc.Index(PINECONE_INDEX_NAME)

# Function to embed text
# Use the new OpenAI client

def get_embedding(text: str) -> list:
    res = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return res.data[0].embedding

# print(pc.list_indexes().to_dict())
# print("Embedding dimension:", len(get_embedding("test")))
# Prepare your data from JSON and upsert to Pinecone
def upsert_data(json_file="data.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        listings = json.load(f)

    vectors = []
    for i, listing in enumerate(tqdm(listings)):        
        id = f"listing-{i}"
        try:
            # Extract searchable fields
            title = listing.get("title", "")
            detail = listing.get("property_detail", {})
            desc = listing.get("description_detail", {})
            location = desc.get("Address", "")
            bedrooms = detail.get("BEDROOMS", "")
            price = detail.get("PRICE", "")
            structure = desc.get("Structure", "")
            summary = f"{title}. Located in {location}, priced at {price}, with {bedrooms} bedrooms. Type: {structure}"

            embedding = get_embedding(summary)

            vectors.append((id, embedding, {"full": json.dumps(listing, ensure_ascii=False)}))

            # chunk upload every 100
            if len(vectors) >= 100:
                index.upsert(vectors=vectors)
                vectors.clear()
        except Exception as e:
            print(f"Error processing listing {i}: {e}")

    if vectors:
        index.upsert(vectors=vectors)
    print("✅ Upload to Pinecone completed.")

# Run the upload
if __name__ == "__main__":
    upsert_data()
