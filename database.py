import sqlite3
import os
import random
import string
from datetime import datetime

DB_FILE = "bookkeeping.db"

def get_connection():
    """取得資料庫連接"""
    return sqlite3.connect(DB_FILE)

def initialize_db():
    """初始化資料庫與資料表，支援多人共同記帳多帳本架構，並進行平滑遷移"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 建立帳本資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ledgers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 確保當前至少有預設帳本，且 ID = 1，Token = 'DEFAULT'
    cursor.execute("SELECT 1 FROM ledgers WHERE id = 1")
    if not cursor.fetchone():
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO ledgers (id, name, token, created_at)
        VALUES (1, '預設帳本', 'DEFAULT', ?)
        """, (now_str,))
    
    # 2. 建立/升級交易資料表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        ledger_id INTEGER DEFAULT 1,
        recorder TEXT DEFAULT ''
    )
    """)
    
    # 檢查 transactions 是否有 ledger_id 與 recorder 欄位，若無則 ALTER TABLE
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'ledger_id' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN ledger_id INTEGER DEFAULT 1")
    if 'recorder' not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN recorder TEXT DEFAULT ''")
        
    # 3. 建立/升級預算資料表
    cursor.execute("PRAGMA table_info(budget)")
    budget_columns = [col[1] for col in cursor.fetchall()]
    
    if len(budget_columns) > 0 and 'ledger_id' not in budget_columns:
        # 進行 budget 遷移
        # 1. 重新命名舊表
        cursor.execute("ALTER TABLE budget RENAME TO _budget_old")
        # 2. 建立新表
        cursor.execute("""
        CREATE TABLE budget (
            ledger_id INTEGER NOT NULL DEFAULT 1,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (ledger_id, year, month)
        )
        """)
        # 3. 複製資料
        cursor.execute("""
        INSERT INTO budget (ledger_id, year, month, amount)
        SELECT 1, year, month, amount FROM _budget_old
        """)
        # 4. 刪除舊表
        cursor.execute("DROP TABLE _budget_old")
    else:
        # 若不存在，直接建立新結構的表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            ledger_id INTEGER NOT NULL DEFAULT 1,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (ledger_id, year, month)
        )
        """)
        
    conn.commit()
    
    # 4. 建立同步版本追蹤表 (sync_meta)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_meta (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        version INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL
    )
    """)
    
    # 確保 sync_meta 有初始紀錄 (id=1 唯一列)
    cursor.execute("SELECT 1 FROM sync_meta WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO sync_meta (id, version, updated_at)
        VALUES (1, 0, ?)
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    
    conn.commit()
    
    # 確保當月預算存在，若無則插入預設預算
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    cursor.execute("""
    INSERT OR IGNORE INTO budget (ledger_id, year, month, amount)
    VALUES (1, ?, ?, 10000.0)
    """, (current_year, current_month))
    
    conn.commit()
    conn.close()

# ==========================================
# 同步版本管理 (Sync Version Tracking)
# ==========================================

def get_db_version():
    """取得目前資料庫的全域同步版本號"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM sync_meta WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def _bump_version(cursor):
    """內部輔助：在同一個 cursor/connection 交易中遞增版本號
    必須在 conn.commit() 之前呼叫，以保證原子性。"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE sync_meta
    SET version = version + 1, updated_at = ?
    WHERE id = 1
    """, (now_str,))

# ==========================================
# 帳本管理功能 (Ledger Management)
# ==========================================

def generate_unique_token():
    """產生隨機 8 碼不重複的大寫英數字 Token (排除易混淆字元如 O, 0, I, 1)"""
    chars = string.ascii_uppercase + string.digits
    chars = ''.join(c for c in chars if c not in 'O0I1')
    conn = get_connection()
    cursor = conn.cursor()
    while True:
        token = ''.join(random.choices(chars, k=8))
        cursor.execute("SELECT 1 FROM ledgers WHERE token = ?", (token,))
        if not cursor.fetchone():
            conn.close()
            return token

def create_ledger(name):
    """建立新帳本並產生隨機 Token"""
    token = generate_unique_token()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO ledgers (name, token, created_at)
    VALUES (?, ?, ?)
    """, (name, token, created_at))
    ledger_id = cursor.lastrowid
    _bump_version(cursor)  # 新帳本建立，版本遞增
    conn.commit()
    conn.close()
    return {"id": ledger_id, "name": name, "token": token, "created_at": created_at}

def join_ledger(token):
    """透過 Token 加入/獲取現有帳本"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, token, created_at FROM ledgers WHERE token = ?
    """, (token.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "token": row[2], "created_at": row[3]}
    return None

def get_all_ledgers():
    """取得所有已儲存的帳本"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, token, created_at FROM ledgers ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "token": r[2], "created_at": r[3]} for r in rows]

