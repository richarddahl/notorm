/**
 * Report Execution View Component
 * 
 * Displays the status and results of a report execution.
 */
class ReportExecutionView extends LitElement {
  static properties = {
    executionId: { type: String },
    execution: { type: Object },
    template: { type: Object },
    loading: { type: Boolean },
    error: { type: String },
    refreshInterval: { type: Number }
  };

  constructor() {
    super();
    this.executionId = null;
    this.execution = null;
    this.template = null;
    this.loading = true;
    this.error = null;
    this.refreshInterval = null;
  }

  connectedCallback() {
    super.connectedCallback();
    // Extract execution ID from URL
    const url = new URL(window.location.href);
    const pathParts = url.pathname.split('/');
    const executionsIndex = pathParts.indexOf('executions');
    if (executionsIndex !== -1 && executionsIndex + 1 < pathParts.length) {
      this.executionId = pathParts[executionsIndex + 1];
      this.loadExecution();
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  async loadExecution() {
    if (!this.executionId) return;
    
    try {
      this.loading = true;
      const response = await fetch(`/api/reports/executions/${this.executionId}`);
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      this.execution = await response.json();
      
      // Load the template
      if (this.execution.report_template_id) {
        await this.loadTemplate(this.execution.report_template_id);
      }
      
      // Set up polling for pending/running executions
      if (this.execution.status === 'pending' || this.execution.status === 'in_progress') {
        this.refreshInterval = setInterval(() => this.loadExecution(), 5000);
      } else if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }
      
      this.error = null;
    } catch (err) {
      this.error = err.message;
      console.error('Error loading execution:', err);
    } finally {
      this.loading = false;
    }
  }

  async loadTemplate(templateId) {
    try {
      const response = await fetch(`/api/reports/templates/${templateId}`);
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      this.template = await response.json();
    } catch (err) {
      console.error('Error loading template:', err);
    }
  }

  async downloadResult(format = 'csv') {
    try {
      const response = await fetch(`/api/reports/executions/${this.executionId}/result?format=${format}`);
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      // Handle the download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `report-${this.executionId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading result:', err);
      alert(`Failed to download result: ${err.message}`);
    }
  }

  getStatusBadgeClass(status) {
    switch (status) {
      case 'completed': return 'badge-success';
      case 'failed': return 'badge-danger';
      case 'canceled': return 'badge-warning';
      case 'in_progress': return 'badge-primary';
      case 'pending': return 'badge-secondary';
      default: return 'badge-info';
    }
  }

  formatDuration(startTime, endTime) {
    if (!startTime || !endTime) return 'N/A';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;
    
    // Format as mm:ss or hh:mm:ss
    const seconds = Math.floor((durationMs / 1000) % 60);
    const minutes = Math.floor((durationMs / (1000 * 60)) % 60);
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    
    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
  }

  render() {
    if (this.loading && !this.execution) {
      return html`<div class="loading">Loading execution details...</div>`;
    }

    if (this.error) {
      return html`
        <div class="error">
          <p>Error loading execution: ${this.error}</p>
          <button @click=${this.loadExecution}>Try Again</button>
        </div>
      `;
    }

    if (!this.execution) {
      return html`<div class="not-found">Execution not found</div>`;
    }

    return html`
      <div class="report-execution">
        <div class="header">
          <h2>
            ${this.template ? this.template.name : 'Report'} Execution
            <span class="badge ${this.getStatusBadgeClass(this.execution.status)}">
              ${this.execution.status}
            </span>
          </h2>
          <div class="actions">
            <a href="/reports/templates/${this.execution.report_template_id}" class="btn btn-secondary">
              Back to Template
            </a>
            ${this.execution.status === 'completed' ? html`
              <div class="dropdown">
                <button class="btn btn-primary dropdown-toggle">Download</button>
                <div class="dropdown-menu">
                  <a @click=${() => this.downloadResult('csv')} class="dropdown-item">CSV</a>
                  <a @click=${() => this.downloadResult('json')} class="dropdown-item">JSON</a>
                  <a @click=${() => this.downloadResult('pdf')} class="dropdown-item">PDF</a>
                  <a @click=${() => this.downloadResult('excel')} class="dropdown-item">Excel</a>
                </div>
              </div>
            ` : ''}
          </div>
        </div>
        
        <div class="execution-details">
          <div class="card">
            <div class="card-header">Execution Details</div>
            <div class="card-body">
              <dl>
                <dt>Execution ID</dt>
                <dd>${this.execution.id}</dd>
                
                <dt>Status</dt>
                <dd>
                  <span class="badge ${this.getStatusBadgeClass(this.execution.status)}">
                    ${this.execution.status}
                  </span>
                </dd>
                
                <dt>Started</dt>
                <dd>${new Date(this.execution.started_at).toLocaleString()}</dd>
                
                ${this.execution.completed_at ? html`
                  <dt>Completed</dt>
                  <dd>${new Date(this.execution.completed_at).toLocaleString()}</dd>
                  
                  <dt>Duration</dt>
                  <dd>${this.formatDuration(this.execution.started_at, this.execution.completed_at)}</dd>
                ` : ''}
                
                <dt>Triggered By</dt>
                <dd>${this.execution.triggered_by}</dd>
                
                <dt>Trigger Type</dt>
                <dd>${this.execution.trigger_type}</dd>
                
                ${this.execution.row_count !== null ? html`
                  <dt>Result Rows</dt>
                  <dd>${this.execution.row_count.toLocaleString()}</dd>
                ` : ''}
                
                ${this.execution.execution_time_ms ? html`
                  <dt>Execution Time</dt>
                  <dd>${(this.execution.execution_time_ms / 1000).toFixed(2)} seconds</dd>
                ` : ''}
              </dl>
            </div>
          </div>
          
          ${Object.keys(this.execution.parameters || {}).length > 0 ? html`
            <div class="card">
              <div class="card-header">Parameters</div>
              <div class="card-body">
                <dl>
                  ${Object.entries(this.execution.parameters).map(([key, value]) => html`
                    <dt>${key}</dt>
                    <dd>${JSON.stringify(value)}</dd>
                  `)}
                </dl>
              </div>
            </div>
          ` : ''}
          
          ${this.execution.error_details ? html`
            <div class="card error-card">
              <div class="card-header">Error Details</div>
              <div class="card-body">
                <pre>${this.execution.error_details}</pre>
              </div>
            </div>
          ` : ''}
          
          ${this.execution.status === 'completed' && this.execution.output_executions ? html`
            <div class="card">
              <div class="card-header">Outputs</div>
              <div class="card-body">
                <table class="table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Format</th>
                      <th>Status</th>
                      <th>Location</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this.execution.output_executions.map(output => html`
                      <tr>
                        <td>${output.report_output.output_type}</td>
                        <td>${output.report_output.format}</td>
                        <td>
                          <span class="badge ${this.getStatusBadgeClass(output.status)}">
                            ${output.status}
                          </span>
                        </td>
                        <td>${output.output_location || 'N/A'}</td>
                      </tr>
                    `)}
                  </tbody>
                </table>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  static styles = css`
    .report-execution {
      padding: 1rem;
    }
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    .badge {
      display: inline-block;
      padding: 0.25em 0.4em;
      font-size: 75%;
      font-weight: 700;
      line-height: 1;
      text-align: center;
      white-space: nowrap;
      vertical-align: baseline;
      border-radius: 0.25rem;
      color: white;
    }
    
    .badge-success {
      background-color: #28a745;
    }
    
    .badge-danger {
      background-color: #dc3545;
    }
    
    .badge-warning {
      background-color: #ffc107;
      color: #212529;
    }
    
    .badge-primary {
      background-color: #007bff;
    }
    
    .badge-secondary {
      background-color: #6c757d;
    }
    
    .badge-info {
      background-color: #17a2b8;
    }
    
    .actions {
      display: flex;
      gap: 0.5rem;
    }
    
    .execution-details {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
      gap: 1rem;
    }
    
    .card {
      border: 1px solid rgba(0, 0, 0, 0.125);
      border-radius: 0.25rem;
      margin-bottom: 1rem;
    }
    
    .card-header {
      padding: 0.75rem 1.25rem;
      background-color: rgba(0, 0, 0, 0.03);
      border-bottom: 1px solid rgba(0, 0, 0, 0.125);
      font-weight: bold;
    }
    
    .card-body {
      padding: 1.25rem;
    }
    
    .error-card {
      border-color: #f5c6cb;
    }
    
    .error-card .card-header {
      background-color: #f8d7da;
      color: #721c24;
    }
    
    dl {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 0.5rem 1rem;
    }
    
    dt {
      font-weight: bold;
    }
    
    dd {
      margin-bottom: 0;
    }
    
    .btn {
      display: inline-block;
      padding: 0.375rem 0.75rem;
      border-radius: 0.25rem;
      text-decoration: none;
      cursor: pointer;
      border: none;
    }
    
    .btn-primary {
      background-color: #007bff;
      color: white;
    }
    
    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }
    
    .dropdown {
      position: relative;
      display: inline-block;
    }
    
    .dropdown-toggle::after {
      display: inline-block;
      margin-left: 0.255em;
      vertical-align: 0.255em;
      content: "";
      border-top: 0.3em solid;
      border-right: 0.3em solid transparent;
      border-bottom: 0;
      border-left: 0.3em solid transparent;
    }
    
    .dropdown-menu {
      position: absolute;
      top: 100%;
      left: 0;
      z-index: 1000;
      display: none;
      min-width: 10rem;
      padding: 0.5rem 0;
      margin: 0.125rem 0 0;
      background-color: white;
      border: 1px solid rgba(0, 0, 0, 0.15);
      border-radius: 0.25rem;
    }
    
    .dropdown:hover .dropdown-menu {
      display: block;
    }
    
    .dropdown-item {
      display: block;
      width: 100%;
      padding: 0.25rem 1.5rem;
      clear: both;
      text-align: inherit;
      white-space: nowrap;
      background-color: transparent;
      border: 0;
      cursor: pointer;
    }
    
    .dropdown-item:hover {
      background-color: #f8f9fa;
    }
    
    .table {
      width: 100%;
      border-collapse: collapse;
    }
    
    .table th, .table td {
      padding: 0.75rem;
      border-bottom: 1px solid #dee2e6;
    }
    
    .loading, .error, .not-found {
      padding: 2rem;
      text-align: center;
    }
    
    .error {
      color: red;
    }
    
    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      background-color: #f8f9fa;
      padding: 1rem;
      border-radius: 0.25rem;
      margin: 0;
    }
  `;
}

customElements.define('report-execution-view', ReportExecutionView);