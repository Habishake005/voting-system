const API_BASE = '/api';

function getToken()  { return localStorage.getItem('token'); }
function getUser()   { return localStorage.getItem('username'); }

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  window.location.href = '/';
}

function requireAuth() {
  if (!getToken()) window.location.href = '/';
}

// ── Tab switching ─────────────────────────────────────────
function switchTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('login-form').classList.toggle('hidden', !isLogin);
  document.getElementById('register-form').classList.toggle('hidden', isLogin);
  document.getElementById('tab-login').classList.toggle('active', isLogin);
  document.getElementById('tab-register').classList.toggle('active', !isLogin);
  hideAllAlerts();
}

function hideAllAlerts() {
  ['login-error','register-error','register-success'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });
}

function showAlert(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
}

// ── Login ─────────────────────────────────────────────────
async function handleLogin() {
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value.trim();

  if (!username || !password) {
    showAlert('login-error', 'Please fill in all fields.');
    return;
  }

  try {
    const res  = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('username', username);
    window.location.href = '/vote.html';
  } catch (err) {
    showAlert('login-error', err.message);
  }
}

// ── Register ──────────────────────────────────────────────
async function handleRegister() {
  const username = document.getElementById('reg-username').value.trim();
  const password = document.getElementById('reg-password').value.trim();
  const confirm  = document.getElementById('reg-confirm').value.trim();

  if (!username || !password || !confirm) {
    showAlert('register-error', 'Please fill in all fields.');
    return;
  }
  if (password !== confirm) {
    showAlert('register-error', 'Passwords do not match.');
    return;
  }
  if (password.length < 4) {
    showAlert('register-error', 'Password must be at least 4 characters.');
    return;
  }

  try {
    const res  = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');

    showAlert('register-success', 'Account created! Switching to login...');
    setTimeout(() => {
      switchTab('login');
      document.getElementById('login-username').value = username;
    }, 1500);
  } catch (err) {
    showAlert('register-error', err.message);
  }
}

// ── Vote page ─────────────────────────────────────────────
let selectedCandidate = null;

async function loadCandidates() {
  requireAuth();
  document.getElementById('nav-user').textContent = getUser();

  try {
    const res  = await fetch(`${API_BASE}/vote/candidates`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    renderCandidates(data.candidates);
    if (data.has_voted) {
      document.getElementById('already-voted').classList.remove('hidden');
      document.getElementById('vote-btn').disabled = true;
    }
  } catch (err) { console.error('Failed to load candidates:', err); }
}

function renderCandidates(candidates) {
  const colors = ['#f59e0b','#6c63ff','#10b981'];
  document.getElementById('candidates').innerHTML = candidates.map((c, i) => `
    <div class="candidate-card" onclick="selectCandidate('${c.id}', this)">
      <input type="radio" name="candidate" value="${c.id}"/>
      <div class="candidate-avatar" style="background:${colors[i] || '#6c63ff'}">
        ${c.name.charAt(0)}
      </div>
      <div class="candidate-info">
        <div class="candidate-name">${c.name}</div>
        <div class="candidate-party">${c.party}</div>
      </div>
    </div>
  `).join('');
}

function selectCandidate(id, el) {
  document.querySelectorAll('.candidate-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  el.querySelector('input').checked = true;
  selectedCandidate = id;
  document.getElementById('vote-btn').disabled = false;
}

async function submitVote() {
  if (!selectedCandidate) return;
  try {
    const res  = await fetch(`${API_BASE}/vote/cast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({ candidate_id: selectedCandidate })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Vote failed');
    alert('Vote cast successfully!');
    window.location.href = '/results.html';
  } catch (err) { alert(err.message); }
}

// ── Results page ──────────────────────────────────────────
async function loadResults() {
  requireAuth();
  try {
    const res  = await fetch(`${API_BASE}/analytics/results`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    renderResults(data);
  } catch (err) { console.error('Failed to load results:', err); }
}

function renderResults(data) {
  const total = data.total_votes || 0;
  document.getElementById('results-container').innerHTML = data.results.map(r => {
    const pct = total > 0 ? Math.round((r.votes / total) * 100) : 0;
    return `
      <div class="result-item">
        <div class="result-header">
          <div class="result-avatar">${r.name.charAt(0)}</div>
          <span class="result-name">${r.name}</span>
          <span class="result-count">${r.votes} votes · ${pct}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width:${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');
  document.getElementById('total-votes').textContent = `Total votes cast: ${total}`;
}

// ── Auto-load ─────────────────────────────────────────────
const page = window.location.pathname;
if (page.includes('vote.html'))    loadCandidates();
if (page.includes('results.html')) { loadResults(); setInterval(loadResults, 5000); }