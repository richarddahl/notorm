import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-semantic-search
 * @description Component for performing semantic vector searches using pgvector in the UNO framework
 * 
 * This component is also registered with alias names for URL compatibility:
 * - okui-semantic-search
 * - okui-vector-search-dashboard
 */
export class WebAwesomeSemanticSearch extends LitElement {
  static get properties() {
    return {
      query: { type: String },
      searchType: { type: String },
      entityType: { type: String },
      similarityThreshold: { type: Number },
      availableEntityTypes: { type: Array },
      includeMetadata: { type: Boolean },
      maxResults: { type: Number },
      searchResults: { type: Array },
      recentSearches: { type: Array },
      loading: { type: Boolean },
      error: { type: String },
      activeTab: { type: String },
      selectedItem: { type: Object },
      vectorStats: { type: Object },
      hybridSearch: { type: Boolean },
      keywordQuery: { type: String }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --search-bg: var(--wa-background-color, #f5f5f5);
        --search-padding: 20px;
      }
      .search-container {
        padding: var(--search-padding);
        background-color: var(--search-bg);
        min-height: 600px;
      }
      .search-header {
        margin-bottom: 24px;
      }
      .search-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .search-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .search-form {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 24px;
        margin-bottom: 24px;
      }
      .search-controls {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 16px;
        margin-bottom: 24px;
      }
      .search-button {
        margin-top: 16px;
      }
      .results-container {
        margin-top: 24px;
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
      .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
      }
      .result-card {
        height: 100%;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .result-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--wa-shadow-3, 0 3px 5px rgba(0,0,0,0.2));
      }
      .result-content {
        padding: 16px;
      }
      .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .result-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .result-similarity {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .result-description {
        color: var(--wa-text-secondary-color, #757575);
        margin: 0 0 16px 0;
        font-size: 14px;
      }
      .history-card {
        margin-bottom: 24px;
      }
      .history-item {
        padding: 12px 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
        cursor: pointer;
      }
      .history-item:hover {
        background-color: var(--wa-hover-color, #f5f5f5);
      }
      .history-query {
        font-weight: 500;
      }
      .history-meta {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
        margin-top: 4px;
        display: flex;
        justify-content: space-between;
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
      }
      .detail-content {
        padding: 16px;
      }
      .detail-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
      }
      .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      .stat-card {
        padding: 16px;
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        text-align: center;
      }
      .stat-value {
        font-size: 24px;
        font-weight: 500;
        color: var(--wa-primary-color, #3f51b5);
        margin-bottom: 4px;
      }
      .stat-label {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .vector-badge {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 8px;
      }
      .advanced-options {
        padding: 16px;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: var(--wa-border-radius, 4px);
        margin-top: 16px;
      }
      .option-title {
        font-weight: 500;
        margin-bottom: 8px;
      }
    `;
  }
  constructor() {
    super();
    console.log('wa-semantic-search constructor called');
    
    this.query = '';
    this.searchType = 'semantic';
    this.entityType = 'all';
    this.similarityThreshold = 0.5;
    this.availableEntityTypes = [];
    this.includeMetadata = true;
    this.maxResults = 20;
    this.searchResults = [];
    this.recentSearches = [];
    this.loading = false;
    this.error = null;
    this.activeTab = 'search';
    this.selectedItem = null;
    this.vectorStats = {};
    this.hybridSearch = false;
    this.keywordQuery = '';
    
    // Mock data for demo
    this._loadMockData();
  }
  _loadMockData() {
    this.availableEntityTypes = [
      { value: 'all', label: 'All Entities' },
      { value: 'product', label: 'Products' },
      { value: 'customer', label: 'Customers' },
      { value: 'document', label: 'Documents' },
      { value: 'support_ticket', label: 'Support Tickets' }
    ];
    
    this.recentSearches = [
      {
        id: 1,
        query: 'customers who purchased premium products',
        type: 'semantic',
        entityType: 'customer',
        timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
        resultCount: 12
      },
      {
        id: 2,
        query: 'technical specifications for smart devices',
        type: 'semantic',
        entityType: 'product',
        timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
        resultCount: 8
      },
      {
        id: 3,
        query: 'support tickets about login issues',
        type: 'semantic',
        entityType: 'support_ticket',
        timestamp: new Date(Date.now() - 1 * 86400000).toISOString(),
        resultCount: 15
      }
    ];
    
    this.vectorStats = {
      totalVectors: 124567,
      totalEntities: 4,
      avgVectorsPerEntity: 31141,
      dimensions: 384,
      latestUpdate: new Date(Date.now() - 35 * 60000).toISOString(),
      indexSize: '1.2 GB',
      entityStats: {
        product: {
          count: 45678,
          size: '420 MB',
          lastUpdate: new Date(Date.now() - 35 * 60000).toISOString()
        },
        customer: {
          count: 23456,
          size: '210 MB',
          lastUpdate: new Date(Date.now() - 2 * 86400000).toISOString()
        },
        document: {
          count: 12345,
          size: '350 MB',
          lastUpdate: new Date(Date.now() - 1 * 86400000).toISOString()
        },
        support_ticket: {
          count: 43088,
          size: '240 MB',
          lastUpdate: new Date(Date.now() - 12 * 3600000).toISOString()
        }
      }
    };
  }
  connectedCallback() {
    super.connectedCallback();
    console.log('wa-semantic-search connected to DOM');
    // In a real app, you might fetch additional data from the server
    
    // Force UI update after connection
    this.requestUpdate();
    
    // Dispatch a custom event to notify the app that we're ready
    this.dispatchEvent(new CustomEvent('component-ready', {
      bubbles: true,
      composed: true,
      detail: { component: 'wa-semantic-search' }
    }));
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    console.log('wa-semantic-search disconnected from DOM');
  }
  
  firstUpdated(changedProperties) {
    super.firstUpdated(changedProperties);
    console.log('wa-semantic-search first updated, shadow DOM initialized');
  }
  
  updated(changedProperties) {
    super.updated(changedProperties);
    if (changedProperties.size > 0) {
      console.log('wa-semantic-search properties updated:', 
        [...changedProperties.keys()].map(key => key.toString()).join(', '));
    }
  }
  handleQueryChange(e) {
    this.query = e.target.value;
  }
  handleKeywordQueryChange(e) {
    this.keywordQuery = e.target.value;
  }
  handleEntityTypeChange(e) {
    this.entityType = e.target.value;
  }
  handleSearchTypeChange(e) {
    this.searchType = e.target.value;
  }
  handleSimilarityThresholdChange(e) {
    this.similarityThreshold = parseFloat(e.target.value);
  }
  handleMaxResultsChange(e) {
    this.maxResults = parseInt(e.target.value, 10);
  }
  handleHybridSearchChange(e) {
    this.hybridSearch = e.target.checked;
  }
  handleIncludeMetadataChange(e) {
    this.includeMetadata = e.target.checked;
  }
  handleTabChange(e) {
    this.activeTab = e.detail.value;
  }
  selectItem(item) {
    this.selectedItem = item;
  }
  closeDetail() {
    this.selectedItem = null;
  }
  executeSearch() {
    if (!this.query) {
      this._showNotification('Please enter a search query', 'warning');
      return;
    }
    
    this.loading = true;
    this.error = null;
    this.searchResults = [];
    
    // In a real app, this would be an API call
    // Simulate API delay
    setTimeout(() => {
      try {
        // Mock search results based on the query and entity type
        const results = this._generateMockResults();
        
        // Update search results
        this.searchResults = results;
        
        // Add to recent searches
        const newSearch = {
          id: Date.now(),
          query: this.query,
          type: this.searchType,
          entityType: this.entityType,
          timestamp: new Date().toISOString(),
          resultCount: results.length
        };
        this.recentSearches = [newSearch, ...this.recentSearches].slice(0, 10);
        
        this.loading = false;
      } catch (err) {
        console.error('Error during search:', err);
        this.error = `Failed to execute search: ${err.message}`;
        this.loading = false;
      }
    }, 1500);
  }
  _generateMockResults() {
    // Generate different mock results based on the entity type and search type
    let results = [];
    
    const generateProduct = (i, similarity) => ({
      id: `product-${i}`,
      type: 'product',
      title: `Product ${i}`,
      description: `This is a mock product result with similarity score of ${similarity.toFixed(2)}. It matches your query for "${this.query}".`,
      similarity,
      metadata: {
        price: Math.floor(Math.random() * 1000) + 10,
        category: ['Electronics', 'Office', 'Home', 'Outdoor'][Math.floor(Math.random() * 4)],
        inStock: Math.random() > 0.3,
        sku: `SKU-${Math.floor(Math.random() * 10000)}`
      },
      embeddings: {
        dimensions: 384,
        model: 'text-embedding-ada-002'
      }
    });
    
    const generateCustomer = (i, similarity) => ({
      id: `customer-${i}`,
      type: 'customer',
      title: `Customer ${i}`,
      description: `This is a mock customer result with similarity score of ${similarity.toFixed(2)}. It matches your query for "${this.query}".`,
      similarity,
      metadata: {
        email: `customer${i}@example.com`,
        location: ['New York', 'Los Angeles', 'Chicago', 'Houston'][Math.floor(Math.random() * 4)],
        joinDate: new Date(Date.now() - Math.floor(Math.random() * 730) * 86400000).toISOString().split('T')[0],
        tier: ['Bronze', 'Silver', 'Gold', 'Platinum'][Math.floor(Math.random() * 4)]
      },
      embeddings: {
        dimensions: 384,
        model: 'text-embedding-ada-002'
      }
    });
    
    const generateDocument = (i, similarity) => ({
      id: `document-${i}`,
      type: 'document',
      title: `Document ${i}`,
      description: `This is a mock document result with similarity score of ${similarity.toFixed(2)}. It matches your query for "${this.query}".`,
      similarity,
      metadata: {
        author: `Author ${i}`,
        created: new Date(Date.now() - Math.floor(Math.random() * 365) * 86400000).toISOString().split('T')[0],
        fileType: ['PDF', 'DOCX', 'TXT', 'MD'][Math.floor(Math.random() * 4)],
        pageCount: Math.floor(Math.random() * 100) + 1
      },
      embeddings: {
        dimensions: 384,
        model: 'text-embedding-ada-002'
      }
    });
    
    const generateSupportTicket = (i, similarity) => ({
      id: `ticket-${i}`,
      type: 'support_ticket',
      title: `Support Ticket ${i}`,
      description: `This is a mock support ticket result with similarity score of ${similarity.toFixed(2)}. It matches your query for "${this.query}".`,
      similarity,
      metadata: {
        status: ['Open', 'In Progress', 'Resolved', 'Closed'][Math.floor(Math.random() * 4)],
        priority: ['Low', 'Medium', 'High', 'Critical'][Math.floor(Math.random() * 4)],
        created: new Date(Date.now() - Math.floor(Math.random() * 30) * 86400000).toISOString().split('T')[0],
        assignee: `Agent ${Math.floor(Math.random() * 10) + 1}`
      },
      embeddings: {
        dimensions: 384,
        model: 'text-embedding-ada-002'
      }
    });
    
    // Number of results to generate
    const numResults = Math.floor(Math.random() * 15) + 5;
    
    // Generate different types of results based on the entity type
    if (this.entityType === 'all') {
      // Mix of all entity types
      for (let i = 1; i <= numResults; i++) {
        const similarity = Math.random() * (1 - this.similarityThreshold) + this.similarityThreshold;
        const entityType = Math.floor(Math.random() * 4); // 0-3
        
        switch (entityType) {
          case 0:
            results.push(generateProduct(i, similarity));
            break;
          case 1:
            results.push(generateCustomer(i, similarity));
            break;
          case 2:
            results.push(generateDocument(i, similarity));
            break;
          case 3:
            results.push(generateSupportTicket(i, similarity));
            break;
        }
      }
    } else if (this.entityType === 'product') {
      // Only products
      for (let i = 1; i <= numResults; i++) {
        const similarity = Math.random() * (1 - this.similarityThreshold) + this.similarityThreshold;
        results.push(generateProduct(i, similarity));
      }
    } else if (this.entityType === 'customer') {
      // Only customers
      for (let i = 1; i <= numResults; i++) {
        const similarity = Math.random() * (1 - this.similarityThreshold) + this.similarityThreshold;
        results.push(generateCustomer(i, similarity));
      }
    } else if (this.entityType === 'document') {
      // Only documents
      for (let i = 1; i <= numResults; i++) {
        const similarity = Math.random() * (1 - this.similarityThreshold) + this.similarityThreshold;
        results.push(generateDocument(i, similarity));
      }
    } else if (this.entityType === 'support_ticket') {
      // Only support tickets
      for (let i = 1; i <= numResults; i++) {
        const similarity = Math.random() * (1 - this.similarityThreshold) + this.similarityThreshold;
        results.push(generateSupportTicket(i, similarity));
      }
    }
    
    // Sort by similarity score (highest first)
    results.sort((a, b) => b.similarity - a.similarity);
    
    // Limit to max results
    results = results.slice(0, this.maxResults);
    
    return results;
  }
  executeHistorySearch(search) {
    this.query = search.query;
    this.entityType = search.entityType;
    this.searchType = search.type;
    
    this.executeSearch();
  }
  buildIndexForEntity(entityType) {
    this.loading = true;
    
    // Simulate API delay
    setTimeout(() => {
      // Update the last update time for the entity
      const updatedStats = {...this.vectorStats};
      if (updatedStats.entityStats[entityType]) {
        updatedStats.entityStats[entityType].lastUpdate = new Date().toISOString();
      }
      updatedStats.latestUpdate = new Date().toISOString();
      
      this.vectorStats = updatedStats;
      this.loading = false;
      
      this._showNotification(`Vector index for ${entityType} rebuilt successfully`, 'success');
    }, 2000);
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
  getEntityTypeLabel(value) {
    const entity = this.availableEntityTypes.find(e => e.value === value);
    return entity ? entity.label : value;
  }
  renderResultDetail() {
    if (!this.selectedItem) return html``;
    
    const item = this.selectedItem;
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 class="detail-title">${item.title}</h2>
            
            <wa-button variant="text" @click=${this.closeDetail}>
              <wa-icon name="close"></wa-icon>
            </wa-button>
          </div>
          
          <div style="margin-top: 8px;">
            <wa-chip>${this.getEntityTypeLabel(item.type)}</wa-chip>
            <span style="margin-left: 8px; color: var(--wa-text-secondary-color);">
              Similarity Score: ${(item.similarity * 100).toFixed(1)}%
            </span>
          </div>
        </div>
        
        <div class="detail-content">
          <wa-tabs>
            <wa-tab value="overview">Overview</wa-tab>
            <wa-tab value="metadata">Metadata</wa-tab>
            <wa-tab value="vector">Vector Details</wa-tab>
          </wa-tabs>
          
          <wa-tab-panel value="overview" active>
            <div style="margin-top: 16px;">
              <h3 style="margin-top: 0; margin-bottom: 16px;">Description</h3>
              <p>${item.description}</p>
              
              <h3 style="margin-top: 24px; margin-bottom: 16px;">Summary</h3>
              <div class="detail-grid">
                <div>
                  <strong>ID:</strong> ${item.id}
                </div>
                <div>
                  <strong>Type:</strong> ${this.getEntityTypeLabel(item.type)}
                </div>
                <div>
                  <strong>Similarity:</strong> ${(item.similarity * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </wa-tab-panel>
          
          <wa-tab-panel value="metadata">
            <div style="margin-top: 16px;">
              <h3 style="margin-top: 0; margin-bottom: 16px;">Metadata</h3>
              
              ${item.metadata ? html`
                <table style="width: 100%; border-collapse: collapse;">
                  <thead>
                    <tr>
                      <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Key</th>
                      <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${Object.entries(item.metadata).map(([key, value]) => html`
                      <tr>
                        <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">${key}</td>
                        <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                          ${typeof value === 'object' ? JSON.stringify(value) : value.toString()}
                        </td>
                      </tr>
                    `)}
                  </tbody>
                </table>
              ` : html`
                <p>No metadata available for this item.</p>
              `}
            </div>
          </wa-tab-panel>
          
          <wa-tab-panel value="vector">
            <div style="margin-top: 16px;">
              <h3 style="margin-top: 0; margin-bottom: 16px;">Vector Information</h3>
              
              <div class="detail-grid">
                <div>
                  <strong>Dimensions:</strong> ${item.embeddings?.dimensions || 'Unknown'}
                </div>
                <div>
                  <strong>Model:</strong> ${item.embeddings?.model || 'Unknown'}
                </div>
                <div>
                  <strong>Distance Metric:</strong> Cosine Similarity
                </div>
              </div>
              
              <h3 style="margin-top: 24px; margin-bottom: 16px;">Actions</h3>
              
              <div style="display: flex; gap: 16px;">
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="refresh"></wa-icon>
                  Recalculate Vector
                </wa-button>
                
                <wa-button variant="outlined">
                  <wa-icon slot="prefix" name="find_replace"></wa-icon>
                  Find Similar
                </wa-button>
              </div>
            </div>
          </wa-tab-panel>
        </div>
      </div>
    `;
  }
  renderSearchTab() {
    return html`
      <div class="search-form">
        <div style="display: flex; gap: 16px; align-items: flex-start;">
          <wa-input 
            label="Search Query"
            placeholder="Enter your natural language query"
            .value=${this.query}
            @input=${this.handleQueryChange}
            style="flex: 1;">
          </wa-input>
          
          <wa-button 
            @click=${this.executeSearch}
            class="search-button">
            <wa-icon slot="prefix" name="search"></wa-icon>
            Search
          </wa-button>
        </div>
        
        <div class="search-controls">
          <wa-select 
            label="Entity Type"
            .value=${this.entityType}
            @change=${this.handleEntityTypeChange}>
            ${this.availableEntityTypes.map(entity => html`
              <wa-option value="${entity.value}">${entity.label}</wa-option>
            `)}
          </wa-select>
          
          <wa-select 
            label="Search Type"
            .value=${this.searchType}
            @change=${this.handleSearchTypeChange}>
            <wa-option value="semantic">Semantic Search</wa-option>
            <wa-option value="hybrid">Hybrid Search</wa-option>
          </wa-select>
          
          <wa-select 
            label="Max Results"
            .value=${this.maxResults.toString()}
            @change=${this.handleMaxResultsChange}>
            <wa-option value="10">10</wa-option>
            <wa-option value="20">20</wa-option>
            <wa-option value="50">50</wa-option>
            <wa-option value="100">100</wa-option>
          </wa-select>
        </div>
        
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
          <wa-button variant="text" size="small" style="margin-left: auto;">
            <wa-icon slot="prefix" name="tune"></wa-icon>
            Advanced Options
          </wa-button>
        </div>
        
        <div class="advanced-options">
          <div class="option-title">Advanced Search Options</div>
          
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 16px;">
            <div>
              <div style="margin-bottom: 8px;">Similarity Threshold</div>
              <wa-slider 
                min="0.1" 
                max="0.9" 
                step="0.05" 
                .value=${this.similarityThreshold}
                @change=${this.handleSimilarityThresholdChange}>
                ${this.similarityThreshold.toFixed(2)}
              </wa-slider>
              <div style="display: flex; justify-content: space-between; font-size: 12px;">
                <span>Low (0.1)</span>
                <span>Medium (0.5)</span>
                <span>High (0.9)</span>
              </div>
            </div>
            
            <div>
              <div style="margin-bottom: 16px;">
                <wa-switch 
                  .checked=${this.includeMetadata}
                  @change=${this.handleIncludeMetadataChange}>
                  Include Metadata
                </wa-switch>
              </div>
              
              <div>
                <wa-switch 
                  .checked=${this.hybridSearch}
                  @change=${this.handleHybridSearchChange}>
                  Hybrid Search
                </wa-switch>
              </div>
            </div>
            
            ${this.hybridSearch ? html`
              <div>
                <wa-input 
                  label="Keyword Query"
                  placeholder="Additional keywords to filter results"
                  .value=${this.keywordQuery}
                  @input=${this.handleKeywordQueryChange}>
                </wa-input>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
      
      ${this.searchResults.length > 0 ? html`
        <div class="results-container">
          <div class="results-header">
            <h2 class="results-title">
              ${this.searchResults.length} results for "${this.query}"
            </h2>
            
            <div>
              <wa-button variant="outlined" size="small">
                <wa-icon slot="prefix" name="filter_list"></wa-icon>
                Filter Results
              </wa-button>
            </div>
          </div>
          
          <div class="results-grid">
            ${this.searchResults.map(result => html`
              <wa-card 
                class="result-card" 
                elevation="1"
                @click=${() => this.selectItem(result)}>
                <div class="result-content">
                  <div class="result-header">
                    <h3 class="result-title">${result.title}</h3>
                    <div class="result-similarity">${(result.similarity * 100).toFixed(1)}%</div>
                  </div>
                  
                  <div style="margin-bottom: 8px;">
                    <span class="vector-badge">${this.getEntityTypeLabel(result.type)}</span>
                  </div>
                  
                  <p class="result-description">${result.description}</p>
                  
                  ${result.metadata && this.includeMetadata ? html`
                    <div style="font-size: 12px; color: var(--wa-text-secondary-color);">
                      ${Object.entries(result.metadata).slice(0, 2).map(([key, value]) => html`
                        <div><strong>${key}:</strong> ${typeof value === 'object' ? JSON.stringify(value) : value.toString()}</div>
                      `)}
                      ${Object.keys(result.metadata).length > 2 ? html`
                        <div>+ ${Object.keys(result.metadata).length - 2} more fields</div>
                      ` : ''}
                    </div>
                  ` : ''}
                </div>
              </wa-card>
            `)}
          </div>
        </div>
      ` : this.loading ? html`
        <div style="display: flex; justify-content: center; padding: 48px;">
          <wa-spinner size="large"></wa-spinner>
        </div>
      ` : this.query ? html`
        <div style="text-align: center; padding: 48px; background-color: var(--wa-surface-color); border-radius: var(--wa-border-radius);">
          <wa-icon name="search_off" style="font-size: 48px; margin-bottom: 16px; color: var(--wa-text-secondary-color);"></wa-icon>
          <h3>No results found</h3>
          <p>Try adjusting your search query or lowering the similarity threshold.</p>
        </div>
      ` : html`
        <wa-card class="history-card">
          <div style="padding: 16px;">
            <h3 style="margin-top: 0; margin-bottom: 16px;">Recent Searches</h3>
            
            ${this.recentSearches.length > 0 ? html`
              ${this.recentSearches.map(search => html`
                <div class="history-item" @click=${() => this.executeHistorySearch(search)}>
                  <div class="history-query">${search.query}</div>
                  <div class="history-meta">
                    <div>
                      <span>${this.getEntityTypeLabel(search.entityType)}</span>
                      <span style="margin-left: 8px;">${search.resultCount} results</span>
                    </div>
                    <div>${this.formatRelativeTime(search.timestamp)}</div>
                  </div>
                </div>
              `)}
            ` : html`
              <div style="text-align: center; padding: 24px; color: var(--wa-text-secondary-color);">
                No recent searches
              </div>
            `}
          </div>
        </wa-card>
      `}
      
      ${this.selectedItem ? this.renderResultDetail() : ''}
    `;
  }
  renderStatsTab() {
    return html`
      <div style="margin-top: 24px;">
        <div class="stats-grid">
          <wa-card>
            <div style="padding: 16px; text-align: center;">
              <div class="stat-value">${this.vectorStats.totalVectors.toLocaleString()}</div>
              <div class="stat-label">Total Vectors</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px; text-align: center;">
              <div class="stat-value">${this.vectorStats.totalEntities}</div>
              <div class="stat-label">Entity Types</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px; text-align: center;">
              <div class="stat-value">${this.vectorStats.dimensions}</div>
              <div class="stat-label">Vector Dimensions</div>
            </div>
          </wa-card>
          
          <wa-card>
            <div style="padding: 16px; text-align: center;">
              <div class="stat-value">${this.vectorStats.indexSize}</div>
              <div class="stat-label">Index Size</div>
            </div>
          </wa-card>
        </div>
        
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <h2 style="margin: 0;">Vector Index Status</h2>
              
              <div>
                <wa-button color="primary">
                  <wa-icon slot="prefix" name="refresh"></wa-icon>
                  Rebuild All Indexes
                </wa-button>
              </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr>
                  <th style="text-align: left; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Entity Type</th>
                  <th style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Vectors</th>
                  <th style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Size</th>
                  <th style="text-align: right; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Last Update</th>
                  <th style="text-align: center; padding: 8px; border-bottom: 1px solid var(--wa-border-color);">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${Object.entries(this.vectorStats.entityStats).map(([entityType, stats]) => html`
                  <tr>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color);">
                      ${this.getEntityTypeLabel(entityType)}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color); text-align: right;">
                      ${stats.count.toLocaleString()}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color); text-align: right;">
                      ${stats.size}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color); text-align: right;">
                      ${this.formatRelativeTime(stats.lastUpdate)}
                    </td>
                    <td style="padding: 8px; border-bottom: 1px solid var(--wa-border-color); text-align: center;">
                      <wa-button variant="text" @click=${() => this.buildIndexForEntity(entityType)}>
                        <wa-icon slot="prefix" name="refresh"></wa-icon>
                        Rebuild Index
                      </wa-button>
                    </td>
                  </tr>
                `)}
              </tbody>
            </table>
          </div>
        </wa-card>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Performance Metrics</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
              <div>
                <h3 style="margin-top: 0; margin-bottom: 16px;">Average Query Time</h3>
                <div style="font-size: 32px; font-weight: 500; color: var(--wa-primary-color); margin-bottom: 8px;">
                  125 ms
                </div>
                <p>Average time to complete a semantic search query.</p>
              </div>
              
              <div>
                <h3 style="margin-top: 0; margin-bottom: 16px;">Queries per Day</h3>
                <div style="font-size: 32px; font-weight: 500; color: var(--wa-primary-color); margin-bottom: 8px;">
                  1,245
                </div>
                <p>Number of vector search queries executed per day.</p>
              </div>
              
              <div>
                <h3 style="margin-top: 0; margin-bottom: 16px;">Cache Hit Rate</h3>
                <div style="font-size: 32px; font-weight: 500; color: var(--wa-primary-color); margin-bottom: 8px;">
                  78.5%
                </div>
                <p>Percentage of queries served from the cache.</p>
              </div>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }
  renderSettingsTab() {
    return html`
      <div style="margin-top: 24px;">
        <wa-card style="margin-bottom: 24px;">
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Model Configuration</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
              <div>
                <wa-select 
                  label="Embedding Model"
                  value="text-embedding-ada-002">
                  <wa-option value="text-embedding-ada-002">OpenAI Ada 002 (384d)</wa-option>
                  <wa-option value="text-embedding-3-small">OpenAI 3 Small (1536d)</wa-option>
                  <wa-option value="text-embedding-3-large">OpenAI 3 Large (3072d)</wa-option>
                  <wa-option value="sentence-transformers/all-mpnet-base-v2">MpNet Base v2 (768d)</wa-option>
                </wa-select>
                
                <div style="margin-top: 16px;">
                  <wa-select 
                    label="Distance Metric"
                    value="cosine">
                    <wa-option value="cosine">Cosine Similarity</wa-option>
                    <wa-option value="l2">Euclidean (L2)</wa-option>
                    <wa-option value="ip">Inner Product</wa-option>
                  </wa-select>
                </div>
              </div>
              
              <div>
                <div style="margin-bottom: 16px;">
                  <wa-switch checked>
                    Enable Vector Search Cache
                  </wa-switch>
                </div>
                
                <div style="margin-bottom: 16px;">
                  <wa-switch checked>
                    Auto-rebuild Indexes on Schema Change
                  </wa-switch>
                </div>
                
                <div>
                  <wa-switch>
                    Enable Query Logging
                  </wa-switch>
                </div>
              </div>
            </div>
            
            <div style="margin-top: 24px;">
              <h3 style="margin-top: 0; margin-bottom: 16px;">Optimization Settings</h3>
              
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                <div>
                  <div style="margin-bottom: 8px;">Query Result Limit</div>
                  <wa-slider 
                    min="10" 
                    max="1000" 
                    step="10" 
                    value="100">
                    100
                  </wa-slider>
                </div>
                
                <div>
                  <div style="margin-bottom: 8px;">Cache Expiration (minutes)</div>
                  <wa-slider 
                    min="1" 
                    max="60" 
                    step="1" 
                    value="15">
                    15
                  </wa-slider>
                </div>
              </div>
            </div>
            
            <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
              <wa-button color="primary">
                Save Settings
              </wa-button>
            </div>
          </div>
        </wa-card>
        
        <wa-card>
          <div style="padding: 16px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Hybrid Search Configuration</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
              <div>
                <wa-select 
                  label="Text Search Strategy"
                  value="tsvector">
                  <wa-option value="tsvector">PostgreSQL Full Text Search (tsvector)</wa-option>
                  <wa-option value="trigram">Trigram Similarity</wa-option>
                  <wa-option value="custom">Custom SQL Function</wa-option>
                </wa-select>
                
                <div style="margin-top: 16px;">
                  <wa-input 
                    label="Default Weight Vector (Semantic:Keyword)"
                    value="0.7:0.3">
                  </wa-input>
                </div>
              </div>
              
              <div>
                <div style="margin-bottom: 16px;">
                  <wa-switch checked>
                    Allow User-defined Weights
                  </wa-switch>
                </div>
                
                <div style="margin-bottom: 16px;">
                  <wa-switch checked>
                    Use Combined Ranking
                  </wa-switch>
                </div>
                
                <div>
                  <wa-switch checked>
                    Auto-detect Query Type
                  </wa-switch>
                </div>
              </div>
            </div>
            
            <div style="margin-top: 24px; display: flex; justify-content: flex-end;">
              <wa-button color="primary">
                Save Settings
              </wa-button>
            </div>
          </div>
        </wa-card>
      </div>
    `;
  }
  render() {
    // Add a guard to ensure we don't render before we're ready
    if (!this || !this.isConnected) {
      console.log('wa-semantic-search render called before component is ready');
      return html`
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh;">
          <div style="text-align: center;">
            <div style="font-size: 24px; margin-bottom: 16px;">Loading Vector Search Component...</div>
            <div style="border: 4px solid #f3f3f3; border-top: 4px solid #3f51b5; border-radius: 50%; width: 40px; height: 40px; animation: spin 2s linear infinite; margin: 0 auto;"></div>
            <style>
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            </style>
          </div>
        </div>
      `;
    }

    console.log('wa-semantic-search rendering component');
    return html`
      <div class="search-container">
        <div class="search-header">
          <h1 class="search-title">Vector Search</h1>
          <p class="search-subtitle">Semantic search using vector embeddings in PGVector</p>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="search">Search</wa-tab>
          <wa-tab value="stats">Vector Stats</wa-tab>
          <wa-tab value="settings">Settings</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="search" ?active=${this.activeTab === 'search'}>
          ${this.renderSearchTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="stats" ?active=${this.activeTab === 'stats'}>
          ${this.renderStatsTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="settings" ?active=${this.activeTab === 'settings'}>
          ${this.renderSettingsTab()}
        </wa-tab-panel>
        
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
// Define the custom element if not already registered
if (!customElements.get('wa-semantic-search')) {
  customElements.define('wa-semantic-search', WebAwesomeSemanticSearch);
  console.log('wa-semantic-search component registered');
} else {
  console.log('wa-semantic-search component already registered');
}