const API = '';

// ── Token helpers ─────────────────────────────────────────────────────────────
const getToken  = ()  => localStorage.getItem('vitalid_token');
const setToken  = (t) => localStorage.setItem('vitalid_token', t);
const clearToken = () => localStorage.removeItem('vitalid_token');
const authHdr   = ()  => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` });

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, { headers: authHdr(), ...opts });
  if (res.status === 401) { logout(); return null; }
  return res.ok ? res.json() : null;
}

// ── Greeting ──────────────────────────────────────────────────────────────────
function greeting() {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
}

// ── Auth tab switch ───────────────────────────────────────────────────────────
function showTab(tab) {
  document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
  document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
  document.querySelectorAll('.auth-tab').forEach((b, i) =>
    b.classList.toggle('active', (i === 0) === (tab === 'login')));
}

// ── Login ─────────────────────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  const body = new URLSearchParams({
    username: document.getElementById('login-email').value,
    password: document.getElementById('login-password').value,
  });
  const res  = await fetch(`${API}/api/auth/login`, { method: 'POST', body });
  const data = await res.json();
  if (!res.ok) { errEl.textContent = data.detail || 'Login failed'; return; }
  setToken(data.access_token);
  showDashboard(data.name);
}

// ── Register ──────────────────────────────────────────────────────────────────
async function handleRegister(e) {
  e.preventDefault();
  const errEl = document.getElementById('reg-error');
  errEl.textContent = '';
  const body = {
    name:     document.getElementById('reg-name').value,
    email:    document.getElementById('reg-email').value,
    password: document.getElementById('reg-password').value,
    age:      parseInt(document.getElementById('reg-age').value) || null,
  };
  const res  = await fetch(`${API}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { errEl.textContent = data.detail || 'Registration failed'; return; }
  // auto-login
  document.getElementById('login-email').value    = body.email;
  document.getElementById('login-password').value = body.password;
  showTab('login');
  document.getElementById('login-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  clearToken();
  document.getElementById('dashboard').classList.add('hidden');
  document.getElementById('auth-gate').classList.remove('hidden');
}

// ── Show dashboard ────────────────────────────────────────────────────────────
function showDashboard(name) {
  document.getElementById('auth-gate').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('hidden');
  document.getElementById('greeting-text').textContent = greeting();
  document.getElementById('user-name').textContent     = name;
  document.getElementById('user-avatar').textContent   = name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  buildHeatmap();
  loadDashboard();
}

// ── Load all dashboard data ───────────────────────────────────────────────────
async function loadDashboard() {
  const [dash, history] = await Promise.all([
    apiFetch('/api/dashboard/analytics-dashboard'),
    apiFetch('/api/vitals/history?limit=7'),
  ]);
  if (dash)    renderDashboard(dash);
  if (history) renderBpChart(history.slice().reverse());
}

// ── Log vitals ────────────────────────────────────────────────────────────────
async function handleLogVitals(e) {
  e.preventDefault();
  const msg = document.getElementById('vitals-msg');
  const body = {
    systolic_bp:  parseInt(document.getElementById('v-sys').value)     || null,
    diastolic_bp: parseInt(document.getElementById('v-dia').value)     || null,
    blood_glucose:parseFloat(document.getElementById('v-glucose').value)|| null,
    weight:       parseFloat(document.getElementById('v-weight').value) || null,
    height:       parseFloat(document.getElementById('v-height').value) || null,
  };
  const res = await fetch(`${API}/api/vitals/log`, { method: 'POST', headers: authHdr(), body: JSON.stringify(body) });
  if (res.ok) {
    msg.textContent  = '✓ Vitals saved — refreshing dashboard...';
    msg.style.color  = '#1A9E98';
    document.getElementById('vitals-form').reset();
    setTimeout(() => { msg.textContent = ''; loadDashboard(); }, 1200);
  } else {
    msg.textContent = 'Failed to save vitals';
    msg.style.color = '#e57373';
  }
}

