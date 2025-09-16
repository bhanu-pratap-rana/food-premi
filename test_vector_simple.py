"""
Simple test for vector functionality using sentence-transformers only
"""
import os
import numpy as np
from sentence_transformers import SentenceTransformer

def test_embeddings():
    print("Testing sentence-transformers embeddings...")

    # Initialize model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Test texts
    texts = [
        "Our restaurant serves fresh organic vegetables and healthy meals.",
        "We offer catering services for events and parties.",
        "All ingredients are locally sourced and certified organic."
    ]

    # Generate embeddings
    embeddings = model.encode(texts, normalize_embeddings=True)
    print(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")

    # Test similarity
    query = "healthy organic food"
    query_embedding = model.encode([query], normalize_embeddings=True)[0]

    # Calculate similarities
    similarities = np.dot(embeddings, query_embedding)

    print(f"\nQuery: '{query}'")
    print("Similarity scores:")
    for i, (text, score) in enumerate(zip(texts, similarities)):
        print(f"{i+1}. {score:.3f} - {text[:50]}...")

    print("Vector Store Embedding Test PASSED")

if __name__ == "__main__":
    test_embeddings()