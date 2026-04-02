// ── Employment type normalisation (mirrors backend EMPLOYMENT_TYPE_MAP) ────────
const EMPLOYMENT_TYPE_MAP = {
  'Full Time':           'Full Time',
  'FULL_TIME':           'Full Time',
  'Part Time':           'Part Time',
  'PART_TIME':           'Part Time',
  'FULL_TIME_PART_TIME': 'Full or Part Time',
  'Contractor':          'Contractor',
  'Intern':              'Intern',
  'SEASONAL':            'Seasonal',
  'Other':               'Other',
};

function normalizeEmploymentType(raw) {
  if (!raw) return null;
  return EMPLOYMENT_TYPE_MAP[raw] || raw;
}

// ── State ─────────────────────────────────────────────────────────────────────
const oja = {
  offset:        0,
  limit:         18,          // 3-column grid — multiples of 3 look clean
  total:         0,
  search:        '',
  sortBy:        'date_posted',
  sortOrder:     'desc',
  filter:        { employment_type: '' },
  debounceTimer: null,
  loading:       false,
};

// ── Init ──────────────────────────────────────────────────────────────────────

async function ojaInit() {
  await renderOjaControls();
  setupOjaSearch();
  setupOjaInfiniteScroll();
  loadOjaJobs(true);
}

function ojaNavigate() {
  // state preserved when switching panels
}

// ── Controls ──────────────────────────────────────────────────────────────────

async function renderOjaControls() {
  const el = document.getElementById('oja-filters');
  el.innerHTML = `
    <select id="oja-sort" class="filter-select" title="Sort by">
      <option value="date_posted|desc">Newest first</option>
      <option value="date_posted|asc">Oldest first</option>
      <option value="title|asc">Title A–Z</option>
      <option value="title|desc">Title Z–A</option>
      <option value="location|asc">Location A–Z</option>
    </select>
    <select id="oja-type" class="filter-select" title="Employment type">
      <option value="">All types</option>
    </select>`;

  el.querySelector('#oja-sort').addEventListener('change', e => {
    const [col, dir] = e.target.value.split('|');
    oja.sortBy    = col;
    oja.sortOrder = dir;
    loadOjaJobs(true);
  });

  el.querySelector('#oja-type').addEventListener('change', e => {
    oja.filter.employment_type = e.target.value;
    loadOjaJobs(true);
  });

  // Populate type options from backend
  try {
    const res  = await fetch('/api/oja/jobs/employment_types');
    if (!res.ok) throw new Error();
    const types = await res.json();
    const select = el.querySelector('#oja-type');
    types.forEach(({ label }) => {
      const opt = document.createElement('option');
      opt.value       = label;
      opt.textContent = label;
      select.appendChild(opt);
    });
  } catch {
    // silently keep the empty dropdown if fetch fails
  }
}

function setupOjaSearch() {
  document.getElementById('oja-search').addEventListener('input', e => {
    clearTimeout(oja.debounceTimer);
    oja.debounceTimer = setTimeout(() => {
      oja.search = e.target.value.trim();
      loadOjaJobs(true);
    }, 350);
  });
}

// ── Infinite scroll ───────────────────────────────────────────────────────────

