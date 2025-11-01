
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.MongoWrapper import MongoWrapper

import faiss 
import numpy as np 
import pickle

from tqdm import tqdm

from sentence_transformers import SentenceTransformer

def enrichWithEmbeddings(items):
    model = SentenceTransformer('all-MiniLM-L6-v2') 

    for item in tqdm(items) : 

        textContent = item.get('submission_text', "") + item.get("submission_title", "")

        embedding = model.encode(textContent)
        embedding = embedding.astype('float32')

        item['embedding'] = embedding
    
    return items

def getItemsInMongoCollection():
    mongoWrapper = MongoWrapper()
    connection = mongoWrapper.get_connection()

    # Load all the items in Memory 
    collection = connection['RedditSubmissions']
    items = list(collection.find())

    items = enrichWithEmbeddings(items)

    # Process the entries (optional)
    subredditToPost = defaultdict(list)

    for item in items:
        subredditToPost[item['subreddit']].append(item)    
    
    return subredditToPost

def createIndex(items, subredditName = "Default"):

    dimension = len(items[0]['embedding'])

    embeddings = np.array([item['embedding'] for item in items], dtype = 'float32')

    quantizer = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFFlat(quantizer, dimension, 3)

    index.train(embeddings)

    index.add(embeddings)

    faiss.write_index(index, subredditName + ".faiss")

    doc_ids = [str(item['submission_id']) for item in items]

    with open(subredditName + "_ids.pkl", "wb") as f:
        pickle.dump(doc_ids, f)





def main():

    posts = getItemsInMongoCollection()

    for subreddit in posts : 
        createIndex(posts[subreddit], subreddit)

    return 



if __name__ == "__main__":
    main()
