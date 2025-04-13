import { LitElement, html, css } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-date-picker.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-table.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-divider.js';

/**
 * @element wa-report-execution-manager
 * @description Component for managing report executions including scheduling, monitoring, and viewing results
 * @property {String} templateId - The ID of the report template being managed
 * @property {Object} template - The report template object
 * @property {Array} executions - List of recent executions for this report template
 * @property {Object} schedules - List of schedules for this report template
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 * @property {String} activeTab - Currently active tab
 */
export class WebAwesomeReportExecutionManager extends LitElement {
  static get properties() {
    return {
      templateId: { type: String },
      template: { type: Object },
      executions: { type: Array },
      schedules: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      activeTab: { type: String },
      showScheduleDialog: { type: Boolean },
      currentSchedule: { type: Object },
      showExecuteDialog: { type: Boolean },
      executionParameters: { type: Object },
      sortBy: { type: String },
      sortDirection: { type: String },
      filters: { type: Object }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --manager-bg: var(--wa-background-color, #f5f5f5);
        --manager-padding: 20px;
        --section-gap: 24px;
      }
      .manager-container {
        padding: var(--manager-padding);
        background-color: var(--manager-bg);
        min-height: 600px;
      }
      .manager-header {
        margin-bottom: var(--section-gap);
      }
      .manager-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .manager-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
      }
      .section-title {
        font-size: 18px;
        font-weight: 500;
        margin: 24px 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .filter-bar {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        background-color: var(--wa-surface-color, #ffffff);
        padding: 12px 16px;
        border-radius: var(--wa-border-radius, 4px);
        margin-bottom: 16px;
      }
      .status-chip {
        display: inline-flex;
        align-items: center;
        border-radius: 16px;
        font-size: 13px;
        padding: 4px 12px;
        font-weight: 500;
      }
      .status-completed {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.12));
        color: var(--wa-success-color, #4caf50);
      }
      .status-failed {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.12));
        color: var(--wa-error-color, #f44336);
      }
      .status-pending {
        background-color: var(--wa-warning-color-light, rgba(255, 152, 0, 0.12));
        color: var(--wa-warning-color, #ff9800);
      }
      .status-in-progress {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.12));
        color: var(--wa-primary-color, #3f51b5);
      }
      .status-canceled {
        background-color: var(--wa-default-color-light, rgba(158, 158, 158, 0.12));
        color: var(--wa-default-color, #9e9e9e);
      }
      .schedule-item {
        padding: 16px;
        margin-bottom: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .schedule-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }
      .schedule-name {
        font-weight: 500;
        font-size: 16px;
      }
      .schedule-details {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 12px;
      }
      .detail-label {
        font-size: 13px;
        color: var(--wa-text-secondary-color, #757575);
        margin-bottom: 4px;
      }
      .detail-value {
        font-size: 14px;
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px;
        text-align: center;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        color: var(--wa-text-secondary-color, #757575);
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-disabled-color, #bdbdbd);
      }
      .parameter-section {
        margin-top: 24px;
      }
      .parameter-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-top: 16px;
      }
      .button-row {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 24px;
      }
      .execution-detail {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      .execution-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
        font-size: 13px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .execution-meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .cron-helper {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.12));
        padding: 12px 16px;
        border-radius: var(--wa-border-radius, 4px);
        margin-top: 12px;
        margin-bottom: 16px;
      }
      .cron-helper-title {
        font-weight: 500;
        margin-bottom: 8px;
      }
      .cron-examples {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 8px;
        margin-top: 8px;
      }
      .cron-example {
        background-color: var(--wa-surface-color, #ffffff);
        padding: 8px 12px;
        border-radius: var(--wa-border-radius, 4px);
        cursor: pointer;
      }
      .cron-example:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .cron-value {
        font-family: monospace;
        font-weight: 500;
      }
      .cron-description {
        font-size: 13px;
        color: var(--wa-text-secondary-color, #757575);
      }
    `;
  }

  constructor() {
    super();
    this.templateId = '';
    this.template = null;
    this.executions = [];
    this.schedules = [];
    this.loading = false;
    this.error = null;
    this.activeTab = 'executions';
    this.showScheduleDialog = false;
    this.currentSchedule = null;
    this.showExecuteDialog = false;
    this.executionParameters = {};
    this.sortBy = 'started_at';
    this.sortDirection = 'desc';
    this.filters = {
      status: ''
    };
    this._refreshTimer = null;
  }

  connectedCallback() {
    super.connectedCallback();
    
    if (this.templateId) {
      this.loadTemplate();
      this.loadExecutions();
      this.loadSchedules();
    }
    
    // Auto refresh active executions
    this._refreshTimer = setInterval(() => {
      this.refreshActiveExecutions();
    }, 30000); // 30 seconds
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
  }

  updated(changedProperties) {
    if (changedProperties.has('templateId') && this.templateId) {
      this.loadTemplate();
      this.loadExecutions();
      this.loadSchedules();
    }
  }

  async loadTemplate() {
    if (!this.templateId) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`/api/reports/templates/${this.templateId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.template = await response.json();
      
      // Initialize execution parameters based on template parameters
      this.executionParameters = {};
      if (this.template && this.template.fields) {
        this.template.fields
          .filter(field => field.type === 'parameter')
          .forEach(param => {
            this.executionParameters[param.name] = param.default || '';
          });
      }
      
    } catch (err) {
      console.error('Failed to load template:', err);
      this.error = `Error loading template: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  async loadExecutions() {
    if (!this.templateId) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      // Build query params
      const params = new URLSearchParams();
      
      // Add template ID
      params.append('template_id', this.templateId);
      
      // Add sort
      params.append('sort_by', this.sortBy);
      params.append('sort_dir', this.sortDirection);
      
      // Add filters
      if (this.filters.status) {
        params.append('status', this.filters.status);
      }
      
      // Add pagination (limit to recent executions)
      params.append('limit', '50');
      
      const response = await fetch(`/api/reports/executions?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.executions = await response.json();
      
    } catch (err) {
      console.error('Failed to load executions:', err);
      this.error = `Error loading executions: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  async loadSchedules() {
    if (!this.templateId) return;
    
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`/api/reports/schedules?template_id=${this.templateId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.schedules = await response.json();
      
    } catch (err) {
      console.error('Failed to load schedules:', err);
      this.error = `Error loading schedules: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  async refreshActiveExecutions() {
    // Only refresh if we have active executions
    const activeExecutions = this.executions.filter(exec => 
      exec.status === 'pending' || exec.status === 'in_progress'
    );
    
    if (activeExecutions.length === 0) return;
    
    try {
      // Create a batch request for each active execution
      const executionIds = activeExecutions.map(exec => exec.id);
      const queryParams = new URLSearchParams();
      executionIds.forEach(id => queryParams.append('ids', id));
      
      const response = await fetch(`/api/reports/executions/status?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const statusUpdates = await response.json();
      
      // Update local execution data
      let hasChanges = false;
      
      this.executions = this.executions.map(exec => {
        const update = statusUpdates.find(update => update.id === exec.id);
        if (update && update.status !== exec.status) {
          hasChanges = true;
          return {...exec, ...update};
        }
        return exec;
      });
      
      // If status has changed, refresh the full list
      if (hasChanges) {
        this.loadExecutions();
      }
      
    } catch (err) {
      console.error('Failed to refresh execution status:', err);
      // Don't show error for background refresh
    }
  }

  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }

  showAddSchedule() {
    this.currentSchedule = {
      name: '',
      template_id: this.templateId,
      type: 'cron',
      cron_expression: '0 0 * * *', // Daily at midnight
      enabled: true,
      parameters: {},
      next_run_date: null
    };
    this.showScheduleDialog = true;
  }

  showEditSchedule(schedule) {
    this.currentSchedule = {...schedule};
    this.showScheduleDialog = true;
  }

  closeScheduleDialog() {
    this.showScheduleDialog = false;
    this.currentSchedule = null;
  }

  handleScheduleChange(field, value) {
    this.currentSchedule = {
      ...this.currentSchedule,
      [field]: value
    };
  }

  handleScheduleParameterChange(paramName, value) {
    this.currentSchedule = {
      ...this.currentSchedule,
      parameters: {
        ...this.currentSchedule.parameters,
        [paramName]: value
      }
    };
  }

  applyCronExample(cronExpression) {
    this.currentSchedule = {
      ...this.currentSchedule,
      cron_expression: cronExpression
    };
  }

  async saveSchedule() {
    if (!this.currentSchedule.name) {
      this._showNotification('Schedule name is required', 'error');
      return;
    }
    
    if (!this.currentSchedule.cron_expression) {
      this._showNotification('Cron expression is required', 'error');
      return;
    }
    
    this.loading = true;
    
    try {
      const method = this.currentSchedule.id ? 'PUT' : 'POST';
      const endpoint = this.currentSchedule.id ? 
        `/api/reports/schedules/${this.currentSchedule.id}` : 
        '/api/reports/schedules';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.currentSchedule)
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      // Show success notification
      this._showNotification(
        `Schedule ${this.currentSchedule.id ? 'updated' : 'created'} successfully`, 
        'success'
      );
      
      // Reload schedules
      await this.loadSchedules();
      
      // Close dialog
      this.closeScheduleDialog();
      
    } catch (err) {
      console.error('Failed to save schedule:', err);
      this._showNotification(`Error saving schedule: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  async toggleScheduleStatus(scheduleId, currentEnabled) {
    this.loading = true;
    
    try {
      const response = await fetch(`/api/reports/schedules/${scheduleId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          enabled: !currentEnabled
        })
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      // Show success notification
      this._showNotification(
        `Schedule ${currentEnabled ? 'disabled' : 'enabled'} successfully`, 
        'success'
      );
      
      // Reload schedules
      await this.loadSchedules();
      
    } catch (err) {
      console.error('Failed to toggle schedule status:', err);
      this._showNotification(`Error updating schedule: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  async deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    
    this.loading = true;
    
    try {
      const response = await fetch(`/api/reports/schedules/${scheduleId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      // Show success notification
      this._showNotification('Schedule deleted successfully', 'success');
      
      // Reload schedules
      await this.loadSchedules();
      
    } catch (err) {
      console.error('Failed to delete schedule:', err);
      this._showNotification(`Error deleting schedule: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  showExecuteNow() {
    // Reset parameters to default values
    this.executionParameters = {};
    
    if (this.template && this.template.fields) {
      this.template.fields
        .filter(field => field.type === 'parameter')
        .forEach(param => {
          this.executionParameters[param.name] = param.default || '';
        });
    }
    
    this.showExecuteDialog = true;
  }

  closeExecuteDialog() {
    this.showExecuteDialog = false;
  }

  handleParameterChange(paramName, value) {
    this.executionParameters = {
      ...this.executionParameters,
      [paramName]: value
    };
  }

  async executeReport() {
    this.loading = true;
    
    try {
      const response = await fetch('/api/reports/executions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template_id: this.templateId,
          parameters: this.executionParameters,
          trigger_type: 'manual'
        })
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const result = await response.json();
      
      // Show success notification
      this._showNotification('Report execution started successfully', 'success');
      
      // Close dialog
      this.closeExecuteDialog();
      
      // Reload executions
      await this.loadExecutions();
      
      // Navigate to the execution view
      if (result && result.execution_id) {
        this.navigateToExecution(result.execution_id);
      }
      
    } catch (err) {
      console.error('Failed to execute report:', err);
      this._showNotification(`Error executing report: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  navigateToExecution(executionId) {
    window.location.href = `/reports/executions/${executionId}`;
  }

  handleSortChange(field) {
    if (this.sortBy === field) {
      // Toggle direction
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      // New field, default to descending
      this.sortBy = field;
      this.sortDirection = 'desc';
    }
    
    this.loadExecutions();
  }

  handleStatusFilterChange(e) {
    this.filters.status = e.target.value;
    this.loadExecutions();
  }

  formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
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

  getStatusClass(status) {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'failed': return 'status-failed';
      case 'pending': return 'status-pending';
      case 'in_progress': return 'status-in-progress';
      case 'canceled': return 'status-canceled';
      default: return '';
    }
  }

  _showNotification(message, type = 'info') {
    // Create and show a notification
    const alertEl = document.createElement('wa-alert');
    alertEl.type = type;
    alertEl.message = message;
    alertEl.duration = 5000;
    alertEl.position = 'top-right';
    
    document.body.appendChild(alertEl);
    alertEl.show();
    
    alertEl.addEventListener('close', () => {
      document.body.removeChild(alertEl);
    });
  }

  renderExecutionsTab() {
    const hasExecutions = this.executions && this.executions.length > 0;
    
    return html`
      <div>
        <div class="controls">
          <wa-button @click=${this.showExecuteNow}>
            <wa-icon slot="prefix" name="play_arrow"></wa-icon>
            Execute Now
          </wa-button>
          
          <div class="filter-bar">
            <wa-select 
              label="Status" 
              @change=${this.handleStatusFilterChange}
              .value=${this.filters.status}>
              <wa-option value="">All Statuses</wa-option>
              <wa-option value="completed">Completed</wa-option>
              <wa-option value="failed">Failed</wa-option>
              <wa-option value="pending">Pending</wa-option>
              <wa-option value="in_progress">In Progress</wa-option>
              <wa-option value="canceled">Canceled</wa-option>
            </wa-select>
            
            <wa-button variant="text" @click=${this.loadExecutions}>
              <wa-icon slot="prefix" name="refresh"></wa-icon>
              Refresh
            </wa-button>
          </div>
        </div>
        
        ${!hasExecutions ? html`
          <div class="empty-state">
            <wa-icon name="history" size="xlarge" class="empty-state-icon"></wa-icon>
            <h3>No executions found</h3>
            <p>There are no report executions matching your criteria.</p>
            <wa-button @click=${this.showExecuteNow}>Execute Report Now</wa-button>
          </div>
        ` : html`
          <wa-table
            .columns=${[
              { name: 'id', label: 'ID' },
              { name: 'status', label: 'Status' },
              { name: 'started_at', label: 'Started' },
              { name: 'trigger_type', label: 'Trigger' },
              { name: 'actions', label: 'Actions' }
            ]}
            .sortable=${true}
            .sortBy=${this.sortBy}
            .sortDirection=${this.sortDirection}
            @sort-changed=${e => this.handleSortChange(e.detail.column)}
          >
            ${repeat(this.executions, execution => execution.id, execution => html`
              <tr>
                <td class="execution-detail">
                  <div>
                    <div>${execution.id.substring(0, 8)}...</div>
                    <div class="execution-meta">
                      ${execution.row_count !== undefined ? html`
                        <span class="execution-meta-item">
                          <wa-icon name="data_array" size="small"></wa-icon>
                          ${execution.row_count.toLocaleString()} rows
                        </span>
                      ` : ''}
                      ${execution.execution_time_ms ? html`
                        <span class="execution-meta-item">
                          <wa-icon name="timer" size="small"></wa-icon>
                          ${(execution.execution_time_ms / 1000).toFixed(2)}s
                        </span>
                      ` : ''}
                    </div>
                  </div>
                </td>
                <td>
                  <span class="status-chip ${this.getStatusClass(execution.status)}">
                    ${execution.status}
                  </span>
                </td>
                <td>
                  <div>${this.formatDate(execution.started_at)}</div>
                  ${execution.completed_at ? html`
                    <div class="execution-meta">
                      Completed: ${this.formatDate(execution.completed_at)}<br>
                      Duration: ${this.formatDuration(execution.started_at, execution.completed_at)}
                    </div>
                  ` : ''}
                </td>
                <td>
                  <wa-chip size="small">
                    ${execution.trigger_type || 'manual'}
                  </wa-chip>
                </td>
                <td>
                  <wa-button variant="text" @click=${() => this.navigateToExecution(execution.id)}>
                    View Details
                  </wa-button>
                  ${execution.status === 'completed' ? html`
                    <wa-button variant="text" @click=${() => window.open(`/api/reports/executions/${execution.id}/download?format=csv`, '_blank')}>
                      <wa-icon slot="prefix" name="download"></wa-icon>
                      CSV
                    </wa-button>
                  ` : ''}
                </td>
              </tr>
            `)}
          </wa-table>
        `}
      </div>
    `;
  }

  renderSchedulesTab() {
    const hasSchedules = this.schedules && this.schedules.length > 0;
    
    return html`
      <div>
        <div class="controls">
          <wa-button @click=${this.showAddSchedule}>
            <wa-icon slot="prefix" name="add"></wa-icon>
            Add Schedule
          </wa-button>
          
          <wa-button variant="text" @click=${this.loadSchedules}>
            <wa-icon slot="prefix" name="refresh"></wa-icon>
            Refresh
          </wa-button>
        </div>
        
        ${!hasSchedules ? html`
          <div class="empty-state">
            <wa-icon name="schedule" size="xlarge" class="empty-state-icon"></wa-icon>
            <h3>No schedules found</h3>
            <p>Add a schedule to automate this report's execution.</p>
            <wa-button @click=${this.showAddSchedule}>Add Schedule</wa-button>
          </div>
        ` : html`
          ${repeat(this.schedules, schedule => schedule.id, schedule => html`
            <div class="schedule-item">
              <div class="schedule-header">
                <div class="schedule-name">
                  ${schedule.name}
                  <wa-chip size="small" color=${schedule.enabled ? 'success' : 'default'}>
                    ${schedule.enabled ? 'Enabled' : 'Disabled'}
                  </wa-chip>
                </div>
                <div>
                  <wa-button variant="text" @click=${() => this.showEditSchedule(schedule)}>Edit</wa-button>
                  <wa-button variant="text" @click=${() => this.toggleScheduleStatus(schedule.id, schedule.enabled)}>
                    ${schedule.enabled ? 'Disable' : 'Enable'}
                  </wa-button>
                  <wa-button variant="text" color="error" @click=${() => this.deleteSchedule(schedule.id)}>Delete</wa-button>
                </div>
              </div>
              
              <div class="schedule-details">
                <div>
                  <div class="detail-label">Schedule Type</div>
                  <div class="detail-value">${schedule.type === 'cron' ? 'Cron Expression' : schedule.type}</div>
                </div>
                
                <div>
                  <div class="detail-label">Schedule Pattern</div>
                  <div class="detail-value">${schedule.cron_expression}</div>
                </div>
                
                <div>
                  <div class="detail-label">Next Run</div>
                  <div class="detail-value">${schedule.next_run_date ? this.formatDate(schedule.next_run_date) : 'Not scheduled'}</div>
                </div>
                
                <div>
                  <div class="detail-label">Last Run</div>
                  <div class="detail-value">${schedule.last_run_date ? this.formatDate(schedule.last_run_date) : 'Never'}</div>
                </div>
              </div>
              
              ${schedule.last_execution_id ? html`
                <div>
                  <wa-button variant="text" @click=${() => this.navigateToExecution(schedule.last_execution_id)}>
                    View Last Execution
                  </wa-button>
                </div>
              ` : ''}
              
              ${Object.keys(schedule.parameters || {}).length > 0 ? html`
                <wa-divider style="margin: 16px 0;"></wa-divider>
                <div>
                  <div class="detail-label">Parameters</div>
                  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                    ${Object.entries(schedule.parameters).map(([key, value]) => html`
                      <wa-chip>
                        ${key}: ${value}
                      </wa-chip>
                    `)}
                  </div>
                </div>
              ` : ''}
            </div>
          `)}
        `}
      </div>
    `;
  }

  renderScheduleDialog() {
    if (!this.showScheduleDialog || !this.currentSchedule) return html``;
    
    // Check if template has parameters
    const hasParameters = this.template && this.template.fields && 
      this.template.fields.some(field => field.type === 'parameter');
    
    const cronExamples = [
      { value: '0 0 * * *', desc: 'Daily at midnight' },
      { value: '0 12 * * *', desc: 'Daily at noon' },
      { value: '0 0 * * 1', desc: 'Weekly on Monday at midnight' },
      { value: '0 0 1 * *', desc: 'Monthly on the 1st at midnight' },
      { value: '0 0 1 1 *', desc: 'Yearly on Jan 1st at midnight' },
      { value: '0 */2 * * *', desc: 'Every 2 hours' },
      { value: '0 9-17 * * 1-5', desc: 'Every hour 9-5, Monday to Friday' },
      { value: '0 0,12 * * *', desc: 'Twice daily at midnight and noon' }
    ];
    
    return html`
      <wa-dialog open @close=${this.closeScheduleDialog}>
        <div slot="header">
          ${this.currentSchedule.id ? 'Edit Schedule' : 'Add Schedule'}
        </div>
        
        <div>
          <wa-input 
            label="Schedule Name"
            required
            .value=${this.currentSchedule.name}
            @input=${e => this.handleScheduleChange('name', e.target.value)}
            placeholder="e.g., Daily Sales Report">
          </wa-input>
          
          <div style="margin-top: 16px;">
            <wa-select 
              label="Schedule Type"
              .value=${this.currentSchedule.type}
              @change=${e => this.handleScheduleChange('type', e.target.value)}>
              <wa-option value="cron">Cron Expression</wa-option>
            </wa-select>
          </div>
          
          <div style="margin-top: 16px;">
            <wa-input 
              label="Cron Expression"
              required
              .value=${this.currentSchedule.cron_expression}
              @input=${e => this.handleScheduleChange('cron_expression', e.target.value)}
              placeholder="e.g., 0 0 * * * (daily at midnight)">
            </wa-input>
            
            <div class="cron-helper">
              <div class="cron-helper-title">Common Cron Patterns</div>
              <div class="cron-description">Click any example to use it:</div>
              <div class="cron-examples">
                ${cronExamples.map(example => html`
                  <div class="cron-example" @click=${() => this.applyCronExample(example.value)}>
                    <div class="cron-value">${example.value}</div>
                    <div class="cron-description">${example.desc}</div>
                  </div>
                `)}
              </div>
            </div>
          </div>
          
          <wa-checkbox
            .checked=${this.currentSchedule.enabled}
            @change=${e => this.handleScheduleChange('enabled', e.target.checked)}>
            Schedule Enabled
          </wa-checkbox>
          
          ${hasParameters ? html`
            <div class="parameter-section">
              <div class="section-title">Parameters</div>
              <p>Set parameter values for this scheduled execution:</p>
              
              <div class="parameter-list">
                ${this.template.fields
                  .filter(field => field.type === 'parameter')
                  .map(param => html`
                    <wa-input 
                      label="${param.display_name || param.name}"
                      .value=${this.currentSchedule.parameters[param.name] || param.default || ''}
                      @input=${e => this.handleScheduleParameterChange(param.name, e.target.value)}
                      placeholder=${param.default || ''}>
                    </wa-input>
                  `)}
              </div>
            </div>
          ` : ''}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeScheduleDialog}>Cancel</wa-button>
          <wa-button @click=${this.saveSchedule}>
            ${this.currentSchedule.id ? 'Update' : 'Create'} Schedule
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }

  renderExecuteDialog() {
    if (!this.showExecuteDialog) return html``;
    
    // Check if template has parameters
    const hasParameters = this.template && this.template.fields && 
      this.template.fields.some(field => field.type === 'parameter');
    
    return html`
      <wa-dialog open @close=${this.closeExecuteDialog}>
        <div slot="header">Execute Report</div>
        
        <div>
          <p>You are about to execute ${this.template?.name || 'this report'}.</p>
          
          ${hasParameters ? html`
            <div class="parameter-section">
              <div class="section-title">Parameters</div>
              <p>Set parameter values for this execution:</p>
              
              <div class="parameter-list">
                ${this.template.fields
                  .filter(field => field.type === 'parameter')
                  .map(param => html`
                    <wa-input 
                      label="${param.display_name || param.name}"
                      .value=${this.executionParameters[param.name] || ''}
                      @input=${e => this.handleParameterChange(param.name, e.target.value)}
                      placeholder=${param.default || ''}>
                    </wa-input>
                  `)}
              </div>
            </div>
          ` : ''}
          
          <div class="button-row">
            <wa-button variant="outlined" @click=${this.closeExecuteDialog}>Cancel</wa-button>
            <wa-button @click=${this.executeReport}>Execute Now</wa-button>
          </div>
        </div>
      </wa-dialog>
    `;
  }

  render() {
    return html`
      <div class="manager-container">
        <div class="manager-header">
          <h1 class="manager-title">
            ${this.template ? this.template.name : 'Report'} Execution Manager
          </h1>
          <p class="manager-subtitle">
            Manage executions and schedules for this report
          </p>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error">
            ${this.error}
            <wa-button slot="action" variant="text" @click=${() => this.loadTemplate()}>Try Again</wa-button>
          </wa-alert>
        ` : ''}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="executions">Executions</wa-tab>
          <wa-tab value="schedules">Schedules</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="executions" ?active=${this.activeTab === 'executions'}>
          ${this.renderExecutionsTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="schedules" ?active=${this.activeTab === 'schedules'}>
          ${this.renderSchedulesTab()}
        </wa-tab-panel>
        
        ${this.renderScheduleDialog()}
        ${this.renderExecuteDialog()}
        
        ${this.loading ? html`
          <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                    background: rgba(255, 255, 255, 0.7); display: flex; 
                    align-items: center; justify-content: center; z-index: 9999;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('wa-report-execution-manager', WebAwesomeReportExecutionManager);