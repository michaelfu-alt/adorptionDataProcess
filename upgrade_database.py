import sqlite3
import os

DB_PATH = "adsorption.db"  # 改成你的数据库文件名

def upgrade_sample_info_table(db_path):
    assert os.path.isfile(db_path), f"Database not found: {db_path}"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print(f"[INFO] Upgrading sample_info in: {db_path}")

    # 检查表结构
    c.execute("PRAGMA table_info(sample_info);")
    columns = [row[1] for row in c.fetchall()]
    print("[INFO] sample_info columns:", columns)

    # 1. 创建新表，有联合主键
    c.execute("""
        CREATE TABLE IF NOT EXISTS sample_info_new (
            sample_id INTEGER,
            field_name TEXT,
            field_value TEXT,
            PRIMARY KEY(sample_id, field_name),
            FOREIGN KEY(sample_id) REFERENCES samples(id)
        );
    """)
    print("[INFO] sample_info_new created.")

    # 2. 把去重后的数据写入新表（保留最新一条）
    c.execute("""
        INSERT OR REPLACE INTO sample_info_new (sample_id, field_name, field_value)
        SELECT sample_id, field_name, field_value
        FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY sample_id, field_name
                ORDER BY rowid DESC
            ) AS rn
            FROM sample_info
        ) WHERE rn = 1;
    """)
    print("[INFO] 去重迁移完成.")

    conn.commit()

    # 3. 删原表，改名
    c.execute("DROP TABLE sample_info;")
    c.execute("ALTER TABLE sample_info_new RENAME TO sample_info;")
    conn.commit()
    print("[INFO] 新表替换完成.")

    # 4. 检查
    c.execute("PRAGMA table_info(sample_info);")
    new_cols = c.fetchall()
    print("[INFO] 新表结构:", new_cols)
    c.execute("SELECT COUNT(*) FROM sample_info;")
    print("[INFO] 样品信息总数:", c.fetchone()[0])

    conn.close()
    print("[SUCCESS] sample_info 升级并去重完毕！")

if __name__ == "__main__":
    upgrade_sample_info_table(DB_PATH)