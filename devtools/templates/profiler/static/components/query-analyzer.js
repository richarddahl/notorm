/**
 * Query Analyzer Component
 * 
 * A web component for analyzing SQL query performance
 */

import { formatDuration, formatNumber, getDurationClass } from './chart-loader.js';

// Import or use the LitElement base class
const LitElement = window.litElement?.LitElement || Object.getPrototypeOf(document.createElement('span')).constructor;
const html = window.litElement?.html || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));
const css = window.litElement?.css || ((strings, ...values) => strings.reduce((acc, str, i) => acc + str + (values[i] || ''), ''));

/**
 * Query Analyzer
 * 
 * @element query-analyzer
 * @attr {String} api-base-url - Base URL for API endpoints
 */
class QueryAnalyzer extends LitElement {
  static get properties() {
    return {
      apiBaseUrl: { type: String, attribute: 'api-base-url' },
      data: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      showFullQuery: { type: Boolean },
      showNPlusOne: { type: Boolean },
      analysisMode: { type: String },
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
      }
      
      .monospace {
        font-family: monospace;
        white-space: pre-wrap;
        word-break: break-all;
        background-color: #f5f5f5;
        padding: 8px;
        border-radius: 4px;
        max-height: 120px;
        overflow-y: auto;
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
      
      .hidden {
        display: none;
      }
      
      .toggle-button {
        background: none;
        border: none;
        color: var(--primary-color, #0078d7);
        padding: 4px;
        cursor: pointer;
        text-decoration: underline;
        font-size: 12px;
        font-weight: normal;
      }
      
      .expand-icon {
        display: inline-block;
        width: 10px;
        height: 10px;
        margin-right: 4px;
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
      
      .tab-content {
        display: none;
      }
      
      .tab-content.active {
        display: block;
      }
    `;
  }

  constructor() {
    super();
    this.apiBaseUrl = '/api';
    this.data = null;
    this.loading = false;
    this.error = null;
    this.showFullQuery = false;
    this.showNPlusOne = true;
    this.analysisMode = 'slow';
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadData();
  }

  async loadData() {
    this.loading = true;
    this.error = null;

    try {
      const response = await fetch(`${this.apiBaseUrl}/metrics/queries?include_patterns=true&include_slow=true&include_n_plus_1=true&limit=50`);
      if (!response.ok) {
        throw new Error(`Failed to load query data: ${response.statusText}`);
      }
      this.data = await response.json();
    } catch (error) {
      console.error('Error loading data:', error);
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }

  toggleFullQuery() {
    this.showFullQuery = !this.showFullQuery;
  }

  toggleNPlusOne() {
    this.showNPlusOne = !this.showNPlusOne;
  }

  setAnalysisMode(mode) {
    this.analysisMode = mode;
  }

  render() {
    return html`
      <div class="card">
        <h2 class="card-title">SQL Query Analysis</h2>
        
        <div class="controls">
          <div class="tab-buttons">
            <button class="${this.analysisMode === 'slow' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('slow')}>
              Slow Queries
            </button>
            <button class="${this.analysisMode === 'patterns' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('patterns')}>
              Query Patterns
            </button>
            <button class="${this.analysisMode === 'n-plus-1' ? 'active' : 'secondary'}" 
                    @click=${() => this.setAnalysisMode('n-plus-1')}>
              N+1 Issues
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
              <strong>Total Queries:</strong> ${formatNumber(this.data.total_queries)} | 
              <strong>Unique Patterns:</strong> ${formatNumber(this.data.unique_patterns)}
            </div>
          </div>
          
          <div class="tab-content ${this.analysisMode === 'slow' ? 'active' : ''}">
            ${this.renderSlowQueries()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'patterns' ? 'active' : ''}">
            ${this.renderQueryPatterns()}
          </div>
          
          <div class="tab-content ${this.analysisMode === 'n-plus-1' ? 'active' : ''}">
            ${this.renderNPlusOneIssues()}
          </div>
        ` : html`
          <p>Loading query data...</p>
        `}
      </div>
    `;
  }

  renderSlowQueries() {
    if (!this.data.slow_queries || this.data.slow_queries.length === 0) {
      return html`<p class="success">No slow queries detected</p>`;
    }

    return html`
      <div>
        <div class="flex justify-between items-center">
          <h3>Slow Queries <span class="badge error">${this.data.slow_queries.length}</span></h3>
          <button class="toggle-button" @click=${this.toggleFullQuery}>
            ${this.showFullQuery ? 'Show Less' : 'Show Full Queries'}
          </button>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Query</th>
              <th>Duration</th>
              <th>Database</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            ${this.data.slow_queries.map(query => html`
              <tr>
                <td>
                  <div class="monospace" style="max-height: ${this.showFullQuery ? 'none' : '80px'}">
                    ${query.query}
                  </div>
                </td>
                <td class="${getDurationClass(query.duration)}">${formatDuration(query.duration)}</td>
                <td>${query.db_name || 'Unknown'}</td>
                <td>${new Date(query.timestamp).toLocaleString()}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderQueryPatterns() {
    if (!this.data.patterns || Object.keys(this.data.patterns).length === 0) {
      return html`<p>No query patterns available</p>`;
    }

    // Sort patterns by average duration (slowest first)
    const sortedPatterns = Object.entries(this.data.patterns)
      .sort(([, a], [, b]) => b.avg - a.avg);

    return html`
      <div>
        <h3>Query Patterns <span class="badge">${sortedPatterns.length}</span></h3>
        
        <table>
          <thead>
            <tr>
              <th>Pattern</th>
              <th>Count</th>
              <th>Avg Duration</th>
              <th>Max Duration</th>
              <th>P95 Duration</th>
            </tr>
          </thead>
          <tbody>
            ${sortedPatterns.map(([pattern, stats]) => html`
              <tr>
                <td>
                  <div class="monospace" style="max-height: ${this.showFullQuery ? 'none' : '80px'}">
                    ${pattern}
                  </div>
                </td>
                <td>${stats.count}</td>
                <td class="${getDurationClass(stats.avg)}">${formatDuration(stats.avg)}</td>
                <td class="${getDurationClass(stats.max)}">${formatDuration(stats.max)}</td>
                <td class="${getDurationClass(stats.p95)}">${formatDuration(stats.p95)}</td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  renderNPlusOneIssues() {
    if (!this.data.n_plus_1_candidates || Object.keys(this.data.n_plus_1_candidates).length === 0) {
      return html`<p class="success">No N+1 query issues detected</p>`;
    }

    return html`
      <div>
        <h3>Potential N+1 Query Issues <span class="badge warning">${Object.keys(this.data.n_plus_1_candidates).length}</span></h3>
        
        <p>
          N+1 query issues occur when an application executes one query to fetch a set of records, 
          then executes additional queries for each record. This can lead to performance problems 
          as the number of records increases.
        </p>
        
        ${Object.values(this.data.n_plus_1_candidates).map(candidate => html`
          <div class="card">
            <h4>Pattern executed ${candidate.count} times:</h4>
            <div class="monospace">
              ${candidate.pattern.length > 200 && !this.showFullQuery 
                ? candidate.pattern.slice(0, 200) + '...' 
                : candidate.pattern}
            </div>
            
            <h5>Similar patterns:</h5>
            <ul>
              ${candidate.similar_patterns.map(similar => html`
                <li>Pattern executed ${similar.count} times</li>
              `)}
            </ul>
            
            <div class="flex justify-between">
              <button class="toggle-button" @click=${this.toggleFullQuery}>
                ${this.showFullQuery ? 'Show Less' : 'Show Full Patterns'}
              </button>
            </div>
          </div>
        `)}
      </div>
    `;
  }
}

// Define the custom element
if (!customElements.get('query-analyzer')) {
  customElements.define('query-analyzer', QueryAnalyzer);
}