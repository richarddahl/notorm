#!/bin/bash
set -e

# Install additional PostgreSQL extensions
mkdir -p /tmp/ext_build
cd /tmp/ext_build

# Install AGE (Apache Graph Extension)
apt-get update && apt-get install -y git build-essential postgresql-server-dev-16 cmake flex bison curl unzip libcurl4-openssl-dev

# Download and install AGE
curl -L -o age.zip https://github.com/apache/age/archive/refs/heads/master.zip
unzip age.zip
cd age-master
make
make install

# Download and install pgjwt
cd /tmp/ext_build
curl -L -o pgjwt.zip https://github.com/michelp/pgjwt/archive/refs/heads/master.zip
unzip pgjwt.zip
cd pgjwt-master
make
make install

# Download and install supa_audit
cd /tmp/ext_build
curl -L -o supa_audit.zip https://github.com/supabase/supa_audit/archive/refs/heads/main.zip
unzip supa_audit.zip
cd supa_audit-main
make
make install

# Create plugins directory if it doesn't exist
mkdir -p /usr/local/lib/postgresql/plugins
ln -s /usr/local/lib/postgresql/age.so /usr/local/lib/postgresql/plugins/age.so

# Clean up
cd /
rm -rf /tmp/ext_build
apt-get clean