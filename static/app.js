// Enhanced UI functionality
function selectTab(event, id) {
  event.preventDefault();
  
  // Add smooth transition
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.remove('active');
    t.style.opacity = '0';
  });
  
  setTimeout(() => {
    const el = document.getElementById(id);
    if (el) {
      el.classList.add('active');
      el.style.opacity = '1';
    }
  }, 150);
  
  // Start polling for console logs if console tab is selected
  if (id === 'tab-console') {
    startConsolePolling();
  } else {
    stopConsolePolling();
  }
}

// Console functionality
let consolePollingInterval = null;
let autoScroll = true;
let lastLogCount = 0;

function startConsolePolling() {
  if (consolePollingInterval) return;
  consolePollingInterval = setInterval(fetchConsoleLogs, 1000);
}

function stopConsolePolling() {
  if (consolePollingInterval) {
    clearInterval(consolePollingInterval);
    consolePollingInterval = null;
  }
}

function fetchConsoleLogs() {
  fetch('/api/console-logs')
    .then(response => response.json())
    .then(data => {
      if (data.logs && data.logs.length > lastLogCount) {
        updateConsole(data.logs);
        lastLogCount = data.logs.length;
      }
    })
    .catch(error => console.error('Error fetching logs:', error));
}

function updateConsole(logs) {
  const consoleOutput = document.getElementById('console-output');
  
  // Clear and rebuild with animation
  consoleOutput.innerHTML = '';
  
  logs.forEach((log, index) => {
    const line = document.createElement('div');
    line.className = `console-line ${log.type || 'info'}`;
    line.textContent = `[${log.timestamp}] ${log.message}`;
    line.style.opacity = '0';
    line.style.transform = 'translateY(10px)';
    consoleOutput.appendChild(line);
    
    // Animate in
    setTimeout(() => {
      line.style.transition = 'all 0.3s ease';
      line.style.opacity = '1';
      line.style.transform = 'translateY(0)';
    }, index * 50);
  });
  
  if (autoScroll) {
    setTimeout(() => {
      consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }, 100);
  }
}

function clearConsole() {
  const consoleOutput = document.getElementById('console-output');
  consoleOutput.style.opacity = '0.5';
  
  fetch('/api/clear-console', { method: 'POST' })
    .then(() => {
      consoleOutput.innerHTML = '<div class="console-line success">Console cleared successfully.</div>';
      consoleOutput.style.opacity = '1';
      lastLogCount = 0;
    })
    .catch(() => {
      consoleOutput.innerHTML = '<div class="console-line error">Failed to clear console.</div>';
      consoleOutput.style.opacity = '1';
    });
}

function toggleAutoScroll() {
  autoScroll = !autoScroll;
  const statusEl = document.getElementById('auto-scroll-status');
  statusEl.textContent = autoScroll ? 'ON' : 'OFF';
  statusEl.style.color = autoScroll ? '#34d399' : '#f87171';
}

// Loading functionality
function showLoading(button) {
  const originalText = button.textContent;
  button.innerHTML = '<span class="loader"></span>Processing...';
  button.classList.add('loading');
  button.disabled = true;
  
  return () => {
    button.textContent = originalText;
    button.classList.remove('loading');
    button.disabled = false;
  };
}

// Enhanced form submissions
document.addEventListener('DOMContentLoaded', function() {
  // Add loading to all form submissions
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        const hideLoading = showLoading(submitButton);
        
        // Hide loading after 3 seconds (in case redirect is slow)
        setTimeout(hideLoading, 3000);
        
        // Show View Testcases button after generation
        if (form.id === 'generate-form') {
          setTimeout(() => {
            const viewBtn = document.getElementById('view-testcases-btn');
            if (viewBtn) {
              viewBtn.style.display = 'block';
            }
          }, 1000);
        }
      }
    });
  });
  
  // Add smooth scrolling to console
  const consoleOutput = document.getElementById('console-output');
  if (consoleOutput) {
    consoleOutput.addEventListener('scroll', function() {
      const isAtBottom = Math.abs(consoleOutput.scrollHeight - consoleOutput.clientHeight - consoleOutput.scrollTop) < 1;
      if (!isAtBottom) {
        autoScroll = false;
        document.getElementById('auto-scroll-status').textContent = 'OFF';
        document.getElementById('auto-scroll-status').style.color = '#f87171';
      }
    });
  }
  
  // Add keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
      switch(e.key) {
        case '1':
          e.preventDefault();
          selectTab(e, 'tab-upload');
          break;
        case '2':
          e.preventDefault();
          selectTab(e, 'tab-generate');
          break;
        case '3':
          e.preventDefault();
          selectTab(e, 'tab-positive');
          break;
        case '4':
          e.preventDefault();
          selectTab(e, 'tab-all');
          break;
        case '5':
          e.preventDefault();
          selectTab(e, 'tab-console');
          break;
      }
    }
  });
  
  // Add tooltips
  const buttons = document.querySelectorAll('button');
  buttons.forEach(button => {
    button.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-2px)';
    });
    button.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });
});

