import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from scraper import scrape_scholarships, save_to_db


# ======================
#  Authentication Setup
# ======================
# Example user credentials (replace with real ones later)
config = {
    "credentials": {
        "usernames": {
            "nuel": {
                "name": "Nuel Chris",
                "password": stauth.Hasher(["mypassword"]).generate()[0],  # hashed
            },
            "admin": {
                "name": "Admin User",
                "password": stauth.Hasher(["admin123"]).generate()[0],
            },
        }
    },
    "cookie": {"name": "scholarship_tracker", "key": "random_secret_key", "expiry_days": 30},
    "preauthorized": {"emails": []},
}

authenticator = stauth.Authenticate(
    config["credentials"], config["cookie"]["name"], config["cookie"]["key"], config["cookie"]["expiry_days"]
)


# ======================
#  DB Helper
# ======================
def get_scholarships(query, params=()):
    conn = sqlite3.connect("scholarships.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


# Deadline highlighter
def highlight_deadline(row):
    try:
        deadline = datetime.strptime(str(row["Deadline"]), "%Y-%m-%d")
        days_left = (deadline - datetime.today()).days
        if days_left <= 7:
            return ["background-color: #ffcccc"] * len(row)
        elif days_left <= 30:
            return ["background-color: #fff3cd"] * len(row)
        else:
            return ["background-color: #d4edda"] * len(row)
    except:
        return [""] * len(row)


# ======================
#  Login Page
# ======================
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    # ======================
    #  Main App
    # ======================
    st.set_page_config(page_title="Scholarship Tracker", layout="wide")

    st.title("🎓 Scholarship Tracker")
    st.write(f"Welcome, **{name}** 👋")

    authenticator.logout("Logout", "sidebar")

    menu = st.sidebar.radio(
        "📌 Menu",
        ["Scrape New Scholarships", "View Scholarships", "Search Scholarships", "Upcoming Deadlines"],
    )

    if menu == "Scrape New Scholarships":
        st.subheader("🔄 Scraping Scholarships...")
        data = scrape_scholarships()
        if data:
            save_to_db(data)
            st.success(f"✅ {len(data)} scholarships scraped and saved!")
        else:
            st.warning("No new scholarships found.")

    elif menu == "View Scholarships":
        st.subheader("📋 Latest Scholarships")
        rows = get_scholarships(
            "SELECT title, link, deadline, eligibility, description, date_scraped FROM scholarships ORDER BY date_scraped DESC LIMIT 50"
        )
        if rows:
            df = pd.DataFrame(rows, columns=["Title", "Link", "Deadline", "Eligibility", "Description", "Scraped"])
            df["Link"] = df["Link"].apply(lambda x: f"[🔗 Open]({x})")
            st.dataframe(df.style.apply(highlight_deadline, axis=1), width="stretch")
        else:
            st.info("No scholarships found in the database.")

    elif menu == "Search Scholarships":
        keyword = st.text_input("🔍 Enter keyword (e.g., Undergraduate, Africa, MBA):")
        if keyword:
            rows = get_scholarships(
                """
                SELECT title, link, deadline, eligibility, description, date_scraped
                FROM scholarships
                WHERE title LIKE ? OR description LIKE ? OR eligibility LIKE ?
                """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
            )
            if rows:
                df = pd.DataFrame(rows, columns=["Title", "Link", "Deadline", "Eligibility", "Description", "Scraped"])
                df["Link"] = df["Link"].apply(lambda x: f"[🔗 Open]({x})")
                st.dataframe(df.style.apply(highlight_deadline, axis=1), width="stretch")
            else:
                st.warning(f"No scholarships found for keyword: {keyword}")

    elif menu == "Upcoming Deadlines":
        st.subheader("⏳ Scholarships Closing Soon")
        rows = get_scholarships(
            "SELECT title, link, deadline, eligibility, description, date_scraped FROM scholarships WHERE deadline != ''"
        )
        if rows:
            df = pd.DataFrame(rows, columns=["Title", "Link", "Deadline", "Eligibility", "Description", "Scraped"])
            df["Link"] = df["Link"].apply(lambda x: f"[🔗 Open]({x})")

            try:
                df["Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
                df = df.dropna(subset=["Deadline"])
                df = df.sort_values("Deadline").head(20)
            except:
                pass

            st.dataframe(df.style.apply(highlight_deadline, axis=1), width="stretch")
        else:
            st.info("No deadlines found.")

elif authentication_status is False:
    st.error("Username or password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")
