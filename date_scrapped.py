import sqlite3

conn = sqlite3.connect("scholarships.db")
cursor = conn.cursor()

# Drop old table
cursor.execute("DROP TABLE IF EXISTS scholarships")

# Create new table with date_scraped
cursor.execute("""
CREATE TABLE scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    link TEXT,
    date_scraped TEXT
)
""")

conn.commit()
conn.close()
print("✅ Table recreated with date_scraped column.")
