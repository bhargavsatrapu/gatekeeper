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

async function uploadSwagger() {
  const input = byId('swaggerFile');
  if (!input.files || !input.files[0]) return;
  const fd = new FormData();
  fd.append('file', input.files[0]);
  const res = await fetch('/swagger/upload', { method: 'POST', body: fd });
  const data = await res.json();
  byId('uploadInfo').textContent = JSON.stringify(data, null, 2);
}

async function previewEndpoints() {
  const res = await fetch('/endpoints/preview');
  const data = await res.json();
  byId('endpointsPreview').textContent = JSON.stringify(data, null, 2);
}

async function generateTestcases() {
  const res = await fetch('/testcases/generate', { method: 'POST' });
  const data = await res.json();
  const total = Object.values(data.mapping || {}).reduce((acc, arr) => acc + arr.length, 0);
  const header = { generated_total: total, total_endpoints: data.total_endpoints };
  byId('testcasesPreview').textContent = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
  byId('genCount').textContent = String(total);
}

async function executeAll() {
  const res = await fetch('/execute/all', { method: 'POST' });
  const data = await res.json();
  const header = { generated_total: data.generated_total, executed_total: data.executed };
  byId('executeAllResults').textContent = JSON.stringify(header, null, 2) + "\n" + JSON.stringify(data, null, 2);
  if (typeof data.generated_total === 'number') byId('genCountExec').textContent = String(data.generated_total);
  if (typeof data.executed === 'number') byId('execCount').textContent = String(data.executed);
}

byId('uploadSwagger').addEventListener('click', uploadSwagger);
byId('previewEndpoints').addEventListener('click', previewEndpoints);
byId('generateTestcases').addEventListener('click', generateTestcases);
byId('executeAll').addEventListener('click', executeAll);
byId('startRun').addEventListener('click', startRun);
byId('refreshStatus').addEventListener('click', refreshStatus);
byId('loadLogs').addEventListener('click', loadLogs);
byId('loadResults').addEventListener('click', loadResults);


