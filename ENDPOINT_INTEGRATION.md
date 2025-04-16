# Endpoint Integration with Domain-Driven Design

This document outlines the plan to fully integrate the UnoEndpoint system with the domain-driven design approach, replacing the older UnoObj pattern.

## Current Status Assessment

### 1. UnoEndpoint & Router Components
- **Code Structure**: The code is well-structured with a clear class hierarchy for different endpoint types.
- **Architecture**: Uses a modern approach with FastAPI and Pydantic for API definitions.
- **Features**: 
  - Supports standard CRUD operations
  - Includes streaming support for large result sets
  - Has filtering and pagination
  - Provides field selection capabilities

### 2. Documentation
- **Endpoint Factory Documentation**: Fairly comprehensive, but still references UnoObj (outdated)
- **API Documentation**: Lacks comprehensive examples for domain-driven approaches
- **Incomplete Transitions**: Some docs still refer to the UnoObj pattern rather than domain entities

### 3. Tests
- **Test Coverage**: Good test coverage for the endpoint factory, but limited for other API components
- **Test Quality**: Tests are well-structured and use appropriate mocking
- **Missing Tests**: No integration tests for endpoints with real domain entities

### 4. Domain-Driven Design Integration
- **Current State**: Partially updated for domain-driven design
- **Issues**: Still has references to UnoObj and doesn't fully leverage repository patterns

## Deficiencies and Implementation Plan

### 1. Completion of Domain-Driven Design Integration

**Issues:**
- Several parts of the endpoint implementation still expect UnoObj-style models
- Many methods like `filter`, `get`, `save` are called directly on model classes instead of repositories

**Plan:**
1. Update `UnoRouter` and derived classes to work with repositories instead of directly with models
2. Modify endpoint factory to accept repositories as parameters
3. Update endpoint implementations to use repository methods for CRUD operations
4. Remove assumptions about model class methods

### 2. Documentation Updates

**Issues:**
- Outdated references to UnoObj pattern
- Lack of examples showing domain-driven approach
- Inconsistent with the new architecture

**Plan:**
1. Update `docs/api/endpoint-factory.md` to replace UnoObj examples with domain entity examples
2. Create a new document `docs/api/domain-integration.md` showing how to integrate endpoints with domain entities and repositories
3. Review and update all API documentation to ensure consistency with domain-driven architecture
4. Add comprehensive examples for all endpoint types

### 3. Test Coverage Improvement

**Issues:**
- Limited tests for endpoints beyond factory
- No integration tests with real domain entities and repositories

**Plan:**
1. Add unit tests for all endpoint router classes
2. Create integration tests that demonstrate endpoints working with domain entities
3. Add test scenarios for error handling
4. Ensure test coverage for new domain-driven integration features

### 4. Enhanced Functionality

**Issues:**
- Limited support for custom authorization
- No built-in support for OpenAPI enhancements
- No support for batch operations

**Plan:**
1. Add support for dependency injection in endpoint creation
2. Implement standardized authorization handling
3. Add OpenAPI schema enhancements
4. Create support for batch operations endpoints
5. Add versioning support

## Implementation Roadmap

### Phase 1: Domain-Driven Design Integration
1. Update `endpoint.py` to remove UnoObj dependencies
2. Create adapter classes to bridge repositories with endpoints
3. Update endpoint factory to support domain entities and repositories
4. Update error handling to work with domain error types

### Phase 2: Documentation Updates
1. Rewrite all API documentation to match domain-driven approach
2. Create new integration examples
3. Document all endpoint types and configuration options
4. Add tutorials for common use cases

### Phase 3: Test Coverage Improvement
1. Add unit tests for all endpoint classes
2. Create integration tests with mock repositories
3. Add test cases for error conditions and edge cases
4. Ensure test coverage meets standards

### Phase 4: Enhanced Functionality
1. Implement dependency injection support
2. Add authorization integration
3. Enhance OpenAPI documentation
4. Implement batch operations endpoints
5. Add versioning support

## Implementation Progress

