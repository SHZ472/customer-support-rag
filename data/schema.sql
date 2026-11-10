CREATE TABLE IF NOT EXISTS products (
    sku text PRIMARY KEY,
    title text NOT NULL,
    price_yuan integer NOT NULL CHECK (price_yuan >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id text PRIMARY KEY,
    status text NOT NULL
);
