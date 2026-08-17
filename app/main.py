import os, re, time, socket, ipaddress, secrets
from urllib.parse import urlparse, urljoin
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
app=FastAPI(title='Ideal Local Business Engine')
app.mount('/static',StaticFiles(directory='app/static'),name='static')
DEMO_STORE={}

class Business(BaseModel):
    name:str; category:str=''; city:str=''; website:str=''; phone:str=''; notes:str=''
    rating:float|None=None; reviews:int|None=None; place_id:str=''; maps_url:str=''
    photos:list[str]=Field(default_factory=list); audit:dict|None=None
class LeadSearch(BaseModel):
    category:str; city:str; limit:int=10; no_website_only:bool=True
class DemoRequest(BaseModel):
    business:Business; brief:dict={}

@app.get('/')
def home(): return FileResponse('app/static/index.html')
@app.get('/api/health')
def health():
    return {'ok':True,'gemini_configured':bool(os.getenv('GEMINI_API_KEY')),'pexels_configured':bool(os.getenv('PEXELS_API_KEY')),'google_places_configured':bool(os.getenv('GOOGLE_PLACES_API_KEY'))}

@app.post('/api/score')
def score(b:Business):
    value=25; reasons=[]
    if not b.website: value+=40; reasons.append('No website supplied — major website opportunity')
    else: reasons.append('Website exists — deeper audit recommended')
    if b.rating is not None:
        if b.rating<4: value+=15; reasons.append(f'Google rating is {b.rating:.1f} — reputation improvement opportunity')
        elif b.rating<4.5: value+=8; reasons.append(f'Google rating is {b.rating:.1f} — room to improve reputation')
        else: reasons.append(f'Strong Google rating ({b.rating:.1f}) — reputation is a strength')
    if b.reviews is not None:
        if b.reviews<25: value+=10; reasons.append(f'Only {b.reviews} reviews — review growth opportunity')
        elif b.reviews<100: value+=5; reasons.append(f'{b.reviews} reviews — more review volume could help')
        else: reasons.append(f'Strong review volume ({b.reviews})')
    if not b.phone: value+=5; reasons.append('Phone number is missing')
    value=min(value,100)
    return {'ok':True,'score':value,'priority':'High' if value>=70 else 'Medium' if value>=45 else 'Low','reasons':reasons}

def clean(v): return re.sub(r'\s+',' ',v or '').strip()
def public_host(h):
    try:
        for x in socket.getaddrinfo(h,None):
            a=ipaddress.ip_address(x[4][0])
            if a.is_private or a.is_loopback or a.is_link_local or a.is_reserved or a.is_multicast:return False
        return True
    except:return False

def tags(html,tag,attr=None,val=None):
    if tag=='meta':
        out=[]
        for m in re.findall(r'<meta\b([^>]*)>',html,re.I|re.S):
            if attr and val and re.search(rf'{attr}\s*=\s*["\']{re.escape(val)}["\']',m,re.I):
                z=re.search(r'content\s*=\s*["\'](.*?)["\']',m,re.I|re.S)
                if z:out.append(z.group(1))
        return [clean(x) for x in out]
    return [clean(re.sub(r'<[^>]+>',' ',x)) for x in re.findall(rf'<{tag}\b[^>]*>(.*?)</{tag}>',html,re.I|re.S)]

