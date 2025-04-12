#!/bin/bash
# -----------------------------------------------------------------------------
# This script is deprecated and will be removed in a future version.
# Please use the new standardized script instead:
#   scripts/db/extensions/pgvector.sh
# -----------------------------------------------------------------------------

echo "[DEPRECATED] This script is deprecated. Please use scripts/db/extensions/pgvector.sh instead."
echo "Redirecting to the new script location..."

# Forward to the new script
"$(dirname "$0")/db/extensions/pgvector.sh" "$@"