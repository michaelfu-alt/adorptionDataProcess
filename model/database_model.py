import sqlite3
import os
import shutil
import json
from datetime import datetime

class DatabaseModel:
    def __init__(self, db_path="adsorption.db"):
        self.db_path = db_path
        self.conn = None
        if db_path:
            self.connect_database(db_path)

    def connect_database(self, db_path):
        if self.conn:
            self.conn.close()
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        print(f"[SQLite] Switched to DB: {db_path}")
        self._ensure_tables()  # 如需建表

    def create_new_database(self, db_path):
        """创建新库并连接"""
        # 删除同名旧文件
        if os.path.isfile(db_path):
            os.remove(db_path)
        self.connect_database(db_path)
        print(f"[SQLite] Created new DB: {db_path}")

    def backup_database(self, backup_path):
        """备份数据库（直接复制DB文件即可）"""
        if not self.db_path or not os.path.isfile(self.db_path):
            raise RuntimeError("当前无数据库连接或数据库文件不存在")
        shutil.copy2(self.db_path, backup_path)
        print(f"[SQLite] Backup complete: {backup_path}")

    import os

    def delete_database(self):
        """关闭并删除当前 SQLite 数据库文件"""
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.db_path and os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_path = None


            
    def _ensure_tables(self):
        """初始化表结构，只建一次"""
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                psd_json TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sample_info (
                sample_id INTEGER,
                field_name TEXT,
                field_value TEXT,
                PRIMARY KEY(sample_id, field_name),
                FOREIGN KEY(sample_id) REFERENCES samples(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sample_results (
                sample_id INTEGER,
                result_name TEXT,
                result_value TEXT,
                FOREIGN KEY(sample_id) REFERENCES samples(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS adsorption_data (
                sample_id INTEGER,
                q REAL,
                i_ads REAL,
                i_des REAL,
                FOREIGN KEY(sample_id) REFERENCES samples(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS pore_distribution (
                sample_id INTEGER,
                pore_size REAL,
                distribution REAL,
                FOREIGN KEY(sample_id) REFERENCES samples(id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS dft_data (
                sample_id INTEGER,
                row_index INTEGER,
                data_json TEXT,
                FOREIGN KEY(sample_id) REFERENCES samples(id)
            )
        """)
        self.conn.commit()

    def get_sample_overview(self):
        """
        Returns list of tuples:
        (name, sample_meta, probe, bet, vol, pore0_0.5, pore2_5, analysis_date, date_logged)
        """
        c = self.conn.cursor()
        c.execute("SELECT id, name FROM samples ORDER BY name")
        overview = []

        for sid, name in c.fetchall():
            # sample_meta
            c.execute(
                "SELECT field_value FROM sample_info WHERE sample_id=? AND field_name LIKE ?",
                (sid, "%样品名称%")
            )
            row = c.fetchone()
            sample_meta = row[0] if row and row[0] is not None else ""

            # probe
            c.execute(
                "SELECT field_value FROM sample_info WHERE sample_id=? AND field_name LIKE ?",
                (sid, "%吸附质%")
            )
            row = c.fetchone()
            probe = row[0] if row and row[0] is not None else ""

            # BET surface
            c.execute(
                "SELECT result_value FROM sample_results WHERE sample_id=? AND result_name LIKE ?",
                (sid, "%BET比表面积%")
            )
            row = c.fetchone()
            bet = row[0] if row and row[0] is not None else ""

            # pore volume
            c.execute(
                "SELECT result_value FROM sample_results WHERE sample_id=? AND result_name LIKE ?",
                (sid, "%总孔体积%")
            )
            row = c.fetchone()
            vol = row[0] if row and row[0] is not None else ""

            # DFT percentages by explicit range labels
            pr_0_0_5   = self.get_percentage_for_range(sid, "0~0.5")
            pr_0_5_0_7 = self.get_percentage_for_range(sid, "0.5~0.7")
            pr_0_7_1   = self.get_percentage_for_range(sid, "0.7~1")
            pr_1_2     = self.get_percentage_for_range(sid, "1~2")
            pr_2_5     = self.get_percentage_for_range(sid, "2~5")
            pr_5_10    = self.get_percentage_for_range(sid, "5~10")
            pr_10_inf  = self.get_percentage_for_range(sid, "10~Inf")

            # analysis date
            c.execute(
                "SELECT field_value FROM sample_info WHERE sample_id=? AND field_name LIKE ?",
                (sid, "%完成分析时间%")
            )
            row = c.fetchone()
            raw = row[0] if row and row[0] is not None else ""
            analysis_date = raw.split()[0] if raw else ""

            # date logged
            c.execute(
                "SELECT field_value FROM sample_info WHERE sample_id=? AND field_name LIKE ?",
                (sid, "%Date Logged%")
            )
            row = c.fetchone()
            date_logged = row[0] if row and row[0] is not None else ""

            overview.append((name, sample_meta, probe, bet, vol, pr_0_0_5, pr_0_5_0_7, pr_0_7_1, pr_1_2, pr_2_5, pr_5_10, pr_10_inf, analysis_date, date_logged))

        return overview


    def get_percentage_for_range(self, sample_id, range_label):
        """
        Look up the exact percentage for a given 'pore_range' label
        from the dft_data JSON table.
        """
        c = self.conn.cursor()
        c.execute(
        "SELECT data_json FROM dft_data WHERE sample_id = ? ORDER BY row_index",
        (sample_id,)
        )
        for (blob,) in c.fetchall():
            rec = json.loads(blob)
            if rec.get("pore_range") == range_label:
                try:
                    return float(rec.get("percentage", 0))
                except:
                    return 0
        return 0

    def get_sample_info(self, sample_name):
        """
        Return the sample_info fields for a given sample as a dict.
        """
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return {}
        sid = row[0]
        c.execute("SELECT field_name, field_value FROM sample_info WHERE sample_id = ?", (sid,))
        return {r[0]: r[1] for r in c.fetchall()}

    def get_sample_results(self, sample_name):
        """
        Return the sample_results fields for a given sample as a dict.
        """
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return {}
        sid = row[0]
        c.execute("SELECT result_name, result_value FROM sample_results WHERE sample_id = ?", (sid,))
        return {r[0]: r[1] for r in c.fetchall()}

    def get_adsorption_data(self, sample_name):
        """
        Return two lists of (q, value) for adsorption and desorption.
        """
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return [], []
        sid = row[0]
        c.execute("SELECT q, i_ads, i_des FROM adsorption_data WHERE sample_id = ? ORDER BY q", (sid,))
        ads, des = [], []
        for q, i_ads, i_des in c.fetchall():
            if i_ads is not None:
                ads.append((q, i_ads))
            if i_des is not None:
                des.append((q, i_des))
        return ads, des

    def get_pore_distribution(self, sample_name):
        """
        Return the pore_distribution rows as a list of (pore_size, distribution).
        """
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return []
        sid = row[0]
        c.execute(
            "SELECT pore_size, distribution FROM pore_distribution "
            "WHERE sample_id = ? ORDER BY pore_size",
            (sid,)
        )
        return c.fetchall()

    def get_dft_data(self, sample_name):
        """
        Return the raw DFT rows JSON for a given sample as a list of dicts.
        """
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return []
        sid = row[0]
        c.execute("SELECT data_json FROM dft_data WHERE sample_id = ? ORDER BY row_index", (sid,))
        rows = c.fetchall()
        return [json.loads(r[0]) for r in rows]


    #Edit Sample info
    def get_edit_sample_info(self, sample_name):
        
        info = self.get_sample_info(sample_name)
        if not info:
            print(f"[Warning] No info for sample: {sample_name}")
            return {}  # 返回空dict
        return info
    
    def update_sample_info(self, sample_name, new_info):
        print("[DEBUG] 正在写入 db_path:", self.db_path, "conn id:", id(self.conn))
        print("[DEBUG] update_sample_info:", sample_name, new_info)

        c = self.conn.cursor()
        # 查找样品ID
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            print(f"[ERROR] 未找到样品: {sample_name}，数据库未更新！")
            return
        sample_id = row[0]
        print(f"[DEBUG] 样品ID: {sample_id}")

        # 对每个字段进行更新（推荐用 REPLACE，确保唯一性）
        for field, value in new_info.items():
            c.execute(
                "INSERT OR REPLACE INTO sample_info(sample_id, field_name, field_value) VALUES (?, ?, ?)",
                (sample_id, field, str(value))
            )
        self.conn.commit()
        print("[DEBUG] 保存后 sample_info：", c.fetchall())
        print(f"{sample_name} is updated")



    #Delete Sample
    def delete_sample(self, sample_name):
        c = self.conn.cursor()
        # 查找样品ID
        c.execute("SELECT id FROM samples WHERE name = ?", (sample_name,))
        row = c.fetchone()
        if not row:
            return False
        sample_id = row[0]
        # 删除相关表数据
        for table in [
            "sample_info", "sample_results", "adsorption_data",
            "pore_distribution", "dft_data"
        ]:
            c.execute(f"DELETE FROM {table} WHERE sample_id = ?", (sample_id,))
        # 删除主表
        c.execute("DELETE FROM samples WHERE id = ?", (sample_id,))
        self.conn.commit()
        return True
    
    # Colone Sample
    def clone_sample(self, old_name):
        """
        Create a brand‐new sample in this same database by copying EVERYTHING
        (metadata, results, adsorption/desorption, DFT‐rows, pore_distribution)
        from an existing sample named old_name.  Returns the new sample_name used.
        """
        # 1) Retrieve old sample’s ID
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (old_name,))
        row = c.fetchone()
        if not row:
            raise ValueError(f"No such sample to clone: '{old_name}'")
        old_sid = row[0]

        # 2) Read **all** data out of the old sample
        # – sample_info
        c.execute("SELECT field_name, field_value FROM sample_info WHERE sample_id = ?", (old_sid,))
        info = {r[0]: r[1] for r in c.fetchall()}

        # – sample_results
        c.execute("SELECT result_name, result_value FROM sample_results WHERE sample_id = ?", (old_sid,))
        results = {r[0]: r[1] for r in c.fetchall()}

        # – adsorption_data
        c.execute("SELECT q, i_ads, i_des FROM adsorption_data WHERE sample_id = ? ORDER BY q", (old_sid,))
        ads_list = []
        des_list = []
        for q, i_ads, i_des in c.fetchall():
            if i_ads is not None:
                ads_list.append((q, i_ads))
            if i_des is not None:
                des_list.append((q, i_des))

        # – raw DFT JSON rows
        c.execute("SELECT data_json FROM dft_data WHERE sample_id = ? ORDER BY row_index", (old_sid,))
        dft_list = [json.loads(r[0]) for r in c.fetchall()]

        # 3) Choose a brand‐new unique name based on old_name
        base = old_name
        name = base
        idx = 1
        c.execute("SELECT COUNT(*) FROM samples WHERE name = ?", (name,))
        while c.fetchone()[0] > 0:
            name = f"{base}_{idx}"
            idx += 1
            c.execute("SELECT COUNT(*) FROM samples WHERE name = ?", (name,))

        # 4) Insert new row into samples
        new_sid = self._get_or_create_sample(name)

        # 5) Insert a fresh “Date Logged” timestamp
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._insert_field(new_sid, "Date Logged", ts)

        # 6) Re‐insert metadata & results
        for k, v in info.items():
            self._insert_field(new_sid, k, v)
        for k, v in results.items():
            self._insert_result(new_sid, k, v)

        # 7) Re‐insert adsorption/desorption
        qvals = sorted({q for q, _ in ads_list} | {q for q, _ in des_list})
        for q in qvals:
            va = next((x for p, x in ads_list if p == q), None)
            vd = next((x for p, x in des_list if p == q), None)
            self._insert_data_point(new_sid, q, va, vd)

        # 8) Re‐insert raw DFT rows JSON & rebuild pore_distribution
        self._ingest_dft_list(new_sid, dft_list)
        self._ingest_pore_distribution_from_dft(new_sid, dft_list)

        # 9) Commit & return the new sample name
        self.conn.commit()
        return name
    
    def _get_or_create_sample(self, name: str) -> int:
        c = self.conn.cursor()
        c.execute("SELECT id FROM samples WHERE name = ?", (name,))
        row = c.fetchone()
        if row:
            return row[0]  # 返回已有样品ID

        # 不存在则插入新样品
        c.execute("INSERT INTO samples (name) VALUES (?)", (name,))
        self.conn.commit()
        return c.lastrowid