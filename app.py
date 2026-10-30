import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "blood_bank.db"

st.set_page_config(
    page_title="Blood Bank Management System",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Database layer -----------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                city TEXT,
                last_donation TEXT,
                available INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                units_required INTEGER NOT NULL,
                hospital TEXT NOT NULL,
                phone TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_group TEXT UNIQUE NOT NULL,
                units INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id INTEGER,
                blood_group TEXT NOT NULL,
                units INTEGER NOT NULL,
                hospital TEXT NOT NULL,
                urgency TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                requested_at TEXT NOT NULL,
                FOREIGN KEY(recipient_id) REFERENCES recipients(id)
            );
            """
        )
        groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for group in groups:
            conn.execute(
                "INSERT OR IGNORE INTO inventory (blood_group, units, last_updated) VALUES (?, 0, ?)",
                (group, datetime.now().isoformat(timespec="seconds")),
            )


def query(sql, params=(), fetch=False):
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.lastrowid


def rows_to_df(rows):
    return pd.DataFrame([dict(row) for row in rows]) if rows else pd.DataFrame()


init_db()

# ----------------------------- Styling -----------------------------
st.markdown(
    """
    <style>
    .main { background: #f8fafc; }
    [data-testid="stSidebar"] { background: #111827; }
    [data-testid="stSidebar"] * { color: #f9fafb !important; }
    .hero { background: linear-gradient(120deg,#991b1b,#dc2626); color:white; padding: 1.5rem 2rem; border-radius: 16px; margin-bottom: 1.2rem; }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: .35rem 0 0; opacity: .92; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e5e7eb; padding: 0.8rem; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
    .small-note { color:#64748b; font-size:.88rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Helpers -----------------------------
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GENDERS = ["Female", "Male", "Other"]


def add_flash(kind, message):
    getattr(st, kind)(message)


def inventory_df():
    return rows_to_df(query("SELECT * FROM inventory ORDER BY CASE blood_group WHEN 'O-' THEN 1 WHEN 'O+' THEN 2 WHEN 'A+' THEN 3 WHEN 'A-' THEN 4 WHEN 'B+' THEN 5 WHEN 'B-' THEN 6 WHEN 'AB+' THEN 7 ELSE 8 END", fetch=True))


# ----------------------------- Sidebar -----------------------------
st.sidebar.title("🩸 Blood Bank")
st.sidebar.caption("Management & tracking portal")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Donors", "Recipients", "Inventory", "Blood Requests", "About Project"],
)
st.sidebar.divider()
st.sidebar.info("Demo-ready Streamlit project\n\nData is stored locally in SQLite. For production, use authentication and a managed database.")

# ----------------------------- Dashboard -----------------------------
if page == "Dashboard":
    st.markdown('<div class="hero"><h1>Blood Bank Management System</h1><p>Monitor donors, recipients, inventory, and urgent blood requests in one place.</p></div>', unsafe_allow_html=True)
    donors = query("SELECT COUNT(*) AS c FROM donors", fetch=True)[0]["c"]
    recipients = query("SELECT COUNT(*) AS c FROM recipients", fetch=True)[0]["c"]
    total_units = query("SELECT COALESCE(SUM(units),0) AS c FROM inventory", fetch=True)[0]["c"]
    pending = query("SELECT COUNT(*) AS c FROM requests WHERE status='Pending'", fetch=True)[0]["c"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registered Donors", donors)
    c2.metric("Recipients", recipients)
    c3.metric("Available Units", total_units)
    c4.metric("Pending Requests", pending)

    st.subheader("Inventory overview")
    inv = inventory_df()
    left, right = st.columns([1.25, 1])
    with left:
        st.dataframe(inv[["blood_group", "units", "last_updated"]].rename(columns={"blood_group":"Blood Group", "units":"Units", "last_updated":"Last Updated"}), use_container_width=True, hide_index=True)
    with right:
        chart = inv.set_index("blood_group")["units"]
        st.bar_chart(chart, color="#dc2626", height=270)

    st.subheader("Recent requests")
    recent = rows_to_df(query("SELECT r.id, r.blood_group, r.units, r.hospital, r.urgency, r.status, r.requested_at FROM requests r ORDER BY r.id DESC LIMIT 8", fetch=True))
    if recent.empty:
        st.info("No blood requests yet. Add one from the Blood Requests page.")
    else:
        st.dataframe(recent.rename(columns={"id":"ID", "blood_group":"Blood Group", "units":"Units", "hospital":"Hospital", "urgency":"Urgency", "status":"Status", "requested_at":"Requested At"}), use_container_width=True, hide_index=True)

# ----------------------------- Donors -----------------------------
elif page == "Donors":
    st.title("Donor Management")
    tab_add, tab_list = st.tabs(["Add donor", "Donor directory"])
    with tab_add:
        with st.form("donor_form", clear_on_submit=True):
            a, b, c = st.columns(3)
            name = a.text_input("Full name *")
            age = b.number_input("Age *", min_value=18, max_value=70, value=25)
            gender = c.selectbox("Gender *", GENDERS)
            d, e, f = st.columns(3)
            blood_group = d.selectbox("Blood group *", BLOOD_GROUPS)
            phone = e.text_input("Phone *")
            email = f.text_input("Email")
            city = st.text_input("City")
            last_donation = st.date_input("Last donation date (optional)", value=None)
            available = st.checkbox("Currently available for donation", value=True)
            submitted = st.form_submit_button("Save donor", type="primary")
            if submitted:
                if not name.strip() or not phone.strip():
                    st.error("Name and phone are required.")
                else:
                    query("INSERT INTO donors (name,age,gender,blood_group,phone,email,city,last_donation,available,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (name.strip(), age, gender, blood_group, phone.strip(), email.strip(), city.strip(), last_donation.isoformat() if last_donation else None, int(available), datetime.now().isoformat(timespec="seconds")))
                    st.success(f"Donor {name.strip()} added successfully.")
    with tab_list:
        search = st.text_input("Search by name, phone, city, or blood group")
        sql = "SELECT id, name, age, gender, blood_group, phone, email, city, last_donation, available FROM donors"
        params = ()
        if search.strip():
            sql += " WHERE name LIKE ? OR phone LIKE ? OR city LIKE ? OR blood_group LIKE ?"
            s = f"%{search.strip()}%"
            params = (s, s, s, s)
        sql += " ORDER BY id DESC"
        df = rows_to_df(query(sql, params, fetch=True))
        if df.empty:
            st.info("No donors found.")
        else:
            df["available"] = df["available"].map({1: "Yes", 0: "No"})
            st.dataframe(df.rename(columns={"id":"ID", "name":"Name", "age":"Age", "gender":"Gender", "blood_group":"Blood Group", "phone":"Phone", "email":"Email", "city":"City", "last_donation":"Last Donation", "available":"Available"}), use_container_width=True, hide_index=True)
            delete_id = st.number_input("Enter donor ID to delete", min_value=0, step=1, value=0)
            if st.button("Delete donor", type="secondary") and delete_id:
                query("DELETE FROM donors WHERE id=?", (delete_id,))
                st.success("Donor deleted.")
                st.rerun()

# ----------------------------- Recipients -----------------------------
elif page == "Recipients":
    st.title("Recipient Management")
    tab_add, tab_list = st.tabs(["Register recipient", "Recipient records"])
    with tab_add:
        with st.form("recipient_form", clear_on_submit=True):
            a, b, c = st.columns(3)
            name = a.text_input("Full name *")
            age = b.number_input("Age *", min_value=0, max_value=120, value=30)
            gender = c.selectbox("Gender *", GENDERS)
            d, e, f = st.columns(3)
            blood_group = d.selectbox("Required blood group *", BLOOD_GROUPS)
            units = e.number_input("Units required *", min_value=1, max_value=20, value=1)
            hospital = f.text_input("Hospital *")
            phone = st.text_input("Contact phone")
            submitted = st.form_submit_button("Register recipient", type="primary")
            if submitted:
                if not name.strip() or not hospital.strip():
                    st.error("Name and hospital are required.")
                else:
                    query("INSERT INTO recipients (name,age,gender,blood_group,units_required,hospital,phone,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)", (name.strip(), age, gender, blood_group, units, hospital.strip(), phone.strip(), "Pending", datetime.now().isoformat(timespec="seconds")))
                    st.success("Recipient registered successfully.")
    with tab_list:
        df = rows_to_df(query("SELECT id,name,age,gender,blood_group,units_required,hospital,phone,status,created_at FROM recipients ORDER BY id DESC", fetch=True))
        if df.empty:
            st.info("No recipients registered.")
        else:
            st.dataframe(df.rename(columns={"id":"ID", "name":"Name", "age":"Age", "gender":"Gender", "blood_group":"Blood Group", "units_required":"Units", "hospital":"Hospital", "phone":"Phone", "status":"Status", "created_at":"Created At"}), use_container_width=True, hide_index=True)
            rid = st.number_input("Recipient ID", min_value=0, step=1, value=0)
            status = st.selectbox("Update status", ["Pending", "Approved", "Fulfilled", "Cancelled"])
            if st.button("Update recipient status") and rid:
                query("UPDATE recipients SET status=? WHERE id=?", (status, rid))
                st.success("Recipient status updated.")
                st.rerun()

# ----------------------------- Inventory -----------------------------
elif page == "Inventory":
    st.title("Blood Inventory")
    st.caption("Update the number of available blood units for each blood group.")
    inv = inventory_df()
    for _, row in inv.iterrows():
        col1, col2, col3 = st.columns([1, 1, 2])
        col1.markdown(f"### {row['blood_group']}")
        new_units = col2.number_input("Units", min_value=0, max_value=10000, value=int(row["units"]), key=f"inv_{row['blood_group']}")
        if col3.button(f"Save {row['blood_group']}", key=f"save_{row['blood_group']}"):
            query("UPDATE inventory SET units=?, last_updated=? WHERE blood_group=?", (new_units, datetime.now().isoformat(timespec="seconds"), row["blood_group"]))
            st.success(f"Inventory updated for {row['blood_group']}.")
            st.rerun()
    st.divider()
    st.subheader("Compatibility quick guide")
    st.dataframe(pd.DataFrame({"Blood Group": BLOOD_GROUPS, "Can donate to": ["A+, AB+", "A-, A+, AB-, AB+", "B+, AB+", "B-, B+, AB-, AB+", "AB+", "AB-, AB+", "O+, A+, B+, AB+", "All blood groups"]}), use_container_width=True, hide_index=True)

# ----------------------------- Requests -----------------------------
elif page == "Blood Requests":
    st.title("Blood Requests")
    with st.form("request_form", clear_on_submit=True):
        a, b, c = st.columns(3)
        recipient_id = a.number_input("Recipient ID (optional)", min_value=0, step=1, value=0)
        blood_group = b.selectbox("Blood group *", BLOOD_GROUPS)
        units = c.number_input("Units *", min_value=1, max_value=20, value=1)
        hospital = st.text_input("Hospital *")
        urgency = st.select_slider("Urgency", options=["Routine", "High", "Critical"], value="Routine")
        submitted = st.form_submit_button("Create request", type="primary")
        if submitted:
            if not hospital.strip():
                st.error("Hospital is required.")
            else:
                query("INSERT INTO requests (recipient_id,blood_group,units,hospital,urgency,status,requested_at) VALUES (?,?,?,?,?,?,?)", (recipient_id if recipient_id else None, blood_group, units, hospital.strip(), urgency, "Pending", datetime.now().isoformat(timespec="seconds")))
                st.success("Blood request created.")
    st.subheader("Request queue")
    df = rows_to_df(query("SELECT id,recipient_id,blood_group,units,hospital,urgency,status,requested_at FROM requests ORDER BY CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 ELSE 3 END, id DESC", fetch=True))
    if df.empty:
        st.info("No blood requests yet.")
    else:
        st.dataframe(df.rename(columns={"id":"ID", "recipient_id":"Recipient ID", "blood_group":"Blood Group", "units":"Units", "hospital":"Hospital", "urgency":"Urgency", "status":"Status", "requested_at":"Requested At"}), use_container_width=True, hide_index=True)
        request_id = st.number_input("Request ID", min_value=0, step=1, value=0)
        new_status = st.selectbox("Update request status", ["Pending", "Approved", "Fulfilled", "Rejected"])
        if st.button("Update request") and request_id:
            query("UPDATE requests SET status=? WHERE id=?", (new_status, request_id))
            st.success("Request status updated.")
            st.rerun()

# ----------------------------- About -----------------------------
else:
    st.title("About this project")
    st.markdown("""
    ### Blood Bank Management System
    This project is a beginner-friendly information systems application built with **Python, Streamlit, SQLite, and Pandas**.

    **Main modules**
    - Dashboard with live KPIs and inventory chart
    - Donor registration and searchable donor directory
    - Recipient registration and status management
    - Blood inventory management for all eight blood groups
    - Blood request queue with urgency and fulfilment status

    **Suggested future enhancements**
    - Login and role-based access control
    - Email/SMS notifications for urgent requests
    - Donor eligibility reminders and donation history
    - PostgreSQL or Supabase database for multi-user deployment
    - Export reports to PDF/Excel
    """)
    st.info("To deploy: push this folder to GitHub, then create a Streamlit Community Cloud app using app.py as the main file.")
