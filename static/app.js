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
let executionStartTime = null;
let progressInterval = null;
let isConsoleActive = false;

function startConsolePolling() {
  if (consolePollingInterval) return;
  isConsoleActive = true;
  updateConsoleStatus();
  // Start with faster polling for immediate updates
  consolePollingInterval = setInterval(fetchConsoleLogs, 500);
}

function stopConsolePolling() {
  if (consolePollingInterval) {
    clearInterval(consolePollingInterval);
    consolePollingInterval = null;
  }
  isConsoleActive = false;
  updateConsoleStatus();
}

function updateConsoleStatus() {
  const statusIndicator = document.getElementById('console-status');
  if (statusIndicator) {
    if (isConsoleActive) {
      statusIndicator.innerHTML = '<i class="fas fa-circle" style="color: #10b981; animation: pulse 2s infinite;"></i> Live';
      statusIndicator.className = 'console-status active';
    } else {
      statusIndicator.innerHTML = '<i class="fas fa-circle" style="color: #6b7280;"></i> Paused';
      statusIndicator.className = 'console-status inactive';
    }
  }
}

function fetchConsoleLogs() {
  fetch('/api/console-logs')
    .then(response => response.json())
    .then(data => {
      if (data.logs && data.logs.length > lastLogCount) {
        updateConsole(data.logs);
        
        // Check for execution completion messages
        const newLogs = data.logs.slice(lastLogCount);
        checkForExecutionCompletion(newLogs);
        
        lastLogCount = data.logs.length;
        
        // Adjust polling frequency based on activity
        if (consolePollingInterval) {
          clearInterval(consolePollingInterval);
          // If we're getting frequent updates, poll faster
          const interval = data.logs.length > lastLogCount + 5 ? 300 : 500;
          consolePollingInterval = setInterval(fetchConsoleLogs, interval);
        }
      }
    })
    .catch(error => console.error('Error fetching logs:', error));
}

