// ─── Router ──────────────────────────────────────────────────────────────────

const initialized = {};

function parseHash() {
  const hash = location.hash.replace(/^#\/?/, '');
  const parts = hash.split('/').filter(Boolean);
  const panel  = parts[0] || 'esco';
  const subtab = parts[1] || (panel === 'oja' ? 'jobs' : 'occupations');
  const id     = parts[2] || null;
  return { panel, subtab, id };
}

function buildHash(panel, subtab, id) {
  let h = `#/${panel}/${subtab}`;
  if (id) h += `/${id}`;
  return h;
}

function navigate(panel, subtab, id) {
  const next = buildHash(panel, subtab, id);
  if (location.hash !== next) location.hash = next;
  else route();
}

// ─── Shell visibility ─────────────────────────────────────────────────────────

// When showing a detail page we hide all panels and the bottom nav's active state
// but keep the chrome (top bar, bottom bar) in place.

function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  const panel = document.getElementById(`panel-${name}`);
  panel.classList.remove('hidden');
  panel.classList.add('active');
  document.querySelector(`.nav-btn[data-panel="${name}"]`).classList.add('active');
}

function showDetailPage(html) {
  // Hide all panels
  document.querySelectorAll('.panel').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });

  let page = document.getElementById('detail-page');
  if (!page) {
    page = document.createElement('div');
    page.id = 'detail-page';
    page.className = 'detail-page';
    document.querySelector('.content').appendChild(page);
  }
  page.innerHTML = html;
  page.classList.add('active');
}

function hideDetailPage() {
  const page = document.getElementById('detail-page');
  if (page) page.classList.remove('active');
}

function renderIscoGroupDetailPage(d, backHash, backLabel) {
  // Broader ISCO group breadcrumb
  const broaderGroup = d.broader_isco_group_id
    ? `<div class="dp-breadcrumb">
        <span class="dp-breadcrumb-sep">|</span>
        <span class="dp-breadcrumb-label">Part of</span>
        <a class="dp-chip dp-chip-link dp-chip-sm"
           href="${buildHash('esco', 'isco', d.broader_isco_group_id)}">
          ${d.broader_isco_group_id}
        </a>
      </div>`
    : '';

  // Occupations list
  const occupationsSection = d.occupations?.length
    ? dpSection('Occupations',
        dpLinkChips(d.occupations, o => buildHash('esco', 'occupations', o.id))
      )
    : '';

  const leftCol = `
    <div class="dp-col-main">
      ${dpSection('Description', dpText(d.description))}
      ${occupationsSection}
    </div>`;

  const metaRows = [
    { label: 'Status',      value: d.status },
    { label: 'Green Share', value: d.green_share != null ? d.green_share : null },
  ].filter(r => r.value != null && r.value !== '');

  const metaCard = metaRows.length ? `
    <div class="dp-meta-card">
      <h2 class="dp-section-title">Details</h2>
      <dl class="dp-meta-dl">
        ${metaRows.map(r => `<dt>${r.label}</dt><dd>${r.value}</dd>`).join('')}
      </dl>
    </div>` : '';

  const linksCard = d.url ? `
    <div class="dp-links-card">
      <h2 class="dp-section-title">External Links</h2>
      <ul class="dp-link-list">
        <li>
          <a class="dp-ext-link" href="${d.url}" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            ESCO URI
          </a>
        </li>
      </ul>
    </div>` : '';

  const altLabelsCard = d.alt_labels ? `
    <div class="dp-section">
      <h2 class="dp-section-title">Alternative Labels</h2>
      <ul class="dp-label-list">
        ${d.alt_labels.split('\n').filter(Boolean).map(l => `<li>${l.trim()}</li>`).join('')}
      </ul>
    </div>` : '';

  const rightCol = `
    <div class="dp-col-side">
      ${metaCard}
      ${linksCard}
      ${altLabelsCard}
    </div>`;

  return `
    <div class="dp-header">
      <div class="dp-header-row">
        <div>
          <div class="dp-eyebrow">ISCO Group</div>
          <h1 class="dp-title">${d.preferred_label}</h1>
        </div>
        ${broaderGroup}
      </div>
    </div>
    <div class="dp-subbar">
      <a class="dp-back" href="${backHash}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
        Back to ${backLabel}
      </a>
    </div>
    <div class="dp-body dp-body-cols">
      ${leftCol}
      ${rightCol}
    </div>`;
}

// ─── Route handler ────────────────────────────────────────────────────────────

async function route() {
  const { panel, subtab, id } = parseHash();

  hideDetailPage();

  if (id) {
    // Full detail page
    if (panel === 'esco') {
      await renderEscoDetailPage(subtab, id);
    } else if (panel === 'oja') {
      await renderOjaDetailPage(id);
    }
    return;
  }

  // List view
  showPanel(panel);

  if (panel === 'esco') {
    if (!initialized['esco']) {
      initialized['esco'] = true;
      await escoInit(subtab);
    } else {
      escoNavigate(subtab);
    }
  }

  if (panel === 'oja') {
    if (!initialized['oja']) {
      initialized['oja'] = true;
      ojaInit();
    } else {
      ojaNavigate();
    }
  }
}

// ─── URL helpers (called by esco.js / oja.js) ─────────────────────────────────

function pushEscoSubtab(subtab) {
  const next = buildHash('esco', subtab);
  if (location.hash !== next) location.hash = next;
}

function goToEscoDetail(subtab, id) {
  location.hash = buildHash('esco', subtab, id);
}

function goToOjaDetail(id) {
  location.hash = buildHash('oja', 'jobs', id);
}

function goBack() {
  history.back();
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const name = btn.dataset.panel;
    navigate(name, name === 'oja' ? 'jobs' : 'occupations');
  });
});

window.addEventListener('hashchange', route);

document.addEventListener('DOMContentLoaded', () => {
  if (!location.hash || location.hash === '#') {
    location.hash = '#/esco/occupations';
  } else {
    route();
  }
});
