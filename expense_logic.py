import sqlite3
from datetime import datetime

DB_NAME = "expenses.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():

    with connect() as conn:
        cur = conn.cursor()

        # расходы

        cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            description TEXT,
            category TEXT,
            date TEXT
        )
        """)

        # месячные лимиты

        cur.execute("""
        CREATE TABLE IF NOT EXISTS budgets(
            user_id INTEGER PRIMARY KEY,
            monthly_limit REAL
        )
        """)

        conn.commit()


init_db()

# ---------- РАСХОДЫ ----------

def add_expense(user_id, amount, description, category):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        INSERT INTO expenses
        (user_id, amount, description, category, date)
        VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            amount,
            description,
            category,
            datetime.now().strftime("%d.%m.%Y %H:%M")
        ))

        conn.commit()


def get_expenses(user_id):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        SELECT amount, description, category, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """, (user_id,))

        rows = cur.fetchall()

        return [
            {
                "amount": r[0],
                "description": r[1],
                "category": r[2],
                "date": r[3]
            }
            for r in rows
        ]


def clear_expenses(user_id):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        DELETE FROM expenses
        WHERE user_id = ?
        """, (user_id,))

        conn.commit()


def get_total(user_id):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = ?
        """, (user_id,))

        result = cur.fetchone()[0]

        return result or 0


# ---------- ЗА МЕСЯЦ ----------

def get_month_total(user_id):

    month = datetime.now().strftime(".%m.%Y")

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = ?
        AND date LIKE ?
        """, (user_id, f"%{month}"))

        result = cur.fetchone()[0]

        return result or 0


# ---------- ЛИМИТ ----------

def set_budget(user_id, monthly_limit):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        INSERT OR REPLACE INTO budgets
        (user_id, monthly_limit)
        VALUES (?, ?)
        """, (
            user_id,
            monthly_limit
        ))

        conn.commit()


def get_budget(user_id):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        SELECT monthly_limit
        FROM budgets
        WHERE user_id = ?
        """, (user_id,))

        result = cur.fetchone()

        if result:
            return result[0]

        return None


# ---------- СТАТИСТИКА ----------

def get_stats(user_id):

    with connect() as conn:

        cur = conn.cursor()

        cur.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        """, (user_id,))

        return cur.fetchall()