function updateConsole(logs) {
  const consoleOutput = document.getElementById('console-output');
  const currentLogCount = consoleOutput.children.length;
  
  // Only add new logs to avoid rebuilding everything
  if (logs.length > currentLogCount) {
    const newLogs = logs.slice(currentLogCount);
    
    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    
    newLogs.forEach((log, index) => {
      const line = document.createElement('div');
      line.className = `console-line ${log.type || 'info'}`;
      
      // Add appropriate icon based on log type
      let icon = '';
      switch(log.type) {
        case 'success':
          icon = '<i class="fas fa-check-circle"></i>';
          break;
        case 'error':
          icon = '<i class="fas fa-exclamation-circle"></i>';
          break;
        case 'warning':
          icon = '<i class="fas fa-exclamation-triangle"></i>';
          break;
        case 'test':
          icon = '<i class="fas fa-flask"></i>';
          break;
        case 'api':
          icon = '<i class="fas fa-exchange-alt"></i>';
          break;
        case 'response':
          icon = '<i class="fas fa-reply"></i>';
          break;
        default:
          icon = '<i class="fas fa-info-circle"></i>';
      }
      
      line.innerHTML = `<span class="log-timestamp">[${log.timestamp}]</span> <span class="log-icon">${icon}</span> <span class="log-message">${log.message}</span>`;
      line.style.opacity = '0';
      line.style.transform = 'translateY(10px)';
      fragment.appendChild(line);
    });
    
    // Append all new logs at once for better performance
    consoleOutput.appendChild(fragment);
    
    // Animate new logs in
    const newElements = consoleOutput.children;
    for (let i = currentLogCount; i < newElements.length; i++) {
      const element = newElements[i];
      setTimeout(() => {
        element.style.transition = 'all 0.3s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
      }, (i - currentLogCount) * 20);
    }
  }
  
  // Optimize scrolling for large log volumes
  if (autoScroll) {
    requestAnimationFrame(() => {
      consoleOutput.scrollTop = consoleOutput.scrollHeight;
    });
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

function checkForExecutionCompletion(newLogs) {
  // Check if any of the new logs indicate execution completion
  newLogs.forEach(log => {
    const message = log.message.toLowerCase();
    
    // Check for positive flow completion
    if (message.includes('positive flow execution completed successfully')) {
      updateNoticeMessage('success', 'Positive execution is completed');
    } else if (message.includes('positive flow execution failed')) {
      updateNoticeMessage('error', 'Positive execution failed');
    }
    
    // Check for all tests completion
    if (message.includes('all tests execution completed successfully')) {
      updateNoticeMessage('success', 'All tests execution is completed');
    } else if (message.includes('all tests execution failed')) {
      updateNoticeMessage('error', 'All tests execution failed');
    }
    
    // Check for individual endpoints completion
    if (message.includes('test execution completed successfully')) {
      updateNoticeMessage('success', 'Individual endpoints execution is completed');
    } else if (message.includes('test execution failed')) {
      updateNoticeMessage('error', 'Individual endpoints execution failed');
    }
  });
}

function updateNoticeMessage(status, message) {
  // Find the existing notice element
  let existingNotice = document.querySelector('.notice');
  if (!existingNotice) {
    // Create notice element if it doesn't exist
    existingNotice = document.createElement('div');
    existingNotice.className = 'notice';
    document.querySelector('h1').insertAdjacentElement('afterend', existingNotice);
  }
  // Update the existing notice
  existingNotice.className = `notice ${status}`;
  const icon = status === 'success' ? 'check-circle' : 'exclamation-circle';
  existingNotice.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
}

// Positive APIs functionality
function loadPositiveAPIs() {
  const loadBtn = document.getElementById('load-positive-btn');
  const clearBtn = document.getElementById('clear-positive-btn');
  const container = document.getElementById('positive-apis-container');
  const grid = document.getElementById('positive-apis-grid');
  
  // Show loading state
  loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
  loadBtn.disabled = true;
  
  fetch('/api/positive-apis')
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert('Error loading positive APIs: ' + data.error);
        return;
      }
      
      const positiveAPIs = data.positive_apis || [];
      
      if (positiveAPIs.length === 0) {
        grid.innerHTML = '<div class="no-data">No positive test cases found. Please generate test cases first.</div>';
      } else {
        // Display positive APIs in list format
        grid.innerHTML = `
          <div class="positive-apis-list">
            <div class="list-header">
              <div class="header-item method-col">Method</div>
              <div class="header-item url-col">URL</div>
              <div class="header-item description-col">Test Description</div>
              <div class="header-item status-col">Expected Status Code</div>
            </div>
            ${positiveAPIs.map(api => {
              const method = api.method || 'GET';
              const url = api.url || api.endpoint || 'N/A';
              const status = api.expected_status || api.status || '200';
              const description = api.test_name || api.description || 'No description';
              
              return `
                <div class="list-item">
                  <div class="list-cell method-col">
                    <span class="method ${method.toLowerCase()}">${method}</span>
                  </div>
                  <div class="list-cell url-col">
                    <code>${url}</code>
                  </div>
                  <div class="list-cell description-col">
                    ${description}
                  </div>
                  <div class="list-cell status-col">
                    <span class="status success">${status}</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        `;
      }
      
      // Show container and buttons
      container.style.display = 'block';
      clearBtn.style.display = 'inline-block';
      loadBtn.style.display = 'none';
      
    })
    .catch(error => {
      console.error('Error loading positive APIs:', error);
      alert('Error loading positive APIs: ' + error.message);
    })
    .finally(() => {
      // Reset button state
      loadBtn.innerHTML = '<i class="fas fa-download"></i> Load Positive APIs';
      loadBtn.disabled = false;
    });
}

function clearPositiveAPIs() {
  const loadBtn = document.getElementById('load-positive-btn');
  const clearBtn = document.getElementById('clear-positive-btn');
  const container = document.getElementById('positive-apis-container');
  
  // Hide container and buttons
  container.style.display = 'none';
  clearBtn.style.display = 'none';
  loadBtn.style.display = 'inline-block';
}

// Enhanced loading functionality
function showLoading(button, loadingText = 'Processing...') {
  const originalHTML = button.innerHTML;
  button.innerHTML = `<span class="loader"></span>${loadingText}`;
  button.classList.add('loading');
  button.disabled = true;
  
  return () => {
    button.innerHTML = originalHTML;
    button.classList.remove('loading');
    button.disabled = false;
  };
}

// Global execution state tracking
let isExecutionRunning = false;
let currentExecutionType = null;
let generationProgressInterval = null;
let currentStep = 0;

function setExecutionState(running, type = null) {
  isExecutionRunning = running;
  currentExecutionType = type;
  
  if (running) {
    executionStartTime = Date.now();
    startProgressIndicator();
  } else {
    executionStartTime = null;
    stopProgressIndicator();
  }
  
  // Disable/enable all execution buttons
  const executionButtons = [
    'generate-btn',
    'run-positive-btn', 
    'run-all-btn',
    'run-endpoints-btn'
  ];
  
  executionButtons.forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.disabled = running;
      if (running && type && btnId.includes(type)) {
        btn.classList.add('loading');
      } else {
        btn.classList.remove('loading');
      }
    }
  });
  
  // Update console tab indicator
  const consoleTab = document.querySelector('a[href="#tab-console"]');
  if (consoleTab) {
    if (running) {
      consoleTab.innerHTML = '<i class="fas fa-terminal"></i> Execution Console <span class="status-indicator status-running"><i class="fas fa-spinner fa-spin"></i> Running</span>';
    } else {
      consoleTab.innerHTML = '<i class="fas fa-terminal"></i> Execution Console';
    }
  }
}

function startProgressIndicator() {
  const consoleOutput = document.getElementById('console-output');
  if (!consoleOutput) return;
  
  // Add progress bar to console
  const progressBar = document.createElement('div');
  progressBar.id = 'execution-progress';
  progressBar.className = 'progress-bar';
  progressBar.innerHTML = '<div class="progress-fill" style="width: 0%"></div>';
  consoleOutput.appendChild(progressBar);
  
  // Update progress every second
  progressInterval = setInterval(() => {
    if (executionStartTime) {
      const elapsed = Date.now() - executionStartTime;
      const progress = Math.min((elapsed / 30000) * 100, 95); // Max 95% until completion
      const progressFill = progressBar.querySelector('.progress-fill');
      if (progressFill) {
        progressFill.style.width = progress + '%';
      }
    }
  }, 1000);
}

function stopProgressIndicator() {
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }
  
  // Complete the progress bar
  const progressBar = document.getElementById('execution-progress');
  if (progressBar) {
    const progressFill = progressBar.querySelector('.progress-fill');
    if (progressFill) {
      progressFill.style.width = '100%';
      progressFill.style.background = 'linear-gradient(90deg, #34d399, #10b981)';
    }
    
    // Remove progress bar after 2 seconds
    setTimeout(() => {
      if (progressBar && progressBar.parentNode) {
        progressBar.parentNode.removeChild(progressBar);
      }
    }, 2000);
  }
}

// Test Generation Loader Functions
function showTestGenerationLoader() {
  const loader = document.getElementById('test-generation-loader');
  const testcasesSection = document.getElementById('testcases-section');
  
  if (loader && testcasesSection) {
    // Show the testcases section and loader
    testcasesSection.style.display = 'block';
    loader.style.display = 'block';
    
    // Reset progress
    currentStep = 0;
    updateGenerationProgress(0);
    
    // Start the step animation
    startGenerationStepAnimation();
    
    // Start progress simulation
    startGenerationProgressSimulation();
  }
}

function hideTestGenerationLoader() {
  const loader = document.getElementById('test-generation-loader');
  
  if (loader) {
    // Complete all steps
    completeAllSteps();
    
    // Hide loader after a short delay
    setTimeout(() => {
      loader.style.display = 'none';
    }, 1000);
  }
  
  // Clear progress interval
  if (generationProgressInterval) {
    clearInterval(generationProgressInterval);
    generationProgressInterval = null;
  }
}

function startGenerationStepAnimation() {
  const steps = document.querySelectorAll('.loader-steps .step');
  
  // Reset all steps
  steps.forEach((step, index) => {
    step.classList.remove('active', 'completed');
    if (index === 0) {
      step.classList.add('active');
    }
  });
  
  // Animate through steps
  const stepInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      // Mark current step as completed
      steps[currentStep].classList.remove('active');
      steps[currentStep].classList.add('completed');
      
      // Move to next step
      currentStep++;
      steps[currentStep].classList.add('active');
    } else {
      // All steps completed
      clearInterval(stepInterval);
    }
  }, 30000); // Change step every 30 seconds (adjust based on actual generation time)
}

function completeAllSteps() {
  const steps = document.querySelectorAll('.loader-steps .step');
  steps.forEach(step => {
    step.classList.remove('active');
    step.classList.add('completed');
  });
}

function startGenerationProgressSimulation() {
  const progressFill = document.getElementById('generation-progress');
  let progress = 0;
  
  generationProgressInterval = setInterval(() => {
    progress += Math.random() * 2; // Random progress increment
    
    if (progress > 95) {
      progress = 95; // Don't complete until actual generation is done
    }
    
    if (progressFill) {
      progressFill.style.width = progress + '%';
    }
  }, 1000);
}

function updateGenerationProgress(percentage) {
  const progressFill = document.getElementById('generation-progress');
  if (progressFill) {
    progressFill.style.width = percentage + '%';
  }
}

function monitorGenerationCompletion() {
  // Check for completion every 5 seconds
  const checkInterval = setInterval(() => {
    // Check if the page has been redirected (which happens when generation completes)
    // or if we can detect completion through other means
    
    // For now, we'll use a timeout as fallback
    // In a real implementation, you might want to poll an API endpoint
    // or use WebSockets to get real-time updates
    
  }, 5000);
  
  // Fallback: complete after 2.5 minutes
  setTimeout(() => {
    clearInterval(checkInterval);
    completeTestGeneration();
  }, 150000); // 2.5 minutes
}

function completeTestGeneration() {
  hideTestGenerationLoader();
  updateGenerationProgress(100);
  
  // Show View Testcases button
  const viewBtn = document.getElementById('view-testcases-btn');
  if (viewBtn) {
    viewBtn.style.display = 'block';
  }
  
  // Show success message
  const notice = document.createElement('div');
  notice.className = 'notice success';
  notice.innerHTML = `<i class="fas fa-check-circle"></i> Test cases generated successfully! You can now view them below.`;
  document.querySelector('h1').insertAdjacentElement('afterend', notice);
  
  // Auto-remove notice after 5 seconds
  setTimeout(() => {
    notice.remove();
  }, 5000);
}

// Enhanced form submissions
document.addEventListener('DOMContentLoaded', function() {
  // Check for active tab parameter in URL and switch to it
  const urlParams = new URLSearchParams(window.location.search);
  const activeTab = urlParams.get('tab');
  if (activeTab) {
    const tabId = 'tab-' + activeTab;
    const tabElement = document.getElementById(tabId);
    if (tabElement) {
      // Remove active class from all tabs
      document.querySelectorAll('.tab').forEach(t => {
        t.classList.remove('active');
        t.style.opacity = '0';
      });
      
      // Add active class to the specified tab
      setTimeout(() => {
        tabElement.classList.add('active');
        tabElement.style.opacity = '1';
        
        // Start console polling if switching to console tab
        if (activeTab === 'console') {
          startConsolePolling();
        }
      }, 150);
    }
  }
  // Add loading to all form submissions
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        let executionType = null;
        
        // Determine execution type based on form
        if (form.id === 'generate-form') {
          executionType = 'generate';
          setExecutionState(true, 'generate');
          showTestGenerationLoader();
        } else if (form.action.includes('run-positive')) {
          executionType = 'positive';
          setExecutionState(true, 'positive');
        } else if (form.action.includes('run-all-tests')) {
          executionType = 'all';
          setExecutionState(true, 'all');
        }
        
        const hideLoading = showLoading(submitButton, executionType ? 'Running...' : 'Processing...');
        
        // Auto-switch to console tab for execution (but not for test generation)
        if (executionType && executionType !== 'generate') {
          setTimeout(() => {
            selectTab({preventDefault: () => {}}, 'tab-console');
          }, 500);
        }
        
        // Hide loading after 3 seconds (in case redirect is slow)
        setTimeout(hideLoading, 3000);
        
        // Show View Testcases button after generation
        if (form.id === 'generate-form') {
          // Monitor for generation completion
          monitorGenerationCompletion();
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
  
  // Debug log to help identify issues
  console.log(`Selected endpoints: ${Array.from(selectedEndpoints).join(', ')} (${selectedEndpoints.size} total)`);
  
  updateRunButton();
}

function updateRunButton() {
  const runBtn = document.getElementById('run-endpoints-btn');
  const countSpan = document.getElementById('selected-count');
  
  const count = selectedEndpoints.size;
  
  console.log(`Updating button: count=${count}, countSpan exists=${!!countSpan}`);
  
  // Update the count in the span
  if (countSpan) {
    countSpan.textContent = count;
    console.log(`Updated countSpan textContent to: ${countSpan.textContent}`);
  } else {
    console.error('countSpan element not found!');
  }
  
  // Update button state
  if (count > 0) {
    runBtn.disabled = false;
  } else {
    runBtn.disabled = true;
  }
}

function runSelectedEndpoints() {
  if (selectedEndpoints.size === 0) {
    alert('Please select at least one endpoint to test.');
    return;
  }
  
  if (isExecutionRunning) {
    alert('Another test execution is already running. Please wait for it to complete.');
    return;
  }
  
  const runBtn = document.getElementById('run-endpoints-btn');
  const endpointIds = Array.from(selectedEndpoints);
  
  // Set execution state
  setExecutionState(true, 'individual');
  
  // Show loading state
  const hideLoading = showLoading(runBtn, 'Running Tests...');
  
  // Update existing notice to show "Running individual tests"
  let existingNotice = document.querySelector('.notice');
  if (!existingNotice) {
    // Create notice element if it doesn't exist
    existingNotice = document.createElement('div');
    existingNotice.className = 'notice';
    document.querySelector('h1').insertAdjacentElement('afterend', existingNotice);
  }
  existingNotice.className = 'notice info';
  existingNotice.innerHTML = `<i class="fas fa-play"></i> Running individual tests`;
  
  // Navigate to console tab
  setTimeout(() => {
    selectTab({preventDefault: () => {}}, 'tab-console');
  }, 500);
  
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
    if (data.error) {
      alert('Error: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error running endpoints:', error);
    alert('Error running endpoints: ' + error.message);
  })
  .finally(() => {
    // Restore button state
    hideLoading();
    setExecutionState(false);
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

// AI Reports Functions
let currentAnalysisData = null;

function generateAIAnalysis() {
  const loader = document.getElementById('ai-analysis-loader');
  const generateBtn = document.getElementById('generate-analysis-btn');
  
  // Show loader and disable button
  loader.style.display = 'block';
  generateBtn.disabled = true;
  generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
  
  // Hide previous results
  hideAnalysisResults();
  
  // Start step animation
  startAnalysisStepAnimation();
  
  // Fetch AI analysis
  fetch('/api/ai-reports/analysis')
    .then(response => response.json())
    .then(data => {
      currentAnalysisData = data;
      displayAnalysisResults(data);
      hideLoader();
      showActionButtons();
    })
    .catch(error => {
      console.error('Error generating AI analysis:', error);
      hideLoader();
      showError('Failed to generate AI analysis. Please try again.');
    });
}

function regenerateAIAnalysis() {
  const loader = document.getElementById('ai-analysis-loader');
  const regenerateBtn = document.getElementById('regenerate-analysis-btn');
  
  // Show loader and disable button
  loader.style.display = 'block';
  regenerateBtn.disabled = true;
  regenerateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Regenerating...';
  
  // Start step animation
  startAnalysisStepAnimation();
  
  // Fetch regenerated analysis
  fetch('/api/ai-reports/regenerate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({})
  })
    .then(response => response.json())
    .then(data => {
      currentAnalysisData = data;
      displayAnalysisResults(data);
      hideLoader();
      showActionButtons();
    })
    .catch(error => {
      console.error('Error regenerating AI analysis:', error);
      hideLoader();
      showError('Failed to regenerate AI analysis. Please try again.');
    });
}

function startAnalysisStepAnimation() {
  const steps = document.querySelectorAll('.analysis-steps .step');
  let currentStep = 0;
  
  // Reset all steps
  steps.forEach((step, index) => {
    step.classList.remove('active');
    if (index === 0) {
      step.classList.add('active');
    }
  });
  
  // Animate through steps
  const stepInterval = setInterval(() => {
    if (currentStep < steps.length - 1) {
      steps[currentStep].classList.remove('active');
      currentStep++;
      steps[currentStep].classList.add('active');
    } else {
      clearInterval(stepInterval);
    }
  }, 2000); // Change step every 2 seconds
}

function hideLoader() {
  const loader = document.getElementById('ai-analysis-loader');
  const generateBtn = document.getElementById('generate-analysis-btn');
  const regenerateBtn = document.getElementById('regenerate-analysis-btn');
  
  loader.style.display = 'none';
  generateBtn.disabled = false;
  generateBtn.innerHTML = '<i class="fas fa-robot"></i> Generate Analysis';
  regenerateBtn.disabled = false;
  regenerateBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Regenerate Analysis';
}

function hideAnalysisResults() {
  const sections = [
    'summary-metrics',
    'charts-section', 
    'failed-tests-details',
    'endpoint-stability',
    'schema-issues',
    'ai-insights'
  ];
  
  sections.forEach(sectionId => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.style.display = 'none';
    }
  });
}

function displayAnalysisResults(data) {
  // Display summary metrics
  displaySummaryMetrics(data.summary_metrics);
  
  // Display charts
  displayCharts(data);
  
  // Display AI insights
  displayAIInsights(data.ai_insights);
  
  // Display endpoint stability
  displayEndpointStability(data.endpoint_stability);
  
  // Display schema issues
  displaySchemaIssues(data.schema_issues);
  
  // Display failed tests details
  displayFailedTestsDetails(data.failed_tests_details);
  
  // Show all sections
  showAnalysisResults();
}

function displaySummaryMetrics(metrics) {
  document.getElementById('total-tests').textContent = metrics.total_tests || 0;
  document.getElementById('passed-tests').textContent = metrics.passed_tests || 0;
  document.getElementById('failed-tests').textContent = metrics.failed_tests || 0;
  document.getElementById('pass-rate').textContent = `${metrics.pass_rate || 0}%`;
}

function displayCharts(data) {
  // Simple chart placeholder - in a real implementation, you'd use Chart.js or similar
  const passFailChart = document.getElementById('pass-fail-chart');
  
  // Pass/Fail Chart - Create a single pie chart
  const totalTests = data.summary_metrics.total_tests || 0;
  const passedTests = data.summary_metrics.passed_tests || 0;
  const failedTests = data.summary_metrics.failed_tests || 0;
  
  if (totalTests > 0) {
    const passPercentage = Math.round((passedTests / totalTests) * 100);
    const failPercentage = Math.round((failedTests / totalTests) * 100);
    
    // Create SVG pie chart using paths
    const radius = 80;
    const centerX = 90;
    const centerY = 90;
    
    // Calculate angles for pie segments
    const passAngle = (passPercentage / 100) * 360;
    const failAngle = (failPercentage / 100) * 360;
    
    // Helper function to create arc path
    function createArcPath(startAngle, endAngle) {
      const start = polarToCartesian(centerX, centerY, radius, endAngle);
      const end = polarToCartesian(centerX, centerY, radius, startAngle);
      const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
      return `M ${centerX} ${centerY} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
    }
    
    function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
      const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
      return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
      };
    }
    
    // Create paths for each segment
    const passPath = createArcPath(0, passAngle);
    const failPath = createArcPath(passAngle, passAngle + failAngle);
    
    passFailChart.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; height: 100%; gap: 40px;">
        <div style="position: relative; width: 180px; height: 180px;">
          <svg width="180" height="180">
            <!-- Passed tests segment -->
            <path d="${passPath}" fill="url(#passGradient)" stroke="#fff" stroke-width="2"/>
            <!-- Failed tests segment -->
            <path d="${failPath}" fill="url(#failGradient)" stroke="#fff" stroke-width="2"/>
            <!-- Gradients -->
            <defs>
              <linearGradient id="passGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#34d399;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
              </linearGradient>
              <linearGradient id="failGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#f87171;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#ef4444;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
          <!-- Center text -->
          <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #1f2937;">${totalTests}</div>
            <div style="font-size: 12px; color: #6b7280;">Total Tests</div>
          </div>
        </div>
        <!-- Legend -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 16px; height: 16px; border-radius: 50%; background: linear-gradient(135deg, #34d399, #10b981);"></div>
            <div>
              <div style="font-weight: 600; color: #1f2937;">Passed</div>
              <div style="font-size: 14px; color: #6b7280;">${passedTests} tests (${passPercentage}%)</div>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 16px; height: 16px; border-radius: 50%; background: linear-gradient(135deg, #f87171, #ef4444);"></div>
            <div>
              <div style="font-weight: 600; color: #1f2937;">Failed</div>
              <div style="font-size: 14px; color: #6b7280;">${failedTests} tests (${failPercentage}%)</div>
            </div>
          </div>
        </div>
      </div>
    `;
  } else {
    passFailChart.innerHTML = '<div>No test data available</div>';
  }
  
}

function displayAIInsights(insights) {
  document.getElementById('ai-narrative').textContent = insights.narrative || 'No analysis available';
  
  const recommendationsList = document.getElementById('ai-recommendations');
  recommendationsList.innerHTML = '';
  
  if (insights.recommendations && insights.recommendations.length > 0) {
    insights.recommendations.forEach(recommendation => {
      const li = document.createElement('li');
      li.textContent = recommendation;
      recommendationsList.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'No specific recommendations available';
    recommendationsList.appendChild(li);
  }
  
  const fixesContainer = document.getElementById('ai-suggested-fixes');
  fixesContainer.innerHTML = '';
  
  if (insights.suggested_fixes && insights.suggested_fixes.length > 0) {
    insights.suggested_fixes.forEach(fix => {
      const fixDiv = document.createElement('div');
      fixDiv.style.cssText = 'padding: 16px; margin-bottom: 12px; background: rgba(255,255,255,0.5); border-radius: 12px; border-left: 4px solid #667eea;';
      fixDiv.innerHTML = `
        <div style="font-weight: 600; color: #374151; margin-bottom: 8px;">${fix.issue || 'Issue'}</div>
        <div style="color: #6b7280; margin-bottom: 8px;">${fix.fix || 'Fix'}</div>
        <span class="priority-tag priority-${(fix.priority || 'medium').toLowerCase()}" style="font-size: 10px;">${fix.priority || 'Medium'}</span>
      `;
      fixesContainer.appendChild(fixDiv);
    });
  } else {
    fixesContainer.innerHTML = '<div style="color: #6b7280; text-align: center; padding: 20px;">No suggested fixes available</div>';
  }
}

function displayEndpointStability(endpoints) {
  const tbody = document.getElementById('stability-table-body');
  tbody.innerHTML = '';
  
  if (endpoints && endpoints.length > 0) {
    endpoints.forEach(endpoint => {
      const row = document.createElement('tr');
      
      // Format endpoint URL for better readability
      const endpointUrl = endpoint.endpoint || 'Unknown';
      const formattedUrl = endpointUrl.length > 50 ? 
        endpointUrl.substring(0, 47) + '...' : endpointUrl;
      
      // Get failure rate styling class
      const failureRate = endpoint.failure_rate || 0;
      let failureRateClass = 'failure-rate-low';
      if (failureRate > 30) {
        failureRateClass = 'failure-rate-high';
      } else if (failureRate > 10) {
        failureRateClass = 'failure-rate-medium';
      }
      
      // Format common issues for better display
      const commonIssues = endpoint.common_issues || [];
      const formattedIssues = commonIssues.length > 0 ? 
        commonIssues.slice(0, 2).join(', ') + (commonIssues.length > 2 ? '...' : '') : 
        'No issues detected';
      
      row.innerHTML = `
        <td title="${endpointUrl}">${formattedUrl}</td>
        <td><span style="background: #e0f2fe; color: #0277bd; padding: 4px 8px; border-radius: 6px; font-weight: 600;">${endpoint.total_tests || 0}</span></td>
        <td><span style="background: #ffebee; color: #c62828; padding: 4px 8px; border-radius: 6px; font-weight: 600;">${endpoint.failed_tests || 0}</span></td>
        <td><span class="${failureRateClass}">${failureRate}%</span></td>
        <td><span class="priority-tag priority-${(endpoint.priority || 'minor').toLowerCase()}">${endpoint.priority || 'Minor'}</span></td>
        <td title="${commonIssues.join(', ')}">${formattedIssues}</td>
      `;
      tbody.appendChild(row);
    });
  } else {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td colspan="6" style="text-align: center; color: #6b7280; padding: 40px; font-style: italic;">
        <i class="fas fa-info-circle" style="margin-right: 8px;"></i>
        No endpoint stability data available
      </td>
    `;
    tbody.appendChild(row);
  }
}