// ── Upload blood report ───────────────────────────────────────────────────────
async function handleReportUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const msg = document.getElementById('report-msg');
  msg.textContent  = 'Uploading and parsing report...';
  msg.style.color  = '#7ECCC7';

  const form = new FormData();
  form.append('file', file);

  const res  = await fetch(`${API}/api/reports/upload`, { method: 'POST', headers: { Authorization: `Bearer ${getToken()}` }, body: form });
  const data = await res.json();

  if (!res.ok) {
    msg.textContent = data.detail || 'Upload failed';
    msg.style.color = '#e57373';
    return;
  }

  msg.textContent = `✓ ${data.message}`;
  msg.style.color = '#1A9E98';
  renderReportValues(data.parsed_values);
  setTimeout(() => loadDashboard(), 800); // refresh tasks + preventive care
}

// ── Render report values ──────────────────────────────────────────────────────
function renderReportValues(vals) {
  const el = document.getElementById('report-values');
  if (!vals || !Object.keys(vals).length) return;
  const labels = { hemoglobin: 'Hemoglobin', platelets: 'Platelets', wbc: 'WBC', total_cholesterol: 'Cholesterol', ldl: 'LDL', hdl: 'HDL', triglycerides: 'Triglycerides', creatinine: 'Creatinine', hba1c: 'HbA1c', tsh: 'TSH', vitamin_d: 'Vit D', vitamin_b12: 'Vit B12' };
  el.innerHTML = Object.entries(vals)
    .filter(([k]) => labels[k])
    .map(([k, v]) => `<span class="report-chip"><span class="report-chip-label">${labels[k]}</span><span class="report-chip-val">${v}</span></span>`)
    .join('');
  el.classList.remove('hidden');
}

// ── Render full dashboard ─────────────────────────────────────────────────────
function renderDashboard(data) {
  const vitals    = data.latest_vitals || {};
  const preventive = data.preventive_care || {};
  const tasks     = data.daily_tasks || [];
  const chart     = data.chart_data  || [];
  const report    = data.blood_report || {};
  const bmi       = data.bmi;

  // Header score & badge
  const risk = preventive.overall_future_risk || {};
  const score = risk.level === 'low' ? 85 : risk.level === 'moderate' ? 65 : 40;
  setDonut(score);
  document.getElementById('score-num').textContent = score;
  document.getElementById('header-sub').textContent = risk.message || 'Log vitals to see your health index';
  const badge = document.getElementById('risk-badge');
  badge.textContent  = risk.level ? (risk.level.charAt(0).toUpperCase() + risk.level.slice(1)) + ' future risk' : '—';
  badge.className    = 'attention-badge risk-' + (risk.level || 'low');

  // Vitals strip
  renderVitalsStrip(vitals);

  // Preventive care cards
  renderPreventive(preventive.predictions || []);

  // BP chart
  if (chart.length >= 2) renderBpChart(chart);

  // BP insight
  const bpTrend = (data.vitals_trend || {}).bp || {};
  const sys = (bpTrend.systolic || {});
  if (sys.trend && !sys.error) {
    const vel = Math.abs(sys.velocity || 0).toFixed(1);
    document.getElementById('bp-insight').textContent =
      sys.trend === 'increasing' ? `↑ Systolic trending up (${vel} pts/reading) — reduce salt intake`
      : sys.trend === 'decreasing' ? `↓ Systolic trending down — keep it up`
      : '→ BP is stable over this period';
  }

  // Body metrics
  renderMetrics(vitals, bmi, report);

  // Tasks
  renderTasks(tasks);
}

// ── Donut ring ────────────────────────────────────────────────────────────────
function setDonut(score) {
  const circumference = 188.5;
  const filled = (score / 100) * circumference;
  const arc = document.getElementById('donut-arc');
  arc.setAttribute('stroke-dasharray', `${filled} ${circumference}`);
}

// ── Vitals strip ──────────────────────────────────────────────────────────────
function renderVitalsStrip(v) {
  const strip = document.getElementById('vitals-strip');
  const bp    = v.systolic_bp ? `${v.systolic_bp}/${v.diastolic_bp}` : '—';
  const bpWatch = v.systolic_bp > 130;
  const gWatch  = v.blood_glucose > 100;

  strip.innerHTML = [
    { svg: heartSVG(), num: bp,                    unit: 'mmHg',  name: 'Blood Pressure', watch: bpWatch },
    { svg: dropSVG(),  num: v.blood_glucose || '—', unit: 'mg/dL', name: 'Blood Sugar',    watch: gWatch  },
    { svg: scaleSVG(), num: v.weight ? `${v.weight} kg` : '—', unit: 'kg', name: 'Weight', watch: false },
  ].map(i => `
    <div class="vital-card">
      ${i.svg}
      <span class="vital-num">${i.num}</span>
      <span class="vital-unit">${i.unit}</span>
      <span class="vital-name">${i.name}</span>
      <span class="vital-tag ${i.watch ? 'tag-watch' : 'tag-normal'}">${i.watch ? 'Watch' : 'Normal'}</span>
    </div>`).join('');
}

