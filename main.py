import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="RoamBudget Secure API")

# Enable CORS so your GitHub Pages site can talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables from Render settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- HELPER FUNCTION ---
# This function extracts the user's Token from the browser request
# and creates a temporary Supabase client with that user's permissions.
def get_user_client(auth_header: str):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Remove "Bearer " prefix to get just the token
    token = auth_header.replace("Bearer ", "")
    
    # Return a client that is RESTRICTED to this specific user
    return create_client(
        SUPABASE_URL, 
        SUPABASE_KEY, 
        options={"headers": {"Authorization": f"Bearer {token}"}}
    )

# --- MODELS ---
class ExpenseCreate(BaseModel):
    item_name: str
    amount: float
    category: str
    paid_by: str
    split_count: int = 1

# --- ROUTES ---

@app.get("/expenses")
async def get_expenses(authorization: str = Header(None)):
    client = get_user_client(authorization)
    # Because of RLS, this .select("*") ONLY returns rows owned by the user
    response = client.table("trip_expenses").select("*").execute()
    return response.data

@app.post("/expenses")
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    client = get_user_client(authorization)
    # We don't need to manually set user_id; 
    # the DB does it automatically via 'DEFAULT auth.uid()'
    response = client.table("trip_expenses").insert(expense.dict()).execute()
    return response.data[0]

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    client = get_user_client(authorization)
    # RLS ensures you can't delete someone else's ID even if you guess it
    response = client.table("trip_expenses").delete().eq("id", expense_id).execute()
    return {"status": "deleted"}

@app.get("/")
def root():
    return {"message": "RoamBudget Auth API is Online"}
