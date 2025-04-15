# Query UI Component Proposal

## Overview

This document proposes the development of a UI component for configuring QueryModel conditions in uno's workflow module. The component will enable non-technical users to build complex graph-based queries without understanding the underlying technical implementation.

## Goals

1. **User Empowerment**: Allow non-technical users to create complex graph-based queries
2. **Visual Representation**: Provide intuitive visualization of graph paths and relationships
3. **Workflow Integration**: Seamlessly integrate with the workflow condition configuration UI
4. **Live Feedback**: Provide real-time validation and preview of query results
5. **Reusability**: Design components that can be used in other parts of the application

## User Experience

### Query Builder Interface

The Query Builder will provide a visual interface for constructing graph paths:

- **Entity Type Selection**: Dropdown to select the source entity type
- **Relationship Visualization**: Interactive graph showing available relationships
- **Path Construction**: Click-to-build paths between entity types
- **Condition Groups**: Visual grouping of conditions with AND/OR logic
- **Condition Description**: Natural language explanation of the constructed query

### Condition Editor

For each path in the query, users can configure filtering conditions:

- **Lookup Type Selection**: Dropdown for selecting comparison type (equals, contains, etc.)
- **Value Input**: Context-sensitive input fields based on the data type
- **Multi-Value Support**: Interface for defining lists of values
- **Range Selection**: Min/max inputs for range-based lookups
- **Property Selectors**: For complex objects with multiple properties

### Testing & Preview

To validate queries before saving:

- **Match Count**: Real-time display of how many records match the query
- **Sample Matches**: Table showing sample matching records
- **Explain View**: Natural language explanation of the query logic
- **Performance Indicators**: Visual feedback on query complexity and performance

### Workflow Integration

For integrating with the workflow system:

- **Condition Selection**: Option to use saved queries or create new ones
- **Query Library**: Browse and search existing queries
- **Context Variables**: Access to event context variables in queries
- **Condition Negation**: Option to negate query results (NOT logic)

## Technical Architecture

### Frontend Components

1. **QueryBuilder**: Main container component
   - **EntitySelector**: For choosing entity types
   - **RelationshipGraph**: Visual graph representation of relationships 
   - **PathBuilder**: Interface for constructing paths
   - **ConditionGroup**: Container for grouping conditions
   - **ConditionEditor**: Interface for configuring individual conditions
   - **ResultPreview**: Shows query match results

2. **State Management**:
   - Query definition model
   - UI state management
   - Validation state

### Backend Integration

1. **API Endpoints**:
   - `/api/queries/entity-types`: Available entity types
   - `/api/queries/relationships`: Relationships between entity types
   - `/api/queries/validate`: Validate a query definition
   - `/api/queries/preview`: Execute a query and return preview results
   - `/api/queries/save`: Save a query definition

2. **Data Models**:
   - `QueryDefinition`: Complete query specification
   - `QueryPath`: Path between entity types
   - `QueryCondition`: Filtering condition
   - `QueryPreview`: Preview results for a query

## Implementation Plan

### Phase 1: Core Components

1. Develop basic entity and relationship visualization
2. Implement path selection interface
3. Create condition editor for simple conditions
4. Build query preview functionality

### Phase 2: Advanced Features

1. Add support for complex condition grouping (AND/OR logic)
2. Implement path suggestion based on common usage patterns
3. Develop the query library for saved queries
4. Create natural language query explanation

### Phase 3: Workflow Integration

1. Integrate with workflow condition editor
2. Add support for event context variables in queries
3. Implement condition negation
4. Create templates for common query patterns

### Phase 4: Performance & Optimization

1. Implement query validation and optimization suggestions
2. Add performance indicators
3. Develop caching strategies for query previews
4. Optimize rendering for complex query visualizations

## Technical Challenges

1. **Graph Visualization**: Efficiently rendering complex relationship graphs
2. **Query Optimization**: Providing guidance for efficient query construction
3. **Real-time Preview**: Balancing responsiveness with accurate previews
4. **Intuitive UX**: Making complex graph concepts accessible to non-technical users

## Success Metrics

1. **Adoption Rate**: Percentage of workflow conditions using query matching
2. **Complexity Handling**: Ability to represent increasingly complex business rules
3. **User Satisfaction**: Feedback from workflow administrators
4. **Performance**: Response time for query previews and validations

## Future Extensions

1. **Query Templates**: Library of pre-built query patterns for common scenarios
2. **AI Assistance**: Natural language to query conversion
3. **Query Analytics**: Usage statistics and optimization recommendations
4. **Collaborative Editing**: Multi-user editing of query definitions
5. **Version Control**: History and comparison of query versions

## Conclusion

The Query UI Component will significantly enhance the power and flexibility of uno by enabling non-technical users to leverage the graph database for complex conditional logic in workflows. By providing an intuitive visual interface, the component bridges the gap between sophisticated query capabilities and business-oriented workflow configuration.

OTHER STUFF:

  1. Integration Testing: Create integration tests that verify the entire flow from query definition to workflow execution.
  2. Query Optimization Documentation: Expand documentation with best practices for optimizing complex queries.
  3. Additional Lookup Types: Implement more specialized lookup types for specific use cases.
  4. Query Templates: Create pre-defined query templates for common business scenarios.
  5. Advanced Graph Traversal: Enhance the QueryExecutor to support more complex graph traversal patterns.
  6. Exporting/Importing Queries: Add functionality to export and import query definitions.
