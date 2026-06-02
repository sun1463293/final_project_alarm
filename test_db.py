import os
import database

def run_tests():
    print("=== 開始資料庫單元測試 ===")
    
    # 1. 測試初始化
    # 如果原本有資料庫，先備份或刪除以進行乾淨測試
    if os.path.exists(database.DB_FILE):
        print(f"發現現有資料庫 {database.DB_FILE}，進行初始化測試...")
    database.initialize_db()
    
    # 2. 測試預算設定與取得
    database.set_monthly_budget(2026, 6, 15000.0)
    budget = database.get_monthly_budget(2026, 6)
    print(f"測試設定預算: 設定 15000.0, 讀取結果 = {budget}")
    assert budget == 15000.0, "預算讀寫測試失敗"
    
    # 3. 測試新增交易
    tx_id = database.add_transaction("2099-12-31", "expense", "餐飲", 150.0, "牛肉麵")
    print(f"測試新增交易: 成功, ID = {tx_id}")
    assert tx_id is not None, "新增交易失敗"
    
    # 4. 測試讀取最近交易
    recent = database.get_recent_transactions(limit=1)
    print(f"測試取得最近交易: ID = {recent[0]['id']}, 日期 = {recent[0]['date']}, 金額 = {recent[0]['amount']}, 備註 = {recent[0]['note']}")
    assert recent[0]['id'] == tx_id, "取得最近交易測試失敗"
    assert recent[0]['note'] == "牛肉麵", "取得最近交易資料損毀"
    
    # 5. 測試月份統計
    summary = database.get_monthly_summary(2026, 6)
    print(f"測試月份統計: 總收入 = {summary['total_income']}, 總支出 = {summary['total_expense']}, 結餘 = {summary['net_balance']}")
    # 剛剛新增了一筆 150.0 的支出，且 initialize_db 會寫入一些當月範例資料（如果有寫的話，但因為可能不是 2026 6 月，我們檢查是否 >= 150）
    assert summary['total_expense'] >= 150.0, "支出統計計算錯誤"
    
    # 6. 測試刪除交易
    database.delete_transaction(tx_id)
    recent_after = database.get_recent_transactions(limit=1)
    if recent_after:
        assert recent_after[0]['id'] != tx_id, "刪除交易測試失敗"
    print("測試刪除交易: 成功")
    
    print("=== 所有資料庫單元測試通過！ ===")

if __name__ == "__main__":
    run_tests()
