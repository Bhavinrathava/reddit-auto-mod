from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List
import os

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')
index_cache = {}
id_cache = {}

class PostSimilarityRequest(BaseModel):
    post_title: str
    post_text: str
    subreddit: str
    k: int = 10  # Number of neighbors to consider for similarity
    nprobe: int = 2

class SubredditFitRequest(BaseModel):
    post_title: str
    post_text: str
    subreddits: List[str]  # Check against multiple subreddits
    k: int = 10

class SimilarityScore(BaseModel):
    subreddit: str
    similarity_score: float  # 0-1, higher = more similar
    avg_distance: float
    min_distance: float
    max_distance: float
    nearest_neighbors: List[Dict]

def load_index(subreddit_name):
    """Load index and ID mapping for a subreddit"""
    if subreddit_name in index_cache:
        return index_cache[subreddit_name], id_cache[subreddit_name]
    
    # Use user's home directory for index files (works with installed packages)
    from pathlib import Path
    index_dir = Path.home() / ".reddit-auto-mod" / "indexes"
    index_path = index_dir / f"{subreddit_name}.faiss"
    ids_path = index_dir / f"{subreddit_name}_ids.pkl"
    
    print(f"Looking for files at:")
    print(f"Index path: {index_path}")
    print(f"IDs path: {ids_path}")
    
    # Convert Path objects to strings for compatibility
    index_path = str(index_path)
    ids_path = str(ids_path)
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index not found at: {index_path}")
    if not os.path.exists(ids_path):
        raise FileNotFoundError(f"IDs file not found at: {ids_path}")
    
    index = faiss.read_index(index_path)
    with open(ids_path, "rb") as f:
        doc_ids = pickle.load(f)
    
    index_cache[subreddit_name] = index
    id_cache[subreddit_name] = doc_ids
    
    return index, doc_ids

def calculate_similarity_score(distances):
    """
    Convert distances to similarity score (0-1 range)
    Lower distance = higher similarity
    """
    # Method 1: Using average distance and converting to similarity
    avg_distance = np.mean(distances)
    
    # Convert to similarity score (using exponential decay)
    # You can tune the decay factor based on your data
    similarity = np.exp(-avg_distance / 10)  # Adjust denominator to tune sensitivity
    
    return float(similarity)

def calculate_advanced_similarity(distances):
    """
    More sophisticated similarity calculation
    Returns score between 0-1
    """
    # Use harmonic mean of similarities for better penalty on outliers
    similarities = [1 / (1 + d) for d in distances]
    
    # Harmonic mean
    harmonic_mean = len(similarities) / sum(1/s for s in similarities)
    
    return float(harmonic_mean)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify service is running and model is loaded
    """
    try:
        # Verify model is loaded
        if model is None:
            return {"status": "unhealthy", "error": "Model not loaded"}
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/similarity", response_model=SimilarityScore)
async def get_post_similarity(request: PostSimilarityRequest):
    """
    Calculate how similar a new post is to existing posts in a subreddit
    """
    try:
        # Load index
        index, doc_ids = load_index(request.subreddit)
        print("Loaded Index")

        # Create embedding for the new post
        post_content = request.post_title + " " + request.post_text
        post_embedding = model.encode([post_content]).astype('float32')
        
        print("Generated Query Embedding")
        # Set search parameters
        index.nprobe = request.nprobe
        
        # Find k nearest neighbors
        distances, indices = index.search(post_embedding, request.k)
        
        # Extract distances for this query
        neighbor_distances = distances[0]
        neighbor_indices = indices[0]
        
        # Calculate similarity metrics
        avg_distance = float(np.mean(neighbor_distances))
        min_distance = float(np.min(neighbor_distances))
        max_distance = float(np.max(neighbor_distances))
        
        # Calculate overall similarity score
        similarity_score = calculate_advanced_similarity(neighbor_distances)
        
        # Get nearest neighbor details
        nearest_neighbors = []
        for idx, dist in zip(neighbor_indices, neighbor_distances):
            if idx < len(doc_ids):
                nearest_neighbors.append({
                    'document_id': doc_ids[idx],
                    'distance': float(dist),
                    'similarity': float(1 / (1 + dist))
                })
        
        return SimilarityScore(
            subreddit=request.subreddit,
            similarity_score=similarity_score,
            avg_distance=avg_distance,
            min_distance=min_distance,
            max_distance=max_distance,
            nearest_neighbors=nearest_neighbors
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
