/**
 * Endpoint Analyzer Component
 * 
 * A web component for analyzing HTTP endpoint performance
 */

import { formatDuration, formatNumber, getDurationClass } from './chart-loader.js';

// Import or use the LitElement base class
const LitElement = window.litElement?.LitElement || Object.getPrototypeOf(document.createElement('span')).constructor;
const html = window.litElement?.html || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));
const css = window.litElement?.css || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));

/**
 * Endpoint Analyzer
 * 
 * @element endpoint-analyzer
 * @attr {String} api-base-url - Base URL for API endpoints
 */
class EndpointAnalyzer extends LitElement {
  static get properties() {
    return {
      apiBaseUrl: { type: String, attribute: 'api-base-url' },
      data: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      analysisMode: { type: String },
      sortField: { type: String },
      sortOrder: { type: String },
      searchQuery: { type: String },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        width: 100%;
      }
      
      .card {
        background-color: white;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 16px;
        margin-bottom: 16px;
      }
      
      .card-title {
        font-size: 18px;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ddd;
      }
      
      .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      
      .tab-buttons {
        display: flex;
        gap: 8px;
      }
      
      button {
        cursor: pointer;
        padding: 8px 16px;
        background-color: var(--primary-color, #0078d7);
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 500;
        transition: background-color 0.2s;
      }
      
      button.secondary {
        background-color: #f0f0f0;
        color: #333;
      }
      
      button.active {
        background-color: var(--primary-color, #0078d7);
        color: white;
      }
      
      input[type="search"] {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        min-width: 250px;
      }
      
      table {
        width: 100%;
        border-collapse: collapse;
      }
      
      th, td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
      }
      
      th {
        font-weight: 600;
        background-color: #f5f5f5;
        cursor: pointer;
      }
      
      th.sortable:hover {
        background-color: #e5e5e5;
      }
      
      th.sorted {
        color: var(--primary-color, #0078d7);
      }
      
      .sort-icon {
        display: inline-block;
        width: 0;
        height: 0;
        margin-left: 4px;
        vertical-align: middle;
      }
      
      .sort-icon.asc {
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 6px solid currentColor;
      }
      
      .sort-icon.desc {
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid currentColor;
      }
      
      .success { color: #107c10; }
      .warning { color: #ff8c00; }
      .error { color: #e81123; }
      
      .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 2px solid rgba(0, 120, 212, 0.2);
        border-radius: 50%;
        border-top-color: var(--primary-color, #0078d7);
        animation: spin 1s ease-in-out infinite;
        margin-right: 8px;
      }
      
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      
      .tab-content {
        display: none;
      }
      
      .tab-content.active {
        display: block;
      }
      
      .badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        margin-left: 4px;
      }
      
      .badge.success { background-color: rgba(16, 124, 16, 0.1); }
      .badge.warning { background-color: rgba(255, 140, 0, 0.1); }
      .badge.error { background-color: rgba(232, 17, 35, 0.1); }
      
      .flex {
        display: flex;
      }
      
      .justify-between {
        justify-content: space-between;
      }
      
      .items-center {
        align-items: center;
      }
      
      .gap-2 {
        gap: 8px;
      }
      
      p.info {
        background-color: #f0f7ff;
        padding: 12px;
        border-radius: 4px;
        border-left: 4px solid #0078d7;
        margin-bottom: 16px;
      }
      
      .status-code {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      
      .status-chip {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        background-color: #f5f5f5;
        border-radius: 16px;
        font-size: 12px;
      }
      
      .status-chip.success { background-color: rgba(16, 124, 16, 0.1); }
      .status-chip.redirect { background-color: rgba(0, 120, 212, 0.1); }
      .status-chip.client-error { background-color: rgba(255, 140, 0, 0.1); }
      .status-chip.server-error { background-color: rgba(232, 17, 35, 0.1); }
      
      .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 4px;
      }
      
      .status-dot.success { background-color: #107c10; }
      .status-dot.redirect { background-color: #0078d7; }
      .status-dot.client-error { background-color: #ff8c00; }
      .status-dot.server-error { background-color: #e81123; }
      
      details {
        margin-bottom: 8px;
      }
      
      summary {
        cursor: pointer;
        padding: 8px;
        background-color: #f5f5f5;
        border-radius: 4px;
      }
      
      details[open] summary {
        margin-bottom: 8px;
      }
    `;
  }

  constructor() {
    super();
    this.apiBaseUrl = '/api';
    this.data = null;
    this.loading = false;
    this.error = null;
    this.analysisMode = 'overview';
    this.sortField = 'avg';
    this.sortOrder = 'desc';
    this.searchQuery = '';
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadData();
  }

  async loadData() {
    this.loading = true;
    this.error = null;

    try {
      const response = await fetch(`${this.apiBaseUrl}/metrics/endpoints?include_stats=true&include_slow=true&include_error_prone=true&limit=100`);
      if (!response.ok) {
        throw new Error(`Failed to load endpoint data: ${response.statusText}`);
      }
      this.data = await response.json();
    } catch (error) {
      console.error('Error loading data:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  setAnalysisMode(mode) {
    this.analysisMode = mode;
  }

  setSorting(field) {
    if (this.sortField === field) {
      // Toggle sort order if same field
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      // Set new field with default desc order
      this.sortField = field;
      this.sortOrder = 'desc';
    }
  }

  handleSearch(event) {
    this.searchQuery = event.target.value.trim().toLowerCase();
  }

  filterBySearch(items) {
    if (!this.searchQuery) {
      return items;
    }
    
    return items.filter(item => {
      const path = item.path.toLowerCase();
      const method = item.method.toLowerCase();
      
      return path.includes(this.searchQuery) || method.includes(this.searchQuery);
    });
  }

  getStatusCodeClass(code) {
    if (code >= 200 && code < 300) {
      return 'success';
    } else if (code >= 300 && code < 400) {
      return 'redirect';
    } else if (code >= 400 && code < 500) {
      return 'client-error';
    } else {
      return 'server-error';
    }
  }

  getSortIcon(field) {
    if (this.sortField !== field) {
      return '';
    }
    
    return html`<span class="sort-icon ${this.sortOrder}"></span>`;
  }

  render() {
    return html`
      <div class="card">
        <h2 class="card-title">Endpoint Performance Analysis</h2>
        
        <div class="controls">
          <div class="tab-buttons">
            <button class="${this.analysisMode === 'overview' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('overview')}>
              Overview
            </button>
            <button class="${this.analysisMode === 'slow' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('slow')}>
              Slow Endpoints
            </button>
            <button class="${this.analysisMode === 'errors' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('errors')}>
              Error Prone
            </button>
          </div>
          
          <div class="flex items-center gap-2">
            ${this.loading ? html`<div class="loading-spinner"></div> Loading...` : 
              html`<button @click=${this.loadData}>Refresh</button>`}
          </div>
        </div>
        
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        
        ${this.data ? html`
          <div class="flex justify-between items-center">
            <div>
              <strong>Total Requests:</strong> ${formatNumber(this.data.total_requests)} | 
              <strong>Unique Endpoints:</strong> ${formatNumber(this.data.total_endpoints)}
            </div>
            
            <div>
              <input type="search" placeholder="Search by path or method..." @input=${this.handleSearch}>
            </div>
          </div>
          
          <div class="tab-content ${this.analysisMode === 'overview' ? 'active' : ''}">
            ${this.renderOverview()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'slow' ? 'active' : ''}">
            ${this.renderSlowEndpoints()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'errors' ? 'active' : ''}">
            ${this.renderErrorProneEndpoints()}
          </div>
        ` : html`
          <p>Loading endpoint data...</p>
        `}
      </div>
    `;
  }

  renderOverview() {
    if (!this.data.endpoint_stats || Object.keys(this.data.endpoint_stats).length === 0) {
      return html`<p>No endpoint statistics available</p>`;
    }
    
    // Convert to array for filtering and sorting
    let endpointStats = Object.entries(this.data.endpoint_stats).map(([key, stats]) => {
      return {
        key,
        ...stats
      };
    });
    
    // Filter by search query
    endpointStats = this.filterBySearch(endpointStats);
    
    // Sort based on current sort field and order
    endpointStats.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          This overview shows all monitored HTTP endpoints and their performance metrics.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'method' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('method')}>
                Method ${this.getSortIcon('method')}
              </th>
              <th class="sortable ${this.sortField === 'path' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('path')}>
                Path ${this.getSortIcon('path')}
              </th>
              <th class="sortable ${this.sortField === 'count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('count')}>
                Requests ${this.getSortIcon('count')}
              </th>
              <th class="sortable ${this.sortField === 'avg' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('avg')}>
                Avg Duration ${this.getSortIcon('avg')}
              </th>
              <th class="sortable ${this.sortField === 'p95' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('p95')}>
                p95 ${this.getSortIcon('p95')}
              </th>
              <th>Status Codes</th>
              <th class="sortable ${this.sortField === 'last_accessed' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('last_accessed')}>
                Last Access ${this.getSortIcon('last_accessed')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${endpointStats.map(endpoint => html`
              <tr>
                <td>${endpoint.method}</td>
                <td>${endpoint.path}</td>
                <td>${formatNumber(endpoint.count)}</td>
                <td class="${getDurationClass(endpoint.avg)}">${formatDuration(endpoint.avg)}</td>
                <td class="${getDurationClass(endpoint.p95)}">${formatDuration(endpoint.p95)}</td>
                <td>
                  <div class="status-code">
                    ${Object.entries(endpoint.status_codes).map(([code, count]) => html`
                      <span class="status-chip ${this.getStatusCodeClass(code)}">
                        <span class="status-dot ${this.getStatusCodeClass(code)}"></span>
                        ${code}: ${count}
                      </span>
                    `)}
                  </div>
                </td>
                <td>${new Date(endpoint.last_accessed).toLocaleString()}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderSlowEndpoints() {
    if (!this.data.slow_endpoints || this.data.slow_endpoints.length === 0) {
      return html`<p class="success">No slow endpoints detected</p>`;
    }
    
    // Filter and sort slow endpoints
    let slowEndpoints = this.filterBySearch([...this.data.slow_endpoints]);
    
    // Sort based on current sort field and order
    slowEndpoints.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          Slow endpoints are HTTP endpoints with response times exceeding the configured threshold (typically 1 second).
          These can lead to poor user experience and increased server load.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'method' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('method')}>
                Method ${this.getSortIcon('method')}
              </th>
              <th class="sortable ${this.sortField === 'path' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('path')}>
                Path ${this.getSortIcon('path')}
              </th>
              <th class="sortable ${this.sortField === 'avg' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('avg')}>
                Avg Duration ${this.getSortIcon('avg')}
              </th>
              <th class="sortable ${this.sortField === 'max' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('max')}>
                Max Duration ${this.getSortIcon('max')}
              </th>
              <th class="sortable ${this.sortField === 'count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('count')}>
                Request Count ${this.getSortIcon('count')}
              </th>
              <th class="sortable ${this.sortField === 'query_count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('query_count')}>
                Avg Queries ${this.getSortIcon('query_count')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${slowEndpoints.map(endpoint => html`
              <tr>
                <td>${endpoint.method}</td>
                <td>${endpoint.path}</td>
                <td class="${getDurationClass(endpoint.avg)}">${formatDuration(endpoint.avg)}</td>
                <td class="${getDurationClass(endpoint.max)}">${formatDuration(endpoint.max)}</td>
                <td>${formatNumber(endpoint.count)}</td>
                <td>${endpoint.query_count !== undefined ? endpoint.query_count : 'N/A'}</td>
              </tr>
            `)}
          </tbody>
        </table>
        
        <div class="card">
          <h3>Optimization Tips</h3>
          <details>
            <summary>Database Optimizations</summary>
            <ul>
              <li>Check if endpoints are executing too many database queries (N+1 pattern)</li>
              <li>Add database indexes for frequently queried fields</li>
              <li>Use query caching for expensive or frequently executed queries</li>
              <li>Batch multiple database operations into fewer queries</li>
            </ul>
          </details>
          
          <details>
            <summary>Application Optimizations</summary>
            <ul>
              <li>Use data pagination instead of returning large datasets</li>
              <li>Implement response caching for endpoints with static data</li>
              <li>Optimize data serialization/deserialization process</li>
              <li>Consider adding asynchronous processing for heavy operations</li>
            </ul>
          </details>
          
          <details>
            <summary>Resource Optimizations</summary>
            <ul>
              <li>Check if server resources (CPU/memory) are sufficient</li>
              <li>Optimize memory usage in request handlers</li>
              <li>Consider horizontal scaling for high-traffic endpoints</li>
            </ul>
          </details>
        </div>
      </div>
    `;
  }

  renderErrorProneEndpoints() {
    if (!this.data.error_prone_endpoints || this.data.error_prone_endpoints.length === 0) {
      return html`<p class="success">No error-prone endpoints detected</p>`;
    }
    
    // Filter and sort error-prone endpoints
    let errorEndpoints = this.filterBySearch([...this.data.error_prone_endpoints]);
    
    // Sort based on current sort field and order
    errorEndpoints.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          Error-prone endpoints are HTTP endpoints with high error rates (4xx or 5xx responses).
          These may indicate issues with input validation, authorization, or internal server errors.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'method' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('method')}>
                Method ${this.getSortIcon('method')}
              </th>
              <th class="sortable ${this.sortField === 'path' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('path')}>
                Path ${this.getSortIcon('path')}
              </th>
              <th class="sortable ${this.sortField === 'error_rate' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('error_rate')}>
                Error Rate ${this.getSortIcon('error_rate')}
              </th>
              <th class="sortable ${this.sortField === 'error_count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('error_count')}>
                Error Count ${this.getSortIcon('error_count')}
              </th>
              <th class="sortable ${this.sortField === 'total_requests' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('total_requests')}>
                Total Requests ${this.getSortIcon('total_requests')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${errorEndpoints.map(endpoint => html`
              <tr>
                <td>${endpoint.method}</td>
                <td>${endpoint.path}</td>
                <td class="error">${(endpoint.error_rate * 100).toFixed(1)}%</td>
                <td>${endpoint.error_count}</td>
                <td>${endpoint.total_requests}</td>
              </tr>
            `)}
          </tbody>
        </table>
        
        <div class="card">
          <h3>Common Error Causes</h3>
          <details>
            <summary>4xx Client Errors</summary>
            <ul>
              <li><strong>400 Bad Request</strong>: Improve input validation and provide better error messages</li>
              <li><strong>401 Unauthorized</strong>: Check authentication flow and token handling</li>
              <li><strong>403 Forbidden</strong>: Review authorization rules and permissions</li>
              <li><strong>404 Not Found</strong>: Ensure resources exist or return proper fallbacks</li>
              <li><strong>429 Too Many Requests</strong>: Implement rate limiting with proper client feedback</li>
            </ul>
          </details>
          
          <details>
            <summary>5xx Server Errors</summary>
            <ul>
              <li><strong>500 Internal Server Error</strong>: Improve error handling and exception catching</li>
              <li><strong>502 Bad Gateway</strong>: Check downstream service connectivity</li>
              <li><strong>503 Service Unavailable</strong>: Ensure adequate resources and implement graceful degradation</li>
              <li><strong>504 Gateway Timeout</strong>: Optimize long-running operations or implement async processing</li>
            </ul>
          </details>
          
          <details>
            <summary>Recommendations</summary>
            <ul>
              <li>Review application logs for these endpoints to identify specific error causes</li>
              <li>Implement structured error responses with actionable messages</li>
              <li>Add more comprehensive error handling and recovery mechanisms</li>
              <li>Consider circuit breakers for dependent services</li>
              <li>Implement better request validation before processing</li>
            </ul>
          </details>
        </div>
      </div>
    `;
  }
}

// Define the custom element
if (!customElements.get('endpoint-analyzer')) {
  customElements.define('endpoint-analyzer', EndpointAnalyzer);
}