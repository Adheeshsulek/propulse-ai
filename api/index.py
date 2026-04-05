import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Path handling for deployment
try:
    from .data import PROPERTIES
except ImportError:
    from data import PROPERTIES

load_dotenv()

# Gemini REST API (FIXED - no more v1beta issues)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-latest:generateContent"

app = FastAPI(title="Propulse AI Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    query: str


# 🔥 Gemini caller (SAFE + STABLE)
def call_gemini(prompt):
    response = requests.post(
        GEMINI_URL,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": os.environ.get("GEMINI_API_KEY"),
        },
        json={
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
    )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        print("Gemini error:", data)
        return "{}"


# Extract intent from user query
def extract_intent(query: str):
    prompt = f"""
    Extract real estate filters from the user query. Return ONLY valid JSON:
    {{
        "location": string or null,
        "max_price": integer or null,
        "bhk": integer or null,
        "amenities": []
    }}
    Query: "{query}"
    """

    response_text = call_gemini(prompt)

    try:
        return json.loads(response_text)
    except:
        return {}


# Generate explanations
def generate_explanations(intent, top_properties):
    if not top_properties:
        return {"reply": "No matching properties found.", "insights": []}

    prompt = f"""
    You are Propulse AI, a professional real estate agent.

    User intent: {json.dumps(intent)}
    Properties: {json.dumps(top_properties)}

    Return ONLY JSON:
    {{
        "reply": "Short professional response",
        "insights": [{{"id": "id", "ai_insight": "text"}}]
    }}
    """

    response_text = call_gemini(prompt)

    try:
        return json.loads(response_text)
    except:
        return {"reply": "Here are some good options for you.", "insights": []}


# Root route (health check)
@app.get("/")
@app.get("/api")
def read_root():
    return {
        "status": "Propulse AI API is running",
        "total_properties": len(PROPERTIES)
    }


# Main agent endpoint
@app.post("/api/agent")
@app.post("/agent")
async def run_agent(req: AgentRequest):
    try:
        intent = extract_intent(req.query)
        scored_props = []

        for p in PROPERTIES:
            if intent.get("max_price") and p["price"] > intent["max_price"]:
                continue
            if intent.get("bhk") and p["bhk"] != intent["bhk"]:
                continue

            score = 0

            if intent.get("location"):
                u_loc = intent["location"].lower()
                p_loc = p["location"].lower()
                if u_loc in p_loc or p_loc in u_loc:
                    score += 50

            scored_props.append({"property": p, "score": score})

        scored_props.sort(key=lambda x: x["score"], reverse=True)
        top_3 = [item["property"] for item in scored_props[:3]]

        ai_data = generate_explanations(intent, top_3)

        final_matches = []
        for p in top_3:
            insight_list = ai_data.get("insights", [])
            insight = "Ideal match for your preferences."

            for item in insight_list:
                if str(item.get("id")) == str(p.get("id")):
                    insight = item.get("ai_insight", insight)
                    break

            p_with_insight = p.copy()
            p_with_insight["ai_insight"] = insight
            final_matches.append(p_with_insight)

        return {
            "reply": ai_data.get("reply", "Here are the top picks based on your search."),
            "matches": final_matches
        }

    except Exception as e:
        print(f"Deployment Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))