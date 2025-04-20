# Event System Unification Checklist

This checklist documents the concrete steps for consolidating all event types to inherit from a single canonical `Event` base class and conform to `EventProtocol` throughout the codebase.

---

## 1. Preparation
- [ ] Designate `src/uno/core/events/event.py:Event` as the canonical event base class.
- [ ] Review all event types and usages in the codebase (domain, monitoring, audit, security, infrastructure).

## 2. Refactor Monitoring Events
- [ ] Refactor `src/uno/core/monitoring/events.py:Event` to inherit from the canonical `Event`.
- [ ] Remove redundant fields (e.g., id, timestamp, context, data) in monitoring events.
- [ ] Move unique fields (e.g., level, type, context) to subclasses or as extra fields.
- [ ] Update all usages and handlers to use the new unified event type.

## 3. Refactor Security/Audit Events
- [ ] Refactor `src/uno/infrastructure/security/audit/event.py:SecurityEvent` to inherit from the canonical `Event`.
- [ ] Remove redundant metadata fields (event_id, timestamp, etc.).
- [ ] Map unique fields (user_id, ip_address, severity, etc.) as extra fields or use composition.
- [ ] Update all factory methods and serialization logic to use the canonical base.

## 4. Refactor Domain Events (if needed)
- [ ] Ensure all domain events inherit from the canonical `Event`.
- [ ] Remove any legacy or duplicate event base classes in domain modules.

## 5. Protocol Conformance
- [ ] Ensure all event types implement or inherit all `EventProtocol` properties and methods.
- [ ] Update event bus, store, and publisher logic to accept the canonical base or its subclasses.

## 6. Update Event Creation and Handling
- [ ] Update all event creation code to use the canonical base or its subclasses.
- [ ] Update event handler signatures and registration to use the unified event type.
- [ ] Refactor tests to use the unified event base.

## 7. Remove Redundant Code
- [ ] Remove legacy event base classes and protocols that are no longer needed.
- [ ] Remove duplicate or conflicting serialization/context logic.

## 8. Documentation and Examples
- [ ] Update documentation to reflect the unified event system.
- [ ] Provide canonical examples for domain, monitoring, and security events using the new base class.

## 9. Final Review
- [ ] Review the codebase for any remaining direct references to old event classes.
- [ ] Ensure all events are handled, persisted, and serialized in a unified, protocol-compliant manner.
- [ ] Confirm all tests pass and update/add tests for new event types.

---

**Progress:** Check off each item as you complete it. This checklist should be kept up to date as migration proceeds.
