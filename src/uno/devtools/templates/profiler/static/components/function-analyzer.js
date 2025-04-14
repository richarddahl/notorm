/**
 * Function Analyzer Component
 * 
 * A web component for analyzing function performance
 */

import { formatDuration, formatNumber, getDurationClass } from './chart-loader.js';

// Import or use the LitElement base class
const LitElement = window.litElement?.LitElement || Object.getPrototypeOf(document.createElement('span')).constructor;
const html = window.litElement?.html || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));
const css = window.litElement?.css || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));

/**
 * Function Analyzer
 * 
 * @element function-analyzer
 * @attr {String} api-base-url - Base URL for API endpoints
 */
class FunctionAnalyzer extends LitElement {
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
      
      .monospace {
        font-family: monospace;
        white-space: pre-wrap;
        word-break: break-all;
        background-color: #f5f5f5;
        padding: 8px;
        border-radius: 4px;
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
    `;
  }

  constructor() {
    super();
    this.apiBaseUrl = '/api';
    this.data = null;
    this.loading = false;
    this.error = null;
    this.analysisMode = 'hotspots';
    this.sortField = 'total_time';
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
      const response = await fetch(`${this.apiBaseUrl}/metrics/functions?include_stats=true&include_slow=true&include_hotspots=true&limit=100`);
      if (!response.ok) {
        throw new Error(`Failed to load function data: ${response.statusText}`);
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
      const name = item.name.toLowerCase();
      const module = (item.module || '').toLowerCase();
      
      return name.includes(this.searchQuery) || module.includes(this.searchQuery);
    });
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
        <h2 class="card-title">Function Performance Analysis</h2>
        
        <div class="controls">
          <div class="tab-buttons">
            <button class="${this.analysisMode === 'hotspots' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('hotspots')}>
              Hotspots
            </button>
            <button class="${this.analysisMode === 'slow' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('slow')}>
              Slow Functions
            </button>
            <button class="${this.analysisMode === 'all' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('all')}>
              All Functions
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
              <strong>Total Function Calls:</strong> ${formatNumber(this.data.total_calls)} | 
              <strong>Unique Functions:</strong> ${formatNumber(this.data.total_functions)}
            </div>
            
            <div>
              <input type="search" placeholder="Search by name or module..." @input=${this.handleSearch}>
            </div>
          </div>
          
          <div class="tab-content ${this.analysisMode === 'hotspots' ? 'active' : ''}">
            ${this.renderHotspots()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'slow' ? 'active' : ''}">
            ${this.renderSlowFunctions()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'all' ? 'active' : ''}">
            ${this.renderAllFunctions()}
          </div>
        ` : html`
          <p>Loading function data...</p>
        `}
      </div>
    `;
  }

  renderHotspots() {
    if (!this.data.hotspots || this.data.hotspots.length === 0) {
      return html`<p class="success">No function hotspots detected</p>`;
    }
    
    // Filter and sort hotspots
    let hotspots = this.filterBySearch([...this.data.hotspots]);
    
    // Sort based on current sort field and order
    hotspots.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          Function hotspots are frequently called functions with high cumulative execution time. 
          These functions have the biggest impact on overall application performance.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'name' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('name')}>
                Function ${this.getSortIcon('name')}
              </th>
              <th class="sortable ${this.sortField === 'module' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('module')}>
                Module ${this.getSortIcon('module')}
              </th>
              <th class="sortable ${this.sortField === 'count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('count')}>
                Call Count ${this.getSortIcon('count')}
              </th>
              <th class="sortable ${this.sortField === 'avg' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('avg')}>
                Avg Duration ${this.getSortIcon('avg')}
              </th>
              <th class="sortable ${this.sortField === 'total_time' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('total_time')}>
                Total Time ${this.getSortIcon('total_time')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${hotspots.map(func => html`
              <tr>
                <td>${func.name}</td>
                <td>${func.module || '(unknown)'}</td>
                <td>${formatNumber(func.count)}</td>
                <td class="${getDurationClass(func.avg)}">${formatDuration(func.avg)}</td>
                <td class="${getDurationClass(func.total_time / 10)}">${formatDuration(func.total_time)}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderSlowFunctions() {
    if (!this.data.slow_functions || this.data.slow_functions.length === 0) {
      return html`<p class="success">No slow functions detected</p>`;
    }
    
    // Filter and sort slow functions
    let slowFunctions = this.filterBySearch([...this.data.slow_functions]);
    
    // Sort based on current sort field and order
    slowFunctions.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          Slow functions are individual function calls with high execution time.
          These can cause responsiveness issues or bottlenecks in your application.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'name' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('name')}>
                Function ${this.getSortIcon('name')}
              </th>
              <th class="sortable ${this.sortField === 'module' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('module')}>
                Module ${this.getSortIcon('module')}
              </th>
              <th class="sortable ${this.sortField === 'max' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('max')}>
                Max Duration ${this.getSortIcon('max')}
              </th>
              <th class="sortable ${this.sortField === 'avg' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('avg')}>
                Avg Duration ${this.getSortIcon('avg')}
              </th>
              <th class="sortable ${this.sortField === 'count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('count')}>
                Call Count ${this.getSortIcon('count')}
              </th>
              <th class="sortable ${this.sortField === 'last_called' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('last_called')}>
                Last Called ${this.getSortIcon('last_called')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${slowFunctions.map(func => html`
              <tr>
                <td>${func.name}</td>
                <td>${func.module || '(unknown)'}</td>
                <td class="${getDurationClass(func.max)}">${formatDuration(func.max)}</td>
                <td class="${getDurationClass(func.avg)}">${formatDuration(func.avg)}</td>
                <td>${formatNumber(func.count)}</td>
                <td>${new Date(func.last_called).toLocaleString()}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderAllFunctions() {
    if (!this.data.function_stats || Object.keys(this.data.function_stats).length === 0) {
      return html`<p>No function statistics available</p>`;
    }
    
    // Convert to array for filtering and sorting
    let functionStats = Object.entries(this.data.function_stats).map(([key, stats]) => {
      return {
        key,
        ...stats
      };
    });
    
    // Filter by search query
    functionStats = this.filterBySearch(functionStats);
    
    // Sort based on current sort field and order
    functionStats.sort((a, b) => {
      const fieldA = a[this.sortField];
      const fieldB = b[this.sortField];
      
      const comparison = fieldA < fieldB ? -1 : fieldA > fieldB ? 1 : 0;
      return this.sortOrder === 'asc' ? comparison : -comparison;
    });

    return html`
      <div>
        <p class="info">
          This view shows all monitored functions and their performance metrics.
        </p>
        
        <table>
          <thead>
            <tr>
              <th class="sortable ${this.sortField === 'name' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('name')}>
                Function ${this.getSortIcon('name')}
              </th>
              <th class="sortable ${this.sortField === 'module' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('module')}>
                Module ${this.getSortIcon('module')}
              </th>
              <th class="sortable ${this.sortField === 'count' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('count')}>
                Calls ${this.getSortIcon('count')}
              </th>
              <th class="sortable ${this.sortField === 'avg' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('avg')}>
                Avg ${this.getSortIcon('avg')}
              </th>
              <th class="sortable ${this.sortField === 'min' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('min')}>
                Min ${this.getSortIcon('min')}
              </th>
              <th class="sortable ${this.sortField === 'max' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('max')}>
                Max ${this.getSortIcon('max')}
              </th>
              <th class="sortable ${this.sortField === 'p95' ? 'sorted' : ''}" 
                  @click=${() => this.setSorting('p95')}>
                p95 ${this.getSortIcon('p95')}
              </th>
            </tr>
          </thead>
          <tbody>
            ${functionStats.map(func => html`
              <tr>
                <td>${func.name}</td>
                <td>${func.module || '(unknown)'}</td>
                <td>${formatNumber(func.count)}</td>
                <td class="${getDurationClass(func.avg)}">${formatDuration(func.avg)}</td>
                <td>${formatDuration(func.min)}</td>
                <td class="${getDurationClass(func.max)}">${formatDuration(func.max)}</td>
                <td class="${getDurationClass(func.p95)}">${formatDuration(func.p95)}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }
}

// Define the custom element
if (!customElements.get('function-analyzer')) {
  customElements.define('function-analyzer', FunctionAnalyzer);
}