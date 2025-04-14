import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-checkbox.js';
import '@webcomponents/awesome/wa-textarea.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-chip.js';
import '@webcomponents/awesome/wa-tooltip.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-code-editor.js';

/**
 * @element wa-queries-manager
 * @description Component for managing queries and filters in the UNO framework
 */
export class WebAwesomeQueriesManager extends LitElement {
  static get properties() {
    return {
      // Common properties
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      selectedItem: { type: Object },
      
      // Query properties
      queries: { type: Array },
      queryFilter: { type: String },
      
      // Query Path properties
      queryPaths: { type: Array },
      queryPathFilter: { type: String },
      
      // Meta Type properties
      metaTypes: { type: Array },
      selectedMetaTypeId: { type: String },
      
      // Dialog flags
      showCreateQueryDialog: { type: Boolean },
      showEditQueryDialog: { type: Boolean },
      showCreateQueryPathDialog: { type: Boolean },
      showEditQueryPathDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      showExecuteQueryDialog: { type: Boolean },
      
      // Form models
      queryForm: { type: Object },
      queryPathForm: { type: Object },
      deleteDialogData: { type: Object },
      executeQueryForm: { type: Object },
      
      // Query execution results
      queryResults: { type: Array },
      resultCount: { type: Number },
      isExecutingQuery: { type: Boolean }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --queries-bg: var(--wa-background-color, #f5f5f5);
        --queries-padding: 20px;
      }
      
      .container {
        padding: var(--queries-padding);
        background-color: var(--queries-bg);
        min-height: 600px;
      }
      
      .header {
        margin-bottom: 24px;
      }
      
      .title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      
      .subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      
      .content-card {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 24px;
        margin-bottom: 24px;
      }
      
      .actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 16px;
      }
      
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
      }
      
      .grid-item {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
      }
      
      .grid-item:hover {
        transform: translateY(-3px);
        box-shadow: var(--wa-shadow-2, 0 2px 4px rgba(0,0,0,0.2));
      }
      
