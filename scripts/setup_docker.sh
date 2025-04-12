#!/bin/bash
# -----------------------------------------------------------------------------
# This script is deprecated and will be removed in a future version.
# Please use the new standardized script instead:
#   scripts/docker/start.sh
# -----------------------------------------------------------------------------

echo "[DEPRECATED] This script is deprecated. Please use scripts/docker/start.sh instead."
echo "Redirecting to the new script location..."

# Forward to the new script
"$(dirname "$0")/docker/start.sh" "$@"