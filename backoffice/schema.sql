CREATE TABLE branches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
) STRICT;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'common')),
    branch_id INTEGER REFERENCES branches(id) ON DELETE RESTRICT,
    is_delete INTEGER NOT NULL DEFAULT 0 CHECK (is_delete IN (0, 1)),
    created_at TEXT NOT NULL,
    update_at TEXT NOT NULL,
    CHECK ((role = 'admin' AND branch_id IS NULL) OR (role = 'common' AND branch_id IS NOT NULL))
) STRICT;

CREATE TABLE stock (
    branch_id INTEGER NOT NULL REFERENCES branches(id),
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (branch_id, product_id)
) STRICT;

CREATE INDEX ix_stock_product ON stock (product_id) WHERE quantity > 0;
