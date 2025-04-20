# Endpoint Router Consolidation Plan

## Objective
Consolidate all FastAPI router registrations into a single central module to improve discoverability, auditability, and onboarding for API endpoints.

## Motivation
- Single source of truth for endpoint registration
- Easier to audit which routers are included
- Simplifies onboarding for new contributors
- Reduces risk of missing or duplicate registrations

## Steps

1. **Create a Central Router Registration Module**
   - Create a new file, e.g., `src/uno/api/router.py`.
   - This file will import all routers from domain endpoint modules and register them with the FastAPI app.

2. **Import All Routers**
   - Import routers (e.g., `workflow_def_router`, `meta_type_router`, etc.) from each domain's `domain_endpoints.py` or equivalent.

3. **Define a Single Registration Function**
   - Define a function `register_all_routers(app: FastAPI)` that calls `app.include_router(...)` for each imported router.

4. **Update Main App Initialization**
   - In `main.py` or the main app entrypoint, replace all individual registration calls with a single call to `register_all_routers(app)`.

5. **(Optional) Remove Redundant Registration Functions**
   - Remove now-redundant `register_X_routers(app)` functions from each domain's endpoint module.

6. **Update Documentation**
   - Update onboarding and architecture docs to instruct contributors to add new routers to the central registration module.

7. **Test**
   - Ensure all endpoints are still available and functional. Check OpenAPI docs for completeness.

## Tradeoffs
- Slightly less modular (domains no longer self-register)
- Central file may grow as the number of routers increases

## Next Steps
- [ ] Scaffold `src/uno/api/router.py` and import all routers
- [ ] Implement `register_all_routers(app)`
- [ ] Update `main.py` to use new central registration
- [ ] Remove redundant registration functions from domain endpoint modules
- [ ] Update documentation
- [ ] Test and verify endpoint availability
