# SQL Migrations

SQL migrations are a simple way to define database schema changes using plain SQL statements. This guide explains how to create and work with SQL migrations in the Uno framework.

## Creating SQL Migrations

### Manually

Create a new SQL migration file with the following format:

```sql
-- Migration: Create users table
-- Description: Creates the initial users table with basic fields

-- Write your UP SQL here
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- DOWN

-- Write your DOWN SQL here
DROP TABLE IF EXISTS users;
```

The file should have:
1. A header comment with the migration name and description
2. The "up" SQL statements for applying the migration
3. A `-- DOWN` marker to separate up and down statements
4. The "down" SQL statements for reverting the migration

Save the file with a timestamp-based name: `<timestamp>_<name>.sql`

For example: `1616721123_create_users_table.sql`

### Using the CLI

The migration CLI provides a command to create SQL migrations:

```bash
python -m uno.core.migrations.cli create "create users table" --type sql --directory ./migrations
```

This creates a new migration file with the current timestamp and a template structure.

## SQL Migration Format

### Structure

An SQL migration file has this general structure:

```sql
-- Optional comments and metadata

-- UP SQL statements
CREATE TABLE ...;
ALTER TABLE ...;
...

-- DOWN

-- DOWN SQL statements
DROP TABLE ...;
...
```

### Up SQL

The "up" SQL contains statements for applying the migration, such as:

- `CREATE TABLE` statements for new tables
- `ALTER TABLE` statements for modifying existing tables
- `CREATE INDEX` statements for adding indexes
- `INSERT` statements for initial/reference data

Example:

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
```

### Down SQL

The "down" SQL contains statements for reverting the migration, in the reverse order of the "up" SQL:

```sql
DROP INDEX IF EXISTS idx_categories_parent_id;
DROP INDEX IF EXISTS idx_categories_slug;
DROP TABLE IF EXISTS categories;
```

## SQL Migration Best Practices

### Use IF EXISTS / IF NOT EXISTS

Use `IF EXISTS` and `IF NOT EXISTS` clauses to make your migrations more robust:

```sql
-- Up SQL
CREATE TABLE IF NOT EXISTS users (...);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Down SQL
DROP INDEX IF EXISTS idx_users_email;
DROP TABLE IF EXISTS users;
```

### Include Comments

Add comments to explain complex operations:

```sql
-- Create the users table with basic authentication fields
CREATE TABLE users (...);

-- Add indexes for faster lookups during authentication
CREATE INDEX idx_users_email ON users(email);
```

### Use Transactions

For databases that support transactions for DDL (like PostgreSQL), wrap your migrations in transactions:

```sql
BEGIN;

-- Migration statements here...

COMMIT;
```

The migration system will automatically handle transactions if supported by the database and enabled in the configuration.

### Handle Dependencies

If a migration depends on another migration, make sure to specify the dependencies:

```sql
-- Dependencies: 1616720000_create_users_table
-- Create user profiles table that references the users table
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    ...
);
```

### Schema Qualifiers

When working with specific schemas, include the schema name in your statements:

```sql
-- Create a schema for authentication
CREATE SCHEMA IF NOT EXISTS auth;

-- Create tables in the auth schema
CREATE TABLE auth.users (...);
CREATE TABLE auth.roles (...);
```

## Special SQL Comments

The migration system recognizes special comments in SQL migrations:

### Dependencies

```sql
-- Dependencies: 1616720000_create_users_table, 1616721000_create_roles_table
```

### Tags

```sql
-- Tags: schema, auth, users
```

### Version

```sql
-- Version: 1.0.0
```

### Hooks

```sql
-- BeforeApply: notify_migration_start
-- AfterApply: update_schema_version
```

## Example SQL Migrations

### Creating a Table

```sql
-- Migration: Create products table
-- Description: Creates the products table for e-commerce functionality

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_category_id ON products(category_id);

-- DOWN

DROP INDEX IF EXISTS idx_products_category_id;
DROP INDEX IF EXISTS idx_products_slug;
DROP TABLE IF EXISTS products;
```

### Altering a Table

```sql
-- Migration: Add product images
-- Description: Add support for multiple product images

CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    url VARCHAR(255) NOT NULL,
    alt_text VARCHAR(255),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_product_images_product_id ON product_images(product_id);

-- DOWN

DROP INDEX IF EXISTS idx_product_images_product_id;
DROP TABLE IF EXISTS product_images;
```

### Adding Initial Data

```sql
-- Migration: Add default categories
-- Description: Insert initial product categories

INSERT INTO categories (name, slug, description) VALUES
('Electronics', 'electronics', 'Electronic devices and accessories'),
('Clothing', 'clothing', 'Apparel and fashion items'),
('Books', 'books', 'Books and publications'),
('Home & Kitchen', 'home-kitchen', 'Home and kitchen products');

-- DOWN

DELETE FROM categories WHERE slug IN (
    'electronics', 'clothing', 'books', 'home-kitchen'
);
```

## Conclusion

SQL migrations provide a straightforward way to manage database schema changes. By following consistent patterns and best practices, you can create migrations that are easy to understand, apply, and revert.