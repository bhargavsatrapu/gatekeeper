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
  // Don't auto-refresh preview after upload - wait for extraction
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
    
    // Show persistence results if available
    if (data.persisted) {
      const persistMsg = `=== Auto-Persisted @ ${stamp} ===\n` + JSON.stringify(data.persisted, null, 2);
      byId('persistOutput').textContent = persistMsg;
    }
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
    // Use web-based Allure viewer instead of CLI
    const resultsDir = type === 'positive' ? 'allure-results-positive' : 'allure-results-all';
    
    // Check if results exist
    const res = await fetch(`/allure/data/${resultsDir}`);
    if (!res.ok) {
      alert(`No Allure results found for ${type} tests. Please run tests first.`);
      return;
    }
    
    // Open web-based Allure viewer
    const viewerUrl = `/allure-viewer.html?type=${type}&results=${resultsDir}`;
    window.open(viewerUrl, '_blank');
    
  } catch (e) {
    alert(`Error opening Allure report: ${e.message}`);
  }
}

async function generateStaticAllureReport(type) {
  try {
    const res = await fetch(`/allure/generate-static/${type}`);
    const data = await res.json();
    
    if (res.ok) {
      alert(`Static Allure report generated!\n\nReport location: ${data.report_dir}\n\nYou can open the index.html file in your browser to view the report.`);
      
      // Try to open the static report
      const reportUrl = `file://${data.index_file.replace(/\\/g, '/')}`;
      window.open(reportUrl, '_blank');
    } else {
      alert(`Error generating static report: ${data.detail}`);
    }
  } catch (e) {
    alert(`Error generating static report: ${e.message}`);
  }
}

async function openAllureReportEndpoint(endpointId, method, path) {
  try {
    // Use web-based Allure viewer for endpoint-specific reports
    const resultsDir = `allure-results-endpoint-${endpointId}`;
    
    // Check if results exist
    const res = await fetch(`/allure/data/${resultsDir}`);
    if (!res.ok) {
      alert(`No Allure results found for ${method} ${path}. Please run tests first.`);
      return;
    }
    
    // Open web-based Allure viewer
    const viewerUrl = `/allure-viewer.html?type=endpoint&results=${resultsDir}&endpoint=${method} ${path}`;
    window.open(viewerUrl, '_blank');
    
  } catch (e) {
    alert(`Error opening Allure report for ${method} ${path}: ${e.message}`);
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
    
    // Check if server actually started
    if (data.status === 'failed') {
      throw new Error(data.message + (data.suggestion ? '\n\n' + data.suggestion : ''));
    }
    
    return data;
  } catch (e) {
    console.error('Failed to start Allure server:', e);
    throw e;
  }
}

async function executeAll() {
  // Use streaming execution instead of regular execution to avoid duplicate runs
  await streamAll();
}

async function executePositive() {
  // Use streaming execution instead of regular execution to avoid duplicate runs
  await streamPositive();
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
  c.innerHTML = '<div class="console-empty">Starting live execution...</div>';
  const res = await fetch('/stream/positive');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let testCount = 0;
  
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
          
          // Add test case one by one as they execute
          testCount++;
          renderTestCard('positiveConsole', evt);
          
          // Scroll to show the latest test case
          c.scrollTop = c.scrollHeight;
        }
        if (evt.type === 'summary') {
          if (typeof evt.passed === 'number') byId('posPassCount').textContent = String(evt.passed);
          if (typeof evt.failed === 'number') byId('posFailCount').textContent = String(evt.failed);
          if (typeof evt.executed === 'number') byId('posExecCount').textContent = String(evt.executed);
          
          // Auto-refresh preview after execution completes
          setTimeout(() => {
            previewEndpoints();
          }, 1000);
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
async function loadEndpoints() {
  const btn = byId('loadEndpoints');
  const loading = byId('loadEndpointsLoading');
  btn.disabled = true; loading.style.display = 'inline-flex';
  try {
    const res = await fetch('/endpoints/preview');
    if (!res.ok) {
      const text = await res.text();
      byId('endpointsList').innerHTML = `<div class="error">Failed to load endpoints: ${text}</div>`;
      return;
    }
    const data = await res.json();
    const endpoints = data.endpoints || [];
    
    let html = '<div class="endpoints-grid">';
    endpoints.forEach(ep => {
      const endpointKey = `${ep.method} ${ep.path}`;
            html += `
              <div class="endpoint-card">
                <div class="endpoint-header">
                  <span class="method ${ep.method.toLowerCase()}">${ep.method}</span>
                  <span class="path">${ep.path}</span>
                </div>
                <div class="endpoint-info">
                  <div class="endpoint-id">ID: ${ep.id}</div>
                  <div class="endpoint-summary">${ep.summary || 'No summary'}</div>
                </div>
                <div class="endpoint-actions">
                  <button class="run-endpoint-btn" data-endpoint-id="${ep.id}" data-method="${ep.method}" data-path="${ep.path}">
                    Run Testcases
                  </button>
                  <button class="allure-endpoint-btn" data-endpoint-id="${ep.id}" data-method="${ep.method}" data-path="${ep.path}">
                    Allure Report
                  </button>
                </div>
              </div>
            `;
    });
    html += '</div>';
    byId('endpointsList').innerHTML = html;
    
    // Add click handlers to all run buttons
    document.querySelectorAll('.run-endpoint-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const endpointId = parseInt(e.target.dataset.endpointId);
        const method = e.target.dataset.method;
        const path = e.target.dataset.path;
        runEndpointTestcases(endpointId, method, path);
      });
    });
    
    // Add click handlers to all allure report buttons
    document.querySelectorAll('.allure-endpoint-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const endpointId = parseInt(e.target.dataset.endpointId);
        const method = e.target.dataset.method;
        const path = e.target.dataset.path;
        openAllureReportEndpoint(endpointId, method, path);
      });
    });
    
  } finally {
    btn.disabled = false; loading.style.display = 'none';
  }
}

async function runEndpointTestcases(endpointId, method, path) {
  const btn = document.querySelector(`[data-endpoint-id="${endpointId}"]`);
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Running...';
  
  try {
    const res = await fetch(`/execute/endpoint/${endpointId}`, { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      byId('endpointResults').textContent = JSON.stringify({ error: 'Execute endpoint failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    const header = {
      endpoint: `${method} ${path}`,
      endpoint_id: endpointId,
      total_tests: data.summary?.total_tests,
      passed_tests: data.summary?.passed_tests,
      failed_tests: data.summary?.failed_tests
    };
    const prev = byId('endpointResults').textContent;
    const stamp = new Date().toISOString();
    const block = `=== Execute Endpoint @ ${stamp} ===\n` + JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
    byId('endpointResults').textContent = (prev ? prev + "\n\n" : "") + block;
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

byId('generateTestcases').addEventListener('click', generateTestcases);
byId('loadEndpoints').addEventListener('click', loadEndpoints);
byId('executeAll').addEventListener('click', executeAll);
byId('executePositive').addEventListener('click', executePositive);
byId('startRun').addEventListener('click', startRun);
byId('refreshStatus').addEventListener('click', refreshStatus);
byId('loadLogs').addEventListener('click', loadLogs);
byId('loadResults').addEventListener('click', loadResults);
byId('generateReport').addEventListener('click', generateReport);
byId('allureReportPositive').addEventListener('click', () => openAllureReport('positive'));
byId('allureReportAll').addEventListener('click', () => openAllureReport('all'));
byId('extractSwagger').addEventListener('click', extractSwagger);
byId('persistTestcases').addEventListener('click', persistTestcases);


