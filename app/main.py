import os
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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
    rating: float | None = None
    reviews: int | None = None

class LeadSearch(BaseModel):
    category: str
    city: str
    limit: int = 10

@app.get("/")
def home():
    return FileResponse("app/static/index.html")

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "pexels_configured": bool(os.getenv("PEXELS_API_KEY")),
        "google_places_configured": bool(os.getenv("GOOGLE_PLACES_API_KEY")),
    }

@app.post("/api/score")
def score(b: Business):
    # Opportunity score = how much room there appears to be for SEO/sales work.
    # It is intentionally different from a business-quality score: a strong
    # reputation should normally reduce the immediate sales opportunity.
    value = 25
    reasons = []

    if not b.website:
        value += 40
        reasons.append("No website supplied — major website opportunity")
    else:
        reasons.append("Website exists — deeper audit recommended")

    if b.rating is not None:
        if b.rating < 4.0:
            value += 15
            reasons.append(f"Google rating is {b.rating:.1f} — reputation improvement opportunity")
        elif b.rating < 4.5:
            value += 8
            reasons.append(f"Google rating is {b.rating:.1f} — room to improve reputation")
        else:
            reasons.append(f"Strong Google rating ({b.rating:.1f}) — reputation is a strength")

    if b.reviews is not None:
        if b.reviews < 25:
            value += 10
            reasons.append(f"Only {b.reviews} reviews — review growth opportunity")
        elif b.reviews < 100:
            value += 5
            reasons.append(f"{b.reviews} reviews — more review volume could help")
        else:
            reasons.append(f"Strong review volume ({b.reviews})")

    if not b.phone:
        value += 5
        reasons.append("Phone number is missing")

    if not b.category:
        value += 3
    if not b.city:
        value += 3

    value = min(value, 100)
    return {
        "ok": True,
        "score": value,
        "priority": "High" if value >= 70 else "Medium" if value >= 45 else "Low",
        "reasons": reasons,
    }

@app.post("/api/leads/search")
async def search_leads(req: LeadSearch):
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        return {"ok": False, "error": "GOOGLE_PLACES_API_KEY is not configured", "leads": []}
    limit = max(1, min(req.limit, 20))
    field_mask = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.primaryTypeDisplayName",
        "places.websiteUri",
        "places.nationalPhoneNumber",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
    ])
    payload = {
        "textQuery": f"{req.category} in {req.city}",
        "pageSize": limit,
        "includePureServiceAreaBusinesses": True,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": field_mask},
            json=payload,
        )
    if response.status_code >= 400:
        return {"ok": False, "error": response.text, "leads": []}
    data = response.json()
    leads = []
    for place in data.get("places", []):
        display = place.get("displayName", {})
        leads.append({
            "id": place.get("id", ""),
            "name": display.get("text", "Unknown business"),
            "category": place.get("primaryTypeDisplayName", {}).get("text", req.category),
            "address": place.get("formattedAddress", ""),
            "website": place.get("websiteUri", ""),
            "phone": place.get("nationalPhoneNumber", ""),
            "rating": place.get("rating"),
            "reviews": place.get("userRatingCount"),
            "maps_url": place.get("googleMapsUri", ""),
            "website_missing": not bool(place.get("websiteUri")),
        })
    return {"ok": True, "count": len(leads), "leads": leads}

@app.post("/api/gemini")
async def gemini(b: Business):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"ok": False, "error": "GEMINI_API_KEY is not configured"}
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    prompt = f"""You are an expert local SEO strategist for Ideal SEO Agency. Analyze this prospect and return concise JSON with keys: summary, website_opportunities, seo_opportunities, suggested_services, outreach_subject, outreach_message. Do not invent facts. Business: {b.model_dump_json()}"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                url,
                headers={"Content-Type": "application/json", "x-goog-api-key": key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
    except httpx.RequestError as e:
        return {"ok": False, "error": f"Gemini network error: {e}"}

    if r.status_code >= 400:
        try:
            error_data = r.json()
            message = error_data.get("error", {}).get("message") or r.text
        except Exception:
            message = r.text
        return {"ok": False, "error": f"Gemini API HTTP {r.status_code}: {message}"}

    try:
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return {"ok": False, "error": f"Unexpected Gemini response: {e}"}
    return {"ok": True, "text": text}

@app.get("/api/photos")
async def photos(q: str):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return {"ok": False, "error": "PEXELS_API_KEY is not configured", "photos": []}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": q, "per_page": 12},
        )
        r.raise_for_status()
        data = r.json()
    return {"ok": True, "photos": [{"id": p["id"], "url": p["src"]["large"]} for p in data.get("photos", [])]}
