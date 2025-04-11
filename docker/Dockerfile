FROM postgres:16-alpine

# Create directory for extension files
RUN mkdir -p /docker-entrypoint-initdb.d

# Install required packages 
RUN apk add --no-cache unzip \
    make \
    gcc \
    g++ \
    musl-dev \
    postgresql16-dev \
    flex \
    bison \
    perl \
    clang \
    git \
    cmake \
    libcurl \
    llvm19

# Create a directory for extensions
WORKDIR /tmp/build

# Clone and build pgvector directly (more reliable than using zip)
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install

# Clone and build age
RUN git clone --branch master https://github.com/apache/age.git && \
    cd age && \
    make && \
    make install

# Clone and build pgjwt
RUN git clone --branch master https://github.com/michelp/pgjwt.git && \
    cd pgjwt && \
    make && \
    make install

# Clone and build supa_audit
RUN git clone --branch main https://github.com/supabase/supa_audit.git && \
    cd supa_audit && \
    make && \
    make install

# Configure PostgreSQL environment variables
ENV POSTGRES_DB=postgres
ENV POSTGRES_USER=postgres
# Do not explicitly set PGDATA environment variable
ENV POSTGRES_PASSWORD="postgreSQLR0ck%"

# Create plugins directory and link extension shared objects 
# (Allows non superusers to use the extensions)
RUN mkdir -p /usr/local/lib/postgresql/plugins
RUN ln -s /usr/local/lib/postgresql/age.so /usr/local/lib/postgresql/plugins/age.so
RUN ln -s /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/plugins/vector.so

# Create initialization script to create extensions on database startup
COPY ./init-db.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Cleanup build directory
RUN rm -rf /tmp/build

# Expose PostgreSQL port
EXPOSE 5432

# Start PostgreSQL
CMD ["postgres", "-c", "shared_preload_libraries=age"]
