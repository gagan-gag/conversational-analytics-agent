"""
data/seed_db.py — Create and seed the SQLite analytics database.

Tables: customers, orders, events, churn
Each seeded with ~500 realistic synthetic rows.

Run directly: python data/seed_db.py
Or called at FastAPI startup if DB doesn't exist.
"""
from __future__ import annotations

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "analytics.db"

REGIONS = ["North", "South", "East", "West"]
PLANS = ["Free", "Pro", "Enterprise"]
STATUSES = ["completed", "pending", "refunded", "cancelled"]
CATEGORIES = ["SaaS", "Hardware", "Consulting", "Support", "Training"]
EVENT_TYPES = ["page_view", "button_click", "form_submit", "checkout", "login", "logout", "search"]
CHURN_REASONS = ["price", "competitor", "product_fit", "support", "unused", "budget"]


def _rand_date(start_year: int = 2022, end_year: int = 2024) -> str:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")


def _rand_ts(start_year: int = 2023, end_year: int = 2024) -> str:
    start = datetime(start_year, 1, 1)
    delta = (datetime(end_year, 12, 31) - start).total_seconds()
    return (start + timedelta(seconds=random.randint(0, int(delta)))).strftime("%Y-%m-%d %H:%M:%S")


def seed(db_path: Path = DB_PATH, n_customers: int = 500) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    # ── Schema ────────────────────────────────────────────────────────────────
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
        id               INTEGER PRIMARY KEY,
        name             TEXT NOT NULL,
        email            TEXT UNIQUE NOT NULL,
        region           TEXT NOT NULL,
        signup_date      DATE NOT NULL,
        plan             TEXT NOT NULL,
        churn_risk_score REAL NOT NULL DEFAULT 0.0
    );

    CREATE TABLE IF NOT EXISTS orders (
        id               INTEGER PRIMARY KEY,
        customer_id      INTEGER NOT NULL REFERENCES customers(id),
        amount           REAL NOT NULL,
        status           TEXT NOT NULL,
        created_at       DATETIME NOT NULL,
        product_category TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS events (
        id          INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        event_type  TEXT NOT NULL,
        timestamp   DATETIME NOT NULL,
        session_id  TEXT NOT NULL,
        page        TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS churn (
        id               INTEGER PRIMARY KEY,
        customer_id      INTEGER NOT NULL REFERENCES customers(id),
        predicted_date   DATE NOT NULL,
        reason           TEXT NOT NULL,
        confidence_score REAL NOT NULL
    );
    """)

    # Skip if already seeded
    existing = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    if existing >= n_customers:
        print(f"DB already seeded ({existing} customers). Skipping.")
        con.close()
        return

    random.seed(42)
    first_names = ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Hank",
                   "Iris", "Jack", "Karen", "Liam", "Mia", "Noah", "Olivia", "Paul",
                   "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
                   "Yara", "Zoe"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                  "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White"]

    # ── Customers ─────────────────────────────────────────────────────────────
    customers = []
    for i in range(1, n_customers + 1):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"user{i}@example.com"
        region = random.choice(REGIONS)
        signup = _rand_date(2022, 2023)
        plan = random.choices(PLANS, weights=[50, 35, 15])[0]
        churn_risk = round(random.uniform(0.0, 1.0), 4)
        customers.append((i, name, email, region, signup, plan, churn_risk))

    cur.executemany(
        "INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?,?,?)", customers
    )

    # ── Orders ────────────────────────────────────────────────────────────────
    orders = []
    for o_id in range(1, 1501):  # ~3 orders per customer
        cust_id = random.randint(1, n_customers)
        amount = round(random.uniform(19.99, 4999.99), 2)
        status = random.choices(STATUSES, weights=[70, 15, 10, 5])[0]
        created_at = _rand_ts(2023, 2024)
        category = random.choice(CATEGORIES)
        orders.append((o_id, cust_id, amount, status, created_at, category))

    cur.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders
    )

    # ── Events ────────────────────────────────────────────────────────────────
    pages = ["/home", "/pricing", "/dashboard", "/docs", "/signup", "/settings", "/billing"]
    events = []
    for e_id in range(1, 3001):  # ~6 events per customer
        cust_id = random.randint(1, n_customers)
        session_id = f"sess_{random.randint(1000, 9999)}"
        events.append((
            e_id,
            cust_id,
            random.choice(EVENT_TYPES),
            _rand_ts(2023, 2024),
            session_id,
            random.choice(pages),
        ))

    cur.executemany(
        "INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)", events
    )

    # ── Churn ─────────────────────────────────────────────────────────────────
    # Only high-risk customers (score > 0.6)
    high_risk = [c for c in customers if c[6] > 0.6]
    churn_rows = []
    for idx, c in enumerate(high_risk[:200], start=1):
        predicted = _rand_date(2024, 2025)
        reason = random.choice(CHURN_REASONS)
        confidence = round(random.uniform(0.6, 0.99), 4)
        churn_rows.append((idx, c[0], predicted, reason, confidence))

    cur.executemany(
        "INSERT OR IGNORE INTO churn VALUES (?,?,?,?,?)", churn_rows
    )

    con.commit()
    con.close()
    print(f"[OK] Seeded DB: {n_customers} customers, {len(orders)} orders, {len(events)} events, {len(churn_rows)} churn records")


if __name__ == "__main__":
    seed()
