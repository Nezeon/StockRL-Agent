import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'stockrl_dev.db'
print(f"DB: {DB_PATH}")

run_id = sys.argv[1] if len(sys.argv) > 1 else None

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# List tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("Tables:", [r[0] for r in cur.fetchall()])

if run_id:
    # Count metrics for specific run
    cur.execute("SELECT COUNT(*) as c FROM agent_metrics WHERE agent_run_id = ?", (run_id,))
    print("agent_metrics count for run:", cur.fetchone()[0])
    cur.execute("SELECT * FROM agent_metrics WHERE agent_run_id = ? ORDER BY timestamp DESC LIMIT 5", (run_id,))
    rows = cur.fetchall()
    for r in rows:
        print(dict(r))
else:
    # Show counts overview
    for table in ("users","portfolios","agent_runs","agent_metrics"):
        try:
            cur.execute(f"SELECT COUNT(*) as c FROM {table}")
            print(f"{table}:", cur.fetchone()[0])
        except Exception as e:
            print(f"{table}: (error) {e}")

conn.close()
