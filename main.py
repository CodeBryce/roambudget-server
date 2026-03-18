from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from typing import Optional, List
import os
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI app with your custom project title
app = FastAPI(
    title="RoamBudget API", 
    description="Dedicated backend for the RoamBudget group trip expense tracker."
)

# --- Middleware Configuration ---
# CRITICAL: Setting allow_origins to ["*"] allows your GitHub Pages 
# site to access this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase Connection ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables in Render.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ROAMBUDGET MODELS ---
class ExpenseCreate(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0)
    paid_by: str = Field(..., min_length=1)
    split_count: int = Field(1, ge=1)
    is_booked: bool = False

class ExpenseUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    paid_by: Optional[str] = None
    split_count: Optional[int] = None
    is_booked: Optional[bool] = None

# --- ROOT ENDPOINT ---
@app.get("/")
async def root():
    return {
        "project": "RoamBudget",
        "status": "online",
        "docs": "/docs"
    }

# --- EXPENSES ENDPOINTS ---

@app.get("/expenses")
async def list_expenses():
    """Fetch all trip expenses from the Supabase 'trip_expenses' table."""
    response = supabase.table("trip_expenses").select("*").order("id").execute()
    return response.data

@app.post("/expenses", status_code=201)
async def create_expense(expense: ExpenseCreate):
    """Add a new trip expense to the database."""
    payload = expense.model_dump()
    response = supabase.table("trip_expenses").insert(payload).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create expense entry.")
    
    return response.data[0]

@app.patch("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: ExpenseUpdate):
    """Update specific fields of an existing expense (e.g., mark as booked)."""
    update_data = expense.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    response = supabase.table("trip_expenses").update(update_data).eq("id", expense_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Expense not found.")

    return response.data[0]

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    """Remove an expense from the database."""
    response = supabase.table("trip_expenses").delete().eq("id", expense_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Expense not found.")

    return {"message": "Expense deleted successfully from RoamBudget."}
