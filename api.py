import requests
import sqlite3
API_URL = "https://openlibrary.org/search.json?q=python"

conn = sqlite3.connect("books.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    year INTEGER
    )
""")

response = requests.get(API_URL)
if response.status_code == 200:
    data = response.json()
    books = data.get('docs', [])  # Get the 'docs' array from the response

    for book in books:
        title = book.get('title', 'Unknown')
        # Author names are in an array, get the first one or 'Unknown'
        author = book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'
        # First publish year
        year = book.get('first_publish_year', 0)
        
        cursor.execute("""INSERT INTO books(title, author, year) VALUES(?, ?, ?)""", (title, author, year))
    
    conn.commit()
    print("Data stored successfully")

else:
    print("Failed to fetch data")


print("Stored Books:")
cursor.execute("SELECT title,author,year FROM books")
rows = cursor.fetchall()
for row in rows:
    print(f"Title: {row[0]}, Author: {row[1]}, Year: {row[2]}")

conn.close()


