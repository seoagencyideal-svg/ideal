import os
import json
import re
import time
import socket
import ipaddress
from urllib.parse import urlparse, urljoin
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
    return {"ok": True, "score": value, "priority": "High" if value >= 70 else "Medium" if value >= 45 else "Low", "reasons": reasons}

def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()

def _public_host(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            addr = ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
                return False
        return True
    except Exception:
        return False

def _tag_values(html: str, tag: str, attr: str | None = None, attr_value: str | None = None) -> list[str]:
    pattern = rf"<{tag}\b[^>]*>(.*?)</{tag}>"
    values = re.findall(pattern, html, re.I | re.S)
    if tag.lower() == "meta":
        values = []
        for m in re.findall(r"<meta\b([^>]*)>", html, re.I | re.S):
            if attr and attr_value and re.search(rf"{attr}\s*=\s*[\"']{re.escape(attr_value)}[\"']", m, re.I):
                x = re.search(r"content\s*=\s*[\"'](.*?)[\"']", m, re.I | re.S)
                if x:
                    values.append(x.group(1))
    return [_clean_text(re.sub(r"<[^>]+>", " ", x)) for x in values]

@app.post("/api/audit")
async def audit(b: Business):
    raw_url = (b.website or "").strip()
    if not raw_url:
        return {"ok": False, "error": "No website supplied. A live website URL is required for SEO audit."}
    url = raw_url if re.match(r"^https?://", raw_url, re.I) else "https://" + raw_url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return {"ok": False, "error": "Invalid website URL."}
    if not _public_host(parsed.hostname):
        return {"ok": False, "error": "Website host could not be safely reached for audit."}

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "IdealSEOAgency-Audit/1.0"}) as client:
            response = await client.get(url)
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            final_url = str(response.url)
            content_type = response.headers.get("content-type", "")
            html = response.text[:2_000_000] if "text/html" in content_type.lower() else ""
            origin = f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}"
            robots_response = await client.get(urljoin(origin + "/", "robots.txt"))
            sitemap_response = await client.get(urljoin(origin + "/", "sitemap.xml"))
    except (httpx.RequestError, httpx.TimeoutException) as e:
        return {"ok": False, "error": f"Website could not be reached: {e}"}

    title = (_tag_values(html, "title") or [""])[0]
    descriptions = _tag_values(html, "meta", "name", "description")
    h1s = _tag_values(html, "h1")
    h1_count = len(h1s)
    canonical = ""
    cm = re.search(r"<link\b[^>]*rel\s*=\s*[\"'][^\"']*canonical[^\"']*[\"'][^>]*>", html, re.I)
    if cm:
        hm = re.search(r"href\s*=\s*[\"'](.*?)[\"']", cm.group(0), re.I)
        canonical = hm.group(1).strip() if hm else ""
    viewport = bool(re.search(r"<meta\b[^>]*name\s*=\s*[\"']viewport[\"']", html, re.I))
    links = re.findall(r"<a\b[^>]*href\s*=\s*[\"'](.*?)[\"']", html, re.I | re.S)
    host = urlparse(final_url).netloc.lower()
    internal = sum(1 for href in links if urlparse(urljoin(final_url, href)).netloc.lower() in ("", host))
    external = max(0, len(links) - internal)
    word_count = len(re.findall(r"\b[\w’'-]+\b", re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I | re.S)))

    issues = []
    strengths = []
    if response.status_code >= 400:
        issues.append(f"HTTP status is {response.status_code}")
    else:
        strengths.append(f"Website responds successfully with HTTP {response.status_code}")
    if not final_url.lower().startswith("https://"):
        issues.append("HTTPS is not detected on the final URL")
    else:
        strengths.append("HTTPS is enabled")
    if not title:
        issues.append("Missing page title")
    elif len(title) < 30 or len(title) > 65:
        issues.append(f"Page title length is {len(title)} characters; review title targeting")
    else:
        strengths.append("Page title is present with a reasonable length")
    if not descriptions:
        issues.append("Missing meta description")
    elif len(descriptions[0]) < 70 or len(descriptions[0]) > 165:
        issues.append(f"Meta description length is {len(descriptions[0])} characters; review it")
    else:
        strengths.append("Meta description is present with a reasonable length")

    # Keep the H1 metric and H1 findings driven by the exact same count.
    if h1_count == 0:
        issues.append("No H1 heading detected")
    elif h1_count > 1:
        issues.append(f"Multiple H1 headings detected ({h1_count})")
    else:
        strengths.append("One H1 heading detected")

    if not viewport:
        issues.append("Mobile viewport meta tag is missing")
    else:
        strengths.append("Mobile viewport is configured")
    if not canonical:
        issues.append("Canonical link is not detected")
    else:
        strengths.append("Canonical link is present")
    if robots_response.status_code >= 400:
        issues.append("robots.txt was not found or could not be read")
    else:
        strengths.append("robots.txt is reachable")
    if sitemap_response.status_code >= 400:
        issues.append("sitemap.xml was not found at the standard location")
    else:
        strengths.append("sitemap.xml is reachable")
    if elapsed_ms > 3000:
        issues.append(f"Initial response took about {elapsed_ms} ms")
    elif elapsed_ms <= 1500:
        strengths.append(f"Initial response was fast at about {elapsed_ms} ms")

    score = max(0, min(100, 100 - len(issues) * 10))
    priority = "High" if score < 60 else "Medium" if score < 80 else "Low"
    return {
        "ok": True,
        "url": final_url,
        "status_code": response.status_code,
        "response_time_ms": elapsed_ms,
        "score": score,
        "priority": priority,
        "metrics": {"title": title, "title_length": len(title), "meta_description": descriptions[0] if descriptions else "", "h1_count": h1_count, "h1s": h1s[:5], "viewport": viewport, "canonical": canonical, "robots": robots_response.status_code < 400, "sitemap": sitemap_response.status_code < 400, "word_count": word_count, "internal_links": internal, "external_links": external, "content_type": content_type},
        "issues": issues,
        "strengths": strengths,
        "note": "This is a live technical/on-page snapshot, not a substitute for a full crawler, backlink audit, or Google Search Console data."
    }