| Task | Status | Description |
|------|--------|-------------|
| Create Repository Adapter | Complete | Created adapter class to bridge repositories with endpoints |
| Update UnoRouter | Complete | Updated to work with Repository pattern |
| Update Router Implementations | Complete | Updated all router classes to work with repositories |
| Update UnoEndpoint | Complete | Updated to support repository adapters |
| Update Endpoint Factory | Complete | Modified to accept repositories and domain entities |
| Create Example | Complete | Created example showing domain-driven API integration |
| Create Domain Integration Doc | Complete | Created comprehensive guide for domain-driven API integration |
| Update Endpoint Factory Doc | Complete | Updated to show domain-driven and legacy approaches |
| Update API Overview Doc | Complete | Updated to reflect domain-driven architecture |
| Create Repository Adapter Doc | Complete | Created comprehensive guide for repository adapters |
| Add Tests | Not Started | Add tests for new functionality |

## Completed Implementation

The following components have been implemented to support domain-driven design with API endpoints:

1. **Repository Adapter (`src/uno/api/repository_adapter.py`)**
   - Bridges domain repositories with API endpoints
   - Provides methods compatible with endpoint routers
   - Handles conversion between entities and DTOs
   - Supports read-only and batch operations

2. **Updated Router Classes (`src/uno/api/endpoint.py`)**
   - All router classes now work with repository adapters
   - Support both legacy UnoObj pattern and new domain entities
   - Improved error handling and logging
   - Added support for field selection and pagination

3. **Updated Endpoint Factory (`src/uno/api/endpoint_factory.py`)**
   - Added support for creating endpoints from repositories
   - Creates repository adapter automatically
   - Supports dependency injection
   - Handles both legacy and domain-driven approaches

4. **Example Implementation (`src/uno/api/examples/domain_endpoint_example.py`)**
   - Shows how to set up endpoints with domain entities
   - Demonstrates repository pattern integration
   - Includes schema management for DTOs
   - Provides a complete working example

## Detailed Implementation Plan for Remaining Work

### Phase 2: Documentation Updates

| Task | Status | Description | Priority |
|------|--------|-------------|----------|
| Create Domain Integration Document | Complete | Created new doc explaining DDD API integration | High |
| Update Endpoint Factory Documentation | Complete | Updated with repository adapter support | High |
| Update API Overview Documentation | Complete | Updated to reflect new architecture | Medium |
| Create Repository Adapter Documentation | Complete | Created comprehensive documentation for repository adapters | Medium |
| Add Tutorial: Migration from UnoObj | Not Started | Guide on migrating from UnoObj to domain entities | Medium |
| Add Tutorial: Creating DDD API Endpoints | Not Started | Step-by-step guide for new API endpoints | High |

### Phase 3: Test Coverage Improvement

| Task | Status | Description | Priority |
|------|--------|-------------|----------|
| Create Repository Adapter Unit Tests | Not Started | Test adapter functionality | High |
| Create Endpoint Factory Unit Tests | Not Started | Test factory with repositories | High |
| Add Mock Repository Tests | Not Started | Test endpoints with mock repositories | Medium |
| Create Integration Tests | Not Started | End-to-end API endpoint tests | Medium |
| Test Error Handling | Not Started | Verify error responses and handling | Medium |
| Test Batch Operations | Not Started | Test batch create/update/delete | Low |

### Phase 4: Enhanced Functionality

| Task | Status | Description | Priority |
|------|--------|-------------|----------|
| Implement Authorization Integration | Not Started | Add role-based access control | Medium |
| Add Request Validation Middleware | Not Started | Add request validation | Medium |
| Add Response Transformation | Not Started | Add HATEOAS links support | Low |
| Implement API Versioning | Not Started | Add explicit versioning support | Low |
| Add OpenAPI Enhancements | Not Started | Improve schema documentation | Medium |
| Implement Rate Limiting | Not Started | Add configurable rate limiting | Low |

## Next Implementation Steps

1. Add tutorial for migrating from UnoObj to domain entities
2. Create unit tests for the repository adapter
3. Create unit tests for the endpoint factory with repositories
4. Implement the authorization integration
5. Add OpenAPI enhancements