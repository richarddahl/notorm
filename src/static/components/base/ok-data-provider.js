import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element ok-data-provider
 * @description Generic data provider component for querying and managing entity data
 * @fires load-start - When data loading starts
 * @fires load-complete - When data loading completes
 * @fires load-error - When data loading fails
 * @fires data-changed - When data is created, updated, or deleted
 */
export class OkDataProvider extends LitElement {
  static get properties() {
    return {
      // API configuration
      baseUrl: { type: String },
      entityType: { type: String },
      
      // Query parameters
      filter: { type: Object },
      sort: { type: Object },
      pagination: { type: Object },
      
      // State
      data: { type: Array },
      totalCount: { type: Number },
      loading: { type: Boolean },
      error: { type: String },
      
      // Single entity mode
      entityId: { type: String },
      entity: { type: Object },
      
      // Cache settings
      cacheTime: { type: Number }, // milliseconds
    };
  }
  constructor() {
    super();
    this.baseUrl = '';
    this.entityType = '';
    this.filter = {};
    this.sort = { field: 'id', direction: 'asc' };
    this.pagination = { page: 1, pageSize: 20 };
    this.data = [];
    this.totalCount = 0;
    this.loading = false;
    this.error = null;
    this.entityId = null;
    this.entity = null;
    this.cacheTime = 30000; // 30 seconds
    
    this._cache = {};
    this._lastFetchTime = null;
  }
  /**
   * Fetch data based on current configuration
   * @returns {Promise<Object>} Promise resolving to the fetched data
   */
  async fetchData() {
    if (this.entityId) {
      return this.fetchEntity();
    } else {
      return this.fetchList();
    }
  }
  /**
   * Fetch a list of entities based on current filter, sort, and pagination
   * @returns {Promise<Array>} Promise resolving to list of entities
   */
  async fetchList() {
    this.loading = true;
    this.error = null;
    this.dispatchEvent(new CustomEvent('load-start'));
    
    // Check cache
    const cacheKey = this._generateCacheKey();
    const now = Date.now();
    if (this._cache[cacheKey] && 
        this._lastFetchTime && 
        (now - this._lastFetchTime) < this.cacheTime) {
      this.loading = false;
      this.data = this._cache[cacheKey].data;
      this.totalCount = this._cache[cacheKey].totalCount;
      this.dispatchEvent(new CustomEvent('load-complete', { 
        detail: { data: this.data, totalCount: this.totalCount } 
      }));
      return { data: this.data, totalCount: this.totalCount };
    }
    
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
      
      this.data = result.data || [];
      this.totalCount = result.meta?.total || this.data.length;
      
      // Update cache
      this._cache[cacheKey] = { 
        data: this.data, 
        totalCount: this.totalCount 
      };
      this._lastFetchTime = now;
      
      this.dispatchEvent(new CustomEvent('load-complete', { 
        detail: { data: this.data, totalCount: this.totalCount } 
      }));
      
      return { data: this.data, totalCount: this.totalCount };
    } catch (error) {
      console.error('Error fetching data:', error);
      this.error = error.message;
      this.dispatchEvent(new CustomEvent('load-error', { detail: { error } }));
      throw error;
    } finally {
      this.loading = false;
    }
  }
  /**
   * Fetch a single entity by ID
   * @returns {Promise<Object>} Promise resolving to single entity
   */
  async fetchEntity() {
    if (!this.entityId) {
      return null;
    }
    
    this.loading = true;
    this.error = null;
    this.dispatchEvent(new CustomEvent('load-start'));
    
    // Check cache
    const cacheKey = `${this.entityType}_${this.entityId}`;
    const now = Date.now();
    if (this._cache[cacheKey] && 
        this._lastFetchTime && 
        (now - this._lastFetchTime) < this.cacheTime) {
      this.loading = false;
      this.entity = this._cache[cacheKey];
      this.dispatchEvent(new CustomEvent('load-complete', { 
        detail: { entity: this.entity } 
      }));
      return this.entity;
    }
    
    try {
      const url = `${this.baseUrl}/${this.entityType}/${this.entityId}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      this.entity = result.data || result;
      
      // Update cache
      this._cache[cacheKey] = this.entity;
      this._lastFetchTime = now;
      
      this.dispatchEvent(new CustomEvent('load-complete', { 
        detail: { entity: this.entity } 
      }));
      
      return this.entity;
    } catch (error) {
      console.error('Error fetching entity:', error);
      this.error = error.message;
      this.dispatchEvent(new CustomEvent('load-error', { detail: { error } }));
      throw error;
    } finally {
      this.loading = false;
    }
  }
  /**
   * Create a new entity
   * @param {Object} entity - Entity data to create
   * @returns {Promise<Object>} Promise resolving to created entity
   */
  async createEntity(entity) {
    this.loading = true;
    this.error = null;
    
    try {
      const url = `${this.baseUrl}/${this.entityType}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(entity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      const createdEntity = result.data || result;
      
      // Clear cache
      this._cache = {};
      this._lastFetchTime = null;
      
      this.dispatchEvent(new CustomEvent('data-changed', { 
        detail: { 
          type: 'create', 
          entity: createdEntity 
        } 
      }));
      
      return createdEntity;
    } catch (error) {
      console.error('Error creating entity:', error);
      this.error = error.message;
      throw error;
    } finally {
      this.loading = false;
    }
  }
  /**
   * Update an existing entity
   * @param {string} id - Entity ID to update
   * @param {Object} entity - Updated entity data
   * @returns {Promise<Object>} Promise resolving to updated entity
   */
  async updateEntity(id, entity) {
    this.loading = true;
    this.error = null;
    
    try {
      const url = `${this.baseUrl}/${this.entityType}/${id}`;
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(entity)
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const result = await response.json();
      const updatedEntity = result.data || result;
      
      // Clear cache
      this._cache = {};
      this._lastFetchTime = null;
      
      this.dispatchEvent(new CustomEvent('data-changed', { 
        detail: { 
          type: 'update', 
          entity: updatedEntity 
        } 
      }));
      
      return updatedEntity;
    } catch (error) {
      console.error('Error updating entity:', error);
      this.error = error.message;
      throw error;
    } finally {
      this.loading = false;
    }
  }
  /**
   * Delete an entity
   * @param {string} id - Entity ID to delete
   * @returns {Promise<void>} Promise resolving when entity is deleted
   */
  async deleteEntity(id) {
    this.loading = true;
    this.error = null;
    
    try {
      const url = `${this.baseUrl}/${this.entityType}/${id}`;
      const response = await fetch(url, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      // Clear cache
      this._cache = {};
      this._lastFetchTime = null;
      
      this.dispatchEvent(new CustomEvent('data-changed', { 
        detail: { 
          type: 'delete', 
          entityId: id 
        } 
      }));
    } catch (error) {
      console.error('Error deleting entity:', error);
      this.error = error.message;
      throw error;
    } finally {
      this.loading = false;
    }
  }
  /**
   * Set filter criteria and refresh data
   * @param {Object} filter - Filter criteria
   * @returns {Promise<Object>} Promise resolving to fetched data
   */
  async setFilter(filter) {
    this.filter = filter;
    return this.fetchData();
  }
  /**
   * Set sort order and refresh data
   * @param {Object} sort - Sort configuration
   * @returns {Promise<Object>} Promise resolving to fetched data
   */
  async setSort(sort) {
    this.sort = sort;
    return this.fetchData();
  }
  /**
   * Set pagination configuration and refresh data
   * @param {Object} pagination - Pagination configuration
   * @returns {Promise<Object>} Promise resolving to fetched data
   */
  async setPagination(pagination) {
    this.pagination = pagination;
    return this.fetchData();
  }
  /**
   * Clear cache and force-refresh data
   * @returns {Promise<Object>} Promise resolving to fetched data
   */
  async refresh() {
    this._cache = {};
    this._lastFetchTime = null;
    return this.fetchData();
  }
  /**
   * Generate a cache key based on current state
   * @returns {string} Cache key
   * @private
   */
  _generateCacheKey() {
    return [
      this.entityType,
      JSON.stringify(this.filter),
      JSON.stringify(this.sort),
      JSON.stringify(this.pagination)
    ].join('_');
  }
  /**
   * Empty render method as this is a non-UI component
   */
  render() {
    return html`<!-- No UI, this is a data provider component -->`;
  }
}
customElements.define('ok-data-provider', OkDataProvider);