from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client, Client
from datetime import date, datetime, timezone
from typing import Optional, List
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="President & RoamBudget API")

# --- Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://zhangsgithub04.github.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase Connection ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Helper Functions ---
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# --- PRESIDENT MODELS ---
class PresidentCreate(BaseModel):
    firstname: str = Field(..., min_length=1, max_length=100)
    lastname: str = Field(..., min_length=1, max_length=100)
    birthdate: Optional[date] = None

class PresidentUpdate(BaseModel):
    firstname: Optional[str] = Field(None, min_length=1, max_length=100)
    lastname: Optional[str] = Field(None, min_length=1, max_length=100)
    birthdate: Optional[date] = None

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
        "message": "Combined API is running",
        "endpoints": ["/presidents", "/expenses"]
    }

# --- PRESIDENT ENDPOINTS ---

@app.get("/presidents")
async def list_presidents():
    response = supabase.table("president").select("*").order("id").execute()
    return response.data

@app.get("/presidents/{president_id}")
async def get_president(president_id: int):
    response = supabase.table("president").select("*").eq("id", president_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="President not found")
    return response.data[0]

@app.post("/presidents", status_code=201)
async def create_president(president: PresidentCreate):
    payload = {
        "firstname": president.firstname.strip(),
        "lastname": president.lastname.strip(),
        "birthdate": president.birthdate.isoformat() if president.birthdate else None,
        "updated_at": utc_now_iso()
    }
    response = supabase.table("president").insert(payload).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create president")
    return response.data[0]

@app.delete("/presidents/{president_id}")
async def delete_president(president_id: int):
    response = supabase.table("president").delete().eq("id", president_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="President not found")
    return {"message": "President deleted successfully"}

# --- ROAMBUDGET (EXPENSES) ENDPOINTS ---

@app.get("/expenses")
async def list_expenses():
    """Fetch all trip expenses from the database."""
    response = supabase.table("trip_expenses").select("*").order("id").execute()
    return response.data

@app.post("/expenses", status_code=201)
async def create_expense(expense: ExpenseCreate):
    """Add a new trip expense."""
    payload = expense.model_dump()
    response = supabase.table("trip_expenses").insert(payload).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create expense")
    
    return response.data[0]

@app.patch("/expenses/{expense_id}")
async def update_expense(expense_id: int, expense: ExpenseUpdate):
    """Update specific fields of an existing expense."""
    update_data = expense.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    response = supabase.table("trip_expenses").update(update_data).eq("id", expense_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Expense not found")

    return response.data[0]

@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    """Remove an expense from the trip plan."""
    response = supabase.table("trip_expenses").delete().eq("id", expense_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted successfully"}
