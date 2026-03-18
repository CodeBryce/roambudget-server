# RoamBudget API ✈️
A secure, multi-tenant FastAPI backend for the RoamBudget group expense tracker. 

This server acts as the secure bridge between the frontend and Supabase, utilizing **JWT-based authentication** to ensure strict data isolation between users.

## 🚀 Features
- **Stateless CRUD:** Full Create, Read, and Delete operations for trip expenses.
- **JWT Middleware:** Custom logic to validate Supabase authentication tokens for every request.
- **Data Isolation:** Implements PostgreSQL **Row Level Security (RLS)** to automatically filter data based on the authenticated user's UUID.
- **CORS Configuration:** Optimized for secure cross-origin communication with GitHub Pages.

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL via Supabase
- **Authentication:** Supabase Auth (JWT)
- **Deployment:** Render (Web Service)
- **Server Gateway:** Uvicorn

## ⚙️ Environment Variables
Required configurations for deployment:
- `SUPABASE_URL`: The project-specific Supabase URL.
- `SUPABASE_KEY`: The project's public anonymous key.

## 🛠️ Local Development
1. Clone the repository: `git clone <repo-url>`
2. Install requirements: `pip install -r requirements.txt`
3. Launch the server: `uvicorn main:app --reload`