// Endpoints functionality
function loadEndpoints() {
  const endpointsSection = document.getElementById('endpoints-section');
  const tableContainer = document.getElementById('endpoints-table-container');
  
  // Show loading state
  tableContainer.innerHTML = `
    <div class="loading-endpoints">
      <div class="loader"></div>
      <div>Loading endpoints...</div>
    </div>
  `;
  
  endpointsSection.style.display = 'block';
  
  // Fetch endpoints
  fetch('/api/endpoints')
    .then(response => response.json())
    .then(data => {
      if (data.endpoints && data.endpoints.length > 0) {
        renderEndpointsTable(data.endpoints);
      } else {
        tableContainer.innerHTML = `
          <div class="no-endpoints">
            <h4>No endpoints found</h4>
            <p>Upload a Swagger file first to see endpoints here.</p>
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Error loading endpoints:', error);
      tableContainer.innerHTML = `
        <div class="no-endpoints">
          <h4>Error loading endpoints</h4>
          <p>Please try again or check if the database is accessible.</p>
        </div>
      `;
    });
}

function renderEndpointsTable(endpoints) {
  const tableContainer = document.getElementById('endpoints-table-container');
  
  const tableHTML = `
    <table class="endpoints-table">
      <thead>
        <tr>
          <th>Method</th>
          <th>Path</th>
          <th>Summary</th>
          <th>Tags</th>
          <th>Operation ID</th>
        </tr>
      </thead>
      <tbody>
        ${endpoints.map(endpoint => `
          <tr>
            <td>
              <span class="method-badge method-${endpoint.method.toLowerCase()}">
                ${endpoint.method}
              </span>
            </td>
            <td class="path-cell">${endpoint.path}</td>
            <td class="summary-cell" title="${endpoint.summary || 'No summary'}">
              ${endpoint.summary || 'No summary'}
            </td>
            <td class="tags-cell">
              ${endpoint.tags && endpoint.tags.length > 0 
                ? endpoint.tags.map(tag => `<span class="tag">${tag}</span>`).join('')
                : '<span class="tag">No tags</span>'
              }
            </td>
            <td class="path-cell">${endpoint.operation_id || 'N/A'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  tableContainer.innerHTML = tableHTML;
  
  // Add animation to table rows
  const rows = tableContainer.querySelectorAll('tbody tr');
  rows.forEach((row, index) => {
    row.style.opacity = '0';
    row.style.transform = 'translateY(10px)';
    setTimeout(() => {
      row.style.transition = 'all 0.3s ease';
      row.style.opacity = '1';
      row.style.transform = 'translateY(0)';
    }, index * 50);
  });
}

function filterEndpoints() {
  const searchTerm = document.getElementById('endpoint-search').value.toLowerCase();
  const table = document.querySelector('.endpoints-table');
  
  if (!table) return;
  
  const rows = table.querySelectorAll('tbody tr');
  let visibleCount = 0;
  
  rows.forEach(row => {
    const method = row.cells[0].textContent.toLowerCase();
    const path = row.cells[1].textContent.toLowerCase();
    const summary = row.cells[2].textContent.toLowerCase();
    const tags = row.cells[3].textContent.toLowerCase();
    const operationId = row.cells[4].textContent.toLowerCase();
    
    const matches = method.includes(searchTerm) || 
                   path.includes(searchTerm) || 
                   summary.includes(searchTerm) || 
                   tags.includes(searchTerm) || 
                   operationId.includes(searchTerm);
    
    if (matches) {
      row.style.display = '';
      visibleCount++;
    } else {
      row.style.display = 'none';
    }
  });
  
  // Show no results message if needed
  const tbody = table.querySelector('tbody');
  let noResultsRow = tbody.querySelector('.no-results-row');
  
  if (visibleCount === 0 && searchTerm) {
    if (!noResultsRow) {
      noResultsRow = document.createElement('tr');
      noResultsRow.className = 'no-results-row';
      noResultsRow.innerHTML = `
        <td colspan="5" style="text-align: center; padding: 20px; color: #6b7280; font-style: italic;">
          No endpoints match your search criteria.
        </td>
      `;
      tbody.appendChild(noResultsRow);
    }
    noResultsRow.style.display = '';
  } else if (noResultsRow) {
    noResultsRow.style.display = 'none';
  }
}

function clearEndpoints() {
  const endpointsSection = document.getElementById('endpoints-section');
  const searchInput = document.getElementById('endpoint-search');
  
  endpointsSection.style.display = 'none';
  searchInput.value = '';
}

// Testcases functionality
function loadTestcases() {
  const testcasesSection = document.getElementById('testcases-section');
  const testcasesContainer = document.getElementById('testcases-container');
  
  // Show loading state
  testcasesContainer.innerHTML = `
    <div class="loading-testcases">
      <div class="loader"></div>
      <div>Loading test cases...</div>
    </div>
  `;
  
  testcasesSection.style.display = 'block';
  
  // Fetch testcases
  fetch('/api/testcases')
    .then(response => response.json())
    .then(data => {
      if (data.testcases && Object.keys(data.testcases).length > 0) {
        renderTestcases(data.testcases);
        populateEndpointFilter(data.testcases);
      } else {
        testcasesContainer.innerHTML = `
          <div class="no-testcases">
            <h4>No test cases found</h4>
            <p>Generate test cases first to see them here.</p>
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Error loading testcases:', error);
      testcasesContainer.innerHTML = `
        <div class="no-testcases">
          <h4>Error loading test cases</h4>
          <p>Please try again or check if the database is accessible.</p>
        </div>
      `;
    });
}

function renderTestcases(testcases) {
  const testcasesContainer = document.getElementById('testcases-container');
  
  let html = '';
  
  Object.entries(testcases).forEach(([tableName, testcasesList]) => {
    if (testcasesList.length === 0) return;
    
    html += `
      <div class="endpoint-testcases" data-endpoint="${tableName}">
        <div class="endpoint-header">
          <div class="endpoint-name">${tableName}</div>
          <div class="testcase-count">${testcasesList.length} test cases</div>
        </div>
        <table class="testcases-table">
          <thead>
            <tr>
              <th>Test Name</th>
              <th>Type</th>
              <th>Method</th>
              <th>URL</th>
              <th>Expected Status</th>
            </tr>
          </thead>
          <tbody>
            ${testcasesList.map(testcase => `
              <tr>
                <td class="test-name-cell" title="${testcase.test_name || 'No name'}">
                  ${testcase.test_name || 'No name'}
                </td>
                <td>
                  <span class="test-type-badge test-${testcase.test_type || 'positive'}">
                    ${testcase.test_type || 'positive'}
                  </span>
                </td>
                <td class="test-status-cell">${testcase.method || 'N/A'}</td>
                <td class="test-url-cell" title="${testcase.url || 'No URL'}">
                  ${testcase.url || 'No URL'}
                </td>
                <td class="test-status-cell">${testcase.expected_status || 'N/A'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  });
  
  testcasesContainer.innerHTML = html;
  
  // Add animation to endpoint sections
  const endpointSections = testcasesContainer.querySelectorAll('.endpoint-testcases');
  endpointSections.forEach((section, index) => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';
    setTimeout(() => {
      section.style.transition = 'all 0.3s ease';
      section.style.opacity = '1';
      section.style.transform = 'translateY(0)';
    }, index * 100);
  });
}

function populateEndpointFilter(testcases) {
  const endpointFilter = document.getElementById('endpoint-filter');
  
  // Clear existing options except "All Endpoints"
  endpointFilter.innerHTML = '<option value="">All Endpoints</option>';
  
  Object.keys(testcases).forEach(tableName => {
    if (testcases[tableName].length > 0) {
      const option = document.createElement('option');
      option.value = tableName;
      option.textContent = tableName;
      endpointFilter.appendChild(option);
    }
  });
}

function filterTestcases() {
  const searchTerm = document.getElementById('testcase-search').value.toLowerCase();
  const endpointFilter = document.getElementById('endpoint-filter').value;
  const endpointSections = document.querySelectorAll('.endpoint-testcases');
  
  endpointSections.forEach(section => {
    const tableName = section.getAttribute('data-endpoint');
    const rows = section.querySelectorAll('tbody tr');
    let visibleRows = 0;
    
    // Filter by endpoint first
    if (endpointFilter && tableName !== endpointFilter) {
      section.style.display = 'none';
      return;
    } else {
      section.style.display = '';
    }
    
    // Then filter by search term
    rows.forEach(row => {
      const testName = row.cells[0].textContent.toLowerCase();
      const testType = row.cells[1].textContent.toLowerCase();
      const method = row.cells[2].textContent.toLowerCase();
      const url = row.cells[3].textContent.toLowerCase();
      const status = row.cells[4].textContent.toLowerCase();
      
      const matches = testName.includes(searchTerm) || 
                     testType.includes(searchTerm) || 
                     method.includes(searchTerm) || 
                     url.includes(searchTerm) || 
                     status.includes(searchTerm);
      
      if (matches) {
        row.style.display = '';
        visibleRows++;
      } else {
        row.style.display = 'none';
      }
    });
    
    // Hide endpoint section if no visible rows
    if (visibleRows === 0) {
      section.style.display = 'none';
    }
  });
}

function filterByEndpoint() {
  filterTestcases(); // Reuse the same filtering logic
}

function clearTestcases() {
  const testcasesSection = document.getElementById('testcases-section');
  const searchInput = document.getElementById('testcase-search');
  const endpointFilter = document.getElementById('endpoint-filter');
  
  testcasesSection.style.display = 'none';
  searchInput.value = '';
  endpointFilter.value = '';
}

// Individual Endpoints functionality
let selectedEndpoints = new Set();

function loadIndividualEndpoints() {
  const container = document.getElementById('individual-endpoints-container');
  const grid = document.getElementById('endpoints-grid');
  
  // Show loading state
  grid.innerHTML = `
    <div class="loading-endpoints">
      <div class="loader"></div>
      <div>Loading endpoints...</div>
    </div>
  `;
  
  container.style.display = 'block';
  document.getElementById('clear-individual-btn').style.display = 'block';
  
  // Fetch endpoints
  fetch('/api/endpoints')
    .then(response => response.json())
    .then(data => {
      if (data.endpoints && data.endpoints.length > 0) {
        renderIndividualEndpoints(data.endpoints);
      } else {
        grid.innerHTML = `
          <div class="no-endpoints">
            <h4>No endpoints found</h4>
            <p>Upload a Swagger file first to see endpoints here.</p>
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Error loading endpoints:', error);
      grid.innerHTML = `
        <div class="no-endpoints">
          <h4>Error loading endpoints</h4>
          <p>Please try again or check if the database is accessible.</p>
        </div>
      `;
    });
}

function renderIndividualEndpoints(endpoints) {
  const grid = document.getElementById('endpoints-grid');

  if (!Array.isArray(endpoints)) {
    grid.innerHTML = `
      <div class="no-endpoints">
        <h4>Invalid endpoints data</h4>
        <p>Expected a list of endpoints from the server.</p>
      </div>
    `;
    return;
  }

  const safeCards = endpoints.map((raw) => {
    const id = Number(raw && raw.id) || 0;
    const method = ((raw && raw.method) ? String(raw.method) : 'GET').toLowerCase();
    const methodLabel = ((raw && raw.method) ? String(raw.method) : 'GET').toUpperCase();
    const path = (raw && raw.path) ? String(raw.path) : '/unknown';
    const summary = (raw && raw.summary) ? String(raw.summary) : 'No summary available';
    const tagsRaw = raw && raw.tags;
    const tags = Array.isArray(tagsRaw)
      ? tagsRaw
      : (tagsRaw ? [String(tagsRaw)] : []);

    const tagsHtml = tags.length > 0
      ? tags.map(tag => `<span class="tag">${String(tag)}</span>`).join('')
      : '<span class="tag">No tags</span>';

    return {
      id,
      method,
      methodLabel,
      path,
      summary,
      tagsHtml,
    };
  });

  const cardsHTML = safeCards.map(endpoint => `
    <div class="endpoint-card" data-endpoint-id="${endpoint.id}" onclick="toggleEndpointSelection(${endpoint.id})">
      <div class="endpoint-card-header">
        <span class="method-badge method-${endpoint.method}">${endpoint.methodLabel}</span>
        <div class="endpoint-selection-indicator">
          <input type="checkbox" id="endpoint-${endpoint.id}" onchange="toggleEndpointSelection(${endpoint.id})" />
        </div>
      </div>
      <div class="endpoint-card-body">
        <div class="endpoint-path">${endpoint.path}</div>
        <div class="endpoint-summary">${endpoint.summary}</div>
        <div class="endpoint-tags">${endpoint.tagsHtml}</div>
      </div>
    </div>
  `).join('');

  grid.innerHTML = cardsHTML;

  // Add animation to cards
  const cards = grid.querySelectorAll('.endpoint-card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'all 0.3s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 50);
  });
}

function toggleEndpointSelection(endpointId) {
  const card = document.querySelector(`[data-endpoint-id="${endpointId}"]`);
  const checkbox = document.getElementById(`endpoint-${endpointId}`);
  
  if (selectedEndpoints.has(endpointId)) {
    selectedEndpoints.delete(endpointId);
    card.classList.remove('selected');
    checkbox.checked = false;
  } else {
    selectedEndpoints.add(endpointId);
    card.classList.add('selected');
    checkbox.checked = true;
  }
  
  updateRunButton();
}

function updateRunButton() {
  const runBtn = document.getElementById('run-endpoints-btn');
  const countSpan = document.getElementById('selected-count');
  
  const count = selectedEndpoints.size;
  countSpan.textContent = count;
  
  if (count > 0) {
    runBtn.disabled = false;
    runBtn.textContent = `Run Endpoints (${count} selected)`;
  } else {
    runBtn.disabled = true;
    runBtn.textContent = 'Run Endpoints (0 selected)';
  }
}

function runSelectedEndpoints() {
  if (selectedEndpoints.size === 0) {
    alert('Please select at least one endpoint to test.');
    return;
  }
  
  const runBtn = document.getElementById('run-endpoints-btn');
  const originalText = runBtn.textContent;
  
  // Show loading state
  runBtn.innerHTML = '<span class="loader"></span>Running Tests...';
  runBtn.disabled = true;
  
  const endpointIds = Array.from(selectedEndpoints);
  
  fetch('/run-individual-endpoints', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      endpoint_ids: endpointIds
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      // Show success message
      const notice = document.createElement('div');
      notice.className = 'notice success';
      notice.textContent = data.message;
      document.querySelector('h1').insertAdjacentElement('afterend', notice);
      
      // Auto-remove notice after 5 seconds
      setTimeout(() => {
        notice.remove();
      }, 5000);
    } else if (data.error) {
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error running endpoints:', error);
    alert('Error running endpoints: ' + error.message);
  })
  .finally(() => {
    // Restore button state
    runBtn.textContent = originalText;
    runBtn.disabled = false;
  });
}

function clearIndividualEndpoints() {
  const container = document.getElementById('individual-endpoints-container');
  const clearBtn = document.getElementById('clear-individual-btn');
  
  container.style.display = 'none';
  clearBtn.style.display = 'none';
  
  // Clear selections
  selectedEndpoints.clear();
  updateRunButton();
  
  // Clear any selected states
  document.querySelectorAll('.endpoint-card').forEach(card => {
    card.classList.remove('selected');
  });
  document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.checked = false;
  });
}


