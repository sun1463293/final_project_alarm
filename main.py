import customtkinter as ctk
import database
import os
import csv
from datetime import datetime
from tkinter import messagebox

# 引入 Matplotlib 用於數據可視化
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# 解決 matplotlib 中文亂碼與負號顯示問題 (針對 macOS 優化)
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial Unicode MS', 'PingFang HK', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 確保資料庫初始化
database.initialize_db()

import wave
import math
import struct
import sys
import subprocess

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

def ensure_alarm_sound(filename="alarm.wav"):
    """確保警報音效檔存在，若不存在則利用 wave & math 動態生成"""
    if os.path.exists(filename):
        return
    
    sample_rate = 22050  # 取樣率
    duration = 3.0       # 3 秒
    
    try:
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1) # 單聲道
            wav_file.setsampwidth(2) # 16-bit
            wav_file.setframerate(sample_rate)
            
            num_samples = int(duration * sample_rate)
            for i in range(num_samples):
                t = float(i) / sample_rate
                # 頻率在 600Hz 到 1200Hz 之間每秒震盪兩次 (2Hz)
                freq = 900.0 + 300.0 * math.sin(2.0 * math.pi * 2.0 * t)
                value = int(32767.0 * math.sin(2.0 * math.pi * freq * t))
                data = struct.pack('<h', value)
                wav_file.writeframesraw(data)
    except Exception as e:
        print(f"無法建立警報音效檔案: {e}")

# 全局的警報音效播放行程
_alarm_process = None

