import { LitElement, html, css } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/all/lit-all.min.js';

/**
 * @element wa-event-subscription-manager
 * @description Event subscription management UI for UNO framework
 * @property {string} baseUrl - Base URL for event subscription API
 * @property {boolean} loading - Whether the component is loading data
 * @property {Array} subscriptions - List of active event subscriptions
 * @property {Array} availableEvents - List of available event types
 * @property {Object} metrics - Subscription metrics data
 */
export class WebAwesomeEventSubscriptionManager extends LitElement {
  static get properties() {
    return {
      baseUrl: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      subscriptions: { type: Array },
      availableEvents: { type: Array },
      selectedEventType: { type: String },
      metrics: { type: Object },
      activeTab: { type: String },
      newHandlerData: { type: Object }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        --subscription-bg: var(--wa-background-color, #f5f5f5);
        --subscription-padding: 20px;
      }
      .subscription-container {
        padding: var(--subscription-padding);
        background-color: var(--subscription-bg);
        min-height: 600px;
      }
      .subscription-header {
        margin-bottom: 24px;
      }
      .subscription-title {
        font-size: 24px;
        font-weight: 500;
        margin: 0 0 8px 0;
        color: var(--wa-text-primary-color, #212121);
      }
      .subscription-subtitle {
        font-size: 16px;
        color: var(--wa-text-secondary-color, #757575);
        margin: 0;
      }
      .controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
      }
      .subscription-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 16px;
      }
      .subscription-table {
        width: 100%;
        border-collapse: collapse;
      }
      .subscription-table th, .subscription-table td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
      }
      .subscription-table th {
        font-weight: 500;
        color: var(--wa-text-primary-color, #212121);
      }
      .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
      }
      .status-active {
        background-color: var(--wa-success-color, #4caf50);
      }
      .status-inactive {
        background-color: var(--wa-error-color, #f44336);
      }
      .handler-form {
        padding: 16px;
        margin-bottom: 24px;
      }
      .form-row {
        margin-bottom: 16px;
      }
      .events-list {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid var(--wa-border-color, #e0e0e0);
        border-radius: 4px;
      }
      .event-item {
        padding: 12px 16px;
        border-bottom: 1px solid var(--wa-border-color, #e0e0e0);
        cursor: pointer;
      }
      .event-item:hover {
        background-color: var(--wa-hover-color, #f0f0f0);
      }
      .event-item.selected {
        background-color: var(--wa-selected-color, #e3f2fd);
      }
      .metric-card {
        padding: 16px;
        text-align: center;
      }
      .metric-value {
        font-size: 24px;
        font-weight: 500;
        color: var(--wa-primary-color, #3f51b5);
        margin-bottom: 8px;
      }
      .metric-label {
        font-size: 12px;
        color: var(--wa-text-secondary-color, #757575);
      }
      .chart-container {
        height: 300px;
        position: relative;
        margin-bottom: 24px;
      }
    `;
  }
  
  constructor() {
    super();
    this.baseUrl = '/api/events';
    this.loading = false;
    this.error = null;
    this.subscriptions = [];
    this.availableEvents = [];
    this.selectedEventType = '';
    this.metrics = {
      totalSubscriptions: 0,
      activeSubscriptions: 0,
      totalHandlers: 0,
      eventsProcessed: {
        total: 0,
        success: 0,
        failed: 0
      },
      byEventType: {},
      processingTime: {
        average: 0,
        p95: 0
      }
    };
    this.activeTab = 'subscriptions';
    this.newHandlerData = {
      eventType: '',
      handlerName: '',
      handlerModule: '',
      description: '',
      isAsync: true,
      config: {}
    };
    this._charts = {};
    
    // For demo purposes - would be replaced with actual API calls
    this._loadMockData();
  }
  
  _loadMockData() {
    // Mock available event types
    this.availableEvents = [
      { name: 'UserCreated', description: 'Triggered when a new user is created' },
      { name: 'UserUpdated', description: 'Triggered when a user is updated' },
      { name: 'UserDeleted', description: 'Triggered when a user is deleted' },
      { name: 'OrderCreated', description: 'Triggered when a new order is created' },
      { name: 'OrderUpdated', description: 'Triggered when an order is updated' },
      { name: 'OrderFulfilled', description: 'Triggered when an order is fulfilled' },
      { name: 'OrderCancelled', description: 'Triggered when an order is cancelled' },
      { name: 'ProductCreated', description: 'Triggered when a new product is created' },
      { name: 'ProductUpdated', description: 'Triggered when a product is updated' },
      { name: 'ProductDeleted', description: 'Triggered when a product is deleted' },
      { name: 'PaymentProcessed', description: 'Triggered when a payment is processed' },
      { name: 'PaymentFailed', description: 'Triggered when a payment fails' }
    ];
    
    // Mock subscriptions
    this.subscriptions = [
      {
        id: '1',
        eventType: 'UserCreated',
        handlerName: 'SendWelcomeEmail',
        handlerModule: 'user.notifications',
        description: 'Sends a welcome email to newly registered users',
        isActive: true,
        created: new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(),
        lastInvoked: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
        invocationCount: 128,
        successCount: 124,
        failureCount: 4,
        avgProcessingTime: 245
      },
      {
        id: '2',
        eventType: 'UserCreated',
        handlerName: 'CreateUserProfile',
        handlerModule: 'user.profile',
        description: 'Creates a default profile for new users',
        isActive: true,
        created: new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(),
        lastInvoked: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
        invocationCount: 128,
        successCount: 128,
        failureCount: 0,
        avgProcessingTime: 320
      },
      {
        id: '3',
        eventType: 'OrderCreated',
        handlerName: 'NotifyInventorySystem',
        handlerModule: 'inventory.integration',
        description: 'Notifies the inventory system about a new order',
        isActive: true,
        created: new Date(Date.now() - 14 * 24 * 3600 * 1000).toISOString(),
        lastInvoked: new Date(Date.now() - 1 * 3600 * 1000).toISOString(),
        invocationCount: 87,
        successCount: 85,
        failureCount: 2,
        avgProcessingTime: 178
      },
      {
        id: '4',
        eventType: 'OrderFulfilled',
        handlerName: 'SendOrderShippedEmail',
        handlerModule: 'order.notifications',
        description: 'Sends an email when an order has been shipped',
        isActive: true,
        created: new Date(Date.now() - 21 * 24 * 3600 * 1000).toISOString(),
        lastInvoked: new Date(Date.now() - 5 * 3600 * 1000).toISOString(),
        invocationCount: 54,
        successCount: 51,
        failureCount: 3,
        avgProcessingTime: 290
      },
      {
        id: '5',
        eventType: 'PaymentFailed',
        handlerName: 'NotifyCustomerService',
        handlerModule: 'payment.service',
        description: 'Notifies customer service when a payment fails',
        isActive: false,
        created: new Date(Date.now() - 30 * 24 * 3600 * 1000).toISOString(),
        lastInvoked: new Date(Date.now() - 10 * 24 * 3600 * 1000).toISOString(),
        invocationCount: 12,
        successCount: 10,
        failureCount: 2,
        avgProcessingTime: 150
      }
    ];
    
    // Calculate metrics
    this.metrics = {
      totalSubscriptions: this.subscriptions.length,
      activeSubscriptions: this.subscriptions.filter(s => s.isActive).length,
      totalHandlers: this.subscriptions.length,
      eventsProcessed: {
        total: this.subscriptions.reduce((total, sub) => total + sub.invocationCount, 0),
        success: this.subscriptions.reduce((total, sub) => total + sub.successCount, 0),
        failed: this.subscriptions.reduce((total, sub) => total + sub.failureCount, 0)
      },
      byEventType: this._calculateEventTypeMetrics(),
      processingTime: {
        average: Math.round(this.subscriptions.reduce((total, sub) => total + sub.avgProcessingTime, 0) / this.subscriptions.length),
        p95: 350 // Mock value
      }
    };
  }
  
  _calculateEventTypeMetrics() {
    const metrics = {};
    
    // Group subscriptions by event type
    this.subscriptions.forEach(sub => {
      if (!metrics[sub.eventType]) {
        metrics[sub.eventType] = {
          name: sub.eventType,
          subscriptionCount: 0,
          invocationCount: 0,
          successRate: 0,
          failureCount: 0
        };
      }
      
      metrics[sub.eventType].subscriptionCount++;
      metrics[sub.eventType].invocationCount += sub.invocationCount;
      metrics[sub.eventType].failureCount += sub.failureCount;
    });
    
    // Calculate success rates
    Object.values(metrics).forEach(metric => {
      metric.successRate = metric.invocationCount > 0 ? 
        ((metric.invocationCount - metric.failureCount) / metric.invocationCount * 100).toFixed(1) : 100;
    });
    
    return metrics;
  }
  
  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    this._destroyCharts();
  }
  
  async fetchData() {
    // In a real implementation, this would fetch data from the API
    this.loading = true;
    
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // In a real app, we would fetch:
      // 1. Available event types
      // 2. Active subscriptions
      // 3. Subscription metrics
      
      // For demo, we'll use the mock data
      this.loading = false;
    } catch (error) {
      this.error = `Error loading subscription data: ${error.message}`;
      this.loading = false;
    }
  }
  
  async createSubscription() {
    this.loading = true;
    
    try {
      // Validate form data
      if (!this.newHandlerData.eventType) {
        throw new Error('Event type is required');
      }
      if (!this.newHandlerData.handlerName) {
        throw new Error('Handler name is required');
      }
      if (!this.newHandlerData.handlerModule) {
        throw new Error('Handler module is required');
      }
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // In a real app, we would make a POST request to create the subscription
      
      // For demo, add the new subscription to our mock data
      const newSubscription = {
        id: Date.now().toString(),
        eventType: this.newHandlerData.eventType,
        handlerName: this.newHandlerData.handlerName,
        handlerModule: this.newHandlerData.handlerModule,
        description: this.newHandlerData.description,
        isActive: true,
        created: new Date().toISOString(),
        lastInvoked: null,
        invocationCount: 0,
        successCount: 0,
        failureCount: 0,
        avgProcessingTime: 0
      };
      
      this.subscriptions = [...this.subscriptions, newSubscription];
      
      // Reset form
      this.newHandlerData = {
        eventType: '',
        handlerName: '',
        handlerModule: '',
        description: '',
        isAsync: true,
        config: {}
      };
      
      // Recalculate metrics
      this.metrics = {
        ...this.metrics,
        totalSubscriptions: this.subscriptions.length,
        activeSubscriptions: this.subscriptions.filter(s => s.isActive).length,
        totalHandlers: this.subscriptions.length,
        byEventType: this._calculateEventTypeMetrics()
      };
      
      this.loading = false;
      
      // Show success message
      this.dispatchEvent(new CustomEvent('notification', {
        detail: {
          message: 'Subscription created successfully',
          type: 'success'
        }
      }));
    } catch (error) {
      this.error = `Error creating subscription: ${error.message}`;
      this.loading = false;
    }
  }
  
  async toggleSubscriptionStatus(id) {
    this.loading = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // In a real app, we would make a PUT/PATCH request to update the subscription
      
      // For demo, toggle the subscription status
      this.subscriptions = this.subscriptions.map(sub => {
        if (sub.id === id) {
          return {
            ...sub,
            isActive: !sub.isActive
          };
        }
        return sub;
      });
      
      // Recalculate metrics
      this.metrics = {
        ...this.metrics,
        activeSubscriptions: this.subscriptions.filter(s => s.isActive).length
      };
      
      this.loading = false;
    } catch (error) {
      this.error = `Error updating subscription: ${error.message}`;
      this.loading = false;
    }
  }
  
  async deleteSubscription(id) {
    if (!confirm('Are you sure you want to delete this subscription?')) {
      return;
    }
    
    this.loading = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // In a real app, we would make a DELETE request
      
      // For demo, remove the subscription from our mock data
      this.subscriptions = this.subscriptions.filter(sub => sub.id !== id);
      
      // Recalculate metrics
      this.metrics = {
        ...this.metrics,
        totalSubscriptions: this.subscriptions.length,
        activeSubscriptions: this.subscriptions.filter(s => s.isActive).length,
        totalHandlers: this.subscriptions.length,
        byEventType: this._calculateEventTypeMetrics()
      };
      
      this.loading = false;
      
      // Show success message
      this.dispatchEvent(new CustomEvent('notification', {
        detail: {
          message: 'Subscription deleted successfully',
          type: 'success'
        }
      }));
    } catch (error) {
      this.error = `Error deleting subscription: ${error.message}`;
      this.loading = false;
    }
  }
  
  handleInputChange(field, event) {
    this.newHandlerData = {
      ...this.newHandlerData,
      [field]: event.target.value
    };
  }
  
  handleEventTypeSelect(eventType) {
    this.newHandlerData = {
      ...this.newHandlerData,
      eventType
    };
  }
  
  handleTabChange(event) {
    this.activeTab = event.target.value;
    
    // If we're switching to metrics tab, initialize charts
    if (this.activeTab === 'metrics') {
      setTimeout(() => {
        this._initializeCharts();
      }, 100);
    }
  }
  
  _formatDate(dateString) {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  }
  
  _formatRelativeTime(dateString) {
    if (!dateString) return 'Never';
    
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
      return this._formatDate(dateString);
    }
  }
  
  _initializeCharts() {
    if (!window.Chart) {
      console.warn('Chart.js not loaded, skipping chart initialization');
      return;
    }
    
    // Destroy existing charts
    this._destroyCharts();
    
    // Initialize success rate chart
    this._initSuccessRateChart();
    
    // Initialize events by type chart
    this._initEventsByTypeChart();
  }
  
  _destroyCharts() {
    Object.values(this._charts).forEach(chart => {
      if (chart) chart.destroy();
    });
    this._charts = {};
  }
  
  _initSuccessRateChart() {
    const chartContainer = this.shadowRoot.querySelector('#successRateChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const total = this.metrics.eventsProcessed.total;
    const success = this.metrics.eventsProcessed.success;
    const failed = this.metrics.eventsProcessed.failed;
    
    this._charts.successRateChart = new window.Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Success', 'Failed'],
        datasets: [{
          data: [success, failed],
          backgroundColor: [
            'rgba(76, 175, 80, 0.7)',
            'rgba(244, 67, 54, 0.7)'
          ],
          borderColor: [
            'rgba(76, 175, 80, 1)',
            'rgba(244, 67, 54, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          title: {
            display: true,
            text: 'Event Processing Success Rate'
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.raw || 0;
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }
  
  _initEventsByTypeChart() {
    const chartContainer = this.shadowRoot.querySelector('#eventsByTypeChartContainer');
    if (!chartContainer) return;
    
    const canvas = document.createElement('canvas');
    chartContainer.innerHTML = '';
    chartContainer.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    const eventTypes = Object.values(this.metrics.byEventType);
    
    this._charts.eventsByTypeChart = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: eventTypes.map(et => et.name),
        datasets: [{
          label: 'Invocations',
          data: eventTypes.map(et => et.invocationCount),
          backgroundColor: 'rgba(63, 81, 181, 0.7)',
          borderColor: 'rgba(63, 81, 181, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          title: {
            display: true,
            text: 'Events Processed by Type'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Count'
            }
          }
        }
      }
    });
  }
  
  render() {
    return html`
      <div class="subscription-container">
        <div class="subscription-header">
          <h1 class="subscription-title">Event Subscription Manager</h1>
          <p class="subscription-subtitle">Manage event subscriptions and monitor event processing</p>
        </div>
        
        <div class="controls">
          <div style="display: flex; gap: 16px;">
            <button 
              @click=${() => this.activeTab = 'subscriptions'}
              style="background-color: ${this.activeTab === 'subscriptions' ? 'var(--wa-primary-color, #3f51b5)' : 'transparent'}; 
                     color: ${this.activeTab === 'subscriptions' ? 'white' : 'var(--wa-text-primary-color, #212121)'};
                     border: 1px solid var(--wa-border-color, #e0e0e0);
                     padding: 8px 16px;
                     border-radius: 4px;
                     cursor: pointer;">
              Subscriptions
            </button>
            <button 
              @click=${() => this.activeTab = 'create'}
              style="background-color: ${this.activeTab === 'create' ? 'var(--wa-primary-color, #3f51b5)' : 'transparent'}; 
                     color: ${this.activeTab === 'create' ? 'white' : 'var(--wa-text-primary-color, #212121)'};
                     border: 1px solid var(--wa-border-color, #e0e0e0);
                     padding: 8px 16px;
                     border-radius: 4px;
                     cursor: pointer;">
              Create Subscription
            </button>
            <button 
              @click=${() => this.activeTab = 'metrics'}
              style="background-color: ${this.activeTab === 'metrics' ? 'var(--wa-primary-color, #3f51b5)' : 'transparent'}; 
                     color: ${this.activeTab === 'metrics' ? 'white' : 'var(--wa-text-primary-color, #212121)'};
                     border: 1px solid var(--wa-border-color, #e0e0e0);
                     padding: 8px 16px;
                     border-radius: 4px;
                     cursor: pointer;">
              Metrics
            </button>
          </div>
          
          <button 
            @click=${this.fetchData}
            style="background-color: transparent;
                   color: var(--wa-primary-color, #3f51b5);
                   border: 1px solid var(--wa-primary-color, #3f51b5);
                   padding: 8px 16px;
                   border-radius: 4px;
                   cursor: pointer;
                   display: flex;
                   align-items: center;
                   gap: 8px;">
            <span style="display: inline-block; width: 24px; height: 24px;">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
              </svg>
            </span>
            Refresh
          </button>
        </div>
        
        ${this.error ? html`
          <div style="background-color: var(--wa-error-color-light, #ffebee); 
                      color: var(--wa-error-color, #f44336);
                      padding: 16px;
                      border-radius: 4px;
                      margin-bottom: 24px;
                      display: flex;
                      align-items: center;
                      gap: 8px;">
            <span style="display: inline-block; width: 24px; height: 24px;">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
            </span>
            ${this.error}
            <button 
              @click=${() => this.error = null}
              style="background: none;
                     border: none;
                     color: var(--wa-error-color, #f44336);
                     cursor: pointer;
                     margin-left: auto;">
              <span style="display: inline-block; width: 20px; height: 20px;">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
              </span>
            </button>
          </div>
        ` : ''}
        
        ${this.loading ? html`
          <div style="display: flex; justify-content: center; padding: 32px;">
            <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; 
                        border-top: 4px solid var(--wa-primary-color, #3f51b5); 
                        border-radius: 50%; animation: spin 1s linear infinite;"></div>
          </div>
          <style>
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          </style>
        ` : ''}
        
        <!-- Subscriptions Tab -->
        ${this.activeTab === 'subscriptions' && !this.loading ? html`
          <div style="margin-bottom: 24px;">
            <div class="subscription-grid">
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.totalSubscriptions}</div>
                <div class="metric-label">Total Subscriptions</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.activeSubscriptions}</div>
                <div class="metric-label">Active Subscriptions</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.eventsProcessed.total}</div>
                <div class="metric-label">Events Processed</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.processingTime.average}ms</div>
                <div class="metric-label">Avg Processing Time</div>
              </div>
            </div>
          </div>
          
          <div style="background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <table class="subscription-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Event Type</th>
                  <th>Handler</th>
                  <th>Description</th>
                  <th>Last Invoked</th>
                  <th>Success Rate</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${this.subscriptions.map(subscription => html`
                  <tr>
                    <td>
                      <span class="status-indicator ${subscription.isActive ? 'status-active' : 'status-inactive'}"></span>
                      ${subscription.isActive ? 'Active' : 'Inactive'}
                    </td>
                    <td>${subscription.eventType}</td>
                    <td>${subscription.handlerName}</td>
                    <td>${subscription.description}</td>
                    <td>${this._formatRelativeTime(subscription.lastInvoked)}</td>
                    <td>
                      ${subscription.invocationCount === 0 ? 'N/A' : 
                        `${((subscription.successCount / subscription.invocationCount) * 100).toFixed(1)}% 
                        (${subscription.successCount}/${subscription.invocationCount})`}
                    </td>
                    <td>
                      <div style="display: flex; gap: 8px;">
                        <button 
                          @click=${() => this.toggleSubscriptionStatus(subscription.id)}
                          style="background-color: ${subscription.isActive ? 'var(--wa-warning-color, #ff9800)' : 'var(--wa-success-color, #4caf50)'};
                                 color: white;
                                 border: none;
                                 padding: 4px 8px;
                                 border-radius: 4px;
                                 cursor: pointer;">
                          ${subscription.isActive ? 'Disable' : 'Enable'}
                        </button>
                        <button 
                          @click=${() => this.deleteSubscription(subscription.id)}
                          style="background-color: var(--wa-error-color, #f44336);
                                 color: white;
                                 border: none;
                                 padding: 4px 8px;
                                 border-radius: 4px;
                                 cursor: pointer;">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                `)}
              </tbody>
            </table>
          </div>
        ` : ''}
        
        <!-- Create Subscription Tab -->
        ${this.activeTab === 'create' && !this.loading ? html`
          <div style="background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <div class="handler-form">
              <h2 style="margin-top: 0; margin-bottom: 16px;">Create Event Subscription</h2>
              
              <div class="form-row">
                <label style="display: block; margin-bottom: 8px; font-weight: 500;">Event Type</label>
                <div style="display: flex; gap: 16px;">
                  <div style="flex: 1;">
                    <select 
                      @change=${e => this.handleInputChange('eventType', e)}
                      style="width: 100%; padding: 8px; border: 1px solid var(--wa-border-color, #e0e0e0); border-radius: 4px;">
                      <option value="" disabled ${!this.newHandlerData.eventType ? 'selected' : ''}>Select an event type</option>
                      ${this.availableEvents.map(event => html`
                        <option value=${event.name} ?selected=${this.newHandlerData.eventType === event.name}>${event.name}</option>
                      `)}
                    </select>
                  </div>
                  <div style="flex: 1;">
                    <input 
                      type="text" 
                      placeholder="Or enter a custom event type"
                      @input=${e => this.handleInputChange('eventType', e)}
                      .value=${this.newHandlerData.eventType}
                      style="width: 100%; padding: 8px; border: 1px solid var(--wa-border-color, #e0e0e0); border-radius: 4px;">
                  </div>
                </div>
              </div>
              
              <div class="form-row">
                <label style="display: block; margin-bottom: 8px; font-weight: 500;">Handler Name</label>
                <input 
                  type="text" 
                  placeholder="e.g., SendWelcomeEmail"
                  @input=${e => this.handleInputChange('handlerName', e)}
                  .value=${this.newHandlerData.handlerName}
                  style="width: 100%; padding: 8px; border: 1px solid var(--wa-border-color, #e0e0e0); border-radius: 4px;">
              </div>
              
              <div class="form-row">
                <label style="display: block; margin-bottom: 8px; font-weight: 500;">Handler Module</label>
                <input 
                  type="text" 
                  placeholder="e.g., user.notifications"
                  @input=${e => this.handleInputChange('handlerModule', e)}
                  .value=${this.newHandlerData.handlerModule}
                  style="width: 100%; padding: 8px; border: 1px solid var(--wa-border-color, #e0e0e0); border-radius: 4px;">
              </div>
              
              <div class="form-row">
                <label style="display: block; margin-bottom: 8px; font-weight: 500;">Description</label>
                <textarea 
                  @input=${e => this.handleInputChange('description', e)}
                  .value=${this.newHandlerData.description}
                  placeholder="Describe what this handler does"
                  style="width: 100%; padding: 8px; border: 1px solid var(--wa-border-color, #e0e0e0); border-radius: 4px; min-height: 80px;"></textarea>
              </div>
              
              <div class="form-row">
                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                  <input 
                    type="checkbox" 
                    ?checked=${this.newHandlerData.isAsync}
                    @change=${e => this.handleInputChange('isAsync', { target: { value: e.target.checked } })}>
                  Async Handler
                </label>
              </div>
              
              <div style="margin-top: 24px;">
                <button 
                  @click=${this.createSubscription}
                  style="background-color: var(--wa-primary-color, #3f51b5);
                         color: white;
                         border: none;
                         padding: 8px 16px;
                         border-radius: 4px;
                         cursor: pointer;">
                  Create Subscription
                </button>
              </div>
            </div>
          </div>
          
          <div style="margin-top: 24px;">
            <h2 style="margin-top: 0; margin-bottom: 16px;">Available Event Types</h2>
            <p style="margin-top: 0; margin-bottom: 16px; color: var(--wa-text-secondary-color, #757575);">
              Select from the list of registered event types or enter a custom event type
            </p>
            
            <div class="events-list">
              ${this.availableEvents.map(event => html`
                <div 
                  class="event-item ${this.newHandlerData.eventType === event.name ? 'selected' : ''}"
                  @click=${() => this.handleEventTypeSelect(event.name)}>
                  <div style="font-weight: 500;">${event.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color, #757575);">${event.description}</div>
                </div>
              `)}
            </div>
          </div>
        ` : ''}
        
        <!-- Metrics Tab -->
        ${this.activeTab === 'metrics' && !this.loading ? html`
          <div style="margin-bottom: 24px;">
            <div class="subscription-grid">
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.totalSubscriptions}</div>
                <div class="metric-label">Total Subscriptions</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.activeSubscriptions}</div>
                <div class="metric-label">Active Subscriptions</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.eventsProcessed.total}</div>
                <div class="metric-label">Events Processed</div>
              </div>
              
              <div style="padding: 16px; text-align: center;">
                <div class="metric-value">${this.metrics.processingTime.average}ms</div>
                <div class="metric-label">Avg Processing Time</div>
              </div>
            </div>
          </div>
          
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 24px; margin-bottom: 24px;">
            <div style="background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
              <div style="padding: 16px;">
                <h2 style="margin-top: 0; margin-bottom: 16px;">Event Processing Success Rate</h2>
                <div id="successRateChartContainer" class="chart-container"></div>
              </div>
            </div>
            
            <div style="background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
              <div style="padding: 16px;">
                <h2 style="margin-top: 0; margin-bottom: 16px;">Events Processed by Type</h2>
                <div id="eventsByTypeChartContainer" class="chart-container"></div>
              </div>
            </div>
          </div>
          
          <div style="background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">
            <div style="padding: 16px;">
              <h2 style="margin-top: 0; margin-bottom: 16px;">Event Type Metrics</h2>
              
              <table class="subscription-table">
                <thead>
                  <tr>
                    <th>Event Type</th>
                    <th>Subscriptions</th>
                    <th>Events Processed</th>
                    <th>Success Rate</th>
                    <th>Last Processed</th>
                  </tr>
                </thead>
                <tbody>
                  ${Object.values(this.metrics.byEventType).map(metric => html`
                    <tr>
                      <td>${metric.name}</td>
                      <td>${metric.subscriptionCount}</td>
                      <td>${metric.invocationCount}</td>
                      <td>${metric.successRate}%</td>
                      <td>${this._formatRelativeTime(this.subscriptions.find(s => s.eventType === metric.name)?.lastInvoked)}</td>
                    </tr>
                  `)}
                </tbody>
              </table>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('wa-event-subscription-manager', WebAwesomeEventSubscriptionManager);