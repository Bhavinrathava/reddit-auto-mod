from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
import json

app = FastAPI()

class Violation(BaseModel):
    rule: str
    violating_text: str
    explanation: str

class Post(BaseModel):
    postText: str
    postTitle: str
    postId: str = None  # Optional identifier for the post

class RuleViolationRequest(BaseModel):
    posts: list[Post]
    subredditRules: list[str]

class PostViolationResult(BaseModel):
    postId: str
    postTitle: str
    ruleViolations: list[Violation]
    violationDetected: bool

class RuleViolationResponse(BaseModel):
    results: list[PostViolationResult]
    totalPostsAnalyzed: int
    totalViolationsFound: int

# Base prompt for OpenAI
BASEPROMPT = """You are a Reddit moderation assistant. Your task is to analyze a post and determine if it violates any subreddit rules.

You will be given:
1. A post title
2. A post text/body
3. A list of subreddit rules

Your job is to:
- Carefully read each rule
- Examine the post title and text for ANY violations of these rules
- Extract the EXACT text from the post (title or body) that violates each rule
- Provide a brief explanation of why it violates that rule

Return your analysis as a JSON object with this structure:
{
    "violations": [
        {
            "rule": "The exact rule text that was violated",
            "violating_text": "The exact quote from the post title or text that violates this rule",
            "explanation": "Brief explanation of why this text violates the rule"
        }
    ]
}

If no violations are found, return:
{
    "violations": []
}

Be thorough but fair. Only flag clear violations, not borderline cases unless they obviously break the rule.
Only return valid JSON, no additional text or markdown.
"""

# Initialize OpenAI client
# Load API key from config file
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from cli.config import ConfigManager
    config_manager = ConfigManager()
    api_key = config_manager.get_openai_key()
    if not api_key:
        print("WARNING: No OpenAI API key found in config. Please run 'reddit-auto-mod config' to set up credentials.")
        api_key = os.getenv('OPENAI_API_KEY', '')  # Fallback to environment variable
except Exception as e:
    print(f"Error loading OpenAI key from config: {e}")
    api_key = os.getenv('OPENAI_API_KEY', '')  # Fallback to environment variable

client = OpenAI(api_key=api_key)

@app.post("/ruleViolations", response_model=RuleViolationResponse)
def ruleViolations(ruleViolationRequest: RuleViolationRequest):
    try:
        results = []
        total_violations = 0
        
        # Process each post
        for idx, post in enumerate(ruleViolationRequest.posts):
            # Generate a post ID if not provided
            post_id = post.postId if post.postId else f"post_{idx + 1}"
            
            # Prepare the prompt for this specific post
            user_prompt = f"""
POST TITLE: {post.postTitle}

POST TEXT: {post.postText}

SUBREDDIT RULES:
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(ruleViolationRequest.subredditRules))}

Analyze this post for rule violations and return the result in JSON format.
"""
            
            # Send request to OpenAI
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": BASEPROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            # Process response
            response_text = response.choices[0].message.content
            
            # Extract JSON from response (handle potential markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse the JSON response
            parsed_response = json.loads(response_text)
            
            # Convert to our response model
            violations = [
                Violation(
                    rule=v["rule"],
                    violating_text=v["violating_text"],
                    explanation=v["explanation"]
                )
                for v in parsed_response.get("violations", [])
            ]
            
            # Create result for this post
            post_result = PostViolationResult(
                postId=post_id,
                postTitle=post.postTitle,
                ruleViolations=violations,
                violationDetected=len(violations) > 0
            )
            
            results.append(post_result)
            total_violations += len(violations)
        
        return RuleViolationResponse(
            results=results,
            totalPostsAnalyzed=len(ruleViolationRequest.posts),
            totalViolationsFound=total_violations
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/")
def read_root():
    return {"message": "Reddit Rule Violation Checker API", "endpoint": "/ruleViolations"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
