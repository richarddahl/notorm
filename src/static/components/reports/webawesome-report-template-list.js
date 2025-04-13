import { LitElement, html, css } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-tooltip.js';

/**
 * @element wa-report-template-list
 * @description Component for listing and managing report templates using WebAwesome
 * @property {Array} templates - Array of report templates
 * @property {String} searchTerm - Search term to filter templates
 * @property {String} entityFilter - Filter templates by entity type
 * @property {Boolean} loading - Loading state
 * @property {String} error - Error message if loading failed
 */
export class WebAwesomeReportTemplateList extends LitElement {
  static get properties() {
    return {
      templates: { type: Array },
      categories: { type: Array },
      searchTerm: { type: String },
      entityFilter: { type: String },
      categoryFilter: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      view: { type: String },
      showDeleteDialog: { type: Boolean },
      templateToDelete: { type: Object },
      sortField: { type: String },
      sortDirection: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --list-bg: var(--wa-background-color, #f5f5f5);
        --list-padding: 20px;
      }
      .list-container {
        padding: var(--list-padding);
        background-color: var(--list-bg);
        min-height: 600px;
      }
      .list-header {
        margin-bottom: 24px;
      }
      .list-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .list-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .search-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
      }
      .filter-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
      }
      .view-toggle {
        display: flex;
        align-items: center;
        margin-left: auto;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
      }
      .template-card {
        border-radius: var(--wa-border-radius, 4px);
        height: 100%;
      }
      .template-card-content {
        padding: 16px;
        flex: 1;
        display: flex;
        flex-direction: column;
      }
      .template-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .template-description {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0 0 16px 0;
        flex: 1;
      }
      .template-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .template-actions {
        display: flex;
        gap: 8px;
        margin-top: 16px;
        justify-content: flex-end;
      }
      .template-chip {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.12));
        color: var(--wa-primary-color, #3f51b5);
        border-radius: 16px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
      }
      .list-view-item {
        display: flex;
        padding: 16px;
        margin-bottom: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .list-view-content {
        flex: 1;
      }
      .list-view-actions {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 300px;
        padding: 32px;
        text-align: center;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-disabled-color, #bdbdbd);
      }
      .empty-message {
        margin-bottom: 16px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .sort-button {
        display: flex;
        align-items: center;
        cursor: pointer;
      }
      .sort-icon {
        margin-left: 4px;
        opacity: 0.6;
      }
    `;
  }

  constructor() {
    super();
    this.templates = [];
    this.categories = [];
    this.searchTerm = '';
    this.entityFilter = '';
    this.categoryFilter = '';
    this.loading = true;
    this.error = null;
    this.view = 'grid';
    this.showDeleteDialog = false;
    this.templateToDelete = null;
    this.sortField = 'updated_at';
    this.sortDirection = 'desc';
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadTemplates();
    
    // Default sorting
    this.sortField = 'updated_at';
    this.sortDirection = 'desc';
    
    // Load user preferences for view type
    const savedView = localStorage.getItem('report-template-view');
    if (savedView) {
      this.view = savedView;
    }
  }

  async loadTemplates() {
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch('/api/reports/templates');
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      this.templates = await response.json();
      
      // Extract unique categories
      const categorySet = new Set();
      this.templates.forEach(template => {
        if (template.category) {
          categorySet.add(template.category);
        }
      });
      
      this.categories = Array.from(categorySet).sort();
      
    } catch (err) {
      console.error('Failed to load templates:', err);
      this.error = `Error loading templates: ${err.message}`;
    } finally {
      this.loading = false;
    }
  }

  handleSearch(e) {
    this.searchTerm = e.target.value.toLowerCase();
  }

  handleEntityFilterChange(e) {
    this.entityFilter = e.target.value;
  }

  handleCategoryFilterChange(e) {
    this.categoryFilter = e.target.value;
  }

  changeView(viewType) {
    this.view = viewType;
    localStorage.setItem('report-template-view', viewType);
  }

  handleSort(field) {
    if (field === this.sortField) {
      // Toggle direction
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortField = field;
      this.sortDirection = 'desc';
    }
  }

  sortTemplates(templates) {
    // Make a copy to avoid mutating original array
    const sorted = [...templates];
    
    return sorted.sort((a, b) => {
      let valueA, valueB;
      
      switch (this.sortField) {
        case 'name':
          valueA = a.name || '';
          valueB = b.name || '';
          break;
        case 'entity_type':
          valueA = a.entity_type || '';
          valueB = b.entity_type || '';
          break;
        case 'created_at':
          valueA = new Date(a.created_at || 0).getTime();
          valueB = new Date(b.created_at || 0).getTime();
          break;
        case 'updated_at':
        default:
          valueA = new Date(a.updated_at || 0).getTime();
          valueB = new Date(b.updated_at || 0).getTime();
      }
      
      // For strings, use localeCompare
      if (typeof valueA === 'string') {
        return this.sortDirection === 'asc' ? 
          valueA.localeCompare(valueB) : 
          valueB.localeCompare(valueA);
      }
      
      // For numbers and dates (as numbers)
      return this.sortDirection === 'asc' ? 
        valueA - valueB : 
        valueB - valueA;
    });
  }

  confirmDelete(template) {
    this.templateToDelete = template;
    this.showDeleteDialog = true;
  }

  cancelDelete() {
    this.showDeleteDialog = false;
    this.templateToDelete = null;
  }

  async deleteTemplate() {
    if (!this.templateToDelete) return;
    
    this.loading = true;
    
    try {
      const response = await fetch(`/api/reports/templates/${this.templateToDelete.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      
      // Show success notification
      this._showNotification(`Template "${this.templateToDelete.name}" deleted successfully`, 'success');
      
      // Close dialog and reload templates
      this.showDeleteDialog = false;
      this.templateToDelete = null;
      this.loadTemplates();
      
    } catch (err) {
      console.error('Failed to delete template:', err);
      this._showNotification(`Error deleting template: ${err.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  navigateToTemplate(templateId) {
    window.location.href = `/reports/templates/${templateId}`;
  }

  navigateToEdit(templateId) {
    window.location.href = `/reports/templates/${templateId}/edit`;
  }

  navigateToExecutionManager(templateId) {
    window.location.href = `/reports/templates/${templateId}/executions`;
  }

  createNewTemplate() {
    window.location.href = '/reports/templates/new';
  }

  formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    
    // If today, show only time
    if (date.toDateString() === today.toDateString()) {
      return `Today at ${date.toLocaleTimeString()}`;
    }
    
    // If yesterday, show "Yesterday"
    if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday at ${date.toLocaleTimeString()}`;
    }
    
    // Otherwise show full date
    return date.toLocaleString();
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

  get filteredTemplates() {
    if (!this.templates || this.templates.length === 0) {
      return [];
    }
    
    let filtered = this.templates;
    
    // Apply search filter
    if (this.searchTerm) {
      filtered = filtered.filter(template => 
        template.name.toLowerCase().includes(this.searchTerm) || 
        (template.description && template.description.toLowerCase().includes(this.searchTerm))
      );
    }
    
    // Apply entity filter
    if (this.entityFilter) {
      filtered = filtered.filter(template => 
        template.entity_type === this.entityFilter
      );
    }
    
    // Apply category filter
    if (this.categoryFilter) {
      filtered = filtered.filter(template => 
        template.category === this.categoryFilter
      );
    }
    
    // Apply sorting
    return this.sortTemplates(filtered);
  }

  getUniqueEntityTypes() {
    if (!this.templates || this.templates.length === 0) {
      return [];
    }
    
    const entityTypes = new Set();
    this.templates.forEach(template => {
      if (template.entity_type) {
        entityTypes.add(template.entity_type);
      }
    });
    
    return Array.from(entityTypes).sort();
  }

  renderGridView() {
    return html`
      <div class="grid">
        ${this.filteredTemplates.map(template => html`
          <wa-card class="template-card" elevation="1">
            <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
              <div class="template-title">${template.name}</div>
              ${template.category ? html`
                <wa-chip size="small">${template.category}</wa-chip>
              ` : ''}
            </div>
            
            <div class="template-card-content">
              <div class="template-meta">
                <wa-icon name="category" size="small"></wa-icon>
                <span>${template.entity_type || 'No entity type'}</span>
              </div>
              
              <div class="template-meta">
                <wa-icon name="update" size="small"></wa-icon>
                <span>Updated ${this.formatDate(template.updated_at)}</span>
              </div>
              
              <div class="template-description">
                ${template.description || 'No description provided'}
              </div>
              
              <div class="template-meta">
                <wa-icon name="summarize" size="small"></wa-icon>
                <span>${template.fields?.length || 0} fields</span>
                
                ${template.triggers?.length ? html`
                  <span style="margin-left: auto; display: flex; align-items: center;">
                    <wa-icon name="schedule" size="small"></wa-icon>
                    <span>${template.triggers.length} schedule${template.triggers.length !== 1 ? 's' : ''}</span>
                  </span>
                ` : ''}
              </div>
              
              <div class="template-actions">
                <wa-button variant="text" @click=${() => this.navigateToTemplate(template.id)}>
                  View
                </wa-button>
                <wa-button variant="text" @click=${() => this.navigateToEdit(template.id)}>
                  Edit
                </wa-button>
                <wa-button variant="text" @click=${() => this.navigateToExecutionManager(template.id)}>
                  Execute
                </wa-button>
                <wa-button variant="text" color="error" @click=${() => this.confirmDelete(template)}>
                  Delete
                </wa-button>
              </div>
            </div>
          </wa-card>
        `)}
      </div>
    `;
  }

  renderListView() {
    return html`
      <div>
        <div style="margin-bottom: 16px; display: flex; align-items: center;">
          <div class="sort-button" @click=${() => this.handleSort('name')}>
            <span>Name</span>
            <wa-icon 
              name=${this.sortField === 'name' ? 
                (this.sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward') : 
                'unfold_more'} 
              size="small" 
              class="sort-icon">
            </wa-icon>
          </div>
          <div style="flex: 1;"></div>
          <div class="sort-button" @click=${() => this.handleSort('entity_type')}>
            <span>Entity Type</span>
            <wa-icon 
              name=${this.sortField === 'entity_type' ? 
                (this.sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward') : 
                'unfold_more'} 
              size="small" 
              class="sort-icon">
            </wa-icon>
          </div>
          <div style="flex: 1;"></div>
          <div class="sort-button" @click=${() => this.handleSort('updated_at')}>
            <span>Last Updated</span>
            <wa-icon 
              name=${this.sortField === 'updated_at' ? 
                (this.sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward') : 
                'unfold_more'} 
              size="small" 
              class="sort-icon">
            </wa-icon>
          </div>
          <div style="width: 200px;"></div>
        </div>
        
        <wa-divider></wa-divider>
        
        ${this.filteredTemplates.map(template => html`
          <div class="list-view-item">
            <div class="list-view-content">
              <div style="display: flex; align-items: center;">
                <div class="template-title">
                  ${template.name}
                </div>
                ${template.category ? html`
                  <wa-chip size="small" style="margin-left: 12px;">${template.category}</wa-chip>
                ` : ''}
              </div>
              <div class="template-description" style="margin-bottom: 8px;">
                ${template.description || 'No description provided'}
              </div>
              <div style="display: flex; align-items: center; gap: 16px;">
                <div class="template-meta">
                  <wa-icon name="summarize" size="small"></wa-icon>
                  <span>${template.fields?.length || 0} fields</span>
                </div>
                ${template.triggers?.length ? html`
                  <div class="template-meta">
                    <wa-icon name="schedule" size="small"></wa-icon>
                    <span>${template.triggers.length} schedule${template.triggers.length !== 1 ? 's' : ''}</span>
                  </div>
                ` : ''}
              </div>
            </div>
            <div style="flex: 0 0 120px; padding: 0 16px;">
              <div class="template-chip">
                ${template.entity_type || 'No entity'}
              </div>
            </div>
            <div style="flex: 0 0 180px; padding: 0 16px;">
              <div class="template-meta">
                ${this.formatDate(template.updated_at)}
              </div>
            </div>
            <div class="list-view-actions">
              <wa-button variant="text" @click=${() => this.navigateToTemplate(template.id)}>
                View
              </wa-button>
              <wa-button variant="text" @click=${() => this.navigateToExecutionManager(template.id)}>
                Execute
              </wa-button>
              <wa-button variant="icon" @click=${() => this.navigateToEdit(template.id)}>
                <wa-icon name="edit"></wa-icon>
              </wa-button>
              <wa-button variant="icon" color="error" @click=${() => this.confirmDelete(template)}>
                <wa-icon name="delete"></wa-icon>
              </wa-button>
            </div>
          </div>
        `)}
      </div>
    `;
  }

  renderDeleteDialog() {
    if (!this.showDeleteDialog || !this.templateToDelete) return html``;
    
    return html`
      <wa-dialog open @close=${this.cancelDelete}>
        <div slot="header">Delete Report Template</div>
        
        <div>
          <p>Are you sure you want to delete the report template "${this.templateToDelete.name}"?</p>
          <p>This action cannot be undone. All schedules and configurations for this report will be permanently removed.</p>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.cancelDelete}>Cancel</wa-button>
          <wa-button color="error" @click=${this.deleteTemplate}>Delete</wa-button>
        </div>
      </wa-dialog>
    `;
  }

  render() {
    return html`
      <div class="list-container">
        <div class="list-header">
          <h1 class="list-title">Report Templates</h1>
          <p class="list-subtitle">Browse, create and manage report templates</p>
        </div>
        
        <div class="search-bar">
          <wa-input 
            placeholder="Search templates..."
            .value=${this.searchTerm}
            @input=${this.handleSearch}
            style="flex: 1;">
            <wa-icon slot="prefix" name="search"></wa-icon>
          </wa-input>
          
          <wa-button @click=${this.createNewTemplate}>
            <wa-icon slot="prefix" name="add"></wa-icon>
            New Template
          </wa-button>
        </div>
        
        <div class="filter-bar">
          <wa-select 
            label="Entity Type"
            .value=${this.entityFilter}
            @change=${this.handleEntityFilterChange}>
            <wa-option value="">All Entity Types</wa-option>
            ${this.getUniqueEntityTypes().map(entityType => html`
              <wa-option value="${entityType}">${entityType}</wa-option>
            `)}
          </wa-select>
          
          ${this.categories.length > 0 ? html`
            <wa-select 
              label="Category"
              .value=${this.categoryFilter}
              @change=${this.handleCategoryFilterChange}>
              <wa-option value="">All Categories</wa-option>
              ${this.categories.map(category => html`
                <wa-option value="${category}">${category}</wa-option>
              `)}
            </wa-select>
          ` : ''}
          
          <div class="view-toggle">
            <wa-button 
              variant=${this.view === 'grid' ? 'filled' : 'outlined'}
              @click=${() => this.changeView('grid')}>
              <wa-icon name="grid_view"></wa-icon>
            </wa-button>
            <wa-button 
              variant=${this.view === 'list' ? 'filled' : 'outlined'}
              @click=${() => this.changeView('list')}>
              <wa-icon name="view_list"></wa-icon>
            </wa-button>
          </div>
        </div>
        
        ${this.error ? html`
          <wa-alert type="error">
            ${this.error}
            <wa-button slot="action" variant="text" @click=${this.loadTemplates}>Retry</wa-button>
          </wa-alert>
        ` : ''}
        
        ${this.loading ? html`
          <div style="display: flex; justify-content: center; padding: 48px;">
            <wa-spinner size="large"></wa-spinner>
          </div>
        ` : this.filteredTemplates.length === 0 ? html`
          <div class="empty-state">
            <wa-icon name="description" size="xlarge" class="empty-state-icon"></wa-icon>
            <h3>No templates found</h3>
            <p class="empty-message">
              ${this.searchTerm || this.entityFilter || this.categoryFilter ? 
                'No templates match your search criteria.' : 
                'There are no report templates available.'}
            </p>
            <wa-button @click=${this.createNewTemplate}>Create New Template</wa-button>
          </div>
        ` : this.view === 'grid' ? this.renderGridView() : this.renderListView()}
        
        ${this.renderDeleteDialog()}
      </div>
    `;
  }
}

customElements.define('wa-report-template-list', WebAwesomeReportTemplateList);