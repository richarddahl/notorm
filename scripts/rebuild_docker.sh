#!/bin/bash
# Main script to rebuild Docker containers

# Change to docker directory and run rebuild script
cd docker && ./scripts/rebuild.sh "$@"