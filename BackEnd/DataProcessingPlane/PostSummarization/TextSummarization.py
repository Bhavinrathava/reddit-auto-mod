from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class TextInput(BaseModel):
    text: str
    max_length: int = 2000

class SummarizationModel:
    def __init__(self, modelName = ""):
        self.modelName = modelName
        self.loadModel()
    
    def loadModel(self):
        self.summarizer = pipeline("summarization", model=self.modelName)

    
    def summarizeText(self, text, maxLength = 2000):

        try:
            return self.summarizer(text, max_length = maxLength)[0]['summary_text']
        
        except Exception as e :
            print("There was a error Summarizing the text : ", e)



app = FastAPI()

# Initialize model on startup
model = SummarizationModel("Falconsai/text_summarization") 

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify service is running and model is loaded
    """
    try:
        # Verify model is loaded
        if model.summarizer is None:
            return {"status": "unhealthy", "error": "Model not loaded"}
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/generatesummary")
async def generate_summary(input_data: TextInput):
    try:
        summary = model.summarizeText(input_data.text, input_data.max_length)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
