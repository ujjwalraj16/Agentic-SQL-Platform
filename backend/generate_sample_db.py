"""
generate_sample_db.py – Creates a realistic sample SQLite database for demo.

Tables:
  departments, employees, customers, products, orders, order_items, payments

Generates 20-50k realistic records with:
- Realistic names, dates, amounts
- Year-over-year trends (2024-2025 comparison works)
- Some anomalies for interesting analysis
- Proper foreign key relationships

Run with: python generate_sample_db.py
"""

import random
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DB_PATH = Path(__file__).parent / "data" / "sample.db"
DB_PATH.parent.mkdir(exist_ok=True)

# ── Data pools ────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael",
    "Linda", "William", "Barbara", "David", "Elizabeth", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Emma",
    "Noah", "Olivia", "Liam", "Ava", "Sophia", "Lucas", "Isabella",
    "Mason", "Mia", "Ethan", "Amelia", "Aiden", "Harper", "Mateo",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
]
DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "proton.me", "icloud.com", "aol.com",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Indianapolis", "San Francisco", "Seattle", "Denver", "Nashville",
]
STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

DEPARTMENTS = [
    ("Engineering", 95000), ("Sales", 72000), ("Marketing", 78000),
    ("Finance", 88000), ("HR", 68000), ("Operations", 74000),
    ("Product", 92000), ("Customer Support", 62000),
]

PRODUCT_CATEGORIES = {
    "Electronics": [
        ("Laptop Pro 15", 1299.99), ("Wireless Headphones", 249.99),
        ("Smart Watch Series 5", 399.99), ("Tablet Ultra", 599.99),
        ("Bluetooth Speaker", 129.99), ("USB-C Hub", 59.99),
        ("Mechanical Keyboard", 149.99), ("4K Webcam", 179.99),
        ("Gaming Mouse", 89.99), ("Monitor 27inch", 449.99),
    ],
    "Clothing": [
        ("Premium Hoodie", 79.99), ("Classic Jeans", 59.99),
        ("Sports T-Shirt", 29.99), ("Winter Jacket", 149.99),
        ("Running Shoes", 119.99), ("Casual Sneakers", 89.99),
        ("Dress Shirt", 49.99), ("Yoga Pants", 64.99),
    ],
    "Home & Kitchen": [
        ("Coffee Maker Pro", 129.99), ("Air Fryer XL", 89.99),
        ("Robot Vacuum", 299.99), ("Blender 900W", 79.99),
        ("Instant Pot 8qt", 99.99), ("Stand Mixer", 349.99),
        ("Smart Thermostat", 199.99), ("LED Desk Lamp", 44.99),
    ],
    "Books": [
        ("Python Programming Guide", 39.99), ("Data Science Handbook", 49.99),
        ("Business Strategy 2025", 34.99), ("Machine Learning Basics", 44.99),
        ("Leadership Excellence", 24.99), ("Finance Fundamentals", 29.99),
    ],
    "Sports": [
        ("Yoga Mat Premium", 49.99), ("Resistance Bands Set", 34.99),
        ("Dumbbell Set 20kg", 79.99), ("Jump Rope", 19.99),
        ("Gym Bag Large", 59.99), ("Foam Roller", 29.99),
    ],
}

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]
ORDER_STATUSES = ["completed", "completed", "completed", "pending", "cancelled", "refunded"]


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def rand_name() -> tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    PRAGMA foreign_keys = ON;
    
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        budget REAL NOT NULL,
        location TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department_id INTEGER REFERENCES departments(department_id),
        salary REAL NOT NULL,
        hire_date TEXT NOT NULL,
        job_title TEXT NOT NULL,
        manager_id INTEGER REFERENCES employees(employee_id),
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        city TEXT,
        state TEXT,
        country TEXT DEFAULT 'USA',
        created_at TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        cost REAL NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        shipping_city TEXT,
        shipping_state TEXT,
        total_amount REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        employee_id INTEGER REFERENCES employees(employee_id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL REFERENCES orders(order_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        discount_pct REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL REFERENCES orders(order_id),
        payment_method TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        status TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
    CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
    CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
    CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
    CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department_id);
    """)


def seed_departments(conn: sqlite3.Connection) -> list[int]:
    ids = []
    for name, budget_base in DEPARTMENTS:
        budget = budget_base * random.uniform(50, 200)
        loc = random.choice(CITIES)
        cur = conn.execute(
            "INSERT INTO departments (name, budget, location, created_at) VALUES (?,?,?,?)",
            (name, round(budget, 2), loc, "2020-01-01"),
        )
        ids.append(cur.lastrowid)
    return ids


def seed_employees(conn: sqlite3.Connection, dept_ids: list[int]) -> list[int]:
    ids = []
    for dept_id in dept_ids:
        # 5-20 employees per department
        dept_name = DEPARTMENTS[dept_ids.index(dept_id)][0]
        base_salary = DEPARTMENTS[dept_ids.index(dept_id)][1]
        for _ in range(random.randint(5, 20)):
            fn, ln = rand_name()
            email = f"{fn.lower()}.{ln.lower()}{random.randint(1,999)}@company.com"
            salary = round(base_salary * random.uniform(0.7, 1.5), 2)
            hire_date = rand_date(datetime(2018, 1, 1), datetime(2024, 1, 1)).strftime("%Y-%m-%d")
            titles = {
                "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "Principal Engineer"],
                "Sales": ["Sales Rep", "Account Executive", "Sales Manager", "VP Sales"],
                "Marketing": ["Marketing Specialist", "Content Manager", "CMO"],
                "Finance": ["Analyst", "Senior Analyst", "Finance Manager", "CFO"],
                "HR": ["HR Specialist", "HR Manager", "Recruiter"],
                "Operations": ["Operations Manager", "Coordinator", "VP Operations"],
                "Product": ["Product Manager", "Senior PM", "VP Product"],
                "Customer Support": ["Support Agent", "Team Lead", "Support Manager"],
            }
            title = random.choice(titles.get(dept_name, ["Specialist"]))
            cur = conn.execute(
                """INSERT INTO employees 
                   (first_name, last_name, email, department_id, salary, hire_date, job_title, is_active)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (fn, ln, email, dept_id, salary, hire_date, title, 1),
            )
            ids.append(cur.lastrowid)
    return ids


