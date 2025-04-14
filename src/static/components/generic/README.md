# Generic CRUD Components

This directory contains reusable components that developers can use to quickly build CRUD (Create, Read, Update, Delete) interfaces for their applications built with the UNO framework.

## WebAwesome CRUD Manager

The `wa-crud-manager` component provides a fully-featured, customizable interface for managing entities with CRUD operations, filtering, pagination, and more.

### Features

- Complete CRUD operations (Create, Read, Update, Delete)
- Multiple view types (table, card, grid)
- Advanced filtering
- Sorting
- Pagination 
- Bulk actions
- Export to CSV
- Responsive design
- Schema-based form generation
- Customizable templates
- Event-based integration

### Basic Usage

```html
<wa-crud-manager
  base-url="/api"
  entity-type="users"
  title="User Management"
  description="Create and manage application users">
</wa-crud-manager>
```

### Schema Configuration

The component uses a schema to define the entity fields, their types, and display properties:

```javascript
// Configure the component with a schema
const crudManager = document.querySelector('wa-crud-manager');
crudManager.schema = {
  fields: [
    {
      name: 'id',
      label: 'ID',
      type: 'number',
      readOnly: true,
      hidden: false,
      sortable: true
    },
    {
      name: 'name',
      label: 'Full Name',
      type: 'string',
      isTitle: true,
      inSummary: true,
      sortable: true,
      filterable: true,
      description: 'User\'s full name'
    },
    {
      name: 'email',
      label: 'Email Address',
      type: 'string',
      inSummary: true,
      sortable: true,
      filterable: true
    },
    {
      name: 'role',
      label: 'User Role',
      type: 'select',
      inSummary: true,
      options: [
        { value: 'admin', label: 'Administrator' },
        { value: 'editor', label: 'Editor' },
        { value: 'user', label: 'Standard User' }
      ],
      filterable: true
    },
    {
      name: 'active',
      label: 'Status',
      type: 'boolean',
      sortable: true,
      filterable: true
    },
    {
      name: 'created_at',
      label: 'Created Date',
      type: 'datetime',
      sortable: true,
      filterable: true
    }
  ]
};
```

### Field Types

The component supports various field types:

- `string` - Text input
- `number` - Numeric input
- `boolean` - True/false switch
- `select` - Dropdown select with options
- `multiselect` - Multi-select dropdown
- `date` - Date picker
- `datetime` - Date and time picker
- `textarea` - Multiline text input
- `status` - Special status formatting

### Custom Actions

You can add custom actions to the entity list:

```javascript
crudManager.customActions = [
  {
    label: 'Send Invitation',
    icon: 'mail',
    color: 'primary',
    handler: (entity) => {
      // Handle the action for this entity
      console.log('Sending invitation to', entity.email);
    }
  },
  {
    label: 'Reset Password',
    icon: 'lock_reset',
    color: 'warning',
    handler: (entity) => {
      // Handle reset password action
      console.log('Reset password for', entity.email);
    }
  },
  // Bulk actions (applied to multiple selected items)
  {
    label: 'Approve Selected',
    icon: 'check_circle',
    color: 'success',
    bulk: true,
    bulkHandler: (selectedIds) => {
      console.log('Approving items with IDs:', selectedIds);
    }
  }
];
```

### Custom Templates

The component allows customizing the rendering of entities:

```javascript
// Custom detail view template
crudManager.detailTemplate = (entity) => {
  return html`
    <div class="custom-detail">
      <div class="user-avatar">
        <img src="${entity.avatar_url || '/assets/default-avatar.png'}" alt="${entity.name}">
      </div>
      <div class="user-info">
        <h2>${entity.name}</h2>
        <p>${entity.email}</p>
        <p>Role: ${entity.role}</p>
        <p>Status: ${entity.active ? 'Active' : 'Inactive'}</p>
      </div>
    </div>
  `;
};

// Custom summary template (for card view)
crudManager.summaryTemplate = (entity) => {
  return html`
    <div class="activity-indicator">
      <wa-icon name="activity"></wa-icon>
      Last login: ${new Date(entity.last_login).toLocaleString()}
    </div>
  `;
};

// Custom form template
crudManager.formTemplate = (entity, handleChange) => {
  return html`
    <div class="custom-form">
      <div class="form-row">
        <label for="name">Name</label>
        <input 
          type="text" 
          name="name" 
          value="${entity.name || ''}" 
          @input=${handleChange}
        >
      </div>
      <!-- Other custom form fields -->
    </div>
  `;
};
```

### API Configuration

The component can be configured to work with different API formats:

```javascript
crudManager.apiOptions = {
  // Response format
  dataPath: 'data.items', // Path to data in response
  totalPath: 'data.meta.total', // Path to total count in response
  
  // Request format
  filterFormat: 'filter[{field}]={value}', // Format for filter params
  sortFormat: 'sort={direction}{field}', // Format for sort params
  paginationFormat: 'page={page}&limit={pageSize}', // Format for pagination
  
  // HTTP methods
  methods: {
    list: 'GET',
    get: 'GET',
    create: 'POST',
    update: 'PATCH', // Some APIs use PATCH instead of PUT
    delete: 'DELETE'
  }
};
```

### Events

The component emits events for various operations:

```javascript
// Listen for entity created event
crudManager.addEventListener('entity-created', (e) => {
  console.log('Entity created:', e.detail.entity);
});

// Listen for entity updated event
crudManager.addEventListener('entity-updated', (e) => {
  console.log('Entity updated:', e.detail.entity);
});

// Listen for entity deleted event
crudManager.addEventListener('entity-deleted', (e) => {
  console.log('Entity deleted, ID:', e.detail.entityId);
});

// Listen for filter changes
crudManager.addEventListener('filter-changed', (e) => {
  console.log('Filter changed:', e.detail.filter);
});

// Listen for sort changes
crudManager.addEventListener('sort-changed', (e) => {
  console.log('Sort changed:', e.detail.sort);
});

// Listen for pagination changes
crudManager.addEventListener('page-changed', (e) => {
  console.log('Page changed:', e.detail.pagination);
});
```

### Properties Reference

| Property | Type | Description |
|----------|------|-------------|
| baseUrl | String | Base URL for the API |
| entityType | String | Type of entity (e.g., "users", "products") |
| title | String | Title displayed at the top of the component |
| description | String | Description displayed under the title |
| schema | Object | Schema definition for the entity |
| icon | String | Icon name for the empty state |
| customActions | Array | Custom actions to display for entities |
| layoutType | String | View type: "table", "grid", or "card" |
| detailTemplate | Function | Custom template for detail view |
| summaryTemplate | Function | Custom template for summary in card view |
| formTemplate | Function | Custom template for edit/create forms |
| enableCreate | Boolean | Enable entity creation |
| enableEdit | Boolean | Enable entity editing |
| enableDelete | Boolean | Enable entity deletion |
| enableExport | Boolean | Enable CSV export |
| enableBulkActions | Boolean | Enable bulk actions |
| enableFiltering | Boolean | Enable filtering |
| enableSorting | Boolean | Enable sorting |
| enablePagination | Boolean | Enable pagination |
| enableDetail | Boolean | Enable detail view |
| apiOptions | Object | API configuration options |
| labels | Object | Customizable text labels |

## Integration with UNO

This component is designed to work seamlessly with UNO's backend API structure and follows the API conventions established in the UNO framework.