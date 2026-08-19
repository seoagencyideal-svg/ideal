import os, re, time, socket, ipaddress, secrets, base64
from urllib.parse import urlparse, urljoin
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
app = FastAPI(title='Ideal Local Business Engine')
app.mount('/static', StaticFiles(directory='app/static'), name='static')
DEMO_STORE = {}

class Business(BaseModel):
    name: str
    category: str = ''
    city: str = ''
    website: str = ''
    phone: str = ''
    notes: str = ''
    rating: float | None = None
    reviews: int | None = None
    place_id: str = ''
    maps_url: str = ''
    photos: list[str] = Field(default_factory=list)
    audit: dict | None = None

class LeadSearch(BaseModel):
    category: str
    city: str
    limit: int = 10
    no_website_only: bool = True

class DemoRequest(BaseModel):
    business: Business
    brief: dict = Field(default_factory=dict)

class DeployRequest(DemoRequest):
    slug: str = ''

@app.get('/')
def home():
    return FileResponse('app/static/index.html')

@app.get('/api/health')
def health():
    return {
        'ok': True,
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY')),
        'google_places_configured': bool(os.getenv('GOOGLE_PLACES_API_KEY')),
        'github_deployment_configured': bool(os.getenv('GITHUB_TOKEN')),
        'github_repo_configured': bool(os.getenv('GITHUB_REPO_OWNER') and os.getenv('GITHUB_REPO_NAME')),
        'pages_base_url': os.getenv('GITHUB_PAGES_BASE_URL', '')
    }

@app.post('/api/score')
def score(b: Business):
    value = 25; reasons = []
    if not b.website:
        value += 40; reasons.append('No website supplied — major website opportunity')
    else: reasons.append('Website exists — deeper audit recommended')
    if b.rating is not None:
        if b.rating < 4: value += 15; reasons.append(f'Google rating is {b.rating:.1f} — reputation improvement opportunity')
        elif b.rating < 4.5: value += 8; reasons.append(f'Google rating is {b.rating:.1f} — room to improve reputation')
        else: reasons.append(f'Strong Google rating ({b.rating:.1f}) — reputation is a strength')
    if b.reviews is not None:
        if b.reviews < 25: value += 10; reasons.append(f'Only {b.reviews} reviews — review growth opportunity')
        elif b.reviews < 100: value += 5; reasons.append(f'{b.reviews} reviews — more review volume could help')
        else: reasons.append(f'Strong review volume ({b.reviews})')
    if not b.phone: value += 5; reasons.append('Phone number is missing')
    value = min(value, 100)
    return {'ok': True, 'score': value, 'priority': 'High' if value >= 70 else 'Medium' if value >= 45 else 'Low', 'reasons': reasons}

def clean(v):
    return re.sub(r'\s+', ' ', v or '').strip()

def public_host(hostname):
    try:
        for info in socket.getaddrinfo(hostname, None):
            addr = ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
                return False
        return True
    except Exception:
        return False

def tags(html, tag, attr=None, val=None):
    if tag == 'meta':
        out = []
        for m in re.findall(r'<meta\b([^>]*)>', html, re.I | re.S):
            if attr and val and re.search(rf'{attr}\s*=\s*["\']{re.escape(val)}["\']', m, re.I):
                z = re.search(r'content\s*=\s*["\'](.*?)["\']', m, re.I | re.S)
                if z: out.append(z.group(1))
        return [clean(x) for x in out]
    return [clean(re.sub(r'<[^>]+>', ' ', x)) for x in re.findall(rf'<{tag}\b[^>]*>(.*?)</{tag}>', html, re.I | re.S)]

