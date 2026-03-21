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
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY")
EXPENSES_TABLE = "trip_expenses"
TRIPS_TABLE    = "trips"
MEMBERS_TABLE  = "trip_members"


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

def get_user_id(auth_header: str) -> str:
    """Decodes the JWT to extract the user's UUID without a network call."""
    import base64, json
    token = auth_header.split(" ", 1)[1]
    # JWT payload is the second segment, base64url-encoded
    payload_b64 = token.split(".")[1]
    # Fix padding
    payload_b64 += "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    return payload.get("sub")


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


# ── Expenses ──────────────────────────────────────────────────────────

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
            raise HTTPException(status_code=400, detail="Insert returned no data — check RLS policies.")
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


# ── Trips ─────────────────────────────────────────────────────────────

@app.delete("/trips/{trip_code}")
async def delete_trip(trip_code: str, authorization: str = Header(None)):
    """
    Deletes a trip and all its expenses + member records.
    Only the trip creator is allowed to do this — enforced here AND via Supabase RLS.
    """
    client  = get_user_client(authorization)
    user_id = get_user_id(authorization)

    try:
        # 1. Verify the caller is the creator
        trip_resp = (
            client.table(TRIPS_TABLE)
            .select("id, creator_id")
            .eq("trip_code", trip_code)
            .single()
            .execute()
        )
        trip = trip_resp.data
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_code}' not found.")
        if trip["creator_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only the trip creator can delete a trip.")

        trip_uuid = trip["id"]

        # 2. Delete all expenses for this trip
        client.table(EXPENSES_TABLE).delete().eq("trip_id", trip_code).execute()

        # 3. Delete all member records for this trip
        client.table(MEMBERS_TABLE).delete().eq("trip_id", trip_uuid).execute()

        # 4. Delete the trip itself
        client.table(TRIPS_TABLE).delete().eq("id", trip_uuid).execute()

        return {"status": "deleted", "trip_code": trip_code}

    except HTTPException:
        raise
    except Exception as e:
        print(f"DELETE /trips/{trip_code} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

# ── Members ───────────────────────────────────────────────────────────

@app.get("/members/{trip_code}")
async def get_members(trip_code: str, authorization: str = Header(None)):
    """
    Returns all members of a trip with their display_name and avatar_color
    pulled from Supabase auth user_metadata.

    Flow:
      1. Resolve trip_code → trips.id (uuid)
      2. Query trip_members for all user_ids in that trip
      3. For each user_id, call the Supabase Admin API to read user_metadata
         (requires SUPABASE_SERVICE_KEY — a separate env var from the anon key)
    """
    import os, httpx

    SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    if not SERVICE_KEY:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_SERVICE_KEY env var is not set on Render. "
                   "Add it in Render → Environment (use your Supabase service_role key)."
        )

    # Verify the caller is authenticated
    client = get_user_client(authorization)

    try:
        # 1. Resolve trip_code → trip uuid
        trip_resp = (
            client.table(TRIPS_TABLE)
            .select("id")
            .eq("trip_code", trip_code)
            .single()
            .execute()
        )
        if not trip_resp.data:
            raise HTTPException(status_code=404, detail=f"Trip '{trip_code}' not found.")
        trip_uuid = trip_resp.data["id"]

        # 2. Get all user_ids for this trip
        members_resp = (
            client.table(MEMBERS_TABLE)
            .select("user_id")
            .eq("trip_id", trip_uuid)
            .execute()
        )
        user_ids = [m["user_id"] for m in (members_resp.data or [])]
        if not user_ids:
            return []

        # 3. Fetch user metadata via Supabase Admin API for each user_id
        #    Supabase Admin REST: GET /auth/v1/admin/users/{user_id}
        result = []
        headers = {
            "apikey":        SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
        }
        async with httpx.AsyncClient() as http:
            for uid in user_ids:
                r = await http.get(
                    f"{SUPABASE_URL}/auth/v1/admin/users/{uid}",
                    headers=headers,
                    timeout=5.0
                )
                if r.status_code == 200:
                    user_data = r.json()
                    meta = user_data.get("user_metadata", {})
                    result.append({
                        "user_id":      uid,
                        "display_name": meta.get("display_name", ""),
                        "avatar_color": meta.get("avatar_color", "#6366f1"),
                    })
                else:
                    # User exists in members but metadata fetch failed — include with fallback
                    result.append({
                        "user_id":      uid,
                        "display_name": "",
                        "avatar_color": "#6366f1",
                    })

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"GET /members/{trip_code} error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")