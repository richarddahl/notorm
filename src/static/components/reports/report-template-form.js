/**
 * Report Template Form Component
 * 
 * Form for creating and editing report templates.
 */
class ReportTemplateForm extends LitElement {
  static properties = {
    templateId: { type: String },
    template: { type: Object },
    loading: { type: Boolean },
    saving: { type: Boolean },
    error: { type: String },
    mode: { type: String }, // 'create' or 'edit'
    availableObjectTypes: { type: Array }
  };
  constructor() {
    super();
    this.templateId = null;
    this.template = {
      name: '',
      description: '',
      base_object_type: '',
      format_config: {
        title_format: '{name} - Generated on {date}',
        show_footer: true
      },
      parameter_definitions: {},
      cache_policy: {
        ttl_seconds: 3600
      },
      version: '1.0.0'
    };
    this.loading = false;
    this.saving = false;
    this.error = null;
    this.mode = 'create';
    this.availableObjectTypes = ['customer', 'order', 'product', 'user'];
  }
  connectedCallback() {
    super.connectedCallback();
    // Check if we're in edit mode based on URL
    const url = new URL(window.location.href);
    const pathParts = url.pathname.split('/');
    if (pathParts.includes('edit')) {
      const idIndex = pathParts.indexOf('edit') - 1;
      if (idIndex > 0) {
        this.templateId = pathParts[idIndex];
        this.mode = 'edit';
        this.loadTemplate();
      }
    }
  }
  async loadTemplate() {
    if (!this.templateId) return;
    
    try {
      this.loading = true;
      const response = await fetch(`/api/reports/templates/${this.templateId}`);
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      this.template = await response.json();
      this.error = null;
    } catch (err) {
      this.error = err.message;
      console.error('Error loading template:', err);
    } finally {
      this.loading = false;
    }
  }
  async saveTemplate(event) {
    event.preventDefault();
    
    try {
      this.saving = true;
      
      const url = this.mode === 'edit' 
        ? `/api/reports/templates/${this.templateId}` 
        : '/api/reports/templates';
      
      const method = this.mode === 'edit' ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.template)
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const savedTemplate = await response.json();
      
      // Navigate to the template view page
      window.location.href = `/reports/templates/${savedTemplate.id}`;
    } catch (err) {
      this.error = err.message;
      console.error('Error saving template:', err);
    } finally {
      this.saving = false;
    }
  }
  handleInputChange(event) {
    const field = event.target.name;
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    
    // Handle nested properties
    if (field.includes('.')) {
      const [section, key] = field.split('.');
      this.template = {
        ...this.template,
        [section]: {
          ...this.template[section],
          [key]: value
        }
      };
    } else {
      this.template = {
        ...this.template,
        [field]: value
      };
    }
  }
  render() {
    if (this.loading) {
      return html`<div class="loading">Loading template...</div>`;
    }
    return html`
      <div class="report-template-form">
        <h2>${this.mode === 'edit' ? 'Edit' : 'Create'} Report Template</h2>
        
        ${this.error ? html`<div class="alert alert-danger">${this.error}</div>` : ''}
        
        <form @submit=${this.saveTemplate}>
          <div class="form-group">
            <label for="name">Template Name</label>
            <input 
              type="text" 
              id="name" 
              name="name" 
              .value=${this.template.name} 
              @input=${this.handleInputChange}
              required
              class="form-control"
            />
          </div>
          
          <div class="form-group">
            <label for="description">Description</label>
            <textarea 
              id="description" 
              name="description" 
              .value=${this.template.description} 
              @input=${this.handleInputChange}
              class="form-control"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label for="base_object_type">Base Object Type</label>
            <select 
              id="base_object_type" 
              name="base_object_type" 
              .value=${this.template.base_object_type} 
              @change=${this.handleInputChange}
              required
              class="form-control"
            >
              <option value="">Select an object type</option>
              ${this.availableObjectTypes.map(type => html`
                <option value=${type} ?selected=${this.template.base_object_type === type}>${type}</option>
              `)}
            </select>
          </div>
          
          <div class="form-group">
            <label for="format_config.title_format">Title Format</label>
            <input 
              type="text" 
              id="format_config.title_format" 
              name="format_config.title_format" 
              .value=${this.template.format_config.title_format} 
              @input=${this.handleInputChange}
              class="form-control"
            />
            <small class="form-text text-muted">Use {name} for template name and {date} for generation date</small>
          </div>
          
          <div class="form-check">
            <input 
              type="checkbox" 
              id="format_config.show_footer" 
              name="format_config.show_footer" 
              .checked=${this.template.format_config.show_footer} 
              @change=${this.handleInputChange}
              class="form-check-input"
            />
            <label class="form-check-label" for="format_config.show_footer">Show Footer</label>
          </div>
          
          <div class="form-group">
            <label for="version">Version</label>
            <input 
              type="text" 
              id="version" 
              name="version" 
              .value=${this.template.version} 
              @input=${this.handleInputChange}
              required
              class="form-control"
            />
          </div>
          
          <div class="form-group">
            <label for="cache_policy.ttl_seconds">Cache TTL (seconds)</label>
            <input 
              type="number" 
              id="cache_policy.ttl_seconds" 
              name="cache_policy.ttl_seconds" 
              .value=${this.template.cache_policy.ttl_seconds} 
              @input=${this.handleInputChange}
              class="form-control"
            />
          </div>
          
          <div class="form-actions">
            <button 
              type="submit" 
              class="btn btn-primary" 
              ?disabled=${this.saving}
            >
              ${this.saving ? 'Saving...' : 'Save Template'}
            </button>
            <a href="/reports/templates" class="btn btn-secondary">Cancel</a>
          </div>
        </form>
      </div>
    `;
  }
  static styles = css`
    .report-template-form {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
    }
    
    .loading {
      padding: 2rem;
      text-align: center;
    }
    
    .alert {
      padding: 0.75rem 1.25rem;
      margin-bottom: 1rem;
      border-radius: 0.25rem;
    }
    
    .alert-danger {
      color: #721c24;
      background-color: #f8d7da;
      border: 1px solid #f5c6cb;
    }
    
    .form-group {
      margin-bottom: 1rem;
    }
    
    .form-check {
      margin-bottom: 1rem;
    }
    
    label {
      display: block;
      margin-bottom: 0.5rem;
    }
    
    .form-control {
      display: block;
      width: 100%;
      padding: 0.375rem 0.75rem;
      border: 1px solid #ced4da;
      border-radius: 0.25rem;
    }
    
    textarea.form-control {
      min-height: 100px;
    }
    
    .form-text {
      display: block;
      margin-top: 0.25rem;
      font-size: 0.875rem;
    }
    
    .text-muted {
      color: #6c757d;
    }
    
    .form-actions {
      margin-top: 2rem;
      display: flex;
      gap: 1rem;
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
    
    .btn:disabled {
      opacity: 0.65;
      cursor: not-allowed;
    }
  `;
}
customElements.define('report-template-form', ReportTemplateForm);