@app.post('/api/audit')
async def audit(b: Business):
    raw = b.website.strip()
    if not raw: return {'ok': False, 'error': 'No website supplied. A live website URL is required for SEO audit.'}
    url = raw if re.match(r'^https?://', raw, re.I) else 'https://' + raw
    parsed = urlparse(url)
    if not parsed.hostname or parsed.scheme not in ('http', 'https') or not public_host(parsed.hostname):
        return {'ok': False, 'error': 'Website host could not be safely reached for audit.'}
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={'User-Agent': 'IdealSEOAgency-Audit/1.0'}) as c:
            response = await c.get(url)
            elapsed = round((time.perf_counter() - started) * 1000)
            final = str(response.url)
            html = response.text[:2_000_000] if 'text/html' in response.headers.get('content-type', '').lower() else ''
            origin = f'{urlparse(final).scheme}://{urlparse(final).netloc}'
            robots = await c.get(urljoin(origin + '/', 'robots.txt'))
            sitemap = await c.get(urljoin(origin + '/', 'sitemap.xml'))
    except Exception as e:
        return {'ok': False, 'error': f'Website could not be reached: {e}'}
    title = (tags(html, 'title') or [''])[0]
    desc = (tags(html, 'meta', 'name', 'description') or [''])[0]
    h1s = tags(html, 'h1')
    canonical = ''
    cm = re.search(r'<link\b[^>]*rel\s*=\s*["\'][^"\']*canonical[^"\']*["\'][^>]*>', html, re.I)
    if cm:
        hm = re.search(r'href\s*=\s*["\'](.*?)["\']', cm.group(0), re.I)
        canonical = hm.group(1) if hm else ''
    viewport = bool(re.search(r'<meta\b[^>]*name\s*=\s*["\']viewport["\']', html, re.I))
    links = re.findall(r'<a\b[^>]*href\s*=\s*["\'](.*?)["\']', html, re.I | re.S)
    host = urlparse(final).netloc.lower()
    internal = sum(1 for x in links if urlparse(urljoin(final, x)).netloc.lower() in ('', host))
    words = len(re.findall(r'\b[\w’\'-]+\b', re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.I | re.S)))
    issues = []; strengths = []
    if response.status_code >= 400: issues.append(f'HTTP status is {response.status_code}')
    else: strengths.append(f'Website responds successfully with HTTP {response.status_code}')
    if not final.lower().startswith('https://'): issues.append('HTTPS is not detected on the final URL')
    else: strengths.append('HTTPS is enabled')
    if not title: issues.append('Missing page title')
    elif len(title) < 30 or len(title) > 65: issues.append(f'Page title length is {len(title)} characters; review title targeting')
    else: strengths.append('Page title is present with a reasonable length')
    if not desc: issues.append('Missing meta description')
    elif len(desc) < 70 or len(desc) > 165: issues.append(f'Meta description length is {len(desc)} characters; review it')
    else: strengths.append('Meta description is present with a reasonable length')
    if len(h1s) == 0: issues.append('No H1 heading detected')
    elif len(h1s) > 1: issues.append(f'Multiple H1 headings detected ({len(h1s)})')
    else: strengths.append('One H1 heading detected')
    if not viewport: issues.append('Mobile viewport meta tag is missing')
    else: strengths.append('Mobile viewport is configured')
    if not canonical: issues.append('Canonical link is not detected')
    else: strengths.append('Canonical link is present')
    if robots.status_code >= 400: issues.append('robots.txt was not found or could not be read')
    else: strengths.append('robots.txt is reachable')
    if sitemap.status_code >= 400: issues.append('sitemap.xml was not found at the standard location')
    else: strengths.append('sitemap.xml is reachable')
    if elapsed > 3000: issues.append(f'Initial response took about {elapsed} ms')
    elif elapsed <= 1500: strengths.append(f'Initial response was fast at about {elapsed} ms')
    score_value = max(0, min(100, 100 - len(issues) * 10))
    priority = 'High' if score_value < 60 else 'Medium' if score_value < 80 else 'Low'
    return {'ok': True, 'url': final, 'status_code': response.status_code, 'response_time_ms': elapsed, 'score': score_value, 'priority': priority,
            'metrics': {'title': title, 'title_length': len(title), 'meta_description': desc, 'h1_count': len(h1s), 'h1s': h1s[:5], 'viewport': viewport, 'canonical': canonical, 'robots': robots.status_code < 400, 'sitemap': sitemap.status_code < 400, 'word_count': words, 'internal_links': internal, 'external_links': max(0, len(links) - internal)},
            'issues': issues, 'strengths': strengths,
            'note': 'This is a live technical/on-page snapshot, not a substitute for a full crawler, backlink audit, or Google Search Console data.'}

