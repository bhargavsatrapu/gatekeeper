const byId = (id) => document.getElementById(id);

// Navigation and UI Management
let currentSection = 'swagger-upload';

// Section titles mapping
const sectionTitles = {
  'swagger-upload': 'Swagger Upload',
  'endpoints': 'Endpoints',
  'testcases': 'Generate Testcases',
  'positive-tests': 'Positive Tests',
  'individual-tests': 'Individual Tests',
  'all-tests': 'All Tests',
  'reports': 'Reports & Results',
  'orchestration': 'Orchestration'
};

// Initialize navigation
function initNavigation() {
  const sidebar = byId('sidebar');
  const sidebarToggle = byId('sidebarToggle');
  const mobileMenuToggle = byId('mobileMenuToggle');
  const navLinks = document.querySelectorAll('.nav-link');
  const pageTitle = byId('pageTitle');

  console.log('Initializing navigation...');
  console.log('Sidebar:', sidebar);
  console.log('Mobile menu toggle:', mobileMenuToggle);

  // Sidebar toggle functionality
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      console.log('Sidebar toggled, classes:', sidebar.className);
    });
  }

  // Mobile menu toggle
  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        console.log('Mobile menu closed');
      } else {
        sidebar.classList.add('open');
        console.log('Mobile menu opened');
      }
    });
  }

  // Navigation link clicks
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const section = link.dataset.section;
      if (section) {
        showSection(section);
        
        // Update active nav link
        navLinks.forEach(nav => nav.classList.remove('active'));
        link.classList.add('active');
        
        // Close mobile menu if open
        sidebar.classList.remove('open');
      }
    });
  });

  // Close mobile menu when clicking outside
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && 
        sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && 
        !mobileMenuToggle.contains(e.target)) {
      sidebar.classList.remove('open');
      console.log('Mobile menu closed by outside click');
    }
  });

  // Handle window resize
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('open');
    }
  });
}

// Show specific section
function showSection(sectionId) {
  // Hide all sections
  const sections = document.querySelectorAll('.content-section');
  sections.forEach(section => {
    section.classList.remove('active');
  });

  // Show target section
  const targetSection = byId(sectionId);
  if (targetSection) {
    targetSection.classList.add('active');
    currentSection = sectionId;
    
    // Update page title
    const pageTitle = byId('pageTitle');
    if (pageTitle && sectionTitles[sectionId]) {
      pageTitle.textContent = sectionTitles[sectionId];
    }
    
    // Reset endpoints preview when navigating to endpoints section
    if (sectionId === 'endpoints') {
      const preview = byId('endpointsPreview');
      if (preview) {
        preview.textContent = 'Click "Load Endpoints from DB" to view endpoints stored in the database';
        preview.className = 'placeholder-text';
      }
    }
  }
}

// Toast Notification Functions
function showToast(type, title, message, duration = 5000) {
  const container = byId('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };
  
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" onclick="removeToast(this.parentElement)">×</button>
  `;
  
  container.appendChild(toast);
  
  // Auto remove after duration
  setTimeout(() => {
    if (toast.parentElement) {
      removeToast(toast);
    }
  }, duration);
  
  return toast;
}

function removeToast(toast) {
  toast.style.animation = 'slideOut 0.3s ease';
  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast);
    }
  }, 300);
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  
  // File input handling
  const swaggerFile = byId('swaggerFile');
  const fileName = byId('fileName');
  
  if (swaggerFile && fileName) {
    swaggerFile.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        fileName.textContent = `Selected: ${file.name}`;
        fileName.style.color = 'var(--accent)';
        fileName.style.fontWeight = '500';
      } else {
        fileName.textContent = 'No file selected';
        fileName.style.color = 'var(--muted)';
        fileName.style.fontWeight = 'normal';
      }
    });
  }
  
  // Fallback mobile menu toggle
  const mobileMenuToggle = byId('mobileMenuToggle');
  const sidebar = byId('sidebar');
  
  if (mobileMenuToggle && sidebar) {
    // Add additional event listener as fallback
    mobileMenuToggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        console.log('Mobile menu closed');
      } else {
        sidebar.classList.add('open');
        console.log('Mobile menu opened');
      }
    });
  }
});

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
  const preview = byId('endpointsPreview');
  
  btn.disabled = true; 
  loading.style.display = 'inline-flex';
  
  // Clear any previous results and show loading state
  preview.textContent = 'Loading endpoints from database...';
  preview.className = ''; // Remove placeholder styling
  
  try {
    const res = await fetch('/endpoints/preview');
    if (!res.ok) {
      const text = await res.text();
      preview.textContent = JSON.stringify({ error: 'Preview failed', status: res.status, body: text }, null, 2);
      return;
    }
    const data = await res.json();
    preview.textContent = JSON.stringify(data, null, 2);
  } finally {
    btn.disabled = false; 
    loading.style.display = 'none';
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
    // Note: Endpoints preview will need to be manually refreshed after extraction
  } finally {
    btn.disabled = false;
  }
}

async function persistTestcases() {
  const btn = byId('persistTestcases');
  btn.disabled = true;
  btn.textContent = 'Storing...';
  
  try {
    const res = await fetch('/testcases/persist', { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      const prev = byId('testcasesPreview').textContent;
      byId('testcasesPreview').textContent = (prev ? prev + "\n\n" : "") + JSON.stringify({ error: 'Persist failed', status: res.status, body: text }, null, 2);
      
      // Show error toast
      showToast('error', 'Storage Failed', 'Failed to store testcases to database. Please try again.');
      return;
    }
    
    const data = await res.json();
    const prev = byId('testcasesPreview').textContent;
    const stamp = new Date().toISOString();
    const msg = `=== Persisted @ ${stamp} ===\n` + JSON.stringify(data, null, 2);
    byId('testcasesPreview').textContent = (prev ? prev + "\n\n" : "") + msg;
    
    // Check if there's data to store
    if (data && (data.stored_count > 0 || data.persisted_count > 0)) {
      const count = data.stored_count || data.persisted_count || 0;
      showToast('success', 'Successfully Stored', `${count} testcases have been stored to the database.`);
    } else {
      showToast('warning', 'Nothing to Store', 'No testcases were found to store. Please generate testcases first.');
    }
    
  } catch (error) {
    console.error('Error persisting testcases:', error);
    showToast('error', 'Storage Error', 'An error occurred while storing testcases. Please try again.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Store Testcases to DB';
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
  // Ensure we can see all results by scrolling to top
  c.scrollTop = 0;
  
  // Ensure the container is scrollable and shows all content
  setTimeout(() => {
    c.scrollTop = 0;
  }, 100);
  
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
          
          // Note: Endpoints preview can be manually refreshed if needed
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


