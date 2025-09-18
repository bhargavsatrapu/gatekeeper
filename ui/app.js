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


