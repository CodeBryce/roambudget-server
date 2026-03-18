import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel

app = FastAPI(title="RoamBudget Secure API")

# Enable CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# This helper function creates a Supabase client using the USER'S token
def get_supabase_client(auth_header: str):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Extract 'Bearer <token>'
    token = auth_header.replace("Bearer ", "")
    
    # We create a client that uses the user's JWT instead of the master key
    return create_client(
        SUPABASE_URL, 
        SUPABASE_KEY, 
        options={"headers": {"Authorization": f"Bearer {token}"}}
    )

class ExpenseCreate(BaseModel):
    item_name: str
    amount: float
    category: str
    paid_by: str
    split_count: int = 1

@app.get("/expenses")
async def get_expenses(authorization: str = Header(None)):
    client = get_supabase_client(authorization)
    response = client.table("trip_expenses").select("*").execute()
    return response.data

@app.post("/expenses")
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    client = get_supabase_client(authorization)
    # user_id is automatically handled by the DB DEFAULT auth.uid()
    response = client.table("trip_expenses").insert(expense.dict()).execute()
    return response.data[0]

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    client = get_supabase_client(authorization)
    response = client.table("trip_expenses").delete().eq("id", expense_id).execute()
    return {"status": "deleted"}

@app.get("/")
def root():
    return {"status": "RoamBudget Secure API Online"}