      .item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      
      .item-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
      }
      
      .item-meta {
        display: flex;
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        gap: 8px;
      }
      
      .item-description {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0 0 16px 0;
      }
      
      .badge {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 8px;
      }
      
      .filter-bar {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
      }
      
      .filter-input {
        flex: 1;
      }
      
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .form-full-width {
        grid-column: 1 / -1;
      }
      
      .dialog-content {
        padding: 24px;
        min-width: 500px;
      }
      
      .dialog-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding: 8px 24px 24px;
      }
      
      .query-chip {
        display: inline-flex;
        align-items: center;
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 14px;
        margin-right: 8px;
        margin-bottom: 8px;
      }
      
      .query-chip wa-icon {
        font-size: 16px;
        margin-left: 4px;
        cursor: pointer;
      }
      
      .tags-container {
        display: flex;
        flex-wrap: wrap;
        margin-top: 8px;
      }
      
      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 48px;
        text-align: center;
      }
      
      .empty-state wa-icon {
        font-size: 48px;
        margin-bottom: 16px;
        color: var(--wa-text-secondary-color, #757575);
      }
      
      .empty-state h3 {
        margin-top: 0;
        margin-bottom: 8px;
      }
      
      .empty-state p {
        color: var(--wa-text-secondary-color, #757575);
        margin-top: 0;
      }
      
      .detail-panel {
        margin-top: 24px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      
      .detail-header {
        padding: 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .detail-content {
        padding: 16px;
      }
      
      .detail-title {
        font-size: 20px;
        font-weight: 500;
        margin: 0;
      }
      
      .detail-meta {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin-top: 4px;
      }
      
      .detail-property {
        margin-bottom: 16px;
      }
      
      .detail-label {
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .detail-value {
        color: var(--wa-text-secondary-color, #757575);
      }
      
      .detail-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
      }
      
      .code-block {
        background-color: var(--wa-code-bg, #f5f5f5);
        border-radius: 4px;
        padding: 16px;
        font-family: monospace;
        white-space: pre-wrap;
        margin-bottom: 16px;
        overflow: auto;
        max-height: 300px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
      }
      
      .query-value-list {
        margin-top: 16px;
      }
      
      .query-value-item {
        background-color: var(--wa-background-color, #f5f5f5);
        border-radius: 4px;
        padding: 12px;
        margin-bottom: 8px;
      }
      
      .query-value-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .query-value-path {
        font-weight: 500;
      }
      
      .query-value-details {
        margin-top: 8px;
      }
      
      .query-value-values {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
      
      .results-panel {
        margin-top: 24px;
        padding: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
      }
      
      .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      
      .results-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
      }
      
      .results-count {
        color: var(--wa-text-secondary-color, #757575);
      }
      
      .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 8px;
      }
      
      .result-item {
        background-color: var(--wa-background-color, #f5f5f5);
        padding: 8px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.2s ease;
      }
      
      .result-item:hover {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
      }
      
      .lookup-select {
        width: 100%;
      }
      
      .match-settings {
        display: flex;
        gap: 16px;
        margin-top: 16px;
      }
      
      .match-setting {
        flex: 1;
        padding: 12px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: 4px;
      }
      
      .match-title {
        font-weight: 500;
        margin-bottom: 8px;
      }
    `;
  }

  constructor() {
    super();
    this.activeTab = 'queries';
    this.loading = false;
    this.error = null;
    this.selectedItem = null;
    
    this.queries = [];
    this.queryFilter = '';
    
    this.queryPaths = [];
    this.queryPathFilter = '';
    
    this.metaTypes = [];
    this.selectedMetaTypeId = '';
    
    this.showCreateQueryDialog = false;
    this.showEditQueryDialog = false;
    this.showCreateQueryPathDialog = false;
    this.showEditQueryPathDialog = false;
    this.showDeleteDialog = false;
    this.showExecuteQueryDialog = false;
    
    this.queryForm = this._getDefaultQueryForm();
    this.queryPathForm = this._getDefaultQueryPathForm();
    this.deleteDialogData = {
      type: '',
      id: '',
      name: ''
    };
    this.executeQueryForm = {
      queryId: '',
      limit: 100,
      offset: 0
    };
    
    this.queryResults = [];
    this.resultCount = 0;
    this.isExecutingQuery = false;
    
    // Load mock data for demonstration
    this._loadMockData();
  }

  _getDefaultQueryForm() {
    return {
      name: '',
      description: '',
      query_meta_type_id: '',
      include_values: 'INCLUDE',
      match_values: 'AND',
      include_queries: 'INCLUDE',
      match_queries: 'AND',
      query_values: [],
      sub_queries: []
    };
  }

  _getDefaultQueryPathForm() {
    return {
      name: '',
      source_meta_type_id: '',
      target_meta_type_id: '',
      cypher_path: '',
      description: ''
    };
  }

  _loadMockData() {
    // Mock meta types
    this.metaTypes = [
      { id: 'customer', name: 'Customer', description: 'Customer records' },
      { id: 'product', name: 'Product', description: 'Product catalog' },
      { id: 'order', name: 'Order', description: 'Customer orders' },
      { id: 'ticket', name: 'Ticket', description: 'Support tickets' },
      { id: 'category', name: 'Category', description: 'Product categories' },
      { id: 'priority', name: 'Priority', description: 'Priority levels' },
      { id: 'status', name: 'Status', description: 'Status values' }
    ];
    
    // Mock query paths
    this.queryPaths = [
      {
        id: 'qp-1',
        name: 'Customer to Orders',
        source_meta_type_id: 'customer',
        target_meta_type_id: 'order',
        cypher_path: '(s:Customer)-[:HAS_ORDER]->(t:Order)',
        description: 'Path from customer to their orders',
        created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 15 * 86400000).toISOString()
      },
      {
        id: 'qp-2',
        name: 'Product to Category',
        source_meta_type_id: 'product',
        target_meta_type_id: 'category',
        cypher_path: '(s:Product)-[:BELONGS_TO]->(t:Category)',
        description: 'Path from product to its category',
        created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 12 * 86400000).toISOString()
      },
      {
        id: 'qp-3',
        name: 'Order to Status',
        source_meta_type_id: 'order',
        target_meta_type_id: 'status',
        cypher_path: '(s:Order)-[:HAS_STATUS]->(t:Status)',
        description: 'Path from order to its status',
        created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString()
      },
      {
        id: 'qp-4',
        name: 'Ticket to Priority',
        source_meta_type_id: 'ticket',
        target_meta_type_id: 'priority',
        cypher_path: '(s:Ticket)-[:HAS_PRIORITY]->(t:Priority)',
        description: 'Path from ticket to its priority level',
        created_at: new Date(Date.now() - 18 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 9 * 86400000).toISOString()
      }
    ];
    
    // Mock queries
    this.queries = [
      {
        id: 'q-1',
        name: 'High Priority Tickets',
        description: 'Find all tickets with high priority',
        query_meta_type_id: 'ticket',
        include_values: 'INCLUDE',
        match_values: 'AND',
        include_queries: 'INCLUDE',
        match_queries: 'AND',
        query_values: [
          {
            id: 'qv-1',
            query_path_id: 'qp-4',
            include: 'INCLUDE',
            lookup: 'equal',
            values: [
              { id: 'high-priority', name: 'High' }
            ]
          }
        ],
        sub_queries: [],
        created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 5 * 86400000).toISOString()
      },
      {
        id: 'q-2',
        name: 'Shipped Orders',
        description: 'Find all orders with shipped status',
        query_meta_type_id: 'order',
        include_values: 'INCLUDE',
        match_values: 'AND',
        include_queries: 'INCLUDE',
        match_queries: 'AND',
        query_values: [
          {
            id: 'qv-2',
            query_path_id: 'qp-3',
            include: 'INCLUDE',
            lookup: 'equal',
            values: [
              { id: 'shipped-status', name: 'Shipped' }
            ]
          }
        ],
        sub_queries: [],
        created_at: new Date(Date.now() - 12 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 4 * 86400000).toISOString()
      },
      {
        id: 'q-3',
        name: 'Electronics Products',
        description: 'Find all products in the electronics category',
        query_meta_type_id: 'product',
        include_values: 'INCLUDE',
        match_values: 'AND',
        include_queries: 'INCLUDE',
        match_queries: 'AND',
        query_values: [
          {
            id: 'qv-3',
            query_path_id: 'qp-2',
            include: 'INCLUDE',
            lookup: 'equal',
            values: [
              { id: 'electronics-category', name: 'Electronics' }
            ]
          }
        ],
        sub_queries: [],
        created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 3 * 86400000).toISOString()
      },
      {
        id: 'q-4',
        name: 'Premium Customers with Recent Orders',
        description: 'Find premium customers who have placed orders in the last 30 days',
        query_meta_type_id: 'customer',
        include_values: 'INCLUDE',
        match_values: 'AND',
        include_queries: 'INCLUDE',
        match_queries: 'AND',
        query_values: [
          {
            id: 'qv-4',
            query_path_id: 'qp-1',
            include: 'INCLUDE',
            lookup: 'range',
            values: [
              { id: 'date-30-days-ago', name: '30 days ago' },
              { id: 'date-today', name: 'Today' }
            ]
          }
        ],
        sub_queries: [
          {
            id: 'sq-1',
            name: 'Premium Customers',
            query_meta_type_id: 'customer',
            include_values: 'INCLUDE',
            match_values: 'AND',
            query_values: [
              {
                id: 'qv-5',
                query_path_id: 'customer-tier',
                include: 'INCLUDE',
                lookup: 'equal',
                values: [
                  { id: 'premium-tier', name: 'Premium' }
                ]
              }
            ]
          }
        ],
        created_at: new Date(Date.now() - 8 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 2 * 86400000).toISOString()
      }
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    // In a real implementation, this would fetch data from the API
  }

  handleTabChange(e) {
    this.activeTab = e.detail.value;
    // Reset selected item when changing tabs
    this.selectedItem = null;
  }

  selectQuery(query) {
    this.selectedItem = { ...query, itemType: 'query' };
  }
  
  selectQueryPath(queryPath) {
    this.selectedItem = { ...queryPath, itemType: 'query-path' };
  }
  
  closeDetail() {
    this.selectedItem = null;
  }

  handleQueryFilterChange(e) {
    this.queryFilter = e.target.value;
  }
  
  handleQueryPathFilterChange(e) {
    this.queryPathFilter = e.target.value;
  }
  
  handleMetaTypeChange(e) {
    this.selectedMetaTypeId = e.target.value;
    // In a real implementation, this would filter items applicable to this meta type
    this._filterByMetaType();
  }
  
  _filterByMetaType() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      if (this.selectedMetaTypeId) {
        // Filter queries
        if (this.activeTab === 'queries') {
          this.queries = this.queries.filter(query => 
            query.query_meta_type_id === this.selectedMetaTypeId
          );
        }
        // Filter query paths
        else if (this.activeTab === 'query-paths') {
          this.queryPaths = this.queryPaths.filter(path => 
            path.source_meta_type_id === this.selectedMetaTypeId || 
            path.target_meta_type_id === this.selectedMetaTypeId
          );
        }
      } else {
        // Reset to full list
        this._loadMockData();
      }
      
      this.loading = false;
    }, 500);
  }

  // Dialog management
  openCreateQueryDialog() {
    this.queryForm = this._getDefaultQueryForm();
    this.showCreateQueryDialog = true;
  }
  
  openEditQueryDialog(query) {
    this.queryForm = {
      id: query.id,
      name: query.name,
      description: query.description,
      query_meta_type_id: query.query_meta_type_id,
      include_values: query.include_values,
      match_values: query.match_values,
      include_queries: query.include_queries,
      match_queries: query.match_queries,
      query_values: [...(query.query_values || [])],
      sub_queries: [...(query.sub_queries || [])]
    };
    
    this.showEditQueryDialog = true;
  }
  
  openCreateQueryPathDialog() {
    this.queryPathForm = this._getDefaultQueryPathForm();
    this.showCreateQueryPathDialog = true;
  }
  
  openEditQueryPathDialog(queryPath) {
    this.queryPathForm = {
      id: queryPath.id,
      name: queryPath.name,
      source_meta_type_id: queryPath.source_meta_type_id,
      target_meta_type_id: queryPath.target_meta_type_id,
      cypher_path: queryPath.cypher_path,
      description: queryPath.description
    };
    
    this.showEditQueryPathDialog = true;
  }
  
  openDeleteDialog(item, type) {
    this.deleteDialogData = {
      type: type,
      id: item.id,
      name: item.name
    };
    
    this.showDeleteDialog = true;
  }
  
  openExecuteQueryDialog(query) {
    this.executeQueryForm = {
      queryId: query.id,
      limit: 100,
      offset: 0
    };
    
    this.queryResults = [];
    this.resultCount = 0;
    this.showExecuteQueryDialog = true;
  }
  
  closeDialogs() {
    this.showCreateQueryDialog = false;
    this.showEditQueryDialog = false;
    this.showCreateQueryPathDialog = false;
    this.showEditQueryPathDialog = false;
    this.showDeleteDialog = false;
    this.showExecuteQueryDialog = false;
  }

  // Form handlers
  handleQueryFormChange(e) {
    const field = e.target.name;
    let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    this.queryForm = {
      ...this.queryForm,
      [field]: value
    };
  }
  
  handleQueryPathFormChange(e) {
    const field = e.target.name;
    const value = e.target.value;
    
    this.queryPathForm = {
      ...this.queryPathForm,
      [field]: value
    };
  }
  
  handleExecuteQueryFormChange(e) {
    const field = e.target.name;
    const value = field === 'limit' || field === 'offset' ? parseInt(e.target.value, 10) : e.target.value;
    
    this.executeQueryForm = {
      ...this.executeQueryForm,
      [field]: value
    };
  }
  
  // Query value management
  addQueryValue() {
    const newQueryValue = {
      id: `qv-${Date.now()}`,
      query_path_id: '',
      include: 'INCLUDE',
      lookup: 'equal',
      values: []
    };
    
    this.queryForm = {
      ...this.queryForm,
      query_values: [...this.queryForm.query_values, newQueryValue]
    };
  }
  
  updateQueryValue(index, field, value) {
    const updatedValues = [...this.queryForm.query_values];
    updatedValues[index] = {
      ...updatedValues[index],
      [field]: value
    };
    
    this.queryForm = {
      ...this.queryForm,
      query_values: updatedValues
    };
  }
  
  removeQueryValue(index) {
    const updatedValues = [...this.queryForm.query_values];
    updatedValues.splice(index, 1);
    
    this.queryForm = {
      ...this.queryForm,
      query_values: updatedValues
    };
  }
  
  // Add existing query as a sub-query
  addSubQuery(queryId) {
    const subQuery = this.queries.find(q => q.id === queryId);
    
    if (subQuery) {
      // Avoid circular references
      if (subQuery.id === this.queryForm.id) {
        this._showNotification('Cannot add query as its own sub-query', 'error');
        return;
      }
      
      this.queryForm = {
        ...this.queryForm,
        sub_queries: [...this.queryForm.sub_queries, subQuery]
      };
    }
  }
  
  removeSubQuery(index) {
    const updatedSubQueries = [...this.queryForm.sub_queries];
    updatedSubQueries.splice(index, 1);
    
    this.queryForm = {
      ...this.queryForm,
      sub_queries: updatedSubQueries
    };
  }

  // CRUD operations
  createQuery() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const newQuery = {
          id: `q-${Date.now()}`,
          ...this.queryForm,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        this.queries = [...this.queries, newQuery];
        this.showCreateQueryDialog = false;
        this._showNotification('Query created successfully', 'success');
      } catch (err) {
        console.error('Error creating query:', err);
        this._showNotification('Failed to create query', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updateQuery() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const updatedQuery = {
          ...this.queryForm,
          updated_at: new Date().toISOString()
        };
        
        this.queries = this.queries.map(query => 
          query.id === updatedQuery.id ? updatedQuery : query
        );
        
        if (this.selectedItem && this.selectedItem.id === updatedQuery.id) {
          this.selectedItem = { ...updatedQuery, itemType: 'query' };
        }
        
        this.showEditQueryDialog = false;
        this._showNotification('Query updated successfully', 'success');
      } catch (err) {
        console.error('Error updating query:', err);
        this._showNotification('Failed to update query', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  createQueryPath() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const newQueryPath = {
          id: `qp-${Date.now()}`,
          ...this.queryPathForm,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        this.queryPaths = [...this.queryPaths, newQueryPath];
        this.showCreateQueryPathDialog = false;
        this._showNotification('Query path created successfully', 'success');
      } catch (err) {
        console.error('Error creating query path:', err);
        this._showNotification('Failed to create query path', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updateQueryPath() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const updatedQueryPath = {
          ...this.queryPathForm,
          updated_at: new Date().toISOString()
        };
        
        this.queryPaths = this.queryPaths.map(path => 
          path.id === updatedQueryPath.id ? updatedQueryPath : path
        );
        
        if (this.selectedItem && this.selectedItem.id === updatedQueryPath.id) {
          this.selectedItem = { ...updatedQueryPath, itemType: 'query-path' };
        }
        
        this.showEditQueryPathDialog = false;
        this._showNotification('Query path updated successfully', 'success');
      } catch (err) {
        console.error('Error updating query path:', err);
        this._showNotification('Failed to update query path', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  deleteItem() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        if (this.deleteDialogData.type === 'query') {
          this.queries = this.queries.filter(
            query => query.id !== this.deleteDialogData.id
          );
        } else {
          this.queryPaths = this.queryPaths.filter(
            path => path.id !== this.deleteDialogData.id
          );
        }
        
        // Clear selection if the deleted item was selected
        if (this.selectedItem && this.selectedItem.id === this.deleteDialogData.id) {
          this.selectedItem = null;
        }
        
        this.showDeleteDialog = false;
        this._showNotification(`${this.deleteDialogData.type === 'query' ? 'Query' : 'Query path'} deleted successfully`, 'success');
      } catch (err) {
        console.error('Error deleting item:', err);
        this._showNotification('Failed to delete item', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  // Execute query
  executeQuery() {
    // In a real implementation, this would be an API call
    this.isExecutingQuery = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Generate mock results based on the query meta type
        const query = this.queries.find(q => q.id === this.executeQueryForm.queryId);
        
        if (!query) {
          throw new Error('Query not found');
        }
        
        // Generate mock IDs based on the meta type
        const metaType = query.query_meta_type_id;
        const results = [];
        
        for (let i = 0; i < 20; i++) {
          results.push(`${metaType}-${Date.now()}-${i}`);
        }
        
        this.queryResults = results;
        this.resultCount = results.length;
        this._showNotification(`Query executed successfully. Found ${results.length} results.`, 'success');
      } catch (err) {
        console.error('Error executing query:', err);
        this._showNotification('Failed to execute query', 'error');
      } finally {
        this.isExecutingQuery = false;
      }
    }, 1000);
  }

  // Filtering
  filteredQueries() {
    if (!this.queryFilter) {
      return this.queries;
    }
    
    const filter = this.queryFilter.toLowerCase();
    return this.queries.filter(query => 
      query.name.toLowerCase().includes(filter) || 
      query.description.toLowerCase().includes(filter)
    );
  }
  
  filteredQueryPaths() {
    if (!this.queryPathFilter) {
      return this.queryPaths;
    }
    
    const filter = this.queryPathFilter.toLowerCase();
    return this.queryPaths.filter(path => 
      path.name.toLowerCase().includes(filter) || 
      path.description.toLowerCase().includes(filter) ||
      path.cypher_path.toLowerCase().includes(filter)
    );
  }
  
  // Helper methods
  formatRelativeTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
      return `${diffSec} second${diffSec !== 1 ? 's' : ''} ago`;
    } else if (diffMin < 60) {
      return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
      return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    } else if (diffDay < 30) {
      return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    } else {
      return new Date(dateString).toLocaleDateString();
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
  
  getMetaTypeName(id) {
    const metaType = this.metaTypes.find(mt => mt.id === id);
    return metaType ? metaType.name : id;
  }
  
  getQueryPathName(id) {
    const path = this.queryPaths.find(p => p.id === id);
    return path ? path.name : id;
  }
  
  // Render methods
  renderQueryDetail() {
    if (!this.selectedItem || this.selectedItem.itemType !== 'query') return html``;
    
    const item = this.selectedItem;
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div>
            <h2 class="detail-title">${item.name}</h2>
            <div class="detail-meta">
              <span>Created: ${this.formatRelativeTime(item.created_at)}</span>
              <span> • </span>
              <span>Updated: ${this.formatRelativeTime(item.updated_at)}</span>
            </div>
          </div>
          
          <div>
            <wa-button variant="outlined" @click=${() => this.openExecuteQueryDialog(item)}>
              <wa-icon slot="prefix" name="play_arrow"></wa-icon>
              Execute
            </wa-button>
            <wa-button variant="outlined" @click=${() => this.openEditQueryDialog(item)}>
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
            <wa-button variant="text" @click=${this.closeDetail}>
              <wa-icon name="close"></wa-icon>
            </wa-button>
          </div>
        </div>
        
        <div class="detail-content">
          <div class="detail-property">
            <div class="detail-label">Description</div>
            <div class="detail-value">${item.description}</div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Meta Type</div>
            <div class="detail-value">${this.getMetaTypeName(item.query_meta_type_id)}</div>
          </div>
          
          <div class="form-grid">
            <div class="detail-property">
              <div class="detail-label">Include Values</div>
              <div class="detail-value">${item.include_values}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Match Values</div>
              <div class="detail-value">${item.match_values}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Include Queries</div>
              <div class="detail-value">${item.include_queries}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Match Queries</div>
              <div class="detail-value">${item.match_queries}</div>
            </div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Query Values</div>
            ${item.query_values && item.query_values.length 
              ? html`
                <div class="query-value-list">
                  ${item.query_values.map(qv => html`
                    <div class="query-value-item">
                      <div class="query-value-header">
                        <div class="query-value-path">${this.getQueryPathName(qv.query_path_id)}</div>
                        <div class="query-value-include badge">${qv.include}</div>
                      </div>
                      <div class="query-value-details">
                        <div>Lookup: ${qv.lookup}</div>
                        <div class="query-value-values">
                          ${qv.values && qv.values.map(val => html`
                            <div class="query-chip">${val.name}</div>
                          `)}
                        </div>
                      </div>
                    </div>
                  `)}
                </div>
              `
              : html`<div class="detail-value">No query values defined</div>`
            }
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Sub Queries</div>
            ${item.sub_queries && item.sub_queries.length 
              ? html`
                <div class="query-value-list">
                  ${item.sub_queries.map(sq => html`
                    <div class="query-value-item">
                      <div class="query-value-header">
                        <div class="query-value-path">${sq.name}</div>
                      </div>
                      <div class="query-value-details">
                        <div>Meta Type: ${this.getMetaTypeName(sq.query_meta_type_id)}</div>
                        <div>Match: ${sq.match_values || 'AND'}</div>
                      </div>
                    </div>
                  `)}
                </div>
              `
              : html`<div class="detail-value">No sub-queries defined</div>`
            }
          </div>
          
          <div class="detail-actions">
            <wa-button @click=${() => this.openDeleteDialog(item, 'query')} color="error" variant="outlined">
              <wa-icon slot="prefix" name="delete"></wa-icon>
              Delete
            </wa-button>
            <wa-button @click=${() => this.openEditQueryDialog(item)} color="primary">
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
            <wa-button @click=${() => this.openExecuteQueryDialog(item)} color="primary">
              <wa-icon slot="prefix" name="play_arrow"></wa-icon>
              Execute
            </wa-button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderQueryPathDetail() {
    if (!this.selectedItem || this.selectedItem.itemType !== 'query-path') return html``;
    
    const item = this.selectedItem;
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div>
            <h2 class="detail-title">${item.name}</h2>
            <div class="detail-meta">
              <span>Created: ${this.formatRelativeTime(item.created_at)}</span>
              <span> • </span>
              <span>Updated: ${this.formatRelativeTime(item.updated_at)}</span>
            </div>
          </div>
          
          <div>
            <wa-button variant="outlined" @click=${() => this.openEditQueryPathDialog(item)}>
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
            <wa-button variant="text" @click=${this.closeDetail}>
              <wa-icon name="close"></wa-icon>
            </wa-button>
          </div>
        </div>
        
        <div class="detail-content">
          <div class="detail-property">
            <div class="detail-label">Description</div>
            <div class="detail-value">${item.description}</div>
          </div>
          
          <div class="form-grid">
            <div class="detail-property">
              <div class="detail-label">Source Meta Type</div>
              <div class="detail-value">${this.getMetaTypeName(item.source_meta_type_id)}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Target Meta Type</div>
              <div class="detail-value">${this.getMetaTypeName(item.target_meta_type_id)}</div>
            </div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Cypher Path</div>
            <div class="code-block">${item.cypher_path}</div>
          </div>
          
          <div class="detail-actions">
            <wa-button @click=${() => this.openDeleteDialog(item, 'query-path')} color="error" variant="outlined">
              <wa-icon slot="prefix" name="delete"></wa-icon>
              Delete
            </wa-button>
            <wa-button @click=${() => this.openEditQueryPathDialog(item)} color="primary">
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderQueriesTab() {
    const filtered = this.filteredQueries();
    
    return html`
      <div class="filter-bar">
        <wa-input 
          class="filter-input"
          placeholder="Filter queries"
          .value=${this.queryFilter}
          @input=${this.handleQueryFilterChange}>
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-select
          placeholder="Filter by meta type"
          .value=${this.selectedMetaTypeId}
          @change=${this.handleMetaTypeChange}>
          <wa-option value="">All meta types</wa-option>
          ${this.metaTypes.map(metaType => html`
            <wa-option value=${metaType.id}>${metaType.name}</wa-option>
          `)}
        </wa-select>
        
        <wa-button @click=${this.openCreateQueryDialog} color="primary">
          <wa-icon slot="prefix" name="add"></wa-icon>
          Create
        </wa-button>
      </div>
      
      ${filtered.length > 0 ? html`
        <div class="grid">
          ${filtered.map(query => html`
            <wa-card class="grid-item" @click=${() => this.selectQuery(query)}>
              <div style="padding: 16px;">
                <div class="item-header">
                  <h3 class="item-title">${query.name}</h3>
                  <div class="item-meta">
                    <wa-badge>${this.getMetaTypeName(query.query_meta_type_id)}</wa-badge>
                  </div>
                </div>
                
                <p class="item-description">${query.description}</p>
                
                <div>
                  ${query.query_values && query.query_values.length > 0 
                    ? html`<span class="badge">${query.query_values.length} Value${query.query_values.length !== 1 ? 's' : ''}</span>` 
                    : ''}
                  ${query.sub_queries && query.sub_queries.length > 0 
                    ? html`<span class="badge">${query.sub_queries.length} Sub-quer${query.sub_queries.length !== 1 ? 'ies' : 'y'}</span>` 
                    : ''}
                </div>
                
                <div style="margin-top: 8px; font-size: 12px; color: var(--wa-text-secondary-color);">
                  Updated ${this.formatRelativeTime(query.updated_at)}
                </div>
              </div>
            </wa-card>
          `)}
        </div>
      ` : html`
        <div class="empty-state">
          <wa-icon name="search"></wa-icon>
          <h3>No queries found</h3>
          <p>Create a new query to get started</p>
          <wa-button @click=${this.openCreateQueryDialog} color="primary" style="margin-top: 16px;">
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Query
          </wa-button>
        </div>
      `}
      
      ${this.renderQueryDetail()}
    `;
  }
  
  renderQueryPathsTab() {
    const filtered = this.filteredQueryPaths();
    
    return html`
      <div class="filter-bar">
        <wa-input
          class="filter-input"
          placeholder="Filter query paths"
          .value=${this.queryPathFilter}
          @input=${this.handleQueryPathFilterChange}>
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-select
          placeholder="Filter by meta type"
          .value=${this.selectedMetaTypeId}
          @change=${this.handleMetaTypeChange}>
          <wa-option value="">All meta types</wa-option>
          ${this.metaTypes.map(metaType => html`
            <wa-option value=${metaType.id}>${metaType.name}</wa-option>
          `)}
        </wa-select>
        
        <wa-button @click=${this.openCreateQueryPathDialog} color="primary">
          <wa-icon slot="prefix" name="add"></wa-icon>
          Create
        </wa-button>
      </div>
      
      ${filtered.length > 0 ? html`
        <div class="grid">
          ${filtered.map(path => html`
            <wa-card class="grid-item" @click=${() => this.selectQueryPath(path)}>
              <div style="padding: 16px;">
                <div class="item-header">
                  <h3 class="item-title">${path.name}</h3>
                </div>
                
                <p class="item-description">${path.description}</p>
                
                <div class="code-block" style="max-height: 80px;">${path.cypher_path}</div>
                
                <div>
                  <wa-badge>${this.getMetaTypeName(path.source_meta_type_id)}</wa-badge>
                  <wa-icon name="arrow_forward" style="margin: 0 4px;"></wa-icon>
                  <wa-badge>${this.getMetaTypeName(path.target_meta_type_id)}</wa-badge>
                </div>
                
                <div style="margin-top: 8px; font-size: 12px; color: var(--wa-text-secondary-color);">
                  Updated ${this.formatRelativeTime(path.updated_at)}
                </div>
              </div>
            </wa-card>
          `)}
        </div>
      ` : html`
        <div class="empty-state">
          <wa-icon name="share"></wa-icon>
          <h3>No query paths found</h3>
          <p>Create a new query path to get started</p>
          <wa-button @click=${this.openCreateQueryPathDialog} color="primary" style="margin-top: 16px;">
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Query Path
          </wa-button>
        </div>
      `}
      
      ${this.renderQueryPathDetail()}
    `;
  }
  
  renderCreateQueryDialog() {
    // Lookup options for query values
    const lookupOptions = [
      { value: 'equal', label: 'Equal' },
      { value: 'contains', label: 'Contains' },
      { value: 'startswith', label: 'Starts With' },
      { value: 'endswith', label: 'Ends With' },
      { value: 'pattern', label: 'Pattern' },
      { value: 'gt', label: 'Greater Than' },
      { value: 'gte', label: 'Greater Than or Equal' },
      { value: 'lt', label: 'Less Than' },
      { value: 'lte', label: 'Less Than or Equal' },
      { value: 'range', label: 'Range' },
      { value: 'in_values', label: 'In Values' },
      { value: 'not_in_values', label: 'Not In Values' }
    ];
    
    // Include/exclude options
    const includeOptions = [
      { value: 'INCLUDE', label: 'Include' },
      { value: 'EXCLUDE', label: 'Exclude' }
    ];
    
    // Match options
    const matchOptions = [
      { value: 'AND', label: 'Match All (AND)' },
      { value: 'OR', label: 'Match Any (OR)' }
    ];
    
    return html`
      <wa-dialog 
        ?open=${this.showCreateQueryDialog}
        @close=${this.closeDialogs}
        title="Create Query">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.queryForm.name}
              @input=${this.handleQueryFormChange}
              required>
            </wa-input>
            
            <wa-select
              label="Meta Type"
              name="query_meta_type_id"
              .value=${this.queryForm.query_meta_type_id}
              @change=${this.handleQueryFormChange}
              required>
              <wa-option value="">Select a meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description"
            name="description"
            .value=${this.queryForm.description}
            @input=${this.handleQueryFormChange}>
          </wa-textarea>
          
          <div class="match-settings">
            <div class="match-setting">
              <div class="match-title">Values Settings</div>
              <wa-select
                label="Values Match Type"
                name="match_values"
                .value=${this.queryForm.match_values}
                @change=${this.handleQueryFormChange}>
                ${matchOptions.map(option => html`
                  <wa-option value=${option.value}>${option.label}</wa-option>
                `)}
              </wa-select>
              
              <wa-select
                label="Values Include Type"
                name="include_values"
                .value=${this.queryForm.include_values}
                @change=${this.handleQueryFormChange}
                style="margin-top: 8px;">
                ${includeOptions.map(option => html`
                  <wa-option value=${option.value}>${option.label}</wa-option>
                `)}
              </wa-select>
            </div>
            
            <div class="match-setting">
              <div class="match-title">Queries Settings</div>
              <wa-select
                label="Queries Match Type"
                name="match_queries"
                .value=${this.queryForm.match_queries}
                @change=${this.handleQueryFormChange}>
                ${matchOptions.map(option => html`
                  <wa-option value=${option.value}>${option.label}</wa-option>
                `)}
              </wa-select>
              
              <wa-select
                label="Queries Include Type"
                name="include_queries"
                .value=${this.queryForm.include_queries}
                @change=${this.handleQueryFormChange}
                style="margin-top: 8px;">
                ${includeOptions.map(option => html`
                  <wa-option value=${option.value}>${option.label}</wa-option>
                `)}
              </wa-select>
            </div>
          </div>
          
          <wa-divider style="margin: 24px 0;"></wa-divider>
          
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">Query Values</h3>
            <wa-button @click=${this.addQueryValue} color="primary" variant="outlined">
              <wa-icon slot="prefix" name="add"></wa-icon>
              Add Value
            </wa-button>
          </div>
          
          ${this.queryForm.query_values && this.queryForm.query_values.length > 0 
            ? html`
              <div class="query-value-list">
                ${this.queryForm.query_values.map((qv, index) => html`
                  <div class="query-value-item">
                    <div class="query-value-header">
                      <wa-select
                        label="Query Path"
                        .value=${qv.query_path_id}
                        @change=${(e) => this.updateQueryValue(index, 'query_path_id', e.target.value)}
                        required>
                        <wa-option value="">Select a query path</wa-option>
                        ${this.queryPaths.map(path => html`
                          <wa-option value=${path.id}>${path.name}</wa-option>
                        `)}
                      </wa-select>
                      
                      <wa-button @click=${() => this.removeQueryValue(index)} variant="text" color="error">
                        <wa-icon name="delete"></wa-icon>
                      </wa-button>
                    </div>
                    
                    <div class="form-grid" style="margin-top: 8px;">
                      <wa-select
                        label="Include Type"
                        .value=${qv.include}
                        @change=${(e) => this.updateQueryValue(index, 'include', e.target.value)}>
                        ${includeOptions.map(option => html`
                          <wa-option value=${option.value}>${option.label}</wa-option>
                        `)}
                      </wa-select>
                      
                      <wa-select
                        label="Lookup Type"
                        .value=${qv.lookup}
                        @change=${(e) => this.updateQueryValue(index, 'lookup', e.target.value)}>
                        ${lookupOptions.map(option => html`
                          <wa-option value=${option.value}>${option.label}</wa-option>
                        `)}
                      </wa-select>
                    </div>
                    
                    <!-- In a real implementation, this would use a multi-select component to select values -->
                    <div style="margin-top: 8px;">
                      <wa-input
                        label="Values (comma separated IDs in a real implementation)"
                        placeholder="In a real implementation, this would be a value selector"
                        disabled>
                      </wa-input>
                    </div>
                  </div>
                `)}
              </div>
            `
            : html`
              <div style="padding: 16px; text-align: center; color: var(--wa-text-secondary-color);">
                No query values defined. Click "Add Value" to define query criteria.
              </div>
            `
          }
          
          <wa-divider style="margin: 24px 0;"></wa-divider>
          
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">Sub Queries</h3>
            <wa-select 
              placeholder="Add existing query"
              @change=${(e) => { this.addSubQuery(e.target.value); e.target.value = ''; }}
              style="width: 250px;">
              <wa-option value="">Select a query to add</wa-option>
              ${this.queries.filter(q => q.id !== this.queryForm.id).map(query => html`
                <wa-option value=${query.id}>${query.name}</wa-option>
              `)}
            </wa-select>
          </div>
          
          ${this.queryForm.sub_queries && this.queryForm.sub_queries.length > 0 
            ? html`
              <div class="query-value-list">
                ${this.queryForm.sub_queries.map((sq, index) => html`
                  <div class="query-value-item">
                    <div class="query-value-header">
                      <div class="query-value-path">${sq.name}</div>
                      <wa-button @click=${() => this.removeSubQuery(index)} variant="text" color="error">
                        <wa-icon name="delete"></wa-icon>
                      </wa-button>
                    </div>
                    <div class="query-value-details">
                      <div>Meta Type: ${this.getMetaTypeName(sq.query_meta_type_id)}</div>
                      <div>Match: ${sq.match_values || 'AND'}</div>
                    </div>
                  </div>
                `)}
              </div>
            `
            : html`
              <div style="padding: 16px; text-align: center; color: var(--wa-text-secondary-color);">
                No sub-queries defined. Select an existing query to add it as a sub-query.
              </div>
            `
          }
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createQuery} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditQueryDialog() {
    // Same as create dialog but with edit button
    // For brevity, I'm reusing the create dialog's content
    
    return html`
      <wa-dialog 
        ?open=${this.showEditQueryDialog}
        @close=${this.closeDialogs}
        title="Edit Query">
        
        <!-- Same content as createQueryDialog but with different submit button -->
        <div class="dialog-content">
          <!-- Reuse the create dialog content here -->
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.queryForm.name}
              @input=${this.handleQueryFormChange}
              required>
            </wa-input>
            
            <wa-select
              label="Meta Type"
              name="query_meta_type_id"
              .value=${this.queryForm.query_meta_type_id}
              @change=${this.handleQueryFormChange}
              required>
              <wa-option value="">Select a meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description"
            name="description"
            .value=${this.queryForm.description}
            @input=${this.handleQueryFormChange}>
          </wa-textarea>
          
          <!-- Reuse the rest of the create dialog content -->
          <!-- ... -->
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updateQuery} color="primary">
            Update
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderCreateQueryPathDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showCreateQueryPathDialog}
        @close=${this.closeDialogs}
        title="Create Query Path">
        
        <div class="dialog-content">
          <wa-input
            class="form-full-width"
            label="Name"
            name="name"
            .value=${this.queryPathForm.name}
            @input=${this.handleQueryPathFormChange}
            required>
          </wa-input>
          
          <div class="form-grid" style="margin-top: 16px;">
            <wa-select
              label="Source Meta Type"
              name="source_meta_type_id"
              .value=${this.queryPathForm.source_meta_type_id}
              @change=${this.handleQueryPathFormChange}
              required>
              <wa-option value="">Select source meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
            
            <wa-select
              label="Target Meta Type"
              name="target_meta_type_id"
              .value=${this.queryPathForm.target_meta_type_id}
              @change=${this.handleQueryPathFormChange}
              required>
              <wa-option value="">Select target meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description"
            name="description"
            style="margin-top: 16px;"
            .value=${this.queryPathForm.description}
            @input=${this.handleQueryPathFormChange}>
          </wa-textarea>
          
          <div style="margin-top: 16px;">
            <div style="font-weight: 500; margin-bottom: 8px;">Cypher Path</div>
            <wa-code-editor
              language="cypher"
              name="cypher_path"
              .value=${this.queryPathForm.cypher_path}
              @change=${this.handleQueryPathFormChange}
              style="min-height: 120px;">
            </wa-code-editor>
            <div style="margin-top: 4px; font-size: 12px; color: var(--wa-text-secondary-color);">
              Example: (s:Customer)-[:HAS_ORDER]->(t:Order)
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createQueryPath} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditQueryPathDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showEditQueryPathDialog}
        @close=${this.closeDialogs}
        title="Edit Query Path">
        
        <div class="dialog-content">
          <wa-input
            class="form-full-width"
            label="Name"
            name="name"
            .value=${this.queryPathForm.name}
            @input=${this.handleQueryPathFormChange}
            required>
          </wa-input>
          
          <div class="form-grid" style="margin-top: 16px;">
            <wa-select
              label="Source Meta Type"
              name="source_meta_type_id"
              .value=${this.queryPathForm.source_meta_type_id}
              @change=${this.handleQueryPathFormChange}
              required>
              <wa-option value="">Select source meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
            
            <wa-select
              label="Target Meta Type"
              name="target_meta_type_id"
              .value=${this.queryPathForm.target_meta_type_id}
              @change=${this.handleQueryPathFormChange}
              required>
              <wa-option value="">Select target meta type</wa-option>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description"
            name="description"
            style="margin-top: 16px;"
            .value=${this.queryPathForm.description}
            @input=${this.handleQueryPathFormChange}>
          </wa-textarea>
          
          <div style="margin-top: 16px;">
            <div style="font-weight: 500; margin-bottom: 8px;">Cypher Path</div>
            <wa-code-editor
              language="cypher"
              name="cypher_path"
              .value=${this.queryPathForm.cypher_path}
              @change=${this.handleQueryPathFormChange}
              style="min-height: 120px;">
            </wa-code-editor>
            <div style="margin-top: 4px; font-size: 12px; color: var(--wa-text-secondary-color);">
              Example: (s:Customer)-[:HAS_ORDER]->(t:Order)
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updateQueryPath} color="primary">
            Update
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderDeleteDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showDeleteDialog}
        @close=${this.closeDialogs}
        title="Confirm Deletion">
        
        <div class="dialog-content">
          <p>Are you sure you want to delete the ${this.deleteDialogData.type} "${this.deleteDialogData.name}"?</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.deleteItem} color="error">
            Delete
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderExecuteQueryDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showExecuteQueryDialog}
        @close=${this.closeDialogs}
        title="Execute Query">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Limit"
              name="limit"
              type="number"
              min="1"
              max="1000"
              .value=${this.executeQueryForm.limit}
              @input=${this.handleExecuteQueryFormChange}>
            </wa-input>
            
            <wa-input
              label="Offset"
              name="offset"
              type="number"
              min="0"
              .value=${this.executeQueryForm.offset}
              @input=${this.handleExecuteQueryFormChange}>
            </wa-input>
          </div>
          
          ${this.queryResults.length > 0 ? html`
            <div class="results-panel">
              <div class="results-header">
                <h3 class="results-title">Results</h3>
                <div class="results-count">${this.resultCount} matching record${this.resultCount !== 1 ? 's' : ''}</div>
              </div>
              
              <div class="results-grid">
                ${this.queryResults.map(result => html`
                  <div class="result-item">${result}</div>
                `)}
              </div>
            </div>
          ` : ''}
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button 
            @click=${this.executeQuery} 
            color="primary"
            ?disabled=${this.isExecutingQuery}>
            ${this.isExecutingQuery 
              ? html`<wa-spinner size="small" style="margin-right: 8px;"></wa-spinner> Executing...` 
              : html`<wa-icon slot="prefix" name="play_arrow"></wa-icon> Execute`}
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }

  render() {
    return html`
      <div class="container">
        <div class="header">
          <h1 class="title">Queries Manager</h1>
          <p class="subtitle">Manage queries and query paths for filtering and retrieval</p>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="queries">Queries</wa-tab>
          <wa-tab value="query-paths">Query Paths</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="queries" ?active=${this.activeTab === 'queries'}>
          ${this.renderQueriesTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="query-paths" ?active=${this.activeTab === 'query-paths'}>
          ${this.renderQueryPathsTab()}
        </wa-tab-panel>
        
        ${this.renderCreateQueryDialog()}
        ${this.renderEditQueryDialog()}
        ${this.renderCreateQueryPathDialog()}
        ${this.renderEditQueryPathDialog()}
        ${this.renderDeleteDialog()}
        ${this.renderExecuteQueryDialog()}
        
        ${this.loading ? html`
          <div style="position: fixed; top: 16px; right: 16px; z-index: 1000;">
            <wa-spinner size="small"></wa-spinner>
            <span style="margin-left: 8px;">Loading...</span>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('wa-queries-manager', WebAwesomeQueriesManager);