def seed_customers(conn: sqlite3.Connection, n: int = 2000) -> list[int]:
    ids = []
    emails_used = set()
    for i in range(n):
        fn, ln = rand_name()
        email = f"{fn.lower()}.{ln.lower()}{i}@{random.choice(DOMAINS)}"
        while email in emails_used:
            email = f"{fn.lower()}.{ln.lower()}{i}{random.randint(0,9)}@{random.choice(DOMAINS)}"
        emails_used.add(email)
        phone = f"({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"
        city = random.choice(CITIES)
        state = random.choice(STATES)
        created = rand_date(datetime(2022, 1, 1), datetime(2025, 6, 1)).strftime("%Y-%m-%d")
        cur = conn.execute(
            """INSERT INTO customers 
               (first_name, last_name, email, phone, city, state, country, created_at, is_active)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (fn, ln, email, phone, city, state, "USA", created, 1 if random.random() > 0.05 else 0),
        )
        ids.append(cur.lastrowid)
    return ids


def seed_products(conn: sqlite3.Connection) -> list[int]:
    ids = []
    for category, items in PRODUCT_CATEGORIES.items():
        for name, price in items:
            cost = round(price * random.uniform(0.3, 0.6), 2)
            stock = random.randint(0, 500)
            created = rand_date(datetime(2020, 1, 1), datetime(2023, 1, 1)).strftime("%Y-%m-%d")
            cur = conn.execute(
                """INSERT INTO products (name, category, price, cost, stock_quantity, is_active, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (name, category, price, cost, stock, 1, created),
            )
            ids.append(cur.lastrowid)
    return ids


def seed_orders_and_items(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    product_ids: list[int],
    employee_ids: list[int],
    n_orders: int = 25000,
) -> None:
    """Generate orders across 2023-2025 with realistic seasonal patterns."""

    # Get product prices
    cursor = conn.execute("SELECT product_id, price, category FROM products")
    products = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    # Monthly multipliers for seasonality
    seasonality = {
        1: 0.75, 2: 0.72, 3: 0.88,
        4: 0.92, 5: 0.95, 6: 0.90,
        7: 0.88, 8: 0.93, 9: 1.0,
        10: 1.10, 11: 1.45, 12: 1.60,
    }

    # Year-over-year growth factor
    year_growth = {2023: 1.0, 2024: 1.18, 2025: 1.38}

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 9, 1)

    # 200 customers who never ordered (for "customers with no orders" query)
    non_buyer_pool = set(customer_ids[-200:])
    buying_customers = [c for c in customer_ids if c not in non_buyer_pool]

    batch_orders = []
    batch_items = []
    batch_payments = []

    for i in range(n_orders):
        order_date = rand_date(start_date, end_date)
        month_mult = seasonality[order_date.month]
        year_mult = year_growth.get(order_date.year, 1.0)

        # Weight for higher chance of placing order in good months/years
        customer_id = random.choice(buying_customers)
        emp_id = random.choice(employee_ids) if random.random() > 0.3 else None
        status = random.choice(ORDER_STATUSES)

        # Apply a Q2 2025 dip for interesting analysis
        if order_date.year == 2025 and order_date.month in (4, 5, 6):
            month_mult *= 0.72  # Revenue drop in Q2 2025

        # Number of items per order
        n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        items_in_order = random.sample(product_ids, min(n_items, len(product_ids)))

        total = 0
        order_items_data = []
        for prod_id in items_in_order:
            price, cat = products[prod_id]
            qty = random.randint(1, 4)
            discount_pct = random.choice([0, 0, 0, 5, 10, 15]) / 100
            line_total = price * qty * (1 - discount_pct) * month_mult * year_mult
            total += line_total
            order_items_data.append((prod_id, qty, round(price * month_mult * year_mult, 2), discount_pct * 100))

        discount = round(total * random.choice([0, 0, 0, 0.05, 0.1]), 2)
        total = round(total - discount, 2)
        if total <= 0:
            continue

        city = random.choice(CITIES)
        state = random.choice(STATES)
        order_date_str = order_date.strftime("%Y-%m-%d")

        batch_orders.append((customer_id, order_date_str, status, city, state, total, discount, emp_id))

    # Bulk insert orders
    conn.executemany(
        """INSERT INTO orders 
           (customer_id, order_date, status, shipping_city, shipping_state, 
            total_amount, discount_amount, employee_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        batch_orders,
    )

    # Get inserted order IDs
    cursor = conn.execute("SELECT order_id FROM orders ORDER BY order_id")
    order_ids = [row[0] for row in cursor.fetchall()]

    # Build items and payments for each order
    items_rows = []
    payments_rows = []

    for j, order_id in enumerate(order_ids):
        n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
        items_in_order = random.sample(product_ids, min(n_items, len(product_ids)))
        for prod_id in items_in_order:
            price, _ = products[prod_id]
            qty = random.randint(1, 4)
            disc_pct = random.choice([0, 0, 0, 5, 10])
            items_rows.append((order_id, prod_id, qty, round(price, 2), disc_pct))

        # Payment
        order_row = conn.execute("SELECT total_amount, order_date, status FROM orders WHERE order_id=?", (order_id,)).fetchone()
        if order_row:
            amt, odate, ostatus = order_row
            pstatus = "completed" if ostatus == "completed" else "pending"
            pay_date = (datetime.strptime(odate, "%Y-%m-%d") + timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d")
            payments_rows.append((order_id, random.choice(PAYMENT_METHODS), amt, pay_date, pstatus))

    conn.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_pct) VALUES (?,?,?,?,?)",
        items_rows,
    )
    conn.executemany(
        "INSERT INTO payments (order_id, payment_method, amount, payment_date, status) VALUES (?,?,?,?,?)",
        payments_rows,
    )


def main() -> None:
    print(f"Generating sample database at {DB_PATH}...")

    # Remove old db if exists
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("  Removed old database.")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("  Creating schema...")
    create_schema(conn)

    print("  Seeding departments...")
    dept_ids = seed_departments(conn)

    print("  Seeding employees...")
    emp_ids = seed_employees(conn, dept_ids)

    print("  Seeding customers (2,000)...")
    cust_ids = seed_customers(conn, 2000)

    print("  Seeding products...")
    prod_ids = seed_products(conn)

    print("  Seeding orders & items (25,000 orders)...")
    seed_orders_and_items(conn, cust_ids, prod_ids, emp_ids, n_orders=25000)

    conn.commit()

    # Print summary
    for table in ["departments", "employees", "customers", "products", "orders", "order_items", "payments"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count:,} rows")

    conn.close()
    print(f"\nSample database created: {DB_PATH}")
    print("Ready to use with: LLM_PROVIDER=ollama, DATABASE_URL=sqlite:///./data/sample.db")


if __name__ == "__main__":
    main()