function setupOjaInfiniteScroll() {
  const sentinel  = document.getElementById('oja-sentinel');
  const scrollEl  = document.getElementById('oja-scroll');
  if (!sentinel || !scrollEl) return;
  const obs = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && !oja.loading && oja.offset < oja.total) {
      loadOjaJobs(false);
    }
  }, { root: scrollEl, rootMargin: '200px' });
  obs.observe(sentinel);
}

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadOjaJobs(reset) {
  if (oja.loading) return;
  oja.loading = true;

  if (reset) {
    oja.offset = 0;
    document.getElementById('oja-content').innerHTML = '<div class="loading">Loading…</div>';
    document.getElementById('oja-status').textContent = '';
  }

  const params = new URLSearchParams({
    limit:      oja.limit,
    offset:     oja.offset,
    sort_by:    oja.sortBy,
    sort_order: oja.sortOrder,
  });
  if (oja.search)                params.set('search',          oja.search);
  if (oja.filter.employment_type) params.set('employment_type', oja.filter.employment_type);

  try {
    const res  = await fetch(`/api/oja/jobs?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    oja.total   = data.total;
    oja.offset += data.items.length;

    const container = document.getElementById('oja-content');

    if (reset) {
      if (data.items.length === 0) {
        container.innerHTML = '<div class="empty-state">No job postings found.</div>';
        document.getElementById('oja-status').textContent = '';
        return;
      }
      container.innerHTML = '';
    }

    renderJobCards(data.items, container);

    document.getElementById('oja-status').textContent =
      `Showing ${oja.offset} of ${oja.total} jobs`;

  } catch (err) {
    document.getElementById('oja-content').innerHTML =
      `<div class="empty-state">Error loading jobs: ${err.message}</div>`;
  } finally {
    oja.loading = false;
  }
}

// ── Card renderer ─────────────────────────────────────────────────────────────

function renderJobCards(items, container) {
  items.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.dataset.jobId = job.id;

    const date = job.date_posted
      ? new Date(job.date_posted).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
      : null;

    const meta = [
      { label: 'Location', value: job.location },
      { label: 'Type',     value: normalizeEmploymentType(job.employment_type) },
      { label: 'Posted',   value: date },
      { label: 'Source',   value: job.source_name },
    ].filter(r => r.value);

    card.innerHTML = `
      <div class="jc-header">
        <div class="jc-title">${job.title}</div>
        ${job.company_name ? `<div class="jc-company">${job.company_name}</div>` : ''}
      </div>
      ${meta.length ? `
      <dl class="jc-meta">
        ${meta.map(r => `
          <div class="jc-meta-row">
            <dt>${r.label}</dt>
            <dd>${r.value}</dd>
          </div>`).join('')}
      </dl>` : ''}`;

    card.addEventListener('click', () => goToOjaDetail(job.id));
    container.appendChild(card);
  });
}

// ─── Detail page renderer (called from app.js router) ────────────────────────

async function renderOjaDetailPage(id) {
  showDetailPage(`<div class="page-loading"><div class="loading">Loading...</div></div>`);

  try {
    const res = await fetch(`/api/oja/jobs/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const job = await res.json();

    const backHash = buildHash('oja', 'jobs');
    const date = job.date_posted
      ? new Date(job.date_posted).toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' })
      : null;

    const tagsSection = job.tags?.length
      ? `<section class="dp-section">
           <h2 class="dp-section-title">Skills &amp; Tags</h2>
           <div class="dp-chips">${job.tags.map(t => `<span class="dp-chip">${t}</span>`).join('')}</div>
         </section>`
      : '';

    const descSection = job.description_text
      ? `<section class="dp-section">
           <h2 class="dp-section-title">Description</h2>
           <div class="dp-description">${job.description_text}</div>
         </section>`
      : '<p class="dp-empty">No description available.</p>';

    const leftCol = `
      <div class="dp-col-main">
        ${tagsSection}
        ${descSection}
      </div>`;

    const salary = (job.min_salary || job.max_salary)
      ? `${job.min_salary || ''}${job.min_salary && job.max_salary ? ' – ' : ''}${job.max_salary || ''} ${job.currency || ''}`.trim()
      : null;

    const metaRows = [
      { label: 'Company',  value: job.company_name },
      { label: 'Location', value: job.location },
      { label: 'Type',     value: normalizeEmploymentType(job.employment_type) },
      { label: 'Posted',   value: date },
      { label: 'Source',   value: job.source_name },
      { label: 'Salary',   value: salary },
    ].filter(r => r.value);

    const metaCard = metaRows.length ? `
      <div class="dp-meta-card">
        <h2 class="dp-section-title">Details</h2>
        <dl class="dp-meta-dl">
          ${metaRows.map(r => `<dt>${r.label}</dt><dd>${r.value}</dd>`).join('')}
        </dl>
      </div>` : '';

    const linksCard = job.url ? `
      <div class="dp-links-card">
        <h2 class="dp-section-title">External Links</h2>
        <ul class="dp-link-list">
          <li>
            <a class="dp-ext-link" href="${job.url}" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                   stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              View Original Posting
            </a>
          </li>
        </ul>
      </div>` : '';

    const rightCol = `
      <div class="dp-col-side">
        ${metaCard}
        ${linksCard}
      </div>`;

    showDetailPage(`
      <div class="dp-header">
        <div class="dp-header-row">
          <div>
            <div class="dp-eyebrow">Job Posting</div>
            <h1 class="dp-title">${job.title}</h1>
          </div>
        </div>
      </div>
      <div class="dp-subbar">
        <a class="dp-back" href="${backHash}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
               stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
          </svg>
          Back to Job Postings
        </a>
      </div>
      <div class="dp-body dp-body-cols">
        ${leftCol}
        ${rightCol}
      </div>`);

  } catch (err) {
    showDetailPage(`
      <div class="dp-header">
        <a class="dp-back" href="${buildHash('oja', 'jobs')}">← Back</a>
      </div>
      <div class="dp-body"><p class="dp-empty">Error loading job: ${err.message}</p></div>`);
  }
}
