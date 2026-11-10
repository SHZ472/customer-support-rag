"""Sample PostgreSQL data and parameterized exact lookups."""

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def seed_database(conn):
    conn.execute((DATA / "schema.sql").read_text(encoding="utf-8"))
    fixtures = json.loads((DATA / "acceptance_cases.json").read_text(encoding="utf-8"))
    for source, record in fixtures["database_seed"].items():
        kind, number = source.split(":", 1)
        if kind == "product":
            conn.execute("INSERT INTO products (sku, title, price_yuan) VALUES (%s, %s, %s) "
                         "ON CONFLICT (sku) DO NOTHING", (number, record["title"], record["price_yuan"]))
        elif kind == "order":
            conn.execute("INSERT INTO orders (order_id, status) VALUES (%s, %s) "
                         "ON CONFLICT (order_id) DO NOTHING", (number, record["status"]))


def get_record(conn, kind, number):
    if kind == "product":
        return conn.execute("SELECT title, price_yuan FROM products WHERE sku = %s", (number,)).fetchone()
    return conn.execute("SELECT status FROM orders WHERE order_id = %s", (number,)).fetchone()