@app.post("/api/leads/search")
async def search_leads(req: LeadSearch):
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        return {"ok": False, "error": "GOOGLE_PLACES_API_KEY is not configured", "leads": []}
    limit = max(1, min(req.limit, 20))
    field_mask = ",".join(["places.id","places.displayName","places.formattedAddress","places.primaryTypeDisplayName","places.websiteUri","places.nationalPhoneNumber","places.rating","places.userRatingCount","places.googleMapsUri"])
    payload = {"textQuery": f"{req.category} in {req.city}", "pageSize": limit, "includePureServiceAreaBusinesses": True}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://places.googleapis.com/v1/places:searchText", headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": field_mask}, json=payload)
    if response.status_code >= 400:
        return {"ok": False, "error": response.text, "leads": []}
    data = response.json()
    leads = []
    for place in data.get("places", []):
        display = place.get("displayName", {})
        leads.append({"id": place.get("id", ""), "name": display.get("text", "Unknown business"), "category": place.get("primaryTypeDisplayName", {}).get("text", req.category), "address": place.get("formattedAddress", ""), "website": place.get("websiteUri", ""), "phone": place.get("nationalPhoneNumber", ""), "rating": place.get("rating"), "reviews": place.get("userRatingCount"), "maps_url": place.get("googleMapsUri", ""), "website_missing": not bool(place.get("websiteUri"))})
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
            r = await client.post(url, headers={"Content-Type": "application/json", "x-goog-api-key": key}, json={"contents": [{"parts": [{"text": prompt}]}]})
    except httpx.RequestError as e:
        return {"ok": False, "error": f"Gemini network error: {e}"}
    if r.status_code >= 400:
        try:
            error_data = r.json(); message = error_data.get("error", {}).get("message") or r.text
        except Exception:
            message = r.text
        return {"ok": False, "error": f"Gemini API HTTP {r.status_code}: {message}"}
    try:
        data = r.json(); text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return {"ok": False, "error": f"Unexpected Gemini response: {e}"}
    return {"ok": True, "text": text}

@app.get("/api/photos")
async def photos(q: str):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return {"ok": False, "error": "PEXELS_API_KEY is not configured", "photos": []}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://api.pexels.com/v1/search", headers={"Authorization": key}, params={"query": q, "per_page": 12})
        r.raise_for_status(); data = r.json()
    return {"ok": True, "photos": [{"id": p["id"], "url": p["src"]["large"]} for p in data.get("photos", [])]}
