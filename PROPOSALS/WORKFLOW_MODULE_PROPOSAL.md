# Workflow Module: Implementation Proposal

## Executive Summary

This document outlines a proposal for expanding the workflows module in the Uno framework to enable tenant administrators to define and manage custom notification workflows for database events without requiring developer intervention.

## Current State

The workflows module exists in a preliminary state with basic model scaffolding but lacks the comprehensive functionality needed for business users to define notification rules. Meanwhile, the Uno framework includes a robust event system that provides the technical foundation for event processing.

## Vision

Develop the workflows module into a complete workflow engine that allows non-technical users to create, manage, and deploy custom notification rules based on database events, integrated with the existing event system for execution.

## Proposed Architecture

### 1. Data Model

#### Workflow Definition
```python
class WorkflowDefinition(UnoModel):
    """Defines a workflow that can be triggered by database events."""
    id = Column(String, primary_key=True, default=gen_ulid)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(Enum('active', 'inactive', 'draft'), default='draft')
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tenant_id = Column(String, nullable=False)
```

#### Workflow Trigger
```python
class WorkflowTrigger(UnoModel):
    """Defines what triggers a workflow."""
    id = Column(String, primary_key=True, default=gen_ulid)
    workflow_id = Column(String, ForeignKey('workflow_definition.id'), nullable=False)
    entity_type = Column(String, nullable=False)  # e.g., 'user', 'order'
    operation = Column(Enum('create', 'update', 'delete'), nullable=False)
    field_conditions = Column(JSONB)  # e.g., {"status": "approved"}
    priority = Column(Integer, default=100)
```

#### Workflow Condition
```python
class WorkflowCondition(UnoModel):
    """Additional conditions that must be met for workflow to execute."""
    id = Column(String, primary_key=True, default=gen_ulid)
    workflow_id = Column(String, ForeignKey('workflow_definition.id'), nullable=False)
    condition_type = Column(String, nullable=False)  # e.g., 'field_value', 'time_based', 'role_based'
    condition_config = Column(JSONB, nullable=False)  # Configuration for the condition
```

#### Workflow Action
```python
class WorkflowAction(UnoModel):
    """Action to take when workflow is triggered and conditions are met."""
    id = Column(String, primary_key=True, default=gen_ulid)
    workflow_id = Column(String, ForeignKey('workflow_definition.id'), nullable=False)
    action_type = Column(String, nullable=False)  # e.g., 'notification', 'email', 'webhook'
    action_config = Column(JSONB, nullable=False)  # Configuration for the action
    order = Column(Integer, default=0)  # Order of execution
```

#### Workflow Recipient
```python
class WorkflowRecipient(UnoModel):
    """Recipients for workflow notifications."""
    id = Column(String, primary_key=True, default=gen_ulid)
    workflow_id = Column(String, ForeignKey('workflow_definition.id'), nullable=False)
    recipient_type = Column(Enum('user', 'role', 'group', 'attribute'), nullable=False)
    recipient_id = Column(String, nullable=False)  # User ID, role name, group ID, or attribute value
```

#### Workflow Log
```python
class WorkflowLog(UnoModel):
    """Logs of workflow executions."""
    id = Column(String, primary_key=True, default=gen_ulid)
    workflow_id = Column(String, ForeignKey('workflow_definition.id'), nullable=False)
    trigger_event_id = Column(String, nullable=False)  # Reference to event that triggered the workflow
    status = Column(Enum('success', 'failure', 'pending'), nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    result = Column(JSONB)  # Details about the execution result
    error = Column(String)  # Error message if any
```

### 2. Core Components

#### Workflow Engine
Responsible for:
- Loading workflow definitions
- Evaluating triggers and conditions
- Executing actions
- Logging results

#### Workflow Event Listener
Integrated with the domain event system to:
- Subscribe to relevant domain events
- Filter events based on workflow triggers
- Route events to the workflow engine

#### Workflow Action Executor
Handles:
- Executing different types of actions (notifications, emails, etc.)
- Managing failures and retries
- Tracking execution status

#### Workflow Configuration Service
Provides API for:
- Creating and updating workflow definitions
- Managing workflow status (active/inactive)
- Validating workflow configurations

### 3. Integration Points

#### Event System Integration
- Subscribe to domain events
- Use event bus for distributing notifications
- Store workflow executions in event store for audit

#### Authorization Integration
- Verify permissions for workflow creation/management
- Resolve recipients based on roles/groups
- Apply tenant isolation for multi-tenant workflows

#### Notification System Integration
- Use existing notification system for delivering notifications
- Support multiple notification channels
- Allow customization of notification templates

### 4. Admin Interface Components

#### Workflow Designer
User interface for:
- Defining workflow triggers, conditions, and actions
- Setting up recipient targeting
- Testing workflows before activation

#### Workflow Dashboard
Provides:
- Overview of active workflows
- Execution statistics and logs
- Troubleshooting information

## Implementation Plan

### Phase 1: Foundation (2-3 weeks)
1. Implement the core data models
2. Create the workflow engine base functionality
3. Integrate with the event system
4. Set up basic action executors

### Phase 2: Advanced Features (2-3 weeks)
1. Implement conditional logic for workflows
2. Add support for complex recipient targeting
3. Create execution logging and monitoring
4. Build out action types (email, webhook, etc.)

### Phase 3: Admin Interface (2-3 weeks)
1. Develop workflow designer interface
2. Create workflow dashboard and monitoring
3. Implement testing/simulation capabilities
4. Add import/export functionality

### Phase 4: Testing and Documentation (1-2 weeks)
1. Write comprehensive tests
2. Create user documentation
3. Develop example workflows
4. Performance testing and optimization

## Technical Considerations

### Performance
- Efficient event filtering to avoid processing unnecessary events
- Batch processing for high-volume workflows
- Caching of frequently used workflow definitions

### Scalability
- Horizontal scaling of workflow engine
- Distributed execution for high-load environments
- Background processing for long-running workflows

### Security
- Tenant isolation for workflows
- Permission checks for workflow management
- Validation of user-provided configurations
- Sanitization of action inputs

### Maintainability
- Clear separation of concerns
- Extensive logging for troubleshooting
- Modular design for extending action types
- Versioning of workflow definitions

## Success Metrics

The implementation will be considered successful when:

1. Tenant administrators can create and manage workflows without developer assistance
2. Notifications are reliably delivered based on configured rules
3. The system scales to handle enterprise-level workflow volumes
4. The workflow engine integrates seamlessly with the existing event system
5. The admin interface provides intuitive workflow management

## Conclusion

This proposal outlines a comprehensive approach to implementing the workflows module as a powerful, user-configurable notification system that leverages the existing event infrastructure while adding business-user-friendly configuration capabilities.

The modular approach allows for incremental implementation and testing, with each phase building on the previous one to deliver a complete workflow notification system that meets the original vision.