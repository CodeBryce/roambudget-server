# RoamBudget API ✈️
A secure, multi-tenant FastAPI backend for the RoamBudget group expense tracker. 

This server acts as a secure middleware between the frontend and Supabase, utilizing **JWT Authentication** to ensure users can only access their own private trip data.

## 🚀 Features
- **Secure CRUD:** Full Create, Read, and Delete operations for trip expenses.
- **JWT Middleware:** Validates Supabase auth tokens for every request.
- **Multi-Tenancy:** Automated user isolation via PostgreSQL Row Level Security (RLS).
- **CORS Enabled:** Configured for secure communication with GitHub Pages.

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL via Supabase
- **Authentication:** Supabase Auth (JWT)
- **Deployment:** Render (Web Service)
- **Server:** Uvicorn

## ⚙️ Environment Variables
The following variables must be configured in Render:
- `SUPABASE_URL`: Your Supabase Project URL.
- `SUPABASE_KEY`: Your Supabase Anon Public Key.

## 🛠️ Local Setup
1. Clone the repo: `git clone <repo-url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `uvicorn main:app --reload`
