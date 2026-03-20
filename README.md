# RoamBudget - API Server

The backend engine for **RoamBudget**, responsible for secure data transactions, trip management, and expense logic. Built with **FastAPI** and designed to run on **Render**.

## 🚀 Features
- **Secure Expense Management**: Handles POST and DELETE operations for expenses with Bearer Token authentication.
- **Trip Operations**: API endpoints for managing trip data and cascading deletions when a trip is removed by its creator.
- **Auth Integration**: Decodes Supabase JWTs to verify user identity without unnecessary network calls.
- **CORS Enabled**: Configured to allow secure communication with the frontend domain.

## 🛠️ Tech Stack
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Client**: Supabase-py
- **Authentication**: Supabase Auth (JWT)

## ⚙️ Environment Variables
The following variables must be configured in your **Render** environment settings:
- `SUPABASE_URL`: Your Supabase Project URL.
- `SUPABASE_KEY`: Your Supabase Service Role key (for administrative operations).
- `EXPENSES_TABLE`: Set to `trip_expenses`.
- `TRIPS_TABLE`: Set to `trips`.
- `MEMBERS_TABLE`: Set to `trip_members`.

## 📦 Local Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Start the server: `uvicorn main:app --reload`
