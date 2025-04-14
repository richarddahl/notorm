import { LitElement, html, css } from 'lit';
import '@webcomponents/awesome/wa-card.js';
import '@webcomponents/awesome/wa-button.js';
import '@webcomponents/awesome/wa-input.js';
import '@webcomponents/awesome/wa-select.js';
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
import '@webcomponents/awesome/wa-progress.js';
import '@webcomponents/awesome/wa-date-picker.js';
import '@webcomponents/awesome/wa-time-picker.js';

/**
 * @element wa-job-dashboard
 * @description Dashboard for monitoring and managing background jobs in the UNO framework
 */
export class WebAwesomeJobDashboard extends LitElement {
  static get properties() {
    return {
      activeTab: { type: String },
      loading: { type: Boolean },
      error: { type: String },
      
      // Jobs data
      queuedJobs: { type: Array },
      activeJobs: { type: Array },
      completedJobs: { type: Array },
      failedJobs: { type: Array },
      scheduledJobs: { type: Array },
      
      // Selected job
      selectedJob: { type: Object },
      
      // Filters
      jobTypeFilter: { type: String },
      statusFilter: { type: String },
      dateRangeStart: { type: String },
      dateRangeEnd: { type: String },
      searchTerm: { type: String },
      
      // Pagination
      page: { type: Number },
      pageSize: { type: Number },
      totalItems: { type: Number },
      
      // Dialogs
      showJobDetailDialog: { type: Boolean },
      showCreateScheduleDialog: { type: Boolean },
      showRetryDialog: { type: Boolean },
      showCancelDialog: { type: Boolean },
      
      // Forms
      scheduleForm: { type: Object },
      
      // Metrics
      systemMetrics: { type: Object },
      
      // Refresh timer
      refreshInterval: { type: Number },
      lastRefresh: { type: String },
      
      // Advanced settings
      autoRefresh: { type: Boolean }
    };
  }
  
  static get styles() {
    return css`
      :host {
        display: block;
        --job-dashboard-bg: var(--wa-background-color, #f5f5f5);
        --job-dashboard-padding: 20px;
      }
      
      .container {
        padding: var(--job-dashboard-padding);
        background-color: var(--job-dashboard-bg);
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
      
      .metrics-panel {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }
      
      .metric-card {
        background-color: var(--wa-surface-color, #ffffff);
        border-radius: var(--wa-border-radius, 4px);
        box-shadow: var(--wa-shadow-1, 0 1px 3px rgba(0,0,0,0.1));
        padding: 20px;
        text-align: center;
      }
      
      .metric-value {
        font-size: 32px;
        font-weight: 700;
        margin: 8px 0;
      }
      
      .metric-label {
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        text-transform: uppercase;
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
      
      .job-actions {
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
      
      .status-queued {
        background-color: rgba(156, 39, 176, 0.1);
        color: #9C27B0;
      }
      
      .status-active {
        background-color: rgba(33, 150, 243, 0.1);
        color: #2196F3;
      }
      
      .status-completed {
        background-color: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
      }
      
      .status-failed {
        background-color: rgba(244, 67, 54, 0.1);
        color: #F44336;
      }
      
      .status-scheduled {
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
      
      .job-detail-section {
        margin-bottom: 24px;
      }
      
      .job-detail-header {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 12px;
      }
      
      .job-detail-property {
        display: flex;
        margin-bottom: 8px;
      }
      
      .job-detail-label {
        font-weight: 500;
        width: 150px;
      }
      
      .job-detail-value {
        flex: 1;
      }
      
      .job-detail-tabs {
        margin-top: 24px;
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
      
      .refresh-info {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        font-size: 14px;
        color: var(--wa-text-secondary-color, #757575);
        margin-bottom: 16px;
      }
      
      .refresh-info wa-icon {
        margin-right: 4px;
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
      
      .progress-container {
        display: flex;
        align-items: center;
        gap: 12px;
      }
      
      .progress-value {
        width: 40px;
        text-align: right;
        font-size: 14px;
      }
      
      .progress-bar {
        flex: 1;
      }
      
      .cron-expression {
        font-family: monospace;
        font-size: 14px;
        background-color: var(--wa-code-bg, #f5f5f5);
        padding: 4px 8px;
        border-radius: 4px;
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
    `;
  }

  constructor() {
    super();
    this.activeTab = 'active';
    this.loading = false;
    this.error = null;
    
    this.queuedJobs = [];
    this.activeJobs = [];
    this.completedJobs = [];
    this.failedJobs = [];
    this.scheduledJobs = [];
    
    this.selectedJob = null;
    
    this.jobTypeFilter = '';
    this.statusFilter = '';
    this.dateRangeStart = '';
    this.dateRangeEnd = '';
    this.searchTerm = '';
    
    this.page = 1;
    this.pageSize = 10;
    this.totalItems = 0;
    
    this.showJobDetailDialog = false;
    this.showCreateScheduleDialog = false;
    this.showRetryDialog = false;
    this.showCancelDialog = false;
    
    this.scheduleForm = this._getDefaultScheduleForm();
    
    this.systemMetrics = {
      activeJobs: 0,
      queuedJobs: 0,
      completedJobsToday: 0,
      failedJobsToday: 0
    };
    
    this.refreshInterval = 30; // seconds
    this.lastRefresh = new Date().toLocaleTimeString();
    
    this.autoRefresh = true;
    
    // Load mock data
    this._loadMockData();
    
    // Set up auto-refresh if enabled
    if (this.autoRefresh) {
      this._startAutoRefresh();
    }
  }

