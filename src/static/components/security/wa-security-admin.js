import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
import '@webcomponents/awesome/wa-checkbox.js';
import '@webcomponents/awesome/wa-icon.js';
import '@webcomponents/awesome/wa-spinner.js';
import '@webcomponents/awesome/wa-divider.js';
import '@webcomponents/awesome/wa-alert.js';
import '@webcomponents/awesome/wa-tabs.js';
import '@webcomponents/awesome/wa-tab.js';
import '@webcomponents/awesome/wa-tab-panel.js';
import '@webcomponents/awesome/wa-badge.js';
import '@webcomponents/awesome/wa-dialog.js';
import '@webcomponents/awesome/wa-table.js';
import '@webcomponents/awesome/wa-switch.js';
import '@webcomponents/awesome/wa-date-picker.js';

/**
 * @element wa-security-admin
 * @description Security administration dashboard for UNO framework
 */
export class WebAwesomeSecurityAdmin extends LitElement {
  static get properties() {
    return {
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      
      // Audit logs data
      auditLogs: { type: Array },
      selectedLog: { type: Object },
      
      // Encryption keys
      encryptionKeys: { type: Array },
      selectedKey: { type: Object },
      
      // Security policies
      securityPolicies: { type: Array },
      selectedPolicy: { type: Object },
      
      // Authentication settings
      authSettings: { type: Object },
      
      // Filters
      eventTypeFilter: { type: String },
      userFilter: { type: String },
      dateRangeStart: { type: String },
      dateRangeEnd: { type: String },
      searchTerm: { type: String },
      
      // Pagination
      page: { type: Number },
      pageSize: { type: Number },
      totalItems: { type: Number },
      
      // Dialogs
      showLogDetailDialog: { type: Boolean },
      showCreateKeyDialog: { type: Boolean },
      showEditPolicyDialog: { type: Boolean },
      showDeleteKeyDialog: { type: Boolean },
      showConfirmRevokeDialog: { type: Boolean },
      
      // Forms
      keyForm: { type: Object },
      policyForm: { type: Object }
    };
  }
  
  static get styles() {
    return css`
      :host {
        display: block;
        --security-admin-bg: var(--wa-background-color, #f5f5f5);
        --security-admin-padding: 20px;
      }
      
      .container {
        padding: var(--security-admin-padding);
        background-color: var(--security-admin-bg);
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
        flex-wrap: wrap;
      }
      
      .filter-input {
        flex: 1;
        min-width: 200px;
      }
      
      .filter-select {
        min-width: 150px;
      }
      
      .table-container {
        width: 100%;
        overflow-x: auto;
      }
      
      .actions {
        display: flex;
        gap: 8px;
      }
      
      .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
      }
      
      .status-active {
        background-color: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
      }
      
      .status-expired {
        background-color: rgba(255, 152, 0, 0.1);
        color: #FF9800;
      }
      
      .status-revoked {
        background-color: rgba(244, 67, 54, 0.1);
        color: #F44336;
      }
      
      .event-type-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
      }
      
      .event-authentication {
        background-color: rgba(33, 150, 243, 0.1);
        color: #2196F3;
      }
      
      .event-access {
        background-color: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
      }
      
      .event-data {
        background-color: rgba(156, 39, 176, 0.1);
        color: #9C27B0;
      }
      
      .event-security {
        background-color: rgba(244, 67, 54, 0.1);
        color: #F44336;
      }
      
      .event-system {
        background-color: rgba(255, 152, 0, 0.1);
        color: #FF9800;
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
      
      .detail-section {
        margin-bottom: 24px;
      }
      
      .detail-header {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 12px;
      }
      
      .detail-property {
        display: flex;
        margin-bottom: 8px;
      }
      
      .detail-label {
        font-weight: 500;
        width: 150px;
      }
      
      .detail-value {
        flex: 1;
      }
      
      .pagination {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 8px;
        margin-top: 16px;
      }
      
      .pagination-info {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
      }
      
      .code-block {
        background-color: var(--wa-code-bg, #f5f5f5);
        border-radius: 4px;
        padding: 16px;
        font-family: monospace;
        white-space: pre-wrap;
        overflow: auto;
        max-height: 300px;
        width: 100%;
        box-sizing: border-box;
      }
      
      .date-filter {
        display: flex;
        gap: 8px;
        align-items: center;
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
      
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      
      .panel-title {
        font-size: 18px;
        font-weight: 500;
        margin: 0;
      }
      
      .settings-section {
        margin-bottom: 24px;
      }
      
      .settings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 24px;
      }
      
      .setting-card {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 20px;
      }
      
      .setting-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      
      .setting-title {
        font-size: 16px;
        font-weight: 500;
        margin: 0;
      }
      
      .setting-description {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 8px 0 16px 0;
      }
      
      .setting-value {
        margin-top: 12px;
      }
      
      .security-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      
      .stat-card {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 20px;
        text-align: center;
      }
      
      .stat-value {
        font-size: 32px;
        font-weight: 700;
        margin: 8px 0;
      }
      
      .stat-label {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        text-transform: uppercase;
      }
      
      .key-info {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .key-icon {
        color: var(--wa-primary-color, #3f51b5);
      }
      
      .key-id {
        font-family: monospace;
        background-color: var(--wa-code-bg, #f5f5f5);
        padding: 2px 4px;
        border-radius: 4px;
        font-size: 14px;
      }
    `;
  }