@app.post('/api/audit')
async def audit(b:Business):
    raw=b.website.strip()
    if not raw:return {'ok':False,'error':'No website supplied. A live website URL is required for SEO audit.'}
    url=raw if re.match(r'^https?://',raw,re.I) else 'https://'+raw
    p=urlparse(url)
    if not p.hostname or p.scheme not in ('http','https') or not public_host(p.hostname):return {'ok':False,'error':'Website host could not be safely reached for audit.'}
    start=time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=20,follow_redirects=True,headers={'User-Agent':'IdealSEOAgency-Audit/1.0'}) as c:
            r=await c.get(url); ms=round((time.perf_counter()-start)*1000); final=str(r.url); html=r.text[:2000000] if 'text/html' in r.headers.get('content-type','').lower() else ''
            origin=f'{urlparse(final).scheme}://{urlparse(final).netloc}'
            robots=await c.get(urljoin(origin+'/','robots.txt')); sitemap=await c.get(urljoin(origin+'/','sitemap.xml'))
    except Exception as e:return {'ok':False,'error':f'Website could not be reached: {e}'}
    title=(tags(html,'title') or [''])[0]; desc=(tags(html,'meta','name','description') or [''])[0]; h1=tags(html,'h1'); canon=''
    m=re.search(r'<link\b[^>]*rel\s*=\s*["\'][^"\']*canonical[^"\']*["\'][^>]*>',html,re.I)
    if m:
        z=re.search(r'href\s*=\s*["\'](.*?)["\']',m.group(0),re.I); canon=z.group(1) if z else ''
    viewport=bool(re.search(r'<meta\b[^>]*name\s*=\s*["\']viewport["\']',html,re.I)); links=re.findall(r'<a\b[^>]*href\s*=\s*["\'](.*?)["\']',html,re.I|re.S); host=urlparse(final).netloc.lower(); internal=sum(1 for x in links if urlparse(urljoin(final,x)).netloc.lower() in ('',host)); words=len(re.findall(r'\b[\w’\'-]+\b',re.sub(r'<script.*?</script>|<style.*?</style>',' ',html,flags=re.I|re.S)))
    issues=[]; strengths=[]
    if r.status_code>=400:issues.append(f'HTTP status is {r.status_code}')
    else:strengths.append(f'Website responds successfully with HTTP {r.status_code}')
    if not final.lower().startswith('https://'):issues.append('HTTPS is not detected on the final URL')
    else:strengths.append('HTTPS is enabled')
    if not title:issues.append('Missing page title')
    elif len(title)<30 or len(title)>65:issues.append(f'Page title length is {len(title)} characters; review title targeting')
    else:strengths.append('Page title is present with a reasonable length')
    if not desc:issues.append('Missing meta description')
    elif len(desc)<70 or len(desc)>165:issues.append(f'Meta description length is {len(desc)} characters; review it')
    else:strengths.append('Meta description is present with a reasonable length')
    if len(h1)==0:issues.append('No H1 heading detected')
    elif len(h1)>1:issues.append(f'Multiple H1 headings detected ({len(h1)})')
    else:strengths.append('One H1 heading detected')
    if not viewport:issues.append('Mobile viewport meta tag is missing')
    else:strengths.append('Mobile viewport is configured')
    if not canon:issues.append('Canonical link is not detected')
    else:strengths.append('Canonical link is present')
    if robots.status_code>=400:issues.append('robots.txt was not found or could not be read')
    else:strengths.append('robots.txt is reachable')
    if sitemap.status_code>=400:issues.append('sitemap.xml was not found at the standard location')
    else:strengths.append('sitemap.xml is reachable')
    if ms>3000:issues.append(f'Initial response took about {ms} ms')
    elif ms<=1500:strengths.append(f'Initial response was fast at about {ms} ms')
    s=max(0,min(100,100-len(issues)*10)); pri='High' if s<60 else 'Medium' if s<80 else 'Low'
    return {'ok':True,'url':final,'status_code':r.status_code,'response_time_ms':ms,'score':s,'priority':pri,'metrics':{'title':title,'title_length':len(title),'meta_description':desc,'h1_count':len(h1),'h1s':h1[:5],'viewport':viewport,'canonical':canon,'robots':robots.status_code<400,'sitemap':sitemap.status_code<400,'word_count':words,'internal_links':internal,'external_links':max(0,len(links)-internal)},'issues':issues,'strengths':strengths,'note':'This is a live technical/on-page snapshot, not a substitute for a full crawler, backlink audit, or Google Search Console data.'}

