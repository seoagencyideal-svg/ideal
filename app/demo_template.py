import html
import json
import re
from urllib.parse import quote_plus


def esc(value):
    return html.escape(str(value or ''), quote=True)


def tel(value):
    return esc(value).replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('.', '')


def digits(value):
    return re.sub(r'\D+', '', str(value or ''))


def render_demo_html(data):
    """Render a premium local-business demo while preserving the existing demo API."""
    b = data.get('business') or {}
    brief = data.get('brief') or {}

    name = str(b.get('name') or 'Local Service Business').strip()
    category = str(b.get('category') or 'Local Service').strip()
    city = str(b.get('city') or '').strip()
    address = str(b.get('address') or city).strip()
    phone = str(b.get('phone') or '').strip()
    website = str(b.get('website') or '').strip()
    rating = b.get('rating')
    reviews = b.get('reviews')
    maps_url = str(b.get('maps_url') or '').strip()
    photos = [x for x in (b.get('photos') or []) if isinstance(x, str) and x.strip()][:10]

    brand = brief.get('brand') if isinstance(brief.get('brand'), dict) else {}
    colors = brief.get('brand_colors') if isinstance(brief.get('brand_colors'), dict) else brand.get('colors', {})
    primary = str(colors.get('primary') or '#1769d1')
    secondary = str(colors.get('secondary') or '#07152f')
    accent = str(colors.get('accent') or '#f5bf32')
    surface = str(colors.get('surface') or '#f5f8fc')
    logo_url = str(brief.get('logo_url') or brand.get('logo_url') or '').strip()
    tagline = str(brief.get('tagline') or '').strip()
    about = str(brief.get('about') or '').strip()
    hours = brief.get('hours') if isinstance(brief.get('hours'), list) else []
    socials = brief.get('socials') if isinstance(brief.get('socials'), dict) else {}
    service_area = str(brief.get('service_area') or city or address or 'your local area').strip()
    testimonials = brief.get('testimonials') if isinstance(brief.get('testimonials'), list) else []
    projects = brief.get('projects') if isinstance(brief.get('projects'), list) else []
    before_after = brief.get('before_after') if isinstance(brief.get('before_after'), list) else []
    faqs = brief.get('faqs') if isinstance(brief.get('faqs'), list) else []
    seo_focus = [str(x) for x in (brief.get('seo_focus') or [])][:8]
    opportunities = [str(x) for x in (brief.get('demo_opportunities') or [])][:6]
    cta = str(brief.get('hero_cta') or 'Get a Free Quote')

    excluded = {'hero','reviews','contact','faq','why choose us','service area','about','trust','gallery','team','projects','before & after'}
    sections = [str(x).strip() for x in (brief.get('recommended_sections') or []) if str(x).strip()]
    services = [x for x in sections if x.lower() not in excluded][:9] or [category]

    def safe_color(value, fallback):
        return value if re.match(r'^#[0-9a-fA-F]{3,8}$', str(value or '').strip()) else fallback

    primary = safe_color(primary, '#1769d1')
    secondary = safe_color(secondary, '#07152f')
    accent = safe_color(accent, '#f5bf32')
    surface = safe_color(surface, '#f5f8fc')

    phone_link = 'tel:' + tel(phone) if phone else '#quote'
    maps_link = maps_url or ('https://www.google.com/maps/search/?api=1&query=' + quote_plus(address or name))
    directions_link = 'https://www.google.com/maps/dir/?api=1&destination=' + quote_plus(address or name)
    whatsapp = 'https://wa.me/' + digits(phone) if digits(phone) else ''
    hero_image = photos[0] if photos else ''

    trust = []
    if rating is not None:
        trust.append('<div class="trust-stat"><strong>★ ' + esc(rating) + '</strong><span>Google rating</span></div>')
    if reviews is not None:
        trust.append('<div class="trust-stat"><strong>' + esc(reviews) + '+</strong><span>Google reviews</span></div>')
    trust.append('<div class="trust-stat"><strong>Local</strong><span>Service-focused</span></div>')
    trust_html = ''.join(trust)

    service_html = ''.join(
        '<article class="service-card reveal"><div><div class="service-icon">✓</div><p class="service-kicker">SERVICE</p><h3>' + esc(s) + '</h3><p>Professional ' + esc(s.lower()) + ' with a clear path to availability, pricing, and next steps.</p></div><a class="service-link" href="#quote">Request this service <span>↗</span></a></article>' for s in services
    )
    gallery_html = ''.join('<figure class="gallery-card reveal"><img src="' + esc(p) + '" alt="' + esc(name) + ' ' + esc(category) + ' business photo" loading="lazy" decoding="async"><figcaption>Real business photo</figcaption></figure>' for p in photos)
    project_html = ''.join('<article class="project-card reveal">' + ('<img src="' + esc(str(x.get('image'))) + '" alt="' + esc(str(x.get('title') or name)) + ' project" loading="lazy" decoding="async">' if x.get('image') else '') + '<div class="project-copy"><span class="eyebrow-small">PROJECT</span><h3>' + esc(str(x.get('title') or 'Completed Project')) + '</h3><p>' + esc(str(x.get('description') or 'A completed local-business project.')) + '</p></div></article>' for x in projects if isinstance(x, dict))
    before_after_html = ''.join('<article class="ba-card reveal"><div class="ba-grid">' + ('<figure><img src="' + esc(str(x.get('before'))) + '" alt="Before ' + esc(str(x.get('title') or name)) + '" loading="lazy" decoding="async"><figcaption>Before</figcaption></figure>' if x.get('before') else '') + ('<figure><img src="' + esc(str(x.get('after'))) + '" alt="After ' + esc(str(x.get('title') or name)) + '" loading="lazy" decoding="async"><figcaption>After</figcaption></figure>' if x.get('after') else '') + '</div><h3>' + esc(str(x.get('title') or 'Before & After')) + '</h3></article>' for x in before_after if isinstance(x, dict) and (x.get('before') or x.get('after')))
    testimonial_html = ''.join('<article class="testimonial reveal"><div class="stars">★★★★★</div><blockquote>“' + esc(str(x.get('text') or '')) + '”</blockquote><div class="testimonial-by">' + esc(str(x.get('name') or 'Local customer')) + '</div></article>' for x in testimonials if isinstance(x, dict) and x.get('text'))
    team_html = ''.join('<article class="team-card reveal">' + ('<img src="' + esc(str(x.get('image'))) + '" alt="' + esc(str(x.get('name') or name)) + '" loading="lazy" decoding="async">' if x.get('image') else '<div class="team-avatar">' + esc(str(x.get('name') or 'T')[0]) + '</div>') + '<h3>' + esc(str(x.get('name') or 'Team member')) + '</h3><p>' + esc(str(x.get('role') or 'Professional')) + '</p></article>' for x in team if isinstance(x, dict))

    default_faqs = [('How do I request service?','Use the quote form, call the business, or open the business location in Google Maps.'),('What services are available?','Review the service cards above or contact the business for its current service list.'),('Do you serve my area?','The service area shown here is based on the lead information. Confirm availability directly before booking.'),('How can I get pricing?','Send a quote request with your service needs and contact details so the business can follow up.')]
    faq_items = [(str(x['question']),str(x['answer'])) for x in faqs[:8] if isinstance(x,dict) and x.get('question') and x.get('answer')] or default_faqs
    faq_html = ''.join('<details class="faq-item reveal"><summary>' + esc(q) + '</summary><p>' + esc(a) + '</p></details>' for q,a in faq_items)
    opp_html = ''.join('<li>' + esc(x) + '</li>' for x in opportunities)
    focus_html = ''.join('<span>' + esc(x) + '</span>' for x in seo_focus)
    hours_html = ''.join('<li><span>' + esc(str(x.get('day') or 'Hours')) + '</span><strong>' + esc(str(x.get('hours') or 'Contact business')) + '</strong></li>' for x in hours if isinstance(x,dict))
    social_html = ''.join('<a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(label) + '</a>' for label,url in socials.items() if url)

    hero_style = ("background-image:linear-gradient(90deg,rgba(5,12,28,.94),rgba(5,12,28,.70),rgba(5,12,28,.26)),url('" + esc(hero_image) + "')" if hero_image else 'background-image:radial-gradient(circle at 80% 20%,' + primary + '55,transparent 32%),linear-gradient(135deg,' + secondary + ',' + primary + ')')
    canonical_url = str(brief.get('canonical_url') or website or '').strip()
    canonical_tag = '<link rel="canonical" href="' + esc(canonical_url) + '">' if canonical_url else ''
    meta_description = (tagline or f'{name} provides {category.lower()} services in {city or service_area}. Request service, directions, or a free quote today.')[:160]
    og_image = hero_image or logo_url
    favicon_tag = '<link rel="icon" href="' + esc(logo_url or hero_image) + '">' if (logo_url or hero_image) else ''

    schema_graph = [
        {'@type':'LocalBusiness','@id':(website or maps_link) + '#business','name':name,'url':website or None,'telephone':phone or None,'image':photos[:6] or None,'address':{'@type':'PostalAddress','streetAddress':address} if address else None,'areaServed':service_area or None,'hasMap':maps_link,'sameAs':[str(x) for x in socials.values() if x],'aggregateRating':({'@type':'AggregateRating','ratingValue':rating,'reviewCount':reviews} if rating is not None and reviews is not None else None)},
        {'@type':'Organization','@id':(website or maps_link) + '#organization','name':name,'url':website or None,'logo':logo_url or None}
    ]
    schema_graph += [{'@type':'Service','name':s,'provider':{'@id':(website or maps_link) + '#business'},'areaServed':service_area or None} for s in services]
    schema_graph.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home','item':website or maps_link},{'@type':'ListItem','position':2,'name':name,'item':(website or maps_link) + '#business'}]})
    schema_graph.append({'@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in faq_items]})
    schema_text = json.dumps({'@context':'https://schema.org','@graph':schema_graph},ensure_ascii=False,separators=(',',':'))

    html_doc = '''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>__NAME__ | __CATEGORY__</title><meta name="description" content="__META_DESCRIPTION__">__CANONICAL_TAG__
<meta name="robots" content="index,follow,max-image-preview:large"><meta name="theme-color" content="__SECONDARY__">
<meta property="og:type" content="website"><meta property="og:title" content="__NAME__ | __CATEGORY__"><meta property="og:description" content="__META_DESCRIPTION__"><meta property="og:url" content="__CANONICAL_URL__"><meta property="og:image" content="__OG_IMAGE__"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="__NAME__ | __CATEGORY__"><meta name="twitter:description" content="__META_DESCRIPTION__"><meta name="twitter:image" content="__OG_IMAGE__">__FAVICON__
<script type="application/ld+json">__SCHEMA__</script>
<style>
:root{--primary:__PRIMARY__;--secondary:__SECONDARY__;--accent:__ACCENT__;--surface:__SURFACE__;--ink:#101828;--muted:#61708a;--line:#e6ebf2;--white:#fff;--radius:22px;--shadow:0 20px 60px rgba(15,23,42,.10);--max:1180px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--surface);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;line-height:1.6}a{color:inherit}.topbar{background:var(--secondary);color:#fff;padding:9px 5%;font-size:12px;text-align:center}.topbar b{color:var(--accent)}nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.88);backdrop-filter:blur(16px);border-bottom:1px solid rgba(230,235,242,.8);padding:13px 5%;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:10px;font-weight:950;letter-spacing:-.03em;text-decoration:none}.brand img,.brand-mark{width:38px;height:38px;border-radius:10px;object-fit:cover}.navlinks{display:flex;gap:22px;font-size:13px;font-weight:750}.navlinks a{text-decoration:none;color:#334155}.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;border:1px solid transparent;border-radius:13px;padding:13px 19px;font-weight:900;text-decoration:none;cursor:pointer;transition:transform .22s ease,box-shadow .22s ease}.btn:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(15,23,42,.14)}.btn-primary{background:var(--primary);color:#fff}.btn-accent{background:var(--accent);color:#111}.btn-light{background:#fff;color:var(--secondary);border-color:#dce4ef}.hero{min-height:700px;background-size:cover;background-position:center;display:flex;align-items:center;color:#fff;padding:90px 5%;position:relative;overflow:hidden}.hero:after{content:"";position:absolute;right:-10%;bottom:-45%;width:520px;height:520px;border-radius:50%;background:var(--accent);opacity:.13;filter:blur(8px)}.hero-inner{max-width:var(--max);width:100%;margin:auto;position:relative;z-index:1}.breadcrumb{font-size:12px;color:#dbe5f4;margin-bottom:22px}.breadcrumb a{text-decoration:none}.eyebrow{font-size:12px;font-weight:900;letter-spacing:.13em;text-transform:uppercase;color:#ffe28a}.eyebrow-small{font-size:11px;font-weight:900;letter-spacing:.12em;color:var(--primary)}h1{font-size:clamp(46px,7vw,82px);line-height:.98;letter-spacing:-.055em;max-width:900px;margin:12px 0 22px}.hero-copy{max-width:720px;font-size:19px;color:#e9eef7}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:30px}.hero-note{font-size:12px;color:#c9d5e7;margin-top:18px}.floating-trust{max-width:var(--max);margin:-45px auto 0;position:relative;z-index:5;padding:0 5%}.trust-strip{background:#fff;border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow);display:grid;grid-template-columns:repeat(3,1fr);padding:24px}.trust-stat{padding:5px 22px;border-right:1px solid var(--line);display:flex;flex-direction:column}.trust-stat:last-child{border-right:0}.trust-stat strong{font-size:25px;line-height:1.1}.trust-stat span{font-size:12px;color:var(--muted);margin-top:4px}section{padding:90px 5%}.wrap{max-width:var(--max);margin:auto}.section-head{max-width:760px;margin-bottom:38px}.section-head h2{font-size:clamp(32px,4.5vw,52px);line-height:1.02;letter-spacing:-.045em;margin:0 0 13px}.section-head p{color:var(--muted);margin:0}.services{background:#fff}.service-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.service-card{border:1px solid var(--line);border-radius:var(--radius);padding:28px;background:linear-gradient(180deg,#fff,#fbfcfe);min-height:245px;display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 8px 30px rgba(15,23,42,.05);transition:transform .25s ease,box-shadow .25s ease}.service-card:hover{transform:translateY(-6px);box-shadow:var(--shadow)}.service-icon{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:var(--primary);color:#fff;font-weight:950}.service-kicker{font-size:10px;font-weight:900;letter-spacing:.12em;color:var(--primary);margin:17px 0 3px}.service-card h3{font-size:21px;line-height:1.2;margin:0 0 9px}.service-card p{font-size:14px;color:var(--muted);margin:0}.service-link{margin-top:22px;color:var(--primary);font-weight:900;text-decoration:none}.split,.quote-grid{display:grid;grid-template-columns:1fr 1fr;gap:42px;align-items:center}.dark-panel{background:var(--secondary);color:#fff;border-radius:28px;padding:42px;box-shadow:var(--shadow)}.dark-panel p{color:#cbd6e7}.checklist{display:grid;gap:12px;margin:26px 0 0;padding:0;list-style:none}.checklist li{display:flex;gap:10px}.checklist li:before{content:"✓";color:var(--accent);font-weight:950}.review-box{background:#fff;border:1px solid var(--line);border-radius:24px;padding:34px;box-shadow:var(--shadow)}.stars{color:#e4a900;letter-spacing:2px;font-size:23px}.review-meta{font-size:13px;color:var(--muted)}.review-actions,.map-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}.gallery-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.gallery-card{margin:0;background:#fff;border:1px solid var(--line);border-radius:17px;overflow:hidden}.gallery-card img{display:block;width:100%;height:220px;object-fit:cover}.gallery-card figcaption{font-size:12px;color:var(--muted);padding:10px 12px}.area-section{background:#eef4fb}.area-card{background:#fff;border:1px solid var(--line);border-radius:25px;padding:34px;display:flex;align-items:center;justify-content:space-between;gap:25px;box-shadow:0 10px 35px rgba(15,23,42,.06)}.area-card h2{margin:0 0 7px;font-size:30px}.area-card p{margin:0;color:var(--muted)}.quote{background:linear-gradient(135deg,var(--secondary),var(--primary));color:#fff}.quote h2{font-size:clamp(38px,5vw,58px);line-height:.98;letter-spacing:-.045em;margin:0 0 15px}.quote p{color:#d7e0ee}.form{background:#fff;color:var(--ink);border-radius:24px;padding:28px;box-shadow:var(--shadow)}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.field label{display:block;font-size:11px;font-weight:900;margin-bottom:6px}.field input,.field textarea{width:100%;border:1px solid #d8e0eb;border-radius:12px;padding:13px;font:inherit;outline:none}.field textarea{min-height:125px;resize:vertical}.full{grid-column:1/-1}.faq{display:grid;grid-template-columns:1fr 1fr;gap:14px}.faq-item{background:#fff;border:1px solid var(--line);border-radius:15px;padding:18px 20px}.faq-item summary{font-weight:900;cursor:pointer}.faq-item p{color:var(--muted);font-size:14px}.project-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.project-card,.team-card,.testimonial,.ba-card{background:#fff;border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:0 8px 30px rgba(15,23,42,.05)}.project-card img{width:100%;height:220px;object-fit:cover;display:block}.project-copy{padding:22px}.project-copy h3{margin:5px 0 7px}.project-copy p{color:var(--muted);font-size:14px}.ba-grid{display:grid;grid-template-columns:1fr 1fr}.ba-card figure{margin:0}.ba-card img{width:100%;height:210px;object-fit:cover;display:block}.ba-card figcaption{padding:8px 12px;font-size:11px;font-weight:900}.ba-card h3{padding:0 18px 18px;margin:0}.testimonial{padding:28px}.testimonial blockquote{margin:12px 0 18px;font-size:17px}.testimonial-by{font-weight:850;color:var(--muted);font-size:13px}.team-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.team-card{padding:20px;text-align:center}.team-card img,.team-avatar{width:84px;height:84px;border-radius:50%;object-fit:cover;margin:auto auto 14px}.team-avatar{display:grid;place-items:center;background:var(--primary);color:#fff;font-size:28px;font-weight:950}.team-card h3{margin:0 0 3px}.team-card p{margin:0;color:var(--muted);font-size:13px}.hours-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:25px;margin-top:22px}.hours-card ul{list-style:none;padding:0;margin:0}.hours-card li{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line);gap:20px;font-size:13px}.seo-strip{padding:22px 5%;background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.seo-inner{max-width:var(--max);margin:auto;display:flex;gap:8px;flex-wrap:wrap;align-items:center}.seo-inner span{font-size:11px;padding:7px 10px;border-radius:999px;background:#eef4fb;color:#3b4f6b}.socials{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.socials a{font-size:12px;font-weight:850;color:#dbe5f3;text-decoration:none}.footer{background:#061126;color:#b8c6db;padding:50px 5% 105px}.footer-grid{max-width:var(--max);margin:auto;display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:30px}.footer strong{color:#fff}.footer a{color:#dce6f7;text-decoration:none}.sticky-mobile{display:none}.reveal{animation:rise .7s ease both}@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}@media(max-width:900px){.navlinks{display:none}.hero{min-height:620px;padding:72px 5%}.service-grid,.project-grid{grid-template-columns:1fr 1fr}.split,.quote-grid{grid-template-columns:1fr}.gallery-grid{grid-template-columns:1fr 1fr}.team-grid{grid-template-columns:repeat(2,1fr)}.area-card{display:block}.faq{grid-template-columns:1fr}.footer-grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){section{padding:62px 5%}.hero{min-height:650px;padding:58px 5%}h1{font-size:47px}.hero-copy{font-size:17px}.hero-actions .btn{width:100%}.floating-trust{padding:0 5%;margin-top:18px}.trust-strip{grid-template-columns:1fr;transform:none;padding:10px}.trust-stat{border-right:0;border-bottom:1px solid var(--line);padding:13px 8px}.trust-stat:last-child{border-bottom:0}.service-grid,.gallery-grid,.project-grid,.team-grid,.form-grid{grid-template-columns:1fr}.full{grid-column:auto}.quote h2{font-size:39px}.area-card{padding:25px}.footer-grid{grid-template-columns:1fr}.sticky-mobile{position:fixed;z-index:100;left:0;right:0;bottom:0;background:#fff;padding:9px;display:grid;grid-template-columns:1fr 1fr;gap:8px;box-shadow:0 -10px 30px rgba(15,23,42,.15)}.sticky-mobile a{padding:12px;text-align:center;border-radius:11px;text-decoration:none;font-weight:950}.sticky-call{background:var(--secondary);color:#fff}.sticky-quote{background:var(--accent);color:#111}}
</style></head>
<body>
<div class="topbar"><b>Local service website</b> • __CITY__ • Built for trust, calls & quote requests</div>
<nav><a class="brand" href="#top">__BRAND_MARK__<span>__NAME__</span></a><div class="navlinks"><a href="#services">Services</a><a href="#why">Why Us</a><a href="#reviews">Reviews</a><a href="#gallery">Gallery</a><a href="#area">Location</a></div><a class="btn btn-accent" href="__PHONE_LINK__">__NAV_CTA__</a></nav>
<header class="hero" id="top" style="__HERO_STYLE__"><div class="hero-inner"><div class="breadcrumb"><a href="#top">Home</a> › <strong>__NAME__</strong></div><div class="eyebrow">__CATEGORY__ · __CITY__</div><h1>__HERO_HEADLINE__</h1><p class="hero-copy">__HERO_COPY__</p><div class="hero-actions"><a class="btn btn-accent" href="#quote">__CTA__</a><a class="btn btn-light" href="__PHONE_LINK__">__CALL_CTA__</a>__WHATSAPP_BUTTON__</div><div class="hero-note">Real business information • Real photos • Clear local contact paths</div></div></header>
<div class="floating-trust"><div class="trust-strip">__TRUST__</div></div>
<main>
<section id="services" class="services"><div class="wrap"><div class="section-head"><h2>Services built around what customers need</h2><p>Clear service paths, strong calls to action, and local relevance help visitors move from interest to enquiry.</p></div><div class="service-grid">__SERVICES__</div></div></section>
<section id="why"><div class="wrap split"><div><div class="section-head"><h2>Professional service, clear communication</h2><p>Every important trust and conversion signal is kept easy to find on mobile and desktop.</p></div><ul class="checklist"><li>Service-first navigation</li><li>Prominent call, WhatsApp and quote actions</li><li>Verified location and review context</li><li>Fast-loading, responsive presentation</li><li>SEO-ready semantic structure</li></ul></div><div class="dark-panel"><div class="eyebrow">Why choose __NAME__</div><h3>Local expertise with a better customer experience.</h3><p>__ABOUT_OR_FALLBACK__</p><a class="btn btn-accent" href="#quote">Start a Conversation</a></div></div></section>
<section id="reviews"><div class="wrap"><div class="section-head"><h2>Trusted locally</h2><p>Verified Google Business Profile data is displayed when supplied by the lead source.</p></div><div class="review-box">__REVIEW__<div class="review-actions"><a class="btn btn-primary" href="__MAPS_LINK__" target="_blank" rel="noopener">View Google Maps</a><a class="btn btn-light" href="__DIRECTIONS_LINK__" target="_blank" rel="noopener">Get Directions</a></div></div></div></section>
__TESTIMONIALS__
__GALLERY_SECTION__
__PROJECTS__
__BEFORE_AFTER__
__TEAM__
<section id="area" class="area-section"><div class="wrap area-card"><div><div class="eyebrow-small">LOCAL SERVICE AREA</div><h2>Serving __SERVICE_AREA__</h2><p>__ADDRESS__</p>__HOURS__</div><div class="map-actions"><a class="btn btn-primary" href="__MAPS_LINK__" target="_blank" rel="noopener">Open Google Maps</a><a class="btn btn-light" href="__DIRECTIONS_LINK__" target="_blank" rel="noopener">Directions</a></div></div></section>
__OPPORTUNITIES__
<section id="quote" class="quote"><div class="wrap quote-grid"><div><div class="eyebrow">REQUEST SERVICE</div><h2>Ready to get started?</h2><p>Send a short request and the business can follow up with availability, pricing, and next steps.</p><p><strong>__NAME__</strong><br>__ADDRESS__<br>__PHONE__</p>__SOCIALS__</div><form class="form" onsubmit="submitLead(event)"><div class="form-grid"><div class="field"><label for="fullName">Name</label><input id="fullName" required placeholder="Your name"></div><div class="field"><label for="phoneField">Phone</label><input id="phoneField" required placeholder="(555) 555-5555"></div><div class="field full"><label for="serviceField">Service needed</label><input id="serviceField" placeholder="What do you need help with?"></div><div class="field full"><label for="messageField">Message</label><textarea id="messageField" placeholder="Tell us briefly what you need."></textarea></div><div class="field full"><button class="btn btn-accent" type="submit">Request a Quote</button><p id="formStatus" style="font-size:12px;color:#61708a;margin:10px 0 0">Your request is prepared for the business to follow up.</p></div></div></form></div></section>
<section><div class="wrap"><div class="section-head"><h2>Frequently asked questions</h2><p>Concise answers help customers get the information they need without slowing down the enquiry path.</p></div><div class="faq">__FAQ__</div></div></section>
</main>
__SEO_STRIP__
<footer class="footer"><div class="footer-grid"><div><strong>__NAME__</strong><br>__CATEGORY__ · __CITY__<p>__TAGLINE_OR_DEFAULT__</p></div><div><strong>Contact</strong><br>__ADDRESS__<br><a href="__PHONE_LINK__">__PHONE__</a><br><a href="__MAPS_LINK__" target="_blank" rel="noopener">Google Maps</a></div><div><strong>Quick Links</strong><br><a href="#services">Services</a><br><a href="#reviews">Reviews</a><br><a href="#area">Location</a><br><a href="#quote">Get a Quote</a></div></div></footer>
<div class="sticky-mobile"><a class="sticky-call" href="__PHONE_LINK__">__MOBILE_CALL__</a><a class="sticky-quote" href="#quote">Get Free Quote</a></div>
<script>function submitLead(e){e.preventDefault();var name=document.getElementById('fullName').value.trim();var phone=document.getElementById('phoneField').value.trim();var service=document.getElementById('serviceField').value.trim();var msg=document.getElementById('messageField').value.trim();var text='Name: '+name+'\\nPhone: '+phone+'\\nService: '+service+'\\nMessage: '+msg;document.getElementById('formStatus').textContent='Request captured. Please use the phone/contact method above to send it to the business.';window.location.href='mailto:?subject='+encodeURIComponent('Service request for __NAME__')+'&body='+encodeURIComponent(text)}</script>
</body></html>'''

    review_html = '<div class="stars">★★★★★</div><h3>Google rating: ' + esc(rating) + '</h3><p class="review-meta">Based on ' + esc(reviews) + ' Google reviews.</p>' if rating is not None and reviews is not None else '<h3>Google review data not supplied</h3><p class="review-meta">Connect verified Business Profile data to display live rating and review count.</p>'
    gallery_section = '<section id="gallery"><div class="wrap"><div class="section-head"><h2>Real business photos</h2><p>Original business photos supplied by the lead source are displayed without inventing imagery.</p></div><div class="gallery-grid">' + gallery_html + '</div></div></section>' if gallery_html else ''
    testimonials_section = '<section><div class="wrap"><div class="section-head"><h2>What customers say</h2><p>Customer feedback is shown only when supplied as source data.</p></div><div class="project-grid">' + testimonial_html + '</div></div></section>' if testimonial_html else ''
    projects_section = '<section><div class="wrap"><div class="section-head"><h2>Recent projects</h2><p>Selected work supplied by the business or lead brief.</p></div><div class="project-grid">' + project_html + '</div></div></section>' if project_html else ''
    before_after_section = '<section><div class="wrap"><div class="section-head"><h2>Before &amp; after</h2><p>Project transformation examples supplied by the source data.</p></div><div class="project-grid">' + before_after_html + '</div></div></section>' if before_after_html else ''
    team_section = '<section><div class="wrap"><div class="section-head"><h2>Meet the team</h2><p>The people behind the service.</p></div><div class="team-grid">' + team_html + '</div></div></section>' if team_html else ''
    opportunities_section = '<section><div class="wrap"><div class="section-head"><h2>Growth opportunities</h2><p>Generated from the selected lead and demo brief.</p></div><ul class="checklist">' + opp_html + '</ul></div></section>' if opp_html else ''
    seo_section = '<div class="seo-strip"><div class="seo-inner"><strong>SEO focus:</strong>' + focus_html + '</div></div>' if focus_html else ''
    hours_section = '<div class="hours-card"><strong>Business hours</strong><ul>' + hours_html + '</ul></div>' if hours_html else ''
    socials_section = '<div class="socials">' + social_html + '</div>' if social_html else ''
    whatsapp_button = '<a class="btn btn-light" href="' + esc(whatsapp) + '" target="_blank" rel="noopener">WhatsApp</a>' if whatsapp else ''
    brand_mark = '<img src="' + esc(logo_url) + '" alt="" loading="eager" decoding="async">' if logo_url else '<span class="brand-mark" style="display:grid;place-items:center;background:var(--primary);color:#fff">' + esc(name[:1].upper()) + '</span>'
    headline = tagline or ('Premium ' + category.lower() + ' in ' + (city or service_area))
    hero_copy = about or ('A professional local ' + category.lower() + ' experience built around clear information, trust, and easy contact.')
    about_fallback = about or 'Customers can quickly review services, trust signals, location information, and contact options before taking the next step.'

    values = {
        '__NAME__':esc(name),'__CATEGORY__':esc(category),'__CITY__':esc(city or 'Local Service Area'),'__META_DESCRIPTION__':esc(meta_description),'__CANONICAL_TAG__':canonical_tag,'__CANONICAL_URL__':esc(canonical_url),'__OG_IMAGE__':esc(og_image),'__FAVICON__':favicon_tag,
        '__PRIMARY__':primary,'__SECONDARY__':secondary,'__ACCENT__':accent,'__SURFACE__':surface,'__SCHEMA__':schema_text,'__BRAND_MARK__':brand_mark,'__HERO_STYLE__':hero_style,'__HERO_HEADLINE__':esc(headline),'__HERO_COPY__':esc(hero_copy),'__ABOUT_OR_FALLBACK__':esc(about_fallback),
        '__PHONE__':esc(phone),'__PHONE_LINK__':phone_link,'__NAV_CTA__':'Call Now' if phone else 'Get a Quote','__CALL_CTA__':'Call ' + esc(phone) if phone else 'Contact Business','__MOBILE_CALL__':'Call Now' if phone else 'Contact','__CTA__':esc(cta),
        '__TRUST__':trust_html,'__SERVICES__':service_html,'__REVIEW__':review_html,'__GALLERY_SECTION__':gallery_section,'__TESTIMONIALS__':testimonials_section,'__PROJECTS__':projects_section,'__BEFORE_AFTER__':before_after_section,'__TEAM__':team_section,
        '__SERVICE_AREA__':esc(service_area),'__ADDRESS__':esc(address or 'Contact the business to confirm the service location.'),'__MAPS_LINK__':esc(maps_link),'__DIRECTIONS_LINK__':esc(directions_link),'__WHATSAPP_BUTTON__':whatsapp_button,'__HOURS__':hours_section,'__SOCIALS__':socials_section,'__FAQ__':faq_html,'__OPPORTUNITIES__':opportunities_section,'__SEO_STRIP__':seo_section,'__TAGLINE_OR_DEFAULT__':esc(tagline or 'Local service focused on trust, responsiveness, and customer experience.'),
    }
    for token,value in values.items():
        html_doc = html_doc.replace(token,value)
    return html_doc
