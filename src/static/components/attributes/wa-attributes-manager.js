import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';
/**
 * @element wa-attributes-manager
 * @description Component for managing attributes and attribute types in the UNO framework
 */
export class WebAwesomeAttributesManager extends LitElement {
  static get properties() {
    return {
      // Common properties
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      selectedItem: { type: Object },
      
      // Attribute Type properties
      attributeTypes: { type: Array },
      attributeTypeFilter: { type: String },
      
      // Attribute properties
      attributes: { type: Array },
      attributeFilter: { type: String },
      recordId: { type: String },
      
      // Meta Type properties (for linking attributes)
      metaTypes: { type: Array },
      selectedMetaTypeId: { type: String },
      
      // Dialog flags
      showCreateAttributeTypeDialog: { type: Boolean },
      showEditAttributeTypeDialog: { type: Boolean },
      showCreateAttributeDialog: { type: Boolean },
      showEditAttributeDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      
      // Form models
      attributeTypeForm: { type: Object },
      attributeForm: { type: Object },
      deleteDialogData: { type: Object }
    };
  }
  static get styles() {
    return css`
      :host {
        display: block;
        --attributes-bg: var(--wa-background-color, #f5f5f5);
        --attributes-padding: 20px;
      }
      
      .container {
        padding: var(--attributes-padding);
        background-color: var(--attributes-bg);
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
      
      .attribute-chip {
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
      
      .attribute-chip wa-icon {
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
    `;
  }
  constructor() {
    super();
    this.activeTab = 'attribute-types';
    this.loading = false;
    this.error = null;
    this.selectedItem = null;
    
    this.attributeTypes = [];
    this.attributeTypeFilter = '';
    
    this.attributes = [];
    this.attributeFilter = '';
    this.recordId = '';
    
    this.metaTypes = [];
    this.selectedMetaTypeId = '';
    
    this.showCreateAttributeTypeDialog = false;
    this.showEditAttributeTypeDialog = false;
    this.showCreateAttributeDialog = false;
    this.showEditAttributeDialog = false;
    this.showDeleteDialog = false;
    
    this.attributeTypeForm = this._getDefaultAttributeTypeForm();
    this.attributeForm = this._getDefaultAttributeForm();
    this.deleteDialogData = {
      type: '',
      id: '',
      name: ''
    };
    
    // Load mock data for demonstration
    this._loadMockData();
  }
  _getDefaultAttributeTypeForm() {
    return {
      name: '',
      text: '',
      parent_id: null,
      required: false,
      multiple_allowed: false,
      comment_required: false,
      display_with_objects: true,
      initial_comment: '',
      meta_type_ids: [],
      value_type_ids: []
    };
  }
  _getDefaultAttributeForm() {
    return {
      attribute_type_id: '',
      comment: '',
      follow_up_required: false,
      value_ids: []
    };
  }
  _loadMockData() {
    // Mock meta types
    this.metaTypes = [
      { id: 'meta-type-1', name: 'Customer', description: 'Customer records' },
      { id: 'meta-type-2', name: 'Product', description: 'Product catalog' },
      { id: 'meta-type-3', name: 'Order', description: 'Customer orders' },
      { id: 'meta-type-4', name: 'Ticket', description: 'Support tickets' },
      { id: 'meta-type-5', name: 'Category', description: 'Product categories' },
      { id: 'meta-type-6', name: 'Priority', description: 'Priority levels' },
      { id: 'meta-type-7', name: 'Status', description: 'Status values' }
    ];
    
    // Mock attribute types
    this.attributeTypes = [
      {
        id: 'at-1',
        name: 'Priority',
        text: 'What is the priority of this item?',
        required: true,
        multiple_allowed: false,
        comment_required: false,
        display_with_objects: true,
        initial_comment: '',
        created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        describes: [
          { id: 'meta-type-3', name: 'Order' },
          { id: 'meta-type-4', name: 'Ticket' }
        ],
        value_types: [
          { id: 'meta-type-6', name: 'Priority' }
        ]
      },
      {
        id: 'at-2',
        name: 'Category',
        text: 'Select category for this item',
        required: true,
        multiple_allowed: true,
        comment_required: false,
        display_with_objects: true,
        initial_comment: '',
        created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        describes: [
          { id: 'meta-type-2', name: 'Product' }
        ],
        value_types: [
          { id: 'meta-type-5', name: 'Category' }
        ]
      },
      {
        id: 'at-3',
        name: 'Status',
        text: 'Current status of this item',
        required: true,
        multiple_allowed: false,
        comment_required: true,
        display_with_objects: true,
        initial_comment: 'Initial status set to:',
        created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        describes: [
          { id: 'meta-type-3', name: 'Order' },
          { id: 'meta-type-4', name: 'Ticket' }
        ],
        value_types: [
          { id: 'meta-type-7', name: 'Status' }
        ]
      }
    ];
    
    // Mock attributes
    this.attributes = [
      {
        id: 'attr-1',
        attribute_type_id: 'at-1',
        attribute_type_name: 'Priority',
        comment: 'Set to high due to customer importance',
        follow_up_required: true,
        created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        values: [
          { id: 'value-1', name: 'High', meta_type_id: 'meta-type-6' }
        ],
        record_id: 'order-123'
      },
      {
        id: 'attr-2',
        attribute_type_id: 'at-2',
        attribute_type_name: 'Category',
        comment: '',
        follow_up_required: false,
        created_at: new Date(Date.now() - 8 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 3 * 86400000).toISOString(),
        values: [
          { id: 'value-2', name: 'Electronics', meta_type_id: 'meta-type-5' },
          { id: 'value-3', name: 'Computers', meta_type_id: 'meta-type-5' }
        ],
        record_id: 'product-456'
      },
      {
        id: 'attr-3',
        attribute_type_id: 'at-3',
        attribute_type_name: 'Status',
        comment: 'Customer notified via email',
        follow_up_required: false,
        created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 1 * 86400000).toISOString(),
        values: [
          { id: 'value-4', name: 'Shipped', meta_type_id: 'meta-type-7' }
        ],
        record_id: 'order-123'
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
  selectAttributeType(attributeType) {
    this.selectedItem = { ...attributeType, itemType: 'attribute-type' };
  }
  
  selectAttribute(attribute) {
    this.selectedItem = { ...attribute, itemType: 'attribute' };
  }
  
  closeDetail() {
    this.selectedItem = null;
  }
  handleAttributeTypeFilterChange(e) {
    this.attributeTypeFilter = e.target.value;
  }
  
  handleAttributeFilterChange(e) {
    this.attributeFilter = e.target.value;
  }
  
  handleRecordIdChange(e) {
    this.recordId = e.target.value;
    // In a real implementation, this would trigger a fetch of attributes for this record
    this.fetchAttributesForRecord(this.recordId);
  }
  
  handleMetaTypeChange(e) {
    this.selectedMetaTypeId = e.target.value;
    // In a real implementation, this would filter attribute types applicable to this meta type
    this.fetchAttributeTypesForMetaType(this.selectedMetaTypeId);
  }
  fetchAttributesForRecord(recordId) {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      // Filter existing attributes in mock data
      if (recordId) {
        this.attributes = this.attributes.filter(attr => attr.record_id === recordId);
      } else {
        // Reset to full list
        this._loadMockData();
      }
      
      this.loading = false;
    }, 500);
  }
  