  connectedCallback() {
    super.connectedCallback();
    // Start auto-refresh when component is connected
    if (this.autoRefresh) {
      this._startAutoRefresh();
    }
  }
  
  disconnectedCallback() {
    super.disconnectedCallback();
    // Clear auto-refresh when component is disconnected
    this._stopAutoRefresh();
  }
  
  _startAutoRefresh() {
    this._autoRefreshTimer = setInterval(() => {
      this.refreshData();
    }, this.refreshInterval * 1000);
  }
  
  _stopAutoRefresh() {
    if (this._autoRefreshTimer) {
      clearInterval(this._autoRefreshTimer);
      this._autoRefreshTimer = null;
    }
  }
  
  refreshData() {
    // Simulate API refresh
    this.loading = true;
    
    // In a real implementation, this would call the jobs API
    setTimeout(() => {
      this._loadMockData();
      this.lastRefresh = new Date().toLocaleTimeString();
      this.loading = false;
    }, 500);
  }
  
  _getDefaultScheduleForm() {
    return {
      jobType: '',
      name: '',
      description: '',
      cronExpression: '0 0 * * *', // Daily at midnight
      parameters: {},
      enabled: true
    };
  }
  
  _loadMockData() {
    // Generate mock job data for demonstration
    this.queuedJobs = this._generateMockJobs('queued', 5);
    this.activeJobs = this._generateMockJobs('active', 7);
    this.completedJobs = this._generateMockJobs('completed', 15);
    this.failedJobs = this._generateMockJobs('failed', 3);
    this.scheduledJobs = this._generateMockScheduledJobs(10);
    
    // Update metrics
    this.systemMetrics = {
      activeJobs: this.activeJobs.length,
      queuedJobs: this.queuedJobs.length,
      completedJobsToday: this.completedJobs.length,
      failedJobsToday: this.failedJobs.length
    };
    
    // Update total items for pagination
    switch (this.activeTab) {
      case 'active':
        this.totalItems = this.activeJobs.length;
        break;
      case 'queued':
        this.totalItems = this.queuedJobs.length;
        break;
      case 'completed':
        this.totalItems = this.completedJobs.length;
        break;
      case 'failed':
        this.totalItems = this.failedJobs.length;
        break;
      case 'scheduled':
        this.totalItems = this.scheduledJobs.length;
        break;
    }
  }
  
