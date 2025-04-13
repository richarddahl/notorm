/**
 * Report Template List Component
 * 
 * Displays a list of report templates with actions to view, edit, delete,
 * and execute templates.
 */
class ReportTemplateList extends LitElement {
  static properties = {
    templates: { type: Array },
    loading: { type: Boolean },
    error: { type: String }
  };

  constructor() {
    super();
    this.templates = [];
    this.loading = true;
    this.error = null;
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadTemplates();
  }

  async loadTemplates() {
    try {
      this.loading = true;
      const response = await fetch('/api/reports/templates');
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.templates = data;
      this.error = null;
    } catch (err) {
      this.error = err.message;
      console.error('Error loading templates:', err);
    } finally {
      this.loading = false;
    }
  }

  async executeReport(templateId) {
    try {
      const response = await fetch(`/api/reports/templates/${templateId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          trigger_type: 'manual',
          parameters: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      // Navigate to execution status page
      window.location.href = `/reports/executions/${result.id}`;
    } catch (err) {
      console.error('Error executing report:', err);
      alert(`Failed to execute report: ${err.message}`);
    }
  }

  async deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template?')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/reports/templates/${templateId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      // Reload templates after deletion
      this.loadTemplates();
    } catch (err) {
      console.error('Error deleting template:', err);
      alert(`Failed to delete template: ${err.message}`);
    }
  }

  render() {
    if (this.loading) {
      return html`<div class="loading">Loading templates...</div>`;
    }

    if (this.error) {
      return html`
        <div class="error">
          <p>Error loading templates: ${this.error}</p>
          <button @click=${this.loadTemplates}>Try Again</button>
        </div>
      `;
    }

    if (this.templates.length === 0) {
      return html`
        <div class="empty">
          <p>No report templates found.</p>
          <a href="/reports/templates/new" class="btn btn-primary">Create New Template</a>
        </div>
      `;
    }

    return html`
      <div class="report-templates">
        <div class="header">
          <h2>Report Templates</h2>
          <a href="/reports/templates/new" class="btn btn-primary">Create New Template</a>
        </div>
        
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Base Object</th>
              <th>Last Updated</th>
              <th>Version</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${this.templates.map(template => html`
              <tr>
                <td>${template.name}</td>
                <td>${template.base_object_type}</td>
                <td>${new Date(template.updated_at).toLocaleString()}</td>
                <td>${template.version}</td>
                <td class="actions">
                  <a href="/reports/templates/${template.id}" class="btn btn-sm btn-info">View</a>
                  <a href="/reports/templates/${template.id}/edit" class="btn btn-sm btn-secondary">Edit</a>
                  <button @click=${() => this.executeReport(template.id)} class="btn btn-sm btn-success">Execute</button>
                  <button @click=${() => this.deleteTemplate(template.id)} class="btn btn-sm btn-danger">Delete</button>
                </td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  static styles = css`
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    .loading, .error, .empty {
      padding: 2rem;
      text-align: center;
    }
    
    .error {
      color: red;
    }
    
    .table {
      width: 100%;
      border-collapse: collapse;
    }
    
    .table th, .table td {
      padding: 0.75rem;
      border-bottom: 1px solid #dee2e6;
    }
    
    .actions {
      display: flex;
      gap: 0.5rem;
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
    
    .btn-info {
      background-color: #17a2b8;
      color: white;
    }
    
    .btn-secondary {
      background-color: #6c757d;
      color: white;
    }
    
    .btn-success {
      background-color: #28a745;
      color: white;
    }
    
    .btn-danger {
      background-color: #dc3545;
      color: white;
    }
    
    .btn-sm {
      padding: 0.25rem 0.5rem;
      font-size: 0.875rem;
    }
  `;
}

customElements.define('report-template-list', ReportTemplateList);