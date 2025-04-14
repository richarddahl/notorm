import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-report-parameter-form
 * @description Form component for entering report parameters before execution using WebAwesome components
 * @property {String} templateId - The ID of the report template to execute
 * @property {Object} template - The report template object
 * @property {Object} parameters - The parameter values
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 */
export class WebAwesomeReportParameterForm extends LitElement {
  static get properties() {
    return {
      templateId: { type: String },
      template: { type: Object },
      parameters: { type: Object },
      loading: { type: Boolean },
      error: { type: String },
      formValid: { type: Boolean },
      validationErrors: { type: Object },
      recentExecutions: { type: Array },
      outputOptions: { type: Object }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --form-bg: var(--wa-background-color, #f5f5f5);
        --form-padding: 20px;
      }
      .form-container {
        padding: var(--form-padding);
        background-color: var(--form-bg);
        min-height: 400px;
      }
      .form-header {
        margin-bottom: 24px;
      }
      .form-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .form-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .parameter-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin-bottom: 24px;
      }
      .parameter-full-width {
        grid-column: 1 / -1;
      }
      .button-row {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 24px;
      }
      .section-title {
        font-size: 18px;
        font-weight: 500;
        margin: 24px 0 16px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .output-options {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .output-option {
        padding: 16px;
        border: 2px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        cursor: pointer;
        text-align: center;
        transition: all 0.2s ease;
      }
      .output-option:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .output-option.selected {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
      .output-icon {
        font-size: 32px;
        margin-bottom: 8px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .output-option.selected .output-icon {
        color: var(--wa-primary-color, #3f51b5);
      }
      .executions-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 24px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        overflow: hidden;
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .executions-table th, .executions-table td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .executions-table th {
        font-weight: 500;
        color: var(--wa-text-primary-color, #212121);
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.05));
      }
      .executions-table tr:last-child td {
        border-bottom: none;
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
      .info-message {
        background-color: var(--wa-info-color-light, rgba(25, 118, 210, 0.08));
        color: var(--wa-text-primary-color, #212121);
        border-radius: var(--wa-border-radius, 4px);
        padding: 16px;
        margin-bottom: 24px;
        border-left: 4px solid var(--wa-info-color, #1976d2);
      }
      .validation-error {
        color: var(--wa-error-color, #f44336);
        font-size: 13px;
        margin-top: 4px;
      }
    `;
  }
  constructor() {
    super();
    this.templateId = '';
    this.template = null;
    this.parameters = {};
    this.loading = false;
    this.error = null;
    this.formValid = true;
    this.validationErrors = {};
    this.recentExecutions = [];
    this.outputOptions = {
      format: 'view', // view, csv, excel, pdf
      delivery: 'browser' // browser, email
    };
  }
  connectedCallback() {
    super.connectedCallback();
    
    if (this.templateId) {
      this.loadTemplate();
      this.loadRecentExecutions();
    }
  }
  updated(changedProperties) {
    if (changedProperties.has('templateId') && this.templateId) {
      this.loadTemplate();
      this.loadRecentExecutions();
    }
    
    if (changedProperties.has('parameters')) {
      this.validateForm();
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
      
      // Initialize parameters with default values
      const newParams = {};
      if (this.template && this.template.fields) {
        this.template.fields
          .filter(field => field.type === 'parameter')
          .forEach(param => {
            newParams[param.name] = param.default !== undefined ? param.default : '';
          });
      }
      this.parameters = newParams;
      
    } catch (err) {
      console.error('Failed to load template:', err);
      this.error = `Error loading template: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }
  async loadRecentExecutions() {
    if (!this.templateId) return;
    
    try {
      const params = new URLSearchParams();
      params.append('template_id', this.templateId);
      params.append('limit', '5');
      params.append('sort_by', 'started_at');
      params.append('sort_dir', 'desc');
      
      const response = await fetch(`/api/reports/executions?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.recentExecutions = await response.json();
      
    } catch (err) {
      console.error('Failed to load recent executions:', err);
      // Don't show error for this secondary feature
    }
  }
  handleParameterChange(paramName, value) {
    this.parameters = {
      ...this.parameters,
      [paramName]: value
    };
    
    // Clear validation error for this field if it exists
    if (this.validationErrors[paramName]) {
      const newErrors = {...this.validationErrors};
      delete newErrors[paramName];
      this.validationErrors = newErrors;
    }
  }
  validateForm() {
    const errors = {};
    let isValid = true;
    
    // Only validate if we have template data
    if (this.template && this.template.fields) {
      this.template.fields
        .filter(field => field.type === 'parameter')
        .forEach(param => {
          // Check required parameters
          if (param.required && 
              (this.parameters[param.name] === undefined || this.parameters[param.name] === '')) {
            errors[param.name] = 'This field is required';
            isValid = false;
          }
          
          // Validate by parameter type
          if (this.parameters[param.name] !== undefined && this.parameters[param.name] !== '') {
            switch (param.parameter_type) {
              case 'number':
                if (isNaN(Number(this.parameters[param.name]))) {
                  errors[param.name] = 'Must be a valid number';
                  isValid = false;
                }
                break;
              case 'date':
                if (!/^\d{4}-\d{2}-\d{2}$/.test(this.parameters[param.name]) && 
                    !Date.parse(this.parameters[param.name])) {
                  errors[param.name] = 'Must be a valid date';
                  isValid = false;
                }
                break;
              case 'boolean':
                if (typeof this.parameters[param.name] !== 'boolean' && 
                    !['true', 'false', '0', '1'].includes(String(this.parameters[param.name]).toLowerCase())) {
                  errors[param.name] = 'Must be a boolean value';
                  isValid = false;
                }
                break;
              // Add more validations as needed
            }
          }
        });
    }
    
    this.formValid = isValid;
    this.validationErrors = errors;
    
    return isValid;
  }
  selectOutputFormat(format) {
    this.outputOptions = {
      ...this.outputOptions,
      format
    };
  }
  selectDeliveryMethod(delivery) {
    this.outputOptions = {
      ...this.outputOptions,
      delivery
    };
  }
  async executeReport() {
    if (!this.validateForm()) {
      this._showNotification('Please fix the validation errors before executing the report', 'error');
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch('/api/reports/executions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          template_id: this.templateId,
          parameters: this.parameters,
          trigger_type: 'manual',
          output_format: this.outputOptions.format,
          delivery_method: this.outputOptions.delivery
        })
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      const result = await response.json();
      
      // Show success notification
      this._showNotification('Report execution started successfully', 'success');
      
      // Handle different output formats
      if (this.outputOptions.format !== 'view' && this.outputOptions.delivery === 'browser' && result.execution_id) {
        // For direct download formats, navigate to the download URL
        window.location.href = `/api/reports/executions/${result.execution_id}/download?format=${this.outputOptions.format}`;
      } else if (this.outputOptions.format === 'view' && result.execution_id) {
        // For viewing in browser, navigate to the execution view
        window.location.href = `/reports/executions/${result.execution_id}`;
      } else if (this.outputOptions.delivery === 'email') {
        // For email delivery, just display a success message
        this._showNotification('The report will be delivered to your email when complete', 'success');
      }
      
    } catch (err) {
      console.error('Failed to execute report:', err);
      this._showNotification(`Error executing report: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  cancel() {
    // Navigate back to the previous page
    window.history.back();
  }
  formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
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
  navigateToExecution(executionId) {
    window.location.href = `/reports/executions/${executionId}`;
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
  render() {
    if (this.loading && !this.template) {
      return html`
        <div class="form-container">
          <div style="display: flex; justify-content: center; padding: 48px;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        </div>
      `;
    }
    
    if (this.error) {
      return html`
        <div class="form-container">
          <wa-alert type="error">
            ${this.error}
            <wa-button slot="action" variant="text" @click=${this.loadTemplate}>
              Try Again
            </wa-button>
          </wa-alert>
        </div>
      `;
    }
    
    if (!this.template) {
      return html`
        <div class="form-container">
          <wa-alert type="warning">
            No template found with ID ${this.templateId}
          </wa-alert>
        </div>
      `;
    }
    
    // Get parameter fields
    const parameterFields = this.template.fields?.filter(field => field.type === 'parameter') || [];
    
    return html`
      <div class="form-container">
        <div class="form-header">
          <h1 class="form-title">Execute ${this.template.name}</h1>
          <p class="form-subtitle">Set parameters and output options for this report</p>
        </div>
        
        ${parameterFields.length > 0 ? html`
          <div class="section-title">Parameters</div>
          
          <div class="parameter-list">
            ${parameterFields.map(param => html`
              <div class=${param.parameter_type === 'textarea' ? 'parameter-full-width' : ''}>
                ${this.renderParameterInput(param)}
                ${this.validationErrors[param.name] ? html`
                  <div class="validation-error">${this.validationErrors[param.name]}</div>
                ` : ''}
              </div>
            `)}
          </div>
        ` : html`
          <div class="info-message">
            <wa-icon name="info" style="margin-right: 8px;"></wa-icon>
            This report doesn't require any parameters
          </div>
        `}
        
        <div class="section-title">Output Options</div>
        
        <div class="output-options">
          <div class="output-option ${this.outputOptions.format === 'view' ? 'selected' : ''}"
               @click=${() => this.selectOutputFormat('view')}>
            <wa-icon name="visibility" class="output-icon"></wa-icon>
            <div>View Online</div>
          </div>
          
          <div class="output-option ${this.outputOptions.format === 'csv' ? 'selected' : ''}"
               @click=${() => this.selectOutputFormat('csv')}>
            <wa-icon name="grid_on" class="output-icon"></wa-icon>
            <div>CSV</div>
          </div>
          
          <div class="output-option ${this.outputOptions.format === 'excel' ? 'selected' : ''}"
               @click=${() => this.selectOutputFormat('excel')}>
            <wa-icon name="table_chart" class="output-icon"></wa-icon>
            <div>Excel</div>
          </div>
          
          <div class="output-option ${this.outputOptions.format === 'pdf' ? 'selected' : ''}"
               @click=${() => this.selectOutputFormat('pdf')}>
            <wa-icon name="picture_as_pdf" class="output-icon"></wa-icon>
            <div>PDF</div>
          </div>
        </div>
        
        <div style="margin-bottom: 16px;">
          <wa-radio 
            name="delivery" 
            value="browser"
            ?checked=${this.outputOptions.delivery === 'browser'}
            @change=${() => this.selectDeliveryMethod('browser')}>
            Open in browser
          </wa-radio>
          
          <wa-radio 
            name="delivery" 
            value="email"
            ?checked=${this.outputOptions.delivery === 'email'}
            @change=${() => this.selectDeliveryMethod('email')}>
            Send to my email
          </wa-radio>
        </div>
        
        ${this.recentExecutions.length > 0 ? html`
          <div class="section-title">Recent Executions</div>
          
          <table class="executions-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Status</th>
                <th>Rows</th>
                <th>Duration</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${this.recentExecutions.map(execution => html`
                <tr>
                  <td>${this.formatDate(execution.started_at)}</td>
                  <td>
                    <span class="status-chip ${this.getStatusClass(execution.status)}">
                      ${execution.status}
                    </span>
                  </td>
                  <td>${execution.row_count !== undefined ? execution.row_count.toLocaleString() : 'N/A'}</td>
                  <td>${execution.execution_time_ms ? `${(execution.execution_time_ms / 1000).toFixed(2)}s` : 'N/A'}</td>
                  <td>
                    <wa-button variant="text" @click=${() => this.navigateToExecution(execution.id)}>
                      View
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
            </tbody>
          </table>
        ` : ''}
        
        <div class="button-row">
          <wa-button variant="outlined" @click=${this.cancel}>Cancel</wa-button>
          <wa-button @click=${this.executeReport} ?disabled=${!this.formValid}>
            Execute Report
          </wa-button>
        </div>
        
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
  renderParameterInput(param) {
    const value = this.parameters[param.name] !== undefined ? this.parameters[param.name] : '';
    const displayName = param.display_name || param.name;
    
    switch (param.parameter_type) {
      case 'string':
        return html`
          <wa-input 
            label="${displayName}"
            .value=${value}
            @input=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}
            placeholder=${param.placeholder || ''}>
          </wa-input>
        `;
        
      case 'textarea':
        return html`
          <wa-input 
            label="${displayName}"
            .value=${value}
            @input=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}
            placeholder=${param.placeholder || ''}
            multiline
            rows="4">
          </wa-input>
        `;
        
      case 'number':
        return html`
          <wa-input 
            label="${displayName}"
            type="number"
            .value=${value}
            @input=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}
            placeholder=${param.placeholder || ''}>
          </wa-input>
        `;
        
      case 'date':
        return html`
          <wa-date-picker 
            label="${displayName}"
            .value=${value}
            @change=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}>
          </wa-date-picker>
        `;
        
      case 'daterange':
        // Split value into start and end dates
        const dates = Array.isArray(value) ? value : (value ? value.split(',') : ['', '']);
        return html`
          <div>
            <label>${displayName}</label>
            <div style="display: flex; gap: 8px; align-items: center;">
              <wa-date-picker 
                label="Start"
                .value=${dates[0] || ''}
                @change=${e => this.handleParameterChange(param.name, [e.target.value, dates[1]].join(','))}
                ?required=${param.required}>
              </wa-date-picker>
              
              <span>to</span>
              
              <wa-date-picker 
                label="End"
                .value=${dates[1] || ''}
                @change=${e => this.handleParameterChange(param.name, [dates[0], e.target.value].join(','))}
                ?required=${param.required}>
              </wa-date-picker>
            </div>
          </div>
        `;
        
      case 'boolean':
        return html`
          <wa-checkbox
            label="${displayName}"
            ?checked=${value === true || value === 'true' || value === '1'}
            @change=${e => this.handleParameterChange(param.name, e.target.checked)}>
          </wa-checkbox>
        `;
        
      case 'enum':
        return html`
          <wa-select 
            label="${displayName}"
            .value=${value}
            @change=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}>
            <wa-option value="">Select...</wa-option>
            ${(param.enum_values || []).map(option => html`
              <wa-option value="${option.value}">${option.label || option.value}</wa-option>
            `)}
          </wa-select>
        `;
        
      default:
        return html`
          <wa-input 
            label="${displayName}"
            .value=${value}
            @input=${e => this.handleParameterChange(param.name, e.target.value)}
            ?required=${param.required}
            placeholder=${param.placeholder || ''}>
          </wa-input>
        `;
    }
  }
}
customElements.define('wa-report-parameter-form', WebAwesomeReportParameterForm);