// ── Future preventive care cards ──────────────────────────────────────────────
function renderPreventive(predictions) {
  const el = document.getElementById('preventive-section');
  if (!predictions.length) {
    el.innerHTML = `
      <div class="preventive-empty">
        <span style="font-size:28px">✓</span>
        <p>No future risks detected based on current data.</p>
        <p style="font-size:11px;color:#7ECCC7;margin-top:4px">Keep logging vitals to get personalised predictions.</p>
      </div>`;
    return;
  }

  el.innerHTML = predictions.map((p, idx) => `
    <div class="preventive-card" onclick="togglePrecautions(${idx})">
      <div class="preventive-header">
        <div class="preventive-left">
          <span class="preventive-score score-${scoreClass(p.urgency_score)}">${p.urgency_score}</span>
          <div>
            <p class="preventive-condition">${p.future_condition}</p>
            <p class="preventive-timeframe">Risk window: ${p.timeframe}</p>
          </div>
        </div>
        <span class="preventive-chevron" id="chev-${idx}">›</span>
      </div>
      <p class="preventive-signal">${p.current_signal}</p>
      <p class="preventive-future">${p.future_risk}</p>
      <div class="preventive-precautions hidden" id="prec-${idx}">
        <p class="prec-title">Precautions to take now:</p>
        <ul class="prec-list">
          ${p.precautions.map(pr => `<li>${pr}</li>`).join('')}
        </ul>
        <p class="prec-why">Why this matters: ${p.why_this_matters}</p>
      </div>
    </div>`).join('');
}

function togglePrecautions(idx) {
  const el   = document.getElementById(`prec-${idx}`);
  const chev = document.getElementById(`chev-${idx}`);
  const open = !el.classList.contains('hidden');
  el.classList.toggle('hidden', open);
  chev.textContent = open ? '›' : '⌄';
}

function scoreClass(score) {
  if (score >= 80) return 'critical';
  if (score >= 60) return 'high';
  if (score >= 40) return 'moderate';
  return 'low';
}

// ── BP chart ──────────────────────────────────────────────────────────────────
function renderBpChart(readings) {
  if (!readings || readings.length < 2) return;
  const xs = [30, 77.5, 125, 172.5, 220, 267.5, 315];
  const toY = val => Math.max(5, Math.min(125, 20 + (135 - val) / 30 * 100));

  const pts = readings.slice(0, 7);
  const sysPoints = pts.map((r, i) => r.systolic  ? `${xs[i]},${toY(r.systolic).toFixed(1)}`  : null).filter(Boolean).join(' ');
  const diaPoints = pts.map((r, i) => r.diastolic ? `${xs[i]},${toY(r.diastolic).toFixed(1)}` : null).filter(Boolean).join(' ');

  document.getElementById('sys-line').setAttribute('points', sysPoints);
  document.getElementById('dia-line').setAttribute('points', diaPoints);

  const dots = document.getElementById('chart-dots');
  dots.innerHTML = pts.map((r, i) => r.systolic
    ? `<circle cx="${xs[i]}" cy="${toY(r.systolic).toFixed(1)}" r="4" fill="white" stroke="#26C6BF" stroke-width="1.5"/>`
    : '').join('');

  pts.forEach((r, i) => {
    const el = document.getElementById(`xl${i}`);
    if (el) el.textContent = r.date || '';
  });
}

