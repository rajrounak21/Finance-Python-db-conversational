import pandas as pd
import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
email TEXT NOT NULl)
""")


df = pd.read_csv("users.csv")

for i in df.index:
    name = df["name"][i]
    email = df["email"][i]

    cursor.execute("""INSERT INTO users (name,email) VALUES(?,?)""",(name,email))

conn.commit()
print("Data stored successfully")
    


print("Stored Data:")
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(f"Name: {row[1]}, Email: {row[2]}")
