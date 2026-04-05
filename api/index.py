import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Path handling for deployment
try:
    from .data import PROPERTIES
except ImportError:
    from data import PROPERTIES

load_dotenv()

# 1. Configure Gemini with REST transport to prevent 404/gRPC issues on Vercel
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found")
else:
    # transport='rest' is the key for stable serverless connectivity
    genai.configure(api_key=api_key, transport='rest')

app = FastAPI(title="Propulse AI Backend")

# 2. CORS setup - allowing all for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    query: str

def extract_intent(query: str):
    # Use 'gemini-1.5-flash-latest' for the most stable endpoint
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
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
        return {"reply": "I couldn't find any properties matching those criteria.", "insights": []}
        
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    props_context = [
        {"id": p["id"], "title": p["title"], "price": p["formatted_price"], "bhk": p["bhk"], "location": p["location"]} 
        for p in top_properties
    ]
    
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

@app.get("/")
def read_root():
    return {"status": "Propulse AI API is running", "properties_loaded": len(PROPERTIES)}

@app.post("/api/agent")
@app.post("/agent")
async def run_agent(req: AgentRequest):
    try:
        intent = extract_intent(req.query)
        scored_props = []
        
        # 3. Filtering logic (Matching against your 100+ properties)
        for p in PROPERTIES:
            # Skip if strict criteria (Price/BHK) don't match
            if intent.get("max_price") and p["price"] > intent["max_price"]:
                continue
            if intent.get("bhk") and p["bhk"] != intent["bhk"]:
                continue
                
            score = 0
            # Fuzzy location scoring
            if intent.get("location"):
                u_loc = intent["location"].lower()
                p_loc = p["location"].lower()
                if u_loc in p_loc or p_loc in u_loc:
                    score += 50
            
            scored_props.append({"property": p, "score": score})
            
        scored_props.sort(key=lambda x: x["score"], reverse=True)
        top_3 = [item["property"] for item in scored_props[:3]]
        
        # 4. Generate AI explanations for why these were picked
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