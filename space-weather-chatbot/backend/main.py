import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prediction_loader import get_latest_prediction
from llm_service import generate_chat_response

app = FastAPI(title="Space Weather Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Retrieve live prediction dynamically from our CatBoost model
    prediction = get_latest_prediction()
    
    if prediction is None:
        return {"response": "Data unavailable. I'm currently unable to retrieve the latest live forecasting data from the solar APIs."}

    # Pass the user query + predicted probabilities to the LLM agent
    reply = generate_chat_response(request.message, prediction)
    
    return {"response": reply}

# Mount the static frontend so it runs on port 8000 alongside the API
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def fallback():
        return {"error": "Frontend directory not found at " + frontend_dir}
