// ── Per-tab state ────────────────────────────────────────────────────────────
const escoState = {
  occupations: { page: 1, perPage: 25, total: 0, search: '', sortBy: 'preferred_label', sortOrder: 'asc', filter: {} },
  skills:      { page: 1, perPage: 25, total: 0, search: '', sortBy: 'preferred_label', sortOrder: 'asc', filter: {} },
  isco:        { page: 1, perPage: 25, total: 0, search: '', sortBy: 'preferred_label', sortOrder: 'asc', allRows: [] },
};

let escoActiveTab = 'occupations';
let escoDebounce  = null;

// ── Init ─────────────────────────────────────────────────────────────────────

async function escoInit(subtab) {
  setupEscoSubtabs();
  setupEscoSearch();
  escoActiveTab = subtab || 'occupations';
  syncSubtabUI(escoActiveTab);
  await loadEscoTab(true);
}

function escoNavigate(subtab) {
  const target = subtab || 'occupations';
  if (escoActiveTab !== target) {
    escoActiveTab = target;
    document.getElementById('esco-search').value = escoState[target].search;
    syncSubtabUI(target);
    loadEscoTab(true);
  }
}

function syncSubtabUI(tab) {
  document.querySelectorAll('#panel-esco .sub-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.subtab === tab));
  renderFilterControls(tab);
}

// ── Event setup ───────────────────────────────────────────────────────────────

function setupEscoSubtabs() {
  document.querySelectorAll('#panel-esco .sub-tab').forEach(btn =>
    btn.addEventListener('click', () => pushEscoSubtab(btn.dataset.subtab)));
}

function setupEscoSearch() {
  document.getElementById('esco-search').addEventListener('input', e => {
    clearTimeout(escoDebounce);
    escoDebounce = setTimeout(() => {
      escoState[escoActiveTab].search = e.target.value.trim();
      escoState[escoActiveTab].page   = 1;
      loadEscoTab(true);
    }, 350);
  });
}

// ── Filter controls (per-tab dropdowns rendered into #esco-filters) ───────────

function renderFilterControls(tab) {
  const el = document.getElementById('esco-filters');
  if (tab === 'skills') {
    el.innerHTML = `
      <select id="filter-skill-type" class="filter-select" title="Type">
        <option value="">All types</option>
        <option value="skill/competence">Skill / Competence</option>
        <option value="knowledge">Knowledge</option>
      </select>`;
    const st = escoState.skills.filter;
    el.querySelector('#filter-skill-type').value = st.type || '';
    el.querySelector('#filter-skill-type').addEventListener('change', e => {
      escoState.skills.filter.type = e.target.value;
      escoState.skills.page = 1;
      loadEscoTab(true);
    });
  } else {
    el.innerHTML = '';
  }
}

// ── Main load dispatcher ──────────────────────────────────────────────────────

async function loadEscoTab(reset) {
  if (reset) {
    document.getElementById('esco-content').innerHTML = '<div class="loading">Loading…</div>';
    document.getElementById('esco-pagination').innerHTML = '';
  }
  if (escoActiveTab === 'isco') {
    await loadIscoGroups(reset);
  } else {
    await loadEscoData(reset);
  }
}

// ── Occupations & Skills ──────────────────────────────────────────────────────

async function loadEscoData(reset) {
  const tab = escoActiveTab;
  const st  = escoState[tab];
  const endpoint = tab === 'occupations' ? '/api/esco/occupations' : '/api/esco/skills';

  const params = new URLSearchParams({
    limit:      st.perPage,
    offset:     (st.page - 1) * st.perPage,
    sort_by:    st.sortBy,
    sort_order: st.sortOrder,
  });
  if (st.search) params.set('search', st.search);
  if (tab === 'skills' && st.filter.type) params.set('type', st.filter.type);

  try {
    const res  = await fetch(`${endpoint}?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    st.total = data.total;
    const container = document.getElementById('esco-content');

    if (data.items.length === 0) {
      container.innerHTML = '<div class="empty-state">No results found.</div>';
      document.getElementById('esco-pagination').innerHTML = '';
      return;
    }

    if (tab === 'occupations') renderOccupationTable(data.items, container, st);
    else                       renderSkillTable(data.items, container, st);

    renderPagination(st, () => loadEscoTab(false));
  } catch (err) {
    document.getElementById('esco-content').innerHTML =
      `<div class="empty-state">Error loading data: ${err.message}</div>`;
  }
}

// ── ISCO Groups (all loaded once, client-side pagination + search) ─────────────

async function loadIscoGroups(_reset) {
  const st = escoState.isco;
  try {
    if (st.allRows.length === 0) {
      const res  = await fetch('/api/esco/isco_groups');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      st.allRows = await res.json();
    }

    const q       = st.search.toLowerCase();
    const filtered = q
      ? st.allRows.filter(r =>
          (r.preferred_label || '').toLowerCase().includes(q) ||
          (r.description     || '').toLowerCase().includes(q) ||
          (r.id              || '').toLowerCase().includes(q))
      : st.allRows;

    // sort
    const dir = st.sortOrder === 'asc' ? 1 : -1;
    const key = st.sortBy === 'id' ? 'id' : 'preferred_label';
    const sorted = [...filtered].sort((a, b) =>
      dir * String(a[key] || '').localeCompare(String(b[key] || '')));

    st.total = sorted.length;
    const start = (st.page - 1) * st.perPage;
    const items = sorted.slice(start, start + st.perPage);

    const container = document.getElementById('esco-content');

    if (items.length === 0) {
      container.innerHTML = '<div class="empty-state">No results found.</div>';
      document.getElementById('esco-pagination').innerHTML = '';
      return;
    }

    renderIscoTable(items, container, st);
    renderPagination(st, () => loadEscoTab(false));
  } catch (err) {
    document.getElementById('esco-content').innerHTML =
      `<div class="empty-state">Error: ${err.message}</div>`;
  }
}

// ── Table renderers ───────────────────────────────────────────────────────────

function sortArrow(col, st) {
  if (st.sortBy !== col) return '<span class="sort-arrow sort-arrow--none">⇅</span>';
  return st.sortOrder === 'asc'
    ? '<span class="sort-arrow sort-arrow--asc">↑</span>'
    : '<span class="sort-arrow sort-arrow--desc">↓</span>';
}

function thSort(label, col, st) {
  return `<th class="sortable" data-col="${col}">${label} ${sortArrow(col, st)}</th>`;
}

function attachSortListeners(table, st, reloadFn) {
  table.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (st.sortBy === col) {
        st.sortOrder = st.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        st.sortBy    = col;
        st.sortOrder = 'asc';
      }
      st.page = 1;
      reloadFn();
    });
  });
}

function renderOccupationTable(items, container, st) {
  const table = document.createElement('table');
  table.className = 'data-table';
  table.innerHTML = `
    <thead><tr>
      ${thSort('Code',   'code',            st)}
      ${thSort('Label',  'preferred_label', st)}
      ${thSort('Status', 'status',          st)}
    </tr></thead>
    <tbody>${items.map(o => `
      <tr data-id="${o.id}">
        <td>${o.code || '—'}</td>
        <td>${o.preferred_label}</td>
        <td><span class="badge">${o.status || '—'}</span></td>
      </tr>`).join('')}
    </tbody>`;
  container.innerHTML = '';
  container.appendChild(table);

  table.querySelectorAll('tbody tr').forEach(tr =>
    tr.addEventListener('click', () => goToEscoDetail('occupations', tr.dataset.id)));
  attachSortListeners(table, st, () => loadEscoTab(false));
}

function renderSkillTable(items, container, st) {
  const table = document.createElement('table');
  table.className = 'data-table';
  table.innerHTML = `
    <thead><tr>
      ${thSort('Label',       'preferred_label', st)}
      ${thSort('Type',        'type',            st)}
      ${thSort('Reuse Level', 'reuse_level',     st)}
      ${thSort('Status',      'status',          st)}
    </tr></thead>
    <tbody>${items.map(s => `
      <tr data-id="${s.id}">
        <td>${s.preferred_label}</td>
        <td>${s.type || '—'}</td>
        <td>${s.reuse_level || '—'}</td>
        <td><span class="badge">${s.status || '—'}</span></td>
      </tr>`).join('')}
    </tbody>`;
  container.innerHTML = '';
  container.appendChild(table);

  table.querySelectorAll('tbody tr').forEach(tr =>
    tr.addEventListener('click', () => goToEscoDetail('skills', tr.dataset.id)));
  attachSortListeners(table, st, () => loadEscoTab(false));
}

function renderIscoTable(items, container, st) {
  const table = document.createElement('table');
  table.className = 'data-table';
  table.innerHTML = `
    <thead><tr>
      ${thSort('ID',          'id',              st)}
      ${thSort('Label',       'preferred_label', st)}
      <th>Description</th>
    </tr></thead>
    <tbody>${items.map(r => `
      <tr data-id="${r.id}">
        <td>${r.id}</td>
        <td>${r.preferred_label}</td>
        <td>${truncate(r.description || '', 120)}</td>
      </tr>`).join('')}
    </tbody>`;
  container.innerHTML = '';
  container.appendChild(table);

  table.querySelectorAll('tbody tr').forEach(tr =>
    tr.addEventListener('click', () => goToEscoDetail('isco', tr.dataset.id)));
  attachSortListeners(table, st, () => loadEscoTab(false));
}

// ── Pagination ────────────────────────────────────────────────────────────────

function renderPagination(st, reloadFn) {
  const bar       = document.getElementById('esco-pagination');
  const totalPages = Math.max(1, Math.ceil(st.total / st.perPage));
  const cur       = st.page;

  function btn(label, page, disabled = false, active = false) {
    return `<button class="pg-btn${active ? ' active' : ''}"
      data-page="${page}" ${disabled ? 'disabled' : ''}>${label}</button>`;
  }

  // Page number window
  const pages = [];
  const delta = 2;
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || (p >= cur - delta && p <= cur + delta)) {
      pages.push(p);
    }
  }
  // insert ellipsis markers
  const pageButtons = [];
  let prev = null;
  for (const p of pages) {
    if (prev !== null && p - prev > 1) pageButtons.push('<span class="pg-ellipsis">…</span>');
    pageButtons.push(btn(p, p, false, p === cur));
    prev = p;
  }

  // Per-page dropdown
  const perPageOpts = [10, 25, 50, 100].map(n =>
    `<option value="${n}" ${st.perPage === n ? 'selected' : ''}>${n}</option>`).join('');

  bar.innerHTML = `
    <div class="pg-info">
      Page <strong>${cur}</strong> of <strong>${totalPages}</strong>
      &nbsp;·&nbsp; ${st.total} total
    </div>
    <div class="pg-controls">
      ${btn('«', 1,            cur === 1)}
      ${btn('‹', cur - 1,     cur === 1)}
      ${pageButtons.join('')}
      ${btn('›', cur + 1,     cur === totalPages)}
      ${btn('»', totalPages,  cur === totalPages)}
    </div>
    <div class="pg-perpage">
      <label>Per page
        <select id="esco-per-page">${perPageOpts}</select>
      </label>
    </div>`;

  bar.querySelectorAll('.pg-btn:not([disabled])').forEach(b =>
    b.addEventListener('click', () => {
      st.page = parseInt(b.dataset.page, 10);
      reloadFn();
    }));

  bar.querySelector('#esco-per-page').addEventListener('change', e => {
    st.perPage = parseInt(e.target.value, 10);
    st.page    = 1;
    reloadFn();
  });
}

// ── Detail page helpers ───────────────────────────────────────────────────────

function dpSection(title, content) {
  if (!content) return '';
  return `
    <section class="dp-section">
      <h2 class="dp-section-title">${title}</h2>
      ${content}
    </section>`;
}

function dpText(value) {
  return value ? `<p class="dp-section-text">${value}</p>` : '';
}

function dpChips(items) {
  if (!items || items.length === 0) return '';
  return `<div class="dp-chips">${items.map(t => `<span class="dp-chip">${t}</span>`).join('')}</div>`;
}

function dpLinkChips(items, hashFn) {
  if (!items || items.length === 0) return '';
  return `<div class="dp-chips">${items.map(item =>
    `<a class="dp-chip dp-chip-link" href="${hashFn(item)}">${item.preferred_label}</a>`).join('')}</div>`;
}

async function renderEscoDetailPage(subtab, id) {
  const isSkill    = subtab === 'skills';
  const endpoint   = isSkill ? `/api/esco/skills/${id}` : `/api/esco/occupations/${id}`;
  const backHash   = buildHash('esco', subtab);
  const backLabel  = subtab.charAt(0).toUpperCase() + subtab.slice(1);

  showDetailPage(`<div class="page-loading"><div class="loading">Loading...</div></div>`);

  try {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const d   = await res.json();
    showDetailPage(isSkill
      ? renderSkillDetailPage(d, backHash, backLabel)
      : renderOccupationDetailPage(d, backHash, backLabel));
  } catch (err) {
    showDetailPage(`
      <div class="dp-header">
        <a class="dp-back" href="${backHash}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
               stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
          </svg>Back
        </a>
      </div>
      <div class="dp-body"><p class="dp-empty">Error loading data: ${err.message}</p></div>`);
  }
}

function renderOccupationDetailPage(d, backHash, backLabel) {
  const broaderOccs = d.broader_occupations?.length
    ? `<div class="dp-breadcrumb">
        <span class="dp-breadcrumb-sep">|</span>
        <span class="dp-breadcrumb-label">Part of</span>
        ${d.broader_occupations.map(o =>
          `<a class="dp-chip dp-chip-link dp-chip-sm"
              href="${buildHash('esco', 'occupations', o.occupation_id)}">${o.preferred_label}</a>`
        ).join('')}
      </div>` : '';

  const essentialSkills = d.essential_skills?.length
    ? dpSection('Essential Skills',
        dpLinkChips(d.essential_skills, s => buildHash('esco', 'skills', s.skill_id))) : '';
  const optionalSkills  = d.optional_skills?.length
    ? dpSection('Optional Skills',
        dpLinkChips(d.optional_skills,  s => buildHash('esco', 'skills', s.skill_id))) : '';
  const skillsRow = (essentialSkills || optionalSkills)
    ? `<div class="dp-skills-row">${essentialSkills}${optionalSkills}</div>` : '';

  const leftCol = `<div class="dp-col-main">
    ${dpSection('Description', dpText(d.description))}
    ${dpSection('Definition',  dpText(d.definition))}
    ${dpSection('Scope Note',  dpText(d.scope_note))}
    ${skillsRow}
  </div>`;

  const metaRows = [
    { label: 'Code',        value: d.code },
    { label: 'Status',      value: d.status },
    { label: 'ISCO Group',  value: d.isco_group_label },
    { label: 'Modified',    value: d.modified_date },
    { label: 'Green Share', value: d.green_share != null ? d.green_share : null },
  ].filter(r => r.value != null && r.value !== '');

  const metaCard = metaRows.length ? `
    <div class="dp-meta-card">
      <h2 class="dp-section-title">Details</h2>
      <dl class="dp-meta-dl">
        ${metaRows.map(r => `<dt>${r.label}</dt><dd>${r.value}</dd>`).join('')}
      </dl>
    </div>` : '';

  const externalLinks = [
    d.url                       && { label: 'ESCO URI',             href: d.url },
    d.regulated_profession_note && { label: 'Regulated Profession', href: d.regulated_profession_note },
    d.nace_code                 && { label: 'NACE',                 href: d.nace_code },
  ].filter(Boolean);

  const linksCard = externalLinks.length ? `
    <div class="dp-links-card">
      <h2 class="dp-section-title">External Links</h2>
      <ul class="dp-link-list">
        ${externalLinks.map(l => `<li>
          <a class="dp-ext-link" href="${l.href}" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
            </svg>${l.label}
          </a></li>`).join('')}
      </ul>
    </div>` : '';

  const altLabelsCard = d.alt_labels ? `
    <div class="dp-section">
      <h2 class="dp-section-title">Alternative Labels</h2>
      <ul class="dp-label-list">
        ${d.alt_labels.split('\n').filter(Boolean).map(l => `<li>${l.trim()}</li>`).join('')}
      </ul>
    </div>` : '';

  const rightCol = `<div class="dp-col-side">${metaCard}${linksCard}${altLabelsCard}</div>`;

  return `
    <div class="dp-header">
      <div class="dp-header-row">
        <h1 class="dp-title">${d.preferred_label}</h1>
        ${broaderOccs}
      </div>
    </div>
    <div class="dp-subbar">
      <a class="dp-back" href="${backHash}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
        </svg>Back to ${backLabel}
      </a>
    </div>
    <div class="dp-body dp-body-cols">${leftCol}${rightCol}</div>`;
}

function renderSkillDetailPage(d, backHash, backLabel) {
  const broaderSkills = d.broader_skills?.length
    ? `<div class="dp-breadcrumb">
        <span class="dp-breadcrumb-sep">|</span>
        <span class="dp-breadcrumb-label">Part of</span>
        ${d.broader_skills.map(s =>
          `<a class="dp-chip dp-chip-link dp-chip-sm"
              href="${buildHash('esco', 'skills', s.skill_id)}">${s.preferred_label}</a>`
        ).join('')}
      </div>` : '';

  const skillGroupsSection  = d.skill_groups?.length
    ? dpSection('Skill Groups',
        dpLinkChips(d.skill_groups,   g => buildHash('esco', 'skills', g.skill_group_id))) : '';
  const broaderSkillsSection = d.broader_skills?.length
    ? dpSection('Broader Skills',
        dpLinkChips(d.broader_skills, s => buildHash('esco', 'skills', s.skill_id))) : '';
  const collectionsSection   = d.collections?.length
    ? dpSection('Collections', dpChips(d.collections)) : '';

  const relatedRow = (skillGroupsSection || broaderSkillsSection)
    ? `<div class="dp-skills-row">${skillGroupsSection}${broaderSkillsSection}</div>` : '';

  const leftCol = `<div class="dp-col-main">
    ${dpSection('Description', dpText(d.description))}
    ${dpSection('Definition',  dpText(d.definition))}
    ${dpSection('Scope Note',  dpText(d.scope_note))}
    ${relatedRow}
    ${collectionsSection}
  </div>`;

  const metaRows = [
    { label: 'Type',        value: d.type },
    { label: 'Reuse Level', value: d.reuse_level },
    { label: 'Status',      value: d.status },
    { label: 'Modified',    value: d.modified_date },
  ].filter(r => r.value != null && r.value !== '');

  const metaCard = metaRows.length ? `
    <div class="dp-meta-card">
      <h2 class="dp-section-title">Details</h2>
      <dl class="dp-meta-dl">
        ${metaRows.map(r => `<dt>${r.label}</dt><dd>${r.value}</dd>`).join('')}
      </dl>
    </div>` : '';

  const externalLinks = [d.url && { label: 'ESCO URI', href: d.url }].filter(Boolean);

  const linksCard = externalLinks.length ? `
    <div class="dp-links-card">
      <h2 class="dp-section-title">External Links</h2>
      <ul class="dp-link-list">
        ${externalLinks.map(l => `<li>
          <a class="dp-ext-link" href="${l.href}" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
            </svg>${l.label}
          </a></li>`).join('')}
      </ul>
    </div>` : '';

  const altLabelsCard = d.alt_labels ? `
    <div class="dp-section">
      <h2 class="dp-section-title">Alternative Labels</h2>
      <ul class="dp-label-list">
        ${d.alt_labels.split('\n').filter(Boolean).map(l => `<li>${l.trim()}</li>`).join('')}
      </ul>
    </div>` : '';

  const hiddenLabelsCard = d.hidden_labels ? `
    <div class="dp-section">
      <h2 class="dp-section-title">Hidden Labels</h2>
      <ul class="dp-label-list">
        ${d.hidden_labels.split('\n').filter(Boolean).map(l => `<li>${l.trim()}</li>`).join('')}
      </ul>
    </div>` : '';

  const rightCol = `<div class="dp-col-side">${metaCard}${linksCard}${altLabelsCard}${hiddenLabelsCard}</div>`;

  return `
    <div class="dp-header">
      <div class="dp-header-row">
        <div>
          <div class="dp-eyebrow">Skill / Competence</div>
          <h1 class="dp-title">${d.preferred_label}</h1>
        </div>
        ${broaderSkills}
      </div>
    </div>
    <div class="dp-subbar">
      <a class="dp-back" href="${backHash}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
        </svg>Back to ${backLabel}
      </a>
    </div>
    <div class="dp-body dp-body-cols">${leftCol}${rightCol}</div>`;
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function truncate(str, len) {
  return str.length > len ? str.slice(0, len) + '…' : str;
}
