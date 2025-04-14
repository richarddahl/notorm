#!/bin/bash
# -----------------------------------------------------------------------------
# This script is deprecated and will be removed in a future version.
# Please use the new standardized script instead:
#   scripts/dev/modeler.sh
# -----------------------------------------------------------------------------

echo "[DEPRECATED] This script is deprecated. Please use scripts/dev/modeler.sh instead."
echo "Redirecting to the new script location..."

# Forward to the new script
"$(dirname "$0")/dev/modeler.sh" "$@"