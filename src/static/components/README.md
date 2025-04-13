# UNO WebAwesome UI Components

This directory contains the WebAwesome UI components for the UNO framework's admin interface. These components are built using LitElement and provide a comprehensive administrative interface for managing the various modules of the UNO framework.

## Component Structure

The components are organized by module:

- **app**: Application shell and global components
  - `wa-app-shell.js`: Main application shell with navigation and layout

- **admin**: Dashboard components
  - `wa-admin-dashboard.js`: Administrative dashboard with system overview

- **authorization**: Role-based access control management
  - `wa-role-manager.js`: Interface for managing roles and permissions

- **monitoring**: System monitoring and health dashboard
  - `wa-system-monitor.js`: Monitoring dashboard with metrics and health checks

- **vector-search**: Vector search interface
  - `wa-semantic-search.js`: Interface for semantic search using pgvector

- **reports**: Reporting system components
  - `webawesome-report-builder.js`: Report creation and management interface
  - `webawesome-report-widget.js`: Individual report widgets
  - `webawesome-dashboard.js`: Report dashboard

## Technology Stack

- **LitElement**: Web component base library
- **Shoelace**: Web component library for UI elements
- **Chart.js**: Data visualization library
- **CSS Variables**: For theming support
- **Shadow DOM**: For component encapsulation

## Features

- **Responsive Design**: All components adapt to different screen sizes
- **Dark/Light Mode**: Comprehensive theme support
- **Module Navigation**: Sidebar navigation with module grouping
- **Interactive Dashboards**: Real-time data visualization
- **Role Management**: Comprehensive RBAC interface
- **System Monitoring**: Performance metrics and health checks
- **Vector Search**: Semantic search interface with similarity visualization
- **Report Builder**: Flexible report creation and management

## Usage

To access the admin interface, navigate to `/admin` after starting the UNO application.

```bash
# Start the UNO application
hatch run dev:app

# Access the admin interface
# http://localhost:8000/admin
```

## Development

When developing new components, follow these conventions:

1. Prefix WebAwesome components with `wa-`
2. Use LitElement reactive properties for state management
3. Implement dark/light theme support
4. Use Shadow DOM for style encapsulation
5. Follow the established component structure pattern
6. Emit events with the `wa:` prefix for component communication

## Integration with UNO

The WebAwesome components integrate with UNO through the FastAPI backend. The main integration points are:

- **Data Retrieval**: Components fetch data from UNO API endpoints
- **Authentication**: Components use the UNO authentication system
- **Authorization**: Components respect UNO's RBAC permissions
- **Event System**: Components integrate with UNO's event system for real-time updates

## Contributing

When adding new components:

1. Follow the established naming and organization conventions
2. Add documentation for your components
3. Ensure components work in both dark and light themes
4. Test responsiveness on different screen sizes
5. Ensure accessibility compliance