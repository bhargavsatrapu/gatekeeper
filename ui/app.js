const byId = (id) => document.getElementById(id);

async function startRun() {
  const baseUrl = byId('baseUrl').value.trim();
  const swaggerPath = byId('swaggerPath').value.trim();
  const payload = {};
  if (baseUrl) payload.base_url = baseUrl;
  if (swaggerPath) payload.swagger_file_path = swaggerPath;

  const res = await fetch('/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  byId('startResult').textContent = JSON.stringify(data, null, 2);
  if (data.run_id) byId('runId').value = data.run_id;
}

async function refreshStatus() {
  const runId = byId('runId').value.trim();
  if (!runId) return;
  const res = await fetch(`/runs/${runId}/status`);
  const data = await res.json();
  byId('status').textContent = JSON.stringify(data, null, 2);
}

async function loadLogs() {
  const runId = byId('runId').value.trim();
  if (!runId) return;
  const res = await fetch(`/runs/${runId}/logs`);
  const data = await res.json();
  byId('logs').textContent = JSON.stringify(data, null, 2);
}

async function loadResults() {
  const runId = byId('runId').value.trim();
  if (!runId) return;
  const res = await fetch(`/runs/${runId}/results`);
  const data = await res.json();
  byId('results').textContent = JSON.stringify(data, null, 2);
}

async function generateReport() {
  const btn = byId('generateReport');
  btn.disabled = true;
  try {
    const res = await fetch('/report/generate', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      byId('report').textContent = JSON.stringify({ error: 'Report failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const stamp = new Date().toISOString();
    const header = { generated_at: stamp };
    byId('report').textContent = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
  } finally {
    btn.disabled = false;
  }
}

async function uploadSwagger() {
  const input = byId('swaggerFile');
  if (!input.files || !input.files[0]) return;
  const fd = new FormData();
  fd.append('file', input.files[0]);
  const res = await fetch('/swagger/upload', { method: 'POST', body: fd });
  if (!res.ok) {
    const text = await res.text();
    byId('uploadInfo').textContent = JSON.stringify({ error: 'Upload failed', status: res.status, body: text }, null, 2);
    return;
  }
  const data = await res.json();
  byId('uploadInfo').textContent = JSON.stringify(data, null, 2);
  // Auto-refresh preview so endpoints reflect newly uploaded swagger
  await previewEndpoints();
}

async function previewEndpoints() {
  const btn = byId('previewEndpoints');
  const loading = byId('previewLoading');
  btn.disabled = true; loading.style.display = 'inline-flex';
  try {
    const res = await fetch('/endpoints/preview');
    if (!res.ok) {
      const text = await res.text();
      byId('endpointsPreview').textContent = JSON.stringify({ error: 'Preview failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    byId('endpointsPreview').textContent = JSON.stringify(data, null, 2);
  } finally {
    btn.disabled = false; loading.style.display = 'none';
  }
}

async function generateTestcases() {
  const btn = byId('generateTestcases');
  const loading = byId('genLoading');
  btn.disabled = true; loading.style.display = 'inline-flex';
  try {
    const res = await fetch('/testcases/generate', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      byId('testcasesPreview').textContent = JSON.stringify({ error: 'Generate failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const total = Object.values(data.mapping || {}).reduce((acc, arr) => acc + arr.length, 0);
    const header = { generated_total: total, total_endpoints: data.total_endpoints };
    const prev = byId('testcasesPreview').textContent;
    const stamp = new Date().toISOString();
    const block = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
    byId('testcasesPreview').textContent = (prev ? prev + "\n\n" : "") + `=== Generate @ ${stamp} ===\n` + block;
    byId('genCount').textContent = String(total);
  } finally {
    btn.disabled = false; loading.style.display = 'none';
  }
}

async function extractSwagger() {
  const btn = byId('extractSwagger');
  btn.disabled = true;
  try {
    const res = await fetch('/swagger/extract', { method: 'POST' });
    const data = await res.json();
    const prev = byId('uploadInfo').textContent;
    const stamp = new Date().toISOString();
    const msg = `=== Extracted @ ${stamp} ===\n` + JSON.stringify(data, null, 2);
    byId('uploadInfo').textContent = (prev ? prev + "\n\n" : "") + msg;
    // Auto-refresh endpoints preview so UI reflects DB contents right after extract
    await previewEndpoints();
  } finally {
    btn.disabled = false;
  }
}

async function persistTestcases() {
  const btn = byId('persistTestcases');
  btn.disabled = true;
  try {
    const res = await fetch('/testcases/persist', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      const prev = byId('testcasesPreview').textContent;
      byId('testcasesPreview').textContent = (prev ? prev + "\n\n" : "") + JSON.stringify({ error: 'Persist failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const prev = byId('testcasesPreview').textContent;
    const stamp = new Date().toISOString();
    const msg = `=== Persisted @ ${stamp} ===\n` + JSON.stringify(data, null, 2);
    byId('testcasesPreview').textContent = (prev ? prev + "\n\n" : "") + msg;
  } finally {
    btn.disabled = false;
  }
}

async function openAllureReport(type) {
  try {
    const endpoint = type === 'positive' ? '/allure/report/positive' : '/allure/report/all';
    const res = await fetch(endpoint);
    const data = await res.json();
    
    if (res.ok) {
      // Start Allure live server with specific results directory
      await startAllureServer(data.results_dir);
      
      // Open Allure report in new tab
      const allureUrl = `http://localhost:8080`;
      window.open(allureUrl, '_blank');
      
      alert(`Allure report server started!\n\nReport is now available at: http://localhost:8080\n\nThis will auto-refresh as new tests run.`);
    } else {
      alert(`Error: ${data.detail}`);
    }
  } catch (e) {
    alert(`Error opening Allure report: ${e.message}`);
  }
}

async function startAllureServer(resultsDir = 'allure-results') {
  try {
    const res = await fetch('/allure/serve', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results_dir: resultsDir })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to start Allure server');
    }
    return data;
  } catch (e) {
    console.error('Failed to start Allure server:', e);
    throw e;
  }
}

async function executeAll() {
  const btn = byId('executeAll');
  const loading = byId('execAllLoading');
  btn.disabled = true; loading.style.display = 'inline-flex';
  try {
    const res = await fetch('/execute/all', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      byId('executeAllResults').textContent = JSON.stringify({ error: 'Execute all failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const header = {
      generated_total: data.generated_total,
      executed_total: data.executed,
      passed_tests: data.summary?.passed_tests,
      failed_tests: data.summary?.failed_tests
    };
    const prev = byId('executeAllResults').textContent;
    const stamp = new Date().toISOString();
    const block = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
    byId('executeAllResults').textContent = (prev ? prev + "\n\n" : "") + `=== Execute All @ ${stamp} ===\n` + block;
    if (typeof data.generated_total === 'number') byId('genCountExec').textContent = String(data.generated_total);
    if (typeof data.executed === 'number') byId('execCount').textContent = String(data.executed);
    if (typeof data.summary?.passed_tests === 'number') byId('allPassCount').textContent = String(data.summary.passed_tests);
    if (typeof data.summary?.failed_tests === 'number') byId('allFailCount').textContent = String(data.summary.failed_tests);
  } finally {
    btn.disabled = false; loading.style.display = 'none';
  }
}

async function executePositive() {
  const btn = byId('executePositive');
  const loading = byId('execPositiveLoading');
  btn.disabled = true; loading.style.display = 'inline';
  try {
    const res = await fetch('/execute/positive', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      byId('executePositiveResults').textContent = JSON.stringify({ error: 'Execute positive failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const header = {
      generated_total: data.generated_total,
      executed_total: data.executed,
      passed_tests: data.summary?.passed_tests,
      failed_tests: data.summary?.failed_tests
    };
    const prev = byId('executePositiveResults').textContent;
    const stamp = new Date().toISOString();
    const block = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
    byId('executePositiveResults').textContent = (prev ? prev + "\n\n" : "") + `=== Execute Positive @ ${stamp} ===\n` + block;
    if (typeof data.positive_executed === 'number') byId('posExecCount').textContent = String(data.positive_executed);
    if (typeof data.summary?.passed_tests === 'number') byId('posPassCount').textContent = String(data.summary.passed_tests);
    if (typeof data.summary?.failed_tests === 'number') byId('posFailCount').textContent = String(data.summary.failed_tests);
  } finally {
    btn.disabled = false; loading.style.display = 'none';
  }
}

function renderTestCard(containerId, evt) {
  const c = byId(containerId);
  const wrap = document.createElement('div');
  
  // Determine status and styling
  let statusClass = 'running';
  let statusTag = '<span class="tag running">RUNNING</span>';
  
  if (evt.success !== undefined) {
    statusClass = evt.success ? 'pass' : 'fail';
    statusTag = `<span class="tag ${statusClass}">${evt.success ? 'PASS' : 'FAIL'}</span>`;
  }
  
  wrap.className = `card-item ${statusClass}`;
  
  const req = evt.request || {};
  const resp = evt.response || {};
  const body = typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data, null, 2);
  
  // Format request/response data for better readability
  const formatJson = (obj) => {
    if (!obj || Object.keys(obj).length === 0) return 'N/A';
    return JSON.stringify(obj, null, 2);
  };
  
  wrap.innerHTML = `
    <div class="title">
      <span class="test-number">#${evt.seq}</span>
      <span class="test-name">${evt.name || '(unnamed)'}</span>
      <span class="test-method">${evt.method || 'GET'}</span>
      ${statusTag}
    </div>
    <div class="test-url">${evt.url || ''}</div>
    <div class="kv">
      <div>Description</div><div>${evt.description || 'No description available'}</div>
      <div>Expected Status</div><div>${evt.expected_status || 'N/A'}</div>
      <div>Actual Status</div><div>${resp.status_code || 'Pending...'}</div>
      <div>Headers</div><div><pre>${formatJson(req.headers)}</pre></div>
      <div>Request Body</div><div><pre>${formatJson(req.payload)}</pre></div>
      <div>Response Body</div><div><pre>${body || 'No response yet...'}</pre></div>
    </div>
  `;
  
  // Insert new test case at the top (most recent first)
  c.insertBefore(wrap, c.firstChild);
  
  // Update console header stats
  updateConsoleStats(containerId);
  
  // Auto-scroll to top to show the newest test (since we use column-reverse)
  c.scrollTop = 0;
  
  // Add smooth animation for new cards
  wrap.style.opacity = '0';
  wrap.style.transform = 'translateY(-10px)';
  setTimeout(() => {
    wrap.style.transition = 'all 0.3s ease';
    wrap.style.opacity = '1';
    wrap.style.transform = 'translateY(0)';
  }, 50);
}

function updateConsoleStats(containerId) {
  const c = byId(containerId);
  const cards = c.querySelectorAll('.card-item');
  let passed = 0, failed = 0, running = 0;
  
  cards.forEach(card => {
    if (card.classList.contains('pass')) passed++;
    else if (card.classList.contains('fail')) failed++;
    else if (card.classList.contains('running')) running++;
  });
  
  // Update or create console header
  let header = c.querySelector('.console-header');
  if (!header) {
    header = document.createElement('div');
    header.className = 'console-header';
    c.insertBefore(header, c.firstChild);
  }
  
  const total = passed + failed + running;
  const progress = total > 0 ? ((passed + failed) / total) * 100 : 0;
  
  header.innerHTML = `
    <div class="console-title">Live Test Execution</div>
    <div class="console-stats">
      <span class="console-stat passed">✓ ${passed}</span>
      <span class="console-stat failed">✗ ${failed}</span>
      <span class="console-stat running">⏳ ${running}</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" style="width: ${progress}%"></div>
    </div>
  `;
}

async function streamPositive() {
  const c = byId('positiveConsole');
  c.innerHTML = '<div class="console-empty">Click to start live console for positive tests</div>';
  const res = await fetch('/stream/positive');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop();
    for (const chunk of parts) {
      const line = chunk.split('\n').find(l => l.startsWith('data: '));
      if (!line) continue;
      const json = line.replace(/^data: /, '');
      try {
        const evt = JSON.parse(json);
        if (evt.type === 'test') {
          // Clear empty state when first test arrives
          const emptyState = c.querySelector('.console-empty');
          if (emptyState) emptyState.remove();
          renderTestCard('positiveConsole', evt);
        }
        if (evt.type === 'summary') {
          if (typeof evt.passed === 'number') byId('posPassCount').textContent = String(evt.passed);
          if (typeof evt.failed === 'number') byId('posFailCount').textContent = String(evt.failed);
          if (typeof evt.executed === 'number') byId('posExecCount').textContent = String(evt.executed);
        }
      } catch {}
    }
  }
}

async function streamAll() {
  const c = byId('allConsole');
  c.innerHTML = '<div class="console-empty">Click to start live console for all tests</div>';
  const res = await fetch('/stream/all');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop();
    for (const chunk of parts) {
      const line = chunk.split('\n').find(l => l.startsWith('data: '));
      if (!line) continue;
      const json = line.replace(/^data: /, '');
      try {
        const evt = JSON.parse(json);
        if (evt.type === 'test') {
          // Clear empty state when first test arrives
          const emptyState = c.querySelector('.console-empty');
          if (emptyState) emptyState.remove();
          renderTestCard('allConsole', evt);
        }
        if (evt.type === 'summary') {
          if (typeof evt.passed === 'number') byId('allPassCount').textContent = String(evt.passed);
          if (typeof evt.failed === 'number') byId('allFailCount').textContent = String(evt.failed);
          if (typeof evt.executed === 'number') byId('execCount').textContent = String(evt.executed);
          byId('genCountExec').textContent = byId('genCount').textContent || byId('genCountExec').textContent;
        }
      } catch {}
    }
  }
}

byId('uploadSwagger').addEventListener('click', uploadSwagger);
byId('previewEndpoints').addEventListener('click', previewEndpoints);
byId('generateTestcases').addEventListener('click', generateTestcases);
byId('executeAll').addEventListener('click', executeAll);
byId('executePositive').addEventListener('click', executePositive);
byId('startRun').addEventListener('click', startRun);
byId('refreshStatus').addEventListener('click', refreshStatus);
byId('loadLogs').addEventListener('click', loadLogs);
byId('loadResults').addEventListener('click', loadResults);
byId('generateReport').addEventListener('click', generateReport);
byId('streamPositive').addEventListener('click', streamPositive);
byId('streamAll').addEventListener('click', streamAll);
byId('allureReportPositive').addEventListener('click', () => openAllureReport('positive'));
byId('allureReportAll').addEventListener('click', () => openAllureReport('all'));
byId('extractSwagger').addEventListener('click', extractSwagger);
byId('persistTestcases').addEventListener('click', persistTestcases);