def get_ledger_by_token(token):
    """根據 Token 取得帳本資訊"""
    return join_ledger(token)

# ==========================================
# 財務與交易功能 (已支援多帳本 ledger_id)
# ==========================================

def add_transaction(date_str, tx_type, category, amount, note, ledger_id=1, recorder=''):
    """新增一筆交易，支援儲存記帳人名稱"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (date, type, category, amount, note, ledger_id, recorder)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date_str, tx_type, category, amount, note, ledger_id, recorder))
    tx_id = cursor.lastrowid
    _bump_version(cursor)  # 新交易寫入，版本遞增
    conn.commit()
    conn.close()
    return tx_id

def delete_transaction(tx_id):
    """刪除一筆交易"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    _bump_version(cursor)  # 刪除交易，版本遞增
    conn.commit()
    conn.close()

def get_monthly_summary(year, month, ledger_id=1):
    """取得指定帳本、年份與月份的總收支統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 格式化月份前導零，如 6 -> '06'
    month_str = f"{year:04d}-{month:02d}"
    
    # 計算總收入
    cursor.execute("""
    SELECT SUM(amount) FROM transactions 
    WHERE ledger_id = ? AND date LIKE ? AND type = 'income'
    """, (ledger_id, month_str + '%',))
    total_income = cursor.fetchone()[0] or 0.0
    
    # 計算總支出
    cursor.execute("""
    SELECT SUM(amount) FROM transactions 
    WHERE ledger_id = ? AND date LIKE ? AND type = 'expense'
    """, (ledger_id, month_str + '%',))
    total_expense = cursor.fetchone()[0] or 0.0
    
    # 分類支出匯總
    cursor.execute("""
    SELECT category, SUM(amount) FROM transactions 
    WHERE ledger_id = ? AND date LIKE ? AND type = 'expense'
    GROUP BY category
    ORDER BY SUM(amount) DESC
    """, (ledger_id, month_str + '%',))
    category_expenses = cursor.fetchall()
    
    # 分類收入匯總
    cursor.execute("""
    SELECT category, SUM(amount) FROM transactions 
    WHERE ledger_id = ? AND date LIKE ? AND type = 'income'
    GROUP BY category
    ORDER BY SUM(amount) DESC
    """, (ledger_id, month_str + '%',))
    category_incomes = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "category_expenses": category_expenses,
        "category_incomes": category_incomes
    }

def get_recent_transactions(limit=5, ledger_id=1):
    """取得指定帳本最近 N 筆交易紀錄（含記帳人名稱）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, date, type, category, amount, note, recorder
    FROM transactions 
    WHERE ledger_id = ?
    ORDER BY date DESC, id DESC 
    LIMIT ?
    """, (ledger_id, limit))
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
            "note": r[5],
            "recorder": r[6] or ''
        })
    return result

def get_all_transactions_for_month(year, month, ledger_id=1):
    """取得指定帳本與月份的所有交易紀錄（含記帳人名稱）"""
    conn = get_connection()
    cursor = conn.cursor()
    month_str = f"{year:04d}-{month:02d}"
    cursor.execute("""
    SELECT id, date, type, category, amount, note, recorder
    FROM transactions 
    WHERE ledger_id = ? AND date LIKE ? 
    ORDER BY date DESC, id DESC
    """, (ledger_id, month_str + '%',))
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
            "note": r[5],
            "recorder": r[6] or ''
        })
    return result

def set_monthly_budget(year, month, amount, ledger_id=1):
    """設定或更新指定帳本與月份的預算"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO budget (ledger_id, year, month, amount)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(ledger_id, year, month) DO UPDATE SET amount = excluded.amount
    """, (ledger_id, year, month, amount))
    _bump_version(cursor)  # 預算更新，版本遞增
    conn.commit()
    conn.close()

def get_monthly_budget(year, month, ledger_id=1):
    """取得指定帳本與月份的預算，若不存在則回傳預設值 10000.0"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT amount FROM budget 
    WHERE ledger_id = ? AND year = ? AND month = ?
    """, (ledger_id, year, month))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    else:
        return 10000.0
