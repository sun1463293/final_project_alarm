import os
import database

def run_tests():
    print("=== 開始資料庫單元測試 ===")
    
    # 0. 為了測試乾淨度，若是測試資料庫存在就先刪除
    if os.path.exists(database.DB_FILE):
        try:
            os.remove(database.DB_FILE)
            print("已刪除舊有測試資料庫以進行乾淨測試。")
        except Exception as e:
            print(f"無法刪除舊有資料庫 (可能被佔用): {e}")

    # 1. 測試初始化
    database.initialize_db()
    print("資料庫初始化測試成功")
    
    # 2. 驗證預設帳本是否存在
    ledgers = database.get_all_ledgers()
    print(f"目前帳本數量: {len(ledgers)}")
    assert len(ledgers) == 1, "初始帳本數量不為 1"
    assert ledgers[0]['id'] == 1, "預設帳本 ID 不為 1"
    assert ledgers[0]['token'] == 'DEFAULT', "預設帳本 Token 不為 DEFAULT"
    print("預設帳本驗證通過")
    
    # 3. 測試建立新帳本
    new_ledger = database.create_ledger("情侶存錢旅行帳本")
    print(f"建立新帳本成功: {new_ledger}")
    assert new_ledger['id'] > 1, "新建帳本 ID 錯誤"
    assert len(new_ledger['token']) == 8, "產生的 Token 長度不為 8 碼"
    
    # 4. 測試取得所有帳本
    ledgers_after = database.get_all_ledgers()
    assert len(ledgers_after) == 2, "新建帳本後總數不為 2"
    print("帳本列表查詢測試成功")
    
    # 5. 測試藉由 Token 加入/取得帳本
    searched_ledger = database.join_ledger(new_ledger['token'])
    assert searched_ledger is not None, "由 Token 找不到帳本"
    assert searched_ledger['id'] == new_ledger['id'], "由 Token 找到的帳本 ID 不相符"
    assert searched_ledger['name'] == "情侶存錢旅行帳本", "由 Token 找到的帳本名稱錯誤"
    print("Token 加入/查找測試成功")
    
    # 6. 測試多帳本預算與交易資料隔離 (Isolation)
    ledger_1_id = 1
    ledger_2_id = new_ledger['id']
    
    # 設定預算
    database.set_monthly_budget(2026, 6, 8000.0, ledger_id=ledger_1_id)
    database.set_monthly_budget(2026, 6, 25000.0, ledger_id=ledger_2_id)
    
    budget_1 = database.get_monthly_budget(2026, 6, ledger_id=ledger_1_id)
    budget_2 = database.get_monthly_budget(2026, 6, ledger_id=ledger_2_id)
    print(f"帳本 1 預算: {budget_1}, 帳本 2 預算: {budget_2}")
    assert budget_1 == 8000.0, "帳本 1 預算不正確"
    assert budget_2 == 25000.0, "帳本 2 預算不正確"
    
    # 新增交易
    tx_id_1 = database.add_transaction("2026-06-13", "expense", "餐飲", 150.0, "個人午餐", ledger_id=ledger_1_id, recorder="組員A")
    tx_id_2 = database.add_transaction("2026-06-13", "expense", "娛樂", 3500.0, "雙人遊樂園門票", ledger_id=ledger_2_id, recorder="組員B")
    
    # 驗證最近交易
    recent_1 = database.get_recent_transactions(limit=5, ledger_id=ledger_1_id)
    recent_2 = database.get_recent_transactions(limit=5, ledger_id=ledger_2_id)
    
    assert len(recent_1) == 1, "帳本 1 交易筆數錯誤"
    assert recent_1[0]['id'] == tx_id_1, "帳本 1 交易內容錯誤"
    assert recent_1[0]['recorder'] == "組員A", "帳本 1 記帳人欄位錯誤"
    assert len(recent_2) == 1, "帳本 2 交易筆數錯誤"
    assert recent_2[0]['id'] == tx_id_2, "帳本 2 交易內容錯誤"
    assert recent_2[0]['recorder'] == "組員B", "帳本 2 記帳人欄位錯誤"
    
    # 驗證月份統計
    summary_1 = database.get_monthly_summary(2026, 6, ledger_id=ledger_1_id)
    summary_2 = database.get_monthly_summary(2026, 6, ledger_id=ledger_2_id)
    
    assert summary_1['total_expense'] == 150.0, "帳本 1 支出統計錯誤"
    assert summary_2['total_expense'] == 3500.0, "帳本 2 支出統計錯誤"
    print("資料隔離性測試成功！不同帳本之資料互不干擾。")
    print(f"記帳人欄位驗證通過：帳本1={recent_1[0]['recorder']}，帳本2={recent_2[0]['recorder']}")
    
    # 7. 測試刪除交易
    database.delete_transaction(tx_id_1)
    recent_1_after = database.get_recent_transactions(limit=5, ledger_id=ledger_1_id)
    assert len(recent_1_after) == 0, "帳本 1 刪除交易失敗"
    
    # 8. 測試同步版本號遞增 (sync_meta)
    v0 = database.get_db_version()
    print(f"目前同步版本號: {v0}")
    assert v0 > 0, "初始版本號應大於 0（已有寫入操作）"
    
    # 新增一筆交易，版本號應 +1
    database.add_transaction("2026-06-13", "income", "薪資", 50000.0, "測試同步版本", ledger_id=ledger_1_id)
    v1 = database.get_db_version()
    assert v1 == v0 + 1, f"新增交易後版本號應 +1，實際: {v0} -> {v1}"
    
    # 刪除一筆交易，版本號應再 +1
    all_txs = database.get_recent_transactions(limit=1, ledger_id=ledger_1_id)
    database.delete_transaction(all_txs[0]['id'])
    v2 = database.get_db_version()
    assert v2 == v1 + 1, f"刪除交易後版本號應 +1，實際: {v1} -> {v2}"
    
    # 設定預算，版本號應再 +1
    database.set_monthly_budget(2026, 6, 9999.0, ledger_id=ledger_1_id)
    v3 = database.get_db_version()
    assert v3 == v2 + 1, f"設定預算後版本號應 +1，實際: {v2} -> {v3}"
    
    print(f"同步版本號遞增測試成功！版本變化: {v0} → {v1} → {v2} → {v3}")
    
    print("=== 所有資料庫單元測試通過！ ===")

if __name__ == "__main__":
    run_tests()
