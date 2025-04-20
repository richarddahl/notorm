# DI Consistency Remediation Progress

## Goal
Centralize all dependency registration in each domain to a single provider module (preferably `provider.py`), orchestrated by the central DI provider. Remove ad hoc or legacy registration logic.

## Status by Module

- **uno/application/queries/domain_provider.py**
  - Status: Deprecated and replaced by `provider.py`.
  - Action: No action required.

- **uno/application/workflows/domain_provider.py**
  - Status: DI-compliant, but duplicate with `workflows/provider.py`.
  - Action: Merge all registration logic into `provider.py`. Deprecate or remove `domain_provider.py`.

- **uno/application/workflows/provider.py**
  - Status: DI-compliant, contains main registration logic.
  - Action: Ensure all workflow DI registration is routed through this module. Add documentation.

- **uno/meta/domain_provider.py**
  - Status: DI-compliant, but should be renamed/merged into `provider.py` for consistency.
  - Action: Create or move logic to `provider.py` and deprecate `domain_provider.py`.

- **uno/core/di/provider.py**
  - Status: Central provider. Should orchestrate all registration.
  - Action: Add documentation about canonical registration pattern and enforce usage.

## Next Steps
- Begin by merging `workflows/domain_provider.py` into `workflows/provider.py` and updating all imports/usages.
- Add deprecation warnings/comments to old modules.
- Repeat for `meta/domain_provider.py` and `queries/domain_provider.py`.
- Update documentation and track progress in this file.