@app.post('/api/leads/search')
async def search_leads(req: LeadSearch):
    key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not key: return {'ok': False, 'error': 'GOOGLE_PLACES_API_KEY is not configured', 'leads': []}
    limit = max(1, min(req.limit, 20))
    mask = ','.join(['places.id','places.displayName','places.formattedAddress','places.primaryTypeDisplayName','places.websiteUri','places.nationalPhoneNumber','places.rating','places.userRatingCount','places.googleMapsUri','places.photos'])
    body = {'textQuery': f'{req.category} in {req.city}', 'pageSize': 20, 'includePureServiceAreaBusinesses': True}
    async with httpx.AsyncClient(timeout=30) as c:
        response = await c.post('https://places.googleapis.com/v1/places:searchText', headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': key, 'X-Goog-FieldMask': mask}, json=body)
    if response.status_code >= 400: return {'ok': False, 'error': response.text, 'leads': []}
    leads = []
    for place in response.json().get('places', []):
        display = place.get('displayName', {})
        website = place.get('websiteUri', '')
        photos = []
        for photo in place.get('photos', [])[:6]:
            if photo.get('name'):
                photos.append(f"https://places.googleapis.com/v1/{photo['name']}/media?maxWidthPx=1400&key={key}")
        lead = {'id': place.get('id', ''), 'name': display.get('text', 'Unknown business'), 'category': place.get('primaryTypeDisplayName', {}).get('text', req.category), 'address': place.get('formattedAddress', ''), 'website': website, 'phone': place.get('nationalPhoneNumber', ''), 'rating': place.get('rating'), 'reviews': place.get('userRatingCount'), 'maps_url': place.get('googleMapsUri', ''), 'photos': photos, 'website_missing': not bool(website)}
        if req.no_website_only and not lead['website_missing']: continue
        leads.append(lead)
        if len(leads) >= limit: break
    return {'ok': True, 'count': len(leads), 'leads': leads, 'no_website_only': req.no_website_only}

@app.post('/api/gemini')
async def gemini(b: Business):
    key = os.getenv('GEMINI_API_KEY')
    if not key: return {'ok': False, 'error': 'GEMINI_API_KEY is not configured'}
    model = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')
    prompt = f'''You are an expert local SEO strategist for Ideal SEO Agency. Analyze this prospect and return concise JSON with keys: summary, website_opportunities, seo_opportunities, suggested_services, outreach_subject, outreach_message. Do not invent facts. Business: {b.model_dump_json()}'''
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    try:
        async with httpx.AsyncClient(timeout=45) as c:
            r = await c.post(url, headers={'Content-Type': 'application/json', 'x-goog-api-key': key}, json={'contents': [{'parts': [{'text': prompt}]}]})
    except Exception as e: return {'ok': False, 'error': f'Gemini network error: {e}'}
    if r.status_code >= 400:
        try: message = r.json().get('error', {}).get('message') or r.text
        except Exception: message = r.text
        return {'ok': False, 'error': f'Gemini API HTTP {r.status_code}: {message}'}
    try: text = r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e: return {'ok': False, 'error': f'Unexpected Gemini response: {e}'}
    return {'ok': True, 'text': text}

def demo_html(data):
    from app.demo_template import render_demo_html
    return render_demo_html(data)

def slugify(value):
    s = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return s[:60] or 'local-business'

def pages_base_url():
    configured = os.getenv('GITHUB_PAGES_BASE_URL', '').rstrip('/')
    if configured: return configured
    owner = os.getenv('GITHUB_REPO_OWNER', 'seoagencyideal-svg')
    repo = os.getenv('GITHUB_REPO_NAME', 'ideal')
    return f'https://{owner}.github.io/{repo}'

async def github_put_file(path, content, message):
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_REPO_OWNER', 'seoagencyideal-svg')
    repo = os.getenv('GITHUB_REPO_NAME', 'ideal')
    if not token:
        raise RuntimeError('GITHUB_TOKEN is not configured on the server. Add it to the API hosting environment, then redeploy the API.')
    api = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
    async with httpx.AsyncClient(timeout=30) as c:
        existing = await c.get(api, headers=headers)
        payload = {'message': message, 'content': encoded, 'branch': os.getenv('GITHUB_BRANCH', 'main')}
        if existing.status_code == 200:
            payload['sha'] = existing.json().get('sha')
        elif existing.status_code != 404:
            raise RuntimeError(f'GitHub lookup failed: HTTP {existing.status_code} {existing.text[:300]}')
        r = await c.put(api, headers=headers, json=payload)
        if r.status_code >= 300:
            raise RuntimeError(f'GitHub deployment write failed: HTTP {r.status_code} {r.text[:500]}')
        return r.json().get('commit', {}).get('sha', '')

@app.post('/api/demos')
def create_demo(req: DemoRequest):
    if not req.business.name: return {'ok': False, 'error': 'Business name is required'}
    demo_id = secrets.token_urlsafe(8)
    DEMO_STORE[demo_id] = {'business': req.business.model_dump(), 'brief': req.brief, 'created_at': time.time()}
    return {'ok': True, 'id': demo_id, 'url': f'/demo/{demo_id}'}

@app.post('/api/deploy')
async def deploy(req: DeployRequest):
    if not req.business.name: return {'ok': False, 'error': 'Business name is required'}
    slug = slugify(req.slug or req.business.name)
    try:
        html = demo_html({'business': req.business.model_dump(), 'brief': req.brief})
    except Exception as e:
        return {'ok': False, 'error': f'Demo template generation failed: {type(e).__name__}: {e}'}
    path = f'public/sites/{slug}/index.html'
    try:
        commit = await github_put_file(path, html, f'Deploy website: {req.business.name}')
    except Exception as e:
        return {'ok': False, 'error': f'GitHub deployment failed: {type(e).__name__}: {e}'}
    return {'ok': True, 'slug': slug, 'path': path, 'commit': commit, 'url': f'{pages_base_url()}/sites/{slug}/', 'status': 'committed; GitHub Pages deployment will run from the main branch'}

@app.get('/demo/{demo_id}', response_class=HTMLResponse)
def view_demo(demo_id: str):
    data = DEMO_STORE.get(demo_id)
    if not data: raise HTTPException(status_code=404, detail='Demo not found or expired after server restart')
    return HTMLResponse(demo_html(data))
