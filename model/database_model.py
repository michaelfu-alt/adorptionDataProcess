import sqlite3
import os
import shutil
import json


class DatabaseModel:
    def __init__(self, db_path="adsorption.db"):
        self.db_path = db_path
        self.conn = None
        if db_path:
            self.connect_database(db_path)

    def connect_database(self, db_path):
        """连接数据库（已存在）"""
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        print(f"[SQLite] Connected to DB: {db_path}")
        self._ensure_tables()

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












# import mysql.connector

# class DatabaseModel:
#     def __init__(self, host="localhost", user="root", password="", database=None):
#         self.host = host
#         self.user = user
#         self.password = password
#         self.database = database
#         self.conn = None
#         if database:
#             self.connect_database(database)

#     def connect_database(self, db_name):
#         """连接数据库（已存在）"""
#         self.conn = mysql.connector.connect(
#             host=self.host,
#             user=self.user,
#             password=self.password,
#             database=db_name,
#             charset="utf8mb4"
#         )
#         self.database = db_name
#         print(f"[MySQL] Connected to DB: {db_name}")
#         self._ensure_tables()

#     def create_new_database(self, db_name):
#         """创建新库并连接"""
#         # 先连到 MySQL，不指定库
#         tmp_conn = mysql.connector.connect(
#             host=self.host, user=self.user, password=self.password
#         )
#         tmp_cur = tmp_conn.cursor()
#         tmp_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4;")
#         tmp_conn.commit()
#         tmp_conn.close()
#         self.connect_database(db_name)

#     def backup_database(self, backup_path):
#         """MySQL备份建议用 mysqldump 工具调用，这里只给方法思路"""
#         import subprocess
#         cmd = f"mysqldump -h{self.host} -u{self.user} -p{self.password} {self.database} > {backup_path}"
#         print("Running:", cmd)
#         subprocess.run(cmd, shell=True)
#         print(f"[MySQL] Backup complete: {backup_path}")

#     def delete_database(self):
#         """删除整个数据库"""
#         if not self.database:
#             raise RuntimeError("当前无数据库连接")
#         tmp_conn = mysql.connector.connect(
#             host=self.host, user=self.user, password=self.password
#         )
#         tmp_cur = tmp_conn.cursor()
#         tmp_cur.execute(f"DROP DATABASE `{self.database}`;")
#         tmp_conn.commit()
#         tmp_conn.close()
#         print(f"[MySQL] Database dropped: {self.database}")
#         self.conn = None
#         self.database = None

#     def _ensure_tables(self):
#         """初始化表结构，只建一次"""
#         c = self.conn.cursor()
#         c.execute("""
#             CREATE TABLE IF NOT EXISTS samples (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 name VARCHAR(255) UNIQUE,
#                 psd_json TEXT
#             )
#         """)
#         c.execute("""
#             CREATE TABLE IF NOT EXISTS sample_info (
#                 sample_id INT,
#                 field_name VARCHAR(255),
#                 field_value TEXT,
#                 FOREIGN KEY(sample_id) REFERENCES samples(id)
#             )
#         """)
#         # ... 其它表结构，照 sqlite 改为 MySQL 语法 ...
#         self.conn.commit()