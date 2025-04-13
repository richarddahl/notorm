# UNO Reporting System

The UNO Reporting System is a comprehensive solution for building, managing, and visualizing data reports. It provides a flexible architecture for defining report templates, scheduling their execution, and visualizing the results through dashboards.

## Architecture

The reporting system consists of the following key components:

### Frontend Components

1. **Report Template Builder (`report-builder.js` / `webawesome-report-builder.js`)**
   - Allows users to define report templates with fields, triggers, and outputs
   - Supports field types: source fields, calculated fields, SQL queries, and parameters
   - Provides a tabbed interface for organizing the definition process

2. **Report Template List (`report-template-list.js` / `webawesome-report-template-list.js`)**
   - Displays a list of available report templates
   - Supports searching, filtering, and sorting
   - Provides grid and list view options

3. **Report Execution Manager (`report-execution-view.js` / `webawesome-report-execution-manager.js`)**
   - Manages the execution of reports
   - Displays execution history and status
   - Allows scheduling reports with cron expressions
   - Supports passing parameters to report executions

4. **Report Dashboard (`dashboard-controller.js` / `webawesome-dashboard.js`)**
   - Visualizes report data in an interactive dashboard
   - Supports filtering and date range selection
   - Allows layout customization with grid positioning

5. **Report Widget (`report-widget.js` / `webawesome-report-widget.js`)**
   - Individual visualization components used in dashboards
   - Supports metrics, charts, and tables
   - Uses Chart.js for data visualization

### Backend Services (API Endpoints)

1. **Template Management**
   - `/api/reports/templates` - CRUD operations for report templates
   - `/api/reports/templates/{id}` - Get, update or delete specific template
   - `/api/reports/entities` - Get available entity types
   - `/api/reports/entities/{type}/fields` - Get fields for an entity type

2. **Report Execution**
   - `/api/reports/executions` - Create and list report executions
   - `/api/reports/executions/{id}` - Get execution details
   - `/api/reports/executions/{id}/result` - Get execution results in various formats
   - `/api/reports/executions/status` - Get status updates for multiple executions

3. **Schedule Management**
   - `/api/reports/schedules` - CRUD operations for report schedules
   - `/api/reports/schedules/{id}` - Get, update or delete specific schedule

4. **Dashboard Management**
   - `/api/reports/dashboards` - CRUD operations for dashboards
   - `/api/reports/dashboards/{id}` - Get, update or delete specific dashboard
   - `/api/reports/dashboards/{id}/export` - Export dashboard in various formats
   - `/api/reports/dashboard` - Get data for dashboard widgets

## Features

### Report Templates

- **Field Types**
  - Source Fields: Direct data from entity properties
  - Calculated Fields: Formula-based calculations
  - Parameters: User-provided values for filtering
  - SQL Queries: Custom SQL for complex data extraction

- **Triggers**
  - Schedule: Time-based execution using cron expressions
  - Event: Execute when specific system events occur
  - API: On-demand execution via API
  - Query: Execute when query conditions are met

- **Outputs**
  - PDF: Generate PDF documents
  - Excel: Generate Excel spreadsheets
  - Email: Send report via email
  - Webhook: Send data to external systems
  - Dashboard: Display on interactive dashboards

### Report Execution

- Manual execution with parameter specification
- Scheduled execution using cron expressions
- Execution history with status tracking
- Result downloads in various formats (CSV, JSON, PDF, Excel)

### Dashboards

- Interactive data visualization
- Multiple chart types: line, bar, pie, etc.
- Metric widgets for KPIs
- Table widgets for detailed data
- Customizable layouts with drag-and-drop
- Auto-refresh capabilities
- Date range filtering

## Web Component Implementations

The reporting system is implemented as web components using two approaches:

1. **Base Implementation** (LitElement)
   - Standard web components using LitElement
   - Custom CSS styling

2. **WebAwesome Implementation**
   - Enhanced version using WebAwesome UI components
   - Consistent styling with WebAwesome design system
   - Improved accessibility and user experience

## Usage Examples

### Creating a Report Template

```javascript
// Using the report builder to create a template
const builder = document.createElement('wa-report-builder');
builder.mode = 'create';
builder.availableEntities = [
  { value: 'customer', label: 'Customer' },
  { value: 'order', label: 'Order' }
];
document.body.appendChild(builder);

// Listen for save events
builder.addEventListener('template-saved', (e) => {
  console.log('Template saved:', e.detail.template);
});
```

### Displaying a Dashboard

```javascript
// Create a dashboard with reports
const dashboard = document.createElement('wa-dashboard');
dashboard.reportIds = ['report-1', 'report-2', 'report-3'];
dashboard.dateRange = {
  start: '2023-01-01',
  end: '2023-12-31'
};
dashboard.refreshInterval = 300; // 5 minutes
document.body.appendChild(dashboard);

// Listen for data load events
dashboard.addEventListener('data-loaded', (e) => {
  console.log('Dashboard data loaded:', e.detail.data);
});
```

### Executing a Report

```javascript
// Create execution manager for a specific template
const executionManager = document.createElement('wa-report-execution-manager');
executionManager.templateId = 'template-1';
document.body.appendChild(executionManager);

// The manager handles:
// - Manual executions
// - Schedule management
// - Execution history viewing
```

## Integration with UNO Framework

The reporting system integrates with the UNO framework through:

1. **Entity Integration**: Reports can be defined against any UNO entity
2. **Security**: Leverages UNO authorization for data access control
3. **Async Support**: Uses UNO's async architecture for non-blocking operations
4. **Event-Driven**: Integrates with UNO's event system for triggers and notifications
5. **Error Handling**: Uses UNO's Result pattern for consistent error management

## Styling and Theming

The WebAwesome-based components support comprehensive theming through CSS variables:

- Light/dark mode switching
- Custom color palettes
- Responsive layouts for mobile and desktop
- Accessibility features

## Development

### Prerequisites

- UNO framework
- LitElement
- Chart.js
- WebAwesome components

### Testing

The reporting system includes:

- Unit tests for core functionality
- Integration tests for API endpoints
- Visual regression tests for UI components
- End-to-end tests for critical user flows

### Building

Build process uses standard UNO build tools with steps for:

1. Component compilation
2. CSS processing
3. Asset optimization
4. API documentation generation

## Future Enhancements

- Real-time data streaming for dashboards
- Advanced visualization types (heatmaps, geographic maps)
- AI-powered report insights and anomaly detection
- Enhanced collaboration features (sharing, comments)
- Mobile app support