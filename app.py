import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
from scraper import scrape_scholarships, save_to_db

# ======================
#  Streamlit Page Setup
# ======================
st.set_page_config(page_title="Scholarship Tracker", layout="wide")

# ======================
#  Authentication Setup
# ======================
# Generate password hashes
hashed_passwords = stauth.Hasher(["mypassword", "admin123"]).generate()

config = {
    "credentials": {
        "usernames": {
            "nuel": {
                "name": "Nuel Chris",
                "password": hashed_passwords[0],  
            },
            "admin": {
                "name": "Admin User",
                "password": hashed_passwords[1],  
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
login_return = authenticator.login("Login", "main")

# Handle 2 vs 3 return values
if len(login_return) == 3:
    name, authentication_status, username = login_return
else:
    name, authentication_status = login_return
    username = None

if authentication_status:
    # ======================
    #  Main App
    # ======================
    authenticator.logout("Logout", "sidebar")

    st.title("🎓 Scholarship Tracker")
    st.write(f"Welcome, **{name}** 👋")

    menu = st.sidebar.radio(
        "📌 Menu",
        ["Scrape New Scholarships", "View Scholarships", "Search Scholarships", "Upcoming Deadlines"],
    )

    if menu == "Scrape New Scholarships":
        st.subheader("🔄 Scraping Scholarships...")
        data = scrape_scholarships()
        if data:
            save_to_db(data)
            st.success(f"{len(data)} scholarships scraped and saved!")
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
            st.dataframe(df.style.apply(highlight_deadline, axis=1), use_container_width=True)
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
                st.dataframe(df.style.apply(highlight_deadline, axis=1), use_container_width=True)
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

            st.dataframe(df.style.apply(highlight_deadline, axis=1), use_container_width=True)
        else:
            st.info("No deadlines found.")

elif authentication_status is False:
    st.error("Username or password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")