// ── Body metrics ──────────────────────────────────────────────────────────────
function renderMetrics(v, bmi, report) {
  const strip = document.getElementById('metrics-strip');
  const items = [];

  if (bmi) {
    const bmiLabel = bmi < 18.5 ? 'Underweight' : bmi < 25 ? 'Healthy' : bmi < 30 ? 'Overweight' : 'Obese';
    const bmiWarn  = bmi >= 25;
    items.push({ icon: '📋', val: bmi, label: `BMI · ${bmiLabel}`, warn: bmiWarn });
  }
  if (v.weight) items.push({ icon: '⚖️', val: `${v.weight} kg`, label: 'Weight', warn: false });

  // From blood report
  if (report.platelets) {
    const low = report.platelets < 1.5;
    items.push({ icon: '🩸', val: `${report.platelets}L`, label: `Platelets${low ? ' · Low' : ''}`, warn: low });
  }
  if (report.hemoglobin) {
    const low = report.hemoglobin < 12;
    items.push({ icon: '💉', val: `${report.hemoglobin}`, label: `Hb g/dL${low ? ' · Low' : ''}`, warn: low });
  }
  if (report.total_cholesterol) {
    const high = report.total_cholesterol > 200;
    items.push({ icon: '🫀', val: report.total_cholesterol, label: `Cholesterol${high ? ' · High' : ''}`, warn: high });
  }

  if (!items.length) {
    strip.innerHTML = '<span style="font-size:12px;color:#7ECCC7;padding:8px 0">Log vitals and upload a report to see metrics</span>';
    return;
  }

  strip.innerHTML = items.map(i => `
    <div class="metric-pill ${i.warn ? 'metric-warn' : ''}">
      <span>${i.icon}</span>
      <span class="metric-val">${i.val}</span>
      <span class="metric-label">${i.label}</span>
    </div>`).join('');
}

// ── Daily tasks ───────────────────────────────────────────────────────────────
function renderTasks(tasks) {
  const el = document.getElementById('tasks-list');
  if (!tasks.length) {
    el.innerHTML = '<p style="font-size:12px;color:#7ECCC7">Log your vitals to generate today\'s tasks</p>';
    return;
  }
  const priorityIcon = { urgent: '🚨', high: '🔴', medium: '🟡', low: '🟢' };
  el.innerHTML = tasks.map((t, i) => `
    <div class="task-item" id="task-${i}">
      <div class="task-left">
        <span class="task-icon">${priorityIcon[t.priority] || '🟢'}</span>
        <div class="task-text">
          <p class="task-title">${t.title}</p>
          <p class="task-desc">${t.description}</p>
          <span class="task-meta">${t.category} · ${t.duration_min ? t.duration_min + ' min' : 'ongoing'}</span>
        </div>
      </div>
      <div class="task-right">
        <span class="coin-chip">+${t.points} pts</span>
        <input type="checkbox" class="task-check" onchange="completeTask(${i}, this)" />
      </div>
    </div>`).join('');
}

function completeTask(idx, cb) {
  const el = document.getElementById(`task-${idx}`);
  if (cb.checked) el.classList.add('task-done');
  else el.classList.remove('task-done');
}

// ── Heatmap ───────────────────────────────────────────────────────────────────
function buildHeatmap() {
  const data = [0,25,100,75,50,25,0, 50,75,100,100,75,50,25, 25,50,75,100,50,75,100, 75,100,50,25,75,50,25];
  const color = v => v === 0 ? '#F2FDFB' : v <= 25 ? '#C8F0EC' : v <= 50 ? '#7ECCC7' : v <= 75 ? '#26C6BF' : '#1A3A38';
  const grid  = document.getElementById('heatmap');
  grid.innerHTML = '';
  const today = new Date();
  data.forEach((val, i) => {
    const cell = document.createElement('div');
    cell.className    = 'hm-cell';
    cell.style.background = color(val);
    const d = new Date(today);
    d.setDate(today.getDate() - (27 - i));
    cell.title = `${d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}: ${val}% complete`;
    grid.appendChild(cell);
  });
}

// ── SVG icons ─────────────────────────────────────────────────────────────────
const heartSVG = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 21C12 21 3 13.5 3 8a5 5 0 0 1 9-3 5 5 0 0 1 9 3c0 5.5-9 13-9 13z" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/></svg>`;
const dropSVG  = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="5" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/><path d="M2 12h3M19 12h3M12 2v3M12 19v3" stroke="#26C6BF" stroke-width="1.8" stroke-linecap="round"/></svg>`;
const scaleSVG = () => `<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><rect x="3" y="12" width="18" height="8" rx="2" stroke="#26C6BF" stroke-width="1.8" fill="#E0F7F4"/><path d="M8 12V8a4 4 0 0 1 8 0v4" stroke="#26C6BF" stroke-width="1.8"/></svg>`;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (getToken()) {
    apiFetch('/api/auth/me').then(user => {
      if (user) showDashboard(user.name);
    });
  }
});
