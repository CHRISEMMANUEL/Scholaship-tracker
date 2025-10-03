import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timezone
from notify import send_telegram_message

BASE_URL = "https://www.scholarshipsads.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def scrape_scholarships():
    response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
    if response.status_code != 200:
        print(f"❌ Failed to fetch page, status {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    scholarships = []
    seen = set()

    links = soup.select("a[href^='https://www.scholarshipsads.com/']")
    for a in links:
        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href or href in seen:
            continue
        seen.add(href)

        deadline, eligibility, description = scrape_details(href)

        scholarships.append({
            "title": title,
            "link": href,
            "deadline": deadline,
            "eligibility": eligibility,
            "description": description,
            "date_scraped": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"✅ Found: {title} -> {href}")

    return scholarships


def scrape_details(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None, None, None

        soup = BeautifulSoup(resp.text, "html.parser")

        deadline_tag = soup.find("li", string=lambda t: t and "Deadline" in t)
        deadline = deadline_tag.get_text(strip=True) if deadline_tag else None

        eligibility_tag = soup.find("li", string=lambda t: t and "Eligibility" in t)
        eligibility = eligibility_tag.get_text(strip=True) if eligibility_tag else None

        description_tag = soup.find("div", class_="entry-content")
        description = description_tag.get_text(strip=True) if description_tag else None

        return deadline, eligibility, description
    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")
        return None, None, None


def save_to_db(scholarships):
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()

    data_to_insert = [
        (s["title"], s["link"], s["deadline"], s["eligibility"], s["description"], s["date_scraped"])
        for s in scholarships
    ]

    cursor.executemany(
        """
        INSERT OR IGNORE INTO scholarships 
        (title, link, deadline, eligibility, description, date_scraped)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        data_to_insert,
    )

    conn.commit()
    conn.close()

    # ✅ Send Telegram notification for latest scholarship
    if scholarships:
        latest = scholarships[0]
        msg = f"🎓 New Scholarship Added!\n\n{latest['title']}\nDeadline: {latest['deadline']}\n🔗 {latest['link']}"
        send_telegram_message(msg)

    print(f"💾 Saved {len(scholarships)} scholarships to database.")


if __name__ == "__main__":
    data = scrape_scholarships()
    if data:
        save_to_db(data)
    else:
        print("⚠️ No scholarships found.")
