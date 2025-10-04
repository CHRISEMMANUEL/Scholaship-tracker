# app.py
# =========================
#  Scholarship Tracker App (custom auth + SQLite)
# =========================

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import bcrypt
from scraper import scrape_scholarships, save_to_db

# -------------------------
# Streamlit Config (must be first Streamlit call)
# -------------------------
st.set_page_config(page_title="Scholarship Tracker", layout="wide")

# -------------------------
# Database (users in same DB so one file to manage)
# -------------------------
DB_FILE = "scholarships.db"

def init_user_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            password TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def add_user(username: str, name: str, password_hash: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # INSERT OR IGNORE so default users only created once
    c.execute(
        "INSERT OR IGNORE INTO users (username, name, password) VALUES (?, ?, ?)",
        (username, name, password_hash),
    )
    conn.commit()
    conn.close()

def get_user(username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, name, password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row  # None or tuple (username, name, password_hash)

# initialize
init_user_table()

# create default users if they don't already exist
def create_default_users():
    add_user("nuel", "Nuel Chris", bcrypt.hashpw("mypassword".encode(), bcrypt.gensalt()).decode())
    add_user("admin", "Admin User", bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode())

create_default_users()

# -------------------------
# Helpers
# -------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed.encode())
    except Exception:
        return False

# -------------------------
# Scholarship DB helper (unchanged)
# -------------------------
def get_scholarships(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

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

# -------------------------
# Session init
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["name"] = None

# -------------------------
# Auth UI (tabs: Login | Sign up)
# -------------------------
st.header("Scholarship Tracker — Sign in or create an account")

tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])

with tab_login:
    with st.form("login_form", clear_on_submit=False):
        login_user = st.text_input("Username")
        login_password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        if not login_user or not login_password:
            st.error("Please enter username and password.")
        else:
            user_row = get_user(login_user)
            if not user_row:
                st.error("User not found. Please sign up.")
            else:
                _, name_from_db, hashed_pw = user_row
                if verify_password(login_password, hashed_pw):
                    st.success("Login successful!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_user
                    st.session_state["name"] = name_from_db
                    st.rerun()

                else:
                    st.error("Incorrect password.")

with tab_signup:
    with st.form("signup_form", clear_on_submit=True):
        new_username = st.text_input("Choose a username")
        new_name = st.text_input("Full name")
        new_password = st.text_input("Choose a password", type="password")
        created = st.form_submit_button("Create account")
    if created:
        if not new_username or not new_password:
            st.error("Please provide username and password.")
        else:
            if get_user(new_username):
                st.error("Username already exists — choose another.")
            else:
                new_hashed = hash_password(new_password)
                add_user(new_username, new_name or new_username, new_hashed)
                st.success("Account created — please log in on the Login tab.")

# -------------------------
# If logged in -> main app
# -------------------------
if st.session_state["logged_in"]:
    st.sidebar.write(f"Signed in as **{st.session_state['name']}**")
    if st.sidebar.button("Logout"):
        # clear session
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["name"] = None
        st.rerun()


    st.title("🎓 Scholarship Tracker")
    st.write(f"Welcome, **{st.session_state['name']}** 👋")

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

# -------------------------
# If not logged in show a friendly note under tabs
# -------------------------
if not st.session_state["logged_in"]:
    st.info("Please sign in or create an account to use the tracker.")
