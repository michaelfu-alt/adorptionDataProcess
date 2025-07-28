import json, os

DB_HISTORY_FILE = "db_history.json"

def load_db_history():
    if os.path.exists(DB_HISTORY_FILE):
        with open(DB_HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"history": [], "last": ""}

def save_db_history(history, last):
    with open(DB_HISTORY_FILE, "w") as f:
        json.dump({"history": history, "last": last}, f)