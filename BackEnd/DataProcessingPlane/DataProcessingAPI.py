import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from fastapi import FastAPI, HTTPException
import requests
from typing import Dict, List

from Utils.MongoWrapper import MongoWrapper
from Utils.RedditWrapper import RedditWrapper

from pydantic import BaseModel
# API endpoints for downstream services
API_ENDPOINTS = {
    "similarity": "http://localhost:8004",
    "summarization": "http://localhost:8002",
    "rule_violation": "http://localhost:8003"
}

class Credentials(BaseModel):
    client_id : str
    client_secret : str 
    user_agent : str 
    user_name : str 
    password : str 

class RequestPayload(BaseModel):
    credentials : Credentials 
    subredditList : list
app = FastAPI()

def check_api_health(api_name: str, base_url: str) -> Dict:
    """
    Check if a downstream API is healthy
    Args:
        api_name: Name of the API service
        base_url: Base URL of the API
    Returns:
        Dict with status and any error message
    """
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        return {"status": "healthy", "error": None}
    except requests.exceptions.RequestException as e:
        return {"status": "unhealthy", "error": str(e)}

@app.on_event("startup")
async def startup_event():
    """
    Check health of all downstream APIs on startup
    Raises HTTPException if any API is unhealthy
    """
    unhealthy_apis = []
    
    print("\nChecking downstream API health...")
    for api_name, base_url in API_ENDPOINTS.items():
        health_status = check_api_health(api_name, base_url)
        if health_status["status"] == "healthy":
            print(f"[+] {api_name} API is healthy")
        else:
            error_msg = health_status["error"]
            print(f"[-] {api_name} API is unhealthy: {error_msg}")
            unhealthy_apis.append(f"{api_name} ({error_msg})")
    
    if unhealthy_apis:
        raise HTTPException(
            status_code=503,
            detail=f"Some downstream APIs are not available: {', '.join(unhealthy_apis)}"
        )
    
    print("All downstream APIs are healthy!\n")

def initiateRedditObject(credentials=None):
    """
    Initialize Reddit object with credentials from config or provided credentials
    
    Args:
        credentials: Optional credentials dict. If None, loads from config file
    
    Returns:
        RedditWrapper instance
    """
    if credentials is None:
        # Load credentials from config file
        try:
            from cli.config import ConfigManager
            config_manager = ConfigManager()
            credentials = config_manager.get_reddit_credentials()
            if not credentials:
                raise ValueError("No credentials found. Please run 'reddit-auto-mod config' to set up credentials.")
        except Exception as e:
            raise ValueError(f"Error loading credentials: {e}")
    
    reddit = RedditWrapper(credentials=dict(credentials), subreddits=['DevModPro'])
    return reddit

def storeDatainDB(dbConnection, data):
    print(data)
    if dbConnection is None:
        dbConnection = initiateMongoWrapper()
    
    collection = dbConnection["ProcessedRedditSubmissions"]


    try:

        for subreddit, posts in data.items():

            collection.insert_many(posts)
        return True 
    
    except Exception as e:
        print(f'Error Encountered : {e}')
        return False 


def fetchDataFromRedditStream(redditObject : RedditWrapper, subredditList):
    posts = defaultdict(list)


    for subreddit in subredditList:
        try : 
            posts[subreddit] = redditObject.getQueueItems(subreddit)
        except Exception as e : 
            print(e)

    return posts 

def fetchRulesForReddit(mongoObject, subredditNames):
    
    collection = mongoObject["RedditRules"]
    rules = defaultdict(list)

    for subreddit in subredditNames:
        
        rules[subreddit] = list(collection.find({"subreddit": subreddit}))

    return rules 
        



def getPostSummaries(posts):
    """
    Enrich posts with text summaries by calling the summarization API
    Args:
        posts: Dictionary with subreddit names as keys and lists of posts as values
    Returns:
        The posts dictionary with summaries added to each post
    """
    import requests
    
    SUMMARY_API_URL = API_ENDPOINTS["summarization"] + "/generatesummary"
    
    for subreddit, subreddit_posts in posts.items():
        for post in subreddit_posts:
            try:
                # Combine title and text for summarization
                full_text = f"{post.get('submission_title', '')} {post.get('submission_text', '')}"
                
                # Prepare request payload
                payload = {
                    "text": full_text,
                    "max_length": 2000  # Default max length from TextSummarization.py
                }
                
                # Make request to summarization API
                response = requests.post(SUMMARY_API_URL, json=payload)
                response.raise_for_status()
                
                # Add summary directly to the post
                summary_data = response.json()
                post["post_summary"] = summary_data["summary"]
                
            except requests.exceptions.RequestException as e:
                print(f"Error generating summary for post {post.get('submission_id')}: {str(e)}")
                post["post_summary"] = f"Error generating summary: {str(e)}"
            except Exception as e:
                print(f"Unexpected error for post {post.get('submission_id')}: {str(e)}")
                post["post_summary"] = f"Error generating summary: {str(e)}"
    
    return posts

