import sqlite3
import os
import shutil
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