# app.py
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "scholarships.db"

def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM scholarships", conn)
    conn.close()
    return df

st.set_page_config(page_title="Scholarship Tracker", layout="wide")

st.title("🎓 Scholarship Tracker Dashboard")

df = get_data()

if df.empty:
    st.warning("⚠️ No scholarships found in database. Run the scraper first.")
else:
    # Convert deadlines into datetime
    df["deadline_date"] = pd.to_datetime(df["deadline"], errors="coerce")
    today = datetime.today()
    df["days_left"] = (df["deadline_date"] - today).dt.days

    # --- Dashboard cards ---
    col1, col2, col3 = st.columns(3)
    col1.metric("📌 Total Scholarships", len(df))
    col2.metric("⏳ Upcoming Deadlines", df[df["days_left"] >= 0].shape[0])
    col3.metric("🆕 Scraped Today", df[df["date_scraped"].str.startswith(today.strftime("%Y-%m-%d"))].shape[0])

    # --- Search / filter ---
    st.subheader("🔍 Search Scholarships")
    keyword = st.text_input("Enter keyword (e.g., MBA, Africa, Undergraduate):")
    filtered = df.copy()
    if keyword:
        filtered = df[
            df["title"].str.contains(keyword, case=False, na=False)
            | df["description"].str.contains(keyword, case=False, na=False)
            | df["eligibility"].str.contains(keyword, case=False, na=False)
        ]

    st.dataframe(
        filtered[["title", "link", "deadline", "eligibility", "days_left"]],
        use_container_width=True,
    )

    # --- Chart ---
    st.subheader("📊 Upcoming Deadlines")
    upcoming = df[df["days_left"] >= 0].sort_values("deadline_date")
    if not upcoming.empty:
        chart_data = upcoming.groupby("deadline_date").size().reset_index(name="count")
        st.bar_chart(chart_data.set_index("deadline_date"))
    else:
        st.info("No upcoming deadlines found.")
