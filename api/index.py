import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Path handling
try:
    from .data import PROPERTIES
except ImportError:
    from data import PROPERTIES

load_dotenv()

# Gemini REST API
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-latest:generateContent"

app = FastAPI(title="Propulse AI Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    query: str


# 🔥 LOCATION INTELLIGENCE MAP
LOCATION_MAP = {
    "south bangalore": ["kanakapura", "bannerghatta", "begur", "electronic city", "btm", "jp nagar"],
    "east bangalore": ["whitefield", "sarjapur", "varthur", "kr puram", "itpl"],
    "north bangalore": ["hebbal", "yelahanka", "thanisandra", "devanahalli"],
    "west bangalore": ["rajarajeshwari", "kengeri", "vijayanagar"],
}


# 🔥 GEMINI CALL
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


# 🔥 INTENT EXTRACTION
def extract_intent(query: str):
    prompt = f"""
    Extract real estate filters from the user query. Return ONLY JSON:
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


# 🔥 AI EXPLANATION
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
        return {"reply": "Here are some great options for you.", "insights": []}


# Root route
@app.get("/")
@app.get("/api")
def read_root():
    return {
        "status": "Propulse AI API is running",
        "total_properties": len(PROPERTIES)
    }


# 🔥 MAIN AGENT
@app.post("/api/agent")
@app.post("/agent")
async def run_agent(req: AgentRequest):
    try:
        intent = extract_intent(req.query)
        scored_props = []

        for p in PROPERTIES:

            # 🔥 BHK FILTER
            if intent.get("bhk") and p["bhk"] != intent["bhk"]:
                continue

            # 🔥 PRICE FILTER
            if intent.get("max_price") and p["price"] > intent["max_price"]:
                continue

            # 🔥 LUXURY / AFFORDABLE LOGIC
            query_lower = req.query.lower()

            if "luxury" in query_lower:
                if p["price"] < 15000000:
                    continue

            if "affordable" in query_lower:
                if p["price"] > 8000000:
                    continue

            score = 0

            # 🔥 LOCATION MATCHING (SMART)
            if intent.get("location"):
                u_loc = intent["location"].lower()
                p_loc = p["location"].lower()

                # direct match
                if u_loc in p_loc:
                    score += 50

                # mapped match
                elif u_loc in LOCATION_MAP:
                    for area in LOCATION_MAP[u_loc]:
                        if area in p_loc:
                            score += 40

            scored_props.append({"property": p, "score": score})

        # 🔥 SORT + TAKE TOP 5
        scored_props.sort(key=lambda x: x["score"], reverse=True)
        top_props = [item["property"] for item in scored_props[:5]]

        # 🔥 AI RESPONSE
        ai_data = generate_explanations(intent, top_props)

        final_matches = []

        for p in top_props:
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
            "reply": ai_data.get("reply", "Here are the top matches for you."),
            "matches": final_matches
        }

    except Exception as e:
        print(f"Deployment Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))