def play_alarm():
    """播放警報音效"""
    global _alarm_process
    ensure_alarm_sound()
    if HAS_WINSOUND:
        try:
            winsound.PlaySound("alarm.wav", winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        except Exception as e:
            print(f"Windows 音效播放錯誤: {e}")
    else:
        try:
            if sys.platform == "darwin": # macOS
                _alarm_process = subprocess.Popen(["afplay", "alarm.wav"])
            elif sys.platform.startswith("linux"): # Linux
                _alarm_process = subprocess.Popen(["aplay", "alarm.wav"])
        except Exception as e:
            print(f"跨平台音效播放錯誤: {e}")

def stop_alarm():
    """停止播放警報音效"""
    global _alarm_process
    if HAS_WINSOUND:
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception as e:
            print(f"Windows 停止音效錯誤: {e}")
    else:
        if _alarm_process is not None:
            try:
                _alarm_process.terminate()
                _alarm_process = None
            except Exception:
                pass

class BudgetWarningDialog(ctk.CTkToplevel):
    def __init__(self, parent, budget, current_expense, year, month):
        super().__init__(parent)
        self.title("⚠️ 預算警戒通知")
        self.geometry("400x260")
        self.resizable(False, False)
        
        # 強制置頂並鎖定焦點
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.configure(fg_color="#1e1e1e")
        
        # 標題
        self.lbl_title = ctk.CTkLabel(
            self, text="⚠️ 預算使用率已達 80%！", 
            font=ctk.CTkFont(size=18, weight="bold"), 
            text_color="#f59e0b"
        )
        self.lbl_title.pack(pady=(25, 15))
        
        # 資訊容器
        details_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        details_frame.pack(fill="x", padx=30, pady=5)
        
        # 顯示數值
        lbl_info = ctk.CTkLabel(
            details_frame, 
            text=f"您在 {year} 年 {month} 月的總支出已達：\n$ {current_expense:,.1f} 元\n\n設定之月預算上限為：\n$ {budget:,.1f} 元", 
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        lbl_info.pack(pady=15, padx=20)
        
        # 關閉按鈕
        self.btn_ok = ctk.CTkButton(
            self, text="我知道了", 
            fg_color="#f59e0b", hover_color="#d97706",
            text_color="#181818", font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy
        )
        self.btn_ok.pack(pady=(15, 20))

class BudgetAlarmDialog(ctk.CTkToplevel):
    def __init__(self, parent, budget, current_expense, year, month):
        super().__init__(parent)
        self.title("🚨 預算超支警報 🚨")
        self.geometry("420x320")
        self.resizable(False, False)
        
        # 強制置頂並鎖定焦點
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.configure(fg_color="#241415")
        
        # 警報標題
        self.lbl_title = ctk.CTkLabel(
            self, text="🚨 預算超支暴走中 🚨", 
            font=ctk.CTkFont(size=22, weight="bold"), 
            text_color="#ef4444"
        )
        self.lbl_title.pack(pady=(25, 15))
        
        # 資訊容器
        details_frame = ctk.CTkFrame(self, fg_color="#3b1d20", corner_radius=8)
        details_frame.pack(fill="x", padx=30, pady=5)
        
        exceeded = current_expense - budget
        lbl_info = ctk.CTkLabel(
            details_frame, 
            text=f"【預算防線崩潰】\n您在 {year} 年 {month} 月的總支出已達：\n$ {current_expense:,.1f} 元\n\n已超出預算上限：$ {exceeded:,.1f} 元！\n(設定預算：$ {budget:,.1f} 元)", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#fca5a5",
            justify="center"
        )
        lbl_info.pack(pady=15, padx=20)
        
        # 播放警報音效
        play_alarm()
        
        # 啟動閃爍特效
        self.flash_state = True
        self.flash_title()
        
        # 關閉按鈕
        self.btn_close = ctk.CTkButton(
            self, text="關閉警報 (確認並返回)", 
            fg_color="#ef4444", hover_color="#dc2626",
            text_color="white", font=ctk.CTkFont(size=14, weight="bold"),
            command=self.close_dialog
        )
        self.btn_close.pack(pady=(20, 20))
        
        # 監聽關閉視窗事件
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)
        
    def flash_title(self):
        try:
            if self.winfo_exists():
                if self.flash_state:
                    self.lbl_title.configure(text_color="#ef4444")
                    self.configure(fg_color="#241415")
                else:
                    self.lbl_title.configure(text_color="#fca5a5")
                    self.configure(fg_color="#181818")
                self.flash_state = not self.flash_state
                self.after(500, self.flash_title)
        except Exception:
            pass
            
    def close_dialog(self):
        stop_alarm()
        self.destroy()

class SmartLedgerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 專案標題與幾何尺寸
        self.title("個人智能記帳系統 (Smart Ledger) - D1463293 孫廷沂")
        self.geometry("900x650")
        self.minsize(850, 600)
        
        # 預設外觀
        ctk.set_appearance_mode("dark")
        
        # 初始化變數
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.active_tab = "dashboard"
        
        # 帳本管理變數
        self.current_ledger_id = 1
        self.current_ledger_name = "預設帳本"
        self.current_ledger_token = "DEFAULT"
        
        # 記帳人暱稱（可在設定頁修改，新增交易時自動帶入）
        self.current_user_name = "我"
        
        # 同步輪詢：記錄最後已知的資料庫版本號，-1 代表未初始化
        self._last_known_version = -1
        
        # 自訂主題色彩定義 (莫蘭迪色調、霓虹色)
        self.themes = {
            "Classic Dark": {"primary": "#1f538d", "secondary": "#2b2b2b", "bg": "#1e1e1e", "accent": "#3a7ebf"},
            "Mint": {"primary": "#2ebd7f", "secondary": "#2b2b2b", "bg": "#1e2722", "accent": "#27a36c"},
            "Sakura": {"primary": "#e87ea1", "secondary": "#2b2b2b", "bg": "#241f21", "accent": "#d45d83"},
            "Tech Blue": {"primary": "#00b4d8", "secondary": "#2b2b2b", "bg": "#0f172a", "accent": "#0096c7"}
        }
        self.current_theme_name = "Classic Dark"
        self.current_theme = self.themes[self.current_theme_name]
        
        # 設定視窗主背景
        self.configure(fg_color=self.current_theme["bg"])
        
        # 建立 UI 佈局
        self.setup_ui()
        self.show_page("dashboard")
        
    def setup_ui(self):
        """建立主畫面左側導覽欄與右側內容呈現區"""
        # grid 佈局設定 (1列, 2欄: 左側側欄佔 1, 右側內容佔 4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(0, weight=1)
        
        # ---------------- 左側側欄 (Sidebar Frame) ----------------
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#181818")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # 底部撐開
        
        # App 標題 / Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="💰 Smart Ledger", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=25)
        
        # 導覽按鈕
        self.nav_buttons = {}
        
        self.nav_buttons["dashboard"] = ctk.CTkButton(
            self.sidebar_frame, text="儀表板首頁", font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color="gray", hover_color="#2b2b2b",
            anchor="w", height=40, command=lambda: self.show_page("dashboard")
        )
        self.nav_buttons["dashboard"].grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        
        self.nav_buttons["history"] = ctk.CTkButton(
            self.sidebar_frame, text="交易明細", font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color="gray", hover_color="#2b2b2b",
            anchor="w", height=40, command=lambda: self.show_page("history")
        )
        self.nav_buttons["history"].grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        self.nav_buttons["charts"] = ctk.CTkButton(
            self.sidebar_frame, text="統計圖表", font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color="gray", hover_color="#2b2b2b",
            anchor="w", height=40, command=lambda: self.show_page("charts")
        )
        self.nav_buttons["charts"].grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        self.nav_buttons["settings"] = ctk.CTkButton(
            self.sidebar_frame, text="系統設定", font=ctk.CTkFont(size=14),
            fg_color="transparent", text_color="gray", hover_color="#2b2b2b",
            anchor="w", height=40, command=lambda: self.show_page("settings")
        )
        self.nav_buttons["settings"].grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        
        # ---------------- 側欄底部：帳本名稱 & 同步狀態指示 ----------------
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # 自動擐開空間
        
        sync_status_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#121212", corner_radius=8)
        sync_status_frame.grid(row=6, column=0, padx=10, pady=(0, 15), sticky="ew")
        
        self.lbl_sync_ledger = ctk.CTkLabel(
            sync_status_frame,
            text="📒 預設帳本",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_sync_ledger.pack(anchor="w", padx=10, pady=(8, 2))
        
        self.lbl_sync_status = ctk.CTkLabel(
            sync_status_frame,
            text="🔄 同步中...",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.lbl_sync_status.pack(anchor="w", padx=10, pady=(0, 8))

        # ---------------- 右側主內容區 (Content Container) ----------------
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # 各個分頁對象初始化
        self.pages = {}
        self.init_dashboard_page()
        self.init_history_page()
        self.init_charts_page()
        self.init_settings_page()
        
        # 啟動同步輪詢
        self.start_sync_polling()
        
    def show_page(self, page_name):
        """切換至指定分頁並刷新資料"""
        self.active_tab = page_name
        
        # 隱藏所有分頁
        for page in self.pages.values():
            page.grid_forget()
            
        # 顯示目標分頁
        self.pages[page_name].grid(row=0, column=0, sticky="nsew")
        
        # 更新左側導覽鈕樣式
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color=self.current_theme["primary"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="gray")
                
        # 刷新對應頁面數據
        if page_name == "dashboard":
            self.refresh_dashboard()
        elif page_name == "history":
            self.refresh_history()
        elif page_name == "charts":
            self.refresh_charts()
        elif page_name == "settings":
            self.refresh_settings()

    # ==========================================
    # 即時同步輪詢 (Real-time Sync Polling)
    # ==========================================
    def start_sync_polling(self):
        """啟動定期同步輪詢，每 3 秒比對一次 DB 版本號"""
        self._sync_check()

    def _sync_check(self):
        """讀取 DB 版本號，若與已知版本不同則自動刷新 UI"""
        try:
            current_version = database.get_db_version()
            
            if current_version != self._last_known_version:
                if self._last_known_version != -1:
                    # 版本已變更（非初次載入），刷新目前分頁
                    if self.active_tab == "dashboard":
                        self.refresh_dashboard()
                    elif self.active_tab == "history":
                        self.refresh_history()
                    elif self.active_tab == "charts":
                        self.refresh_charts()
                    elif self.active_tab == "settings":
                        self.refresh_settings()
                    
                    # 短暫閃爍綠色表示已同步
                    self.lbl_sync_status.configure(
                        text=f"✅ 已同步  {datetime.now().strftime('%H:%M:%S')}",
                        text_color="#10b981"
                    )
                    # 1.5 秒後恢復為灰色靜止狀態
                    self.after(1500, lambda: self.lbl_sync_status.configure(
                        text=f"🔄 監聽中  v{current_version}",
                        text_color="gray"
                    ))
                else:
                    # 初次啟動：靜默載入版本號
                    self.lbl_sync_status.configure(
                        text=f"🔄 監聽中  v{current_version}",
                        text_color="gray"
                    )
                
                self._last_known_version = current_version
                
        except Exception as e:
            # DB 不可存取時（如共享檔案暫時鎖定），靜默忽略本次輪詢
            self.lbl_sync_status.configure(text="⚠️ 連線中斷", text_color="#f59e0b")
        
        # 3 秒後再次輪詢（使用 tkinter.after，完全主執行緒安全）
        self.after(3000, self._sync_check)

    # ==========================================
    # 儀表板首頁 (Dashboard Page)
    # ==========================================
    def init_dashboard_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["dashboard"] = page
        
        page.grid_columnconfigure((0, 1, 2), weight=1)
        page.grid_rowconfigure(2, weight=1)
        
        # 頁面標題與日期
        self.dash_title = ctk.CTkLabel(page, text="財務儀表板", font=ctk.CTkFont(size=24, weight="bold"))
        self.dash_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        self.dash_date_label = ctk.CTkLabel(page, text="", font=ctk.CTkFont(size=14), text_color="gray")
        self.dash_date_label.grid(row=0, column=2, sticky="e", pady=(0, 15))
        
        # 頂部收支卡片區 (收入、支出、結餘)
        self.card_income = ctk.CTkFrame(page, height=100, fg_color="#1e293b", corner_radius=10)
        self.card_income.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.card_income.grid_propagate(False)
        self.lbl_inc_title = ctk.CTkLabel(self.card_income, text="本月總收入 📈", font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_inc_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.lbl_inc_val = ctk.CTkLabel(self.card_income, text="$ 0.0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#10b981")
        self.lbl_inc_val.pack(anchor="w", padx=15)
        
        self.card_expense = ctk.CTkFrame(page, height=100, fg_color="#1e293b", corner_radius=10)
        self.card_expense.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.card_expense.grid_propagate(False)
        self.lbl_exp_title = ctk.CTkLabel(self.card_expense, text="本月總支出 📉", font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_exp_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.lbl_exp_val = ctk.CTkLabel(self.card_expense, text="$ 0.0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#f43f5e")
        self.lbl_exp_val.pack(anchor="w", padx=15)
        
        self.card_balance = ctk.CTkFrame(page, height=100, fg_color="#1e293b", corner_radius=10)
        self.card_balance.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.card_balance.grid_propagate(False)
        self.lbl_bal_title = ctk.CTkLabel(self.card_balance, text="本月淨結餘 💰", font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_bal_title.pack(anchor="w", padx=15, pady=(10, 2))
        self.lbl_bal_val = ctk.CTkLabel(self.card_balance, text="$ 0.0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#38bdf8")
        self.lbl_bal_val.pack(anchor="w", padx=15)
        
        # 中間預算進度區
        self.budget_frame = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.budget_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=15, sticky="ew")
        
        self.lbl_budget_status = ctk.CTkLabel(self.budget_frame, text="預算載入中...", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_budget_status.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.budget_progress = ctk.CTkProgressBar(self.budget_frame, height=12, progress_color="#10b981")
        self.budget_progress.pack(fill="x", padx=20, pady=(0, 15))
        
        # 下半部：近期交易清單與快速新增按鈕
        self.bottom_frame = ctk.CTkFrame(page, fg_color="transparent")
        self.bottom_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.bottom_frame.grid_columnconfigure(0, weight=3)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        
        # 交易列表標題
        self.lbl_recent = ctk.CTkLabel(self.bottom_frame, text="最近交易紀錄 (最新5筆)", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_recent.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # 滾動清單區域
        self.recent_scroll = ctk.CTkScrollableFrame(self.bottom_frame, height=200, fg_color="#181818")
        self.recent_scroll.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # 快速記帳按鈕
        self.btn_add_tx = ctk.CTkButton(
            self.bottom_frame, text="➕ 新增記帳紀錄", font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"],
            height=50, command=self.open_add_transaction_dialog
        )
        self.btn_add_tx.grid(row=1, column=1, sticky="ew", padx=5)
        
    def refresh_dashboard(self):
        """從資料庫獲取最新收支並更新儀表板"""
        now = datetime.now()
        self.dash_date_label.configure(text=f"今天: {now.strftime('%Y/%m/%d')}")
        
        # 獲取統計摘要
        sum_data = database.get_monthly_summary(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        self.lbl_inc_val.configure(text=f"$ {sum_data['total_income']:,.1f}")
        self.lbl_exp_val.configure(text=f"$ {sum_data['total_expense']:,.1f}")
        
        net = sum_data['net_balance']
        if net >= 0:
            self.lbl_bal_val.configure(text=f"$ {net:,.1f}", text_color="#38bdf8")
        else:
            self.lbl_bal_val.configure(text=f"$ {net:,.1f}", text_color="#f43f5e")
            
        # 預算狀態計算
        budget = database.get_monthly_budget(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        expense = sum_data['total_expense']
        
        if budget > 0:
            percent = expense / budget
            percent = min(percent, 1.0) # 封頂 100%
            self.budget_progress.set(percent)
            
            # 根據預算百分比動態調整進度條顏色
            if percent < 0.5:
                self.budget_progress.configure(progress_color="#10b981") # 綠色
            elif percent < 0.9:
                self.budget_progress.configure(progress_color="#f59e0b") # 黃色
            else:
                self.budget_progress.configure(progress_color="#ef4444") # 紅色
                
            self.lbl_budget_status.configure(
                text=f"本月預算花費進度： 已支出 $ {expense:,.1f} / 總預算 $ {budget:,.1f} ({percent*100:.1f}%)"
            )
        else:
            self.budget_progress.set(0)
            self.lbl_budget_status.configure(text="尚未設定本月預算，請至「系統設定」設定預算。")
            
        # 刷新最近交易清單
        for widget in self.recent_scroll.winfo_children():
            widget.destroy()
            
        recent_txs = database.get_recent_transactions(limit=5, ledger_id=self.current_ledger_id)
        
        if not recent_txs:
            lbl_empty = ctk.CTkLabel(self.recent_scroll, text="目前尚無記帳紀錄，趕快點擊右側按鈕記下第一筆吧！", font=ctk.CTkFont(size=13), text_color="gray")
            lbl_empty.pack(pady=20)
        else:
            for tx in recent_txs:
                # 建立單條交易卡片
                row_frame = ctk.CTkFrame(self.recent_scroll, fg_color="#242424", height=45, corner_radius=6)
                row_frame.pack(fill="x", pady=4, padx=5)
                row_frame.pack_propagate(False)
                
                # 類別圖示/文字與日期
                type_indicator = "🟢 [入]" if tx['type'] == 'income' else "🔴 [出]"
                lbl_info = ctk.CTkLabel(
                    row_frame, 
                    text=f"{tx['date']}   {type_indicator} {tx['category']}", 
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w"
                )
                lbl_info.pack(side="left", padx=15)
                
                # 記帳人名稱
                recorder_text = tx.get('recorder') or ''
                if recorder_text:
                    lbl_rec = ctk.CTkLabel(row_frame, text=f"👤{recorder_text}", font=ctk.CTkFont(size=11), text_color="#a78bfa", anchor="w")
                    lbl_rec.pack(side="left", padx=(0, 4))
                
                # 備註說明
                note_text = f"({tx['note']})" if tx['note'] else ""
                lbl_note = ctk.CTkLabel(row_frame, text=note_text, font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
                lbl_note.pack(side="left", padx=5)
                
                # 金額
                amt_color = "#10b981" if tx['type'] == 'income' else "#f43f5e"
                amt_sign = "+" if tx['type'] == 'income' else "-"
                lbl_amt = ctk.CTkLabel(
                    row_frame, 
                    text=f"{amt_sign}$ {tx['amount']:,.1f}", 
                    font=ctk.CTkFont(size=14, weight="bold"), 
                    text_color=amt_color,
                    anchor="e"
                )
                lbl_amt.pack(side="right", padx=15)

    # ==========================================
    # 交易明細分頁 (History Page)
    # ==========================================
    def init_history_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["history"] = page
        
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        
        # 標題
        self.hist_title = ctk.CTkLabel(page, text="交易明細查詢", font=ctk.CTkFont(size=24, weight="bold"))
        self.hist_title.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # 篩選控制列
        filter_frame = ctk.CTkFrame(page, fg_color="#1e293b", height=60, corner_radius=8)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        filter_frame.grid_propagate(False)
        
        lbl_year = ctk.CTkLabel(filter_frame, text="年份:", font=ctk.CTkFont(size=13))
        lbl_year.pack(side="left", padx=(15, 5), pady=15)
        
        self.opt_year = ctk.CTkOptionMenu(
            filter_frame, values=["2025", "2026", "2027", "2028"], width=90,
            command=self.on_filter_changed
        )
        self.opt_year.set(str(self.current_year))
        self.opt_year.pack(side="left", padx=5, pady=15)
        
        lbl_month = ctk.CTkLabel(filter_frame, text="月份:", font=ctk.CTkFont(size=13))
        lbl_month.pack(side="left", padx=(15, 5), pady=15)
        
        self.opt_month = ctk.CTkOptionMenu(
            filter_frame, values=[str(m) for m in range(1, 13)], width=80,
            command=self.on_filter_changed
        )
        self.opt_month.set(str(self.current_month))
        self.opt_month.pack(side="left", padx=5, pady=15)
        
        # 滾動明細區域
        self.history_scroll = ctk.CTkScrollableFrame(page, fg_color="#181818")
        self.history_scroll.grid(row=2, column=0, sticky="nsew")
        
    def on_filter_changed(self, value):
        """篩選下拉選單改變時觸發"""
        self.current_year = int(self.opt_year.get())
        self.current_month = int(self.opt_month.get())
        self.refresh_history()
        
    def refresh_history(self):
        """刷新歷史交易列表"""
        # 清空
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
            
        txs = database.get_all_transactions_for_month(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        
        if not txs:
            lbl_empty = ctk.CTkLabel(self.history_scroll, text="本月份查無任何交易明細。", font=ctk.CTkFont(size=13), text_color="gray")
            lbl_empty.pack(pady=40)
        else:
            for tx in txs:
                # 明細卡片
                card = ctk.CTkFrame(self.history_scroll, fg_color="#242424", height=50, corner_radius=6)
                card.pack(fill="x", pady=4, padx=8)
                card.pack_propagate(False)
                
                # 日期
                lbl_date = ctk.CTkLabel(card, text=tx['date'], font=ctk.CTkFont(size=12), text_color="gray", width=90)
                lbl_date.pack(side="left", padx=10)
                
                # 收支標誌與類別
                type_indicator = "🟢 收入" if tx['type'] == 'income' else "🔴 支出"
                lbl_cat = ctk.CTkLabel(card, text=f"{type_indicator} | {tx['category']}", font=ctk.CTkFont(size=13, weight="bold"), width=120, anchor="w")
                lbl_cat.pack(side="left", padx=10)
                
                # 記帳人名稱
                recorder_name = tx.get('recorder') or '未知'
                lbl_recorder = ctk.CTkLabel(
                    card,
                    text=f"👤 {recorder_name}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#a78bfa",
                    width=75,
                    anchor="w"
                )
                lbl_recorder.pack(side="left", padx=5)
                
                # 備註
                lbl_note = ctk.CTkLabel(card, text=tx['note'] or "", font=ctk.CTkFont(size=12), text_color="lightgray", anchor="w")
                lbl_note.pack(side="left", padx=10, fill="x", expand=True)
                
                # 金額
                amt_color = "#10b981" if tx['type'] == 'income' else "#f43f5e"
                amt_sign = "+" if tx['type'] == 'income' else "-"
                lbl_amt = ctk.CTkLabel(card, text=f"{amt_sign}$ {tx['amount']:,.1f}", font=ctk.CTkFont(size=14, weight="bold"), text_color=amt_color, width=100, anchor="e")
                lbl_amt.pack(side="left", padx=10)
                
                # 刪除按鈕
                btn_del = ctk.CTkButton(
                    card, text="🗑️ 刪除", font=ctk.CTkFont(size=11),
                    fg_color="#ef4444", hover_color="#dc2626", width=60, height=26,
                    command=lambda t_id=tx['id']: self.delete_transaction(t_id)
                )
                btn_del.pack(side="right", padx=10)

    def delete_transaction(self, tx_id):
        """刪除指定記帳交易"""
        if messagebox.askyesno("確認刪除", "您確定要永久刪除此筆記帳紀錄嗎？"):
            database.delete_transaction(tx_id)
            self.refresh_history()
            # 同步刷新儀表板 (避免回到主頁沒更新)
            self.refresh_dashboard()

    # ==========================================
    # 統計圖表分頁 (Charts Page)
    # ==========================================
    def init_charts_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["charts"] = page
        
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(3, weight=1)
        
        # 標題
        self.chart_title = ctk.CTkLabel(page, text="收支分析圖表", font=ctk.CTkFont(size=24, weight="bold"))
        self.chart_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # 收支切換按鈕
        self.chart_type_selector = ctk.CTkSegmentedButton(
            page, values=["支出分析", "收入分析"], font=ctk.CTkFont(size=13, weight="bold"),
            command=self.on_chart_type_changed
        )
        self.chart_type_selector.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        self.chart_type_selector.set("支出分析")
        
        # 用於放置 Matplotlib Canvas 的容器
        self.chart_container = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.chart_container.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.chart_container.grid_rowconfigure(0, weight=1)
        self.chart_container.grid_columnconfigure(0, weight=1)
        
        # 下半部類別排行
        self.rank_frame = ctk.CTkFrame(page, fg_color="#181818", corner_radius=8)
        self.rank_frame.grid(row=3, column=0, sticky="nsew")
        self.rank_frame.grid_rowconfigure(1, weight=1)
        self.rank_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_rank_title = ctk.CTkLabel(self.rank_frame, text="📋 分類支出排行榜", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_rank_title.grid(row=0, column=0, sticky="w", padx=15, pady=8)
        
        self.rank_scroll = ctk.CTkScrollableFrame(self.rank_frame, fg_color="transparent", height=150)
        self.rank_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
    def on_chart_type_changed(self, value):
        self.refresh_charts()
        
    def refresh_charts(self):
        """重新撈取數據，繪製並嵌入圓環圖"""
        # 清空 Canvas 容器
        for widget in self.chart_container.winfo_children():
            widget.destroy()
            
        # 清空分類列表
        for widget in self.rank_scroll.winfo_children():
            widget.destroy()
            
        is_expense = (self.chart_type_selector.get() == "支出分析")
        
        sum_data = database.get_monthly_summary(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        if is_expense:
            categories = sum_data["category_expenses"]
            total_amt = sum_data["total_expense"]
            type_text = "支出"
        else:
            categories = sum_data["category_incomes"]
            total_amt = sum_data["total_income"]
            type_text = "收入"
            
        # 更新排行榜標題
        self.lbl_rank_title.configure(text=f"📋 分類{type_text}排行榜")
        
        # 如果無資料，顯示提示
        if not categories or total_amt == 0:
            lbl_empty = ctk.CTkLabel(self.chart_container, text=f"📊 {self.current_year} 年 {self.current_month} 月查無{type_text}資料，無法繪製圖表。", font=ctk.CTkFont(size=15), text_color="gray")
            lbl_empty.pack(pady=100)
            
            lbl_no_rank = ctk.CTkLabel(self.rank_scroll, text=f"目前尚無分類{type_text}統計。", font=ctk.CTkFont(size=13), text_color="gray")
            lbl_no_rank.pack(pady=20)
            return
            
        # 1. 繪製 Matplotlib 圓環圖
        # 設定顏色主題 (配合 UI 風格)
        if is_expense:
            # 支出用偏橘紅暖色系
            colors = ['#f43f5e', '#fbbf24', '#f97316', '#a78bfa', '#38bdf8', '#10b981', '#64748b']
        else:
            # 收入用偏綠藍冷色系
            colors = ['#10b981', '#38bdf8', '#00b4d8', '#a78bfa', '#fbbf24', '#f97316', '#64748b']
        
        labels = [cat[0] for cat in categories]
        sizes = [cat[1] for cat in categories]
        
        # 建立 Figure (設定深色背景，與 GUI 無縫貼合)
        fig, ax = plt.subplots(figsize=(6, 3.2), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        # 繪製圓餅圖並加上圓孔形成圓環
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%', startangle=90, 
            colors=colors[:len(labels)], pctdistance=0.75,
            textprops=dict(color="w", size=9, weight="bold")
        )
        
        # 設定中間的圓孔 (毛玻璃/背景色)
        centre_circle = plt.Circle((0,0), 0.50, fc='#1e293b')
        fig.gca().add_artist(centre_circle)
        
        # 等比圓形
        ax.axis('equal')  
        plt.tight_layout()
        
        # 將 matplotlib 嵌入 Tkinter Canvas
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
        plt.close(fig) # 關閉 matplotlib figure 避免記憶體洩漏
        
        # 2. 顯示分類排行榜
        for i, (cat_name, amount) in enumerate(categories):
            percent = (amount / total_amt) * 100
            
            row_frame = ctk.CTkFrame(self.rank_scroll, fg_color="#242424", height=36, corner_radius=4)
            row_frame.pack(fill="x", pady=2, padx=5)
            row_frame.pack_propagate(False)
            
            # 名次與分類
            lbl_rank = ctk.CTkLabel(row_frame, text=f"No.{i+1}   {cat_name}", font=ctk.CTkFont(size=12, weight="bold"), width=120, anchor="w")
            lbl_rank.pack(side="left", padx=15)
            
            # 進度條模擬佔比
            progress = ctk.CTkProgressBar(row_frame, width=200, height=8, progress_color=colors[i % len(colors)])
            progress.pack(side="left", padx=10)
            progress.set(percent / 100)
            
            # 金額與佔比
            lbl_info = ctk.CTkLabel(row_frame, text=f"$ {amount:,.1f}  ({percent:.1f}%)", font=ctk.CTkFont(size=12), text_color="lightgray", anchor="e")
            lbl_info.pack(side="right", padx=15)

    # ==========================================
    # 系統設定分頁 (Settings Page)
    # ==========================================
    def init_settings_page(self):
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages["settings"] = page
        
        # 標題
        self.set_title = ctk.CTkLabel(page, text="系統設定與工具", font=ctk.CTkFont(size=24, weight="bold"))
        self.set_title.pack(anchor="w", pady=(0, 20))
        
        # 帳本管理設定卡片
        self.ledger_card = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.ledger_card.pack(fill="x", pady=8, padx=5)
        
        self.lbl_ledger_sec_title = ctk.CTkLabel(self.ledger_card, text="👥 多人共同記帳 / 帳本管理", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_ledger_sec_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.ledger_info_frame = ctk.CTkFrame(self.ledger_card, fg_color="transparent")
        self.ledger_info_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        # 顯示目前帳本資訊
        self.lbl_current_ledger_info = ctk.CTkLabel(
            self.ledger_info_frame, 
            text="目前帳本: 預設帳本 | 代碼 (Token): DEFAULT", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_current_ledger_info.pack(side="left", padx=(0, 20))
        
        # 帳本切換下拉選單
        self.lbl_switch_ledger = ctk.CTkLabel(self.ledger_info_frame, text="切換帳本:", font=ctk.CTkFont(size=13))
        self.lbl_switch_ledger.pack(side="left", padx=(10, 5))
        
        self.opt_switch_ledger = ctk.CTkOptionMenu(
            self.ledger_info_frame, values=["預設帳本 (DEFAULT)"], width=180,
            command=self.on_switch_ledger_changed
        )
        self.opt_switch_ledger.pack(side="left", padx=5)
        
        # 按鈕容器
        self.ledger_btn_frame = ctk.CTkFrame(self.ledger_card, fg_color="transparent")
        self.ledger_btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # 建立新帳本按鈕
        self.btn_create_ledger = ctk.CTkButton(
            self.ledger_btn_frame, text="➕ 建立新帳本", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"],
            width=120, command=self.open_create_ledger_dialog
        )
        self.btn_create_ledger.pack(side="left", padx=(0, 10))
        
        # 加入現有帳本按鈕
        self.btn_join_ledger = ctk.CTkButton(
            self.ledger_btn_frame, text="🔑 加入現有帳本 (輸入 Token)", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#a78bfa", hover_color="#8b5cf6",
            width=180, command=self.open_join_ledger_dialog
        )
        self.btn_join_ledger.pack(side="left")
        
        # ── 記帳人暱稱設定卡片 ──
        self.user_card = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.user_card.pack(fill="x", pady=8, padx=5)
        
        self.lbl_user_title = ctk.CTkLabel(self.user_card, text="👤 我的記帳人暱稱", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_user_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        user_input_frame = ctk.CTkFrame(self.user_card, fg_color="transparent")
        user_input_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.ent_user_name = ctk.CTkEntry(user_input_frame, placeholder_text="輸入暱稱 (如: 小明、Alice)", width=180)
        self.ent_user_name.insert(0, self.current_user_name)
        self.ent_user_name.pack(side="left", padx=(0, 10))
        
        self.btn_save_user = ctk.CTkButton(
            user_input_frame, text="儲存暱稱",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#a78bfa", hover_color="#8b5cf6",
            width=90, command=self.save_user_name
        )
        self.btn_save_user.pack(side="left")
        
        ctk.CTkLabel(
            user_input_frame,
            text="  ⚡ 新增交易時自動帶入此暱稱作為「記帳人」",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(side="left", padx=(10, 0))
        
        # 預算設定區卡片
        self.budget_set_card = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.budget_set_card.pack(fill="x", pady=8, padx=5)
        
        self.lbl_b_title = ctk.CTkLabel(self.budget_set_card, text="🎯 本月預算上限設定", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_b_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.budget_input_frame = ctk.CTkFrame(self.budget_set_card, fg_color="transparent")
        self.budget_input_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.ent_budget = ctk.CTkEntry(self.budget_input_frame, placeholder_text="請輸入每月預算上限 (如: 10000)", width=200)
        self.ent_budget.pack(side="left", padx=(0, 10))
        
        self.btn_save_budget = ctk.CTkButton(
            self.budget_input_frame, text="儲存預算", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"],
            width=90, command=self.save_budget
        )
        self.btn_save_budget.pack(side="left")
        
        # 主題風格設定卡片
        self.theme_card = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.theme_card.pack(fill="x", pady=8, padx=5)
        
        self.lbl_t_title = ctk.CTkLabel(self.theme_card, text="🎨 應用程式主題配色", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_t_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.theme_input_frame = ctk.CTkFrame(self.theme_card, fg_color="transparent")
        self.theme_input_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.opt_theme = ctk.CTkOptionMenu(
            self.theme_input_frame, values=list(self.themes.keys()), width=150,
            command=self.change_theme
        )
        self.opt_theme.set(self.current_theme_name)
        self.opt_theme.pack(side="left")
        
        # 資料備份與工具
        self.tool_card = ctk.CTkFrame(page, fg_color="#1e293b", corner_radius=10)
        self.tool_card.pack(fill="x", pady=8, padx=5)
        
        self.lbl_tool_title = ctk.CTkLabel(self.tool_card, text="🛠️ 資料管理與備份", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_tool_title.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.tool_btn_frame = ctk.CTkFrame(self.tool_card, fg_color="transparent")
        self.tool_btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_export = ctk.CTkButton(
            self.tool_btn_frame, text="📤 匯出當月資料為 CSV", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10b981", hover_color="#059669", height=35, command=self.export_csv
        )
        self.btn_export.pack(side="left", padx=(0, 10))
        
    def refresh_settings(self):
        """載入目前預算與帳本列表並更新設定頁面欄位"""
        current_budget = database.get_monthly_budget(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        self.ent_budget.delete(0, 'end')
        self.ent_budget.insert(0, str(current_budget))
        
        # 更新目前帳本顯示
        self.lbl_current_ledger_info.configure(
            text=f"目前帳本: {self.current_ledger_name} | 代碼 (Token): {self.current_ledger_token}"
        )
        
        # 載入所有帳本並更新下拉選單
        ledgers = database.get_all_ledgers()
        options = [f"{l['name']} ({l['token']})" for l in ledgers]
        self.opt_switch_ledger.configure(values=options)
        
        current_opt = f"{self.current_ledger_name} ({self.current_ledger_token})"
        if current_opt in options:
            self.opt_switch_ledger.set(current_opt)
        else:
            self.opt_switch_ledger.set(options[0])
            
    def on_switch_ledger_changed(self, value):
        """切換帳本時觸發"""
        if "(" in value and value.endswith(")"):
            token = value.split("(")[-1][:-1].strip()
            ledger = database.get_ledger_by_token(token)
            if ledger:
                self.current_ledger_id = ledger["id"]
                self.current_ledger_name = ledger["name"]
                self.current_ledger_token = ledger["token"]
                self.lbl_sync_ledger.configure(text=f"📒 {self.current_ledger_name}")
                self.refresh_settings()
                messagebox.showinfo("切換成功", f"已切換至帳本：{self.current_ledger_name}")

    def open_create_ledger_dialog(self):
        """開啟建立新帳本對話框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("建立新帳本")
        dialog.geometry("340x200")
        dialog.resizable(False, False)
        
        # 強制置頂
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        dialog.grid_columnconfigure((0, 1), weight=1)
        
        lbl_name = ctk.CTkLabel(dialog, text="帳本名稱:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_name.grid(row=0, column=0, columnspan=2, padx=20, pady=(25, 5), sticky="w")
        
        ent_name = ctk.CTkEntry(dialog, placeholder_text="例如: 東京自由行、情侶存錢")
        ent_name.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        def save_and_close():
            name = ent_name.get().strip()
            if not name:
                messagebox.showerror("錯誤", "帳本名稱不能為空！", parent=dialog)
                return
            
            ledger = database.create_ledger(name)
            self.current_ledger_id = ledger["id"]
            self.current_ledger_name = ledger["name"]
            self.current_ledger_token = ledger["token"]
            self.lbl_sync_ledger.configure(text=f"📒 {self.current_ledger_name}")
            
            dialog.destroy()
            self.refresh_settings()
            messagebox.showinfo("建立成功", f"已成功建立新帳本！\n帳本名稱: {ledger['name']}\n代碼 (Token): {ledger['token']}\n\n您現在可以在系統中開始共同記帳，或將代碼分享給他人加入！")
            
        btn_cancel = ctk.CTkButton(dialog, text="取消", fg_color="gray", command=dialog.destroy)
        btn_cancel.grid(row=2, column=0, padx=(20, 5), pady=10, sticky="ew")
        
        btn_submit = ctk.CTkButton(
            dialog, text="建立", fg_color=self.current_theme["primary"], 
            hover_color=self.current_theme["accent"], command=save_and_close
        )
        btn_submit.grid(row=2, column=1, padx=(5, 20), pady=10, sticky="ew")

    def open_join_ledger_dialog(self):
        """開啟加入現有帳本對話框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("加入現有帳本")
        dialog.geometry("340x200")
        dialog.resizable(False, False)
        
        # 強制置頂
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        dialog.grid_columnconfigure((0, 1), weight=1)
        
        lbl_token = ctk.CTkLabel(dialog, text="輸入帳本代碼 (Token):", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_token.grid(row=0, column=0, columnspan=2, padx=20, pady=(25, 5), sticky="w")
        
        ent_token = ctk.CTkEntry(dialog, placeholder_text="請輸入 8 碼帳本代碼")
        ent_token.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        def save_and_close():
            token = ent_token.get().strip().upper()
            if not token:
                messagebox.showerror("錯誤", "代碼不能為空！", parent=dialog)
                return
            
            ledger = database.join_ledger(token)
            if not ledger:
                messagebox.showerror("找不到帳本", "在此資料庫中找不到對應代碼的帳本，請確認輸入是否正確！", parent=dialog)
                return
            
            self.current_ledger_id = ledger["id"]
            self.current_ledger_name = ledger["name"]
            self.current_ledger_token = ledger["token"]
            self.lbl_sync_ledger.configure(text=f"📒 {self.current_ledger_name}")
            
            dialog.destroy()
            self.refresh_settings()
            messagebox.showinfo("加入成功", f"成功加入並切換至帳本：\n{ledger['name']} ({ledger['token']})")
            
        btn_cancel = ctk.CTkButton(dialog, text="取消", fg_color="gray", command=dialog.destroy)
        btn_cancel.grid(row=2, column=0, padx=(20, 5), pady=10, sticky="ew")
        
        btn_submit = ctk.CTkButton(
            dialog, text="加入", fg_color="#a78bfa", 
            hover_color="#8b5cf6", command=save_and_close
        )
        btn_submit.grid(row=2, column=1, padx=(5, 20), pady=10, sticky="ew")
        
    def save_budget(self):
        """儲存預算上限到資料庫"""
        val_str = self.ent_budget.get()
        try:
            val = float(val_str)
            if val < 0:
                raise ValueError
            database.set_monthly_budget(self.current_year, self.current_month, val, ledger_id=self.current_ledger_id)
            messagebox.showinfo("設定成功", f"已將本月預算成功設定為 $ {val:,.1f} 元。")
            self.refresh_settings()
        except ValueError:
            messagebox.showerror("格式錯誤", "請輸入有效的正數金額作為預算上限。")
            
    def change_theme(self, theme_name):
        """動態調整視窗與按鈕的主題配色"""
        self.current_theme_name = theme_name
        self.current_theme = self.themes[theme_name]
        
        # 變更視窗背景與主要交互鈕色彩
        self.configure(fg_color=self.current_theme["bg"])
        self.btn_add_tx.configure(fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"])
        self.btn_save_budget.configure(fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"])
        self.btn_create_ledger.configure(fg_color=self.current_theme["primary"], hover_color=self.current_theme["accent"])
        
        # 刷新目前頁面樣式
        self.show_page(self.active_tab)
    
    def save_user_name(self):
        """儲存使用者在設定頁輸入的記帳人暱稱"""
        name = self.ent_user_name.get().strip()
        if not name:
            messagebox.showerror("格式錯誤", "暱稱不能為空！")
            return
        self.current_user_name = name
        self.lbl_sync_ledger.configure(text=f"📒 {self.current_ledger_name}")
        messagebox.showinfo("儲存成功", f"記帳人暱稱已設定為：{name}\n下次新增交易時將自動帶入。")
        
    def export_csv(self):
        """將目前月份的交易資料匯出為本地 CSV 檔案"""
        txs = database.get_all_transactions_for_month(self.current_year, self.current_month, ledger_id=self.current_ledger_id)
        if not txs:
            messagebox.showwarning("無資料", "本月份尚無記帳資料，無法進行匯出。")
            return
            
        filename = f"記帳資料匯出_{self.current_year}年{self.current_month}月.csv"
        
        try:
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 寫入欄位標題（含記帳人）
                writer.writerow(["交易ID", "交易日期", "收支類型", "類別", "交易金額", "備註說明", "記帳人"])
                for tx in txs:
                    type_zh = "收入" if tx['type'] == 'income' else "支出"
                    writer.writerow([tx['id'], tx['date'], type_zh, tx['category'], tx['amount'], tx['note'], tx.get('recorder', '')])
            
            messagebox.showinfo("匯出成功", f"當月資料已成功匯出至同目錄下的：\n{filename}")
        except Exception as e:
            messagebox.showerror("匯出失敗", f"匯出 CSV 時發生錯誤：\n{e}")

    # ==========================================
    # 彈出視窗：新增交易對話框 (Add Transaction Dialog)
    # ==========================================
    def open_add_transaction_dialog(self):
        """建立並開啟一個自訂子視窗用於新增交易"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("新增記帳明細")
        dialog.geometry("380x570")
        dialog.resizable(False, False)
        
        # 強制子視窗置頂
        dialog.attributes("-topmost", True)
        dialog.grab_set() # 鎖定焦點
        
        dialog.grid_columnconfigure((0, 1), weight=1)
        
        # 1. 交易類型選擇
        lbl_type = ctk.CTkLabel(dialog, text="交易類型:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_type.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        seg_type = ctk.CTkSegmentedButton(dialog, values=["支出", "收入"], font=ctk.CTkFont(size=12))
        seg_type.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        seg_type.set("支出")
        
        # 2. 交易日期
        lbl_date = ctk.CTkLabel(dialog, text="交易日期 (YYYY-MM-DD):", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_date.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        ent_date = ctk.CTkEntry(dialog, placeholder_text="YYYY-MM-DD")
        ent_date.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        # 填入今日日期預設值
        ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 3. 類別選擇
        lbl_category = ctk.CTkLabel(dialog, text="類別選擇:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_category.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        expense_cats = ["餐飲", "交通", "娛樂", "購物", "醫療", "學習", "其他"]
        income_cats = ["薪資", "獎學金", "投資", "其他"]
        
        opt_category = ctk.CTkOptionMenu(dialog, values=expense_cats)
        opt_category.grid(row=5, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        
        # 收支切換時，動態改變類別選項
        def on_type_changed(selected_type):
            if selected_type == "支出":
                opt_category.configure(values=expense_cats)
                opt_category.set(expense_cats[0])
            else:
                opt_category.configure(values=income_cats)
                opt_category.set(income_cats[0])
                
        seg_type.configure(command=on_type_changed)
        
        # 4. 金額輸入
        lbl_amount = ctk.CTkLabel(dialog, text="交易金額 (元):", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_amount.grid(row=6, column=0, padx=20, pady=5, sticky="w")
        
        ent_amount = ctk.CTkEntry(dialog, placeholder_text="請輸入大於0的金額")
        ent_amount.grid(row=7, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        
        # 5. 備註欄
        lbl_note = ctk.CTkLabel(dialog, text="備忘錄說明:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_note.grid(row=8, column=0, padx=20, pady=5, sticky="w")
        
        ent_note = ctk.CTkEntry(dialog, placeholder_text="寫些備忘 (選填)...")
        ent_note.grid(row=9, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        
        # 6. 記帳人欄
        lbl_recorder = ctk.CTkLabel(dialog, text="👤 記帳人:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_recorder.grid(row=10, column=0, padx=20, pady=5, sticky="w")
        
        ent_recorder = ctk.CTkEntry(dialog, placeholder_text="輸入記帳人暱稱")
        ent_recorder.grid(row=11, column=0, columnspan=2, padx=20, pady=(0, 15), sticky="ew")
        ent_recorder.insert(0, self.current_user_name)
        
        # 7. 送出與取消按鈕
        def save_and_close():
            date_val = ent_date.get().strip()
            type_zh = seg_type.get()
            type_val = "expense" if type_zh == "支出" else "income"
            category_val = opt_category.get()
            amount_str = ent_amount.get().strip()
            note_val = ent_note.get().strip()
            recorder_val = ent_recorder.get().strip() or self.current_user_name
            
            # 日期基本格式檢查
            try:
                datetime.strptime(date_val, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("格式錯誤", "日期格式必須為 YYYY-MM-DD\n例如：2026-06-02", parent=dialog)
                return
                
            # 金額正數檢查
            try:
                amount_val = float(amount_str)
                if amount_val <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("格式錯誤", "金額必須是比 0 大的有效數字！", parent=dialog)
                return
            
            # 新增至資料庫（含記帳人）
            database.add_transaction(date_val, type_val, category_val, amount_val, note_val,
                                     ledger_id=self.current_ledger_id, recorder=recorder_val)
            
            # 關閉對話框並更新主介面
            dialog.destroy()
            self.refresh_dashboard()
            self.refresh_history()
            self.refresh_charts()
            
            # 如果是支出，則比對是否超出預算，觸發超支/警戒警告
            if type_val == "expense":
                try:
                    dt = datetime.strptime(date_val, "%Y-%m-%d")
                    tx_year, tx_month = dt.year, dt.month
                    
                    budget = database.get_monthly_budget(tx_year, tx_month, ledger_id=self.current_ledger_id)
                    if budget > 0:
                        summary = database.get_monthly_summary(tx_year, tx_month, ledger_id=self.current_ledger_id)
                        total_expense = summary["total_expense"]
                        ratio = total_expense / budget
                        
                        if ratio >= 1.0:
                            BudgetAlarmDialog(self, budget, total_expense, tx_year, tx_month)
                        elif ratio >= 0.8:
                            BudgetWarningDialog(self, budget, total_expense, tx_year, tx_month)
                except Exception as e:
                    print(f"檢查預算時發生錯誤: {e}")
        btn_cancel = ctk.CTkButton(dialog, text="取消", fg_color="gray", height=32, command=dialog.destroy)
        btn_cancel.grid(row=12, column=0, padx=(20, 5), pady=10, sticky="ew")
        
        btn_submit = ctk.CTkButton(
            dialog, text="儲存", fg_color=self.current_theme["primary"], 
            hover_color=self.current_theme["accent"], height=32, command=save_and_close
        )
        btn_submit.grid(row=12, column=1, padx=(5, 20), pady=10, sticky="ew")

if __name__ == "__main__":
    app = SmartLedgerApp()
    app.mainloop()
