# Database Design — Working Standards

## The Foundation Rule
A poor schema creates bugs, performance problems, and painful migrations that compound for years. Get the schema right before optimizing. Normalization is the default; denormalization requires a measured reason and documentation. A schema change in production is expensive — design it correctly the first time.

## Before Writing Any Schema
- Model the domain in an ER diagram (even a rough one) before writing DDL.
- Identify all entities, their attributes, and the cardinalities of their relationships.
- Identify which fields are PII and what their handling requirements are.
- Confirm the database engine and version. Feature availability differs.
- Check existing naming conventions in the project and follow them.

## Schema Design Standards

### Required Columns on Every Table
```
id          UUID or BIGSERIAL  PRIMARY KEY
created_at  TIMESTAMPTZ        NOT NULL DEFAULT NOW()
updated_at  TIMESTAMPTZ        NOT NULL DEFAULT NOW()
```
Use `deleted_at TIMESTAMPTZ NULL` only when a full audit trail is required. Use hard delete in all other cases.

### Naming
- Tables: `snake_case`, plural (`users`, `orders`, `order_items`).
- Columns: `snake_case`, descriptive (`created_at` not `ca`, `user_id` not `uid`).
- Foreign keys: `<referenced_table_singular>_id` (`user_id`, `order_id`).
- Booleans: `is_active`, `has_verified_email`, `can_publish`.
- Indexes: `idx_<table>_<columns>` (`idx_orders_user_id`).

### Primary Keys
- Use `UUID` for entities that will be referenced externally (by clients, in URLs, in API responses).
- Use `BIGSERIAL`/`BIGINT` auto-increment for internal-only, high-write tables.
- Never use natural keys (email, username, phone) as primary keys. They change.

### Data Types
- Money/currency: `NUMERIC(19, 4)`. Never `FLOAT` or `DOUBLE`. Floating-point arithmetic is not safe for currency.
- Timestamps: `TIMESTAMPTZ` always. Never `TIMESTAMP WITHOUT TIME ZONE`. Store in UTC.
- Text: `TEXT` for variable-length strings. `VARCHAR(n)` only when there is a genuine business constraint on length.
- JSON: `JSONB` (binary, indexed) over `JSON` for PostgreSQL.
- Enumerations: `TEXT` with a `CHECK` constraint for flexibility. `ENUM` types are difficult to migrate.

## Relationships

### One-to-Many
The foreign key lives on the "many" side. Index it immediately.
```sql
ALTER TABLE orders ADD COLUMN user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT;
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### Many-to-Many
Use a join table with a composite primary key and indexes on both FK columns.
```sql
CREATE TABLE product_tags (
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    tag_id     UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, tag_id)
);
CREATE INDEX idx_product_tags_tag_id ON product_tags(tag_id);
```

## Indexing Strategy

**Always index**: foreign key columns, columns in `WHERE` clauses, columns in `ORDER BY` for large tables, columns used in `JOIN` conditions.

**Composite indexes**: order columns from most selective to least selective. An index on `(user_id, status)` supports queries on `user_id` alone, but NOT on `status` alone.

**Partial indexes**: when a query always filters on a specific condition, index only the matching rows.
```sql
CREATE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;
```

**Do not over-index**: every index slows down writes. Index what queries actually need.

## Migration Standards
- Every schema change goes through a migration. No manual changes to production schema.
- Migrations are immutable once deployed. Never edit a deployed migration — create a new one.
- Migrations must be idempotent where possible (`CREATE INDEX IF NOT EXISTS`, `ALTER TABLE IF NOT EXISTS`).
- Test migrations against a copy of the production schema with production-representative data volume.

### Zero-Downtime Migration Patterns
Adding a column: `ALTER TABLE ... ADD COLUMN` is safe (null, with a default, or nullable first).

Adding a `NOT NULL` column: do it in 3 steps across 3 deployments:
1. Add nullable column.
2. Backfill existing rows.
3. Add `NOT NULL` constraint.

Adding an index on a large table: use `CREATE INDEX CONCURRENTLY` (PostgreSQL). This does not lock the table.

Renaming a column or table: requires a multi-step migration spanning multiple releases. Never rename and update all code in one deployment on a live system.

## Query Standards
- Never `SELECT *` in production code. Select only the columns needed.
- Paginate all queries that could return unbounded rows. Use cursor-based pagination for large or changing datasets.
- Use `EXPLAIN ANALYZE` during development to verify query plans before deploying new queries.
- Verify that all new queries use indexes — a sequential scan on a large table in production is a bug.
- Use transactions for operations that must be atomic. Keep transactions short — do not hold a transaction open while doing external I/O.

## Security
- Application connects with a least-privilege database user: only `SELECT`, `INSERT`, `UPDATE`, `DELETE` on needed tables. Not the database superuser.
- No user-generated strings interpolated into SQL — always use parameterized queries.
- PII fields encrypted at the application level for the highest-sensitivity data (SSN, payment card data).
