import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure this matches the filename data.py in the same folder
from data import PROPERTIES

load_dotenv()

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env file")
else:
    genai.configure(api_key=api_key)

app = FastAPI(title="Propulse AI Backend")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    query: str

def extract_intent(query: str):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Extract real estate filters from the user query. Return ONLY valid JSON with:
    {{
        "location": string or null,
        "max_price": integer or null,
        "bhk": integer or null,
        "amenities": [list of strings]
    }}
    User Query: "{query}"
    """
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )
    return json.loads(response.text)

def generate_explanations(intent, top_properties):
    if not top_properties:
        return {"reply": "I couldn't find any properties matching those exact criteria.", "insights": []}
        
    model = genai.GenerativeModel('gemini-2.5-flash')
    props_context = [{"id": p["id"], "title": p["title"], "price": p["formatted_price"], "bhk": p["bhk"], "location": p["location"]} for p in top_properties]
    
    prompt = f"""
    You are Propulse AI, a professional real estate agent.
    User intent: {json.dumps(intent)}
    Selected properties: {json.dumps(props_context)}
    Explain why these match the user's needs. Return ONLY JSON:
    {{
        "reply": "1-sentence professional opening.",
        "insights": [{{ "id": "property_id", "ai_insight": "1 persuasive sentence." }}]
    }}
    """
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return json.loads(response.text)

@app.post("/agent")
async def run_agent(req: AgentRequest):
    try:
        intent = extract_intent(req.query)
        scored_props = []
        
        # Filtering logic
        for p in PROPERTIES:
            if intent.get("max_price") and p["price"] > intent["max_price"]:
                continue
            if intent.get("bhk") and p["bhk"] != intent["bhk"]:
                continue
                
            score = 0
            if intent.get("location") and intent["location"].lower() in p["location"].lower():
                score += 10
            
            scored_props.append({"property": p, "score": score})
            
        scored_props.sort(key=lambda x: x["score"], reverse=True)
        top_3 = [item["property"] for item in scored_props[:3]]
        
        ai_data = generate_explanations(intent, top_3)
        
        final_matches = []
        for p in top_3:
            insight = next((item["ai_insight"] for item in ai_data.get("insights", []) if item["id"] == p["id"]), "Ideal match for your needs.")
            p_with_insight = p.copy()
            p_with_insight["ai_insight"] = insight
            final_matches.append(p_with_insight)
            
        return {
            "reply": ai_data.get("reply", "Here are the best matches."),
            "matches": final_matches
        }
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))