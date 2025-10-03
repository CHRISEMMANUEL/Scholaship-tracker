import sqlite3

conn = sqlite3.connect("scholarships.db")
cursor = conn.cursor()

# Add new columns if they don’t exist already
cursor.execute("ALTER TABLE scholarships ADD COLUMN deadline TEXT")
cursor.execute("ALTER TABLE scholarships ADD COLUMN eligibility TEXT")
cursor.execute("ALTER TABLE scholarships ADD COLUMN description TEXT")

conn.commit()
conn.close()
print("✅ Database upgraded with new columns.")
