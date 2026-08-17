/* Visual Demo Builder: client-specific preview, no external dependencies. */
(function () {
  function esc(value) {
    return typeof escapeHtml === 'function' ? escapeHtml(value) : String(value ?? '');
  }

  function serviceList(category) {
    const c = (category || 'local business').toLowerCase();
    if (c.includes('plumb')) return ['Emergency Plumbing', 'Drain Cleaning', 'Water Heaters', 'Leak Repair'];
    if (c.includes('hvac') || c.includes('air')) return ['AC Repair', 'Heating Service', 'Maintenance', 'Emergency Service'];
    if (c.includes('roof')) return ['Roof Repair', 'Roof Replacement', 'Inspections', 'Emergency Roofing'];
    if (c.includes('electric')) return ['Electrical Repair', 'Panel Upgrades', 'Lighting', 'Emergency Electrical'];
    return ['Core Services', 'Emergency Service', 'Free Estimates', 'Local Service'];
  }

  function buildPreview() {
    const noWebsite = !current.website;
    const rating = typeof current.rating === 'number' ? current.rating.toFixed(1) : null;
    const reviews = typeof current.reviews === 'number' ? current.reviews : null;
    const services = serviceList(current.category);
    const phone = current.phone || '';
    const location = current.city || 'Your Service Area';
    const business = current.name || 'Local Business';
    return `
      <div class="demo-preview">
        <div class="demo-browser"><span></span><span></span><span></span><b>Client Demo Preview</b></div>
        <div class="demo-site">
          <div class="demo-nav"><strong>${esc(business)}</strong><div><span>Services</span><span>Reviews</span><span>Service Area</span><button>${noWebsite ? 'Get a Free Quote' : 'Request Service'}</button></div></div>
          <section class="demo-hero">
            <div><small>LOCAL ${esc((current.category || 'BUSINESS').toUpperCase())} · ${esc(location)}</small><h2>Reliable ${esc(current.category || 'local')} service when you need it.</h2><p>Fast, professional service for homeowners in ${esc(location)} and nearby areas.</p><div class="demo-actions"><button>${noWebsite ? 'Get a Free Quote' : 'Request Service'}</button>${phone ? `<a href="tel:${esc(phone)}">Call ${esc(phone)}</a>` : '<a href="#contact">Contact Us</a>'}</div></div>
            <div class="demo-trust">${rating ? `<strong>★ ${esc(rating)}</strong><span>${esc(reviews || 0)} Google reviews</span>` : '<strong>Trusted Local Service</strong><span>Built for local conversions</span>'}</div>
          </section>
          <section class="demo-section"><small>WHAT WE DO</small><h3>Our Services</h3><div class="demo-cards">${services.map(s => `<article><b>${esc(s)}</b><p>Professional ${esc(s.toLowerCase())} with clear pricing and a fast response.</p></article>`).join('')}</div></section>
          <section class="demo-section demo-proof"><div><small>WHY CHOOSE US</small><h3>Built around trust and local service.</h3><p>Clear calls to action, service-focused pages, local search structure, and mobile-first contact paths.</p></div><div class="demo-points"><span>✓ Mobile-first design</span><span>✓ Click-to-call CTA</span><span>✓ Local SEO structure</span><span>✓ Service-area targeting</span></div></section>
          <section class="demo-section" id="contact"><div class="demo-contact"><div><small>READY TO HELP</small><h3>Request Service Today</h3><p>Make it easy for local customers to contact the business from search, mobile, and service pages.</p></div><button>${noWebsite ? 'Get a Free Quote' : 'Request Service'}</button></div></section>
        </div>
      </div>`;
  }

  window.showDemoBuilder = function () {
    showModule('Demo Builder', 'Client-specific website preview', `
      <p class="module-copy">Turn the selected lead into a visual, client-specific landing page preview. This is a sales demo foundation, not a replacement for the client's production website.</p>
      <div class="module-grid">
        <div><b>Business</b><span>${esc(current.name || 'No lead selected')}</span></div>
        <div><b>Category</b><span>${esc(current.category || '—')}</span></div>
        <div><b>Location</b><span>${esc(current.city || '—')}</span></div>
        <div><b>Current Website</b><span>${esc(current.website || 'No website found')}</span></div>
      </div>
      <div class="searchbar">
        <button class="primary" id="generateDemoBtn" onclick="generateDemoPreview()" type="button">Generate Visual Demo</button>
        <button class="secondary" onclick="downloadDemoHtml()" type="button">Export HTML</button>
      </div>
      <div id="demoResult" class="module-result"><div class="demo-empty">Select a lead and generate the visual demo preview.</div></div>
    `);
  };

  window.generateDemoPreview = function () {
    const result = document.getElementById('demoResult');
    const button = document.getElementById('generateDemoBtn');
    if (!current.name) { alert('Select a lead first.'); return; }
    if (button) { button.disabled = true; button.textContent = 'Building preview…'; }
    try {
      result.innerHTML = buildPreview();
      if (typeof demoCount !== 'undefined') { demoCount += 1; updateDemoCounter(); }
    } catch (e) {
      result.innerHTML = `<h3>Demo generation failed</h3><p>${esc(e.message)}</p>`;
    } finally {
      if (button) { button.disabled = false; button.textContent = 'Regenerate Visual Demo'; }
    }
  };

  window.downloadDemoHtml = function () {
    if (!current.name) { alert('Select a lead first.'); return; }
    const preview = buildPreview();
    const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(current.name)} — Demo</title><style>body{margin:0;font-family:Inter,Arial,sans-serif;background:#070b1a;color:#eef2ff}.demo-site{max-width:1100px;margin:auto}.demo-nav{display:flex;justify-content:space-between;padding:22px;align-items:center}.demo-nav div{display:flex;gap:18px;align-items:center}.demo-nav button,.demo-actions button,.demo-contact button{background:#f6c33b;border:0;border-radius:9px;padding:11px 16px;font-weight:800}.demo-hero{padding:70px 8%;display:grid;grid-template-columns:1fr 260px;gap:30px;background:linear-gradient(135deg,#111b45,#080d20)}.demo-hero h2{font-size:46px;margin:14px 0}.demo-hero p{color:#aab5d3;line-height:1.7}.demo-actions{display:flex;gap:12px;align-items:center}.demo-actions a{color:#f6c33b}.demo-trust{border:1px solid #29365f;border-radius:16px;padding:28px;align-self:center}.demo-trust strong,.demo-trust span{display:block}.demo-trust strong{font-size:34px;color:#f6c33b}.demo-section{padding:55px 8%}.demo-section small{color:#f6c33b;letter-spacing:2px}.demo-section h3{font-size:30px}.demo-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.demo-cards article{padding:22px;background:#0d1530;border:1px solid #202d55;border-radius:14px}.demo-cards p,.demo-proof p{color:#9da9c8;line-height:1.6}.demo-proof{display:grid;grid-template-columns:1fr 1fr;gap:30px}.demo-points{display:grid;gap:12px}.demo-contact{padding:30px;border:1px solid #29365f;border-radius:16px;display:flex;justify-content:space-between;align-items:center}@media(max-width:800px){.demo-nav div span{display:none}.demo-hero,.demo-proof{grid-template-columns:1fr}.demo-cards{grid-template-columns:1fr 1fr}.demo-hero h2{font-size:34px}}</style></head><body>${preview.replace(/<div class="demo-browser">[\s\S]*?<\/div>/,'')}</body></html>`;
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `${(current.name || 'client').replace(/[^a-z0-9]+/gi,'-').toLowerCase()}-demo.html`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
})();
