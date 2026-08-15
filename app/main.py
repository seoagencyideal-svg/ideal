import os
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
app = FastAPI(title="Ideal Local Business Engine")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class Business(BaseModel):
    name: str
    category: str = ""
    city: str = ""
    website: str = ""
    phone: str = ""
    notes: str = ""

@app.get("/")
def home():
    return FileResponse("app/static/index.html")

@app.get("/api/health")
def health():
    return {"ok": True, "gemini_configured": bool(os.getenv("GEMINI_API_KEY")), "pexels_configured": bool(os.getenv("PEXELS_API_KEY"))}

@app.post("/api/score")
def score(b: Business):
    score = 40
    if not b.website: score += 35
    if b.phone: score += 5
    if b.category: score += 5
    if b.city: score += 5
    if b.notes: score += 10
    score = min(score, 100)
    reasons = []
    if not b.website: reasons.append("No website supplied")
    if b.website: reasons.append("Website exists — run a deeper audit next")
    return {"score": score, "priority": "High" if score >= 75 else "Medium" if score >= 50 else "Low", "reasons": reasons}

@app.post("/api/gemini")
async def gemini(b: Business):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"ok": False, "error": "GEMINI_API_KEY is not configured"}
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = f"""You are an expert local SEO strategist for Ideal SEO Agency. Analyze this prospect and return concise JSON with keys: summary, website_opportunities, seo_opportunities, suggested_services, outreach_subject, outreach_message. Do not invent facts. Business: {b.model_dump_json()}"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    async with httpx.AsyncClient(timeout=45) as client:
        r = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        r.raise_for_status()
        data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return {"ok": True, "text": text}

@app.get("/api/photos")
async def photos(q: str):
    key = os.getenv("PEXELS_API_KEY")
    if not key: return {"ok": False, "error": "PEXELS_API_KEY is not configured", "photos": []}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://api.pexels.com/v1/search", headers={"Authorization": key}, params={"query": q, "per_page": 12})
        r.raise_for_status()
        data = r.json()
    return {"ok": True, "photos": [{"id": p["id"], "url": p["src"]["large"]} for p in data.get("photos", [])]}
