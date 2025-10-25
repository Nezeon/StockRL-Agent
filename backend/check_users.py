import sqlite3

conn = sqlite3.connect('stockrl_dev.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username, email FROM users')
users = cursor.fetchall()
print('Users in database:')
for user in users:
    print(f'  - {user[1]} ({user[2]})')
conn.close()
