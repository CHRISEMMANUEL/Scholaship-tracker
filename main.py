import sqlite3
import csv
import json
from scraper import scrape_scholarships, save_to_db
import datetime
from datetime import datetime


def view_scholarships():
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, deadline, eligibility, description, date_scraped FROM scholarships ORDER BY date_scraped DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📌 Latest Scholarships:")
        for idx, (title, link, deadline, eligibility, description, date) in enumerate(rows, 1):
            print(f"{idx}. {title}\n   {link}\n   Deadline: {deadline}\n   Eligibility: {eligibility}\n   (Scraped: {date})\n")
    else:
        print("No scholarships found in the database.")

    return rows


def search_scholarships(keyword):
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, link, deadline, eligibility, description, date_scraped
        FROM scholarships
        WHERE title LIKE ? OR description LIKE ? OR eligibility LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    conn.close()

    if results:
        print(f"\n🔍 Scholarships matching '{keyword}':")
        for idx, (title, link, deadline, eligibility, description, date) in enumerate(results, 1):
            print(f"{idx}. {title}\n   {link}\n   Deadline: {deadline}\n   Eligibility: {eligibility}\n   (Scraped: {date})\n")
    else:
        print(f"No scholarships found for keyword: {keyword}")

    return results


def export_scholarships(data, filename, format="csv"):
    if not data:
        print("⚠️ No data to export.")
        return

    if format == "csv":
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Link", "Deadline", "Eligibility", "Description", "Date Scraped"])
            writer.writerows(data)
        print(f"✅ Exported {len(data)} scholarships to {filename}")

    elif format == "json":
        data_list = [
            {
                "title": row[0],
                "link": row[1],
                "deadline": row[2],
                "eligibility": row[3],
                "description": row[4],
                "date_scraped": row[5],
            }
            for row in data
        ]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=4)
        print(f"✅ Exported {len(data)} scholarships to {filename}")

def view_upcoming_scholarships():
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, deadline FROM scholarships WHERE deadline IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    upcoming = []
    today = datetime.today()

    for title, link, deadline in rows:
        try:
            # Handle various date formats (e.g. "2025-10-15", "15 Oct 2025", etc.)
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            if deadline_date >= today:
                upcoming.append((title, link, deadline))
        except Exception:
            continue  # skip invalid date formats

    if upcoming:
        print("\n📅 Upcoming Scholarships:")
        for idx, (title, link, deadline) in enumerate(upcoming, 1):
            print(f"{idx}. {title}\n   {link}\n   Deadline: {deadline}\n")
    else:
        print("No upcoming scholarships found.")

while True:
    print("\n📌 Scholarship Tracker")
    print("1. Scrape new scholarships")
    print("2. View saved scholarships")
    print("3. Search scholarships by keyword")
    print("4. Export scholarships (CSV/Excel)")
    print("5. View upcoming scholarships (filter by deadline)")
    print("6. Exit")

    choice = input("Enter choice (1-6): ")

    if choice == "1":
        data = scrape_scholarships()
        if data:
            save_to_db(data)

    elif choice == "2":
        view_scholarships()

    elif choice == "3":
        keyword = input("Enter keyword to search (e.g., 'Undergraduate', 'Africa', 'MBA'): ")
        search_scholarships(keyword)

    elif choice == "4":
        export_scholarships()

    elif choice == "5":
        view_upcoming_scholarships()

    elif choice == "6":
        print("Goodbye!")
        break

    else:
        print("Invalid choice. Please select 1-6.")


