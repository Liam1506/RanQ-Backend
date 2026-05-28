from supabase import Client
from fastapi import HTTPException


def auth_db(client: Client, id: str):
    try:
        response = client.table("users").select("verified, admin").eq("id", id).execute()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized")

    
    if not response.data:
        raise HTTPException(status_code=401, detail="Unauthorized")

    row = response.data[0]
    if not row["verified"]:
        raise HTTPException(status_code=402, detail="Unverified")
    return id


def auth_db_admin(client: Client, id: str):
    try:
        response = client.table("users").select("verified, admin").eq("id", id).execute()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized")

    
    if not response.data:
        raise HTTPException(status_code=401, detail="Unauthorized")

    row = response.data[0]
    if not row["verified"] or not row["admin"]:
        raise HTTPException(status_code=402, detail="Unverified")
    return id
