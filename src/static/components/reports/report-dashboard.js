import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
// Import Chart.js globally, rather than as a module import
// The UMD version of Chart.js registers itself as window.Chart
// Using CSS Grid instead of lit-grid-layout
/**
 * @element report-dashboard
 * @description An interactive dashboard for report data visualization with customizable widgets
 * @property {String} reportId - ID of the report execution to display
 * @property {Object} reportData - Report data if provided directly
 * @property {Array} widgets - Widget configuration
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 */
export class ReportDashboard extends LitElement {
  static get properties() {
    return {
      reportId: { type: String },
      reportData: { type: Object },
      widgets: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      gridConfig: { type: Object },
      dateRange: { type: Object },
      filters: { type: Object }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        font-family: var(--system-font, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif);
      }
      .dashboard-container {
        padding: 20px;
      }
      .controls {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 10px;
      }
      .date-range {
        display: flex;
        gap: 10px;
        align-items: center;
      }
      .filters {
        display: flex;
        gap: 10px;
        align-items: center;
      }
      .actions {
        display: flex;
        gap: 10px;
      }
      button {
        background-color: var(--primary-color, #4285f4);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 14px;
      }
      button:hover {
        background-color: var(--primary-color-dark, #3367d6);
      }
      .widget {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .widget-header {
        padding: 15px;
        background-color: var(--widget-header-bg, #f8f9fa);
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .widget-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
      }
      .widget-content {
        padding: 15px;
        flex: 1;
        overflow: auto;
        display: flex;
        flex-direction: column;
      }
      .chart-container {
        flex: 1;
        position: relative;
        min-height: 200px;
      }
      .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
        text-align: center;
      }
      .metric-label {
        text-align: center;
        color: #666;
        font-size: 14px;
      }
      .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        grid-auto-rows: minmax(50px, auto);
        gap: 10px;
        width: 100%;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #eee;
      }
      th {
        background-color: var(--table-header-bg, #f1f3f4);
        font-weight: 600;
      }
      .loading-overlay {
        display: flex;
        justify-content: center;
        align-items: center;
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.7);
        z-index: 10;
      }
      .error {
        color: #d32f2f;
        padding: 20px;
        text-align: center;
        background-color: #ffebee;
        border-radius: 4px;
        margin: 20px 0;
      }
      select, input {
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
      .widget-actions {
        display: flex;
        gap: 5px;
      }
      .widget-action-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: #666;
        padding: 2px;
        font-size: 14px;
      }
      .widget-action-btn:hover {
        color: var(--primary-color, #4285f4);
        background: none;
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        color: #666;
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 10px;
        color: #ccc;
      }
    `;
  }
  constructor() {
    super();
    this.reportId = null;
    this.reportData = null;
    this.widgets = [];
    this.loading = false;
    this.error = null;
    this.charts = [];
    this.gridConfig = {
      cols: 12,
      rowHeight: 50,
      gap: 10
    };
    this.dateRange = {
      start: this._getDefaultStartDate(),
      end: this._getDefaultEndDate()
    };
    this.filters = {};
    
    // Default widgets if none provided
    this.defaultWidgets = [
      {
        id: 'w1',
        type: 'metric',
        title: 'Total Records',
        dataKey: 'total_count',
        x: 0, y: 0, w: 3, h: 4
      },
      {
        id: 'w2',
        type: 'chart',
        subtype: 'bar',
        title: 'Top Categories',
        dataKey: 'categories',
        x: 3, y: 0, w: 5, h: 8
      },
      {
        id: 'w3',
        type: 'chart',
        subtype: 'line',
        title: 'Trend Analysis',
        dataKey: 'time_series',
        x: 0, y: 4, w: 3, h: 8
      },
      {
        id: 'w4',
        type: 'table',
        title: 'Latest Data',
        dataKey: 'records',
        x: 8, y: 0, w: 4, h: 12
      }
    ];
  }
  _getDefaultStartDate() {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split('T')[0];
  }
  _getDefaultEndDate() {
    return new Date().toISOString().split('T')[0];
  }
  connectedCallback() {
    super.connectedCallback();
    if (this.reportId && !this.reportData) {
      this.loadReportData();
    }
    
    // Use default widgets if none provided
    if (!this.widgets || this.widgets.length === 0) {
      this.widgets = [...this.defaultWidgets];
    }
    // Handle resize events for charts
    this._resizeHandler = this._handleResize.bind(this);
    window.addEventListener('resize', this._resizeHandler);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('resize', this._resizeHandler);
    this.destroyCharts();
  }
  updated(changedProperties) {
    if (changedProperties.has('reportId') && this.reportId) {
      this.loadReportData();
    }
    
    if ((changedProperties.has('reportData') && this.reportData) || 
        (changedProperties.has('widgets') && this.widgets)) {
      // Schedule render after DOM update
      this.updateComplete.then(() => {
        this.renderWidgetContents();
      });
    }
  }
  _handleResize() {
    // Debounce resize handling
    clearTimeout(this._resizeTimer);
    this._resizeTimer = setTimeout(() => {
      this.destroyCharts();
      this.renderWidgetContents();
    }, 250);
  }
  async loadReportData() {
    if (!this.reportId) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`/api/reports/executions/${this.reportId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const data = await response.json();
      this.reportData = data;
    } catch (err) {
      console.error('Failed to load report data:', err);
      this.error = `Error loading report data: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }
  async refreshData() {
    this.loadReportData();
  }
  exportDashboard(format) {
    if (!this.reportId) return;
    window.open(`/api/reports/executions/${this.reportId}/export?format=${format}`, '_blank');
  }
  destroyCharts() {
    if (this.charts) {
      this.charts.forEach(chart => {
        if (chart) chart.destroy();
      });
      this.charts = [];
    }
  }
  renderWidgetContents() {
    this.destroyCharts();
    
    if (!this.reportData) return;
    
    this.widgets.forEach(widget => {
      const widgetEl = this.shadowRoot.getElementById(`widget-${widget.id}`);
      if (!widgetEl) return;
      
      const contentEl = widgetEl.querySelector('.widget-content');
      if (!contentEl) return;
      
      const widgetData = this.getWidgetData(widget.dataKey);
      
      switch (widget.type) {
        case 'metric':
          this.renderMetricWidget(contentEl, widgetData, widget);
          break;
        case 'chart':
          this.renderChartWidget(contentEl, widgetData, widget);
          break;
        case 'table':
          this.renderTableWidget(contentEl, widgetData, widget);
          break;
      }
    });
  }
  getWidgetData(dataKey) {
    if (!this.reportData || !dataKey) return null;
    
    // Handle nested data paths
    if (dataKey.includes('.')) {
      const parts = dataKey.split('.');
      let data = this.reportData;
      for (const part of parts) {
        if (data === null || data === undefined) return null;
        data = data[part];
      }
      return data;
    }
    
    return this.reportData[dataKey];
  }
  renderMetricWidget(container, data, widget) {
    if (!data) {
      this.renderEmptyState(container, 'No data available');
      return;
    }
    
    let value = data;
    // Handle different data types
    if (typeof data === 'object') {
      if (Array.isArray(data)) {
        value = data.length;
      } else if (widget.valueKey && data[widget.valueKey] !== undefined) {
        value = data[widget.valueKey];
      } else {
        value = Object.keys(data).length;
      }
    }
    
    // Format the value based on widget config
    let formattedValue = value;
    if (widget.format) {
      switch (widget.format) {
        case 'number':
          formattedValue = new Intl.NumberFormat().format(value);
          break;
        case 'currency':
          formattedValue = new Intl.NumberFormat('en-US', { 
            style: 'currency', 
            currency: widget.currency || 'USD' 
          }).format(value);
          break;
        case 'percentage':
          formattedValue = new Intl.NumberFormat('en-US', { 
            style: 'percent',
            maximumFractionDigits: 2
          }).format(value / 100);
          break;
      }
    }
    
    container.innerHTML = `
      <div class="metric-value">${formattedValue}</div>
      <div class="metric-label">${widget.subtitle || ''}</div>
    `;
  }
  renderChartWidget(container, data, widget) {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      this.renderEmptyState(container, 'No data available for chart');
      return;
    }
    
    const canvasId = `chart-${widget.id}`;
    container.innerHTML = `<div class="chart-container"><canvas id="${canvasId}"></canvas></div>`;
    
    const ctx = this.shadowRoot.getElementById(canvasId);
    if (!ctx) return;
    
    let chartData, chartOptions;
    
    // Extract chart configuration
    const labels = this.extractChartLabels(data, widget);
    const datasets = this.extractChartDatasets(data, widget);
    
    chartData = { labels, datasets };
    chartOptions = this.getChartOptions(widget);
    
    // Use the global Chart instance
    const chart = new window.Chart(ctx, {
      type: widget.subtype || 'bar',
      data: chartData,
      options: chartOptions
    });
    
    this.charts.push(chart);
  }
  extractChartLabels(data, widget) {
    if (!data) return [];
    
    if (Array.isArray(data)) {
      if (widget.labelKey) {
        return data.map(item => item[widget.labelKey]);
      }
      return data.map((_, index) => `Item ${index + 1}`);
    }
    
    return Object.keys(data);
  }
  extractChartDatasets(data, widget) {
    if (!data) return [];
    
    let datasets = [];
    
    if (Array.isArray(data)) {
      if (widget.valueKey) {
        // Single series
        datasets.push({
          label: widget.datasetLabel || 'Value',
          data: data.map(item => item[widget.valueKey]),
          backgroundColor: this.getChartColors(1)[0],
          borderColor: widget.subtype === 'line' ? this.getChartColors(1)[0] : undefined
        });
      } else if (widget.seriesConfig) {
        // Multiple series
        datasets = widget.seriesConfig.map((series, index) => {
          return {
            label: series.label,
            data: data.map(item => item[series.valueKey]),
            backgroundColor: this.getChartColors(widget.seriesConfig.length)[index],
            borderColor: widget.subtype === 'line' ? this.getChartColors(widget.seriesConfig.length)[index] : undefined
          };
        });
      } else if (data[0] && typeof data[0] === 'object') {
        // Auto-detect value keys (exclude the label key)
        const valueKeys = Object.keys(data[0]).filter(key => key !== widget.labelKey);
        
        datasets = valueKeys.map((key, index) => {
          return {
            label: key,
            data: data.map(item => item[key]),
            backgroundColor: this.getChartColors(valueKeys.length)[index],
            borderColor: widget.subtype === 'line' ? this.getChartColors(valueKeys.length)[index] : undefined
          };
        });
      } else {
        // Simple array of values
        datasets.push({
          label: widget.datasetLabel || 'Value',
          data: data,
          backgroundColor: this.getChartColors(1)[0],
          borderColor: widget.subtype === 'line' ? this.getChartColors(1)[0] : undefined
        });
      }
    } else {
      // Object with key-value pairs
      datasets.push({
        label: widget.datasetLabel || 'Value',
        data: Object.values(data),
        backgroundColor: this.getChartColors(1)[0],
        borderColor: widget.subtype === 'line' ? this.getChartColors(1)[0] : undefined
      });
    }
    
    return datasets;
  }
  getChartOptions(widget) {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: widget.showLegend !== false,
          position: widget.legendPosition || 'top'
        },
        title: {
          display: !!widget.chartTitle,
          text: widget.chartTitle
        },
        tooltip: {
          enabled: true
        }
      }
    };
    
    // Additional options based on chart type
    switch (widget.subtype) {
      case 'pie':
      case 'doughnut':
        return {
          ...baseOptions,
          cutout: widget.subtype === 'doughnut' ? '50%' : undefined
        };
      case 'line':
        return {
          ...baseOptions,
          scales: {
            y: {
              beginAtZero: widget.beginAtZero !== false
            }
          },
          elements: {
            line: {
              tension: 0.2
            }
          }
        };
      case 'bar':
      default:
        return {
          ...baseOptions,
          scales: {
            y: {
              beginAtZero: widget.beginAtZero !== false
            }
          }
        };
    }
  }
  getChartColors(count) {
    const baseColors = [
      'rgba(66, 133, 244, 0.8)',  // Blue
      'rgba(219, 68, 55, 0.8)',   // Red
      'rgba(244, 180, 0, 0.8)',   // Yellow
      'rgba(15, 157, 88, 0.8)',   // Green
      'rgba(171, 71, 188, 0.8)',  // Purple
      'rgba(255, 112, 67, 0.8)',  // Orange
      'rgba(0, 172, 193, 0.8)',   // Cyan
      'rgba(124, 179, 66, 0.8)'   // Light green
    ];
    
    // If we need more colors than in our base set, generate them
    if (count <= baseColors.length) {
      return baseColors.slice(0, count);
    }
    
    const colors = [...baseColors];
    while (colors.length < count) {
      const r = Math.floor(Math.random() * 200 + 20);
      const g = Math.floor(Math.random() * 200 + 20);
      const b = Math.floor(Math.random() * 200 + 20);
      colors.push(`rgba(${r}, ${g}, ${b}, 0.8)`);
    }
    
    return colors;
  }
  renderTableWidget(container, data, widget) {
    if (!data || (Array.isArray(data) && data.length === 0)) {
      this.renderEmptyState(container, 'No data available for table');
      return;
    }
    
    // Determine columns
    let columns = [];
    if (widget.columns) {
      columns = widget.columns;
    } else if (Array.isArray(data) && data.length > 0) {
      columns = Object.keys(data[0]).map(key => {
        return { key, label: key.replace(/_/g, ' ') };
      });
    } else if (typeof data === 'object') {
      columns = [
        { key: 'key', label: 'Key' },
        { key: 'value', label: 'Value' }
      ];
    }
    
    // Prepare rows
    let rows = [];
    if (Array.isArray(data)) {
      rows = data;
    } else {
      rows = Object.entries(data).map(([key, value]) => {
        return { key, value };
      });
    }
    
    // Apply limit if specified
    if (widget.limit && rows.length > widget.limit) {
      rows = rows.slice(0, widget.limit);
    }
    
    // Generate table HTML
    let tableHTML = `
      <table>
        <thead>
          <tr>
            ${columns.map(col => `<th>${col.label || col.key}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
    `;
    
    rows.forEach(row => {
      tableHTML += '<tr>';
      columns.forEach(col => {
        const value = row[col.key];
        let displayValue = value;
        
        // Format cell value
        if (col.format) {
          switch (col.format) {
            case 'number':
              displayValue = new Intl.NumberFormat().format(value);
              break;
            case 'currency':
              displayValue = new Intl.NumberFormat('en-US', { 
                style: 'currency', 
                currency: col.currency || 'USD' 
              }).format(value);
              break;
            case 'date':
              displayValue = new Date(value).toLocaleDateString();
              break;
            case 'datetime':
              displayValue = new Date(value).toLocaleString();
              break;
            case 'percentage':
              displayValue = new Intl.NumberFormat('en-US', { 
                style: 'percent',
                maximumFractionDigits: 2
              }).format(value / 100);
              break;
          }
        }
        
        // Handle null/undefined values
        if (displayValue === null || displayValue === undefined) {
          displayValue = '-';
        }
        
        tableHTML += `<td>${displayValue}</td>`;
      });
      tableHTML += '</tr>';
    });
    
    tableHTML += `
        </tbody>
      </table>
    `;
    
    container.innerHTML = tableHTML;
  }
  renderEmptyState(container, message) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <div>${message || 'No data available'}</div>
      </div>
    `;
  }
  handleDateRangeChange(e, field) {
    this.dateRange = {
      ...this.dateRange,
      [field]: e.target.value
    };
    // In a real implementation, you would reload data with new date range
  }
  applyFilters() {
    // In a real implementation, you would reload data with filters
    this.loadReportData();
  }
  handleLayoutChange(e) {
    const newLayout = e.detail.layout;
    // Update widget positions based on new layout
    this.widgets = this.widgets.map(widget => {
      const layoutItem = newLayout.find(item => item.id === widget.id);
      if (layoutItem) {
        return {
          ...widget,
          x: layoutItem.x,
          y: layoutItem.y,
          w: layoutItem.w,
          h: layoutItem.h
        };
      }
      return widget;
    });
  }
  render() {
    return html`
      <div class="dashboard-container">
        <div class="controls">
          <div class="date-range">
            <span>Date Range:</span>
            <input type="date" .value=${this.dateRange.start} 
                  @change=${(e) => this.handleDateRangeChange(e, 'start')} />
            <span>to</span>
            <input type="date" .value=${this.dateRange.end} 
                  @change=${(e) => this.handleDateRangeChange(e, 'end')} />
          </div>
          
          <div class="filters">
            <!-- Add your custom filters here -->
          </div>
          
          <div class="actions">
            <button @click=${this.applyFilters}>Apply Filters</button>
            <button @click=${this.refreshData}>Refresh</button>
            <button @click=${() => this.exportDashboard('pdf')}>Export PDF</button>
            <button @click=${() => this.exportDashboard('xlsx')}>Export Excel</button>
          </div>
        </div>
        
        ${this.error ? html`
          <div class="error">
            ${this.error}
            <button @click=${this.refreshData}>Retry</button>
          </div>
        ` : ''}
        
        ${this.loading ? html`
          <div class="loading-overlay">
            Loading dashboard data...
          </div>
        ` : ''}
        
        <div class="dashboard-grid">
          ${this.widgets.map(widget => {
            const style = `
              grid-column: ${widget.x || 0} / span ${widget.w || 3};
              grid-row: ${widget.y || 0} / span ${widget.h || 3};
            `;
            
            return html`
              <div id="widget-${widget.id}" class="widget" style=${style}>
                <div class="widget-header">
                  <h3 class="widget-title">${widget.title}</h3>
                  <div class="widget-actions">
                    <button class="widget-action-btn" title="Refresh" @click=${() => this.refreshWidgetData(widget)}>
                      🔄
                    </button>
                    <button class="widget-action-btn" title="Download" @click=${() => this.downloadWidgetData(widget)}>
                      ⬇️
                    </button>
                  </div>
                </div>
                <div class="widget-content"></div>
              </div>
            `;
          })}
        </div>
      </div>
    `;
  }
  refreshWidgetData(widget) {
    // In a real implementation, you would reload just this widget's data
    this.loadReportData();
  }
  downloadWidgetData(widget) {
    const data = this.getWidgetData(widget.dataKey);
    if (!data) return;
    
    // Convert data to CSV
    let csv;
    if (Array.isArray(data)) {
      const headers = Object.keys(data[0]).join(',');
      const rows = data.map(item => Object.values(item).join(','));
      csv = [headers, ...rows].join('\n');
    } else {
      csv = Object.entries(data).map(([key, value]) => `${key},${value}`).join('\n');
    }
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${widget.title.replace(/\s+/g, '_')}_data.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
customElements.define('report-dashboard', ReportDashboard);