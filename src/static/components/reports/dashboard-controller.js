/**
 * Dashboard Controller Component
 * 
 * This component manages the data flow and interaction between different reporting dashboard widgets.
 * It handles:
 * - Loading data from multiple report sources
 * - Coordinating updates across widgets
 * - Managing shared filters and date ranges
 * - Persisting dashboard layouts and settings
 * - Handling user interactions and events
 */

import { LitElement, html, css } from 'lit-element';

export class DashboardController extends LitElement {
  static get properties() {
    return {
      dashboardId: { type: String },
      reportIds: { type: Array },
      dateRange: { type: Object },
      filters: { type: Object },
      layout: { type: Array },
      data: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      refreshInterval: { type: Number },
      lastRefreshed: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      .dashboard-controller {
        margin-bottom: 20px;
      }
      .controller-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 16px;
        background-color: var(--controller-bg, #f8f9fa);
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 20px;
      }
      .controller-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--controller-title-color, #333);
      }
      .controller-actions {
        display: flex;
        gap: 10px;
        align-items: center;
      }
      .date-range {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-right: 16px;
      }
      .refresh-status {
        font-size: 13px;
        color: #666;
        margin-right: 10px;
      }
      button {
        background-color: var(--primary-color, #4285f4);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        cursor: pointer;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 4px;
      }
      button:hover {
        background-color: var(--primary-color-dark, #3367d6);
      }
      button.secondary {
        background-color: #f1f3f4;
        color: #444;
      }
      button.secondary:hover {
        background-color: #e8eaed;
      }
      select, input {
        padding: 6px 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
      .filter-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
      }
      .filter-tag {
        display: flex;
        align-items: center;
        gap: 4px;
        background-color: #e8f0fe;
        border-radius: 16px;
        padding: 4px 10px;
        font-size: 13px;
        color: #1a73e8;
      }
      .filter-tag button {
        background: none;
        border: none;
        color: #5f6368;
        cursor: pointer;
        padding: 0;
        width: 16px;
        height: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .error-message {
        color: #d32f2f;
        padding: 12px;
        background-color: #ffebee;
        border-radius: 4px;
        margin-bottom: 16px;
      }
      .loading-indicator {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(66, 133, 244, 0.3);
        border-radius: 50%;
        border-top-color: #4285f4;
        animation: spin 1s linear infinite;
        margin-right: 8px;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `;
  }

  constructor() {
    super();
    this.dashboardId = null;
    this.reportIds = [];
    this.dateRange = {
      start: this._getDefaultStartDate(),
      end: this._getDefaultEndDate()
    };
    this.filters = {};
    this.layout = [];
    this.data = {};
    this.loading = false;
    this.error = null;
    this.refreshInterval = 0; // 0 means no auto-refresh
    this.lastRefreshed = '';
    this._refreshTimer = null;
  }

  connectedCallback() {
    super.connectedCallback();
    
    // Initial data load
    if (this.dashboardId) {
      this.loadDashboardConfig();
    } else if (this.reportIds && this.reportIds.length > 0) {
      this.loadData();
    }
    
    // Set up refresh timer if needed
    this._setupRefreshTimer();
    
    // Listen for events from child widgets
    this.addEventListener('filter-changed', this._handleFilterChanged);
    this.addEventListener('refresh-requested', this._handleRefreshRequested);
    this.addEventListener('date-range-changed', this._handleDateRangeChanged);
    this.addEventListener('layout-changed', this._handleLayoutChanged);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    
    // Clear any timers
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
    
    // Remove event listeners
    this.removeEventListener('filter-changed', this._handleFilterChanged);
    this.removeEventListener('refresh-requested', this._handleRefreshRequested);
    this.removeEventListener('date-range-changed', this._handleDateRangeChanged);
    this.removeEventListener('layout-changed', this._handleLayoutChanged);
  }

  updated(changedProps) {
    if (changedProps.has('dashboardId') && this.dashboardId) {
      this.loadDashboardConfig();
    }
    
    if (changedProps.has('reportIds') && this.reportIds.length > 0) {
      this.loadData();
    }
    
    if (changedProps.has('refreshInterval')) {
      this._setupRefreshTimer();
    }
  }

  _getDefaultStartDate() {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split('T')[0];
  }

  _getDefaultEndDate() {
    return new Date().toISOString().split('T')[0];
  }

  _setupRefreshTimer() {
    // Clear existing timer if any
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
    
    // Setup new timer if interval is set
    if (this.refreshInterval > 0) {
      this._refreshTimer = setInterval(() => {
        this.loadData();
      }, this.refreshInterval * 1000);
    }
  }

  async loadDashboardConfig() {
    if (!this.dashboardId) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`/api/reports/dashboards/${this.dashboardId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const config = await response.json();
      
      // Update properties from config
      this.reportIds = config.report_ids || [];
      this.layout = config.layout || [];
      this.refreshInterval = config.refresh_interval || 0;
      
      if (config.date_range) {
        this.dateRange = config.date_range;
      }
      
      if (config.filters) {
        this.filters = config.filters;
      }
      
      // Load data now that we have the config
      await this.loadData();
      
    } catch (err) {
      console.error("Failed to load dashboard config:", err);
      this.error = `Failed to load dashboard configuration: ${err.message}`;
      this.loading = false;
    }
  }

  async loadData() {
    if (!this.reportIds || this.reportIds.length === 0) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      // Prepare query parameters
      const params = new URLSearchParams();
      
      // Add report IDs
      this.reportIds.forEach(id => {
        params.append('template_ids', id);
      });
      
      // Add date range
      if (this.dateRange.start) {
        params.append('date_start', this.dateRange.start);
      }
      
      if (this.dateRange.end) {
        params.append('date_end', this.dateRange.end);
      }
      
      // Add filters
      if (Object.keys(this.filters).length > 0) {
        params.append('filters', JSON.stringify(this.filters));
      }
      
      // Make the API call
      const response = await fetch(`/api/reports/dashboard?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const results = await response.json();
      
      // Process and store the data
      this.data = this._processReportData(results);
      
      // Update last refreshed time
      this.lastRefreshed = new Date().toLocaleTimeString();
      
      // Dispatch data loaded event
      this._dispatchDataLoadedEvent();
      
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      this.error = `Failed to load dashboard data: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  _processReportData(results) {
    // Convert array of report results to an object keyed by template_id
    const processedData = {};
    
    for (const result of results) {
      if (result.error) {
        console.warn(`Error loading report ${result.template_id}: ${result.error}`);
        continue;
      }
      
      processedData[result.template_id] = {
        execution_id: result.execution_id,
        data: result.data
      };
    }
    
    return processedData;
  }

  _dispatchDataLoadedEvent() {
    const event = new CustomEvent('data-loaded', {
      detail: {
        data: this.data,
        timestamp: this.lastRefreshed
      },
      bubbles: true,
      composed: true
    });
    
    this.dispatchEvent(event);
  }

  async saveDashboardConfig() {
    if (!this.dashboardId) return;
    
    this.loading = true;
    
    try {
      const config = {
        id: this.dashboardId,
        report_ids: this.reportIds,
        layout: this.layout,
        date_range: this.dateRange,
        filters: this.filters,
        refresh_interval: this.refreshInterval
      };
      
      const response = await fetch(`/api/reports/dashboards/${this.dashboardId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      // Show success indicator or message
      this._showSuccessMessage('Dashboard saved successfully');
      
    } catch (err) {
      console.error("Failed to save dashboard config:", err);
      this.error = `Failed to save dashboard configuration: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  _showSuccessMessage(message) {
    // Implementation depends on your UI framework
    // This could be a toast, snackbar, or other notification
    console.log("Success:", message);
    
    // Example: Create and dispatch a custom event
    const event = new CustomEvent('notification', {
      detail: {
        type: 'success',
        message: message
      },
      bubbles: true,
      composed: true
    });
    
    this.dispatchEvent(event);
  }

  _handleFilterChanged(e) {
    // Update filters based on event detail
    const { key, value, clear } = e.detail;
    
    if (clear) {
      // Clear all filters
      this.filters = {};
    } else if (value === null) {
      // Remove this filter
      const newFilters = { ...this.filters };
      delete newFilters[key];
      this.filters = newFilters;
    } else {
      // Update or add this filter
      this.filters = {
        ...this.filters,
        [key]: value
      };
    }
    
    // Reload data with new filters
    this.loadData();
  }

  _handleRefreshRequested() {
    this.loadData();
  }

  _handleDateRangeChanged(e) {
    const { start, end } = e.detail;
    
    this.dateRange = {
      start: start || this.dateRange.start,
      end: end || this.dateRange.end
    };
    
    // Reload data with new date range
    this.loadData();
  }

  _handleLayoutChanged(e) {
    this.layout = e.detail.layout;
    
    // Optionally auto-save the layout
    if (this.dashboardId) {
      this.saveDashboardConfig();
    }
  }

  handleDateRangeChange(e, field) {
    this.dateRange = {
      ...this.dateRange,
      [field]: e.target.value
    };
  }

  handleRefreshIntervalChange(e) {
    const interval = parseInt(e.target.value, 10);
    this.refreshInterval = isNaN(interval) ? 0 : interval;
  }

  applyDateRange() {
    this.loadData();
  }

  clearFilters() {
    this.filters = {};
    this.loadData();
  }

  handleSave() {
    this.saveDashboardConfig();
  }

  exportDashboard(format) {
    if (!this.dashboardId) return;
    
    // Create and construct the export URL with parameters
    const params = new URLSearchParams();
    params.append('format', format);
    
    // Add date range
    if (this.dateRange.start) {
      params.append('date_start', this.dateRange.start);
    }
    
    if (this.dateRange.end) {
      params.append('date_end', this.dateRange.end);
    }
    
    // Add filters
    if (Object.keys(this.filters).length > 0) {
      params.append('filters', JSON.stringify(this.filters));
    }
    
    // Open in a new tab/window
    window.open(`/api/reports/dashboards/${this.dashboardId}/export?${params.toString()}`, '_blank');
  }

  render() {
    return html`
      <div class="dashboard-controller">
        <div class="controller-header">
          <div class="controller-title">
            Dashboard Controls
          </div>
          
          <div class="controller-actions">
            <div class="date-range">
              <input type="date" .value=${this.dateRange.start} 
                    @change=${(e) => this.handleDateRangeChange(e, 'start')} />
              <span>to</span>
              <input type="date" .value=${this.dateRange.end} 
                    @change=${(e) => this.handleDateRangeChange(e, 'end')} />
              <button class="secondary" @click=${this.applyDateRange}>Apply</button>
            </div>
            
            <div class="refresh-controls">
              <select @change=${this.handleRefreshIntervalChange}>
                <option value="0" ?selected=${this.refreshInterval === 0}>No auto-refresh</option>
                <option value="30" ?selected=${this.refreshInterval === 30}>30 seconds</option>
                <option value="60" ?selected=${this.refreshInterval === 60}>1 minute</option>
                <option value="300" ?selected=${this.refreshInterval === 300}>5 minutes</option>
                <option value="600" ?selected=${this.refreshInterval === 600}>10 minutes</option>
                <option value="1800" ?selected=${this.refreshInterval === 1800}>30 minutes</option>
              </select>
            </div>
            
            ${this.lastRefreshed ? html`
              <span class="refresh-status">
                Last updated: ${this.lastRefreshed}
              </span>
            ` : ''}
            
            <button @click=${this._handleRefreshRequested}>
              ${this.loading ? html`<span class="loading-indicator"></span>` : ''}
              Refresh
            </button>
            
            ${this.dashboardId ? html`
              <button @click=${this.handleSave}>Save</button>
              <button class="secondary" @click=${() => this.exportDashboard('pdf')}>PDF</button>
              <button class="secondary" @click=${() => this.exportDashboard('xlsx')}>Excel</button>
            ` : ''}
          </div>
        </div>
        
        ${this.error ? html`
          <div class="error-message">
            ${this.error}
          </div>
        ` : ''}
        
        ${Object.keys(this.filters).length > 0 ? html`
          <div class="filter-tags">
            ${Object.entries(this.filters).map(([key, value]) => html`
              <div class="filter-tag">
                <span>${key}: ${value}</span>
                <button @click=${() => this._handleFilterChanged({ detail: { key, value: null } })}>×</button>
              </div>
            `)}
            <button class="secondary" @click=${this.clearFilters}>Clear All</button>
          </div>
        ` : ''}
        
        <slot></slot>
      </div>
    `;
  }
}

customElements.define('dashboard-controller', DashboardController);