(function(){
  const oldSearch=window.searchLeads;
  window.searchLeads=async function(){
    const category=document.getElementById('searchCategory').value.trim();
    const city=document.getElementById('searchCity').value.trim();
    const limit=Number(document.getElementById('searchLimit').value);
    if(!category||!city){document.getElementById('leadMessage').textContent='Enter both niche and city.';return;}
    const box=document.getElementById('leadMessage'); box.textContent='Finding local businesses without a working website…';
    try{
      const x=await api('/api/leads/search',{method:'POST',body:JSON.stringify({category,city,limit,no_website_only:true})});
      if(!x.ok)throw new Error(x.error||'Lead search failed');
      document.getElementById('leads').textContent=x.count;
      document.getElementById('missing').textContent=x.count;
      document.getElementById('high').textContent=x.count;
      box.textContent=`Found ${x.count} no-website prospects. These are the first sales targets.`;
      document.getElementById('leadTable').innerHTML=x.leads.map(l=>`<div class="lead-row"><div><strong>${escapeHtml(l.name)}</strong><small>${escapeHtml(l.address||city)}</small></div><div><span class="badge hot">No website</span></div><div>${l.rating?`★ ${l.rating} (${l.reviews||0})`:'—'}</div><button class="secondary small" onclick='loadLead(${JSON.stringify(l)})' type="button">Analyze</button></div>`).join('');
    }catch(e){box.textContent='Lead search error: '+e.message;}
  };

  window.loadLead=function(l){
    current={name:l.name,category:l.category,city:l.address||'',website:'',phone:l.phone||'',notes:`Google rating: ${l.rating||'N/A'}; reviews: ${l.reviews||0}`,rating:typeof l.rating==='number'?l.rating:null,reviews:typeof l.reviews==='number'?l.reviews:null,audit:null,place_id:l.id||'',maps_url:l.maps_url||'',photos:Array.isArray(l.photos)?l.photos:[]};
    ['name','category','city','website','phone','notes'].forEach(id=>document.getElementById(id).value=current[id]||'');
    document.getElementById('score').textContent='—';document.getElementById('priority').textContent='Waiting';document.getElementById('reasons').textContent='No-website lead loaded. Click Analyze Lead to score it.';window.scrollTo({top:document.body.scrollHeight/2,behavior:'smooth'});
  };

  window.showDemoBuilder=function(){
    showModule('Demo Builder','Client-specific website + real business photos',`<p class="module-copy">Build a mobile-friendly client website from the selected Google Business lead. For no-website leads, the builder uses Google Places business photos when available — no stock photos are substituted.</p><div class="module-grid"><div><b>Business</b><span>${escapeHtml(current.name||'No lead selected')}</span></div><div><b>Category</b><span>${escapeHtml(current.category||'—')}</span></div><div><b>Location</b><span>${escapeHtml(current.city||'—')}</span></div><div><b>Website</b><span>${escapeHtml(current.website||'No website')}</span></div></div><div id="photoStatus" class="module-result">${current.photos?.length?`Google Places photos available: ${current.photos.length}`:'No Google Places photos returned for this lead.'}</div><button class="primary" id="generateDemoBtn" onclick="generateDemoBrief()" type="button">Build & Deploy Website Demo</button><div id="demoResult" class="module-result"></div>`);
  };

  window.generateDemoBrief=async function(){
    const button=document.getElementById('generateDemoBtn'),result=document.getElementById('demoResult');
    if(!current.name){alert('Select a lead first.');return;}
    if(button){button.disabled=true;button.textContent='Building website…';}
    try{
      const brief=buildDemoBrief();
      const x=await api('/api/demos',{method:'POST',body:JSON.stringify({business:current,brief})});
      if(!x.ok)throw new Error(x.error||'Demo deployment failed');
      demoCount+=1;updateDemoCounter();
      const absolute=new URL(x.url,window.location.origin).href;
      result.innerHTML=`<div class="audit-summary"><h3>Website Demo Live</h3><p>Client-specific mobile-friendly website generated and served from this application.</p><p><strong>Real Google Places photos:</strong> ${current.photos?.length||0}</p><a class="cta" href="${absolute}" target="_blank" rel="noopener">Open Live Demo</a></div><p class="module-copy">This is the live demo URL for review. It is not automatically sent to the business.</p>`;
    }catch(e){result.innerHTML=`<h3>Website generation failed</h3><p>${escapeHtml(e.message)}</p>`;}
    finally{if(button){button.disabled=false;button.textContent='Build & Deploy Website Demo';}}
  };
})();