  constructor() {
    super();
    this.activeTab = 'audit';
    this.loading = false;
    this.error = null;
    
    this.auditLogs = [];
    this.selectedLog = null;
    
    this.encryptionKeys = [];
    this.selectedKey = null;
    
    this.securityPolicies = [];
    this.selectedPolicy = null;
    
    this.authSettings = {
      passwordMinLength: 8,
      passwordRequireUppercase: true,
      passwordRequireLowercase: true,
      passwordRequireNumbers: true,
      passwordRequireSpecial: true,
      passwordExpiryDays: 90,
      maxLoginAttempts: 5,
      lockoutDuration: 15, // minutes
      enableTwoFactor: true,
      sessionTimeout: 30, // minutes
      rememberMeDuration: 14, // days
      ssoEnabled: false,
      samlIdpUrl: ''
    };
    
    this.eventTypeFilter = '';
    this.userFilter = '';
    this.dateRangeStart = '';
    this.dateRangeEnd = '';
    this.searchTerm = '';
    
    this.page = 1;
    this.pageSize = 10;
    this.totalItems = 0;
    
    this.showLogDetailDialog = false;
    this.showCreateKeyDialog = false;
    this.showEditPolicyDialog = false;
    this.showDeleteKeyDialog = false;
    this.showConfirmRevokeDialog = false;
    
    this.keyForm = this._getDefaultKeyForm();
    this.policyForm = this._getDefaultPolicyForm();
    
    // Load mock data
    this._loadMockData();
  }
  
  connectedCallback() {
    super.connectedCallback();
    // In a real implementation, this would fetch data from the API
  }
  
  _getDefaultKeyForm() {
    return {
      name: '',
      description: '',
      type: 'aes-256',
      purpose: 'data-encryption',
      validityPeriod: 365, // days
      autoRotate: false
    };
  }
  
  _getDefaultPolicyForm() {
    return {
      id: '',
      name: '',
      description: '',
      enabled: true,
      settings: {}
    };
  }
  
  _loadMockData() {
    // Generate mock audit logs
    this.auditLogs = this._generateMockAuditLogs(50);
    
    // Generate mock encryption keys
    this.encryptionKeys = this._generateMockEncryptionKeys(5);
    
    // Generate mock security policies
    this.securityPolicies = this._generateMockSecurityPolicies();
    
    // Update total items for pagination
    this.totalItems = this.auditLogs.length;
  }
  
  _generateMockAuditLogs(count) {
    const eventTypes = ['authentication', 'access', 'data', 'security', 'system'];
    const users = ['admin@example.com', 'user1@example.com', 'user2@example.com', 'system'];
    const actions = {
      'authentication': ['login', 'logout', 'password_change', 'mfa_enabled', 'mfa_disabled'],
      'access': ['access_granted', 'access_denied', 'permission_changed'],
      'data': ['data_created', 'data_read', 'data_updated', 'data_deleted'],
      'security': ['key_created', 'key_rotated', 'key_revoked', 'policy_changed'],
      'system': ['system_started', 'system_stopped', 'backup_created', 'error']
    };
    const statuses = ['success', 'failure', 'warning'];
    const logs = [];
    
    const now = new Date();
    
    for (let i = 0; i < count; i++) {
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
      const user = users[Math.floor(Math.random() * users.length)];
      const action = actions[eventType][Math.floor(Math.random() * actions[eventType].length)];
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      const timestamp = new Date(now - Math.random() * 86400000 * 30); // Random time in last 30 days
      
      logs.push({
        id: `log-${i + 1}`,
        eventType,
        action,
        user,
        timestamp: timestamp.toISOString(),
        status,
        ip: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
        details: {
          resource: `/api/v1/${eventType.toLowerCase()}/${Math.floor(Math.random() * 1000)}`,
          method: ['GET', 'POST', 'PUT', 'DELETE'][Math.floor(Math.random() * 4)],
          additionalInfo: `Sample info for ${action}`
        }
      });
    }
    
    return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }
  
  _generateMockEncryptionKeys(count) {
    const keyTypes = ['aes-256', 'rsa-2048', 'ed25519'];
    const purposes = ['data-encryption', 'token-signing', 'api-authentication', 'document-signing'];
    const statuses = ['active', 'expired', 'revoked'];
    const keys = [];
    
    const now = new Date();
    
    for (let i = 0; i < count; i++) {
      const created = new Date(now - Math.random() * 86400000 * 365); // Random time in last year
      const validityPeriod = Math.floor(Math.random() * 365) + 90; // 90-455 days
      const expires = new Date(created.getTime() + validityPeriod * 86400000);
      const type = keyTypes[Math.floor(Math.random() * keyTypes.length)];
      const purpose = purposes[Math.floor(Math.random() * purposes.length)];
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      
      keys.push({
        id: `key-${i + 1}`,
        name: `${type.toUpperCase()} ${purpose} key ${i + 1}`,
        description: `${purpose} key using ${type} algorithm`,
        type,
        purpose,
        fingerprint: `${type}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}`,
        created: created.toISOString(),
        expires: expires.toISOString(),
        status,
        lastRotated: i % 2 === 0 ? new Date(created.getTime() + Math.random() * (now - created)).toISOString() : null,
        autoRotate: i % 3 === 0 // Every third key has auto-rotation enabled
      });
    }
    
    return keys;
  }
  