def getRuleViolations(posts, rules):
    """
    Enrich posts with rule violation data by calling the rule violation API
    Args:
        posts: Dictionary with subreddit names as keys and lists of posts as values
        rules: Dictionary with subreddit names as keys and lists of rule objects as values
    Returns:
        The posts dictionary with rule violation data added to each post
    """
    import requests
    
    VIOLATION_API_URL = API_ENDPOINTS["rule_violation"] + "/ruleViolations"
    
    for subreddit, subreddit_posts in posts.items():
        try:
            # Get rules for this subreddit
            subreddit_rules = [rule["rule"] for rule in rules.get(subreddit, [])]
            
            if not subreddit_rules:
                print(f"No rules found for subreddit {subreddit}, skipping violation check")
                continue
                
            # Prepare posts for the API request
            post_list = []
            for post in subreddit_posts:
                post_list.append({
                    "postText": post.get("submission_text", ""),
                    "postTitle": post.get("submission_title", ""),
                    "postId": post.get("submission_id", "")
                })
            
            # Prepare request payload
            payload = {
                "posts": post_list,
                "subredditRules": subreddit_rules
            }
            
            # Make request to rule violation API
            response = requests.post(VIOLATION_API_URL, json=payload)
            response.raise_for_status()
            
            # Process response and add violation data to posts
            violation_data = response.json()
            
            # Map results back to original posts using postId
            results_map = {result["postId"]: result for result in violation_data["results"]}
            
            # Add violation data to each post
            for post in subreddit_posts:
                post_id = post.get("submission_id")
                if post_id in results_map:
                    post["rule_violations"] = {
                        "violations": results_map[post_id]["ruleViolations"],
                        "violation_detected": results_map[post_id]["violationDetected"]
                    }
                else:
                    post["rule_violations"] = {
                        "error": "No violation analysis results found for this post"
                    }
                
        except requests.exceptions.RequestException as e:
            print(f"Error checking rule violations for subreddit {subreddit}: {str(e)}")
            for post in subreddit_posts:
                post["rule_violations"] = {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error processing rule violations for subreddit {subreddit}: {str(e)}")
            for post in subreddit_posts:
                post["rule_violations"] = {"error": f"Processing error: {str(e)}"}
    
    return posts

def getPostSimilarity(posts):
    """
    Enrich posts with similarity scores by calling the similarity API
    Args:
        posts: Dictionary with subreddit names as keys and lists of posts as values
    Returns:
        The posts dictionary with similarity data added to each post
    """
    import requests
    
    SIMILARITY_API_URL = API_ENDPOINTS["similarity"] + "/similarity"
    
    for subreddit, subreddit_posts in posts.items():
        for post in subreddit_posts:
            try:
                # Prepare request payload
                payload = {
                    "post_title": post.get("submission_title", ""),
                    "post_text": post.get("submission_text", ""),
                    "subreddit": subreddit,
                    "k": 10,  # Number of nearest neighbors to consider
                    "nprobe": 2  # Search parameter for FAISS
                }
                
                # Make request to similarity API
                response = requests.post(SIMILARITY_API_URL, json=payload)
                response.raise_for_status()
                
                # Add similarity data directly to the post
                post["similarity_data"] = response.json()
                
            except requests.exceptions.RequestException as e:
                print(f"Error calculating similarity for post {post.get('submission_id')}: {str(e)}")
                post["similarity_data"] = {"error": str(e)}
            except Exception as e:
                print(f"Unexpected error for post {post.get('submission_id')}: {str(e)}")
                post["similarity_data"] = {"error": str(e)}
    
    return posts

def initiateMongoWrapper():
    mongo =  MongoWrapper()
    return mongo.get_connection()

@app.get("/health")
async def health_check() -> Dict:
    """
    Health check endpoint to verify API and all downstream service connectivity
    
    Returns:
        Dict with status of the API and all downstream services
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check MongoDB connection
    try:
        mongo = MongoWrapper()
        if not mongo.is_connected():
            health_status["status"] = "degraded"
            health_status["services"]["mongodb"] = {
                "status": "unhealthy",
                "error": "Database disconnected"
            }
        else:
            health_status["services"]["mongodb"] = {
                "status": "healthy"
            }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check downstream APIs
    return health_status


@app.post("/initiateProcesing")
async def initiateProcessing(payload : RequestPayload):
    
    credentials = payload.credentials
    subredditList = payload.subredditList

    reddit = initiateRedditObject(credentials)
    mongoConnection = initiateMongoWrapper()

    redditPosts = fetchDataFromRedditStream(reddit, subredditList)

    if(not redditPosts or len(redditPosts) == 0):
        return {"ERROR": "No Posts Found", "CODE": 400}
    
    print(redditPosts)
    
    redditRules = fetchRulesForReddit(mongoConnection, subredditList)

    if(not redditRules or len(redditRules) == 0):
        return {"ERROR": "No Rules Found", "CODE": 400}
    
    print(redditRules)

    redditPosts = getPostSummaries(redditPosts)
    print("Generated Summaries for Posts!")

    redditPosts = getPostSimilarity(redditPosts)
    print("Calculated Similarities for the Posts!")

    redditPosts = getRuleViolations(redditPosts, redditRules)
    print("Checked Rule Violations for the posts!")

    storeDatainDB(mongoConnection, redditPosts)

    return {
        "Message": "Success",
        "Code" : "200"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

'''
Test payload for InitiateDataProcessing endpoint:
{
    "credentials": {
        "client_id": "cF0iy7hJIXo85k-kra2w-g",
        "client_secret": "A5F_F6NZKXbpL45uPu37vCivnohmEg",
        "user_agent": "Python-Script-Dev-Testing",
        "username": "Motor_Glove4483",
        "password": "#IamBhavin1998"
    },
    "subredditList": ["DevTestModPro", "explainlikeimfive"]
}

Test submission:
{
    "_id": {"$oid":"65fcba39501d615bfefbec24"},
    "subreddit": "explainlikeimfive",
    "submission_id": "1bkakb2",
    "submission_name": "t3_1bkakb2",
    "submission_title": "ELI5: Emergency Surgery",
    "submission_text": "If someone goes in for emergency surgery requiring general anesthesia, how do you prevent aspiration assuming they ate beforehand since it was unplanned?"
}
'''
