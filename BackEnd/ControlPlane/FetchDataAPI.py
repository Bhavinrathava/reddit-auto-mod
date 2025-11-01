from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.MongoWrapper import MongoWrapper
from Utils.RedditWrapper import RedditWrapper
from pydantic import BaseModel
from bson import ObjectId

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_wrapper = MongoWrapper()

MODQUEUE_TYPE_TRANSLATION = {
    "unmoderated" : "modqueue",
    "edited" : "edited",
    "needs-review" : "needs-review",
    "removed"  : "removed",
    "reported" : "reported"
    }

# Initialize RedditWrapper
credentials = {
    'client_id': 'cF0iy7hJIXo85k-kra2w-g',
    'client_secret': 'A5F_F6NZKXbpL45uPu37vCivnohmEg',
    'user_agent': 'Python-Script-Dev-Testing',
    'username': "Motor_Glove4483",
    'password': "#IamBhavin1998"
}
reddit_wrapper = RedditWrapper(credentials=credentials, subreddits=[])

@app.get("/api/fetch/{subreddit}")
async def fetch_subreddit_data(
    subreddit: str, 
    queue_type: str,
    limit: Optional[int] = None
) -> List[Dict[Any, Any]]:
    """
    Fetch processed Reddit submissions from MongoDB based on subreddit name and queue type
    
    Args:
        subreddit (str): Name of the subreddit to fetch data for
        queue_type (str): Type of queue to fetch from
        limit (Optional[int]): Maximum number of submissions to return. If None, returns all submissions.
        
    Returns:
        List[Dict[Any, Any]]: List of processed Reddit submissions
        
    Raises:
        HTTPException: If database connection fails or other errors occur
    """
    try:
        # Get MongoDB connection
        db = mongo_wrapper.get_connection()
        if db is None :
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to database"
            )
            
        # Query the ProcessedRedditSubmissions collection
        collection = db["ProcessedRedditSubmissions"]
        
        # Build query based on queue type
        query = {"subreddit": subreddit}
        
        if queue_type == "reported":
            # For reported items, only check actionTaken
            query["actionTaken"] = True
        elif queue_type == "removed":
            # For removed items, check actionTaken and status
            query["actionTaken"] = True
            query["status"] = "removed"
        else:
            # For other queue types, use itemType
            query["itemType"] = MODQUEUE_TYPE_TRANSLATION[queue_type]
            query["actionTaken"] = False
        
        # Validate limit parameter
        if limit is not None:
            if limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Limit must be a positive integer"
                )
            cursor = collection.find(query).limit(limit)
        else:
            cursor = collection.find(query)

        submissions = list(cursor)
        
        # Handle empty results
        if not submissions:
            print(f"No items found for subreddit: {subreddit}, queue_type: {queue_type}")
            return []
        
        # Convert ObjectId to string for JSON serialization
        for submission in submissions:
            if '_id' in submission:
                submission['_id'] = str(submission['_id'])
        
        print(f"Returning {len(submissions)} items for {subreddit}")
        return submissions
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching data: {str(e)}"
        )


class PostAction(BaseModel):
    """Model for post action request"""
    submission_id: str
    approve: bool
    item_type: str  # 'submission' or 'comment'

@app.post("/api/post/action")
async def take_post_action(action: PostAction) -> Dict[str, Any]:
    """
    Update post status in MongoDB and take action on Reddit
    
    Args:
        action (PostAction): Contains submission_id, approve flag, and item type
        
    Returns:
        Dict[str, Any]: Action result status
        
    Raises:
        HTTPException: If database connection fails or post not found
    """
    try:
        # Get MongoDB connection
        db = mongo_wrapper.get_connection()
        if  db is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to database"
            )
            
        # Query the ProcessedRedditSubmissions collection
        collection = db["ProcessedRedditSubmissions"]
        
        # Take action on Reddit
        try:
            item_details = {
                'id': action.submission_id,
                'type': action.item_type
            }
            reddit_wrapper.takeAction(item_details, action.approve)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to take action on Reddit: {str(e)}"
            )
        
        # Update MongoDB status
        result = collection.find_one_and_update(
            {"id": action.submission_id},  # Filter to find the document
            {"$set": {
                "status": "approved" if action.approve else "removed",
                "actionTaken": True
            }},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post with ID {action.submission_id} not found"
            )
            
        # Convert ObjectId to string for JSON serialization
        if '_id' in result:
            result['_id'] = str(result['_id'])
            
        return {
            "status": "success",
            "message": f"Post {'approved' if action.approve else 'banned'} successfully",
            "post": result
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing action: {str(e)}"
        )

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify API and database connectivity
    
    Returns:
        Dict[str, str]: Status of the API and database connection
    """
    try:
        is_connected = mongo_wrapper.is_connected()
        if not is_connected:
            return {"status": "degraded", "database": "disconnected"}
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
