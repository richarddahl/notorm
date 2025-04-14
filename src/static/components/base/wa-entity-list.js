import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-entity-list
 * @description Generic entity list component with filtering, sorting, and pagination
 * @fires entity-selected - When an entity is selected
 * @fires entity-created - When an entity is created
 * @fires entity-updated - When an entity is updated
 * @fires entity-deleted - When an entity is deleted
 */
export class WebAwesomeEntityList extends LitElement {
  static get properties() {
    return {
      // Data configuration
      baseUrl: { type: String },
      entityType: { type: String },
      title: { type: String },
      description: { type: String },
      
      // Customization
      icon: { type: String },
      columns: { type: Array },
      filterFields: { type: Array },
      sortFields: { type: Array },
      
      // State
      entities: { type: Array },
      totalCount: { type: Number },
      loading: { type: Boolean },
      error: { type: String },
      filter: { type: Object },
      sort: { type: Object },
      pagination: { type: Object },
      selectedEntity: { type: Object },
      
      // UI state
      showCreateDialog: { type: Boolean },
      showEditDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      activeTab: { type: String },
      
      // Capabilities
      enableCreate: { type: Boolean },
      enableEdit: { type: Boolean },
      enableDelete: { type: Boolean },
      enableExport: { type: Boolean },
      enableBulkActions: { type: Boolean },
      
      // Translations/Labels
      labels: { type: Object },
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --entity-list-bg: var(--wa-background-color, #f5f5f5);
        --entity-list-padding: 20px;
        --section-gap: 24px;
      }
      .container {
        padding: var(--entity-list-padding);
        background-color: var(--entity-list-bg);
        min-height: 600px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
      }
      .title {
        font-size: 24px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .description {
        color: var(--wa-text-secondary-color, #757575);
        margin-top: 8px;
      }
      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
      }
      .search-bar {
        display: flex;
        gap: 16px;
        margin-bottom: var(--section-gap);
      }
      .table-container {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-sm);
        overflow: hidden;
        margin-bottom: var(--section-gap);
      }
      .table {
        width: 100%;
        border-collapse: collapse;
      }
      .table th {
        text-align: left;
        padding: 16px;
        font-weight: 500;
        color: var(--wa-text-primary-color, #212121);
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
        white-space: nowrap;
      }
      .table td {
        padding: 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .table tr:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
      }
      .pagination-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .empty-state {
        text-align: center;
        padding: 40px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        margin-bottom: var(--section-gap);
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .sortable {
        cursor: pointer;
        user-select: none;
      }
      .sortable:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .sortable::after {
        content: '⇅';
        opacity: 0.5;
        margin-left: 8px;
      }
      .sortable.asc::after {
        content: '↑';
        opacity: 1;
      }
      .sortable.desc::after {
        content: '↓';
        opacity: 1;
      }
      .bulk-select {
        width: 20px;
      }
      .status-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 8px;
        font-size: 12px;
        border-radius: 12px;
        font-weight: 500;
      }
      .status-badge.active {
        background-color: var(--wa-success-color-light, rgba(76, 175, 80, 0.1));
        color: var(--wa-success-color, #4caf50);
      }
      .status-badge.inactive {
        background-color: var(--wa-error-color-light, rgba(244, 67, 54, 0.1));
        color: var(--wa-error-color, #f44336);
      }
      .dialog-content {
        margin-bottom: 24px;
      }
      .field-row {
        margin-bottom: 16px;
      }
      .field-label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
      }
      .field-description {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
        margin-top: 4px;
      }
    `;
  }
  constructor() {
    super();
    this.baseUrl = '/api';
    this.entityType = '';
    this.title = 'Entity List';
    this.description = 'Manage entities';
    this.icon = 'list';
    
    this.columns = [];
    this.filterFields = [];
    this.sortFields = [];
    
    this.entities = [];
    this.totalCount = 0;
    this.loading = false;
    this.error = null;
    this.filter = {};
    this.sort = { field: 'id', direction: 'asc' };
    this.pagination = { page: 1, pageSize: 20 };
    this.selectedEntity = null;
    this.showCreateDialog = false;
    this.showEditDialog = false;
    this.showDeleteDialog = false;
    this.activeTab = 'list';
    
    this.enableCreate = true;
    this.enableEdit = true;
    this.enableDelete = true;
    this.enableExport = true;
    this.enableBulkActions = false;
    
    this.labels = {
      create: 'Create',
      edit: 'Edit',
      delete: 'Delete',
      export: 'Export',
      search: 'Search',
      filter: 'Filter',
      clear: 'Clear',
      cancel: 'Cancel',
      save: 'Save',
      confirm: 'Confirm',
      noResults: 'No entities found',
      createPrompt: 'Create your first entity',
      deleteConfirm: 'Are you sure you want to delete this entity?',
      showing: 'Showing',
      of: 'of',
      entries: 'entries'
    };
    
    this.selectedItems = new Set();
  }
  connectedCallback() {
    super.connectedCallback();
    // Load entities when component is connected to DOM
    this.fetchEntities();
  }
  
  /**
   * Fetch entities from the server
   */
  async fetchEntities() {
    this.loading = true;
    this.error = null;
    
    try {
      const url = new URL(`${this.baseUrl}/${this.entityType}`);
      
      // Add filter parameters
      if (this.filter) {
        Object.entries(this.filter).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            url.searchParams.append(`filter[${key}]`, value);
          }
        });
      }
      
      // Add sorting
      if (this.sort) {
        url.searchParams.append('sort', `${this.sort.direction === 'desc' ? '-' : ''}${this.sort.field}`);
      }
      
      // Add pagination
      if (this.pagination) {
        url.searchParams.append('page[number]', this.pagination.page.toString());
        url.searchParams.append('page[size]', this.pagination.pageSize.toString());
      }
      
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      this.entities = result.data || [];
      this.totalCount = result.meta?.total || this.entities.length;
    } catch (error) {
      console.error('Error fetching entities:', error);
      this.error = error.message;
      this._showNotification(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Handle search input changes
   * @param {Event} e - Input event
   */
  handleSearchInput(e) {
    const searchTerm = e.target.value;
    if (!searchTerm) {
      delete this.filter.search;
    } else {
      this.filter = { ...this.filter, search: searchTerm };
    }
    
    // Debounce search to avoid too many requests
    clearTimeout(this._searchTimeout);
    this._searchTimeout = setTimeout(() => {
      this.pagination.page = 1; // Reset to first page on search
      this.fetchEntities();
    }, 300);
  }
  
  /**
   * Handle filter changes
   * @param {Event} e - Change event
   */
  handleFilterChange(e) {
    const field = e.target.name;
    const value = e.target.value;
    
    if (!value) {
      const newFilter = { ...this.filter };
      delete newFilter[field];
      this.filter = newFilter;
    } else {
      this.filter = { ...this.filter, [field]: value };
    }
    
    this.pagination.page = 1; // Reset to first page on filter change
    this.fetchEntities();
  }
  
  /**
   * Clear all filters
   */
  clearFilters() {
    this.filter = {};
    this.pagination.page = 1;
    this.fetchEntities();
  }
  
  /**
   * Handle sort header click
   * @param {string} field - Field to sort by
   */
  handleSort(field) {
    if (this.sort.field === field) {
      // Toggle direction if already sorting by this field
      this.sort = {
        field,
        direction: this.sort.direction === 'asc' ? 'desc' : 'asc'
      };
    } else {
      // Default to ascending for new sort field
      this.sort = { field, direction: 'asc' };
    }
    
    this.fetchEntities();
  }
  
  /**
   * Handle page change
   * @param {Event} e - Page change event
   */
  handlePageChange(e) {
    this.pagination = {
      ...this.pagination,
      page: e.detail.page
    };
    
    this.fetchEntities();
  }
  
  /**
   * Handle page size change
   * @param {Event} e - Page size change event
   */
  handlePageSizeChange(e) {
    this.pagination = {
      ...this.pagination,
      pageSize: parseInt(e.target.value, 10),
      page: 1 // Reset to first page when changing page size
    };
    
    this.fetchEntities();
  }
  
  /**
   * Open create dialog
   */
  openCreateDialog() {
    this.selectedEntity = null;
    this.showCreateDialog = true;
  }
  
  /**
   * Open edit dialog for selected entity
   * @param {Object} entity - Entity to edit
   */
  openEditDialog(entity) {
    this.selectedEntity = { ...entity };
    this.showEditDialog = true;
  }
  
  /**
   * Open delete confirmation dialog
   * @param {Object} entity - Entity to delete
   */
  openDeleteDialog(entity) {
    this.selectedEntity = entity;
    this.showDeleteDialog = true;
  }
  
  /**
   * Close all dialogs
   */
  closeDialogs() {
    this.showCreateDialog = false;
    this.showEditDialog = false;
    this.showDeleteDialog = false;
  }
  
  /**
   * Handle form field changes in dialogs
   * @param {Event} e - Input/change event
   */
  handleFieldChange(e) {
    const field = e.target.name;
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    this.selectedEntity = {
      ...this.selectedEntity,
      [field]: value
    };
  }
  
  /**
   * Create new entity
   */
  async createEntity() {
    this.loading = true;
    
    try {
      const response = await fetch(`${this.baseUrl}/${this.entityType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.selectedEntity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      this._showNotification('Entity created successfully', 'success');
      this.dispatchEvent(new CustomEvent('entity-created', {
        detail: { entity: result.data || result }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error creating entity:', error);
      this._showNotification(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Update existing entity
   */
  async updateEntity() {
    if (!this.selectedEntity || !this.selectedEntity.id) {
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch(`${this.baseUrl}/${this.entityType}/${this.selectedEntity.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.selectedEntity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      this._showNotification('Entity updated successfully', 'success');
      this.dispatchEvent(new CustomEvent('entity-updated', {
        detail: { entity: result.data || result }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error updating entity:', error);
      this._showNotification(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Delete entity
   */
  async deleteEntity() {
    if (!this.selectedEntity || !this.selectedEntity.id) {
      return;
    }
    
    this.loading = true;
    
    try {
      const response = await fetch(`${this.baseUrl}/${this.entityType}/${this.selectedEntity.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      this._showNotification('Entity deleted successfully', 'success');
      this.dispatchEvent(new CustomEvent('entity-deleted', {
        detail: { entityId: this.selectedEntity.id }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error deleting entity:', error);
      this._showNotification(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Export entities to CSV
   */
  async exportEntities() {
    this.loading = true;
    
    try {
      // Get all entities (without pagination)
      const url = new URL(`${this.baseUrl}/${this.entityType}`);
      
      // Add filter parameters
      if (this.filter) {
        Object.entries(this.filter).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            url.searchParams.append(`filter[${key}]`, value);
          }
        });
      }
      
      // Add sorting
      if (this.sort) {
        url.searchParams.append('sort', `${this.sort.direction === 'desc' ? '-' : ''}${this.sort.field}`);
      }
      
      // Request all entities (may be limited by server)
      url.searchParams.append('page[size]', '1000');
      
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      const entities = result.data || [];
      
      if (entities.length === 0) {
        this._showNotification('No data to export', 'warning');
        return;
      }
      
      // Generate CSV
      const headers = this.columns.map(col => col.label || col.field);
      const rows = entities.map(entity => 
        this.columns.map(col => {
          const value = this._getValueByPath(entity, col.field);
          return typeof value === 'object' ? JSON.stringify(value) : value;
        })
      );
      
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');
      
      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url2 = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url2;
      link.setAttribute('download', `${this.entityType}_export_${new Date().toISOString().split('T')[0]}.csv`);
      link.click();
      
      this._showNotification('Export complete', 'success');
    } catch (error) {
      console.error('Error exporting entities:', error);
      this._showNotification(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Show notification
   * @param {string} message - Notification message
   * @param {string} type - Notification type (success, error, warning, info)
   * @private
   */
  _showNotification(message, type = 'info') {
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
  
  /**
   * Get value from object by dot-notation path
   * @param {Object} obj - Source object
   * @param {string} path - Dot-notation path
   * @returns {*} Value at path
   * @private
   */
  _getValueByPath(obj, path) {
    if (!obj || !path) {
      return '';
    }
    
    const parts = path.split('.');
    let result = obj;
    
    for (const part of parts) {
      if (result == null) {
        return '';
      }
      result = result[part];
    }
    
    return result === undefined || result === null ? '' : result;
  }
  
  /**
   * Format cell value based on column configuration
   * @param {Object} entity - Entity object
   * @param {Object} column - Column configuration
   * @returns {string|Object} Formatted value
   * @private
   */
  _formatCellValue(entity, column) {
    const value = this._getValueByPath(entity, column.field);
    
    if (column.format) {
      return column.format(value, entity);
    }
    
    if (column.type === 'date') {
      return new Date(value).toLocaleDateString();
    }
    
    if (column.type === 'datetime') {
      return new Date(value).toLocaleString();
    }
    
    if (column.type === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    
    if (column.type === 'status') {
      return html`
        <span class="status-badge ${value ? 'active' : 'inactive'}">
          ${value ? 'Active' : 'Inactive'}
        </span>
      `;
    }
    
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    
    return value;
  }
  
  /**
   * Render create/edit form fields
   * @returns {import('lit').TemplateResult}
   * @private
   */
  _renderFormFields() {
    return html`
      ${this.columns.map(column => {
        if (column.readOnly || column.field === 'id') {
          return '';
        }
        
        return html`
          <div class="field-row">
            <label class="field-label" for="${column.field}">${column.label || column.field}</label>
            ${this._renderFormField(column)}
            ${column.description ? html`
              <div class="field-description">${column.description}</div>
            ` : ''}
          </div>
        `;
      })}
    `;
  }
  
  /**
   * Render specific form field based on column type
   * @param {Object} column - Column configuration
   * @returns {import('lit').TemplateResult}
   * @private
   */
  _renderFormField(column) {
    const value = this.selectedEntity ? this._getValueByPath(this.selectedEntity, column.field) : '';
    
    if (column.type === 'boolean') {
      return html`
        <wa-switch
          name="${column.field}"
          ?checked=${value}
          @change=${this.handleFieldChange}>
        </wa-switch>
      `;
    }
    
    if (column.type === 'select') {
      return html`
        <wa-select
          name="${column.field}"
          .value=${value}
          @change=${this.handleFieldChange}>
          ${column.options.map(option => html`
            <wa-option value="${option.value}">${option.label}</wa-option>
          `)}
        </wa-select>
      `;
    }
    
    if (column.type === 'textarea') {
      return html`
        <wa-textarea
          name="${column.field}"
          .value=${value}
          @input=${this.handleFieldChange}>
        </wa-textarea>
      `;
    }
    
    if (column.type === 'date') {
      return html`
        <wa-input
          type="date"
          name="${column.field}"
          .value=${value}
          @input=${this.handleFieldChange}>
        </wa-input>
      `;
    }
    
    // Default to text input
    return html`
      <wa-input
        type="${column.type === 'number' ? 'number' : 'text'}"
        name="${column.field}"
        .value=${value}
        @input=${this.handleFieldChange}>
      </wa-input>
    `;
  }
  
  /**
   * Render create dialog
   * @returns {import('lit').TemplateResult}
   * @private
   */
  _renderCreateDialog() {
    if (!this.showCreateDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">Create ${this.entityType}</div>
        
        <div class="dialog-content">
          ${this._renderFormFields()}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.cancel}
          </wa-button>
          <wa-button color="primary" @click=${this.createEntity} ?loading=${this.loading}>
            ${this.labels.save}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  /**
   * Render edit dialog
   * @returns {import('lit').TemplateResult}
   * @private
   */
  _renderEditDialog() {
    if (!this.showEditDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">Edit ${this.entityType}</div>
        
        <div class="dialog-content">
          ${this._renderFormFields()}
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.cancel}
          </wa-button>
          <wa-button color="primary" @click=${this.updateEntity} ?loading=${this.loading}>
            ${this.labels.save}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  /**
   * Render delete confirmation dialog
   * @returns {import('lit').TemplateResult}
   * @private
   */
  _renderDeleteDialog() {
    if (!this.showDeleteDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">Delete ${this.entityType}</div>
        
        <div class="dialog-content">
          <p>${this.labels.deleteConfirm}</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.cancel}
          </wa-button>
          <wa-button color="error" @click=${this.deleteEntity} ?loading=${this.loading}>
            ${this.labels.delete}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  render() {
    return html`
      <div class="container">
        <div class="header">
          <div>
            <h1 class="title">${this.title}</h1>
            <p class="description">${this.description}</p>
          </div>
          
          ${this.enableCreate ? html`
            <wa-button @click=${this.openCreateDialog}>
              <wa-icon slot="prefix" name="add"></wa-icon>
              ${this.labels.create}
            </wa-button>
          ` : ''}
        </div>
        
        ${this.error ? html`
          <wa-alert type="error" style="margin-bottom: 20px;">
            ${this.error}
          </wa-alert>
        ` : ''}
        
        <div class="search-bar">
          <wa-input 
            placeholder="${this.labels.search}"
            .value=${this.filter.search || ''}
            @input=${this.handleSearchInput}
            style="flex: 2;">
            <wa-icon slot="prefix" name="search"></wa-icon>
          </wa-input>
          
          ${this.filterFields.length > 0 ? html`
            ${this.filterFields.map(field => html`
              <wa-select 
                name="${field.field}"
                placeholder="${field.label || field.field}"
                .value=${this.filter[field.field] || ''}
                @change=${this.handleFilterChange}
                style="flex: 1;">
                <wa-option value="">All ${field.label || field.field}s</wa-option>
                ${field.options.map(option => html`
                  <wa-option value="${option.value}">${option.label}</wa-option>
                `)}
              </wa-select>
            `)}
            
            <wa-button variant="outlined" @click=${this.clearFilters}>
              ${this.labels.clear}
            </wa-button>
          ` : ''}
          
          ${this.enableExport ? html`
            <wa-button variant="outlined" @click=${this.exportEntities}>
              <wa-icon slot="prefix" name="download"></wa-icon>
              ${this.labels.export}
            </wa-button>
          ` : ''}
        </div>
        
        ${this.entities.length === 0 ? html`
          <div class="empty-state">
            <wa-icon name="${this.icon}" class="empty-state-icon"></wa-icon>
            <h2>${this.labels.noResults}</h2>
            <p>There are no entities matching your search criteria.</p>
            ${this.enableCreate ? html`
              <wa-button @click=${this.openCreateDialog}>
                ${this.labels.createPrompt}
              </wa-button>
            ` : ''}
          </div>
        ` : html`
          <div class="table-container">
            <table class="table">
              <thead>
                <tr>
                  ${this.enableBulkActions ? html`
                    <th class="bulk-select">
                      <wa-checkbox
                        @change=${this._handleSelectAll}
                        ?checked=${this.selectedItems.size === this.entities.length && this.entities.length > 0}
                        ?indeterminate=${this.selectedItems.size > 0 && this.selectedItems.size < this.entities.length}>
                      </wa-checkbox>
                    </th>
                  ` : ''}
                  
                  ${this.columns.map(column => html`
                    <th 
                      class="${this.sortFields.includes(column.field) ? 'sortable' : ''} 
                             ${this.sort.field === column.field ? this.sort.direction : ''}"
                      @click=${this.sortFields.includes(column.field) ? () => this.handleSort(column.field) : null}>
                      ${column.label || column.field}
                    </th>
                  `)}
                  
                  ${(this.enableEdit || this.enableDelete) ? html`<th>Actions</th>` : ''}
                </tr>
              </thead>
              <tbody>
                ${repeat(this.entities, entity => entity.id || Math.random(), entity => html`
                  <tr>
                    ${this.enableBulkActions ? html`
                      <td>
                        <wa-checkbox
                          ?checked=${this.selectedItems.has(entity.id)}
                          @change=${e => this._handleSelectItem(e, entity.id)}>
                        </wa-checkbox>
                      </td>
                    ` : ''}
                    
                    ${this.columns.map(column => html`
                      <td>${this._formatCellValue(entity, column)}</td>
                    `)}
                    
                    ${(this.enableEdit || this.enableDelete) ? html`
                      <td class="actions">
                        ${this.enableEdit ? html`
                          <wa-button variant="text" color="primary" @click=${() => this.openEditDialog(entity)}>
                            <wa-icon name="edit"></wa-icon>
                          </wa-button>
                        ` : ''}
                        
                        ${this.enableDelete ? html`
                          <wa-button variant="text" color="error" @click=${() => this.openDeleteDialog(entity)}>
                            <wa-icon name="delete"></wa-icon>
                          </wa-button>
                        ` : ''}
                      </td>
                    ` : ''}
                  </tr>
                `)}
              </tbody>
            </table>
            
            <div class="pagination-container">
              <div>
                ${this.labels.showing} ${(this.pagination.page - 1) * this.pagination.pageSize + 1} - 
                ${Math.min(this.pagination.page * this.pagination.pageSize, this.totalCount)}
                ${this.labels.of} ${this.totalCount} ${this.labels.entries}
              </div>
              
              <wa-pagination
                current-page=${this.pagination.page}
                total-pages=${Math.ceil(this.totalCount / this.pagination.pageSize)}
                @page-change=${this.handlePageChange}>
              </wa-pagination>
              
              <wa-select
                .value=${this.pagination.pageSize.toString()}
                @change=${this.handlePageSizeChange}
                style="width: 80px;">
                <wa-option value="10">10</wa-option>
                <wa-option value="20">20</wa-option>
                <wa-option value="50">50</wa-option>
                <wa-option value="100">100</wa-option>
              </wa-select>
            </div>
          </div>
        `}
        
        ${this._renderCreateDialog()}
        ${this._renderEditDialog()}
        ${this._renderDeleteDialog()}
        
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
  
  /**
   * Handle select all checkbox
   * @param {Event} e - Change event
   * @private
   */
  _handleSelectAll(e) {
    if (e.target.checked) {
      this.selectedItems = new Set(this.entities.map(entity => entity.id));
    } else {
      this.selectedItems = new Set();
    }
    this.requestUpdate();
  }
  
  /**
   * Handle individual item selection
   * @param {Event} e - Change event
   * @param {string} id - Entity ID
   * @private
   */
  _handleSelectItem(e, id) {
    if (e.target.checked) {
      this.selectedItems.add(id);
    } else {
      this.selectedItems.delete(id);
    }
    this.requestUpdate();
  }
}
customElements.define('wa-entity-list', WebAwesomeEntityList);