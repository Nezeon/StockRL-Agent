import sqlite3
import sys
sys.path.insert(0, 'd:/Projects/StockRL-Agent/backend')
from app.dependencies import hash_password

conn = sqlite3.connect('stockrl_dev.db')
cursor = conn.cursor()

# Update Ayushmaan's password to "demo123"
new_hash = hash_password("demo123")
cursor.execute("UPDATE users SET hashed_password = ? WHERE username = 'Ayushmaan'", (new_hash,))
conn.commit()

print("✓ Password updated for user 'Ayushmaan' to 'demo123'")
conn.close()
