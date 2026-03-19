import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client, ClientOptions
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="RoamBudget Secure Shared API")

# 1. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 3. Helper Function to create a User-Specific Client
def get_user_client(auth_header: str):
    print(f"DEBUG: Auth Header received: {auth_header[:20] if auth_header else 'NONE'}")
    
    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    try:
        token = auth_header.split(" ")[1]
        opts = ClientOptions(headers={"Authorization": f"Bearer {token}"})
        
        return create_client(
            SUPABASE_URL, 
            SUPABASE_KEY, 
            options=opts
        )
    except Exception as e:
        print(f"DEBUG: Failed to create Supabase client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. Data Models
class ExpenseCreate(BaseModel):
    item_name: str
    amount: float
    category: str
    paid_by: str
    split_count: int = 1
    trip_id: str  # NEW: Links the expense to a shared trip

# 5. Routes

@app.get("/expenses/{trip_id}")
async def get_expenses(trip_id: str, authorization: str = Header(None)):
    """Fetches all expenses for a specific shared trip ID."""
    try:
        client = get_user_client(authorization)
        # We filter by trip_id so everyone in the group sees the same list
        response = client.table("trip_expenses").select("*").eq("trip_id", trip_id).execute()
        return response.data
    except Exception as e:
        print(f"GET Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/expenses")
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    """Inserts an expense tagged with a trip_id."""
    try:
        client = get_user_client(authorization)
        data = expense.dict()
        response = client.table("trip_expenses").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Insert failed")
            
        return response.data[0]
    except Exception as e:
        print(f"POST Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    try:
        client = get_user_client(authorization)
        client.table("trip_expenses").delete().eq("id", expense_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        print(f"DELETE Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "RoamBudget Shared Auth API is Online"}
