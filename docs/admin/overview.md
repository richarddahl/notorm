# UNO Admin Interface

The UNO Admin Interface provides a comprehensive administrative dashboard for managing various aspects of the UNO framework. It offers an intuitive web-based interface for tasks like role management, system monitoring, vector search, and report generation.

## Accessing the Admin Interface

The admin interface is available at `/admin` after starting the UNO application.

```bash
# Start the UNO application
hatch run dev:app

# Access the admin interface
# http://localhost:8000/admin
```

## Modules

The admin interface consists of several modules:

### Admin Dashboard

The main administrative dashboard provides a system overview with real-time statistics, recent activity, and quick access to other modules.

- System statistics (request rates, user counts, error rates)
- Performance metrics (CPU, memory, database connections)
- Activity logs
- System health status

### Role Management

The authorization module provides a comprehensive interface for managing roles and permissions in the RBAC system.

- Role creation and management
- Permission assignment
- User role assignments
- Permission hierarchies

### System Monitor

The monitoring module offers real-time system health and performance monitoring.

- Performance metrics visualization
- Health check status
- Log viewer
- Alert management
- Request tracing

### Vector Search

The vector search module provides an interface for semantic search using pgvector.

- Natural language query interface
- Search result visualization with similarity scores
- Vector index statistics
- Search settings configuration

### Reports

The reporting module allows creating, viewing, and managing reports.

- Report builder interface
- Report templates
- Scheduled reports
- Report dashboard

## Technology Stack

The admin interface is built using modern web technologies:

- **WebAwesome**: UI component system built on LitElement
- **LitElement**: Web component base library
- **Shoelace**: Web component library for UI elements
- **Chart.js**: Data visualization
- **FastAPI**: Backend API
- **UNO Framework**: Core functionality

## Configuration

The admin interface inherits configuration from the UNO application settings. Additional configuration options can be found in `settings.py`.

## Security

Access to the admin interface is controlled through UNO's authentication and authorization system. Only users with appropriate admin permissions can access the interface.

## Customization

The admin interface can be customized by:

1. Adding new WebAwesome components
2. Extending existing modules with new features
3. Customizing the theme through CSS variables
4. Adding new API endpoints for admin functionality

## Development

When developing new admin features:

1. Add frontend components in `/src/static/components/`
2. Add backend API endpoints in `/src/uno/api/admin_ui.py`
3. Update documentation in `/docs/admin/`

For more information on the component architecture, see the [WebAwesome Components README](../developer_tools/images/README.md).