  _generateMockJobs(status, count) {
    const jobTypes = ['data-sync', 'email-notification', 'report-generation', 'data-cleanup', 'backup', 'import', 'export'];
    const jobs = [];
    
    const now = new Date();
    
    for (let i = 0; i < count; i++) {
      const jobType = jobTypes[Math.floor(Math.random() * jobTypes.length)];
      let progress = 0;
      let startTime = new Date(now - Math.random() * 3600000); // Random time within the last hour
      let endTime = null;
      
      if (status === 'active') {
        progress = Math.floor(Math.random() * 100);
      } else if (status === 'completed') {
        progress = 100;
        endTime = new Date(startTime.getTime() + Math.random() * 120000); // 0-2 minutes after start
      } else if (status === 'failed') {
        progress = Math.floor(Math.random() * 100);
        endTime = new Date(startTime.getTime() + Math.random() * 60000); // 0-1 minute after start
      }
      
      jobs.push({
        id: `job-${status}-${i + 1}`,
        jobType,
        status,
        name: `${this._capitalizeFirstLetter(jobType)} Task ${i + 1}`,
        description: `Sample ${jobType} job for demonstration purposes`,
        priority: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)],
        progress,
        createdAt: startTime.toISOString(),
        startedAt: status !== 'queued' ? startTime.toISOString() : null,
        completedAt: endTime ? endTime.toISOString() : null,
        error: status === 'failed' ? 'Mock error: Connection timeout' : null,
        parameters: {
          param1: 'value1',
          param2: 'value2'
        },
        result: status === 'completed' ? {
          recordsProcessed: Math.floor(Math.random() * 1000),
          timeElapsed: Math.floor(Math.random() * 120)
        } : null
      });
    }
    
    return jobs;
  }
  
  _generateMockScheduledJobs(count) {
    const jobTypes = ['data-sync', 'email-notification', 'report-generation', 'data-cleanup', 'backup', 'import', 'export'];
    const cronExpressions = ['0 0 * * *', '0 */6 * * *', '0 0 * * 1', '*/15 * * * *', '0 0 1 * *'];
    const jobs = [];
    
    for (let i = 0; i < count; i++) {
      const jobType = jobTypes[Math.floor(Math.random() * jobTypes.length)];
      
      jobs.push({
        id: `schedule-${i + 1}`,
        jobType,
        name: `Scheduled ${this._capitalizeFirstLetter(jobType)} ${i + 1}`,
        description: `Scheduled ${jobType} task that runs automatically`,
        cronExpression: cronExpressions[Math.floor(Math.random() * cronExpressions.length)],
        enabled: Math.random() > 0.2, // 80% chance of being enabled
        lastRun: Math.random() > 0.3 ? new Date(Date.now() - Math.random() * 86400000 * 10).toISOString() : null,
        nextRun: new Date(Date.now() + Math.random() * 86400000 * 5).toISOString(),
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
        parameters: {
          param1: 'value1',
          param2: 'value2'
        }
      });
    }
    
    return jobs;
  }
  
  _capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
  
  handleTabChange(e) {
    this.activeTab = e.detail.value;
    this.page = 1; // Reset to first page on tab change
    
    // Update total items for the new tab
    switch (this.activeTab) {
      case 'active':
        this.totalItems = this.activeJobs.length;
        break;
      case 'queued':
        this.totalItems = this.queuedJobs.length;
        break;
      case 'completed':
        this.totalItems = this.completedJobs.length;
        break;
      case 'failed':
        this.totalItems = this.failedJobs.length;
        break;
      case 'scheduled':
        this.totalItems = this.scheduledJobs.length;
        break;
    }
  }
  
  handleSearchChange(e) {
    this.searchTerm = e.target.value;
    this.page = 1; // Reset to first page when search changes
  }
  
  handleJobTypeFilterChange(e) {
    this.jobTypeFilter = e.target.value;
    this.page = 1; // Reset to first page when filter changes
  }
  
  handleStatusFilterChange(e) {
    this.statusFilter = e.target.value;
    this.page = 1; // Reset to first page when filter changes
  }
  
  handleDateRangeStartChange(e) {
    this.dateRangeStart = e.target.value;
    this.page = 1; // Reset to first page when filter changes
  }
  
  handleDateRangeEndChange(e) {
    this.dateRangeEnd = e.target.value;
    this.page = 1; // Reset to first page when filter changes
  }
  
  handlePageChange(newPage) {
    this.page = newPage;
  }
  
  handlePageSizeChange(e) {
    this.pageSize = parseInt(e.target.value, 10);
    this.page = 1; // Reset to first page when page size changes
  }
  
  openJobDetail(job) {
    this.selectedJob = job;
    this.showJobDetailDialog = true;
  }
  
  closeJobDetail() {
    this.showJobDetailDialog = false;
    this.selectedJob = null;
  }
  
  openCreateSchedule() {
    this.scheduleForm = this._getDefaultScheduleForm();
    this.showCreateScheduleDialog = true;
  }
  
  closeCreateSchedule() {
    this.showCreateScheduleDialog = false;
  }
  
  openRetryDialog(job) {
    this.selectedJob = job;
    this.showRetryDialog = true;
  }
  
  closeRetryDialog() {
    this.showRetryDialog = false;
  }
  
  openCancelDialog(job) {
    this.selectedJob = job;
    this.showCancelDialog = true;
  }
  
  closeCancelDialog() {
    this.showCancelDialog = false;
  }
  
  retryJob() {
    // Simulate API call to retry job
    this.loading = true;
    
    setTimeout(() => {
      const jobId = this.selectedJob.id;
      
      // Move job from failed to queued
      this.failedJobs = this.failedJobs.filter(job => job.id !== jobId);
      const job = { ...this.selectedJob, status: 'queued', progress: 0 };
      this.queuedJobs.push(job);
      
      this.closeCancelDialog();
      this.showRetryDialog = false;
      this.loading = false;
      
      this._showNotification(`Job ${job.name} has been queued for retry.`, 'success');
    }, 500);
  }
  
  cancelJob() {
    // Simulate API call to cancel job
    this.loading = true;
    
    setTimeout(() => {
      const jobId = this.selectedJob.id;
      
      // Remove job from active or queued list
      if (this.selectedJob.status === 'active') {
        this.activeJobs = this.activeJobs.filter(job => job.id !== jobId);
      } else if (this.selectedJob.status === 'queued') {
        this.queuedJobs = this.queuedJobs.filter(job => job.id !== jobId);
      }
      
      this.closeCancelDialog();
      this.loading = false;
      
      this._showNotification(`Job ${this.selectedJob.name} has been cancelled.`, 'success');
    }, 500);
  }
  
  createSchedule() {
    // Simulate API call to create schedule
    this.loading = true;
    
    setTimeout(() => {
      const newSchedule = {
        ...this.scheduleForm,
        id: `schedule-${Date.now()}`,
        createdAt: new Date().toISOString(),
        nextRun: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
        lastRun: null
      };
      
      this.scheduledJobs.push(newSchedule);
      this.closeCreateSchedule();
      this.loading = false;
      
      this._showNotification(`Schedule "${newSchedule.name}" has been created.`, 'success');
    }, 500);
  }
  
  toggleScheduleStatus(schedule) {
    // Simulate API call to toggle schedule status
    this.loading = true;
    
    setTimeout(() => {
      this.scheduledJobs = this.scheduledJobs.map(s => {
        if (s.id === schedule.id) {
          return { ...s, enabled: !s.enabled };
        }
        return s;
      });
      
      this.loading = false;
      this._showNotification(`Schedule "${schedule.name}" has been ${schedule.enabled ? 'disabled' : 'enabled'}.`, 'success');
    }, 500);
  }
  
  deleteSchedule(schedule) {
    // Simulate API call to delete schedule
    this.loading = true;
    
    setTimeout(() => {
      this.scheduledJobs = this.scheduledJobs.filter(s => s.id !== schedule.id);
      this.loading = false;
      this._showNotification(`Schedule "${schedule.name}" has been deleted.`, 'success');
    }, 500);
  }
  
  handleScheduleFormChange(e) {
    const field = e.target.name;
    let value = e.target.value;
    
    if (field === 'enabled') {
      value = e.target.checked;
    }
    
    this.scheduleForm = {
      ...this.scheduleForm,
      [field]: value
    };
  }
  
  getCronDescription(expression) {
    // A very simple cron description function
    // In a real application, you would use a more robust library
    
    if (expression === '0 0 * * *') {
      return 'Daily at midnight';
    } else if (expression === '0 */6 * * *') {
      return 'Every 6 hours';
    } else if (expression === '0 0 * * 1') {
      return 'Weekly on Monday at midnight';
    } else if (expression === '*/15 * * * *') {
      return 'Every 15 minutes';
    } else if (expression === '0 0 1 * *') {
      return 'Monthly on the 1st at midnight';
    }
    
    return 'Custom schedule';
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
  
  formatDuration(startDate, endDate) {
    if (!startDate || !endDate) {
      return 'N/A';
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diff = end - start;
    
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) {
      return `${seconds} seconds`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) {
      return `${minutes} min ${remainingSeconds} sec`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours} hr ${remainingMinutes} min`;
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
  
  // Filter the jobs based on current filters
  getFilteredJobs() {
    let jobs = [];
    
    // Get jobs based on active tab
    switch (this.activeTab) {
      case 'active':
        jobs = [...this.activeJobs];
        break;
      case 'queued':
        jobs = [...this.queuedJobs];
        break;
      case 'completed':
        jobs = [...this.completedJobs];
        break;
      case 'failed':
        jobs = [...this.failedJobs];
        break;
      case 'scheduled':
        jobs = [...this.scheduledJobs];
        break;
    }
    
    // Apply job type filter
    if (this.jobTypeFilter) {
      jobs = jobs.filter(job => job.jobType === this.jobTypeFilter);
    }
    
    // Apply status filter for all except scheduled tab
    if (this.statusFilter && this.activeTab !== 'scheduled') {
      jobs = jobs.filter(job => job.status === this.statusFilter);
    }
    
    // Apply date range filter
    if (this.dateRangeStart) {
      const startDate = new Date(this.dateRangeStart);
      jobs = jobs.filter(job => new Date(job.createdAt) >= startDate);
    }
    
    if (this.dateRangeEnd) {
      const endDate = new Date(this.dateRangeEnd);
      endDate.setHours(23, 59, 59, 999); // End of the day
      jobs = jobs.filter(job => new Date(job.createdAt) <= endDate);
    }
    
    // Apply search filter
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      jobs = jobs.filter(job => 
        job.name.toLowerCase().includes(term) || 
        job.description.toLowerCase().includes(term) ||
        job.id.toLowerCase().includes(term) ||
        job.jobType.toLowerCase().includes(term)
      );
    }
    
    return jobs;
  }
  
  // Get paginated jobs
  getPaginatedJobs() {
    const filteredJobs = this.getFilteredJobs();
    this.totalItems = filteredJobs.length;
    
    const startIndex = (this.page - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    
    return filteredJobs.slice(startIndex, endIndex);
  }
  
  toggleAutoRefresh() {
    this.autoRefresh = !this.autoRefresh;
    
    if (this.autoRefresh) {
      this._startAutoRefresh();
      this._showNotification('Auto-refresh enabled', 'info');
    } else {
      this._stopAutoRefresh();
      this._showNotification('Auto-refresh disabled', 'info');
    }
  }
  
  // Render methods for different sections
  renderMetricsPanel() {
    return html`
      <div class="metrics-panel">
        <div class="metric-card">
          <div class="metric-label">Active Jobs</div>
          <div class="metric-value" style="color: #2196F3;">${this.systemMetrics.activeJobs}</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-label">Queued Jobs</div>
          <div class="metric-value" style="color: #9C27B0;">${this.systemMetrics.queuedJobs}</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-label">Completed Today</div>
          <div class="metric-value" style="color: #4CAF50;">${this.systemMetrics.completedJobsToday}</div>
        </div>
        
        <div class="metric-card">
          <div class="metric-label">Failed Today</div>
          <div class="metric-value" style="color: #F44336;">${this.systemMetrics.failedJobsToday}</div>
        </div>
      </div>
    `;
  }
  
  renderFilterBar() {
    // Extract unique job types for the filter
    let allJobs = [];
    switch(this.activeTab) {
      case 'active':
        allJobs = this.activeJobs;
        break;
      case 'queued':
        allJobs = this.queuedJobs;
        break;
      case 'completed':
        allJobs = this.completedJobs;
        break;
      case 'failed':
        allJobs = this.failedJobs;
        break;
      case 'scheduled':
        allJobs = this.scheduledJobs;
        break;
    }
    
    const jobTypes = [...new Set(allJobs.map(job => job.jobType))];
    
    return html`
      <div class="filter-bar">
        <wa-input 
          class="filter-input"
          placeholder="Search jobs..."
          .value=${this.searchTerm}
          @input=${this.handleSearchChange}>
          <wa-icon slot="prefix" name="search"></wa-icon>
        </wa-input>
        
        <wa-select
          class="filter-select"
          placeholder="Job Type"
          .value=${this.jobTypeFilter}
          @change=${this.handleJobTypeFilterChange}>
          <wa-option value="">All Types</wa-option>
          ${jobTypes.map(type => html`
            <wa-option value=${type}>${this._capitalizeFirstLetter(type)}</wa-option>
          `)}
        </wa-select>
        
        ${this.activeTab !== 'scheduled' ? html`
          <wa-select
            class="filter-select"
            placeholder="Status"
            .value=${this.statusFilter}
            @change=${this.handleStatusFilterChange}>
            <wa-option value="">All Statuses</wa-option>
            <wa-option value="active">Active</wa-option>
            <wa-option value="queued">Queued</wa-option>
            <wa-option value="completed">Completed</wa-option>
            <wa-option value="failed">Failed</wa-option>
          </wa-select>
        ` : ''}
        
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
        
        ${this.activeTab === 'scheduled' ? html`
          <wa-button @click=${this.openCreateSchedule} color="primary">
            <wa-icon slot="prefix" name="add"></wa-icon>
            Create Schedule
          </wa-button>
        ` : ''}
      </div>
    `;
  }
  
  renderRefreshBar() {
    return html`
      <div class="refresh-info">
        <wa-button 
          variant=${this.autoRefresh ? 'outlined' : 'text'} 
          @click=${this.toggleAutoRefresh}
          size="small">
          <wa-icon name=${this.autoRefresh ? 'pause' : 'play_arrow'}></wa-icon>
          ${this.autoRefresh ? 'Pause' : 'Resume'} Auto-refresh
        </wa-button>
        
        <wa-button 
          variant="text" 
          @click=${this.refreshData}
          size="small">
          <wa-icon name="refresh"></wa-icon>
          Refresh
        </wa-button>
        
        <span>Last updated: ${this.lastRefresh}</span>
      </div>
    `;
  }
  
  renderActiveJobsTable() {
    const jobs = this.getPaginatedJobs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Job</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Started</wa-table-cell>
              <wa-table-cell>Progress</wa-table-cell>
              <wa-table-cell>Priority</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${jobs.map(job => html`
              <wa-table-row @click=${() => this.openJobDetail(job)}>
                <wa-table-cell>
                  <div style="font-weight: 500;">${job.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${job.id}</div>
                </wa-table-cell>
                <wa-table-cell>${this._capitalizeFirstLetter(job.jobType)}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(job.startedAt)}</wa-table-cell>
                <wa-table-cell>
                  <div class="progress-container">
                    <wa-progress 
                      class="progress-bar"
                      value=${job.progress}
                      max="100"></wa-progress>
                    <div class="progress-value">${job.progress}%</div>
                  </div>
                </wa-table-cell>
                <wa-table-cell>
                  <wa-badge color=${job.priority === 'high' ? 'error' : job.priority === 'medium' ? 'warning' : 'info'}>
                    ${this._capitalizeFirstLetter(job.priority)}
                  </wa-badge>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="job-actions">
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openCancelDialog(job); }}>
                      <wa-icon name="cancel"></wa-icon>
                    </wa-button>
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openJobDetail(job); }}>
                      <wa-icon name="info"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
      </div>
    `;
  }
  
  renderQueuedJobsTable() {
    const jobs = this.getPaginatedJobs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Job</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Created</wa-table-cell>
              <wa-table-cell>Priority</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${jobs.map(job => html`
              <wa-table-row @click=${() => this.openJobDetail(job)}>
                <wa-table-cell>
                  <div style="font-weight: 500;">${job.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${job.id}</div>
                </wa-table-cell>
                <wa-table-cell>${this._capitalizeFirstLetter(job.jobType)}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(job.createdAt)}</wa-table-cell>
                <wa-table-cell>
                  <wa-badge color=${job.priority === 'high' ? 'error' : job.priority === 'medium' ? 'warning' : 'info'}>
                    ${this._capitalizeFirstLetter(job.priority)}
                  </wa-badge>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="job-actions">
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openCancelDialog(job); }}>
                      <wa-icon name="cancel"></wa-icon>
                    </wa-button>
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openJobDetail(job); }}>
                      <wa-icon name="info"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
      </div>
    `;
  }
  
  renderCompletedJobsTable() {
    const jobs = this.getPaginatedJobs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Job</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Completed</wa-table-cell>
              <wa-table-cell>Duration</wa-table-cell>
              <wa-table-cell>Result</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${jobs.map(job => html`
              <wa-table-row @click=${() => this.openJobDetail(job)}>
                <wa-table-cell>
                  <div style="font-weight: 500;">${job.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${job.id}</div>
                </wa-table-cell>
                <wa-table-cell>${this._capitalizeFirstLetter(job.jobType)}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(job.completedAt)}</wa-table-cell>
                <wa-table-cell>${this.formatDuration(job.startedAt, job.completedAt)}</wa-table-cell>
                <wa-table-cell>
                  ${job.result ? `${job.result.recordsProcessed} records` : 'N/A'}
                </wa-table-cell>
                <wa-table-cell>
                  <div class="job-actions">
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openJobDetail(job); }}>
                      <wa-icon name="info"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
      </div>
    `;
  }
  
  renderFailedJobsTable() {
    const jobs = this.getPaginatedJobs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Job</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Failed</wa-table-cell>
              <wa-table-cell>Error</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${jobs.map(job => html`
              <wa-table-row @click=${() => this.openJobDetail(job)}>
                <wa-table-cell>
                  <div style="font-weight: 500;">${job.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${job.id}</div>
                </wa-table-cell>
                <wa-table-cell>${this._capitalizeFirstLetter(job.jobType)}</wa-table-cell>
                <wa-table-cell>${this.formatRelativeTime(job.completedAt)}</wa-table-cell>
                <wa-table-cell>
                  <div style="color: var(--wa-error-color);">${job.error || 'Unknown error'}</div>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="job-actions">
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openRetryDialog(job); }}>
                      <wa-icon name="replay"></wa-icon>
                    </wa-button>
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openJobDetail(job); }}>
                      <wa-icon name="info"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
      </div>
    `;
  }
  
  renderScheduledJobsTable() {
    const jobs = this.getPaginatedJobs();
    
    return html`
      <div class="table-container">
        <wa-table>
          <wa-table-header>
            <wa-table-row>
              <wa-table-cell>Schedule</wa-table-cell>
              <wa-table-cell>Type</wa-table-cell>
              <wa-table-cell>Schedule</wa-table-cell>
              <wa-table-cell>Next Run</wa-table-cell>
              <wa-table-cell>Last Run</wa-table-cell>
              <wa-table-cell>Status</wa-table-cell>
              <wa-table-cell>Actions</wa-table-cell>
            </wa-table-row>
          </wa-table-header>
          
          <wa-table-body>
            ${jobs.map(job => html`
              <wa-table-row @click=${() => this.openJobDetail(job)}>
                <wa-table-cell>
                  <div style="font-weight: 500;">${job.name}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">${job.id}</div>
                </wa-table-cell>
                <wa-table-cell>${this._capitalizeFirstLetter(job.jobType)}</wa-table-cell>
                <wa-table-cell>
                  <div class="cron-expression">${job.cronExpression}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">
                    ${this.getCronDescription(job.cronExpression)}
                  </div>
                </wa-table-cell>
                <wa-table-cell>${this.formatDateTime(job.nextRun)}</wa-table-cell>
                <wa-table-cell>${job.lastRun ? this.formatDateTime(job.lastRun) : 'Never'}</wa-table-cell>
                <wa-table-cell>
                  <wa-badge color=${job.enabled ? 'success' : 'default'}>
                    ${job.enabled ? 'Enabled' : 'Disabled'}
                  </wa-badge>
                </wa-table-cell>
                <wa-table-cell>
                  <div class="job-actions">
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.toggleScheduleStatus(job); }}>
                      <wa-icon name=${job.enabled ? 'pause' : 'play_arrow'}></wa-icon>
                    </wa-button>
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.deleteSchedule(job); }}>
                      <wa-icon name="delete"></wa-icon>
                    </wa-button>
                    <wa-button variant="text" size="small" @click=${(e) => { e.stopPropagation(); this.openJobDetail(job); }}>
                      <wa-icon name="info"></wa-icon>
                    </wa-button>
                  </div>
                </wa-table-cell>
              </wa-table-row>
            `)}
          </wa-table-body>
        </wa-table>
        
        ${this.renderPagination()}
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
          <wa-option value="5">5</wa-option>
          <wa-option value="10">10</wa-option>
          <wa-option value="25">25</wa-option>
          <wa-option value="50">50</wa-option>
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
  
  renderJobDetailDialog() {
    if (!this.selectedJob) return html``;
    
    const job = this.selectedJob;
    const isSchedule = this.activeTab === 'scheduled';
    
    return html`
      <wa-dialog 
        ?open=${this.showJobDetailDialog}
        @close=${this.closeJobDetail}
        title=${isSchedule ? 'Schedule Detail' : 'Job Detail'}>
        
        <div class="dialog-content">
          <!-- Basic Information -->
          <div class="job-detail-section">
            <div class="job-detail-header">Basic Information</div>
            
            <div class="job-detail-property">
              <div class="job-detail-label">ID</div>
              <div class="job-detail-value">${job.id}</div>
            </div>
            
            <div class="job-detail-property">
              <div class="job-detail-label">Name</div>
              <div class="job-detail-value">${job.name}</div>
            </div>
            
            <div class="job-detail-property">
              <div class="job-detail-label">Description</div>
              <div class="job-detail-value">${job.description}</div>
            </div>
            
            <div class="job-detail-property">
              <div class="job-detail-label">Type</div>
              <div class="job-detail-value">${this._capitalizeFirstLetter(job.jobType)}</div>
            </div>
            
            ${isSchedule ? html`
              <div class="job-detail-property">
                <div class="job-detail-label">Schedule</div>
                <div class="job-detail-value">
                  <div class="cron-expression">${job.cronExpression}</div>
                  <div style="font-size: 12px; color: var(--wa-text-secondary-color);">
                    ${this.getCronDescription(job.cronExpression)}
                  </div>
                </div>
              </div>
              
              <div class="job-detail-property">
                <div class="job-detail-label">Status</div>
                <div class="job-detail-value">
                  <wa-badge color=${job.enabled ? 'success' : 'default'}>
                    ${job.enabled ? 'Enabled' : 'Disabled'}
                  </wa-badge>
                </div>
              </div>
            ` : html`
              <div class="job-detail-property">
                <div class="job-detail-label">Status</div>
                <div class="job-detail-value">
                  <span class="status-badge status-${job.status}">
                    ${this._capitalizeFirstLetter(job.status)}
                  </span>
                </div>
              </div>
              
              ${job.status === 'active' ? html`
                <div class="job-detail-property">
                  <div class="job-detail-label">Progress</div>
                  <div class="job-detail-value">
                    <div class="progress-container">
                      <wa-progress 
                        class="progress-bar"
                        value=${job.progress}
                        max="100"></wa-progress>
                      <div class="progress-value">${job.progress}%</div>
                    </div>
                  </div>
                </div>
              ` : ''}
              
              <div class="job-detail-property">
                <div class="job-detail-label">Priority</div>
                <div class="job-detail-value">
                  <wa-badge color=${job.priority === 'high' ? 'error' : job.priority === 'medium' ? 'warning' : 'info'}>
                    ${this._capitalizeFirstLetter(job.priority)}
                  </wa-badge>
                </div>
              </div>
            `}
          </div>
          
          <!-- Timing Information -->
          <div class="job-detail-section">
            <div class="job-detail-header">Timing Information</div>
            
            <div class="job-detail-property">
              <div class="job-detail-label">Created</div>
              <div class="job-detail-value">${this.formatDateTime(job.createdAt)}</div>
            </div>
            
            ${isSchedule ? html`
              <div class="job-detail-property">
                <div class="job-detail-label">Next Run</div>
                <div class="job-detail-value">${this.formatDateTime(job.nextRun)}</div>
              </div>
              
              <div class="job-detail-property">
                <div class="job-detail-label">Last Run</div>
                <div class="job-detail-value">${job.lastRun ? this.formatDateTime(job.lastRun) : 'Never'}</div>
              </div>
            ` : html`
              <div class="job-detail-property">
                <div class="job-detail-label">Started</div>
                <div class="job-detail-value">${job.startedAt ? this.formatDateTime(job.startedAt) : 'Not started'}</div>
              </div>
              
              <div class="job-detail-property">
                <div class="job-detail-label">Completed</div>
                <div class="job-detail-value">${job.completedAt ? this.formatDateTime(job.completedAt) : 'Not completed'}</div>
              </div>
              
              <div class="job-detail-property">
                <div class="job-detail-label">Duration</div>
                <div class="job-detail-value">${this.formatDuration(job.startedAt, job.completedAt)}</div>
              </div>
            `}
          </div>
          
          <!-- Parameters -->
          <div class="job-detail-section">
            <div class="job-detail-header">Parameters</div>
            
            <div class="code-block">
              ${JSON.stringify(job.parameters, null, 2)}
            </div>
          </div>
          
          ${!isSchedule && job.result ? html`
            <!-- Result -->
            <div class="job-detail-section">
              <div class="job-detail-header">Result</div>
              
              <div class="code-block">
                ${JSON.stringify(job.result, null, 2)}
              </div>
            </div>
          ` : ''}
          
          ${!isSchedule && job.error ? html`
            <!-- Error -->
            <div class="job-detail-section">
              <div class="job-detail-header">Error</div>
              
              <div class="code-block" style="color: var(--wa-error-color);">
                ${job.error}
              </div>
            </div>
          ` : ''}
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeJobDetail} variant="text">
            Close
          </wa-button>
          
          ${!isSchedule && job.status === 'failed' ? html`
            <wa-button @click=${() => { this.closeJobDetail(); this.openRetryDialog(job); }} color="primary">
              <wa-icon slot="prefix" name="replay"></wa-icon>
              Retry
            </wa-button>
          ` : ''}
          
          ${!isSchedule && (job.status === 'active' || job.status === 'queued') ? html`
            <wa-button @click=${() => { this.closeJobDetail(); this.openCancelDialog(job); }} color="error">
              <wa-icon slot="prefix" name="cancel"></wa-icon>
              Cancel
            </wa-button>
          ` : ''}
          
          ${isSchedule ? html`
            <wa-button @click=${() => { this.closeJobDetail(); this.toggleScheduleStatus(job); }} color="primary">
              <wa-icon slot="prefix" name=${job.enabled ? 'pause' : 'play_arrow'}></wa-icon>
              ${job.enabled ? 'Disable' : 'Enable'}
            </wa-button>
          ` : ''}
        </div>
      </wa-dialog>
    `;
  }
  
  renderCreateScheduleDialog() {
    const jobTypes = ['data-sync', 'email-notification', 'report-generation', 'data-cleanup', 'backup', 'import', 'export'];
    
    return html`
      <wa-dialog 
        ?open=${this.showCreateScheduleDialog}
        @close=${this.closeCreateSchedule}
        title="Create Schedule">
        
        <div class="dialog-content">
          <div class="form-grid">
            <wa-input
              label="Name"
              name="name"
              .value=${this.scheduleForm.name}
              @input=${this.handleScheduleFormChange}
              required>
            </wa-input>
            
            <wa-select
              label="Job Type"
              name="jobType"
              .value=${this.scheduleForm.jobType}
              @change=${this.handleScheduleFormChange}
              required>
              <wa-option value="">Select job type</wa-option>
              ${jobTypes.map(type => html`
                <wa-option value=${type}>${this._capitalizeFirstLetter(type)}</wa-option>
              `)}
            </wa-select>
          </div>
          
          <wa-textarea
            label="Description"
            name="description"
            .value=${this.scheduleForm.description}
            @input=${this.handleScheduleFormChange}
            style="margin-top: 16px;">
          </wa-textarea>
          
          <div style="margin-top: 16px;">
            <div style="font-weight: 500; margin-bottom: 8px;">Schedule (Cron Expression)</div>
            <wa-input
              name="cronExpression"
              .value=${this.scheduleForm.cronExpression}
              @input=${this.handleScheduleFormChange}
              required>
            </wa-input>
            
            <div style="font-size: 12px; color: var(--wa-text-secondary-color); margin-top: 4px;">
              ${this.getCronDescription(this.scheduleForm.cronExpression) || 'Enter a valid cron expression'}
            </div>
          </div>
          
          <div style="margin-top: 16px;">
            <wa-checkbox
              label="Enabled"
              name="enabled"
              ?checked=${this.scheduleForm.enabled}
              @change=${this.handleScheduleFormChange}>
            </wa-checkbox>
          </div>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeCreateSchedule} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.createSchedule} color="primary">
            Create
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderRetryDialog() {
    if (!this.selectedJob) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showRetryDialog}
        @close=${this.closeRetryDialog}
        title="Retry Job">
        
        <div class="dialog-content">
          <p>Are you sure you want to retry the failed job "${this.selectedJob.name}"?</p>
          <p>This will create a new job with the same parameters.</p>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeRetryDialog} variant="text">
            Cancel
          </wa-button>
          <wa-button @click=${this.retryJob} color="primary">
            Retry
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }
  
  renderCancelDialog() {
    if (!this.selectedJob) return html``;
    
    return html`
      <wa-dialog 
        ?open=${this.showCancelDialog}
        @close=${this.closeCancelDialog}
        title="Cancel Job">
        
        <div class="dialog-content">
          <p>Are you sure you want to cancel the job "${this.selectedJob.name}"?</p>
          <p>This action cannot be undone.</p>
        </div>
        
        <div class="dialog-actions">
          <wa-button @click=${this.closeCancelDialog} variant="text">
            Back
          </wa-button>
          <wa-button @click=${this.cancelJob} color="error">
            Cancel Job
          </wa-button>
        </div>
      </wa-dialog>
    `;
  }

  render() {
    return html`
      <div class="container">
        <div class="header">
          <h1 class="title">Job Dashboard</h1>
          <p class="subtitle">Monitor and manage background tasks and scheduled jobs</p>
        </div>
        
        ${this.renderMetricsPanel()}
        ${this.renderRefreshBar()}
        
        <wa-tabs 
          value=${this.activeTab}
          @change=${this.handleTabChange}>
          <wa-tab value="active">Active (${this.activeJobs.length})</wa-tab>
          <wa-tab value="queued">Queued (${this.queuedJobs.length})</wa-tab>
          <wa-tab value="completed">Completed</wa-tab>
          <wa-tab value="failed">Failed (${this.failedJobs.length})</wa-tab>
          <wa-tab value="scheduled">Scheduled</wa-tab>
        </wa-tabs>
        
        <div class="content-card">
          ${this.renderFilterBar()}
          
          ${this.activeTab === 'active' ? this.renderActiveJobsTable() : ''}
          ${this.activeTab === 'queued' ? this.renderQueuedJobsTable() : ''}
          ${this.activeTab === 'completed' ? this.renderCompletedJobsTable() : ''}
          ${this.activeTab === 'failed' ? this.renderFailedJobsTable() : ''}
          ${this.activeTab === 'scheduled' ? this.renderScheduledJobsTable() : ''}
        </div>
        
        ${this.loading ? html`
          <div style="position: fixed; top: 16px; right: 16px; z-index: 1000;">
            <wa-spinner size="small"></wa-spinner>
            <span style="margin-left: 8px;">Loading...</span>
          </div>
        ` : ''}
        
        ${this.renderJobDetailDialog()}
        ${this.renderCreateScheduleDialog()}
        ${this.renderRetryDialog()}
        ${this.renderCancelDialog()}
      </div>
    `;
  }
}

customElements.define('wa-job-dashboard', WebAwesomeJobDashboard);