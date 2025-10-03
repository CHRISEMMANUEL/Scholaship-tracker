import sqlite3
import csv
import pandas as pd
from scraper import scrape_scholarships, save_to_db


def view_scholarships():
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, date_scraped FROM scholarships ORDER BY date_scraped DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n📌 Latest Scholarships:")
        for idx, (title, link, date) in enumerate(rows, 1):
            print(f"{idx}. {title}\n   {link}\n   (Scraped: {date})\n")
    else:
        print("No scholarships found in the database.")


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


def export_scholarships():
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scholarships")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        # Save as CSV
        with open("scholarships.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Link", "Deadline", "Eligibility", "Description", "Date Scraped"])
            writer.writerows(rows)
        print("✅ Scholarships exported to scholarships.csv")

        # Save as Excel
        df = pd.DataFrame(rows, columns=["ID", "Title", "Link", "Deadline", "Eligibility", "Description", "Date Scraped"])
        df.to_excel("scholarships.xlsx", index=False)
        print("✅ Scholarships exported to scholarships.xlsx")
    else:
        print("No scholarships found in the database to export.")


while True:
    print("\n📌 Scholarship Tracker")
    print("1. Scrape new scholarships")
    print("2. View saved scholarships")
    print("3. Search scholarships by keyword")
    print("4. Export scholarships (CSV/Excel)")
    print("5. Exit")

    choice = input("Enter choice (1-5): ")

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
        print("Goodbye!")
        break

    else:
        print("Invalid choice. Please select 1-5.")
