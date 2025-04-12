#!/bin/bash
# -----------------------------------------------------------------------------
# This script is deprecated and will be removed in a future version.
# Please use the new standardized script instead:
#   scripts/ci/build.sh
# -----------------------------------------------------------------------------

echo "[DEPRECATED] This script is deprecated. Please use scripts/ci/build.sh instead."
echo "Redirecting to the new script location..."

# Forward to the new script
"$(dirname "$0")/ci/build.sh" "$@"