@app.post('/api/leads/search')
async def search_leads(req:LeadSearch):
    key=os.getenv('GOOGLE_PLACES_API_KEY')
    if not key:return {'ok':False,'error':'GOOGLE_PLACES_API_KEY is not configured','leads':[]}
    limit=max(1,min(req.limit,20)); mask=','.join(['places.id','places.displayName','places.formattedAddress','places.primaryTypeDisplayName','places.websiteUri','places.nationalPhoneNumber','places.rating','places.userRatingCount','places.googleMapsUri','places.photos'])
    body={'textQuery':f'{req.category} in {req.city}','pageSize':20,'includePureServiceAreaBusinesses':True}
    async with httpx.AsyncClient(timeout=30) as c:r=await c.post('https://places.googleapis.com/v1/places:searchText',headers={'Content-Type':'application/json','X-Goog-Api-Key':key,'X-Goog-FieldMask':mask},json=body)
    if r.status_code>=400:return {'ok':False,'error':r.text,'leads':[]}
    leads=[]
    for place in r.json().get('places',[]):
        d=place.get('displayName',{}); website=place.get('websiteUri',''); photos=[]
        for ph in place.get('photos',[])[:6]:
            if ph.get('name'):photos.append(f"https://places.googleapis.com/v1/{ph['name']}/media?maxWidthPx=1400&key={key}")
        lead={'id':place.get('id',''),'name':d.get('text','Unknown business'),'category':place.get('primaryTypeDisplayName',{}).get('text',req.category),'address':place.get('formattedAddress',''),'website':website,'phone':place.get('nationalPhoneNumber',''),'rating':place.get('rating'),'reviews':place.get('userRatingCount'),'maps_url':place.get('googleMapsUri',''),'photos':photos,'website_missing':not bool(website)}
        if req.no_website_only and not lead['website_missing']:continue
        leads.append(lead)
        if len(leads)>=limit:break
    return {'ok':True,'count':len(leads),'leads':leads,'no_website_only':req.no_website_only}

@app.post('/api/gemini')
async def gemini(b:Business):
    key=os.getenv('GEMINI_API_KEY')
    if not key:return {'ok':False,'error':'GEMINI_API_KEY is not configured'}
    model=os.getenv('GEMINI_MODEL','gemini-3.6-flash'); prompt=f'''You are an expert local SEO strategist for Ideal SEO Agency. Analyze this prospect and return concise JSON with keys: summary, website_opportunities, seo_opportunities, suggested_services, outreach_subject, outreach_message. Do not invent facts. Business: {b.model_dump_json()}'''; url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    try:
        async with httpx.AsyncClient(timeout=45) as c:r=await c.post(url,headers={'Content-Type':'application/json','x-goog-api-key':key},json={'contents':[{'parts':[{'text':prompt}]}]})
    except Exception as e:return {'ok':False,'error':f'Gemini network error: {e}'}
    if r.status_code>=400:
        try:msg=r.json().get('error',{}).get('message') or r.text
        except:msg=r.text
        return {'ok':False,'error':f'Gemini API HTTP {r.status_code}: {msg}'}
    try:text=r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:return {'ok':False,'error':f'Unexpected Gemini response: {e}'}
    return {'ok':True,'text':text}

@app.post('/api/demos')
def create_demo(req:DemoRequest):
    if not req.business.name:return {'ok':False,'error':'Business name is required'}
    did=secrets.token_urlsafe(8); DEMO_STORE[did]={'business':req.business.model_dump(),'brief':req.brief,'created_at':time.time()}
    return {'ok':True,'id':did,'url':f'/demo/{did}'}

