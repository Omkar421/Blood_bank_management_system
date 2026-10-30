# Blood Bank Management System

A GitHub-ready Streamlit project for managing blood donors, recipients, inventory, and blood requests.

## Features

- Dashboard with donor, recipient, inventory, and pending-request KPIs
- Donor registration with searchable directory
- Recipient registration and status tracking
- Blood inventory management for A+, A-, B+, B-, AB+, AB-, O+, and O-
- Blood request queue with urgency levels
- Local SQLite database created automatically on first run
- Responsive interface suitable for Streamlit Community Cloud

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app creates `blood_bank.db` automatically. This database is ignored by Git so demo data stays local.

## Deploy on Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, `README.md`, and `.gitignore`.
3. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
4. Select **Create app**.
5. Choose your repository and branch.
6. Set **Main file path** to `app.py`.
7. Click **Deploy**.

### Important deployment note

The included SQLite database is suitable for demos and single-instance use. Streamlit Community Cloud storage is not intended for production persistence; data may be reset after app restarts. For a real multi-user system, replace SQLite with PostgreSQL, Supabase, or another managed database and add authentication.

## Project structure

```text
blood-bank-management-system/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/config.toml
```

## Technology stack

Python · Streamlit · SQLite · Pandas
