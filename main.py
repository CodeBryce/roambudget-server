import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client, ClientOptions
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="RoamBudget Secure Shared API")

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ENV ───────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Confirmed via Supabase dashboard screenshot: table is "trip_expenses"
EXPENSES_TABLE = "trip_expenses"

# ── AUTH HELPER ───────────────────────────────────────────────────────
def get_user_client(auth_header: Optional[str]) -> Client:
    """Creates a Supabase client scoped to the requesting user's JWT."""
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ", 1)[1]
    opts = ClientOptions(headers={"Authorization": f"Bearer {token}"})

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY, options=opts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase client init failed: {e}")


# ── MODELS ────────────────────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    item_name:   str
    amount:      float
    category:    str
    paid_by:     str
    split_count: int = 1   # How many people this expense is split between
    trip_id:     str       # Groups expenses under a shared trip


# ── ROUTES ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RoamBudget API is online"}


@app.get("/expenses/{trip_id}")
async def get_expenses(trip_id: str, authorization: str = Header(None)):
    """Returns all expenses for a given trip_id, ordered oldest-first."""
    client = get_user_client(authorization)
    try:
        response = (
            client.table(EXPENSES_TABLE)
            .select("*")
            .eq("trip_id", trip_id)
            .order("created_at", desc=False)   # oldest first; remove if no created_at column
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"GET /expenses/{trip_id} error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/expenses", status_code=201)
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    """Inserts a new expense row tagged with a trip_id."""
    client = get_user_client(authorization)
    try:
        response = client.table(EXPENSES_TABLE).insert(expense.dict()).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Insert returned no data — check RLS policies")
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"POST /expenses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    """
    Deletes a single expense by its id.
    Schema confirmed: id is int8, so this correctly types as int.
    """
    client = get_user_client(authorization)
    try:
        client.table(EXPENSES_TABLE).delete().eq("id", expense_id).execute()
        return {"status": "deleted", "id": expense_id}
    except Exception as e:
        print(f"DELETE /expenses/{expense_id} error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
