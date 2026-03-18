import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="RoamBudget Secure API")

# 1. UPDATED CORS: Allow all for testing to bypass the browser block
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_user_client(auth_header: str):
    # Log the header to Render logs so we can see if it's actually arriving
    print(f"DEBUG: Auth Header received: {auth_header[:20] if auth_header else 'NONE'}")
    
    if not auth_header or "Bearer " not in auth_header:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    try:
        token = auth_header.split(" ")[1]
        # Ensure these variables actually exist
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("DEBUG: ERROR - Supabase URL or Key is MISSING in Render Env Vars")
            raise Exception("Server configuration error: Missing Supabase credentials")
            
        return create_client(
            SUPABASE_URL, 
            SUPABASE_KEY, 
            options={"headers": {"Authorization": f"Bearer {token}"}}
        )
    except Exception as e:
        print(f"DEBUG: Failed to create Supabase client: {e}")
        raise HTTPException(status_code=500, detail="Internal Client Error")

class ExpenseCreate(BaseModel):
    item_name: str
    amount: float
    category: str
    paid_by: str
    split_count: int = 1

@app.get("/expenses")
async def get_expenses(authorization: str = Header(None)):
    try:
        client = get_user_client(authorization)
        response = client.table("trip_expenses").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/expenses")
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    try:
        client = get_user_client(authorization)
        # Convert Pydantic model to dict
        data = expense.dict()
        response = client.table("trip_expenses").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to insert data")
            
        return response.data[0]
    except Exception as e:
        print(f"Error: {e}") # This shows up in Render Logs
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    try:
        client = get_user_client(authorization)
        client.table("trip_expenses").delete().eq("id", expense_id).execute()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "RoamBudget Auth API is Online"}
