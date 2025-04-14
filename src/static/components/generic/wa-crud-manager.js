import { LitElement, html, css } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-pagination.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-textarea.js';
import '@webcomponents/awesome/wa-checkbox.js';

/**
 * @element wa-crud-manager
 * @description Highly configurable component for managing entities with CRUD operations
 * @fires entity-selected - When an entity is selected
 * @fires entity-created - When an entity is created
 * @fires entity-updated - When an entity is updated
 * @fires entity-deleted - When an entity is deleted
 * @fires filter-changed - When filter criteria changes
 * @fires sort-changed - When sort criteria changes
 * @fires page-changed - When pagination changes
 */
export class WebAwesomeCrudManager extends LitElement {
  static get properties() {
    return {
      // Data configuration
      baseUrl: { type: String },
      entityType: { type: String },
      title: { type: String },
      description: { type: String },
      
      // Schema configuration
      schema: { type: Object },
      
      // Customization
      icon: { type: String },
      customActions: { type: Array },
      layoutType: { type: String }, // 'table', 'grid', 'cards'
      detailTemplate: { type: Function },
      summaryTemplate: { type: Function },
      formTemplate: { type: Function },
      
      // State
      entities: { type: Array },
      totalCount: { type: Number },
      loading: { type: Boolean },
      error: { type: String },
      filter: { type: Object },
      sort: { type: Object },
      pagination: { type: Object },
      selectedEntity: { type: Object },
      selectedItems: { type: Array },
      
      // UI state
      showCreateDialog: { type: Boolean },
      showEditDialog: { type: Boolean },
      showDetailDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      showBulkDeleteDialog: { type: Boolean },
      showFilterPanel: { type: Boolean },
      activeTab: { type: String },
      
      // Capabilities
      enableCreate: { type: Boolean },
      enableEdit: { type: Boolean },
      enableDelete: { type: Boolean },
      enableExport: { type: Boolean },
      enableBulkActions: { type: Boolean },
      enableFiltering: { type: Boolean },
      enableSorting: { type: Boolean },
      enablePagination: { type: Boolean },
      enableDetail: { type: Boolean },
      
      // API configuration
      apiOptions: { type: Object },
      
      // Translations/Labels
      labels: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --crud-bg: var(--wa-background-color, #f5f5f5);
        --crud-padding: 20px;
        --section-gap: 24px;
        --primary-color: var(--wa-primary-color, #1976d2);
        --error-color: var(--wa-error-color, #f44336);
        --success-color: var(--wa-success-color, #4caf50);
        --warning-color: var(--wa-warning-color, #ff9800);
        --info-color: var(--wa-info-color, #2196f3);
        --text-primary: var(--wa-text-primary-color, #212121);
        --text-secondary: var(--wa-text-secondary-color, #757575);
        --border-color: var(--wa-border-color, #e0e0e0);
        --surface-color: var(--wa-surface-color, #ffffff);
        --hover-color: var(--wa-hover-color, #f5f5f5);
        --border-radius: var(--wa-border-radius, 4px);
        --shadow-sm: var(--wa-shadow-sm, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06));
        --shadow-md: var(--wa-shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06));
      }
      
      .container {
        padding: var(--crud-padding);
        background-color: var(--crud-bg);
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
        color: var(--text-primary);
      }
      
      .description {
        color: var(--text-secondary);
        margin-top: 8px;
      }
      
      .actions-bar {
        display: flex;
        gap: 8px;
      }
      
      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--section-gap);
        flex-wrap: wrap;
        gap: 16px;
      }
      
      .search-filter-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: var(--section-gap);
        width: 100%;
      }
      
      .search-input {
        flex: 1;
        min-width: 250px;
      }
      
      .table-container {
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
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
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-color);
        white-space: nowrap;
      }
      
      .table td {
        padding: 16px;
        border-bottom: 1px solid var(--border-color);
      }
      
      .table tr:hover {
        background-color: var(--hover-color);
        cursor: pointer;
      }
      
      .actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        flex-wrap: nowrap;
        white-space: nowrap;
      }
      
      .pagination-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-top: 1px solid var(--border-color);
        flex-wrap: wrap;
        gap: 16px;
      }
      
      .empty-state {
        text-align: center;
        padding: 40px;
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        margin-bottom: var(--section-gap);
      }
      
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--text-secondary);
      }
      
      .sortable {
        cursor: pointer;
        user-select: none;
      }
      
      .sortable:hover {
        background-color: var(--hover-color);
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
      
      .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
        margin-bottom: var(--section-gap);
      }
      
      .card {
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
        overflow: hidden;
        transition: box-shadow 0.3s ease;
        cursor: pointer;
      }
      
      .card:hover {
        box-shadow: var(--shadow-md);
      }
      
      .card-header {
        padding: 16px;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .card-title {
        font-weight: 500;
        margin: 0;
        color: var(--text-primary);
      }
      
      .card-content {
        padding: 16px;
      }
      
      .card-footer {
        padding: 16px;
        border-top: 1px solid var(--border-color);
        display: flex;
        justify-content: flex-end;
        gap: 8px;
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
        background-color: rgba(76, 175, 80, 0.1);
        color: var(--success-color);
      }
      
      .status-badge.inactive {
        background-color: rgba(244, 67, 54, 0.1);
        color: var(--error-color);
      }
      
      .dialog-content {
        margin-bottom: 24px;
        max-height: 70vh;
        overflow-y: auto;
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
        color: var(--text-secondary);
        margin-top: 4px;
      }
      
      .filter-panel {
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
        padding: 16px;
        margin-bottom: var(--section-gap);
      }
      
      .filter-panel-title {
        font-weight: 500;
        margin-top: 0;
        margin-bottom: 16px;
      }
      
      .filter-field-group {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .filter-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
      }
      
      .detail-container {
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
        padding: 24px;
        margin-bottom: var(--section-gap);
      }
      
      .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid var(--border-color);
      }
      
      .detail-title {
        font-size: 20px;
        font-weight: 500;
        margin: 0;
        color: var(--text-primary);
      }
      
      .detail-content {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 24px;
      }
      
      .detail-field {
        margin-bottom: 16px;
      }
      
      .detail-label {
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: 4px;
      }
      
      .detail-value {
        color: var(--text-primary);
      }
      
      .bulk-action-bar {
        background-color: var(--surface-color);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-sm);
        padding: 16px;
        margin-bottom: var(--section-gap);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .bulk-action-message {
        font-weight: 500;
      }
      
      .bulk-actions {
        display: flex;
        gap: 8px;
      }
      
      .error-state {
        background-color: rgba(244, 67, 54, 0.1);
        color: var(--error-color);
        padding: 16px;
        border-radius: var(--border-radius);
        margin-bottom: var(--section-gap);
      }
      
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
      }
      
      @media (max-width: 768px) {
        .header, .toolbar, .pagination-container {
          flex-direction: column;
          align-items: stretch;
        }
        
        .actions-bar {
          margin-top: 16px;
        }
        
        .table {
          display: block;
          overflow-x: auto;
        }
      }
    `;
  }

  constructor() {
    super();
    // Initialize default values
    this.baseUrl = '/api';
    this.entityType = '';
    this.title = 'Entity Manager';
    this.description = 'Manage your entities with CRUD operations';
    this.icon = 'list';
    
    // Default schema is empty - must be provided by user
    this.schema = {
      fields: []
    };
    
    // Default customization options
    this.customActions = [];
    this.layoutType = 'table';
    this.detailTemplate = null;
    this.summaryTemplate = null;
    this.formTemplate = null;
    
    // Initialize state
    this.entities = [];
    this.totalCount = 0;
    this.loading = false;
    this.error = null;
    this.filter = {};
    this.sort = { field: 'id', direction: 'asc' };
    this.pagination = { page: 1, pageSize: 20 };
    this.selectedEntity = null;
    this.selectedItems = [];
    
    // Initialize UI state
    this.showCreateDialog = false;
    this.showEditDialog = false;
    this.showDetailDialog = false;
    this.showDeleteDialog = false;
    this.showBulkDeleteDialog = false;
    this.showFilterPanel = false;
    this.activeTab = 'list';
    
    // Default capabilities
    this.enableCreate = true;
    this.enableEdit = true;
    this.enableDelete = true;
    this.enableExport = true;
    this.enableBulkActions = true;
    this.enableFiltering = true;
    this.enableSorting = true;
    this.enablePagination = true;
    this.enableDetail = true;
    
    // API configuration defaults
    this.apiOptions = {
      // API response format configuration
      dataPath: 'data',
      totalPath: 'meta.total',
      // Request format configuration
      filterFormat: 'filter[{field}]={value}', // '{field}={value}' for simple APIs
      sortFormat: 'sort={direction}{field}', // 'sort={field}&order={direction}' for some APIs
      paginationFormat: 'page[number]={page}&page[size]={pageSize}', // 'page={page}&limit={pageSize}' for simple APIs
      // Methods configuration
      methods: {
        list: 'GET',
        get: 'GET',
        create: 'POST',
        update: 'PUT', // Some APIs use PATCH
        delete: 'DELETE'
      }
    };
    
    // Translation defaults
    this.labels = {
      create: 'Create',
      edit: 'Edit',
      delete: 'Delete',
      export: 'Export',
      search: 'Search',
      filter: 'Filter',
      clearFilters: 'Clear Filters',
      applyFilters: 'Apply Filters',
      cancel: 'Cancel',
      save: 'Save',
      confirm: 'Confirm',
      back: 'Back',
      view: 'View',
      noResults: 'No entities found',
      createPrompt: 'Create your first entity',
      deleteConfirm: 'Are you sure you want to delete this entity?',
      bulkDeleteConfirm: 'Are you sure you want to delete the selected entities?',
      showing: 'Showing',
      of: 'of',
      entries: 'entries',
      selected: 'selected',
      all: 'All',
      loading: 'Loading...',
      errorTitle: 'Error',
      successCreate: 'Entity created successfully',
      successUpdate: 'Entity updated successfully',
      successDelete: 'Entity deleted successfully',
      successBulkDelete: 'Entities deleted successfully',
      errorCreate: 'Error creating entity',
      errorUpdate: 'Error updating entity',
      errorDelete: 'Error deleting entity',
      errorBulkDelete: 'Error deleting entities',
      errorFetch: 'Error fetching entities',
      details: 'Details',
      detailsFor: 'Details for',
      actions: 'Actions',
      bulkActions: 'Bulk Actions',
      itemsSelected: 'items selected',
      selectAll: 'Select All',
      unselectAll: 'Unselect All',
      more: 'More',
      true: 'Yes',
      false: 'No',
      unknown: 'Unknown',
      notAvailable: 'N/A'
    };
  }

  connectedCallback() {
    super.connectedCallback();
    // Load entities when component is connected to DOM
    this.fetchEntities();
  }

  updated(changedProperties) {
    // If critical props like entityType or baseUrl change, refetch
    if (changedProperties.has('entityType') || changedProperties.has('baseUrl')) {
      this.fetchEntities();
    }
    
    // If schema changes, update sortable fields if not explicitly set
    if (changedProperties.has('schema')) {
      this.updateSortableFields();
    }
  }
  
  /**
   * Update sortable fields based on schema if not explicitly provided
   */
  updateSortableFields() {
    // If schema has sortable fields defined, extract them
    if (this.schema?.fields) {
      // Fields where sortable is either undefined or true
      const sortableFields = this.schema.fields
        .filter(field => field.sortable !== false)
        .map(field => field.name);
      
      // Store these as the sortable fields if not already set
      if (!this.sortableFields || this.sortableFields.length === 0) {
        this.sortableFields = sortableFields;
      }
    }
  }

  /**
   * Format URL for API requests based on apiOptions configuration
   * @param {string} operation - The operation type ('list', 'get', 'create', 'update', 'delete')
   * @param {string|number} id - Optional entity ID for specific operations
   * @returns {URL} Formatted URL object
   */
  formatApiUrl(operation, id = null) {
    let basePath = `${this.baseUrl}/${this.entityType}`;
    
    // Add ID to path for single-entity operations
    if (id !== null && ['get', 'update', 'delete'].includes(operation)) {
      basePath = `${basePath}/${id}`;
    }
    
    const url = new URL(basePath, window.location.origin);
    
    // Add query parameters for list operation
    if (operation === 'list') {
      // Add filter parameters
      if (this.filter && Object.keys(this.filter).length > 0) {
        Object.entries(this.filter).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            // Format: filter[field]=value or field=value depending on API
            const paramName = this.apiOptions.filterFormat
              .replace('{field}', key)
              .split('=')[0];
            const paramValue = value;
            url.searchParams.append(paramName, paramValue);
          }
        });
      }
      
      // Add sorting
      if (this.sort && this.sort.field) {
        // Format: sort=direction+field or sort=field&order=direction
        const sortParam = this.apiOptions.sortFormat
          .replace('{direction}', this.sort.direction === 'desc' ? '-' : '')
          .replace('{field}', this.sort.field);
        
        const [name, value] = sortParam.split('=');
        url.searchParams.append(name, value);
      }
      
      // Add pagination
      if (this.pagination) {
        // Format: page[number]=1&page[size]=20 or page=1&limit=20
        const paginationParams = this.apiOptions.paginationFormat
          .replace('{page}', this.pagination.page.toString())
          .replace('{pageSize}', this.pagination.pageSize.toString());
        
        paginationParams.split('&').forEach(param => {
          const [name, value] = param.split('=');
          url.searchParams.append(name, value);
        });
      }
    }
    
    return url;
  }

  /**
   * Fetch entities from the server
   */
  async fetchEntities() {
    this.loading = true;
    this.error = null;
    
    try {
      const url = this.formatApiUrl('list');
      
      const response = await fetch(url.toString(), {
        method: this.apiOptions.methods.list
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      // Extract data and metadata based on configured paths
      const dataPath = this.apiOptions.dataPath;
      const totalPath = this.apiOptions.totalPath;
      
      // Get data from response
      this.entities = dataPath ? this.getNestedValue(result, dataPath) : result;
      
      // If no entities or not an array, set to empty array
      if (!this.entities || !Array.isArray(this.entities)) {
        this.entities = [];
      }
      
      // Get total count from response metadata
      if (totalPath) {
        this.totalCount = this.getNestedValue(result, totalPath) || this.entities.length;
      } else {
        this.totalCount = this.entities.length;
      }
      
      // Reset selected items when data changes
      this.selectedItems = [];
    } catch (error) {
      console.error('Error fetching entities:', error);
      this.error = error.message;
      this._showNotification(this.labels.errorFetch + ': ' + error.message, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Get nested value from object using dot notation
   * @param {Object} obj - The object to extract value from
   * @param {string} path - Dot notation path (e.g. 'meta.total')
   * @returns {*} The value at the specified path or undefined
   */
  getNestedValue(obj, path) {
    if (!obj || !path) return undefined;
    
    const keys = path.split('.');
    let result = obj;
    
    for (const key of keys) {
      if (result == null || typeof result !== 'object') {
        return undefined;
      }
      result = result[key];
    }
    
    return result;
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
      
      // Dispatch filter changed event
      this.dispatchEvent(new CustomEvent('filter-changed', {
        detail: { filter: this.filter }
      }));
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
  }
  
  /**
   * Apply current filters
   */
  applyFilters() {
    this.pagination.page = 1; // Reset to first page on filter change
    this.fetchEntities();
    this.showFilterPanel = false;
    
    // Dispatch filter changed event
    this.dispatchEvent(new CustomEvent('filter-changed', {
      detail: { filter: this.filter }
    }));
  }
  
  /**
   * Clear all filters
   */
  clearFilters() {
    this.filter = {};
    this.pagination.page = 1;
    this.fetchEntities();
    
    // Dispatch filter changed event
    this.dispatchEvent(new CustomEvent('filter-changed', {
      detail: { filter: this.filter }
    }));
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
    
    // Dispatch sort changed event
    this.dispatchEvent(new CustomEvent('sort-changed', {
      detail: { sort: this.sort }
    }));
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
    
    // Dispatch page changed event
    this.dispatchEvent(new CustomEvent('page-changed', {
      detail: { pagination: this.pagination }
    }));
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
    
    // Dispatch page changed event
    this.dispatchEvent(new CustomEvent('page-changed', {
      detail: { pagination: this.pagination }
    }));
  }
  
  /**
   * Toggle filter panel
   */
  toggleFilterPanel() {
    this.showFilterPanel = !this.showFilterPanel;
  }
  
  /**
   * Open create dialog
   */
  openCreateDialog() {
    // Initialize a new entity with default values from schema
    this.selectedEntity = this.createDefaultEntity();
    this.showCreateDialog = true;
  }
  
  /**
   * Create a default entity with values based on schema
   * @returns {Object} New entity with default values
   */
  createDefaultEntity() {
    const entity = {};
    
    if (this.schema?.fields) {
      for (const field of this.schema.fields) {
        // Skip calculated fields
        if (field.calculated) continue;
        
        // Use default value if provided
        if (field.defaultValue !== undefined) {
          entity[field.name] = field.defaultValue;
        } else {
          // Otherwise set appropriate empty value based on type
          switch (field.type) {
            case 'string':
              entity[field.name] = '';
              break;
            case 'number':
              entity[field.name] = null;
              break;
            case 'boolean':
              entity[field.name] = false;
              break;
            case 'array':
              entity[field.name] = [];
              break;
            case 'object':
              entity[field.name] = {};
              break;
            default:
              entity[field.name] = null;
          }
        }
      }
    }
    
    return entity;
  }
  
  /**
   * Open detail dialog for selected entity
   * @param {Object} entity - Entity to view
   */
  openDetailDialog(entity) {
    this.selectedEntity = { ...entity };
    this.showDetailDialog = true;
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
   * Open bulk delete confirmation dialog
   */
  openBulkDeleteDialog() {
    if (this.selectedItems.length === 0) return;
    this.showBulkDeleteDialog = true;
  }
  
  /**
   * Close all dialogs
   */
  closeDialogs() {
    this.showCreateDialog = false;
    this.showEditDialog = false;
    this.showDetailDialog = false;
    this.showDeleteDialog = false;
    this.showBulkDeleteDialog = false;
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
      const url = this.formatApiUrl('create');
      
      const response = await fetch(url.toString(), {
        method: this.apiOptions.methods.create,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.selectedEntity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      this._showNotification(this.labels.successCreate, 'success');
      this.dispatchEvent(new CustomEvent('entity-created', {
        detail: { 
          entity: this.apiOptions.dataPath ? 
            this.getNestedValue(result, this.apiOptions.dataPath) : 
            result 
        }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error creating entity:', error);
      this._showNotification(this.labels.errorCreate + ': ' + error.message, 'error');
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
      const url = this.formatApiUrl('update', this.selectedEntity.id);
      
      const response = await fetch(url.toString(), {
        method: this.apiOptions.methods.update,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.selectedEntity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      this._showNotification(this.labels.successUpdate, 'success');
      this.dispatchEvent(new CustomEvent('entity-updated', {
        detail: { 
          entity: this.apiOptions.dataPath ? 
            this.getNestedValue(result, this.apiOptions.dataPath) : 
            result 
        }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error updating entity:', error);
      this._showNotification(this.labels.errorUpdate + ': ' + error.message, 'error');
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
      const url = this.formatApiUrl('delete', this.selectedEntity.id);
      
      const response = await fetch(url.toString(), {
        method: this.apiOptions.methods.delete
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      this._showNotification(this.labels.successDelete, 'success');
      this.dispatchEvent(new CustomEvent('entity-deleted', {
        detail: { entityId: this.selectedEntity.id }
      }));
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error deleting entity:', error);
      this._showNotification(this.labels.errorDelete + ': ' + error.message, 'error');
    } finally {
      this.loading = false;
    }
  }
  
  /**
   * Delete multiple entities in bulk
   */
  async bulkDeleteEntities() {
    if (this.selectedItems.length === 0) {
      return;
    }
    
    this.loading = true;
    
    try {
      // Execute delete requests in sequence to avoid overwhelming server
      for (const entityId of this.selectedItems) {
        const url = this.formatApiUrl('delete', entityId);
        
        const response = await fetch(url.toString(), {
          method: this.apiOptions.methods.delete
        });
        
        if (!response.ok) {
          throw new Error(`API returned status ${response.status} for entity ${entityId}`);
        }
      }
      
      this._showNotification(this.labels.successBulkDelete, 'success');
      this.dispatchEvent(new CustomEvent('entities-deleted', {
        detail: { entityIds: [...this.selectedItems] }
      }));
      
      // Clear selected items
      this.selectedItems = [];
      
      // Refresh entity list
      this.fetchEntities();
      
      // Close dialog
      this.closeDialogs();
    } catch (error) {
      console.error('Error bulk deleting entities:', error);
      this._showNotification(this.labels.errorBulkDelete + ': ' + error.message, 'error');
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
      const baseUrl = this.formatApiUrl('list');
      // Set a larger page size for export
      baseUrl.searchParams.set('page[size]', '1000');
      
      const response = await fetch(baseUrl.toString(), {
        method: this.apiOptions.methods.list
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      
      // Extract data based on configured path
      const dataPath = this.apiOptions.dataPath;
      const entities = dataPath ? this.getNestedValue(result, dataPath) : result;
      
      if (!entities || entities.length === 0) {
        this._showNotification('No data to export', 'warning');
        return;
      }
      
      // Get field definitions from schema
      const fields = this.schema?.fields || [];
      
      // Use schema fields or extract from first entity
      const headers = fields.length > 0 ? 
        fields.map(field => field.label || field.name) :
        Object.keys(entities[0]);
      
      // Generate CSV rows
      const rows = entities.map(entity => 
        fields.length > 0 ?
          fields.map(field => {
            const value = this.getNestedValue(entity, field.name);
            return this.formatValueForExport(value);
          }) :
          Object.values(entity).map(value => this.formatValueForExport(value))
      );
      
      // Generate CSV content
      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');
      
      // Create and download CSV file
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
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
   * Format a value for export to CSV
   * @param {*} value - Value to format
   * @returns {string} CSV-safe string representation
   */
  formatValueForExport(value) {
    if (value === null || value === undefined) {
      return '';
    }
    
    if (typeof value === 'object') {
      value = JSON.stringify(value);
    }
    
    // Escape quotes and wrap in quotes if contains comma or quotes
    value = String(value);
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return '"' + value.replace(/"/g, '""') + '"';
    }
    
    return value;
  }
  
  /**
   * Handle select all checkbox
   * @param {Event} e - Change event
   */
  handleSelectAll(e) {
    if (e.target.checked) {
      this.selectedItems = this.entities.map(entity => entity.id);
    } else {
      this.selectedItems = [];
    }
    this.requestUpdate();
  }
  
  /**
   * Handle individual item selection
   * @param {Event} e - Change event
   * @param {string|number} id - Entity ID
   */
  handleSelectItem(e, id) {
    if (e.target.checked) {
      if (!this.selectedItems.includes(id)) {
        this.selectedItems = [...this.selectedItems, id];
      }
    } else {
      this.selectedItems = this.selectedItems.filter(itemId => itemId !== id);
    }
    this.requestUpdate();
  }
  
  /**
   * Handle row click to view entity details
   * @param {Object} entity - Clicked entity
   * @param {Event} e - Click event
   */
  handleRowClick(entity, e) {
    // Ignore if clicking on checkbox or action buttons
    if (e.target.closest('wa-checkbox') || e.target.closest('.actions')) {
      return;
    }
    
    if (this.enableDetail) {
      this.openDetailDialog(entity);
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
   * Format field value based on schema configuration
   * @param {Object} entity - Entity object
   * @param {Object} field - Field configuration from schema
   * @returns {*} Formatted value
   */
  formatFieldValue(entity, field) {
    const value = this.getNestedValue(entity, field.name);
    
    // Handle null/undefined values
    if (value === null || value === undefined) {
      return this.labels.notAvailable;
    }
    
    // Use custom formatter if provided
    if (field.format && typeof field.format === 'function') {
      return field.format(value, entity);
    }
    
    // Format based on field type
    switch (field.type) {
      case 'date':
        return new Date(value).toLocaleDateString();
      
      case 'dateTime':
      case 'datetime':
        return new Date(value).toLocaleString();
      
      case 'boolean':
        return value ? this.labels.true : this.labels.false;
      
      case 'status':
        return html`
          <span class="status-badge ${value ? 'active' : 'inactive'}">
            ${value ? 'Active' : 'Inactive'}
          </span>
        `;
      
      case 'object':
      case 'array':
        if (typeof value === 'object') {
          return JSON.stringify(value);
        }
        return value;
      
      default:
        return value;
    }
  }
  
  /**
   * Render table view
   * @returns {import('lit').TemplateResult}
   */
  renderTableView() {
    const fields = this.schema?.fields || [];
    const sortableFields = fields.filter(field => field.sortable !== false).map(field => field.name);
    
    return html`
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              ${this.enableBulkActions ? html`
                <th class="bulk-select">
                  <wa-checkbox
                    @change=${this.handleSelectAll}
                    ?checked=${this.selectedItems.length === this.entities.length && this.entities.length > 0}
                    ?indeterminate=${this.selectedItems.length > 0 && this.selectedItems.length < this.entities.length}>
                  </wa-checkbox>
                </th>
              ` : ''}
              
              ${fields.map(field => !field.hidden ? html`
                <th 
                  class="${sortableFields.includes(field.name) && this.enableSorting ? 'sortable' : ''} 
                         ${this.sort.field === field.name ? this.sort.direction : ''}"
                  @click=${sortableFields.includes(field.name) && this.enableSorting ? 
                           () => this.handleSort(field.name) : null}>
                  ${field.label || field.name}
                </th>
              ` : '')}
              
              ${(this.enableEdit || this.enableDelete || this.customActions.length > 0) ? 
                html`<th>${this.labels.actions}</th>` : ''}
            </tr>
          </thead>
          <tbody>
            ${repeat(this.entities, entity => entity.id || Math.random(), entity => html`
              <tr @click=${(e) => this.handleRowClick(entity, e)}>
                ${this.enableBulkActions ? html`
                  <td>
                    <wa-checkbox
                      ?checked=${this.selectedItems.includes(entity.id)}
                      @change=${(e) => this.handleSelectItem(e, entity.id)}>
                    </wa-checkbox>
                  </td>
                ` : ''}
                
                ${fields.map(field => !field.hidden ? html`
                  <td>${this.formatFieldValue(entity, field)}</td>
                ` : '')}
                
                ${(this.enableEdit || this.enableDelete || this.customActions.length > 0) ? html`
                  <td class="actions">
                    ${this.enableDetail ? html`
                      <wa-button variant="text" color="primary" @click=${(e) => { e.stopPropagation(); this.openDetailDialog(entity); }}>
                        <wa-icon name="visibility"></wa-icon>
                      </wa-button>
                    ` : ''}
                    
                    ${this.enableEdit ? html`
                      <wa-button variant="text" color="primary" @click=${(e) => { e.stopPropagation(); this.openEditDialog(entity); }}>
                        <wa-icon name="edit"></wa-icon>
                      </wa-button>
                    ` : ''}
                    
                    ${this.enableDelete ? html`
                      <wa-button variant="text" color="error" @click=${(e) => { e.stopPropagation(); this.openDeleteDialog(entity); }}>
                        <wa-icon name="delete"></wa-icon>
                      </wa-button>
                    ` : ''}
                    
                    ${this.customActions.map(action => html`
                      <wa-button 
                        variant="text" 
                        color=${action.color || 'primary'} 
                        @click=${(e) => { 
                          e.stopPropagation(); 
                          if (action.handler) action.handler(entity);
                        }}
                        title=${action.label}>
                        <wa-icon name=${action.icon}></wa-icon>
                      </wa-button>
                    `)}
                  </td>
                ` : ''}
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }
  
  /**
   * Render card/grid view
   * @returns {import('lit').TemplateResult}
   */
  renderCardView() {
    const fields = this.schema?.fields || [];
    
    return html`
      <div class="grid-container">
        ${repeat(this.entities, entity => entity.id || Math.random(), entity => {
          // Find title and summary fields from schema
          const titleField = fields.find(f => f.isTitle) || fields[0];
          const summaryFields = fields.filter(f => f.inSummary && !f.hidden).slice(0, 3);
          
          return html`
            <div class="card" @click=${() => this.enableDetail && this.openDetailDialog(entity)}>
              <div class="card-header">
                <h3 class="card-title">
                  ${titleField ? this.formatFieldValue(entity, titleField) : entity.id}
                </h3>
                
                ${this.enableBulkActions ? html`
                  <wa-checkbox
                    ?checked=${this.selectedItems.includes(entity.id)}
                    @change=${(e) => { e.stopPropagation(); this.handleSelectItem(e, entity.id); }}>
                  </wa-checkbox>
                ` : ''}
              </div>
              
              <div class="card-content">
                ${summaryFields.map(field => html`
                  <div class="detail-field">
                    <div class="detail-label">${field.label || field.name}</div>
                    <div class="detail-value">${this.formatFieldValue(entity, field)}</div>
                  </div>
                `)}
                
                ${this.summaryTemplate ? this.summaryTemplate(entity) : ''}
              </div>
              
              <div class="card-footer">
                ${this.enableDetail ? html`
                  <wa-button variant="text" color="primary" @click=${(e) => { e.stopPropagation(); this.openDetailDialog(entity); }}>
                    <wa-icon name="visibility"></wa-icon>
                  </wa-button>
                ` : ''}
                
                ${this.enableEdit ? html`
                  <wa-button variant="text" color="primary" @click=${(e) => { e.stopPropagation(); this.openEditDialog(entity); }}>
                    <wa-icon name="edit"></wa-icon>
                  </wa-button>
                ` : ''}
                
                ${this.enableDelete ? html`
                  <wa-button variant="text" color="error" @click=${(e) => { e.stopPropagation(); this.openDeleteDialog(entity); }}>
                    <wa-icon name="delete"></wa-icon>
                  </wa-button>
                ` : ''}
                
                ${this.customActions.map(action => html`
                  <wa-button 
                    variant="text" 
                    color=${action.color || 'primary'} 
                    @click=${(e) => { 
                      e.stopPropagation(); 
                      if (action.handler) action.handler(entity);
                    }}
                    title=${action.label}>
                    <wa-icon name=${action.icon}></wa-icon>
                  </wa-button>
                `)}
              </div>
            </div>
          `;
        })}
      </div>
    `;
  }
  
  /**
   * Render form fields based on schema
   * @returns {import('lit').TemplateResult}
   */
  renderFormFields() {
    // If a custom form template is provided, use it
    if (this.formTemplate && typeof this.formTemplate === 'function') {
      return this.formTemplate(this.selectedEntity, this.handleFieldChange.bind(this));
    }
    
    const fields = this.schema?.fields || [];
    
    return html`
      <div class="form-grid">
        ${fields.map(field => {
          // Skip hidden, read-only, calculated fields and ID field (unless it's editable)
          if (field.hidden || field.readOnly || field.calculated || 
              (field.name === 'id' && !field.editable)) {
            return '';
          }
          
          const value = this.selectedEntity ? 
            this.getNestedValue(this.selectedEntity, field.name) : '';
          
          return html`
            <div class="field-row">
              <label class="field-label" for="${field.name}">${field.label || field.name}</label>
              
              ${this.renderFormField(field, value)}
              
              ${field.description ? html`
                <div class="field-description">${field.description}</div>
              ` : ''}
            </div>
          `;
        })}
      </div>
    `;
  }
  
  /**
   * Render specific form field based on field type
   * @param {Object} field - Field configuration
   * @param {*} value - Current field value
   * @returns {import('lit').TemplateResult}
   */
  renderFormField(field, value) {
    switch(field.type) {
      case 'boolean':
        return html`
          <wa-switch
            name="${field.name}"
            ?checked=${value}
            @change=${this.handleFieldChange}>
          </wa-switch>
        `;
      
      case 'select':
        return html`
          <wa-select
            name="${field.name}"
            .value=${value}
            @change=${this.handleFieldChange}>
            ${field.options?.map(option => html`
              <wa-option value="${option.value}">${option.label}</wa-option>
            `)}
          </wa-select>
        `;
      
      case 'multiselect':
        return html`
          <wa-select
            name="${field.name}"
            .value=${value}
            multiple
            @change=${this.handleFieldChange}>
            ${field.options?.map(option => html`
              <wa-option value="${option.value}">${option.label}</wa-option>
            `)}
          </wa-select>
        `;
      
      case 'textarea':
      case 'text':
        return html`
          <wa-textarea
            name="${field.name}"
            .value=${value}
            @input=${this.handleFieldChange}>
          </wa-textarea>
        `;
      
      case 'date':
        return html`
          <wa-input
            type="date"
            name="${field.name}"
            .value=${value}
            @input=${this.handleFieldChange}>
          </wa-input>
        `;
      
      case 'datetime':
      case 'dateTime':
        return html`
          <wa-input
            type="datetime-local"
            name="${field.name}"
            .value=${value}
            @input=${this.handleFieldChange}>
          </wa-input>
        `;
      
      case 'number':
        return html`
          <wa-input
            type="number"
            name="${field.name}"
            .value=${value}
            step="${field.step || 1}"
            min="${field.min || ''}"
            max="${field.max || ''}"
            @input=${this.handleFieldChange}>
          </wa-input>
        `;
      
      // Default to text input
      default:
        return html`
          <wa-input
            type="text"
            name="${field.name}"
            .value=${value}
            @input=${this.handleFieldChange}>
          </wa-input>
        `;
    }
  }
  
  /**
   * Render entity detail view
   * @returns {import('lit').TemplateResult}
   */
  renderDetailView() {
    // If no entity is selected, show nothing
    if (!this.selectedEntity) return '';
    
    // If a custom detail template is provided, use it
    if (this.detailTemplate && typeof this.detailTemplate === 'function') {
      return this.detailTemplate(this.selectedEntity);
    }
    
    const fields = this.schema?.fields || [];
    const titleField = fields.find(f => f.isTitle) || fields[0];
    
    return html`
      <div class="detail-container">
        <div class="detail-header">
          <h2 class="detail-title">
            ${this.labels.detailsFor} 
            ${titleField ? this.formatFieldValue(this.selectedEntity, titleField) : this.selectedEntity.id}
          </h2>
          
          <div class="actions">
            ${this.enableEdit ? html`
              <wa-button @click=${() => this.openEditDialog(this.selectedEntity)}>
                <wa-icon slot="prefix" name="edit"></wa-icon>
                ${this.labels.edit}
              </wa-button>
            ` : ''}
            
            ${this.enableDelete ? html`
              <wa-button color="error" @click=${() => this.openDeleteDialog(this.selectedEntity)}>
                <wa-icon slot="prefix" name="delete"></wa-icon>
                ${this.labels.delete}
              </wa-button>
            ` : ''}
          </div>
        </div>
        
        <div class="detail-content">
          ${fields.map(field => {
            if (field.hidden) return '';
            
            return html`
              <div class="detail-field">
                <div class="detail-label">${field.label || field.name}</div>
                <div class="detail-value">${this.formatFieldValue(this.selectedEntity, field)}</div>
              </div>
            `;
          })}
        </div>
      </div>
    `;
  }
  
  /**
   * Render create dialog
   * @returns {import('lit').TemplateResult}
   */
  renderCreateDialog() {
    if (!this.showCreateDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">${this.labels.create} ${this.entityType}</div>
        
        <div class="dialog-content">
          ${this.renderFormFields()}
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
   */
  renderEditDialog() {
    if (!this.showEditDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">${this.labels.edit} ${this.entityType}</div>
        
        <div class="dialog-content">
          ${this.renderFormFields()}
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
   * Render detail dialog
   * @returns {import('lit').TemplateResult}
   */
  renderDetailDialog() {
    if (!this.showDetailDialog) {
      return '';
    }
    
    const fields = this.schema?.fields || [];
    const titleField = fields.find(f => f.isTitle) || fields[0];
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">
          ${this.labels.details} - 
          ${titleField ? this.formatFieldValue(this.selectedEntity, titleField) : this.selectedEntity.id}
        </div>
        
        <div class="dialog-content">
          ${this.detailTemplate ? 
            this.detailTemplate(this.selectedEntity) : 
            html`
              <div class="detail-content">
                ${fields.map(field => {
                  if (field.hidden) return '';
                  
                  return html`
                    <div class="detail-field">
                      <div class="detail-label">${field.label || field.name}</div>
                      <div class="detail-value">${this.formatFieldValue(this.selectedEntity, field)}</div>
                    </div>
                  `;
                })}
              </div>
            `
          }
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.close}
          </wa-button>
          ${this.enableEdit ? html`
            <wa-button color="primary" @click=${() => {
              this.closeDialogs();
              this.openEditDialog(this.selectedEntity);
            }}>
              ${this.labels.edit}
            </wa-button>
          ` : ''}
        </div>
      </wa-dialog>
    `;
  }
  
  /**
   * Render delete confirmation dialog
   * @returns {import('lit').TemplateResult}
   */
  renderDeleteDialog() {
    if (!this.showDeleteDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">${this.labels.delete} ${this.entityType}</div>
        
        <div class="dialog-content">
          <p>${this.labels.deleteConfirm}</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.cancel}
          </wa-button>
          <wa-button color="error" @click=${this.deleteEntity} ?loading=${this.loading}>
            ${this.labels.confirm}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  /**
   * Render bulk delete confirmation dialog
   * @returns {import('lit').TemplateResult}
   */
  renderBulkDeleteDialog() {
    if (!this.showBulkDeleteDialog) {
      return '';
    }
    
    return html`
      <wa-dialog open @close=${this.closeDialogs}>
        <div slot="header">${this.labels.delete} ${this.selectedItems.length} ${this.entityType}</div>
        
        <div class="dialog-content">
          <p>${this.labels.bulkDeleteConfirm}</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div slot="footer">
          <wa-button variant="outlined" @click=${this.closeDialogs}>
            ${this.labels.cancel}
          </wa-button>
          <wa-button color="error" @click=${this.bulkDeleteEntities} ?loading=${this.loading}>
            ${this.labels.confirm}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  /**
   * Render filter panel
   * @returns {import('lit').TemplateResult}
   */
  renderFilterPanel() {
    if (!this.showFilterPanel || !this.enableFiltering) {
      return '';
    }
    
    const fields = this.schema?.fields || [];
    const filterableFields = fields.filter(field => field.filterable !== false && !field.hidden);
    
    return html`
      <div class="filter-panel">
        <h3 class="filter-panel-title">${this.labels.filter}</h3>
        
        <div class="filter-field-group">
          ${filterableFields.map(field => html`
            <div class="field-row">
              <label class="field-label">${field.label || field.name}</label>
              
              ${field.type === 'select' || field.type === 'multiselect' ? html`
                <wa-select
                  name="${field.name}"
                  .value=${this.filter[field.name] || ''}
                  @change=${this.handleFilterChange}>
                  <wa-option value="">${this.labels.all}</wa-option>
                  ${field.options?.map(option => html`
                    <wa-option value="${option.value}">${option.label}</wa-option>
                  `)}
                </wa-select>
              ` : field.type === 'boolean' ? html`
                <wa-select
                  name="${field.name}"
                  .value=${this.filter[field.name] || ''}
                  @change=${this.handleFilterChange}>
                  <wa-option value="">${this.labels.all}</wa-option>
                  <wa-option value="true">${this.labels.true}</wa-option>
                  <wa-option value="false">${this.labels.false}</wa-option>
                </wa-select>
              ` : html`
                <wa-input
                  type="${field.type === 'number' ? 'number' : 'text'}"
                  name="${field.name}"
                  .value=${this.filter[field.name] || ''}
                  @input=${this.handleFilterChange}>
                </wa-input>
              `}
            </div>
          `)}
        </div>
        
        <div class="filter-actions">
          <wa-button variant="outlined" @click=${this.clearFilters}>
            ${this.labels.clearFilters}
          </wa-button>
          <wa-button color="primary" @click=${this.applyFilters}>
            ${this.labels.applyFilters}
          </wa-button>
        </div>
      </div>
    `;
  }
  
  /**
   * Render bulk action bar
   * @returns {import('lit').TemplateResult}
   */
  renderBulkActionBar() {
    if (!this.enableBulkActions || this.selectedItems.length === 0) {
      return '';
    }
    
    return html`
      <div class="bulk-action-bar">
        <div class="bulk-action-message">
          ${this.selectedItems.length} ${this.labels.itemsSelected}
        </div>
        
        <div class="bulk-actions">
          <wa-button variant="outlined" @click=${() => this.selectedItems = []}>
            ${this.labels.unselectAll}
          </wa-button>
          
          ${this.enableDelete ? html`
            <wa-button color="error" @click=${this.openBulkDeleteDialog}>
              <wa-icon slot="prefix" name="delete"></wa-icon>
              ${this.labels.delete}
            </wa-button>
          ` : ''}
          
          ${this.customActions.filter(action => action.bulk).map(action => html`
            <wa-button 
              color=${action.color || 'primary'} 
              @click=${() => {
                if (action.bulkHandler) action.bulkHandler(this.selectedItems);
              }}>
              <wa-icon slot="prefix" name=${action.icon}></wa-icon>
              ${action.label}
            </wa-button>
          `)}
        </div>
      </div>
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
          
          <div class="actions-bar">
            ${this.enableCreate ? html`
              <wa-button @click=${this.openCreateDialog}>
                <wa-icon slot="prefix" name="add"></wa-icon>
                ${this.labels.create}
              </wa-button>
            ` : ''}
            
            ${this.customActions.filter(action => action.location === 'header').map(action => html`
              <wa-button 
                color=${action.color || 'primary'} 
                @click=${action.handler}>
                <wa-icon slot="prefix" name=${action.icon}></wa-icon>
                ${action.label}
              </wa-button>
            `)}
          </div>
        </div>
        
        ${this.error ? html`
          <div class="error-state">
            <h3>${this.labels.errorTitle}</h3>
            <p>${this.error}</p>
          </div>
        ` : ''}
        
        ${this.renderBulkActionBar()}
        
        <div class="toolbar">
          <div class="search-filter-bar">
            <wa-input 
              class="search-input"
              placeholder="${this.labels.search}"
              .value=${this.filter.search || ''}
              @input=${this.handleSearchInput}>
              <wa-icon slot="prefix" name="search"></wa-icon>
            </wa-input>
            
            ${this.enableFiltering ? html`
              <wa-button variant="outlined" @click=${this.toggleFilterPanel}>
                <wa-icon slot="prefix" name="filter_list"></wa-icon>
                ${this.labels.filter}
              </wa-button>
            ` : ''}
            
            ${this.enableExport ? html`
              <wa-button variant="outlined" @click=${this.exportEntities}>
                <wa-icon slot="prefix" name="download"></wa-icon>
                ${this.labels.export}
              </wa-button>
            ` : ''}
          </div>
        </div>
        
        ${this.renderFilterPanel()}
        
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
          ${this.layoutType === 'card' || this.layoutType === 'grid' ? 
            this.renderCardView() : 
            this.renderTableView()}
          
          ${this.enablePagination ? html`
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
          ` : ''}
        `}
        
        ${this.renderCreateDialog()}
        ${this.renderEditDialog()}
        ${this.renderDetailDialog()}
        ${this.renderDeleteDialog()}
        ${this.renderBulkDeleteDialog()}
        
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

customElements.define('wa-crud-manager', WebAwesomeCrudManager);