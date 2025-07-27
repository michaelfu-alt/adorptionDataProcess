import sqlite3, os, shutil

class DatabaseModel:
    def __init__(self):
        self.db_path = None
        self.conn = None

    def connect_database(self, path):
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(path)
        self.db_path = path

    def create_new_database(self, path):
        self.conn = sqlite3.connect(path)
        self.db_path = path
        self._create_tables()

    def backup_database(self, dest_path):
        shutil.copy2(self.db_path, dest_path)

    def delete_database(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.db_path and os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_path = None

    def _create_tables(self):
        # 建立所有业务表
        pass