function displaySchemaIssues(issues) {
  const tbody = document.getElementById('schema-table-body');
  tbody.innerHTML = '';
  
  if (issues && issues.length > 0) {
    issues.forEach(issue => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td style="font-family: monospace; font-weight: 500;">${issue.endpoint || 'Unknown'}</td>
        <td>${issue.issue_type || 'Unknown'}</td>
        <td>${issue.field_name || 'N/A'}</td>
        <td>${issue.expected_type || 'N/A'}</td>
        <td>${issue.actual_type || 'N/A'}</td>
        <td>${issue.description || 'No description'}</td>
      `;
      tbody.appendChild(row);
    });
  } else {
    const row = document.createElement('tr');
    row.innerHTML = '<td colspan="6" style="text-align: center; color: #6b7280; padding: 20px;">No schema issues found</td>';
    tbody.appendChild(row);
  }
}

function displayFailedTestsDetails(failedTestsData) {
  if (!failedTestsData) return;
  
  // Update summary stats
  document.getElementById('total-failed-count').textContent = failedTestsData.total_failed_count || 0;
  document.getElementById('most-common-error').textContent = failedTestsData.most_common_error || 'None';
  
  // Calculate overall failure rate
  const totalTests = parseInt(document.getElementById('total-tests').textContent) || 0;
  const failedCount = failedTestsData.total_failed_count || 0;
  const failureRate = totalTests > 0 ? Math.round((failedCount / totalTests) * 100) : 0;
  document.getElementById('overall-failure-rate').textContent = `${failureRate}%`;
  
  // Display failed tests table
  const tbody = document.getElementById('failed-tests-table-body');
  tbody.innerHTML = '';
  
  if (failedTestsData.failed_tests && failedTestsData.failed_tests.length > 0) {
    failedTestsData.failed_tests.forEach(test => {
      const row = document.createElement('tr');
      
      // Format timestamp
      const timestamp = test.timestamp ? new Date(test.timestamp).toLocaleString() : 'Unknown';
      
      // Get error type class
      const errorTypeClass = getErrorTypeClass(test.error_type);
      
      // Format failure reason for better display
      const failureReason = test.failure_reason || 'No reason provided';
      const formattedReason = formatFailureReason(failureReason);
      
      row.innerHTML = `
        <td style="font-weight: 500;">${test.test_name || 'Unknown'}</td>
        <td style="font-family: monospace; font-size: 12px;">${test.endpoint || 'Unknown'}</td>
        <td><span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${test.method || 'Unknown'}</span></td>
        <td><span class="status-expected">${test.expected_status || 0}</span></td>
        <td><span class="status-actual">${test.actual_status || 0}</span></td>
        <td><span class="${errorTypeClass}">${test.error_type || 'Unknown'}</span></td>
        <td class="failure-reason-cell">${formattedReason}</td>
        <td class="timestamp">${timestamp}</td>
      `;
      tbody.appendChild(row);
    });
  } else {
    const row = document.createElement('tr');
    row.innerHTML = '<td colspan="8" style="text-align: center; color: #6b7280; padding: 20px;">No failed tests found</td>';
    tbody.appendChild(row);
  }
}

function getErrorTypeClass(errorType) {
  switch (errorType.toLowerCase()) {
    case 'authentication':
      return 'error-type-auth';
    case 'server error':
      return 'error-type-server';
    case 'validation':
      return 'error-type-validation';
    case 'timeout':
      return 'error-type-timeout';
    default:
      return 'error-type-other';
  }
}

function formatFailureReason(reason) {
  if (!reason || reason === 'No reason provided') {
    return '<span style="color: #6b7280; font-style: italic;">No detailed reason available</span>';
  }
  
  // Split the reason into parts for better formatting
  const parts = reason.split(': ');
  if (parts.length >= 2) {
    const title = parts[0]; // The emoji and title part
    const description = parts.slice(1).join(': '); // The rest of the description
    
    return `
      <div class="failure-reason-content">
        <div class="failure-reason-title">${title}</div>
        <div class="failure-reason-description">${description}</div>
      </div>
    `;
  }
  
  // Fallback for simple reasons
  return `<div class="failure-reason-simple">${reason}</div>`;
}

function showAnalysisResults() {
  const sections = [
    'summary-metrics',
    'charts-section', 
    'failed-tests-details',
    'endpoint-stability',
    'schema-issues',
    'ai-insights'
  ];
  
  sections.forEach((sectionId, index) => {
    const section = document.getElementById(sectionId);
    if (section) {
      setTimeout(() => {
        section.style.display = 'block';
        section.style.animation = 'fadeIn 0.5s ease';
      }, index * 200); // Stagger the animations
    }
  });
}

function showActionButtons() {
  document.getElementById('regenerate-analysis-btn').style.display = 'inline-flex';
  document.getElementById('export-report-btn').style.display = 'inline-flex';
}

function exportReport() {
  if (!currentAnalysisData) {
    showError('No analysis data available to export');
    return;
  }
  
  // Create a simple text report
  const report = generateTextReport(currentAnalysisData);
  
  // Download as text file
  const blob = new Blob([report], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ai-analysis-report-${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

function generateTextReport(data) {
  const metrics = data.summary_metrics || {};
  const insights = data.ai_insights || {};
  
  return `
AI Analysis Report
Generated: ${new Date().toLocaleString()}

SUMMARY METRICS
===============
Total Tests: ${metrics.total_tests || 0}
Passed Tests: ${metrics.passed_tests || 0}
Failed Tests: ${metrics.failed_tests || 0}
Pass Rate: ${metrics.pass_rate || 0}%

AI INSIGHTS
===========
${insights.narrative || 'No analysis available'}

RECOMMENDATIONS
===============
${(insights.recommendations || []).map((rec, i) => `${i + 1}. ${rec}`).join('\n')}

SUGGESTED FIXES
===============
${(insights.suggested_fixes || []).map((fix, i) => `${i + 1}. ${fix.issue || 'Issue'}: ${fix.fix || 'Fix'} (Priority: ${fix.priority || 'Medium'})`).join('\n')}

ENDPOINT STABILITY
==================
${(data.endpoint_stability || []).map(ep => `${ep.endpoint}: ${ep.failure_rate}% failure rate (${ep.priority})`).join('\n')}

SCHEMA ISSUES
=============
${(data.schema_issues || []).map(issue => `${issue.endpoint}: ${issue.issue_type} - ${issue.field_name} (Expected: ${issue.expected_type}, Actual: ${issue.actual_type})`).join('\n')}
  `.trim();
}

function showError(message) {
  const notice = document.createElement('div');
  notice.className = 'notice error';
  notice.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
  document.querySelector('h1').insertAdjacentElement('afterend', notice);
  
  setTimeout(() => {
    notice.remove();
  }, 5000);
}

//Reports functionality
function loadAllureReport() {
  const iframe = document.getElementById('allure-frame');
  // Try to build the report on demand, then load it
  fetch('/api/build-allure', { method: 'POST' })
    .then(r => r.json())
    .then(res => {
      if (res.status === 'ok' && res.report_path) {
        iframe.src = res.report_path + '?t=' + Date.now(); // bust cache
      } else if (res.status === 'no_results') {
        iframe.srcdoc = '<div style="padding:16px;color:#6b7280;">No allure-results found yet. Run tests first.</div>';
      } else if (res.status === 'cli_missing') {
        iframe.srcdoc = '<div style="padding:16px;color:#b91c1c;">Allure CLI not found. Please install Allure on the host machine.</div>';
      } else {
        const msg = (res && res.message) ? res.message : 'Failed to build Allure report';
        iframe.srcdoc = `<div style="padding:16px;color:#b91c1c;">${msg}</div>`;
      }
      selectTab({ preventDefault: () => {} }, 'tab-reports');
    })
    .catch(err => {
      iframe.srcdoc = '<div style="padding:16px;color:#b91c1c;">Error building Allure report.</div>';
      selectTab({ preventDefault: () => {} }, 'tab-reports');
    });
}



