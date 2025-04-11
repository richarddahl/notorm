#!/bin/bash

# Create directory for extension files if it doesn't exist
mkdir -p pg_ext_files

# Download pgvector from GitHub
echo "Downloading pgvector from GitHub..."
curl -L -o pg_ext_files/pgvector-master.zip https://github.com/pgvector/pgvector/archive/refs/heads/master.zip
echo "pgvector downloaded successfully to pg_ext_files/pgvector-master.zip"