  _generateRandomHex(length) {
    let result = '';
    const characters = '0123456789ABCDEF';
    for (let i = 0; i < length; i++) {
      result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
  }
  
  _generateMockSecurityPolicies() {
    return [
      {
        id: 'policy-1',
        name: 'Password Policy',
        description: 'Controls password requirements and rotation schedule',
        enabled: true,
        settings: {
          minLength: 8,
          requireUppercase: true,
          requireLowercase: true,
          requireNumbers: true,
          requireSpecial: true,
          historyCount: 5,
          expiryDays: 90
        },
        created: new Date(Date.now() - 365 * 86400000).toISOString(),
        updated: new Date(Date.now() - 30 * 86400000).toISOString()
      },
      {
        id: 'policy-2',
        name: 'Login Security Policy',
        description: 'Controls login attempts and account lockout',
        enabled: true,
        settings: {
          maxLoginAttempts: 5,
          lockoutDuration: 15, // minutes
          requireCaptcha: true,
          requireMfaForAdmin: true
        },
        created: new Date(Date.now() - 300 * 86400000).toISOString(),
        updated: new Date(Date.now() - 45 * 86400000).toISOString()
      },
      {
        id: 'policy-3',
        name: 'Data Access Policy',
        description: 'Controls data access and audit requirements',
        enabled: true,
        settings: {
          auditAllAccess: true,
          requireJustification: true,
          maskSensitiveData: true,
          encryptSensitiveData: true
        },
        created: new Date(Date.now() - 250 * 86400000).toISOString(),
        updated: new Date(Date.now() - 15 * 86400000).toISOString()
      }
    ];
  }
  
  handleTabChange(e) {
    this.activeTab = e.detail.value;
    this.page = 1; // Reset to first page on tab change
    
    // Update total items based on the selected tab
    if (this.activeTab === 'audit') {
      this.totalItems = this.getFilteredLogs().length;
    }
  }
  
  handleSearchChange(e) {
    this.searchTerm = e.target.value;
    this.page = 1; // Reset to first page when search changes
    this.totalItems = this.getFilteredLogs().length;
  }
  
  handleEventTypeFilterChange(e) {
    this.eventTypeFilter = e.target.value;
    this.page = 1; // Reset to first page when filter changes
    this.totalItems = this.getFilteredLogs().length;
  }
  
  handleUserFilterChange(e) {
    this.userFilter = e.target.value;
    this.page = 1; // Reset to first page when filter changes
    this.totalItems = this.getFilteredLogs().length;
  }
  
  handleDateRangeStartChange(e) {
    this.dateRangeStart = e.target.value;
    this.page = 1; // Reset to first page when filter changes
    this.totalItems = this.getFilteredLogs().length;
  }
  
  handleDateRangeEndChange(e) {
    this.dateRangeEnd = e.target.value;
    this.page = 1; // Reset to first page when filter changes
    this.totalItems = this.getFilteredLogs().length;
  }
  
  handlePageChange(newPage) {
    this.page = newPage;
  }
  
  handlePageSizeChange(e) {
    this.pageSize = parseInt(e.target.value, 10);
    this.page = 1; // Reset to first page when page size changes
  }
  
  openLogDetail(log) {
    this.selectedLog = log;
    this.showLogDetailDialog = true;
  }
  
  closeLogDetail() {
    this.showLogDetailDialog = false;
    this.selectedLog = null;
  }
  
  openCreateKeyDialog() {
    this.keyForm = this._getDefaultKeyForm();
    this.showCreateKeyDialog = true;
  }
  
  closeCreateKeyDialog() {
    this.showCreateKeyDialog = false;
  }
  
  openEditPolicyDialog(policy) {
    this.selectedPolicy = policy;
    this.policyForm = {
      id: policy.id,
      name: policy.name,
      description: policy.description,
      enabled: policy.enabled,
      settings: { ...policy.settings }
    };
    this.showEditPolicyDialog = true;
  }
  
  closeEditPolicyDialog() {
    this.showEditPolicyDialog = false;
    this.selectedPolicy = null;
  }
  
  openDeleteKeyDialog(key) {
    this.selectedKey = key;
    this.showDeleteKeyDialog = true;
  }
  
  closeDeleteKeyDialog() {
    this.showDeleteKeyDialog = false;
    this.selectedKey = null;
  }
  
  openConfirmRevokeDialog(key) {
    this.selectedKey = key;
    this.showConfirmRevokeDialog = true;
  }
  
  closeConfirmRevokeDialog() {
    this.showConfirmRevokeDialog = false;
    this.selectedKey = null;
  }
  
  handleKeyFormChange(e) {
    const field = e.target.name;
    let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    if (field === 'validityPeriod') {
      value = parseInt(value, 10);
    }
    
    this.keyForm = {
      ...this.keyForm,
      [field]: value
    };
  }
  
  handlePolicyFormChange(e) {
    const field = e.target.name;
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    
    if (field.startsWith('settings.')) {
      const settingKey = field.split('.')[1];
      this.policyForm = {
        ...this.policyForm,
        settings: {
          ...this.policyForm.settings,
          [settingKey]: e.target.type === 'number' ? parseInt(value, 10) : value
        }
      };
    } else {
      this.policyForm = {
        ...this.policyForm,
        [field]: value
      };
    }
  }
  
  handleAuthSettingChange(e) {
    const field = e.target.name;
    const value = e.target.type === 'checkbox' ? e.target.checked : 
                  e.target.type === 'number' ? parseInt(e.target.value, 10) : 
                  e.target.value;
    
    this.authSettings = {
      ...this.authSettings,
      [field]: value
    };
    
    // In a real implementation, this would update the settings via API
    this._showNotification(`Authentication setting "${field}" updated.`, 'success');
  }
  
  createEncryptionKey() {
    // Simulate API call to create key
    this.loading = true;
    
    setTimeout(() => {
      try {
        const newKey = {
          ...this.keyForm,
          id: `key-${Date.now()}`,
          fingerprint: `${this.keyForm.type}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}`,
          created: new Date().toISOString(),
          expires: new Date(Date.now() + this.keyForm.validityPeriod * 86400000).toISOString(),
          status: 'active',
          lastRotated: null
        };
        
        this.encryptionKeys = [newKey, ...this.encryptionKeys];
        this.closeCreateKeyDialog();
        this._showNotification(`Encryption key "${newKey.name}" created successfully.`, 'success');
        
        // Add to audit log
        this.auditLogs.unshift({
          id: `log-${Date.now()}`,
          eventType: 'security',
          action: 'key_created',
          user: 'admin@example.com',
          timestamp: new Date().toISOString(),
          status: 'success',
          ip: '127.0.0.1',
          userAgent: navigator.userAgent,
          details: {
            resource: `/api/v1/security/keys/${newKey.id}`,
            method: 'POST',
            additionalInfo: `Created ${newKey.type} key for ${newKey.purpose}`
          }
        });
        
      } catch (err) {
        console.error('Error creating key:', err);
        this._showNotification('Failed to create encryption key', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  updatePolicy() {
    // Simulate API call to update policy
    this.loading = true;
    
    setTimeout(() => {
      try {
        const updatedPolicy = {
          ...this.policyForm,
          updated: new Date().toISOString()
        };
        
        this.securityPolicies = this.securityPolicies.map(p => 
          p.id === updatedPolicy.id ? updatedPolicy : p
        );
        
        this.closeEditPolicyDialog();
        this._showNotification(`Security policy "${updatedPolicy.name}" updated successfully.`, 'success');
        
        // Add to audit log
        this.auditLogs.unshift({
          id: `log-${Date.now()}`,
          eventType: 'security',
          action: 'policy_changed',
          user: 'admin@example.com',
          timestamp: new Date().toISOString(),
          status: 'success',
          ip: '127.0.0.1',
          userAgent: navigator.userAgent,
          details: {
            resource: `/api/v1/security/policies/${updatedPolicy.id}`,
            method: 'PUT',
            additionalInfo: `Updated policy: ${updatedPolicy.name}`
          }
        });
        
      } catch (err) {
        console.error('Error updating policy:', err);
        this._showNotification('Failed to update security policy', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  deleteKey() {
    // Simulate API call to delete key
    this.loading = true;
    
    setTimeout(() => {
      try {
        this.encryptionKeys = this.encryptionKeys.filter(k => k.id !== this.selectedKey.id);
        this.closeDeleteKeyDialog();
        this._showNotification(`Encryption key "${this.selectedKey.name}" deleted successfully.`, 'success');
        
        // Add to audit log
        this.auditLogs.unshift({
          id: `log-${Date.now()}`,
          eventType: 'security',
          action: 'key_deleted',
          user: 'admin@example.com',
          timestamp: new Date().toISOString(),
          status: 'success',
          ip: '127.0.0.1',
          userAgent: navigator.userAgent,
          details: {
            resource: `/api/v1/security/keys/${this.selectedKey.id}`,
            method: 'DELETE',
            additionalInfo: `Deleted ${this.selectedKey.type} key: ${this.selectedKey.name}`
          }
        });
        
      } catch (err) {
        console.error('Error deleting key:', err);
        this._showNotification('Failed to delete encryption key', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  revokeKey() {
    // Simulate API call to revoke key
    this.loading = true;
    
    setTimeout(() => {
      try {
        this.encryptionKeys = this.encryptionKeys.map(k => {
          if (k.id === this.selectedKey.id) {
            return { ...k, status: 'revoked' };
          }
          return k;
        });
        
        this.closeConfirmRevokeDialog();
        this._showNotification(`Encryption key "${this.selectedKey.name}" revoked successfully.`, 'success');
        
        // Add to audit log
        this.auditLogs.unshift({
          id: `log-${Date.now()}`,
          eventType: 'security',
          action: 'key_revoked',
          user: 'admin@example.com',
          timestamp: new Date().toISOString(),
          status: 'success',
          ip: '127.0.0.1',
          userAgent: navigator.userAgent,
          details: {
            resource: `/api/v1/security/keys/${this.selectedKey.id}/revoke`,
            method: 'POST',
            additionalInfo: `Revoked ${this.selectedKey.type} key: ${this.selectedKey.name}`
          }
        });
        
      } catch (err) {
        console.error('Error revoking key:', err);
        this._showNotification('Failed to revoke encryption key', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
  }
  
  rotateKey(key) {
    // Simulate API call to rotate key
    this.loading = true;
    
    setTimeout(() => {
      try {
        this.encryptionKeys = this.encryptionKeys.map(k => {
          if (k.id === key.id) {
            return { 
              ...k, 
              lastRotated: new Date().toISOString(),
              fingerprint: `${k.type}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}:${this._generateRandomHex(8)}`
            };
          }
          return k;
        });
        
        this._showNotification(`Encryption key "${key.name}" rotated successfully.`, 'success');
        
        // Add to audit log
        this.auditLogs.unshift({
          id: `log-${Date.now()}`,
          eventType: 'security',
          action: 'key_rotated',
          user: 'admin@example.com',
          timestamp: new Date().toISOString(),
          status: 'success',
          ip: '127.0.0.1',
          userAgent: navigator.userAgent,
          details: {
            resource: `/api/v1/security/keys/${key.id}/rotate`,
            method: 'POST',
            additionalInfo: `Rotated ${key.type} key: ${key.name}`
          }
        });
        
      } catch (err) {
        console.error('Error rotating key:', err);
        this._showNotification('Failed to rotate encryption key', 'error');
      } finally {
        this.loading = false;
      }
    }, 500);
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
    if (!dateString) return 'N/A';
    
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
  
  formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
  }
  
  getFilteredLogs() {
    let logs = [...this.auditLogs];
    
    // Apply event type filter
    if (this.eventTypeFilter) {
      logs = logs.filter(log => log.eventType === this.eventTypeFilter);
    }
    
    // Apply user filter
    if (this.userFilter) {
      logs = logs.filter(log => log.user === this.userFilter);
    }
    
    // Apply date range filter
    if (this.dateRangeStart) {
      const startDate = new Date(this.dateRangeStart);
      logs = logs.filter(log => new Date(log.timestamp) >= startDate);
    }
    
    if (this.dateRangeEnd) {
      const endDate = new Date(this.dateRangeEnd);
      endDate.setHours(23, 59, 59, 999); // End of the day
      logs = logs.filter(log => new Date(log.timestamp) <= endDate);
    }
    
    // Apply search filter
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      logs = logs.filter(log => 
        log.action.toLowerCase().includes(term) || 
        log.user.toLowerCase().includes(term) ||
        log.id.toLowerCase().includes(term) ||
        log.ip.toLowerCase().includes(term)
      );
    }
    
    return logs;
  }
  
  getPaginatedLogs() {
    const filteredLogs = this.getFilteredLogs();
    
    const startIndex = (this.page - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    
    return filteredLogs.slice(startIndex, endIndex);
  }
  
  getActiveUsers() {
    // Get unique users from audit logs in the last 24 hours
    const oneDayAgo = new Date(Date.now() - 86400000);
    const recentLogs = this.auditLogs.filter(log => 
      new Date(log.timestamp) >= oneDayAgo && 
      log.eventType === 'authentication' && 
      log.action === 'login' &&
      log.status === 'success'
    );
    
    // Count unique users
    const uniqueUsers = new Set();
    recentLogs.forEach(log => uniqueUsers.add(log.user));
    
    return uniqueUsers.size;
  }
  
  getFailedLoginAttempts() {
    // Count failed login attempts in the last 24 hours
    const oneDayAgo = new Date(Date.now() - 86400000);
    return this.auditLogs.filter(log => 
      new Date(log.timestamp) >= oneDayAgo && 
      log.eventType === 'authentication' && 
      log.action === 'login' &&
      log.status === 'failure'
    ).length;
  }
  
  getSecurityIncidents() {
    // Count security incidents in the last 7 days
    const sevenDaysAgo = new Date(Date.now() - 7 * 86400000);
    return this.auditLogs.filter(log => 
      new Date(log.timestamp) >= sevenDaysAgo && 
      log.eventType === 'security' &&
      log.status === 'failure'
    ).length;
  }
  
  // Render methods for different sections
  renderFilterBar() {
    // Extract unique users from logs
    const users = [...new Set(this.auditLogs.map(log => log.user))];
    
    return html`
      <div class="filter-bar">
        <wa-input 
          class="filter-input"
          placeholder="Search logs..."
          .value=${this.searchTerm}
          @input=${this.handleSearchChange}>
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-select
          class="filter-select"
          placeholder="Event Type"
          .value=${this.eventTypeFilter}
          @change=${this.handleEventTypeFilterChange}>
          <wa-option value="">All Events</wa-option>
          <wa-option value="authentication">Authentication</wa-option>
          <wa-option value="access">Access</wa-option>
          <wa-option value="data">Data</wa-option>
          <wa-option value="security">Security</wa-option>
          <wa-option value="system">System</wa-option>
        </wa-select>
        
        <wa-select
          class="filter-select"
          placeholder="User"
          .value=${this.userFilter}
          @change=${this.handleUserFilterChange}>
          <wa-option value="">All Users</wa-option>
          ${users.map(user => html`
            <wa-option value=${user}>${user}</wa-option>
          `)}
        </wa-select>
        
        <div class="date-filter">
          <wa-date-picker
            placeholder="From"
            .value=${this.dateRangeStart}
            @change=${this.handleDateRangeStartChange}>
          </wa-date-picker>
          
          <span>-</span>
          
          <wa-date-picker
            placeholder="To"
            .value=${this.dateRangeEnd}
            @change=${this.handleDateRangeEndChange}>
          </wa-date-picker>
        </div>
      </div>
    `;
  }
  
  renderSecurityStatistics() {
    return html`
      <div class="security-stats">
        <div class="stat-card">
          <div class="stat-label">Active Keys</div>
          <div class="stat-value">${this.encryptionKeys.filter(k => k.status === 'active').length}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Active Users (24h)</div>
          <div class="stat-value">${this.getActiveUsers()}</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Failed Logins (24h)</div>
          <div class="stat-value" style="color: ${this.getFailedLoginAttempts() > 10 ? '#F44336' : '#FF9800'}">
            ${this.getFailedLoginAttempts()}
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Security Incidents (7d)</div>
          <div class="stat-value" style="color: ${this.getSecurityIncidents() > 0 ? '#F44336' : '#4CAF50'}">
            ${this.getSecurityIncidents()}
          </div>
        </div>
      </div>
    `;
  }
  
  renderAuditLogTable() {
    const logs = this.getPaginatedLogs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Timestamp</wa-table-cell>
              <wa-table-cell>Event Type</wa-table-cell>
              <wa-table-cell>Action</wa-table-cell>
              <wa-table-cell>User</wa-table-cell>
              <wa-table-cell>Status</wa-table-cell>
              <wa-table-cell>IP Address</wa-table-cell>
              <wa-table-cell>Details</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${logs.map(log => html`
              <wa-table-row @click=${() => this.openLogDetail(log)}>
                <wa-table-cell>${this.formatRelativeTime(log.timestamp)}</wa-table-cell>
                <wa-table-cell>
                  <span class="event-type-badge event-${log.eventType}">
                    ${log.eventType}
                  </span>
                </wa-table-cell>
                <wa-table-cell>${log.action.replace(/_/g, ' ')}</wa-table-cell>
                <wa-table-cell>${log.user}</wa-table-cell>
                <wa-table-cell>
                  <wa-badge 
                    color=${log.status === 'success' ? 'success' : log.status === 'warning' ? 'warning' : 'error'}>
                    ${log.status}
                  </wa-badge>
                </wa-table-cell>
                <wa-table-cell>${log.ip}</wa-table-cell>
                <wa-table-cell>
                  <wa-button variant="text" size="small">
                    <wa-icon name="info"></wa-icon>
                  </wa-button>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
      </div>
    `;
  }
  
  renderEncryptionKeysTable() {
    return html`
      <div class="panel-header">
        <h2 class="panel-title">Encryption Keys</h2>
        <wa-button @click=${this.openCreateKeyDialog} color="primary">
          <wa-icon slot="prefix" name="add"></wa-icon>
          Create Key
        </wa-button>
      </div>
      
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Key</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Purpose</wa-table-cell>
              <wa-table-cell>Created</wa-table-cell>
              <wa-table-cell>Expires</wa-table-cell>
              <wa-table-cell>Status</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${this.encryptionKeys.map(key => html`
              <wa-table-row>
                <wa-table-cell>
                  <div class="key-info">
                    <wa-icon class="key-icon" name="vpn_key"></wa-icon>
                    <div>
                      <div style="font-weight: 500;">${key.name}</div>
                      <div class="key-id">${key.fingerprint}</div>
                    </div>
                  </div>
                </wa-table-cell>
                <wa-table-cell>${key.type}</wa-table-cell>
                <wa-table-cell>${key.purpose}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(key.created)}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(key.expires)}</wa-table-cell>
                <wa-table-cell>
                  <span class="status-badge status-${key.status}">
                    ${key.status}
                  </span>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="actions">
                    ${key.status === 'active' ? html`
                      <wa-button variant="text" size="small" @click=${() => this.rotateKey(key)}>
                        <wa-icon name="refresh"></wa-icon>
                      </wa-button>
                      <wa-button variant="text" size="small" @click=${() => this.openConfirmRevokeDialog(key)}>
                        <wa-icon name="block"></wa-icon>
                      </wa-button>
                    ` : ''}
                    <wa-button variant="text" size="small" @click=${() => this.openDeleteKeyDialog(key)}>
                      <wa-icon name="delete"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
      </div>
    `;
  }
  
  renderSecurityPoliciesTable() {
    return html`
      <div class="panel-header">
        <h2 class="panel-title">Security Policies</h2>
      </div>
      
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Policy</wa-table-cell>
              <wa-table-cell>Description</wa-table-cell>
              <wa-table-cell>Updated</wa-table-cell>
              <wa-table-cell>Status</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${this.securityPolicies.map(policy => html`
              <wa-table-row>
                <wa-table-cell>
                  <div style="font-weight: 500;">${policy.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${policy.id}</div>
                </wa-table-cell>
                <wa-table-cell>${policy.description}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(policy.updated)}</wa-table-cell>
                <wa-table-cell>
                  <wa-badge color=${policy.enabled ? 'success' : 'default'}>
                    ${policy.enabled ? 'Enabled' : 'Disabled'}
                  </wa-badge>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="actions">
                    <wa-button variant="text" size="small" @click=${() => this.openEditPolicyDialog(policy)}>
                      <wa-icon name="edit"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
      </div>
    `;
  }
  
  renderAuthenticationSettings() {
    return html`
      <div class="panel-header">
        <h2 class="panel-title">Authentication Settings</h2>
      </div>
      
      <div class="settings-grid">
        <div class="setting-card">
          <div class="setting-header">
            <h3 class="setting-title">Password Requirements</h3>
          </div>
          <div class="setting-description">
            Configure the password requirements for all users.
          </div>
          
          <div class="setting-value">
            <wa-input
              label="Minimum Length"
              name="passwordMinLength"
              type="number"
              min="6"
              max="64"
              .value=${this.authSettings.passwordMinLength}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
            
            <wa-checkbox
              label="Require Uppercase Letters"
              name="passwordRequireUppercase"
              ?checked=${this.authSettings.passwordRequireUppercase}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Require Lowercase Letters"
              name="passwordRequireLowercase"
              ?checked=${this.authSettings.passwordRequireLowercase}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Require Numbers"
              name="passwordRequireNumbers"
              ?checked=${this.authSettings.passwordRequireNumbers}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
            
            <wa-checkbox
              label="Require Special Characters"
              name="passwordRequireSpecial"
              ?checked=${this.authSettings.passwordRequireSpecial}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
            
            <wa-input
              label="Password Expiry (days)"
              name="passwordExpiryDays"
              type="number"
              min="0"
              max="365"
              .value=${this.authSettings.passwordExpiryDays}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
          </div>
        </div>
        
        <div class="setting-card">
          <div class="setting-header">
            <h3 class="setting-title">Login Security</h3>
          </div>
          <div class="setting-description">
            Configure login attempts and lockout settings.
          </div>
          
          <div class="setting-value">
            <wa-input
              label="Max Login Attempts"
              name="maxLoginAttempts"
              type="number"
              min="1"
              max="20"
              .value=${this.authSettings.maxLoginAttempts}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
            
            <wa-input
              label="Lockout Duration (minutes)"
              name="lockoutDuration"
              type="number"
              min="1"
              max="1440"
              .value=${this.authSettings.lockoutDuration}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
            
            <wa-checkbox
              label="Enable Two-Factor Authentication"
              name="enableTwoFactor"
              ?checked=${this.authSettings.enableTwoFactor}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
          </div>
        </div>
        
        <div class="setting-card">
          <div class="setting-header">
            <h3 class="setting-title">Session Management</h3>
          </div>
          <div class="setting-description">
            Configure session timeout and persistence settings.
          </div>
          
          <div class="setting-value">
            <wa-input
              label="Session Timeout (minutes)"
              name="sessionTimeout"
              type="number"
              min="1"
              max="1440"
              .value=${this.authSettings.sessionTimeout}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
            
            <wa-input
              label="Remember Me Duration (days)"
              name="rememberMeDuration"
              type="number"
              min="1"
              max="90"
              .value=${this.authSettings.rememberMeDuration}
              @change=${this.handleAuthSettingChange}>
            </wa-input>
          </div>
        </div>
        
        <div class="setting-card">
          <div class="setting-header">
            <h3 class="setting-title">Single Sign-On</h3>
          </div>
          <div class="setting-description">
            Configure SSO integration settings.
          </div>
          
          <div class="setting-value">
            <wa-checkbox
              label="Enable SSO"
              name="ssoEnabled"
              ?checked=${this.authSettings.ssoEnabled}
              @change=${this.handleAuthSettingChange}>
            </wa-checkbox>
            
            <wa-input
              label="SAML IdP URL"
              name="samlIdpUrl"
              .value=${this.authSettings.samlIdpUrl}
              ?disabled=${!this.authSettings.ssoEnabled}
              @input=${this.handleAuthSettingChange}>
            </wa-input>
          </div>
        </div>
      </div>
    `;
  }
  
  renderPagination() {
    const totalPages = Math.ceil(this.totalItems / this.pageSize);
    
    return html`
      <div class="pagination">
        <span class="pagination-info">
          Showing ${Math.min((this.page - 1) * this.pageSize + 1, this.totalItems)}-${Math.min(this.page * this.pageSize, this.totalItems)} of ${this.totalItems} items
        </span>
        
        <wa-select
          .value=${this.pageSize.toString()}
          @change=${this.handlePageSizeChange}
          style="width: 80px;">
          <wa-option value="10">10</wa-option>
          <wa-option value="25">25</wa-option>
          <wa-option value="50">50</wa-option>
          <wa-option value="100">100</wa-option>
        </wa-select>
        
        <wa-button
          variant="text"
          @click=${() => this.handlePageChange(1)}
          ?disabled=${this.page === 1}>
          <wa-icon name="first_page"></wa-icon>
        </wa-button>
        
        <wa-button
          variant="text"
          @click=${() => this.handlePageChange(this.page - 1)}
          ?disabled=${this.page === 1}>
          <wa-icon name="navigate_before"></wa-icon>
        </wa-button>
        
        <span>Page ${this.page} of ${totalPages || 1}</span>
        
        <wa-button
          variant="text"
          @click=${() => this.handlePageChange(this.page + 1)}
          ?disabled=${this.page >= totalPages}>
          <wa-icon name="navigate_next"></wa-icon>
        </wa-button>
        
        <wa-button
          variant="text"
          @click=${() => this.handlePageChange(totalPages)}
          ?disabled=${this.page >= totalPages}>
          <wa-icon name="last_page"></wa-icon>
        </wa-button>
      </div>
    `;
  }
  
  renderLogDetailDialog() {
    if (!this.selectedLog) return html``;
    
    const log = this.selectedLog;
    
    return html`
      <wa-dialog 
        ?open=${this.showLogDetailDialog}
        @close=${this.closeLogDetail}
        title="Log Detail">
        
        <div class="dialog-content">
          <div class="detail-section">
            <div class="detail-header">Basic Information</div>
            
            <div class="detail-property">
              <div class="detail-label">ID</div>
              <div class="detail-value">${log.id}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Timestamp</div>
              <div class="detail-value">${this.formatDateTime(log.timestamp)}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Event Type</div>
              <div class="detail-value">
                <span class="event-type-badge event-${log.eventType}">
                  ${log.eventType}
                </span>
              </div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Action</div>
              <div class="detail-value">${log.action.replace(/_/g, ' ')}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">Status</div>
              <div class="detail-value">
                <wa-badge 
                  color=${log.status === 'success' ? 'success' : log.status === 'warning' ? 'warning' : 'error'}>
                  ${log.status}
                </wa-badge>
              </div>
            </div>
          </div>
          
          <div class="detail-section">
            <div class="detail-header">User Information</div>
            
            <div class="detail-property">
              <div class="detail-label">User</div>
              <div class="detail-value">${log.user}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">IP Address</div>
              <div class="detail-value">${log.ip}</div>
            </div>
            
            <div class="detail-property">
              <div class="detail-label">User Agent</div>
              <div class="detail-value">${log.userAgent}</div>
            </div>
          </div>
          
          <div class="detail-section">
            <div class="detail-header">Additional Details</div>
            
            <div class="code-block">
              ${JSON.stringify(log.details, null, 2)}
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeLogDetail} variant="text">
            Close
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderCreateKeyDialog() {
    return html`
      <wa-dialog 
        ?open=${this.showCreateKeyDialog}
        @close=${this.closeCreateKeyDialog}
        title="Create Encryption Key">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.keyForm.name}
              @input=${this.handleKeyFormChange}
              required>
            </wa-input>
            
            <wa-select
              label="Type"
              name="type"
              .value=${this.keyForm.type}
              @change=${this.handleKeyFormChange}
              required>
              <wa-option value="aes-256">AES-256</wa-option>
              <wa-option value="rsa-2048">RSA-2048</wa-option>
              <wa-option value="ed25519">Ed25519</wa-option>
            </wa-select>
          </div>
          
          <div class="form-grid">
            <wa-select
              label="Purpose"
              name="purpose"
              .value=${this.keyForm.purpose}
              @change=${this.handleKeyFormChange}
              required>
              <wa-option value="data-encryption">Data Encryption</wa-option>
              <wa-option value="token-signing">Token Signing</wa-option>
              <wa-option value="api-authentication">API Authentication</wa-option>
              <wa-option value="document-signing">Document Signing</wa-option>
            </wa-select>
            
            <wa-input
              label="Validity Period (days)"
              name="validityPeriod"
              type="number"
              min="1"
              max="3650"
              .value=${this.keyForm.validityPeriod}
              @input=${this.handleKeyFormChange}
              required>
            </wa-input>
          </div>
          
          <wa-textarea
            label="Description"
            name="description"
            .value=${this.keyForm.description}
            @input=${this.handleKeyFormChange}
            style="margin-top: 16px;">
          </wa-textarea>
          
          <div style="margin-top: 16px;">
            <wa-checkbox
              label="Auto-rotate key before expiration"
              name="autoRotate"
              ?checked=${this.keyForm.autoRotate}
              @change=${this.handleKeyFormChange}>
            </wa-checkbox>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeCreateKeyDialog} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createEncryptionKey} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderEditPolicyDialog() {
    if (!this.selectedPolicy) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showEditPolicyDialog}
        @close=${this.closeEditPolicyDialog}
        title="Edit Security Policy">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.policyForm.name}
              @input=${this.handlePolicyFormChange}
              required>
            </wa-input>
            
            <wa-checkbox
              label="Enabled"
              name="enabled"
              ?checked=${this.policyForm.enabled}
              @change=${this.handlePolicyFormChange}>
            </wa-checkbox>
          </div>
          
          <wa-textarea
            label="Description"
            name="description"
            .value=${this.policyForm.description}
            @input=${this.handlePolicyFormChange}
            style="margin-top: 16px;">
          </wa-textarea>
          
          <wa-divider style="margin: 24px 0 16px;"></wa-divider>
          
          <div class="detail-header">Policy Settings</div>
          
          ${this.selectedPolicy.id === 'policy-1' ? html`
            <!-- Password policy settings -->
            <div class="form-grid">
              <wa-input
                label="Minimum Length"
                name="settings.minLength"
                type="number"
                min="6"
                max="64"
                .value=${this.policyForm.settings.minLength}
                @input=${this.handlePolicyFormChange}>
              </wa-input>
              
              <wa-input
                label="History Count"
                name="settings.historyCount"
                type="number"
                min="0"
                max="24"
                .value=${this.policyForm.settings.historyCount}
                @input=${this.handlePolicyFormChange}>
              </wa-input>
              
              <wa-input
                label="Expiry Days"
                name="settings.expiryDays"
                type="number"
                min="0"
                max="365"
                .value=${this.policyForm.settings.expiryDays}
                @input=${this.handlePolicyFormChange}>
              </wa-input>
            </div>
            
            <div class="form-grid">
              <wa-checkbox
                label="Require Uppercase"
                name="settings.requireUppercase"
                ?checked=${this.policyForm.settings.requireUppercase}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Require Lowercase"
                name="settings.requireLowercase"
                ?checked=${this.policyForm.settings.requireLowercase}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Require Numbers"
                name="settings.requireNumbers"
                ?checked=${this.policyForm.settings.requireNumbers}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Require Special Chars"
                name="settings.requireSpecial"
                ?checked=${this.policyForm.settings.requireSpecial}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
            </div>
          ` : this.selectedPolicy.id === 'policy-2' ? html`
            <!-- Login security policy settings -->
            <div class="form-grid">
              <wa-input
                label="Max Login Attempts"
                name="settings.maxLoginAttempts"
                type="number"
                min="1"
                max="20"
                .value=${this.policyForm.settings.maxLoginAttempts}
                @input=${this.handlePolicyFormChange}>
              </wa-input>
              
              <wa-input
                label="Lockout Duration (min)"
                name="settings.lockoutDuration"
                type="number"
                min="1"
                max="1440"
                .value=${this.policyForm.settings.lockoutDuration}
                @input=${this.handlePolicyFormChange}>
              </wa-input>
            </div>
            
            <div class="form-grid">
              <wa-checkbox
                label="Require CAPTCHA"
                name="settings.requireCaptcha"
                ?checked=${this.policyForm.settings.requireCaptcha}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Require MFA for Admin"
                name="settings.requireMfaForAdmin"
                ?checked=${this.policyForm.settings.requireMfaForAdmin}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
            </div>
          ` : this.selectedPolicy.id === 'policy-3' ? html`
            <!-- Data access policy settings -->
            <div class="form-grid">
              <wa-checkbox
                label="Audit All Access"
                name="settings.auditAllAccess"
                ?checked=${this.policyForm.settings.auditAllAccess}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Require Justification"
                name="settings.requireJustification"
                ?checked=${this.policyForm.settings.requireJustification}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Mask Sensitive Data"
                name="settings.maskSensitiveData"
                ?checked=${this.policyForm.settings.maskSensitiveData}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
              
              <wa-checkbox
                label="Encrypt Sensitive Data"
                name="settings.encryptSensitiveData"
                ?checked=${this.policyForm.settings.encryptSensitiveData}
                @change=${this.handlePolicyFormChange}>
              </wa-checkbox>
            </div>
          ` : ''}
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeEditPolicyDialog} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.updatePolicy} color="primary">
            Save Changes
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderDeleteKeyDialog() {
    if (!this.selectedKey) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showDeleteKeyDialog}
        @close=${this.closeDeleteKeyDialog}
        title="Delete Encryption Key">
        
        <div class="dialog-content">
          <p>Are you sure you want to delete the encryption key "${this.selectedKey.name}"?</p>
          <p>This action cannot be undone.</p>
          
          <div style="margin-top: 16px; padding: 16px; background-color: #ffebee; border-radius: 4px;">
            <wa-icon name="warning" style="color: #f44336; margin-right: 8px;"></wa-icon>
            <span style="color: #d32f2f; font-weight: 500;">Warning:</span> 
            Deleting a key may make data encrypted with this key inaccessible.
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeDeleteKeyDialog} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.deleteKey} color="error">
            Delete
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderConfirmRevokeDialog() {
    if (!this.selectedKey) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showConfirmRevokeDialog}
        @close=${this.closeConfirmRevokeDialog}
        title="Revoke Encryption Key">
        
        <div class="dialog-content">
          <p>Are you sure you want to revoke the encryption key "${this.selectedKey.name}"?</p>
          <p>Revoking a key will prevent it from being used for future operations, but allows any data already encrypted with it to be decrypted.</p>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeConfirmRevokeDialog} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.revokeKey} color="primary">
            Revoke
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }

  render() {
    return html`
      <div class="container">
        <div class="header">
          <h1 class="title">Security Administration</h1>
          <p class="subtitle">Monitor and manage security settings and encryption keys</p>
        </div>
        
        ${this.renderSecurityStatistics()}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="audit">Audit Log</wa-tab>
          <wa-tab value="keys">Encryption Keys</wa-tab>
          <wa-tab value="policies">Security Policies</wa-tab>
          <wa-tab value="auth">Authentication</wa-tab>
        </wa-tabs>
        
        <div class="content-card">
          ${this.activeTab === 'audit' ? html`
            ${this.renderFilterBar()}
            ${this.renderAuditLogTable()}
          ` : this.activeTab === 'keys' ? html`
            ${this.renderEncryptionKeysTable()}
          ` : this.activeTab === 'policies' ? html`
            ${this.renderSecurityPoliciesTable()}
          ` : this.activeTab === 'auth' ? html`
            ${this.renderAuthenticationSettings()}
          ` : ''}
        </div>
        
        ${this.loading ? html`
          <div style="position: fixed; top: 16px; right: 16px; z-index: 1000;">
            <wa-spinner size="small"></wa-spinner>
            <span style="margin-left: 8px;">Loading...</span>
          </div>
        ` : ''}
        
        ${this.renderLogDetailDialog()}
        ${this.renderCreateKeyDialog()}
        ${this.renderEditPolicyDialog()}
        ${this.renderDeleteKeyDialog()}
        ${this.renderConfirmRevokeDialog()}
      </div>
    `;
  }
}

customElements.define('wa-security-admin', WebAwesomeSecurityAdmin);