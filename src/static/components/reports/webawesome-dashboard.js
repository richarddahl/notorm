import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
// We'll use a simple CSS grid instead of the missing lit-grid-layout
import './webawesome-report-widget.js';
/**
 * @element wa-dashboard
 * @description An interactive dashboard for visualizing reports using WebAwesome components
 * @property {String} dashboardId - The ID of the dashboard to display
 * @property {Array} reportIds - List of report IDs to include in the dashboard 
 * @property {Object} dateRange - The date range for filtering data
 * @property {Object} filters - Additional filters to apply to reports
 * @property {Array} layout - Layout configuration for dashboard widgets
 * @property {Number} refreshInterval - Auto-refresh interval in seconds
 */
export class WebAwesomeDashboard extends LitElement {
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
      lastRefreshed: { type: String },
      editMode: { type: Boolean },
      theme: { type: String }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --dashboard-bg: var(--wa-background-color, #f5f5f5);
        --dashboard-padding: 16px;
      }
      .dashboard-container {
        padding: var(--dashboard-padding);
        background-color: var(--dashboard-bg);
        min-height: 600px;
      }
      .dashboard-header {
        margin-bottom: 20px;
      }
      .filter-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
        padding: 12px 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .date-range {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .filters-section {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 12px 0;
      }
      .actions {
        display: flex;
        gap: 8px;
        margin-left: auto;
      }
      .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        grid-auto-rows: 80px;
        gap: 16px;
        width: 100%;
      }
      .dashboard-grid-item {
        min-height: 80px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        overflow: hidden;
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 400px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 32px;
        color: var(--wa-text-secondary-color, #666);
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-disabled-color, #ccc);
      }
      .widget-placeholder {
        background-color: var(--wa-surface-color, #ffffff);
        border: 2px dashed var(--wa-border-color, #ddd);
        border-radius: var(--wa-border-radius, 4px);
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 100px;
        color: var(--wa-text-secondary-color, #666);
      }
      .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        font-size: 13px;
        color: var(--wa-text-secondary-color, #666);
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
    this.editMode = false;
    this.theme = 'light';
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
    this.addEventListener('refresh', this._handleRefresh);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    
    // Clear any timers
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
    
    // Remove event listeners
    this.removeEventListener('refresh', this._handleRefresh);
  }
  updated(changedProperties) {
    if (changedProperties.has('dashboardId') && this.dashboardId) {
      this.loadDashboardConfig();
    }
    
    if (changedProperties.has('reportIds') && this.reportIds.length > 0) {
      this.loadData();
    }
    
    if (changedProperties.has('refreshInterval')) {
      this._setupRefreshTimer();
    }
    
    if (changedProperties.has('theme')) {
      // Update theme for child components
      this.updateChildrenTheme();
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
  updateChildrenTheme() {
    // Update theme of all child wa-report-widget elements
    this.updateComplete.then(() => {
      const widgets = this.shadowRoot.querySelectorAll('wa-report-widget');
      widgets.forEach(widget => {
        widget.theme = this.theme;
      });
    });
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
      this.layout = config.widgets || [];
      this.refreshInterval = config.refresh_interval || 0;
      
      if (config.default_date_range) {
        this.dateRange = config.default_date_range;
      }
      
      if (config.default_filters) {
        // Convert filter objects to key-value pairs
        const filterObj = {};
        config.default_filters.forEach(filter => {
          filterObj[filter.field] = filter.value;
        });
        this.filters = filterObj;
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
  async saveDashboard() {
    if (!this.dashboardId) return;
    
    this.loading = true;
    
    try {
      // Convert filters from object to array format
      const filterArray = Object.entries(this.filters).map(([field, value]) => ({
        field,
        value,
        operator: 'eq'
      }));
      
      const config = {
        id: this.dashboardId,
        report_ids: this.reportIds,
        widgets: this.layout,
        default_date_range: this.dateRange,
        default_filters: filterArray,
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
      
      // Show success notification
      this._showNotification('Dashboard saved successfully', 'success');
      
    } catch (err) {
      console.error("Failed to save dashboard config:", err);
      this._showNotification(`Failed to save dashboard: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  _showNotification(message, type = 'info') {
    // Create and show a notification
    // In WebAwesome, we'll use wa-alert
    const alertEl = document.createElement('wa-alert');
    alertEl.type = type;
    alertEl.message = message;
    alertEl.duration = 5000; // 5 seconds
    alertEl.position = 'top-right';
    
    // Add to DOM
    document.body.appendChild(alertEl);
    alertEl.show();
    
    // Clean up after close
    alertEl.addEventListener('close', () => {
      document.body.removeChild(alertEl);
    });
  }
  _handleRefresh(e) {
    // Handle refresh request from a widget
    this.loadData();
  }
  handleDateRangeChange(field, value) {
    this.dateRange = {
      ...this.dateRange,
      [field]: value
    };
  }
  handleRefreshIntervalChange(e) {
    const interval = parseInt(e.target.value, 10);
    this.refreshInterval = isNaN(interval) ? 0 : interval;
  }
  applyDateRange() {
    this.loadData();
  }
  removeFilter(key) {
    const newFilters = { ...this.filters };
    delete newFilters[key];
    this.filters = newFilters;
    this.loadData();
  }
  clearFilters() {
    this.filters = {};
    this.loadData();
  }
  toggleEditMode() {
    this.editMode = !this.editMode;
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
  handleLayoutChange(e) {
    const newLayout = e.detail.layout;
    
    // Update widget positions in our layout array
    this.layout = this.layout.map(widget => {
      const layoutItem = newLayout.find(item => item.id === widget.id);
      if (layoutItem) {
        return {
          ...widget,
          position: {
            x: layoutItem.x,
            y: layoutItem.y,
            w: layoutItem.w,
            h: layoutItem.h
          }
        };
      }
      return widget;
    });
  }
  renderFilterBar() {
    return html`
      <div class="filter-bar">
        <div class="date-range">
          <wa-date-picker 
            label="Start Date"
            value=${this.dateRange.start}
            @change=${(e) => this.handleDateRangeChange('start', e.target.value)}>
          </wa-date-picker>
          
          <span>to</span>
          
          <wa-date-picker 
            label="End Date"
            value=${this.dateRange.end}
            @change=${(e) => this.handleDateRangeChange('end', e.target.value)}>
          </wa-date-picker>
          
          <wa-button variant="outlined" @click=${this.applyDateRange}>
            Apply
          </wa-button>
        </div>
        
        <div class="refresh-controls">
          <wa-select 
            label="Auto-refresh"
            @change=${this.handleRefreshIntervalChange}>
            <wa-option value="0" ?selected=${this.refreshInterval === 0}>None</wa-option>
            <wa-option value="30" ?selected=${this.refreshInterval === 30}>30 seconds</wa-option>
            <wa-option value="60" ?selected=${this.refreshInterval === 60}>1 minute</wa-option>
            <wa-option value="300" ?selected=${this.refreshInterval === 300}>5 minutes</wa-option>
            <wa-option value="600" ?selected=${this.refreshInterval === 600}>10 minutes</wa-option>
          </wa-select>
        </div>
        
        <div class="actions">
          <wa-button variant="text" @click=${this.loadData}>
            <wa-icon slot="prefix" name="refresh"></wa-icon>
            Refresh
          </wa-button>
          
          ${this.dashboardId ? html`
            <wa-button variant="text" @click=${this.saveDashboard}>
              <wa-icon slot="prefix" name="save"></wa-icon>
              Save
            </wa-button>
            
            <wa-button variant="text" @click=${() => this.exportDashboard('pdf')}>
              <wa-icon slot="prefix" name="download"></wa-icon>
              PDF
            </wa-button>
            
            <wa-button variant="text" @click=${() => this.exportDashboard('xlsx')}>
              <wa-icon slot="prefix" name="download"></wa-icon>
              Excel
            </wa-button>
            
            <wa-button variant="text" @click=${this.toggleEditMode}>
              <wa-icon slot="prefix" name=${this.editMode ? 'visibility' : 'edit'}></wa-icon>
              ${this.editMode ? 'View Mode' : 'Edit Mode'}
            </wa-button>
          ` : ''}
        </div>
      </div>
      
      ${Object.keys(this.filters).length > 0 ? html`
        <div class="filters-section">
          ${Object.entries(this.filters).map(([key, value]) => html`
            <wa-chip 
              variant="outlined"
              @remove=${() => this.removeFilter(key)}>
              ${key}: ${value}
            </wa-chip>
          `)}
          
          <wa-button size="small" variant="text" @click=${this.clearFilters}>
            Clear All
          </wa-button>
        </div>
      ` : ''}
    `;
  }
  renderEmptyState() {
    return html`
      <div class="empty-state">
        <wa-icon name="dashboard" size="xlarge" class="empty-state-icon"></wa-icon>
        <h3>No dashboard widgets configured</h3>
        <p>Add widgets to start building your dashboard.</p>
        <wa-button @click=${this.toggleEditMode}>Add Widgets</wa-button>
      </div>
    `;
  }
  getWidgetData(widget) {
    if (!this.data || !widget.report_id || !widget.data_key) return null;
    
    const reportData = this.data[widget.report_id];
    if (!reportData || !reportData.data) return null;
    
    // Handle nested data paths with dot notation
    const keys = widget.data_key.split('.');
    let result = reportData.data;
    
    for (const key of keys) {
      if (result === undefined || result === null) return null;
      result = result[key];
    }
    
    return result;
  }
  render() {
    const hasWidgets = this.layout && this.layout.length > 0;
    
    return html`
      <div class="dashboard-container">
        ${this.renderFilterBar()}
        
        ${this.error ? html`
          <wa-alert type="error">
            ${this.error}
            <wa-button slot="action" variant="text" @click=${this.loadData}>Retry</wa-button>
          </wa-alert>
        ` : ''}
        
        ${this.loading ? html`
          <div style="position: fixed; top: 16px; right: 16px; z-index: 1000;">
            <wa-spinner size="small"></wa-spinner>
            <span style="margin-left: 8px;">Loading...</span>
          </div>
        ` : ''}
        
        ${!hasWidgets ? this.renderEmptyState() : html`
          <div class="dashboard-grid">
            ${this.layout.map(widget => {
              const style = this.editMode ? '' : `
                grid-column: ${widget.position?.x || 0} / span ${widget.position?.w || 3};
                grid-row: ${widget.position?.y || 0} / span ${widget.position?.h || 3};
              `;
              
              return html`
                <div class="dashboard-grid-item" style=${style}>
                  ${this.editMode ? html`
                    <div class="widget-placeholder">
                      ${widget.title}
                    </div>
                  ` : html`
                    <wa-report-widget
                      type=${widget.type}
                      subtype=${widget.type === 'chart' ? widget.config?.chart_type || 'bar' : ''}
                      title=${widget.title}
                      .data=${this.getWidgetData(widget)}
                      .config=${widget.config || {}}
                      theme=${this.theme}
                    ></wa-report-widget>
                  `}
                </div>
              `;
            })}
          </div>
          
          <div class="status-bar">
            <div>
              ${this.lastRefreshed ? `Last updated: ${this.lastRefreshed}` : ''}
            </div>
            <div>
              ${this.dashboardId ? `Dashboard ID: ${this.dashboardId}` : ''}
            </div>
          </div>
        `}
      </div>
    `;
  }
}
customElements.define('wa-dashboard', WebAwesomeDashboard);