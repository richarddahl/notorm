FROM postgres:16-alpine

# Create directory for extension files
RUN mkdir -p /docker-entrypoint-initdb.d

# Install required packages
RUN apk add --no-cache unzip \
    make \
    gcc \
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


# Copy extension files
COPY pg_ext_files/age-master.zip /docker-entrypoint-initdb.d/
COPY pg_ext_files/pgjwt-master.zip /docker-entrypoint-initdb.d/
COPY pg_ext_files/supa_audit-main.zip /docker-entrypoint-initdb.d/

# Set permissions
RUN chmod 755 /docker-entrypoint-initdb.d/*

# Configure PostgreSQL environment variables
ENV POSTGRES_DB=postgres
ENV POSTGRES_USER=postgres
#COPY pg_pwd.txt /run/secrets/pg_pwd
#ENV POSTGRES_PASSWORD_FILE=/run/secrets/pg_pwd
ENV PGDATA=/var/lib/postgresql/data
ENV POSTGRES_PASSWORD="postgreSQLR0ck%"

# Expose PostgreSQL port
EXPOSE 5432

# Unzip extension files
RUN unzip /docker-entrypoint-initdb.d/age-master.zip -d /docker-entrypoint-initdb.d/
RUN unzip /docker-entrypoint-initdb.d/pgjwt-master.zip -d /docker-entrypoint-initdb.d/
RUN unzip /docker-entrypoint-initdb.d/supa_audit-main.zip -d /docker-entrypoint-initdb.d/

# Install extensions
RUN cd /docker-entrypoint-initdb.d/age-master && make install
RUN cd /docker-entrypoint-initdb.d/pgjwt-master && make install
RUN cd /docker-entrypoint-initdb.d/supa_audit-main && make install

# Create plugins directory and link age.so (Allows non superusers to use the extension)
RUN mkdir /usr/local/lib/postgresql/plugins
RUN ln -s /usr/local/lib/postgresql/age.so /usr/local/lib/postgresql/plugins/age.so

# Remove extension files
RUN rm -rf /docker-entrypoint-initdb.d/*

# Start PostgreSQL
CMD ["postgres"]
