# Documentation Resources Index

This document serves as a central index for all documentation-related resources, plans, and standards for the Uno framework.

## Documentation Standards and Processes

These documents define how documentation should be written, formatted, and maintained:

- [Documentation Contributor Guide](./DOCUMENTATION_CONTRIBUTOR_GUIDE.md) - Guidelines for contributors creating or updating documentation
- [Documentation Update Process](./DOCUMENTATION_UPDATE_PROCESS.md) - Detailed methodology for reviewing and updating documentation

## Documentation Status

These documents track the current state of documentation and remaining issues:

- [Documentation Status Visualization](./DOCUMENTATION_STATUS_VISUALIZATION.md) - Visual representation of documentation coverage and priorities
- [Documentation Remaining Issues](./DOCUMENTATION_REMAINING_ISSUES.md) - List of outstanding documentation issues

## Documentation Planning

These documents outline plans for future documentation development:

- [Documentation Development Plan](./DOCUMENTATION_DEVELOPMENT_PLAN.md) - Systematic plan for ongoing documentation improvement
- [Documentation Cleanup Summary](./DOCUMENTATION_CLEANUP_SUMMARY.md) - Summary of documentation improvements already completed

## Documentation Maintenance

For day-to-day documentation maintenance, the following tools and scripts are available:

- `src/scripts/standardize_docs.py` - Script for checking and fixing documentation formatting
- `src/scripts/generate_docs.py` - Script for generating documentation from source code

## Getting Started with Documentation

If you're new to working with Uno framework documentation, we recommend reading these resources in the following order:

1. [Documentation Contributor Guide](./DOCUMENTATION_CONTRIBUTOR_GUIDE.md) - To understand the basics
2. [Documentation Status Visualization](./DOCUMENTATION_STATUS_VISUALIZATION.md) - To see the big picture
3. [Documentation Development Plan](./DOCUMENTATION_DEVELOPMENT_PLAN.md) - To understand future priorities
4. [Documentation Remaining Issues](./DOCUMENTATION_REMAINING_ISSUES.md) - To find areas where you can help

## How to Contribute to Documentation

1. Check [Documentation Remaining Issues](./DOCUMENTATION_REMAINING_ISSUES.md) for areas needing improvement
2. Review the [Documentation Contributor Guide](./DOCUMENTATION_CONTRIBUTOR_GUIDE.md) for standards
3. Use the appropriate template for the type of documentation you're creating
4. Run `standardize_docs.py --check-links` to verify your documentation before submission
5. Submit your documentation changes as part of your pull request

## Documentation Review Process

All documentation submissions will be reviewed for:

1. **Technical accuracy** - Is the information correct?
2. **Completeness** - Does it cover all necessary information?
3. **Clarity** - Is it easy to understand?
4. **Formatting** - Does it follow the formatting standards?
5. **Cross-referencing** - Are links to other documentation correct?

## Documentation Versions

Documentation is versioned alongside the code. When creating documentation for a new feature, ensure it's aligned with the release where the feature will be introduced.