def demo_html(data):
    b=data['business']; brief=data.get('brief') or {}; photos=[x for x in b.get('photos',[]) if isinstance(x,str)][:5]; hero=photos[0] if photos else ''; phone=b.get('phone',''); rating=b.get('rating','—'); reviews=b.get('reviews',0); sections=brief.get('recommended_sections',[]); services=[x for x in sections if x not in ['Hero','Reviews','Contact','FAQ','Why Choose Us','Service Area']] or ['Emergency Service','Repairs','Maintenance','Free Estimates']; cards=''.join(f'<article><h3>{clean(str(x))}</h3><p>Professional local service with clear communication and fast response.</p></article>' for x in services); gallery=''.join(f'<img src="{x}" alt="{clean(b["name"])} real business photo" loading="lazy">' for x in photos[1:])
    return f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>{clean(b['name'])}</title><style>*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,Arial;color:#10172a;background:#f6f8fc}}nav{{padding:18px 7%;background:#0b1530;color:#fff;display:flex;justify-content:space-between;align-items:center}}.cta{{background:#f6c33b;color:#111;padding:12px 18px;border-radius:9px;text-decoration:none;font-weight:800}}.hero{{min-height:560px;padding:80px 7%;display:flex;align-items:center;color:#fff;background:linear-gradient(90deg,rgba(5,12,30,.9),rgba(5,12,30,.35)),url('{hero}') center/cover}}.hero h1{{font-size:clamp(40px,6vw,72px);max-width:850px;margin:10px 0 20px}}.hero p{{font-size:20px;max-width:700px;line-height:1.6}}section{{padding:65px 7%;max-width:1250px;margin:auto}}.trust{{background:#fff;border:1px solid #e5e9f2;border-radius:16px;padding:25px;display:flex;justify-content:space-between;align-items:center;gap:20px}}.cards,.gallery{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}article{{background:#fff;border:1px solid #e5e9f2;border-radius:16px;padding:25px}}.gallery img{{width:100%;height:230px;object-fit:cover;border-radius:14px}}footer{{padding:35px 7%;background:#0b1530;color:#c4cce0}}@media(max-width:800px){{.cards,.gallery{{grid-template-columns:1fr}}.trust{{display:block}}}}</style></head><body><nav><strong>{clean(b['name'])}</strong><a class="cta" href="tel:{clean(phone)}">Call Now</a></nav><div class="hero"><div><div>{clean(b.get('category','Local Service'))} · {clean(b.get('city',''))}</div><h1>Trusted local service when you need it.</h1><p>Professional service from {clean(b['name'])}. Request service today.</p><a class="cta" href="tel:{clean(phone)}">Request Service</a></div></div><section><div class="trust"><div><h2>Trusted by local customers</h2><p>Google rating: <strong>★ {rating}</strong> · {reviews} reviews</p></div><a class="cta" href="tel:{clean(phone)}">Get a Free Quote</a></div></section><section><h2>Services</h2><div class="cards">{cards}</div></section>{('<section><h2>Real Business Photos</h2><div class="gallery">'+gallery+'</div></section>') if gallery else ''}<section><h2>Service Area</h2><p>{clean(b.get('address',b.get('city','')))}</p></section><footer>{clean(b['name'])} · {clean(b.get('city',''))}</footer></body></html>'''

@app.get('/demo/{did}',response_class=HTMLResponse)
def view_demo(did):
    if did not in DEMO_STORE:raise HTTPException(404,'Demo not found or expired after server restart')
    return HTMLResponse(demo_html(DEMO_STORE[did]))

@app.get('/api/photos')
async def photos(q:str):
    key=os.getenv('PEXELS_API_KEY')
    if not key:return {'ok':False,'error':'PEXELS_API_KEY is not configured','photos':[]}
    async with httpx.AsyncClient(timeout=30) as c:r=await c.get('https://api.pexels.com/v1/search',headers={'Authorization':key},params={'query':q,'per_page':12})
    r.raise_for_status();return {'ok':True,'photos':[{'id':p['id'],'url':p['src']['large']} for p in r.json().get('photos',[])]}
