import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import threading
import time
import pandas as pd
import pickle
import os
import re

# Selenium 相关
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.keys import Keys


class WOSCrawlerGUI:
    # ========== 常用期刊预设（可自行扩展）==========
    PRESET_JOURNALS = [
        "Nature",
        "Science",
        "Cell",
        "Nature Medicine",
        "Nature Biotechnology",
        "Nature Materials",
        "Nature Nanotechnology",
        "Nature Chemistry",
        "Nature Physics",
        "Science Advances",
        "Advanced Materials",
        "JACS",
        "Angewandte Chemie",
        "ACS Nano",
        "Nano Letters",
        "Biomaterials",
        "Acta Materialia",
        "Chemical Reviews",
        "Chemical Society Reviews",
        "Progress in Materials Science",
        "Materials Today",
        "Coordination Chemistry Reviews",
        "Small",
        "Journal of Materials Chemistry A",
        "ACS Applied Materials & Interfaces",
        "Bioactive Materials",
        "Nano Today",
        "Nano-Micro Letters",
        "Advanced Functional Materials",
        "Advanced Healthcare Materials",
        "Carbohydrate Polymers",
        "International Journal of Biological Macromolecules",
        "Colloids and Surfaces B",
        "Langmuir",
        "Polymer",
        "Macromolecules",
        "Chemical Engineering Journal",
        "Water Research",
        "Environmental Science & Technology",
        "Analytical Chemistry",
        "Biosensors and Bioelectronics",
        "Sensors and Actuators B",
        "Talanta",
        "Lab on a Chip",
    ]

    # ========== 文献类型预设 ==========
    DOCUMENT_TYPES = [
        "Article",
        "Review",
        "Letter",
        "Editorial",
        "Meeting Abstract",
        "Proceedings Paper",
    ]

    # ========== 稳健选择器配置 ==========
    SELECTORS = {
        "login_indicator": ".mat-mdc-button-touch-target, .user-name-info, .p-header-user, app-user-menu",
        "record_card": "app-record, .record-card, .search-results-item, div[id^='RECORD_'], .snippet-record",
        "title": "h3.title a, [data-ta='result-record-title'], a.snippet-title, .title-link",
        "authors": ".authors, [data-ta='result-author-link'], .metadata-row, app-authors-links",
        "source": ".source, [data-ta='result-source-link'], .journal-title, .source-title",
        "next_btn": "button[aria-label='Next page'], button[aria-label='Next'], .next-page-btn, [data-ta='next-page-button']",
        "abstract": "[data-ta='result-record-abstract'], div.abstract-text, app-abstract, .snippet-content, .abstract",
        "more_btn": "button[data-ta='show-more'], button.show-more, a.show-more, span.see-more, button[aria-label='Show more']",
        "times_cited": "[data-ta='times-cited'], .times-cited, app-times-cited, .citation-count",
        "doi": "[data-ta='doi'], .doi-link, a[href*='doi.org'], app-doi",
        "doc_type": "[data-ta='doc-type'], .document-type, app-document-type, .type-badge",
        "pub_date": "[data-ta='publication-date'], .pub-date, app-pub-date, .publication-date",
    }

    def __init__(self, root):
        self.root = root
        root.title("Web of Science 文献爬虫 Pro")
        root.geometry("900x880")
        root.minsize(850, 750)

        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 10, "bold"))

        # ========== 可滚动主容器 ==========
        main_canvas = tk.Canvas(root)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
        self.scroll_frame = tk.Frame(main_canvas)
        self.scroll_frame.bind("<Configure>",
                               lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        container = self.scroll_frame

        # ========== 1. 检索词输入 ==========
        ttk.Label(container, text="检索词（逗号分隔词组 AND 连接, / 表示 OR; 空格仅作间隔）:", style="Header.TLabel").pack(
            anchor="w", padx=15, pady=(10, 2))
        self.natural_entry = scrolledtext.ScrolledText(container, wrap=tk.WORD, height=4, width=95)
        self.natural_entry.pack(padx=15, pady=2)

        # ========== 2. 高级检索字段 ==========
        adv_frame = ttk.LabelFrame(container, text="高级检索字段（可选）")
        adv_frame.pack(fill=tk.X, padx=15, pady=5)

        # 作者
        row1 = tk.Frame(adv_frame)
        row1.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(row1, text="作者 (AU=):", width=14).pack(side=tk.LEFT)
        self.author_entry = tk.Entry(row1, width=50)
        self.author_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="多作者用分号分隔，如 Zhang, San; Li, Si", foreground="gray").pack(side=tk.LEFT)

        # 标题精确检索
        row2 = tk.Frame(adv_frame)
        row2.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(row2, text="标题 (TI=):", width=14).pack(side=tk.LEFT)
        self.title_entry = tk.Entry(row2, width=50)
        self.title_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row2, text="逗号分隔多组关键词 AND 连接, / 表示 OR", foreground="gray").pack(side=tk.LEFT)

        # DOI
        row3 = tk.Frame(adv_frame)
        row3.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(row3, text="DOI:", width=14).pack(side=tk.LEFT)
        self.doi_entry = tk.Entry(row3, width=50)
        self.doi_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(row3, text="精确 DOI，如 10.1038/s41586-024-07386-0", foreground="gray").pack(side=tk.LEFT)

        # ========== 3. 期刊过滤区 ==========
        journal_frame = ttk.LabelFrame(container, text="期刊过滤 (SO=)")
        journal_frame.pack(fill=tk.X, padx=15, pady=5)

        # 预设期刊下拉选择
        preset_row = tk.Frame(journal_frame)
        preset_row.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(preset_row, text="常用期刊:", width=14).pack(side=tk.LEFT)
        self.journal_combo = ttk.Combobox(preset_row, values=self.PRESET_JOURNALS, width=45)
        self.journal_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_row, text="添加", command=self._add_preset_journal, width=6).pack(side=tk.LEFT, padx=2)

        # 已选期刊列表
        list_row = tk.Frame(journal_frame)
        list_row.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(list_row, text="已选期刊:", width=14).pack(side=tk.LEFT)
        self.journal_listbox = tk.Listbox(list_row, height=4, selectmode=tk.MULTIPLE, width=55)
        self.journal_listbox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        btn_col = tk.Frame(list_row)
        btn_col.pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_col, text="移除", command=self._remove_journal, width=6).pack(pady=1)
        ttk.Button(btn_col, text="清空", command=self._clear_journals, width=6).pack(pady=1)

        # 自定义期刊输入
        custom_row = tk.Frame(journal_frame)
        custom_row.pack(fill=tk.X, padx=8, pady=3)
        ttk.Label(custom_row, text="自定义:", width=14).pack(side=tk.LEFT)
        self.custom_journal_entry = tk.Entry(custom_row, width=45)
        self.custom_journal_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_row, text="添加", command=self._add_custom_journal, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(custom_row, text="回车也可添加", foreground="gray").pack(side=tk.LEFT, padx=5)
        self.custom_journal_entry.bind("<Return>", lambda e: self._add_custom_journal())

        # 期刊匹配模式
        mode_row = tk.Frame(journal_frame)
        mode_row.pack(fill=tk.X, padx=8, pady=3)
        self.journal_mode = tk.StringVar(value="exact")
        ttk.Radiobutton(mode_row, text="精确匹配 (SO=)", variable=self.journal_mode,
                         value="exact").pack(side=tk.LEFT, padx=(14, 10))
        ttk.Radiobutton(mode_row, text="模糊匹配 (SO=*keyword*)", variable=self.journal_mode,
                         value="fuzzy").pack(side=tk.LEFT)

        # ========== 4. 年份选择 ==========
        year_frame = ttk.LabelFrame(container, text="年份范围 (PY=)")
        year_frame.pack(fill=tk.X, padx=15, pady=5)
        yr = tk.Frame(year_frame)
        yr.pack(fill=tk.X, padx=8, pady=5)
        ttk.Label(yr, text="从:").pack(side=tk.LEFT)
        self.year_start_entry = tk.Entry(yr, width=8)
        self.year_start_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(yr, text="到:").pack(side=tk.LEFT)
        self.year_end_entry = tk.Entry(yr, width=8)
        self.year_end_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(yr, text="留空则从检索词中自动解析年份或不限年份", foreground="gray").pack(side=tk.LEFT, padx=10)

        # ========== 5. 文献类型 ==========
        dtype_frame = ttk.LabelFrame(container, text="文献类型 (DT=)")
        dtype_frame.pack(fill=tk.X, padx=15, pady=5)
        dt = tk.Frame(dtype_frame)
        dt.pack(fill=tk.X, padx=8, pady=5)
        self.dtype_var = tk.StringVar(value="不限")
        ttk.Radiobutton(dt, text="不限", variable=self.dtype_var, value="不限").pack(side=tk.LEFT, padx=5)
        for dt_name in self.DOCUMENT_TYPES:
            ttk.Radiobutton(dt, text=dt_name, variable=self.dtype_var, value=dt_name).pack(side=tk.LEFT, padx=5)

        # ========== 6. 生成检索式预览 ==========
        ttk.Label(container, text="生成的检索式:").pack(anchor="w", padx=15, pady=(8, 2))
        self.query_display = tk.Entry(container, width=95, state='readonly', fg='blue',
                                      font=('Consolas', 9))
        self.query_display.pack(padx=15, pady=2)
        ttk.Button(container, text="预览检索式", command=self._preview_query).pack(anchor="w", padx=15, pady=2)

        # ========== 7. 操作按钮 ==========
        btn_frame = tk.Frame(container)
        btn_frame.pack(pady=8)

        self.start_btn = tk.Button(btn_frame, text="开始抓取", command=self.start_crawl,
                                   bg='#e1f5fe', width=12, font=('Arial', 10, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="停止", state=tk.DISABLED,
                                  command=self.stop_crawl, width=10)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = tk.Button(btn_frame, text="导出Excel", state=tk.DISABLED,
                                    command=self.export_excel, width=10)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.save_cookie_btn = tk.Button(btn_frame, text="保存Cookie", state=tk.DISABLED,
                                         command=self.save_cookies, width=10)
        self.save_cookie_btn.pack(side=tk.LEFT, padx=5)

        # ========== 8. 日志区 ==========
        ttk.Label(container, text="运行日志:", style="Header.TLabel").pack(anchor="w", padx=15, pady=(5, 2))
        self.log_area = scrolledtext.ScrolledText(container, wrap=tk.WORD, height=14, bg='#f5f5f5',
                                                  font=('Consolas', 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # ========== 状态变量与路径 ==========
        self.results = []
        self.crawling = False
        self.driver = None
        self.cookies_file = "wos_cookies.pkl"
        self.local_driver_path = r"D:\software\WebDrivers\msedgedriver.exe"

    # ==================== UI 辅助方法 ====================

    def _add_preset_journal(self):
        name = self.journal_combo.get().strip()
        if name and name not in self._get_journals():
            self.journal_listbox.insert(tk.END, name)
        self.journal_combo.set("")

    def _add_custom_journal(self):
        name = self.custom_journal_entry.get().strip()
        if name and name not in self._get_journals():
            self.journal_listbox.insert(tk.END, name)
        self.custom_journal_entry.delete(0, tk.END)

    def _remove_journal(self):
        for idx in reversed(self.journal_listbox.curselection()):
            self.journal_listbox.delete(idx)

    def _clear_journals(self):
        self.journal_listbox.delete(0, tk.END)

    def _get_journals(self):
        return list(self.journal_listbox.get(0, tk.END))

    # ==================== 日志 ====================

    def log(self, msg):
        def _append():
            self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_area.see(tk.END)
        self.root.after(0, _append)

    # ==================== 安全提取 ====================

    def get_text(self, element, default="N/A"):
        try:
            return element.text.strip() if element else default
        except:
            return default

    def safe_find(self, parent, key, attribute=None):
        selectors = self.SELECTORS[key].split(',')
        for s in selectors:
            try:
                element = parent.find_element(By.CSS_SELECTOR, s.strip())
                return element.get_attribute(attribute) if attribute else element
            except:
                continue
        return None

    # ==================== 检索式生成（增强版） ====================

    def _parse_search_terms(self, raw_text):
        """解析检索词文本为 WOS 检索式片段

        规则：
        - 逗号（中英文均可）作为词组分隔符，词组之间用 AND 连接
        - 斜杠 / 作为词组间的 OR 连接符
        - 空格仅作为词组内部的间隔，不做额外处理（原样保留）
        - 用户显式输入的 AND / OR 保留原样
        - 引号内的内容视为完整短语，不被拆分
        - 例如: "3D printing array, biosensor" -> (3D printing array AND biosensor)
        - 例如: "3D printing array / biosensor" -> (3D printing array OR biosensor)
        - 例如: "3D printing, biosensor / immunosensor" -> (3D printing AND (biosensor OR immunosensor))
        """
        text = raw_text.strip()
        if not text:
            return ""

        # 按逗号（中英文）分割为词组（逗号 = AND 分隔）
        groups = re.split(r'[,，]', text)

        group_parts = []
        for grp in groups:
            grp = grp.strip()
            if not grp:
                continue

            # 检查词组内是否有斜杠分隔（斜杠 = OR 连接）
            or_parts = re.split(r'\s*/\s*', grp)
            or_parts = [p.strip() for p in or_parts if p.strip()]

            if len(or_parts) == 1:
                group_parts.append(or_parts[0])
            else:
                group_parts.append(f"({' OR '.join(or_parts)})")

        if not group_parts:
            return ""

        if len(group_parts) == 1:
            return group_parts[0]
        else:
            return f"({' AND '.join(group_parts)})"

    def build_query(self):
        """根据 UI 所有输入项构建完整的 WOS 高级检索式

        生成逻辑：
        - TS=(...)     : 检索词区的关键词（逗号分隔词组 OR 连接，词组内空格 AND 连接）
        - AU=(...)     : 作者（多作者 OR 连接）
        - TI=(...)     : 标题精确关键词
        - SO=(...)     : 期刊名（多期刊 OR 连接）
        - DO=...       : DOI（精确）
        - PY=(起-止)   : 年份范围
        - DT=...       : 文献类型
        所有字段之间用 AND 连接
        """
        parts = []

        # 1. 检索词 -> TS
        ts_text = self.natural_entry.get("1.0", tk.END).strip()
        if ts_text:
            # 先提取年份避免被当作关键词
            year_pattern = r'(\d{4})\s*-\s*(\d{4})'
            years_found = re.findall(year_pattern, ts_text)
            ts_clean = re.sub(year_pattern, '', ts_text)

            ts_expr = self._parse_search_terms(ts_clean)
            if ts_expr:
                parts.append(f"TS=({ts_expr})")

            # 如果检索词里有年份但 UI 年份为空，自动使用
            if years_found and not self.year_start_entry.get().strip():
                self.year_start_entry.delete(0, tk.END)
                self.year_start_entry.insert(0, years_found[0][0])
            if years_found and not self.year_end_entry.get().strip():
                self.year_end_entry.delete(0, tk.END)
                self.year_end_entry.insert(0, years_found[0][1])

        # 2. 作者 -> AU
        author_text = self.author_entry.get().strip()
        if author_text:
            # 支持分号分隔的多作者
            authors = [a.strip() for a in author_text.split(';') if a.strip()]
            if authors:
                au_terms = " OR ".join([f'"{a}"' if ',' in a else a for a in authors])
                parts.append(f"AU=({au_terms})")

        # 3. 标题 -> TI
        title_text = self.title_entry.get().strip()
        if title_text:
            ti_expr = self._parse_search_terms(title_text)
            if ti_expr:
                parts.append(f"TI=({ti_expr})")

        # 4. DOI -> DO
        doi_text = self.doi_entry.get().strip()
        if doi_text:
            parts.append(f'DOI="{doi_text}"')

        # 5. 期刊 -> SO
        journals = self._get_journals()
        if journals:
            if self.journal_mode.get() == "exact":
                so_terms = " OR ".join([f'"{j}"' for j in journals])
                parts.append(f"SO=({so_terms})")
            else:
                # 模糊匹配：SO=*keyword*
                so_terms = " OR ".join([f'SO=*{j}*' for j in journals])
                parts.append(f"({so_terms})")

        # 6. 年份 -> PY
        start_y = self.year_start_entry.get().strip()
        end_y = self.year_end_entry.get().strip()
        if start_y and end_y:
            parts.append(f"PY=({start_y}-{end_y})")
        elif start_y:
            parts.append(f"PY>={start_y}")
        elif end_y:
            parts.append(f"PY<={end_y}")

        # 7. 文献类型 -> DT
        dtype = self.dtype_var.get()
        if dtype != "不限":
            parts.append(f"DT={dtype}")

        if not parts:
            return ""
        return " AND ".join(parts)

    def _preview_query(self):
        query = self.build_query()
        self.query_display.config(state='normal')
        self.query_display.delete(0, tk.END)
        self.query_display.insert(0, query if query else "(请输入至少一个检索条件)")
        self.query_display.config(state='readonly')

    # ==================== 浏览器驱动 ====================

    def setup_driver(self):
        options = webdriver.EdgeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)

        if os.path.exists(self.local_driver_path):
            self.log(f"使用本地驱动: {self.local_driver_path}")
            service = EdgeService(executable_path=self.local_driver_path)
        else:
            self.log("使用 Selenium Manager 自动匹配驱动...")
            service = EdgeService()

        driver = webdriver.Edge(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        return driver

    # ==================== Cookie 管理 ====================

    def save_cookies(self):
        if self.driver:
            with open(self.cookies_file, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            self.log(f"Cookie 已保存至 {self.cookies_file}")

    # ==================== 核心爬取逻辑 ====================

    def execute_task(self, query):
        try:
            self.driver = self.setup_driver()
            wait = WebDriverWait(self.driver, 30)

            self.log("正在加载 WOS 高级检索页面...")
            self.driver.get("https://www.webofscience.com/wos/woscc/advanced-search")

            # 注入 Cookie
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, "rb") as f:
                    for cookie in pickle.load(f):
                        try:
                            self.driver.add_cookie(cookie)
                        except:
                            pass
                self.driver.refresh()
                time.sleep(2)

            # 清理遮罩层
            self.log("清理页面干扰元素...")
            self.driver.execute_script("""
                var masks = document.querySelectorAll('.onetrust-pc-dark-filter, .cdk-overlay-container, #onetrust-banner-sdk');
                masks.forEach(m => m.remove());
                document.body.classList.remove('no-scroll');
            """)

            # 注入检索式
            self.log(f"注入检索式: {query}")
            try:
                input_box = wait.until(EC.element_to_be_clickable((By.ID, "advancedSearchInputArea")))
            except TimeoutException:
                self.log("未找到 advancedSearchInputArea，尝试备选选择器...")
                input_box = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "textarea[id*='search'], textarea[class*='search-input'], wos-search-field textarea")))
            self.driver.execute_script("arguments[0].value = '';", input_box)
            input_box.send_keys(query)
            self.driver.execute_script("""
                var el = arguments[0];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
            """, input_box)
            time.sleep(1)

            # 触发搜索
            input_box.send_keys(Keys.ENTER)
            self.log("已发送搜索指令，等待结果渲染...")

            # 启用 Cookie 保存按钮
            self.root.after(0, lambda: self.save_cookie_btn.config(state=tk.NORMAL))

            # 等待结果页面
            wait.until(lambda d: "/results" in d.current_url or d.find_elements(By.TAG_NAME, "app-record"))
            self.log("跳转成功，开始滚动加载数据...")

            page = 1
            while self.crawling:
                self.log(f"正在分析第 {page} 页...")

                # 模拟滚动触发懒加载
                self.driver.execute_script("window.scrollTo(0, 600);")
                time.sleep(1.5)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(1)

                # 多选择器回退获取记录
                records = []
                for selector in self.SELECTORS["record_card"].split(','):
                    found = self.driver.find_elements(By.CSS_SELECTOR, selector.strip())
                    if found:
                        records = found
                        break

                if not records:
                    self.log("当前页未检测到文献卡片，保存快照以便检查...")
                    with open("debug_no_records.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    break

                for rec in records:
                    if not self.crawling:
                        break
                    try:
                        title_el = self.safe_find(rec, "title")
                        if not title_el:
                            continue

                        title_text = title_el.text.strip()
                        link_url = title_el.get_attribute("href")

                        if not any(d['链接'] == link_url for d in self.results):
                            # 尝试展开摘要
                            try:
                                more_btn = self.safe_find(rec, "more_btn")
                                if more_btn:
                                    self.driver.execute_script("arguments[0].click();", more_btn)
                                    time.sleep(0.2)
                            except:
                                pass

                            # 提取 DOI
                            doi_text = "N/A"
                            doi_el = self.safe_find(rec, "doi")
                            if doi_el:
                                doi_href = doi_el.get_attribute("href") or ""
                                doi_match = re.search(r'10\.\d{4,}/[^\s?]+', doi_href)
                                if doi_match:
                                    doi_text = doi_match.group(0).rstrip('.')
                                else:
                                    doi_text = self.get_text(doi_el)
                            if doi_text == "N/A":
                                # 尝试从链接中提取
                                if link_url:
                                    doi_match = re.search(r'10\.\d{4,}/[^\s?]+', link_url)
                                    if doi_match:
                                        doi_text = doi_match.group(0).rstrip('.')

                            item = {
                                "标题": title_text,
                                "作者": self.get_text(self.safe_find(rec, "authors")),
                                "期刊": self.get_text(self.safe_find(rec, "source")),
                                "DOI": doi_text,
                                "被引频次": self.get_text(self.safe_find(rec, "times_cited")),
                                "文献类型": self.get_text(self.safe_find(rec, "doc_type")),
                                "出版日期": self.get_text(self.safe_find(rec, "pub_date")),
                                "摘要": self.get_text(self.safe_find(rec, "abstract")),
                                "链接": link_url,
                                "采集页码": page,
                            }
                            self.results.append(item)
                    except:
                        continue

                self.log(f"第 {page} 页处理完毕，目前总计抓取: {len(self.results)}")

                # 翻页
                try:
                    next_btn = self.safe_find(self.driver, "next_btn")
                    classes = next_btn.get_attribute("class") or ""
                    if next_btn and next_btn.is_enabled() and "disabled" not in classes:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                        time.sleep(1)
                        self.driver.execute_script("arguments[0].click();", next_btn)
                        page += 1
                        time.sleep(4)
                    else:
                        self.log("已到达最后一页或翻页按钮不可用。")
                        break
                except Exception as e:
                    self.log(f"翻页尝试失败: {str(e)}")
                    break

            self.log(f"采集结束，共获取 {len(self.results)} 条记录。")
            self.root.after(0, lambda: self.export_btn.config(state=tk.NORMAL))

        except Exception as e:
            self.log(f"运行时错误: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("crash_debug.png")
                self.log("已保存错误截图 crash_debug.png")
        finally:
            if self.driver:
                self.driver.quit()
                self.log("浏览器已关闭。")
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.save_cookie_btn.config(state=tk.DISABLED))

    # ==================== 操作入口 ====================

    def start_crawl(self):
        query = self.build_query()
        if not query:
            messagebox.showwarning("提示", "请输入至少一个检索条件！")
            return
        self.query_display.config(state='normal')
        self.query_display.delete(0, tk.END)
        self.query_display.insert(0, query)
        self.query_display.config(state='readonly')

        self.results = []
        self.crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.log_area.delete("1.0", tk.END)

        threading.Thread(target=self.execute_task, args=(query,), daemon=True).start()

    def stop_crawl(self):
        self.crawling = False

    def export_excel(self):
        if not self.results:
            messagebox.showinfo("提示", "暂无数据可导出。")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx"), ("CSV 文件", "*.csv"), ("所有文件", "*.*")])
        if path:
            df = pd.DataFrame(self.results)
            # 列顺序：标题、作者、期刊、DOI、被引频次、文献类型、出版日期、摘要、链接、采集页码
            col_order = ["标题", "作者", "期刊", "DOI", "被引频次", "文献类型", "出版日期", "摘要", "链接", "采集页码"]
            df = df[[c for c in col_order if c in df.columns]]
            df.to_excel(path, index=False)
            messagebox.showinfo("成功", f"已导出 {len(self.results)} 条记录至:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = WOSCrawlerGUI(root)
    root.mainloop()
