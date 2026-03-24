const API = 'http://127.0.0.1:8000';

// ── Auth helpers ──────────────────────────────────────────────────────────────
const getToken = () => localStorage.getItem('vitalid_token');
const setToken = (t) => localStorage.setItem('vitalid_token', t);
const clearToken = () => localStorage.removeItem('vitalid_token');

const authHeaders = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` });

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, { headers: authHeaders(), ...opts });
  if (res.status === 401) { logout(); return null; }
  return res.ok ? res.json() : null;
}

// ── Tab switching ─────────────────────────────────────────────────────────────
function showTab(tab) {
  document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
  document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
  document.querySelectorAll('.auth-tab').forEach((b, i) => b.classList.toggle('active', (i === 0) === (tab === 'login')));
}

// ── Auth handlers ─────────────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API}/api/auth/login`, { method: 'POST', body: form });
  const data = await res.json();

  if (!res.ok) { document.getElementById('login-error').textContent = data.detail || 'Login failed'; return; }
  setToken(data.access_token);
  showDashboard(data.name);
}

async function handleRegister(e) {
  e.preventDefault();
  const body = {
    name: document.getElementById('reg-name').value,
    email: document.getElementById('reg-email').value,
    password: document.getElementById('reg-password').value,
    age: parseInt(document.getElementById('reg-age').value) || null,
  };
  const res = await fetch(`${API}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { document.getElementById('reg-error').textContent = data.detail || 'Registration failed'; return; }
  // Auto-login after register
  document.getElementById('login-email').value = body.email;
  document.getElementById('login-password').value = body.password;
  showTab('login');
  document.getElementById('login-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
}

function logout() {
  clearToken();
  document.getElementById('dashboard').classList.add('hidden');
  document.getElementById('auth-gate').classList.remove('hidden');
}

// ── Dashboard init ────────────────────────────────────────────────────────────
function showDashboard(name) {
  document.getElementById('auth-gate').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('hidden');
  const initials = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  document.getElementById('user-name').textContent = name;
  document.getElementById('user-avatar').textContent = initials;
  loadAll();
}

async function loadAll() {
  const [dashboard, history] = await Promise.all([
    apiFetch('/api/dashboard/analytics-dashboard'),
    apiFetch('/api/vitals/history?limit=7'),
  ]);
  if (dashboard) renderDashboard(dashboard);
  if (history && history.length) renderVitalsStrip(history[0]);
  if (history && history.length >= 2) renderBpChart(history.slice(0, 7).reverse());
  buildHeatmap();
}

// ── Vitals log form ───────────────────────────────────────────────────────────
async function handleLogVitals(e) {
  e.preventDefault();
  const msg = document.getElementById('vitals-msg');
  const body = {
    systolic_bp: parseInt(document.getElementById('v-sys').value) || null,
    diastolic_bp: parseInt(document.getElementById('v-dia').value) || null,
    blood_glucose: parseFloat(document.getElementById('v-glucose').value) || null,
    pulse: parseInt(document.getElementById('v-pulse').value) || null,
    weight: parseFloat(document.getElementById('v-weight').value) || null,
  };
  const res = await fetch(`${API}/api/vitals/log`, { method: 'POST', headers: authHeaders(), body: JSON.stringify(body) });
  if (res.ok) {
    msg.textContent = '✓ Vitals saved';
    msg.style.color = '#1A9E98';
    document.getElementById('vitals-form').reset();
    setTimeout(() => { msg.textContent = ''; loadAll(); }, 1500);
  } else {
    msg.textContent = 'Failed to save';
    msg.style.color = '#e57373';
  }
}

// ── Renderers ─────────────────────────────────────────────────────────────────
function renderDashboard(data) {
  // Header
  const status = data.body_status || {};
  document.getElementById('body-headline').textContent = status.headline || 'No data yet';
  const badge = document.getElementById('body-status-badge');
  badge.textContent = status.status || '—';
  badge.className = 'attention-badge status-' + (status.status || 'stable');

  // Score from risk
  const risk = data.health_risk || {};
  if (!risk.error) {
    const score = Math.round((1 - (risk.risk_score || 0)) * 100);
    document.getElementById('score-num').textContent = score;
  }

  // Risk forecast section
  renderRiskSection(data.body_status);

  // Diet
  renderDiet(data.diet_recommendations);

  // Tasks
  renderTasks(data.daily_tasks || []);

  // BP insight
  const bpTrend = data.vitals_trends?.bp?.systolic;
  if (bpTrend && !bpTrend.error) {
    const dir = bpTrend.trend;
    const vel = Math.abs(bpTrend.velocity).toFixed(1);
    document.getElementById('bp-insight').textContent =
      dir === 'increasing'
        ? `↑ Systolic trending up (${vel} pts/reading) — try reducing salt intake`
        : dir === 'decreasing'
        ? `↓ Systolic trending down — keep up the good work`
        : `→ BP is stable over the last period`;
  }

  // Metrics strip
  renderMetrics(data);
}

function renderVitalsStrip(latest) {
  const strip = document.getElementById('vitals-strip');
  if (!latest) return;
  const items = [
    { icon: heartSVG(), num: latest.systolic_bp ? `${latest.systolic_bp}/${latest.diastolic_bp}` : '—', unit: 'mmHg', name: 'Blood Pressure', tag: latest.systolic_bp > 130 ? 'Watch' : 'Normal', watch: latest.systolic_bp > 130 },
    { icon: dropSVG(), num: latest.blood_glucose ? `${latest.blood_glucose}` : '—', unit: 'mg/dL', name: 'Blood Sugar', tag: latest.blood_glucose > 100 ? 'Watch' : 'Normal', watch: latest.blood_glucose > 100 },
    { icon: waveSVG(), num: latest.pulse ? `${latest.pulse}` : '—', unit: 'bpm', name: 'Heart Rate', tag: 'Normal', watch: false },
    { icon: lungSVG(), num: '97%', unit: 'SpO2', name: 'Oxygen Sat.', tag: 'Normal', watch: false },
  ];
  strip.innerHTML = items.map(i => `
    <div class="vital-card">
      ${i.icon}
      <span class="vital-num">${i.num}</span>
      <span class="vital-unit">${i.unit}</span>
      <span class="vital-name">${i.name}</span>
      <span class="vital-tag ${i.watch ? 'tag-watch' : 'tag-normal'}">${i.tag}</span>
    </div>`).join('');
}

function renderRiskSection(bodyStatus) {
  const el = document.getElementById('risk-section');
  if (!bodyStatus || !bodyStatus.alerts || bodyStatus.alerts.length === 0) {
    el.innerHTML = `<p style="color:#7ECCC7;font-size:13px;text-align:center;padding:12px 0">All vitals look good — keep it up</p>`;
    return;
  }
  const riskMap = { low: 20, medium: 45, high: 65, critical: 85 };
  el.innerHTML = bodyStatus.alerts.map(a => {
    const pct = riskMap[a.severity] || 30;
    return `
    <div class="risk-item">
      <div class="risk-header">
        <span class="risk-name">${a.category || a.type}</span>
        <span class="risk-pct">${pct}%</span>
      </div>
      <p class="risk-insight">${a.message}</p>
      <div class="progress-track"><div class="progress-fill" data-width="${pct}" style="width:0%"></div></div>
      <span class="action-chip">→ ${a.action}</span>
    </div>`;
  }).join('');
  // Animate bars
  requestAnimationFrame(() => {
    el.querySelectorAll('.progress-fill').forEach(b => {
      setTimeout(() => { b.style.width = b.dataset.width + '%'; }, 100);
    });
  });
}

function renderBpChart(readings) {
  if (!readings || readings.length < 2) return;
  const xs = [30, 77.5, 125, 172.5, 220, 267.5, 315];
  const sysData = readings.map(r => r.systolic_bp).filter(Boolean);
  const diaData = readings.map(r => r.diastolic_bp).filter(Boolean);
  if (!sysData.length) return;

  const toY = val => 20 + (135 - val) / 30 * 100;

  const sysPoints = sysData.slice(0, 7).map((v, i) => `${xs[i]},${toY(v).toFixed(1)}`).join(' ');
  const diaPoints = diaData.slice(0, 7).map((v, i) => `${xs[i]},${toY(v).toFixed(1)}`).join(' ');

  document.getElementById('sys-line').setAttribute('points', sysPoints);
  document.getElementById('dia-line').setAttribute('points', diaPoints);

  const dots = document.getElementById('chart-dots');
  dots.innerHTML = sysData.slice(0, 7).map((v, i) =>
    `<circle cx="${xs[i]}" cy="${toY(v).toFixed(1)}" r="4" fill="white" stroke="#26C6BF" stroke-width="1.5"/>`
  ).join('');
}

function renderMetrics(data) {
  const strip = document.getElementById('metrics-strip');
  const latest = data._latest || {};
  const items = [
    { icon: '📋', val: '24.8', label: 'BMI · Healthy' },
    { icon: '⚖️', val: latest.weight ? `${latest.weight} kg` : '— kg', label: 'Weight' },
    { icon: '😴', val: '6.2 hrs', label: 'Sleep · Low' },
    { icon: '⚡', val: '6/10', label: 'Stress · Manage' },
    { icon: '🏃', val: 'Low', label: 'Activity · Increase' },
  ];
  strip.innerHTML = items.map(i => `
    <div class="metric-pill">
      <span>${i.icon}</span>
      <span class="metric-val">${i.val}</span>
      <span class="metric-label">${i.label}</span>
    </div>`).join('');
}

function renderDiet(recs) {
  const strip = document.getElementById('diet-strip');
  if (!recs) { strip.innerHTML = ''; return; }

  const increase = (recs.foods_to_increase || []).slice(0, 3);
  const avoid = (recs.foods_to_avoid || []).slice(0, 3);

  const cards = [
    { tag: 'Eat more', tagClass: 'diet-tag-solid', title: 'Recommended foods', items: increase.length ? increase : ['Potassium foods', 'Whole grains', 'Leafy greens'], footer: 'Based on your vitals' },
    { tag: 'Reduce', tagClass: 'diet-tag-light', title: 'Limit these', items: avoid.length ? avoid : ['High sodium foods', 'Refined sugars', 'Packaged snacks'], footer: 'Raises BP & glucose' },
    { tag: 'Habit', tagClass: 'diet-tag-outline', title: 'Hydration goal', items: [`${recs.hydration || '2–3 litres water daily'}`], footer: 'Flushes excess sodium' },
  ];

  strip.innerHTML = cards.map(c => `
    <div class="diet-card">
      <span class="diet-tag ${c.tagClass}">${c.tag}</span>
      <p class="diet-card-title">${c.title}</p>
      <ul class="diet-items">${c.items.map(i => `<li>${i}</li>`).join('')}</ul>
      <p class="diet-footer">${c.footer}</p>
    </div>`).join('');
}

function renderTasks(tasksData) {
  const tasks = Array.isArray(tasksData) ? tasksData : (tasksData.tasks || []);
  const el = document.getElementById('tasks-timeline');
  if (!tasks.length) { el.innerHTML = '<p style="color:#7ECCC7;font-size:13px">No tasks generated yet — log your vitals first</p>'; return; }

  el.innerHTML = tasks.slice(0, 5).map((t, i) => `
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      ${i < tasks.length - 1 ? '<div class="timeline-line"></div>' : ''}
      <div class="timeline-content">
        <div class="timeline-row">
          <span class="timeline-title">${t.title}</span>
          <span class="coin-chip">+${t.points} pts</span>
        </div>
        <span class="timeline-when">${t.category} · ${t.estimated_duration ? t.estimated_duration + ' min' : 'ongoing'}</span>
      </div>
    </div>`).join('');
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
function buildHeatmap() {
  const data = [0,25,100,75,50,25,0, 50,75,100,100,75,50,25, 25,50,75,100,50,75,100, 75,100,50,25,75,50,25];
  const colorMap = v => v === 0 ? '#F2FDFB' : v <= 25 ? '#C8F0EC' : v <= 50 ? '#7ECCC7' : v <= 75 ? '#26C6BF' : '#1A3A38';
  const grid = document.getElementById('heatmap');
  grid.innerHTML = '';
  const today = new Date();
  data.forEach((val, i) => {
    const cell = document.createElement('div');
    cell.className = 'hm-cell';
    cell.style.background = colorMap(val);
    const d = new Date(today); d.setDate(today.getDate() - (27 - i));
    cell.title = `${d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}: ${val}% complete`;
    grid.appendChild(cell);
  });
}

// ── Inline SVG icons ──────────────────────────────────────────────────────────
const heartSVG = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 21C12 21 3 13.5 3 8a5 5 0 0 1 9-3 5 5 0 0 1 9 3c0 5.5-9 13-9 13z" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/></svg>`;
const dropSVG  = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="5" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/><path d="M2 12h3M19 12h3M12 2v3M12 19v3" stroke="#26C6BF" stroke-width="1.8" stroke-linecap="round"/></svg>`;
const waveSVG  = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M3 12 Q6 6 9 12 Q12 18 15 12 Q18 6 21 12" stroke="#26C6BF" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>`;
const lungSVG  = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><ellipse cx="8" cy="13" rx="4" ry="6" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/><ellipse cx="16" cy="13" rx="4" ry="6" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/><path d="M8 7 Q12 4 16 7" stroke="#26C6BF" stroke-width="1.8" fill="none"/></svg>`;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (getToken()) {
    apiFetch('/api/auth/me').then(user => {
      if (user) showDashboard(user.name);
    });
  }
});
