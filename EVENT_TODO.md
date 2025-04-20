# Event System Refactor TODOs

_Last updated: 2025-04-19_

## Completion Status

All event system refactor TODOs have been completed as of this date.

This file previously tracked all remaining TODOs for the event system unification and modernization effort. All items below are now complete.

---

## Monitoring Events

- [x] Refactor `src/uno/core/monitoring/events.py:Event` to inherit from the canonical `Event`.
- [x] Remove redundant fields (id, timestamp, context, data) in monitoring events.
- [x] Move unique fields (level, type, context) to subclasses or as extra fields.
- [x] Update all usages and handlers to use the new unified event type.

  - Monitoring events now fully inherit from the canonical Event class and redundant fields have been removed. All usages and handlers updated.

## Security/Audit Events

- [x] Refactor `src/uno/infrastructure/security/audit/event.py:SecurityEvent` to inherit from the canonical `Event`.
- [x] Remove redundant metadata fields (event_id, timestamp, etc.).
- [x] Map unique fields (user_id, ip_address, severity, etc.) as extra fields or use composition.
- [x] Update all factory methods and serialization logic to use the canonical base.

  - Security and audit events now use the canonical Event base and all unique fields are handled as extra fields. Serialization and factory logic updated.

## Linting & Consistency

- [x] Address any remaining Ruff linting issues (import order, unused imports, type annotation modernization).
- [x] Double-check for lingering legacy event base classes or protocol violations outside domain events.
- [x] Ensure all event creation and handling logic is updated to use the unified structure.

  - Linting is now clean and all event creation/handling is unified.

## Testing

- [x] Run all tests to confirm event system changes did not break functionality.
- [x] Add/Update tests for monitoring and security event refactors as they are completed.

  - All tests pass and coverage includes new event structure.

---

**Event system unification is now complete.**

---

_If you complete an item, please check it off here and in the main checklist._
