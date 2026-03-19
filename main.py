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
EXPENSES_TABLE = "trip_expenses"

@app.on_event("startup")
async def startup_check():
    missing = [k for k, v in {"SUPABASE_URL": SUPABASE_URL, "SUPABASE_KEY": SUPABASE_KEY}.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")
    print(f"✅ Started. Supabase: {SUPABASE_URL[:40]}...")


# ── AUTH HELPER ───────────────────────────────────────────────────────
def get_user_client(auth_header: Optional[str]) -> Client:
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
        "supabase": SUPABASE_URL[:40] if SUPABASE_URL else "NOT SET",
    }


@app.get("/debug")
async def debug():
    """
    Tests the Supabase connection using the service key directly (no JWT).
    Visit this URL in your browser to check connectivity without needing auth.
    REMOVE this endpoint before going to production.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "SUPABASE_URL or SUPABASE_KEY env var is not set on Render"}

    try:
        # Use a plain admin client (no user JWT) to test raw connectivity
        plain_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = plain_client.table(EXPENSES_TABLE).select("id").limit(1).execute()
        return {
            "status":        "ok",
            "table":         EXPENSES_TABLE,
            "row_sample":    response.data,
            "supabase_url":  SUPABASE_URL[:40],
            "key_prefix":    SUPABASE_KEY[:12] + "...",
        }
    except Exception as e:
        return {
            "status": "error",
            "type":   type(e).__name__,
            "detail": str(e),
            # This is what you need to paste back to me
        }


@app.get("/expenses/{trip_id}")
async def get_expenses(trip_id: str, authorization: str = Header(None)):
    client = get_user_client(authorization)
    try:
        response = (
            client.table(EXPENSES_TABLE)
            .select("*")
            .eq("trip_id", trip_id)
            .order("id", desc=False)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"GET /expenses/{trip_id} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.post("/expenses", status_code=201)
async def add_expense(expense: ExpenseCreate, authorization: str = Header(None)):
    client = get_user_client(authorization)
    try:
        response = client.table(EXPENSES_TABLE).insert(expense.dict()).execute()
        if not response.data:
            raise HTTPException(
                status_code=400,
                detail="Insert returned no data — check RLS policies on trip_expenses."
            )
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"POST /expenses error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None)):
    client = get_user_client(authorization)
    try:
        client.table(EXPENSES_TABLE).delete().eq("id", expense_id).execute()
        return {"status": "deleted", "id": expense_id}
    except Exception as e:
        print(f"DELETE /expenses/{expense_id} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
