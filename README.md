# Propulse AI 🚀
### "Real estate decisions, powered by intelligence."

![Propulse AI Dashboard](./screenshot.png)

Propulse AI is a high-end, full-stack real estate discovery platform. Unlike a standard AI wrapper, this project uses a **Logic-First Architecture** where a FastAPI backend controls the property filtering and scoring, while Gemini 1.5 Flash acts as the natural language translation and presentation layer.

---

## 🏗️ Architecture Overview
Propulse AI moves beyond "hallucination-prone" AI by separating concerns:
1. **Frontend:** Next.js (App Router) & Tailwind CSS for a cinematic, premium UI.
2. **Intent Extraction:** Gemini 1.5 Flash converts user queries into structured JSON filters.
3. **Backend Logic:** Python/FastAPI filters and ranks 100+ properties based on location, budget, and BHK.
4. **Natural Language Explanation:** Gemini explains *why* the backend chose those specific results.



---

## 🛠️ Tech Stack
- **Frontend:** React, Next.js, Tailwind CSS, Lucide Icons
- **Backend:** Python, FastAPI, Pydantic, Dotenv
- **AI Engine:** Google Gemini 1.5 Flash API
- **Version Control:** Git & GitHub (Security-focused with .gitignore)

---

## ⚙️ Setup & Installation

### 1. Backend (Python Engine)
```bash
cd backend
pip install -r requirements.txt
# Create a .env file in the /backend folder and add:
# GEMINI_API_KEY=your_actual_key_here
uvicorn main:app --reload