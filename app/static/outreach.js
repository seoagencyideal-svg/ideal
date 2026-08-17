/* Outreach module: deterministic, human-review workflow. */
(function () {
  function esc(value) {
    return typeof escapeHtml === 'function' ? escapeHtml(value) : String(value ?? '');
  }

  function auditHighlights() {
    const audit = current.audit;
    if (!audit) return [];
    return (audit.issues || []).slice(0, 3);
  }

  function parseAiSalesAnalysis() {
    const el = document.getElementById('ai');
    if (!el || !el.textContent.trim()) return null;
    try {
      let text = el.textContent.trim();
      text = text.replace(/^```json\s*/i, '').replace(/```$/i, '').trim();
      const data = JSON.parse(text);
      return data && typeof data === 'object' ? data : null;
    } catch (_) {
      return null;
    }
  }

  function buildOutreach() {
    const name = current.name || 'there';
    const category = current.category || 'local business';
    const location = current.city || 'your area';
    const score = typeof current.score === 'number' ? current.score : null;
    const audit = current.audit || null;
    const ai = parseAiSalesAnalysis();
    const issues = auditHighlights();
    const noWebsite = !current.website;

    let subject = `A quick growth opportunity for ${name}`;
    let opening = `I was reviewing ${category.toLowerCase()} businesses in ${location} and came across ${name}.`;
    let opportunity = noWebsite
      ? `I noticed there doesn't appear to be a website attached to the business profile. That can make it harder for high-intent local customers to learn about your services and contact you.`
      : `I noticed a few opportunities on the current website and local search presence that may be worth reviewing.`;

    if (ai && typeof ai.outreach_subject === 'string' && ai.outreach_subject.trim()) {
      subject = ai.outreach_subject.trim();
    }
    if (ai && typeof ai.outreach_message === 'string' && ai.outreach_message.trim()) {
      return { subject, message: ai.outreach_message.trim() };
    }

    const details = [];
    if (score !== null) details.push(`Our current opportunity score is ${score}/100.`);
    if (audit && typeof audit.score === 'number') details.push(`The live technical snapshot scored ${audit.score}/100.`);
    issues.forEach(issue => details.push(`One item worth checking: ${issue}.`));

    const detailText = details.length
      ? `\n\nA few notes from the initial review:\n• ${details.join('\n• ')}`
      : '';

    const nextStep = noWebsite
      ? `If you're open to it, I can put together a quick website concept showing how the business could turn local searches into calls and quote requests.`
      : `If you're open to it, I can send over the specific findings and a short improvement plan for the website and local search visibility.`;

    const message = `Hi ${name} team,\n\n${opening} ${opportunity}${detailText}\n\n${nextStep}\n\nWould you be open to a quick 5–10 minute conversation this week?\n\nBest regards,\nIdeal SEO Agency`;
    return { subject, message };
  }

  window.showOutreach = function () {
    showModule('Outreach', 'Personalized draft, human approval', `
      <p class="module-copy">Create a lead-specific outreach draft from the selected lead, Opportunity Score, live SEO Audit, and AI analysis. Nothing is sent automatically.</p>
      <div class="module-grid">
        <div><b>Business</b><span>${esc(current.name || 'No lead selected')}</span></div>
        <div><b>Location</b><span>${esc(current.city || '—')}</span></div>
        <div><b>Opportunity Score</b><span>${esc(current.score ?? 'Not analyzed')}</span></div>
        <div><b>SEO Audit</b><span>${current.audit ? esc(`${current.audit.score}/100`) : 'Not run'}</span></div>
      </div>
      <div class="form">
        <label>Subject</label>
        <input id="outreachSubject" class="module-input" value="">
        <label>Message</label>
        <textarea id="outreachMessage" class="module-textarea" rows="14"></textarea>
        <div class="searchbar">
          <button class="primary" id="prepareOutreachBtn" onclick="prepareOutreach()" type="button">Generate Personalized Draft</button>
          <button class="secondary" onclick="copyOutreach()" type="button">Copy Draft</button>
        </div>
      </div>
      <div id="outreachStatus" class="module-result">Draft is for human review. No email or message will be sent from this module.</div>
    `);
    prepareOutreach(true);
  };

  window.prepareOutreach = function (silent) {
    const subjectEl = document.getElementById('outreachSubject');
    const messageEl = document.getElementById('outreachMessage');
    const status = document.getElementById('outreachStatus');
    if (!subjectEl || !messageEl) return;
    if (!current.name) {
      if (!silent) alert('Select a lead first.');
      return;
    }
    try {
      const draft = buildOutreach();
      subjectEl.value = draft.subject;
      messageEl.value = draft.message;
      if (!silent && status) status.textContent = 'Personalized draft generated. Review it manually before sending.';
    } catch (e) {
      if (status) status.textContent = `Draft generation failed: ${e.message}`;
    }
  };

  window.copyOutreach = async function () {
    const subject = document.getElementById('outreachSubject')?.value || '';
    const message = document.getElementById('outreachMessage')?.value || '';
    const status = document.getElementById('outreachStatus');
    if (!subject && !message) return;
    const text = `Subject: ${subject}\n\n${message}`;
    try {
      await navigator.clipboard.writeText(text);
      if (status) status.textContent = 'Draft copied to clipboard.';
    } catch (_) {
      if (status) status.textContent = 'Copy was blocked by the browser. Select the draft manually and copy it.';
    }
  };

  // Keep the selected score available to Outreach without changing the scoring logic.
  const originalAnalyzeLead = window.analyzeLead;
  if (typeof originalAnalyzeLead === 'function') {
    window.analyzeLead = async function () {
      const result = await originalAnalyzeLead.apply(this, arguments);
      const scoreEl = document.getElementById('score');
      const value = scoreEl ? Number(scoreEl.textContent) : NaN;
      if (Number.isFinite(value)) current.score = value;
      return result;
    };
  }
})();
