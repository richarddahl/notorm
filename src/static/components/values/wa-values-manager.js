import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
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
import '@webcomponents/awesome/wa-date-picker.js';
import '@webcomponents/awesome/wa-time-picker.js';

/**
 * @element wa-values-manager
 * @description Component for managing different types of values in the UNO framework
 */
export class WebAwesomeValuesManager extends LitElement {
  static get properties() {
    return {
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      
      // Value properties
      values: { type: Array },
      selectedValue: { type: Object },
      
      // Search and filter
      searchTerm: { type: String },
      selectedValueType: { type: String },
      
      // Dialog flags
      showCreateValueDialog: { type: Boolean },
      showEditValueDialog: { type: Boolean },
      showDeleteDialog: { type: Boolean },
      showUploadDialog: { type: Boolean },
      
      // Form models  
      valueForm: { type: Object },
      attachmentForm: { type: Object }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --values-bg: var(--wa-background-color, #f5f5f5);
        --values-padding: 20px;
      }
      
      .container {
        padding: var(--values-padding);
        background-color: var(--values-bg);
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
      
      .filter-bar {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
      }
      
      .filter-input {
        flex: 1;
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
      
      .item-value {
        font-size: 16px;
        margin: 8px 0;
        word-break: break-all;
      }
      
      .badge {
        background-color: var(--wa-primary-color-light, rgba(63, 81, 181, 0.1));
        color: var(--wa-primary-color, #3f51b5);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 8px;
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
        word-break: break-all;
      }
      
      .detail-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid var(--wa-border-color, #e0e0e0);
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
      
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      
      .form-field {
        margin-bottom: 16px;
      }
      
      .value-type-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
      }
      
      .type-boolean {
        background-color: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
      }
      
      .type-integer {
        background-color: rgba(33, 150, 243, 0.1);
        color: #2196F3;
      }
      
      .type-decimal {
        background-color: rgba(156, 39, 176, 0.1);
        color: #9C27B0;
      }
      
      .type-text {
        background-color: rgba(255, 152, 0, 0.1);
        color: #FF9800;
      }
      
      .type-date {
        background-color: rgba(0, 188, 212, 0.1);
        color: #00BCD4;
      }
      
      .type-datetime {
        background-color: rgba(63, 81, 181, 0.1);
        color: #3F51B5;
      }
      
      .type-time {
        background-color: rgba(121, 85, 72, 0.1);
        color: #795548;
      }
      
      .type-attachment {
        background-color: rgba(244, 67, 54, 0.1);
        color: #F44336;
      }
      
      .value-display {
        font-size: 18px;
        font-weight: 500;
        margin: 16px 0;
        padding: 8px;
        background-color: var(--wa-background-color, #f5f5f5);
        border-radius: 4px;
        word-break: break-all;
      }
      
      .file-upload {
        border: 2px dashed var(--wa-border-color, #e0e0e0);
        border-radius: 4px;
        padding: 24px;
        text-align: center;
        margin-bottom: 16px;
        cursor: pointer;
        transition: border-color 0.2s ease, background-color 0.2s ease;
      }
      
      .file-upload:hover {
        border-color: var(--wa-primary-color, #3f51b5);
        background-color: rgba(63, 81, 181, 0.05);
      }
      
      .file-upload wa-icon {
        font-size: 48px;
        color: var(--wa-text-secondary-color, #757575);
        margin-bottom: 16px;
      }
      
      .tab-content {
        margin-top: 24px;
      }
    `;
  }

  constructor() {
    super();
    this.activeTab = 'boolean';
    this.loading = false;
    this.error = null;
    
    this.values = [];
    this.selectedValue = null;
    
    this.searchTerm = '';
    this.selectedValueType = 'boolean';
    
    this.showCreateValueDialog = false;
    this.showEditValueDialog = false;
    this.showDeleteDialog = false;
    this.showUploadDialog = false;
    
    this.valueForm = this._getDefaultValueForm();
    this.attachmentForm = {
      name: '',
      file: null
    };
    
    // Load mock data for demonstration
    this._loadMockData();
  }

  _getDefaultValueForm() {
    return {
      valueType: 'boolean',
      name: '',
      value: null
    };
  }

  _loadMockData() {
    // Boolean values
    const booleanValues = [
      {
        id: 'bool-1',
        name: 'Is Active',
        value: true,
        valueType: 'boolean',
        created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 15 * 86400000).toISOString()
      },
      {
        id: 'bool-2',
        name: 'Is Featured',
        value: true,
        valueType: 'boolean',
        created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 12 * 86400000).toISOString()
      },
      {
        id: 'bool-3',
        name: 'Is Deprecated',
        value: false,
        valueType: 'boolean',
        created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString()
      }
    ];
    
    // Integer values
    const integerValues = [
      {
        id: 'int-1',
        name: 'Priority Level',
        value: 1,
        valueType: 'integer',
        created_at: new Date(Date.now() - 28 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 14 * 86400000).toISOString()
      },
      {
        id: 'int-2',
        name: 'Number of Items',
        value: 42,
        valueType: 'integer',
        created_at: new Date(Date.now() - 22 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 11 * 86400000).toISOString()
      },
      {
        id: 'int-3',
        name: 'Max Capacity',
        value: 100,
        valueType: 'integer',
        created_at: new Date(Date.now() - 18 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 9 * 86400000).toISOString()
      }
    ];
    
    // Text values
    const textValues = [
      {
        id: 'text-1',
        name: 'Product Category',
        value: 'Electronics',
        valueType: 'text',
        created_at: new Date(Date.now() - 27 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 13 * 86400000).toISOString()
      },
      {
        id: 'text-2',
        name: 'Status',
        value: 'In Progress',
        valueType: 'text',
        created_at: new Date(Date.now() - 21 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString()
      },
      {
        id: 'text-3',
        name: 'Location',
        value: 'New York',
        valueType: 'text',
        created_at: new Date(Date.now() - 17 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 8 * 86400000).toISOString()
      }
    ];
    
    // Decimal values
    const decimalValues = [
      {
        id: 'decimal-1',
        name: 'Price',
        value: 99.99,
        valueType: 'decimal',
        created_at: new Date(Date.now() - 26 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 13 * 86400000).toISOString()
      },
      {
        id: 'decimal-2',
        name: 'Tax Rate',
        value: 0.085,
        valueType: 'decimal',
        created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString()
      },
      {
        id: 'decimal-3',
        name: 'Discount',
        value: 0.15,
        valueType: 'decimal',
        created_at: new Date(Date.now() - 16 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 8 * 86400000).toISOString()
      }
    ];
    
    // Date values
    const dateValues = [
      {
        id: 'date-1',
        name: 'Due Date',
        value: '2025-05-15',
        valueType: 'date',
        created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 12 * 86400000).toISOString()
      },
      {
        id: 'date-2',
        name: 'Start Date',
        value: '2025-04-01',
        valueType: 'date',
        created_at: new Date(Date.now() - 19 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 9 * 86400000).toISOString()
      },
      {
        id: 'date-3',
        name: 'End Date',
        value: '2025-06-30',
        valueType: 'date',
        created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 7 * 86400000).toISOString()
      }
    ];
    
    // DateTime values
    const dateTimeValues = [
      {
        id: 'datetime-1',
        name: 'Created At',
        value: '2025-04-10T14:30:00',
        valueType: 'datetime',
        created_at: new Date(Date.now() - 24 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 12 * 86400000).toISOString()
      },
      {
        id: 'datetime-2',
        name: 'Updated At',
        value: '2025-04-12T09:15:00',
        valueType: 'datetime',
        created_at: new Date(Date.now() - 18 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 9 * 86400000).toISOString()
      },
      {
        id: 'datetime-3',
        name: 'Scheduled For',
        value: '2025-05-01T10:00:00',
        valueType: 'datetime',
        created_at: new Date(Date.now() - 14 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 7 * 86400000).toISOString()
      }
    ];
    
    // Time values
    const timeValues = [
      {
        id: 'time-1',
        name: 'Opening Time',
        value: '09:00:00',
        valueType: 'time',
        created_at: new Date(Date.now() - 23 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 11 * 86400000).toISOString()
      },
      {
        id: 'time-2',
        name: 'Closing Time',
        value: '17:30:00',
        valueType: 'time',
        created_at: new Date(Date.now() - 17 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 8 * 86400000).toISOString()
      },
      {
        id: 'time-3',
        name: 'Lunch Break',
        value: '12:00:00',
        valueType: 'time',
        created_at: new Date(Date.now() - 13 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 6 * 86400000).toISOString()
      }
    ];
    
    // Attachment values
    const attachmentValues = [
      {
        id: 'attachment-1',
        name: 'User Manual',
        file_path: '/uploads/user_manual.pdf',
        valueType: 'attachment',
        created_at: new Date(Date.now() - 22 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 11 * 86400000).toISOString()
      },
      {
        id: 'attachment-2',
        name: 'Product Image',
        file_path: '/uploads/product.jpg',
        valueType: 'attachment',
        created_at: new Date(Date.now() - 16 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 8 * 86400000).toISOString()
      },
      {
        id: 'attachment-3',
        name: 'Invoice Template',
        file_path: '/uploads/invoice_template.xlsx',
        valueType: 'attachment',
        created_at: new Date(Date.now() - 12 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 6 * 86400000).toISOString()
      }
    ];
    
    // Group all values by type
    this.valuesByType = {
      boolean: booleanValues,
      integer: integerValues,
      text: textValues,
      decimal: decimalValues,
      date: dateValues,
      datetime: dateTimeValues,
      time: timeValues,
      attachment: attachmentValues
    };
    
    // Set initial values based on active tab
    this.values = this.valuesByType[this.activeTab] || [];
  }

  connectedCallback() {
    super.connectedCallback();
  }

  handleTabChange(e) {
    this.activeTab = e.detail.value;
    this.values = this.valuesByType[this.activeTab] || [];
    this.selectedValue = null; // Clear selection
  }
  
  handleSearchChange(e) {
    this.searchTerm = e.target.value;
    this._filterValues();
  }
  
  selectValue(value) {
    this.selectedValue = value;
  }
  
  closeDetail() {
    this.selectedValue = null;
  }
  
  _filterValues() {
    if (!this.searchTerm) {
      this.values = this.valuesByType[this.activeTab] || [];
      return;
    }
    
    const searchTerm = this.searchTerm.toLowerCase();
    const allValues = this.valuesByType[this.activeTab] || [];
    
    this.values = allValues.filter(value => {
      return value.name.toLowerCase().includes(searchTerm) || 
             String(value.value).toLowerCase().includes(searchTerm);
    });
  }
  
  // Dialog management
  openCreateValueDialog() {
    this.valueForm = {
      valueType: this.activeTab,
      name: '',
      value: this._getDefaultValueForType(this.activeTab)
    };
    
    this.showCreateValueDialog = true;
  }
  
  openUploadDialog() {
    this.attachmentForm = {
      name: '',
      file: null
    };
    
    this.showUploadDialog = true;
  }
  
  openEditValueDialog(value) {
    this.valueForm = {
      id: value.id,
      valueType: value.valueType,
      name: value.name,
      value: value.value
    };
    
    this.showEditValueDialog = true;
  }
  
  openDeleteDialog(value) {
    this.selectedValue = value;
    this.showDeleteDialog = true;
  }
  
  closeDialogs() {
    this.showCreateValueDialog = false;
    this.showEditValueDialog = false;
    this.showDeleteDialog = false;
    this.showUploadDialog = false;
  }
  
  _getDefaultValueForType(valueType) {
    switch(valueType) {
      case 'boolean':
        return false;
      case 'integer':
        return 0;
      case 'decimal':
        return 0.0;
      case 'text':
        return '';
      case 'date':
        return new Date().toISOString().split('T')[0];
      case 'datetime':
        return new Date().toISOString().slice(0, 16);
      case 'time':
        return '12:00:00';
      default:
        return null;
    }
  }
  
  // Form handlers
  handleValueFormChange(e) {
    const field = e.target.name;
    let value = e.target.value;
    
    // Special handling for boolean values
    if (field === 'value' && this.valueForm.valueType === 'boolean') {
      value = e.target.checked;
    }
    
    this.valueForm = {
      ...this.valueForm,
      [field]: value
    };
  }
  
  handleAttachmentFormChange(e) {
    const field = e.target.name;
    const value = e.target.value;
    
    this.attachmentForm = {
      ...this.attachmentForm,
      [field]: value
    };
  }
  
  handleFileChange(e) {
    const file = e.target.files[0];
    if (file) {
      this.attachmentForm.file = file;
    }
  }
  
  // Trigger file input click
  triggerFileInput() {
    const fileInput = this.shadowRoot.querySelector('#file-input');
    if (fileInput) {
      fileInput.click();
    }
  }
  
  // CRUD operations
  createValue() {
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Generate a new ID
        const id = `${this.valueForm.valueType}-${Date.now()}`;
        
        // Create new value
        const newValue = {
          id,
          name: this.valueForm.name,
          value: this.valueForm.value,
          valueType: this.valueForm.valueType,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        // Add to values
        this.valuesByType[this.valueForm.valueType] = [
          newValue,
          ...this.valuesByType[this.valueForm.valueType]
        ];
        
        // If current tab is the same as the value type, update the values
        if (this.activeTab === this.valueForm.valueType) {
          this.values = this.valuesByType[this.valueForm.valueType];
        }
        
        this.closeDialogs();
        this._showNotification('Value created successfully', 'success');
      } catch (err) {
        console.error('Error creating value:', err);
        this._showNotification('Failed to create value', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updateValue() {
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Update the value
        const updatedValue = {
          ...this.valueForm,
          updated_at: new Date().toISOString()
        };
        
        // Update in the list
        this.valuesByType[updatedValue.valueType] = this.valuesByType[updatedValue.valueType].map(value => 
          value.id === updatedValue.id ? updatedValue : value
        );
        
        // If current tab is the same as the value type, update the values
        if (this.activeTab === updatedValue.valueType) {
          this.values = this.valuesByType[updatedValue.valueType];
        }
        
        // Update selected value if it's the one being edited
        if (this.selectedValue && this.selectedValue.id === updatedValue.id) {
          this.selectedValue = updatedValue;
        }
        
        this.closeDialogs();
        this._showNotification('Value updated successfully', 'success');
      } catch (err) {
        console.error('Error updating value:', err);
        this._showNotification('Failed to update value', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  uploadAttachment() {
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        // Generate a new ID
        const id = `attachment-${Date.now()}`;
        
        // Get filename from the file
        const fileName = this.attachmentForm.file ? this.attachmentForm.file.name : 'unknown.file';
        
        // Create new attachment
        const newAttachment = {
          id,
          name: this.attachmentForm.name,
          file_path: `/uploads/${fileName}`,
          valueType: 'attachment',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        // Add to attachments
        this.valuesByType.attachment = [
          newAttachment,
          ...this.valuesByType.attachment
        ];
        
        // If current tab is attachment, update the values
        if (this.activeTab === 'attachment') {
          this.values = this.valuesByType.attachment;
        }
        
        this.closeDialogs();
        this._showNotification('Attachment uploaded successfully', 'success');
      } catch (err) {
        console.error('Error uploading attachment:', err);
        this._showNotification('Failed to upload attachment', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  deleteValue() {
    if (!this.selectedValue) return;
    
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      try {
        const valueType = this.selectedValue.valueType;
        const valueId = this.selectedValue.id;
        
        // Remove from values by type
        this.valuesByType[valueType] = this.valuesByType[valueType].filter(value => 
          value.id !== valueId
        );
        
        // If current tab is the same as the value type, update the values
        if (this.activeTab === valueType) {
          this.values = this.valuesByType[valueType];
        }
        
        // Clear selection if it's the one being deleted
        if (this.selectedValue && this.selectedValue.id === valueId) {
          this.selectedValue = null;
        }
        
        this.closeDialogs();
        this._showNotification('Value deleted successfully', 'success');
      } catch (err) {
        console.error('Error deleting value:', err);
        this._showNotification('Failed to delete value', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
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
  
  _getValueTypeIcon(valueType) {
    switch(valueType) {
      case 'boolean':
        return 'toggle_on';
      case 'integer':
        return 'pin';
      case 'text':
        return 'text_fields';
      case 'decimal':
        return 'percent';
      case 'date':
        return 'event';
      case 'datetime':
        return 'schedule';
      case 'time':
        return 'schedule';
      case 'attachment':
        return 'attachment';
      default:
        return 'category';
    }
  }
  
  _formatValueForDisplay(value, valueType) {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    switch(valueType) {
      case 'boolean':
        return value ? 'True' : 'False';
      case 'integer':
      case 'text':
        return String(value);
      case 'decimal':
        return typeof value === 'number' ? value.toFixed(2) : String(value);
      case 'date':
      case 'datetime':
      case 'time':
        return String(value);
      case 'attachment':
        return value.file_path ? value.file_path.split('/').pop() : 'File';
      default:
        return String(value);
    }
  }
  
  // Render methods
  renderValueDetail() {
    if (!this.selectedValue) return html``;
    
    const value = this.selectedValue;
    
    return html`
      <div class="detail-panel">
        <div class="detail-header">
          <div>
            <h2 class="detail-title">${value.name}</h2>
            <div class="detail-meta">
              <span>Created: ${this.formatRelativeTime(value.created_at)}</span>
              <span> • </span>
              <span>Updated: ${this.formatRelativeTime(value.updated_at)}</span>
            </div>
          </div>
          
          <div>
            <wa-button variant="outlined" @click=${() => this.openEditValueDialog(value)}>
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
            <div class="detail-label">Type</div>
            <div class="detail-value">
              <span class="value-type-badge type-${value.valueType}">
                <wa-icon name="${this._getValueTypeIcon(value.valueType)}" style="margin-right: 4px;"></wa-icon>
                ${value.valueType}
              </span>
            </div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">Value</div>
            <div class="value-display">
              ${value.valueType === 'boolean' 
                ? html`<wa-icon name="${value.value ? 'check_circle' : 'cancel'}" 
                              style="color: ${value.value ? '#4CAF50' : '#F44336'}; margin-right: 8px;"></wa-icon>
                       ${value.value ? 'True' : 'False'}`
                : value.valueType === 'attachment'
                  ? html`<a href="#" @click=${(e) => { e.preventDefault(); this._showNotification('Download started', 'info'); }}>
                         <wa-icon name="download" style="margin-right: 8px;"></wa-icon>
                         ${value.file_path.split('/').pop()}
                       </a>`
                  : this._formatValueForDisplay(value.value, value.valueType)
              }
            </div>
          </div>
          
          <div class="detail-property">
            <div class="detail-label">ID</div>
            <div class="detail-value">${value.id}</div>
          </div>
          
          ${value.valueType === 'attachment' ? html`
            <div class="detail-property">
              <div class="detail-label">File Path</div>
              <div class="detail-value">${value.file_path}</div>
            </div>
          ` : ''}
          
          <div class="detail-actions">
            <wa-button @click=${() => this.openDeleteDialog(value)} color="error" variant="outlined">
              <wa-icon slot="prefix" name="delete"></wa-icon>
              Delete
            </wa-button>
            <wa-button @click=${() => this.openEditValueDialog(value)} color="primary">
              <wa-icon slot="prefix" name="edit"></wa-icon>
              Edit
            </wa-button>
          </div>
        </div>
      </div>
    `;
  }
  
  renderCreateValueDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showCreateValueDialog}
        @close=${this.closeDialogs}
        title="Create Value">
        
        <div class="dialog-content">
          <div class="form-field">
            <wa-input
              label="Name"
              name="name"
              .value=${this.valueForm.name}
              @input=${this.handleValueFormChange}
              required>
            </wa-input>
          </div>
          
          <div class="form-field">
            <wa-select
              label="Value Type"
              name="valueType"
              .value=${this.valueForm.valueType}
              @change=${this.handleValueFormChange}
              disabled>
              <wa-option value="boolean">Boolean</wa-option>
              <wa-option value="integer">Integer</wa-option>
              <wa-option value="text">Text</wa-option>
              <wa-option value="decimal">Decimal</wa-option>
              <wa-option value="date">Date</wa-option>
              <wa-option value="datetime">DateTime</wa-option>
              <wa-option value="time">Time</wa-option>
            </wa-select>
          </div>
          
          ${this.valueForm.valueType === 'boolean' ? html`
            <div class="form-field">
              <wa-switch
                label="Value"
                name="value"
                ?checked=${this.valueForm.value}
                @change=${this.handleValueFormChange}>
              </wa-switch>
            </div>
          ` : this.valueForm.valueType === 'integer' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="number"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'decimal' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="number"
                step="0.01"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'text' ? html`
            <div class="form-field">
              <wa-textarea
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-textarea>
            </div>
          ` : this.valueForm.valueType === 'date' ? html`
            <div class="form-field">
              <wa-date-picker
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @change=${this.handleValueFormChange}
                required>
              </wa-date-picker>
            </div>
          ` : this.valueForm.valueType === 'datetime' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="datetime-local"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'time' ? html`
            <div class="form-field">
              <wa-time-picker
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @change=${this.handleValueFormChange}
                required>
              </wa-time-picker>
            </div>
          ` : ''}
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createValue} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditValueDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showEditValueDialog}
        @close=${this.closeDialogs}
        title="Edit Value">
        
        <div class="dialog-content">
          <div class="form-field">
            <wa-input
              label="Name"
              name="name"
              .value=${this.valueForm.name}
              @input=${this.handleValueFormChange}
              required>
            </wa-input>
          </div>
          
          <div class="form-field">
            <wa-select
              label="Value Type"
              name="valueType"
              .value=${this.valueForm.valueType}
              @change=${this.handleValueFormChange}
              disabled>
              <wa-option value="boolean">Boolean</wa-option>
              <wa-option value="integer">Integer</wa-option>
              <wa-option value="text">Text</wa-option>
              <wa-option value="decimal">Decimal</wa-option>
              <wa-option value="date">Date</wa-option>
              <wa-option value="datetime">DateTime</wa-option>
              <wa-option value="time">Time</wa-option>
            </wa-select>
          </div>
          
          ${this.valueForm.valueType === 'boolean' ? html`
            <div class="form-field">
              <wa-switch
                label="Value"
                name="value"
                ?checked=${this.valueForm.value}
                @change=${this.handleValueFormChange}>
              </wa-switch>
            </div>
          ` : this.valueForm.valueType === 'integer' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="number"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'decimal' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="number"
                step="0.01"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'text' ? html`
            <div class="form-field">
              <wa-textarea
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-textarea>
            </div>
          ` : this.valueForm.valueType === 'date' ? html`
            <div class="form-field">
              <wa-date-picker
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @change=${this.handleValueFormChange}
                required>
              </wa-date-picker>
            </div>
          ` : this.valueForm.valueType === 'datetime' ? html`
            <div class="form-field">
              <wa-input
                label="Value"
                name="value"
                type="datetime-local"
                .value=${this.valueForm.value}
                @input=${this.handleValueFormChange}
                required>
              </wa-input>
            </div>
          ` : this.valueForm.valueType === 'time' ? html`
            <div class="form-field">
              <wa-time-picker
                label="Value"
                name="value"
                .value=${this.valueForm.value}
                @change=${this.handleValueFormChange}
                required>
              </wa-time-picker>
            </div>
          ` : ''}
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updateValue} color="primary">
            Update
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderUploadDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showUploadDialog}
        @close=${this.closeDialogs}
        title="Upload Attachment">
        
        <div class="dialog-content">
          <div class="form-field">
            <wa-input
              label="Name"
              name="name"
              .value=${this.attachmentForm.name}
              @input=${this.handleAttachmentFormChange}
              required>
            </wa-input>
          </div>
          
          <div class="file-upload" @click=${this.triggerFileInput}>
            <wa-icon name="cloud_upload"></wa-icon>
            <div>
              <p>Click to select a file or drag and drop</p>
              <p style="font-size: 14px; color: var(--wa-text-secondary-color);">
                ${this.attachmentForm.file ? this.attachmentForm.file.name : 'No file selected'}
              </p>
            </div>
            <input 
              type="file" 
              id="file-input" 
              style="display: none;" 
              @change=${this.handleFileChange} 
            />
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button 
            @click=${this.uploadAttachment} 
            color="primary"
            ?disabled=${!this.attachmentForm.name || !this.attachmentForm.file}>
            Upload
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderDeleteDialog() {
    if (!this.selectedValue) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showDeleteDialog}
        @close=${this.closeDialogs}
        title="Confirm Deletion">
        
        <div class="dialog-content">
          <p>Are you sure you want to delete the ${this.selectedValue.valueType} value "${this.selectedValue.name}"?</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDialogs} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.deleteValue} color="error">
            Delete
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderValuesGrid(values) {
    if (!values || values.length === 0) {
      return html`
        <div class="empty-state">
          <wa-icon name="${this._getValueTypeIcon(this.activeTab)}"></wa-icon>
          <h3>No ${this.activeTab} values found</h3>
          <p>Create a new ${this.activeTab} value to get started</p>
          ${this.activeTab === 'attachment' 
            ? html`
              <wa-button @click=${this.openUploadDialog} color="primary" style="margin-top: 16px;">
                <wa-icon slot="prefix" name="cloud_upload"></wa-icon>
                Upload Attachment
              </wa-button>
            `
            : html`
              <wa-button @click=${this.openCreateValueDialog} color="primary" style="margin-top: 16px;">
                <wa-icon slot="prefix" name="add"></wa-icon>
                Create ${this.activeTab.charAt(0).toUpperCase() + this.activeTab.slice(1)} Value
              </wa-button>
            `
          }
        </div>
      `;
    }
    
    return html`
      <div class="grid">
        ${values.map(value => html`
          <wa-card class="grid-item" @click=${() => this.selectValue(value)}>
            <div style="padding: 16px;">
              <div class="item-header">
                <h3 class="item-title">${value.name}</h3>
                <div class="item-meta">
                  <span class="value-type-badge type-${value.valueType}">
                    <wa-icon name="${this._getValueTypeIcon(value.valueType)}" style="margin-right: 4px;"></wa-icon>
                    ${value.valueType}
                  </span>
                </div>
              </div>
              
              <div class="item-value">
                ${value.valueType === 'boolean' 
                  ? html`<wa-icon name="${value.value ? 'check_circle' : 'cancel'}" 
                                style="color: ${value.value ? '#4CAF50' : '#F44336'}; margin-right: 8px;"></wa-icon>
                         ${value.value ? 'True' : 'False'}`
                  : value.valueType === 'attachment'
                    ? html`<wa-icon name="attachment" style="margin-right: 8px;"></wa-icon>
                           ${value.file_path.split('/').pop()}`
                    : this._formatValueForDisplay(value.value, value.valueType)
                }
              </div>
              
              <div style="margin-top: 8px; font-size: 12px; color: var(--wa-text-secondary-color);">
                Updated ${this.formatRelativeTime(value.updated_at)}
              </div>
            </div>
          </wa-card>
        `)}
      </div>
    `;
  }
  
  render() {
    return html`
      <div class="container">
        <div class="header">
          <h1 class="title">Values Manager</h1>
          <p class="subtitle">Manage typed values for attributes and other entities</p>
        </div>
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="boolean">Boolean</wa-tab>
          <wa-tab value="integer">Integer</wa-tab>
          <wa-tab value="text">Text</wa-tab>
          <wa-tab value="decimal">Decimal</wa-tab>
          <wa-tab value="date">Date</wa-tab>
          <wa-tab value="datetime">DateTime</wa-tab>
          <wa-tab value="time">Time</wa-tab>
          <wa-tab value="attachment">Attachments</wa-tab>
        </wa-tabs>
        
        <div class="tab-content">
          <div class="filter-bar">
            <wa-input 
              class="filter-input"
              placeholder="Search values..."
              .value=${this.searchTerm}
              @input=${this.handleSearchChange}>
              <wa-icon slot="prefix" name="search"></wa-icon>
            </wa-input>
            
            ${this.activeTab === 'attachment' 
              ? html`
                <wa-button @click=${this.openUploadDialog} color="primary">
                  <wa-icon slot="prefix" name="cloud_upload"></wa-icon>
                  Upload
                </wa-button>
              `
              : html`
                <wa-button @click=${this.openCreateValueDialog} color="primary">
                  <wa-icon slot="prefix" name="add"></wa-icon>
                  Create
                </wa-button>
              `
            }
          </div>
          
          ${this.renderValuesGrid(this.values)}
          
          ${this.selectedValue ? this.renderValueDetail() : ''}
        </div>
        
        ${this.renderCreateValueDialog()}
        ${this.renderEditValueDialog()}
        ${this.renderUploadDialog()}
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

customElements.define('wa-values-manager', WebAwesomeValuesManager);