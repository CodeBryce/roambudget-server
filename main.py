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

# Confirmed via Supabase dashboard: table is "trip_expenses"
EXPENSES_TABLE = "trip_expenses"

# ── STARTUP CHECK — catches missing env vars before any request hits ──
@app.on_event("startup")
async def startup_check():
    missing = [k for k, v in {"SUPABASE_URL": SUPABASE_URL, "SUPABASE_KEY": SUPABASE_KEY}.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables on Render: {', '.join(missing)}. "
            "Go to Render Dashboard -> your service -> Environment -> Add these vars."
        )
    print(f"RoamBudget API started. Supabase: {SUPABASE_URL[:40]}...")


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
    split_count: int = 1
    trip_id:     str


# ── ROUTES ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message":  "RoamBudget API is online",
        "table":    EXPENSES_TABLE,
        "supabase": SUPABASE_URL[:40] if SUPABASE_URL else "NOT SET — check Render env vars",
    }


@app.get("/expenses/{trip_id}")
async def get_expenses(trip_id: str, authorization: str = Header(None)):
    """Returns all expenses for a given trip_id, ordered by id ascending."""
    client = get_user_client(authorization)
    try:
        response = (
            client.table(EXPENSES_TABLE)
            .select("*")
            .eq("trip_id", trip_id)
            .order("id", desc=False)   # int8 PK — always exists, no created_at needed
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"GET /expenses/{trip_id} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/expenses", status_code=201)
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    """Inserts a new expense tagged with a trip_id."""
    client = get_user_client(authorization)
    try:
        response = client.table(EXPENSES_TABLE).insert(expense.dict()).execute()
        if not response.data:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Insert returned no data. Check your Supabase RLS policy — "
                    "authenticated users need INSERT permission on trip_expenses."
                )
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"POST /expenses error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    """Deletes a single expense. id is int8 in Supabase, typed as int here."""
    client = get_user_client(authorization)
    try:
        client.table(EXPENSES_TABLE).delete().eq("id", expense_id).execute()
        return {"status": "deleted", "id": expense_id}
    except Exception as e:
        print(f"DELETE /expenses/{expense_id} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
