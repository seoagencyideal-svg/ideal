import json
import html
from urllib.parse import quote_plus


def esc(value):
    return html.escape(str(value or ''), quote=True)


def tel(value):
    return esc(value).replace(' ', '').replace('(', '').replace(')', '').replace('-', '')


def render_demo_html(data):
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
    photos = [x for x in (b.get('photos') or []) if isinstance(x, str) and x.strip()][:8]

    sections = brief.get('recommended_sections') or []
    sections = [str(x) for x in sections]
    requested_services = [x for x in sections if x.lower() not in {
        'hero', 'reviews', 'contact', 'faq', 'why choose us', 'service area', 'about',
        'trust', 'gallery'
    }]

    # Use the lead's existing brief when available. Do not invent specific claims.
    if requested_services:
        services = requested_services[:9]
    else:
        services = [category]

    opportunities = brief.get('demo_opportunities') or []
    seo_focus = brief.get('seo_focus') or []
    service_area_text = city or address or 'Your local service area'
    cta_label = str(brief.get('hero_cta') or 'Request Service')
    hero_image = photos[0] if photos else ''

    trust_items = []
    if rating is not None:
        trust_items.append(f'<strong>★ {esc(rating)}</strong><span>Google rating</span>')
    if reviews is not None:
        trust_items.append(f'<strong>{esc(reviews)}+</strong><span>Google reviews</span>')
    if phone:
        trust_items.append('<strong>Direct</strong><span>Phone support</span>')
    if not trust_items:
        trust_items = [
            '<strong>Local</strong><span>Service-focused</span>',
            '<strong>Fast</strong><span>Response-focused</span>',
            '<strong>Clear</strong><span>Communication</span>',
        ]

    service_cards = ''.join(
        f'''<article class="service-card">
            <div class="icon">✓</div>
            <h3>{esc(service)}</h3>
            <p>Request current availability, pricing, and service details from {esc(name)}.</p>
            <a href="#quote">Request service <span>→</span></a>
        </article>'''
        for service in services
    )

    gallery = ''.join(
        f'<figure><img src="{esc(photo)}" alt="{esc(name)} business photo" loading="lazy"><figcaption>Business photo</figcaption></figure>'
        for photo in photos
    )

    opp_items = ''.join(f'<li>{esc(x)}</li>' for x in opportunities[:6])
    focus_items = ''.join(f'<span>{esc(x)}</span>' for x in seo_focus[:6])

    phone_link = f'tel:{tel(phone)}' if phone else '#quote'
    maps_link = maps_url or ('https://www.google.com/maps/search/?api=1&query=' + quote_plus(address or name))
    image_style = (
        f"background-image:linear-gradient(90deg,rgba(5,14,35,.96) 0%,rgba(5,14,35,.78) 48%,rgba(5,14,35,.34) 100%),url('{esc(hero_image)}')"
        if hero_image else
        "background-image:linear-gradient(135deg,#07152f 0%,#123b72 55%,#0a1b38 100%)"
    )

    schema = {
        '@context': 'https://schema.org',
        '@type': 'LocalBusiness',
        'name': name,
        'url': website or None,
        'telephone': phone or None,
        'address': {'@type': 'PostalAddress', 'streetAddress': address} if address else None,
        'aggregateRating': ({'@type': 'AggregateRating', 'ratingValue': rating, 'reviewCount': reviews}
                            if rating is not None and reviews is not None else None)
    }
    schema = {k: v for k, v in schema.items() if v is not None}

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(name)} — {esc(category)} serving {esc(city or 'local customers')}. Request service or a quote today.">
<meta name="theme-color" content="#08162f">
<title>{esc(name)} | {esc(category)}{(' in ' + esc(city)) if city else ''}</title>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(',', ':'))}</script>
<style>
:root{{--navy:#07152f;--navy2:#0d2347;--blue:#1769d1;--gold:#f5bf32;--gold2:#ffd86a;--ink:#101a2d;--muted:#60708b;--line:#e4eaf3;--bg:#f5f8fc;--white:#fff;--radius:18px;--shadow:0 18px 50px rgba(7,21,47,.10)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6}}a{{color:inherit}}.topbar{{background:var(--navy);color:#fff;font-size:13px;padding:9px 6%;text-align:center}}.topbar b{{color:var(--gold2)}}nav{{position:sticky;top:0;z-index:30;background:rgba(7,21,47,.96);backdrop-filter:blur(12px);color:#fff;padding:16px 6%;display:flex;align-items:center;justify-content:space-between;gap:25px;border-bottom:1px solid rgba(255,255,255,.08)}}.brand{{font-weight:900;letter-spacing:-.02em;font-size:18px}}.navlinks{{display:flex;gap:24px;align-items:center;font-size:14px}}.navlinks a{{text-decoration:none;color:#dce6f7}}.btn{{display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:11px;padding:13px 20px;font-weight:850;text-decoration:none;border:1px solid transparent;cursor:pointer;transition:.2s transform,.2s box-shadow}}.btn:hover{{transform:translateY(-1px);box-shadow:0 10px 25px rgba(0,0,0,.14)}}.btn-gold{{background:var(--gold);color:#111}}.btn-blue{{background:var(--blue);color:#fff}}.btn-outline{{border-color:#cdd7e6;color:var(--ink);background:#fff}}.hero{{min-height:650px;background-size:cover;background-position:center;display:flex;align-items:center;color:#fff;padding:86px 6%}}.hero-inner{{max-width:1180px;width:100%;margin:auto}}.eyebrow{{font-weight:800;color:var(--gold2);letter-spacing:.08em;text-transform:uppercase;font-size:13px}}h1{{font-size:clamp(44px,6.4vw,78px);line-height:1.02;letter-spacing:-.045em;max-width:850px;margin:14px 0 22px}}.hero p{{font-size:20px;line-height:1.65;max-width:690px;color:#e5ecf8;margin-bottom:30px}}.hero-actions{{display:flex;gap:12px;flex-wrap:wrap}}.hero-note{{margin-top:20px;font-size:13px;color:#cdd8ea}}section{{padding:78px 6%}}.wrap{{max-width:1180px;margin:auto}}.section-head{{max-width:720px;margin-bottom:35px}}.section-head h2{{font-size:clamp(31px,4vw,48px);line-height:1.08;letter-spacing:-.035em;margin:0 0 12px}}.section-head p{{color:var(--muted);margin:0}}.trust-strip{{background:#fff;border:1px solid var(--line);box-shadow:var(--shadow);border-radius:20px;padding:23px;display:grid;grid-template-columns:repeat(3,1fr);gap:20px;transform:translateY(-35px);margin-bottom:-10px}}.trust-item{{display:flex;flex-direction:column;padding:5px 18px;border-right:1px solid var(--line)}}.trust-item:last-child{{border-right:0}}.trust-item strong{{font-size:25px;line-height:1.1}}.trust-item span{{font-size:13px;color:var(--muted);margin-top:4px}}.services{{background:#fff}}.service-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.service-card{{background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:27px;box-shadow:0 8px 28px rgba(8,25,55,.05);display:flex;flex-direction:column;min-height:235px}}.icon{{width:42px;height:42px;border-radius:12px;background:#eaf2ff;color:var(--blue);display:grid;place-items:center;font-weight:900;margin-bottom:16px}}.service-card h3{{margin:0 0 8px;font-size:20px}}.service-card p{{color:var(--muted);font-size:14px;margin:0 0 17px}}.service-card a{{margin-top:auto;color:var(--blue);font-weight:800;text-decoration:none}}.why{{background:var(--bg)}}.why-grid{{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}}.why-box{{background:var(--navy);color:#fff;border-radius:25px;padding:42px;box-shadow:var(--shadow)}}.why-box h3{{font-size:30px;line-height:1.15;margin:0 0 12px}}.why-box p{{color:#cbd7e9}}.checklist{{display:grid;gap:13px;margin-top:25px}}.check{{display:flex;gap:12px;align-items:flex-start}}.check b{{color:var(--gold)}}.review-box{{background:#fff;border:1px solid var(--line);border-radius:20px;padding:32px;box-shadow:var(--shadow)}}.stars{{color:#e3a900;letter-spacing:2px;font-size:23px}}.review-meta{{font-size:13px;color:var(--muted)}}.gallery-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}}figure{{margin:0;background:#fff;border:1px solid var(--line);border-radius:15px;overflow:hidden}}figure img{{display:block;width:100%;height:210px;object-fit:cover}}figcaption{{font-size:12px;color:var(--muted);padding:9px 12px}}.area{{background:#eef4fb}}.area-card{{background:#fff;border:1px solid var(--line);border-radius:22px;padding:34px;display:flex;justify-content:space-between;gap:25px;align-items:center}}.area-card h2{{margin:0 0 8px;font-size:30px}}.area-card p{{margin:0;color:var(--muted)}}.quote{{background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff}}.quote-grid{{display:grid;grid-template-columns:.9fr 1.1fr;gap:45px;align-items:start}}.quote h2{{font-size:44px;line-height:1.05;margin:0 0 14px}}.quote p{{color:#d3deee}}.form{{background:#fff;color:var(--ink);border-radius:22px;padding:28px;box-shadow:var(--shadow)}}.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}label{{display:block;font-size:12px;font-weight:800;margin-bottom:6px}}input,textarea{{width:100%;border:1px solid #d7dfeb;border-radius:10px;padding:13px;font:inherit;outline:none}}textarea{{min-height:120px;resize:vertical}}.full{{grid-column:1/-1}}.faq{{display:grid;grid-template-columns:1fr 1fr;gap:15px}}details{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px}}summary{{font-weight:850;cursor:pointer}}details p{{color:var(--muted);font-size:14px}}.seo-strip{{padding:22px 6%;background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}.seo-inner{{max-width:1180px;margin:auto;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}.seo-inner span{{font-size:12px;padding:7px 10px;background:#eef4fb;border-radius:999px;color:#39506f}}footer{{background:#061126;color:#b8c6db;padding:45px 6% 100px}}.footer-grid{{max-width:1180px;margin:auto;display:flex;justify-content:space-between;gap:25px}}footer strong{{color:#fff}}.sticky-mobile{{display:none}}
@media(max-width:900px){{.navlinks{{display:none}}.hero{{min-height:590px;padding:70px 6%}.service-grid,.gallery-grid{{grid-template-columns:1fr 1fr}}.why-grid,.quote-grid{{grid-template-columns:1fr}}.area-card{{display:block}.area-card .btn{{margin-top:18px}}.faq{{grid-template-columns:1fr}}}}
@media(max-width:600px){{section{{padding:58px 5%}}.trust-strip{{grid-template-columns:1fr;transform:none;margin-top:20px;margin-bottom:0}}.trust-item{{border-right:0;border-bottom:1px solid var(--line);padding:10px 4px 16px}}.trust-item:last-child{{border-bottom:0}}.hero{{min-height:640px;padding:55px 5%}}h1{{font-size:45px}}.hero p{{font-size:17px}}.service-grid,.gallery-grid,.form-grid{{grid-template-columns:1fr}}.full{{grid-column:auto}}.quote h2{{font-size:36px}}.sticky-mobile{{position:fixed;z-index:50;bottom:0;left:0;right:0;background:#fff;padding:9px;display:grid;grid-template-columns:1fr 1fr;gap:8px;box-shadow:0 -8px 25px rgba(0,0,0,.15)}}.sticky-mobile a{{padding:12px;text-align:center;border-radius:9px;text-decoration:none;font-weight:900}.sticky-call{{background:var(--navy);color:#fff}}.sticky-quote{{background:var(--gold);color:#111}}footer{{padding-bottom:85px}}}}
</style>
</head>
<body>
<div class="topbar">{('<b>Need service?</b> Call now for a faster response.' if phone else '<b>Local service</b> — request availability and a quote today.')}</div>
<nav><div class="brand">{esc(name)}</div><div class="navlinks"><a href="#services">Services</a><a href="#why">Why Us</a><a href="#reviews">Reviews</a><a href="#area">Service Area</a></div><a class="btn btn-gold" href="{phone_link}">{'Call Now' if phone else 'Get a Quote'}</a></nav>
<header class="hero" style="{image_style}"><div class="hero-inner"><div class="eyebrow">{esc(category)}{(' · ' + esc(city)) if city else ''}</div><h1>Reliable {esc(category.lower())} when you need it.</h1><p>Get clear information, responsive communication, and a simple way to request service from <strong>{esc(name)}</strong>.</p><div class="hero-actions"><a class="btn btn-gold" href="#quote">{esc(cta_label)}</a><a class="btn" style="background:#fff;color:#0a1730" href="{phone_link}">{'Call ' + esc(phone) if phone else 'Contact Business'}</a></div><div class="hero-note">Local-service website designed around calls, quote requests, trust, and location relevance.</div></div></header>
<main>
<div class="wrap"><div class="trust-strip">{''.join(f'<div class="trust-item">{x}</div>' for x in trust_items)}</div></div>
<section id="services" class="services"><div class="wrap"><div class="section-head"><h2>Services customers can request</h2><p>Choose the service you need and request current availability or pricing directly.</p></div><div class="service-grid">{service_cards}</div></div></section>
<section id="why" class="why"><div class="wrap why-grid"><div><div class="section-head"><h2>A better local-service experience</h2><p>The page keeps the most important conversion paths visible while making the business, service, and location context easy to understand.</p></div><div class="checklist"><div class="check"><b>✓</b><span>Clear service-first navigation</span></div><div class="check"><b>✓</b><span>Prominent call and quote actions</span></div><div class="check"><b>✓</b><span>Trust and review information above the fold</span></div><div class="check"><b>✓</b><span>Mobile sticky conversion bar</span></div></div></div><div class="why-box"><h3>Need help now?</h3><p>Use the fastest available contact option below to request service.</p><a class="btn btn-gold" href="{phone_link}">{'Call Now' if phone else 'Request Service'}</a></div></div></section>
<section id="reviews"><div class="wrap"><div class="section-head"><h2>Local trust at a glance</h2><p>Use verified Google Business Profile information when available. Do not fabricate testimonials or review text.</p></div><div class="review-box">{('<div class="stars">★★★★★</div><h3>Google rating: ' + esc(rating) + '</h3><p class="review-meta">Based on ' + esc(reviews) + ' Google reviews.</p>' if rating is not None and reviews is not None else '<h3>Google review data not supplied</h3><p class="review-meta">Connect the verified Business Profile data to display the live rating and review count.</p>')} {('<a class="btn btn-outline" href="' + esc(maps_link) + '" target="_blank" rel="noopener">View on Google Maps</a>') if maps_link else ''}</div></div></section>
{('<section><div class="wrap"><div class="section-head"><h2>Real business photos</h2><p>Photos supplied by the verified lead source are displayed without inventing business imagery.</p></div><div class="gallery-grid">' + gallery + '</div></div></section>') if gallery else ''}
<section id="area" class="area"><div class="wrap"><div class="area-card"><div><h2>Serving {esc(service_area_text)}</h2><p>{esc(address or 'Contact the business to confirm your service location.')}</p></div><a class="btn btn-blue" href="{esc(maps_link)}" target="_blank" rel="noopener">Open Google Maps</a></div></div></section>
{('<section><div class="wrap"><div class="section-head"><h2>Growth opportunities</h2><p>This section is generated from the selected lead and audit brief.</p></div><div class="checklist">' + opp_items + '</div></div></section>') if opp_items else ''}
<section id="quote" class="quote"><div class="wrap quote-grid"><div><div class="eyebrow">Request service</div><h2>Ready to get started?</h2><p>Send a short request. The business can follow up with availability, pricing, and next steps.</p><p><strong>{esc(name)}</strong><br>{esc(address or city)}</p></div><form class="form" onsubmit="submitLead(event)"><div class="form-grid"><div><label for="fullName">Name</label><input id="fullName" required placeholder="Your name"></div><div><label for="phoneField">Phone</label><input id="phoneField" required placeholder="(555) 555-5555"></div><div class="full"><label for="serviceField">Service needed</label><input id="serviceField" placeholder="What do you need help with?"></div><div class="full"><label for="messageField">Message</label><textarea id="messageField" placeholder="Tell us briefly what you need."></textarea></div><div class="full"><button class="btn btn-gold" type="submit">Request a Quote</button><p id="formStatus" style="font-size:12px;color:#60708b;margin:10px 0 0">Your request is prepared for the business to follow up.</p></div></div></form></div></section>
<section><div class="wrap"><div class="section-head"><h2>Frequently asked questions</h2><p>Common questions are kept concise so customers can reach the business quickly.</p></div><div class="faq"><details><summary>How do I request service?</summary><p>Use the quote form or call the business directly if a phone number is available.</p></details><details><summary>What services are available?</summary><p>Review the service cards above or contact the business for its current service list.</p></details><details><summary>Do you serve my area?</summary><p>The listed service area is based on the lead information. Confirm availability directly before booking.</p></details><details><summary>How can I get pricing?</summary><p>Send a quote request with your service needs and contact information.</p></details></div></div></section>
</main>
{('<div class="seo-strip"><div class="seo-inner"><strong>SEO focus:</strong>' + focus_items + '</div></div>') if focus_items else ''}
<footer><div class="footer-grid"><div><strong>{esc(name)}</strong><br>{esc(category)}{(' · ' + esc(city)) if city else ''}</div><div>{esc(address or city)}{('<br>' + esc(phone)) if phone else ''}</div></div></footer>
<div class="sticky-mobile"><a class="sticky-call" href="{phone_link}">{'Call Now' if phone else 'Contact'}</a><a class="sticky-quote" href="#quote">Get Free Quote</a></div>
<script>
function submitLead(e){{e.preventDefault();const name=document.getElementById('fullName').value.trim();const phone=document.getElementById('phoneField').value.trim();const service=document.getElementById('serviceField').value.trim();const msg=document.getElementById('messageField').value.trim();const text='Name: '+name+'\\nPhone: '+phone+'\\nService: '+service+'\\nMessage: '+msg;const status=document.getElementById('formStatus');status.textContent='Request captured. Please use the phone/contact method above to send it to the business.';if({str(bool(phone)).lower()}){{window.location.href='mailto:?subject='+encodeURIComponent('Service request for {esc(name)}')+'&body='+encodeURIComponent(text)}}}}
</script>
</body></html>'''
