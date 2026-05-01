from supabase import Client
from fastapi import HTTPException


def auth_user(client: Client, id: str):
    response = client.table("users").select("verified, admin").eq("id", id).execute()
    row = response.data[0] if response.data else None

    if not row:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not row["verified"]:
        raise HTTPException(status_code=402, detail="Unverified")
    return True