  fetchAttributeTypesForMetaType(metaTypeId) {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      if (metaTypeId) {
        this.attributeTypes = this.attributeTypes.filter(type => 
          type.describes && type.describes.some(mt => mt.id === metaTypeId)
        );
      } else {
        // Reset to full list
        this._loadMockData();
      }
      
      this.loading = false;
    }, 500);
  }
  // Dialog management
  openCreateAttributeTypeDialog() {
    this.attributeTypeForm = this._getDefaultAttributeTypeForm();
    this.showCreateAttributeTypeDialog = true;
  }
  
  openEditAttributeTypeDialog(attributeType) {
    this.attributeTypeForm = {
      id: attributeType.id,
      name: attributeType.name,
      text: attributeType.text,
      parent_id: attributeType.parent_id || null,
      required: attributeType.required,
      multiple_allowed: attributeType.multiple_allowed,
      comment_required: attributeType.comment_required,
      display_with_objects: attributeType.display_with_objects,
      initial_comment: attributeType.initial_comment || '',
      meta_type_ids: attributeType.describes ? attributeType.describes.map(mt => mt.id) : [],
      value_type_ids: attributeType.value_types ? attributeType.value_types.map(vt => vt.id) : []
    };
    
    this.showEditAttributeTypeDialog = true;
  }
  
  openCreateAttributeDialog() {
    this.attributeForm = this._getDefaultAttributeForm();
    this.showCreateAttributeDialog = true;
  }
  
  openEditAttributeDialog(attribute) {
    this.attributeForm = {
      id: attribute.id,
      attribute_type_id: attribute.attribute_type_id,
      comment: attribute.comment || '',
      follow_up_required: attribute.follow_up_required,
      value_ids: attribute.values ? attribute.values.map(v => v.id) : []
    };
    
    this.showEditAttributeDialog = true;
  }
  
  openDeleteDialog(item, type) {
    this.deleteDialogData = {
      type: type,
      id: item.id,
      name: type === 'attribute-type' ? item.name : `${item.attribute_type_name} attribute`
    };
    
    this.showDeleteDialog = true;
  }
  
  closeDialogs() {
    this.showCreateAttributeTypeDialog = false;
    this.showEditAttributeTypeDialog = false;
    this.showCreateAttributeDialog = false;
    this.showEditAttributeDialog = false;
    this.showDeleteDialog = false;
  }
  // Form handlers
  handleAttributeTypeFormChange(e) {
    const field = e.target.name;
    let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    // Handle multi-select fields
    if (field === 'meta_type_ids' || field === 'value_type_ids') {
      value = Array.from(e.target.selectedOptions).map(option => option.value);
    }
    
    this.attributeTypeForm = {
      ...this.attributeTypeForm,
      [field]: value
    };
  }
  
  handleAttributeFormChange(e) {
    const field = e.target.name;
    let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    // Handle multi-select fields
    if (field === 'value_ids') {
      value = Array.from(e.target.selectedOptions).map(option => option.value);
    }
    
    this.attributeForm = {
      ...this.attributeForm,
      [field]: value
    };
  }
  // CRUD operations
  createAttributeType() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const newAttributeType = {
          id: `at-${Date.now()}`,
          ...this.attributeTypeForm,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          describes: this.attributeTypeForm.meta_type_ids.map(id => {
            const metaType = this.metaTypes.find(mt => mt.id === id);
            return { id, name: metaType?.name || id };
          }),
          value_types: this.attributeTypeForm.value_type_ids.map(id => {
            const metaType = this.metaTypes.find(mt => mt.id === id);
            return { id, name: metaType?.name || id };
          })
        };
        
        this.attributeTypes = [...this.attributeTypes, newAttributeType];
        this.showCreateAttributeTypeDialog = false;
        this._showNotification('Attribute type created successfully', 'success');
      } catch (err) {
        console.error('Error creating attribute type:', err);
        this._showNotification('Failed to create attribute type', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updateAttributeType() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const updatedAttributeType = {
          ...this.attributeTypeForm,
          updated_at: new Date().toISOString(),
          describes: this.attributeTypeForm.meta_type_ids.map(id => {
            const metaType = this.metaTypes.find(mt => mt.id === id);
            return { id, name: metaType?.name || id };
          }),
          value_types: this.attributeTypeForm.value_type_ids.map(id => {
            const metaType = this.metaTypes.find(mt => mt.id === id);
            return { id, name: metaType?.name || id };
          })
        };
        
        this.attributeTypes = this.attributeTypes.map(type => 
          type.id === this.attributeTypeForm.id ? updatedAttributeType : type
        );
        
        if (this.selectedItem && this.selectedItem.id === updatedAttributeType.id) {
          this.selectedItem = { ...updatedAttributeType, itemType: 'attribute-type' };
        }
        
        this.showEditAttributeTypeDialog = false;
        this._showNotification('Attribute type updated successfully', 'success');
      } catch (err) {
        console.error('Error updating attribute type:', err);
        this._showNotification('Failed to update attribute type', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  createAttribute() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Get the attribute type name
        const attributeType = this.attributeTypes.find(
          type => type.id === this.attributeForm.attribute_type_id
        );
        
        const attributeTypeName = attributeType ? attributeType.name : 'Unknown';
        
        // Get the values
        const values = this.attributeForm.value_ids.map(id => {
          // In a real implementation, you would fetch these from the API
          // For demo purposes, we'll create mock values
          return {
            id,
            name: `Value ${id.split('-').pop()}`,
            meta_type_id: 'meta-type-1'
          };
        });
        
        const newAttribute = {
          id: `attr-${Date.now()}`,
          attribute_type_id: this.attributeForm.attribute_type_id,
          attribute_type_name: attributeTypeName,
          comment: this.attributeForm.comment,
          follow_up_required: this.attributeForm.follow_up_required,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          values,
          record_id: this.recordId || `record-${Date.now()}`
        };
        
        this.attributes = [...this.attributes, newAttribute];
        this.showCreateAttributeDialog = false;
        this._showNotification('Attribute created successfully', 'success');
      } catch (err) {
        console.error('Error creating attribute:', err);
        this._showNotification('Failed to create attribute', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updateAttribute() {
    // In a real implementation, this would be an API call
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Get the current attribute to preserve any fields not in the form
        const currentAttribute = this.attributes.find(attr => attr.id === this.attributeForm.id);
        
        if (!currentAttribute) {
          throw new Error('Attribute not found');
        }
        
        // Get the values
        const values = this.attributeForm.value_ids.map(id => {
          // First check if the value exists in the current attribute
          const existingValue = currentAttribute.values.find(v => v.id === id);
          
          if (existingValue) {
            return existingValue;
          }
          
          // If not, create a mock value
          return {
            id,
            name: `Value ${id.split('-').pop()}`,
            meta_type_id: 'meta-type-1'
          };
        });
        
        const updatedAttribute = {
          ...currentAttribute,
          comment: this.attributeForm.comment,
          follow_up_required: this.attributeForm.follow_up_required,
          updated_at: new Date().toISOString(),
          values
        };
        
        this.attributes = this.attributes.map(attr => 
          attr.id === this.attributeForm.id ? updatedAttribute : attr
        );
        
        if (this.selectedItem && this.selectedItem.id === updatedAttribute.id) {
          this.selectedItem = { ...updatedAttribute, itemType: 'attribute' };
        }
        
        this.showEditAttributeDialog = false;
        this._showNotification('Attribute updated successfully', 'success');
      } catch (err) {
        console.error('Error updating attribute:', err);
        this._showNotification('Failed to update attribute', 'error');
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
        if (this.deleteDialogData.type === 'attribute-type') {
          this.attributeTypes = this.attributeTypes.filter(
            type => type.id !== this.deleteDialogData.id
          );
        } else {
          this.attributes = this.attributes.filter(
            attr => attr.id !== this.deleteDialogData.id
          );
        }
        
        // Clear selection if the deleted item was selected
        if (this.selectedItem && this.selectedItem.id === this.deleteDialogData.id) {
          this.selectedItem = null;
        }
        
        this.showDeleteDialog = false;
        this._showNotification(`${this.deleteDialogData.type === 'attribute-type' ? 'Attribute type' : 'Attribute'} deleted successfully`, 'success');
      } catch (err) {
        console.error('Error deleting item:', err);
        this._showNotification('Failed to delete item', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  // Filtering
  filteredAttributeTypes() {
    if (!this.attributeTypeFilter) {
      return this.attributeTypes;
    }
    
    const filter = this.attributeTypeFilter.toLowerCase();
    return this.attributeTypes.filter(type => 
      type.name.toLowerCase().includes(filter) || 
      type.text.toLowerCase().includes(filter)
    );
  }
  
  filteredAttributes() {
    if (!this.attributeFilter) {
      return this.attributes;
    }
    
    const filter = this.attributeFilter.toLowerCase();
    return this.attributes.filter(attr => 
      attr.attribute_type_name.toLowerCase().includes(filter) || 
      (attr.comment && attr.comment.toLowerCase().includes(filter)) ||
      attr.values.some(v => v.name.toLowerCase().includes(filter))
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
  // Render methods
  renderAttributeTypeDetail() {
    if (!this.selectedItem || this.selectedItem.itemType !== 'attribute-type') return html``;
    
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
            <wa-button variant="outlined" @click=${() => this.openEditAttributeTypeDialog(item)}>
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
            <div class="detail-value">${item.text}</div>
          </div>
          
          <div class="form-grid">
            <div class="detail-property">
              <div class="detail-label">Required</div>
              <div class="detail-value">${item.required ? 'Yes' : 'No'}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Multiple Values Allowed</div>
              <div class="detail-value">${item.multiple_allowed ? 'Yes' : 'No'}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Comment Required</div>
              <div class="detail-value">${item.comment_required ? 'Yes' : 'No'}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Display with Objects</div>
              <div class="detail-value">${item.display_with_objects ? 'Yes' : 'No'}</div>
            </div>
          </div>
          
          ${item.initial_comment ? html`
            <div class="detail-property">
              <div class="detail-label">Initial Comment Template</div>
              <div class="detail-value">${item.initial_comment}</div>
            </div>
          ` : ''}
          
          <div class="detail-property">
            <div class="detail-label">Applicable Meta Types</div>
            <div class="detail-value">
              ${item.describes && item.describes.length ? html`
                <div class="tags-container">
                  ${item.describes.map(metaType => html`
                    <div class="attribute-chip">
                      ${metaType.name}
                    </div>
                  `)}
                </div>
              ` : 'None specified'}
            </div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Allowed Value Types</div>
            <div class="detail-value">
              ${item.value_types && item.value_types.length ? html`
                <div class="tags-container">
                  ${item.value_types.map(valueType => html`
                    <div class="attribute-chip">
                      ${valueType.name}
                    </div>
                  `)}
                </div>
              ` : 'None specified'}
            </div>
          </div>
          
          <div class="detail-actions">
            <wa-button @click=${() => this.openDeleteDialog(item, 'attribute-type')} color="error" variant="outlined">
              <wa-icon slot="prefix" name="delete"></wa-icon>
              Delete
            </wa-button>
            <wa-button @click=${() => this.openEditAttributeTypeDialog(item)} color="primary">
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderAttributeDetail() {
    if (!this.selectedItem || this.selectedItem.itemType !== 'attribute') return html``;
    
    const item = this.selectedItem;
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div>
            <h2 class="detail-title">${item.attribute_type_name} Attribute</h2>
            <div class="detail-meta">
              <span>Created: ${this.formatRelativeTime(item.created_at)}</span>
              <span> • </span>
              <span>Updated: ${this.formatRelativeTime(item.updated_at)}</span>
            </div>
          </div>
          
          <div>
            <wa-button variant="outlined" @click=${() => this.openEditAttributeDialog(item)}>
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
            <div class="detail-label">Record ID</div>
            <div class="detail-value">${item.record_id || 'Not associated with a record'}</div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Comment</div>
            <div class="detail-value">${item.comment || 'No comment'}</div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Follow-up Required</div>
            <div class="detail-value">${item.follow_up_required ? 'Yes' : 'No'}</div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Values</div>
            <div class="detail-value">
              ${item.values && item.values.length ? html`
                <div class="tags-container">
                  ${item.values.map(value => html`
                    <div class="attribute-chip">
                      ${value.name}
                    </div>
                  `)}
                </div>
              ` : 'No values assigned'}
            </div>
          </div>
          
          <div class="detail-actions">
            <wa-button @click=${() => this.openDeleteDialog(item, 'attribute')} color="error" variant="outlined">
              <wa-icon slot="prefix" name="delete"></wa-icon>
              Delete
            </wa-button>
            <wa-button @click=${() => this.openEditAttributeDialog(item)} color="primary">
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderAttributeTypesTab() {
    const filtered = this.filteredAttributeTypes();
    
    return html`
      <div class="filter-bar">
        <wa-input 
          class="filter-input"
          placeholder="Filter attribute types"
          .value=${this.attributeTypeFilter}
          @input=${this.handleAttributeTypeFilterChange}>
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
        
        <wa-button @click=${this.openCreateAttributeTypeDialog} color="primary">
          <wa-icon slot="prefix" name="add"></wa-icon>
          Create
        </wa-button>
      </div>
      
      ${filtered.length > 0 ? html`
        <div class="grid">
          ${filtered.map(type => html`
            <wa-card class="grid-item" @click=${() => this.selectAttributeType(type)}>
              <div style="padding: 16px;">
                <div class="item-header">
                  <h3 class="item-title">${type.name}</h3>
                  <div class="item-meta">
                    ${type.required ? html`<span class="badge">Required</span>` : ''}
                    ${type.multiple_allowed ? html`<span class="badge">Multiple</span>` : ''}
                  </div>
                </div>
                
                <p class="item-description">${type.text}</p>
                
                <div>
                  <strong>Applies to:</strong>
                  <div class="tags-container">
                    ${type.describes && type.describes.length ? 
                      type.describes.map(metaType => html`<span class="attribute-chip">${metaType.name}</span>`) : 
                      html`<span class="attribute-chip">All</span>`}
                  </div>
                </div>
                
                <div style="margin-top: 8px; font-size: 12px; color: var(--wa-text-secondary-color);">
                  Updated ${this.formatRelativeTime(type.updated_at)}
                </div>
              </div>
            </wa-card>
          `)}
        </div>
      ` : html`
        <div class="empty-state">
          <wa-icon name="view_list"></wa-icon>
          <h3>No attribute types found</h3>
          <p>Create a new attribute type to get started</p>
          <wa-button @click=${this.openCreateAttributeTypeDialog} color="primary" style="margin-top: 16px;">
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Attribute Type
          </wa-button>
        </div>
      `}
      
      ${this.renderAttributeTypeDetail()}
    `;
  }
  
  renderAttributesTab() {
    const filtered = this.filteredAttributes();
    
    return html`
      <div class="filter-bar">
        <wa-input
          class="filter-input"
          placeholder="Filter attributes"
          .value=${this.attributeFilter}
          @input=${this.handleAttributeFilterChange}>
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-input
          placeholder="Filter by record ID"
          .value=${this.recordId}
          @input=${this.handleRecordIdChange}>
          <wa-icon slot="prefix" name="bookmark"></wa-icon>
        </wa-input>
        
        <wa-button @click=${this.openCreateAttributeDialog} color="primary">
          <wa-icon slot="prefix" name="add"></wa-icon>
          Create
        </wa-button>
      </div>
      
      ${filtered.length > 0 ? html`
        <div class="grid">
          ${filtered.map(attribute => html`
            <wa-card class="grid-item" @click=${() => this.selectAttribute(attribute)}>
              <div style="padding: 16px;">
                <div class="item-header">
                  <h3 class="item-title">${attribute.attribute_type_name}</h3>
                  <div class="item-meta">
                    ${attribute.follow_up_required ? html`<span class="badge">Follow-up</span>` : ''}
                  </div>
                </div>
                
                <p class="item-description">
                  ${attribute.comment || 'No comment provided'}
                </p>
                
                <div>
                  <strong>Values:</strong>
                  <div class="tags-container">
                    ${attribute.values && attribute.values.length ? 
                      attribute.values.map(value => html`<span class="attribute-chip">${value.name}</span>`) : 
                      html`<span>None</span>`}
                  </div>
                </div>
                
                <div style="margin-top: 8px; font-size: 12px; color: var(--wa-text-secondary-color);">
                  Record: ${attribute.record_id || 'None'} • Updated ${this.formatRelativeTime(attribute.updated_at)}
                </div>
              </div>
            </wa-card>
          `)}
        </div>
      ` : html`
        <div class="empty-state">
          <wa-icon name="category"></wa-icon>
          <h3>No attributes found</h3>
          <p>Create a new attribute or adjust your filter criteria</p>
          <wa-button @click=${this.openCreateAttributeDialog} color="primary" style="margin-top: 16px;">
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Attribute
          </wa-button>
        </div>
      `}
      
      ${this.renderAttributeDetail()}
    `;
  }
  
  renderCreateAttributeTypeDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showCreateAttributeTypeDialog}
        @close=${this.closeDialogs}
        title="Create Attribute Type">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.attributeTypeForm.name}
              @input=${this.handleAttributeTypeFormChange}
              required>
            </wa-input>
            
            <wa-input
              label="Parent ID"
              name="parent_id"
              .value=${this.attributeTypeForm.parent_id || ''}
              @input=${this.handleAttributeTypeFormChange}>
            </wa-input>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description Text"
            name="text"
            .value=${this.attributeTypeForm.text}
            @input=${this.handleAttributeTypeFormChange}
            required>
          </wa-textarea>
          
          <div class="form-grid" style="margin-top: 16px;">
            <wa-checkbox
              label="Required"
              name="required"
              ?checked=${this.attributeTypeForm.required}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Multiple Values Allowed"
              name="multiple_allowed"
              ?checked=${this.attributeTypeForm.multiple_allowed}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Comment Required"
              name="comment_required"
              ?checked=${this.attributeTypeForm.comment_required}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Display with Objects"
              name="display_with_objects"
              ?checked=${this.attributeTypeForm.display_with_objects}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Initial Comment Template"
            name="initial_comment"
            .value=${this.attributeTypeForm.initial_comment || ''}
            @input=${this.handleAttributeTypeFormChange}>
          </wa-textarea>
          
          <div class="form-grid">
            <wa-select
              label="Applicable Meta Types"
              name="meta_type_ids"
              multiple
              .value=${this.attributeTypeForm.meta_type_ids}
              @change=${this.handleAttributeTypeFormChange}>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
            
            <wa-select
              label="Allowed Value Types"
              name="value_type_ids"
              multiple
              .value=${this.attributeTypeForm.value_type_ids}
              @change=${this.handleAttributeTypeFormChange}>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createAttributeType} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditAttributeTypeDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showEditAttributeTypeDialog}
        @close=${this.closeDialogs}
        title="Edit Attribute Type">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.attributeTypeForm.name}
              @input=${this.handleAttributeTypeFormChange}
              required>
            </wa-input>
            
            <wa-input
              label="Parent ID"
              name="parent_id"
              .value=${this.attributeTypeForm.parent_id || ''}
              @input=${this.handleAttributeTypeFormChange}>
            </wa-input>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Description Text"
            name="text"
            .value=${this.attributeTypeForm.text}
            @input=${this.handleAttributeTypeFormChange}
            required>
          </wa-textarea>
          
          <div class="form-grid" style="margin-top: 16px;">
            <wa-checkbox
              label="Required"
              name="required"
              ?checked=${this.attributeTypeForm.required}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Multiple Values Allowed"
              name="multiple_allowed"
              ?checked=${this.attributeTypeForm.multiple_allowed}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Comment Required"
              name="comment_required"
              ?checked=${this.attributeTypeForm.comment_required}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Display with Objects"
              name="display_with_objects"
              ?checked=${this.attributeTypeForm.display_with_objects}
              @change=${this.handleAttributeTypeFormChange}>
            </wa-checkbox>
          </div>
          
          <wa-textarea
            class="form-full-width"
            label="Initial Comment Template"
            name="initial_comment"
            .value=${this.attributeTypeForm.initial_comment || ''}
            @input=${this.handleAttributeTypeFormChange}>
          </wa-textarea>
          
          <div class="form-grid">
            <wa-select
              label="Applicable Meta Types"
              name="meta_type_ids"
              multiple
              .value=${this.attributeTypeForm.meta_type_ids}
              @change=${this.handleAttributeTypeFormChange}>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
            
            <wa-select
              label="Allowed Value Types"
              name="value_type_ids"
              multiple
              .value=${this.attributeTypeForm.value_type_ids}
              @change=${this.handleAttributeTypeFormChange}>
              ${this.metaTypes.map(metaType => html`
                <wa-option value=${metaType.id}>${metaType.name}</wa-option>
              `)}
            </wa-select>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updateAttributeType} color="primary">
            Update
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderCreateAttributeDialog() {
    // Mock values for dropdown
    const mockValues = [
      { id: 'value-1', name: 'High', meta_type_id: 'meta-type-6' },
      { id: 'value-2', name: 'Electronics', meta_type_id: 'meta-type-5' },
      { id: 'value-3', name: 'Computers', meta_type_id: 'meta-type-5' },
      { id: 'value-4', name: 'Shipped', meta_type_id: 'meta-type-7' },
      { id: 'value-5', name: 'Medium', meta_type_id: 'meta-type-6' },
      { id: 'value-6', name: 'Low', meta_type_id: 'meta-type-6' }
    ];
    
    return html`
      <wa-dialog 
        ?open=${this.showCreateAttributeDialog}
        @close=${this.closeDialogs}
        title="Create Attribute">
        
        <div class="dialog-content">
          <wa-select
            label="Attribute Type"
            name="attribute_type_id"
            .value=${this.attributeForm.attribute_type_id}
            @change=${this.handleAttributeFormChange}
            required>
            <wa-option value="">Select an attribute type</wa-option>
            ${this.attributeTypes.map(type => html`
              <wa-option value=${type.id}>${type.name}</wa-option>
            `)}
          </wa-select>
          
          <wa-textarea
            label="Comment"
            name="comment"
            .value=${this.attributeForm.comment}
            @input=${this.handleAttributeFormChange}
            style="margin-top: 16px;">
          </wa-textarea>
          
          <wa-checkbox
            label="Follow-up Required"
            name="follow_up_required"
            ?checked=${this.attributeForm.follow_up_required}
            @change=${this.handleAttributeFormChange}
            style="margin-top: 16px;">
          </wa-checkbox>
          
          <wa-select
            label="Values"
            name="value_ids"
            multiple
            .value=${this.attributeForm.value_ids}
            @change=${this.handleAttributeFormChange}
            style="margin-top: 16px;">
            ${mockValues.map(value => html`
              <wa-option value=${value.id}>${value.name}</wa-option>
            `)}
          </wa-select>
          
          <wa-input
            label="Record ID"
            name="record_id"
            .value=${this.recordId}
            @input=${this.handleRecordIdChange}
            style="margin-top: 16px;">
          </wa-input>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createAttribute} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditAttributeDialog() {
    // Mock values for dropdown
    const mockValues = [
      { id: 'value-1', name: 'High', meta_type_id: 'meta-type-6' },
      { id: 'value-2', name: 'Electronics', meta_type_id: 'meta-type-5' },
      { id: 'value-3', name: 'Computers', meta_type_id: 'meta-type-5' },
      { id: 'value-4', name: 'Shipped', meta_type_id: 'meta-type-7' },
      { id: 'value-5', name: 'Medium', meta_type_id: 'meta-type-6' },
      { id: 'value-6', name: 'Low', meta_type_id: 'meta-type-6' }
    ];
    
    return html`
      <wa-dialog 
        ?open=${this.showEditAttributeDialog}
        @close=${this.closeDialogs}
        title="Edit Attribute">
        
        <div class="dialog-content">
          <wa-textarea
            label="Comment"
            name="comment"
            .value=${this.attributeForm.comment}
            @input=${this.handleAttributeFormChange}>
          </wa-textarea>
          
          <wa-checkbox
            label="Follow-up Required"
            name="follow_up_required"
            ?checked=${this.attributeForm.follow_up_required}
            @change=${this.handleAttributeFormChange}
            style="margin-top: 16px;">
          </wa-checkbox>
          
          <wa-select
            label="Values"
            name="value_ids"
            multiple
            .value=${this.attributeForm.value_ids}
            @change=${this.handleAttributeFormChange}
            style="margin-top: 16px;">
            ${mockValues.map(value => html`
              <wa-option value=${value.id}>${value.name}</wa-option>
            `)}
          </wa-select>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updateAttribute} color="primary">
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
  render() {
    return html`
      <div class="container">
        <div class="header">
          <h1 class="title">Attributes Manager</h1>
          <p class="subtitle">Manage dynamic attributes and attribute types for your entities</p>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="attribute-types">Attribute Types</wa-tab>
          <wa-tab value="attributes">Attributes</wa-tab>
        </wa-tabs>
        
        <wa-tab-panel value="attribute-types" ?active=${this.activeTab === 'attribute-types'}>
          ${this.renderAttributeTypesTab()}
        </wa-tab-panel>
        
        <wa-tab-panel value="attributes" ?active=${this.activeTab === 'attributes'}>
          ${this.renderAttributesTab()}
        </wa-tab-panel>
        
        ${this.renderCreateAttributeTypeDialog()}
        ${this.renderEditAttributeTypeDialog()}
        ${this.renderCreateAttributeDialog()}
        ${this.renderEditAttributeDialog()}
        ${this.renderDeleteDialog()}
        
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
customElements.define('wa-attributes-manager', WebAwesomeAttributesManager);