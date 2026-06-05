import sqlite3
import os
from datetime import datetime

DB_FILE = "bookkeeping.db"

def get_connection():
    """取得資料庫連接"""
    return sqlite3.connect(DB_FILE)

def initialize_db():
    """初始化資料庫與資料表，若無資料則插入預設範例資料"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 建立交易資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT
    )
    """)
    
    # 建立預算資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budget (
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY (year, month)
    )
    """)
    
    conn.commit()
    
    # 確保當月預算存在，若無則插入預設預算
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    cursor.execute("""
    INSERT OR IGNORE INTO budget (year, month, amount)
    VALUES (?, ?, 10000.0)
    """, (current_year, current_month))
    
    conn.commit()
    conn.close()

def add_transaction(date_str, tx_type, category, amount, note):
    """新增一筆交易"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (date, type, category, amount, note)
    VALUES (?, ?, ?, ?, ?)
    """, (date_str, tx_type, category, amount, note))
    conn.commit()
    tx_id = cursor.lastrowid
    conn.close()
    return tx_id

def delete_transaction(tx_id):
    """刪除一筆交易"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

def get_monthly_summary(year, month):
    """取得指定年份與月份的總收支統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 格式化月份前導零，如 6 -> '06'
    month_str = f"{year:04d}-{month:02d}"
    
    # 計算總收入
    cursor.execute("""
    SELECT SUM(amount) FROM transactions 
    WHERE date LIKE ? AND type = 'income'
    """, (month_str + '%',))
    total_income = cursor.fetchone()[0] or 0.0
    
    # 計算總支出
    cursor.execute("""
    SELECT SUM(amount) FROM transactions 
    WHERE date LIKE ? AND type = 'expense'
    """, (month_str + '%',))
    total_expense = cursor.fetchone()[0] or 0.0
    
    # 分類支出匯總
    cursor.execute("""
    SELECT category, SUM(amount) FROM transactions 
    WHERE date LIKE ? AND type = 'expense'
    GROUP BY category
    ORDER BY SUM(amount) DESC
    """, (month_str + '%',))
    category_expenses = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "category_expenses": category_expenses
    }

def get_recent_transactions(limit=5):
    """取得最近 N 筆交易紀錄"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, date, type, category, amount, note 
    FROM transactions 
    ORDER BY date DESC, id DESC 
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "date": r[1],
            "type": r[2],
            "category": r[3],
            "amount": r[4],
            "note": r[5]
        })
    return result

def get_all_transactions_for_month(year, month):
    """取得指定月份的所有交易紀錄"""
    conn = get_connection()
    cursor = conn.cursor()
    month_str = f"{year:04d}-{month:02d}"
    cursor.execute("""
    SELECT id, date, type, category, amount, note 
    FROM transactions 
    WHERE date LIKE ? 
    ORDER BY date DESC, id DESC
    """, (month_str + '%',))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "date": r[1],
            "type": r[2],
            "category": r[3],
            "amount": r[4],
            "note": r[5]
        })
    return result

def set_monthly_budget(year, month, amount):
    """設定或更新指定月份的預算"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO budget (year, month, amount)
    VALUES (?, ?, ?)
    ON CONFLICT(year, month) DO UPDATE SET amount = excluded.amount
    """, (year, month, amount))
    conn.commit()
    conn.close()

def get_monthly_budget(year, month):
    """取得指定月份的預算，若不存在則回傳預設值 10000.0"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT amount FROM budget 
    WHERE year = ? AND month = ?
    """, (year, month))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    else:
        return 10000.0
