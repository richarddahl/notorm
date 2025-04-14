#!/bin/bash
# -----------------------------------------------------------------------------
# This script is deprecated and will be removed in a future version.
# Please use the new standardized script instead:
#   scripts/dev/convert_tests.sh
# -----------------------------------------------------------------------------

echo "[DEPRECATED] This script is deprecated. Please use scripts/dev/convert_tests.sh instead."
echo "Redirecting to the new script location..."

# Forward to the new script
"$(dirname "$0")/dev/convert_tests.sh" "$@"